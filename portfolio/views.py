from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.http import HttpResponse, FileResponse
from django.core.files.base import ContentFile
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
import cloudinary
import cloudinary.uploader
import cloudinary.api
from io import BytesIO

from .models import (
    Resume, Experience, Education, 
    Skill, ResumeProject, PortfolioProject
)
from .serializers import (
    ResumeSerializer, ResumeCreateSerializer,
    ExperienceSerializer, EducationSerializer, SkillSerializer, ResumeProjectSerializer,
    PortfolioProjectSerializer, PortfolioProjectCreateSerializer, PortfolioProjectUpdateSerializer
)
from .pdf_generator import ResumePDFGenerator
from django.shortcuts import redirect


def api_root_view(request):
    return redirect('api-root')


class ResumeViewSet(viewsets.ModelViewSet):
    queryset = Resume.objects.filter(is_active=True)
    permission_classes = [AllowAny]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ResumeCreateSerializer
        return ResumeSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """Override create to generate PDF after resume is created"""
        instance = serializer.save()
        self.regenerate_resume_pdf(instance)

    def perform_update(self, serializer):
        """Override update to regenerate PDF when resume is modified"""
        instance = serializer.save()

        self.regenerate_resume_pdf(instance)

    def regenerate_resume_pdf(self, resume):
        """Helper method to regenerate PDF for a resume"""
        try:
            pdf_generator = ResumePDFGenerator()
            pdf_buffer = pdf_generator.generate_resume_pdf(resume)
            
            pdf_buffer.seek(0)
            public_id = f"resumes/resume_{resume.id}_{resume.name.replace(' ', '_')}"
            
            result = cloudinary.uploader.upload(
                pdf_buffer,
                resource_type='raw',
                public_id=public_id,
                overwrite=True,
                format='pdf',
                type='upload',
                access_mode='public' 
            )
            
            resume.pdf_file = result
            resume.save()
            return resume.pdf_file
            
        except Exception as e:
            print(f"Error regenerating resume PDF: {e}")
            return None

    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        resume = self.get_object()
        
        if needs_regeneration:
            self.regenerate_resume_pdf(resume)
        
        if resume.pdf_file:
            try:

                cloud_name = cloudinary.config().cloud_name
                public_id = resume.pdf_file.public_id
                
                pdf_url = f"https://res.cloudinary.com/{cloud_name}/raw/upload/{public_id}.pdf"
                
                print(f"Manual PDF URL: {pdf_url}")
                
                import requests
                test_response = requests.head(pdf_url, timeout=10)
                
                if test_response.status_code == 200:
                    return Response({
                        'success': True,
                        'download_url': pdf_url,
                        'filename': f"resume_{resume.name.replace(' ', '_')}.pdf",
                        'message': 'PDF is accessible'
                    })
                else:
                    return Response({
                        'error': f'PDF not publicly accessible (HTTP {test_response.status_code})',
                        'url_tested': pdf_url,
                        'solution': 'Check Cloudinary account settings for raw file access'
                    }, status=500)
                    
            except Exception as e:
                return Response({'error': f'URL generation failed: {str(e)}'}, status=500)
        
        return Response({'error': 'PDF not available'}, status=404)

    @action(detail=True, methods=['get'])
    def pdf_url(self, request, pk=None):
        """Get the Cloudinary PDF URL without redirecting"""
        resume = self.get_object()
        
        if resume.pdf_file:
            try:
                pdf_url = cloudinary.utils.cloudinary_url(
                    resume.pdf_file.public_id,
                    resource_type='raw',
                    format='pdf'
                )[0]
                return Response({'pdf_url': pdf_url})
            except AttributeError:
                return Response({'error': 'PDF file not properly configured'}, status=500)
        
        return Response({'error': 'PDF not available'}, status=404)

    @action(detail=True, methods=['post'])
    def generate_pdf(self, request, pk=None):
        """Manually trigger PDF generation"""
        resume = self.get_object()
        try:
            self.regenerate_resume_pdf(resume)
            return Response({'message': 'PDF generated successfully!'})
        except Exception as e:
            return Response({'error': f'Failed to generate PDF: {str(e)}'}, status=500)

    @action(detail=False, methods=['get'])
    def active(self, request):
        active_resume = Resume.objects.filter(is_active=True).first()
        if not active_resume:
            return Response({'error': 'No active resume found'}, status=404)
        
        serializer = self.get_serializer(active_resume)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def set_active(self, request, pk=None):
        """Set a resume as active and deactivate others"""
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=401)
            
        resume = self.get_object()
        
        # Deactivate all resumes
        Resume.objects.all().update(is_active=False)
        # Activate this resume
        resume.is_active = True
        resume.save()
        
        return Response({
            'message': f'Resume "{resume.name}" set as active successfully!',
            'resume': ResumeSerializer(resume).data
        })

    @action(detail=True, methods=['delete'])
    def delete_pdf(self, request, pk=None):
        """Delete the PDF file from Cloudinary"""
        resume = self.get_object()
        
        if resume.pdf_file:
            try:
                # Delete from Cloudinary
                cloudinary.uploader.destroy(resume.pdf_file.public_id, resource_type='raw')
                resume.pdf_file = None
                resume.save()
                return Response({'message': 'PDF deleted successfully!'})
            except Exception as e:
                return Response({'error': f'Failed to delete PDF: {str(e)}'}, status=500)
        
        return Response({'message': 'No PDF to delete'})


class BaseResumeRelatedViewSet(viewsets.ModelViewSet):
    """Base viewset for resume-related models with PDF regeneration"""
    permission_classes = [IsAuthenticated]
    
    def regenerate_related_resume_pdf(self, resume):
        """Helper method to regenerate PDF for a resume using Cloudinary"""
        try:
            pdf_generator = ResumePDFGenerator()
            pdf_buffer = pdf_generator.generate_resume_pdf(resume)
            
            # Upload PDF to Cloudinary
            pdf_buffer.seek(0)
            public_id = f"resumes/resume_{resume.id}_{resume.name.replace(' ', '_')}"
            
            result = cloudinary.uploader.upload(
                pdf_buffer,
                resource_type='raw',
                public_id=public_id,
                overwrite=True,
                format='pdf'
            )
            
            # Update resume with Cloudinary result
            resume.pdf_file = result
            resume.save()
            
        except Exception as e:
            print(f"Error regenerating resume PDF: {e}")


class ExperienceViewSet(BaseResumeRelatedViewSet):
    queryset = Experience.objects.all()
    serializer_class = ExperienceSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        self.regenerate_related_resume_pdf(instance.resume)

    def perform_update(self, serializer):
        instance = serializer.save()
        self.regenerate_related_resume_pdf(instance.resume)

    def perform_destroy(self, instance):
        resume = instance.resume
        instance.delete()
        self.regenerate_related_resume_pdf(resume)


class EducationViewSet(BaseResumeRelatedViewSet):
    queryset = Education.objects.all()
    serializer_class = EducationSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        self.regenerate_related_resume_pdf(instance.resume)

    def perform_update(self, serializer):
        instance = serializer.save()
        self.regenerate_related_resume_pdf(instance.resume)

    def perform_destroy(self, instance):
        resume = instance.resume
        instance.delete()
        self.regenerate_related_resume_pdf(resume)


class SkillViewSet(BaseResumeRelatedViewSet):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        self.regenerate_related_resume_pdf(instance.resume)

    def perform_update(self, serializer):
        instance = serializer.save()
        self.regenerate_related_resume_pdf(instance.resume)

    def perform_destroy(self, instance):
        resume = instance.resume
        instance.delete()
        self.regenerate_related_resume_pdf(resume)


class ResumeProjectViewSet(BaseResumeRelatedViewSet):
    queryset = ResumeProject.objects.all()
    serializer_class = ResumeProjectSerializer

    def perform_create(self, serializer):
        instance = serializer.save()
        self.regenerate_related_resume_pdf(instance.resume)

    def perform_update(self, serializer):
        instance = serializer.save()
        self.regenerate_related_resume_pdf(instance.resume)

    def perform_destroy(self, instance):
        resume = instance.resume
        instance.delete()
        self.regenerate_related_resume_pdf(resume)


# Portfolio Project Views
class PortfolioProjectViewSet(viewsets.ModelViewSet):
    queryset = PortfolioProject.objects.all()
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['featured']
    search_fields = ['title', 'description', 'technologies']
    ordering_fields = ['created_at', 'updated_at', 'completed_date', 'title']
    ordering = ['-featured', '-completed_date']

    def get_serializer_class(self):
        if self.action == 'create':
            return PortfolioProjectCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return PortfolioProjectUpdateSerializer
        return PortfolioProjectSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [AllowAny]
        return [permission() for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        technologies = request.query_params.get('technologies', None)
        if technologies:
            tech_list = [tech.strip() for tech in technologies.split(',')]
            technology_filters = Q()
            for tech in tech_list:
                technology_filters |= Q(technologies__contains=[tech])
            queryset = queryset.filter(technology_filters)
        
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        project = serializer.save()
        
        headers = self.get_success_headers(serializer.data)
        return Response(
            {
                'message': 'Project created successfully!',
                'project': PortfolioProjectSerializer(project).data
            },
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        project = serializer.save()
        
        return Response(
            {
                'message': 'Project updated successfully!',
                'project': PortfolioProjectSerializer(project).data
            }
        )

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        project_title = instance.title
        
        if instance.image:
            try:
                cloudinary.uploader.destroy(instance.image.public_id)
            except Exception as e:
                print(f"Error deleting image from Cloudinary: {e}")
        
        instance.delete()
        
        return Response(
            {'message': f'Project "{project_title}" deleted successfully!'},
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured projects"""
        featured_projects = self.get_queryset().filter(featured=True)
        serializer = self.get_serializer(featured_projects, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def technologies(self, request):
        """Get all unique technologies used in projects"""
        projects = self.get_queryset()
        all_technologies = set()
        
        for project in projects:
            if project.technologies:
                all_technologies.update(project.technologies)
        
        return Response(sorted(list(all_technologies)))

    @action(detail=True, methods=['post'])
    def toggle_featured(self, request, pk=None):
        """Toggle featured status of a project"""
        project = self.get_object()
        project.featured = not project.featured
        project.save()
        
        status_text = "featured" if project.featured else "unfeatured"
        return Response({
            'message': f'Project "{project.title}" {status_text} successfully!',
            'featured': project.featured
        })

    @action(detail=True, methods=['post'])
    def add_technology(self, request, pk=None):
        """Add a technology to project"""
        project = self.get_object()
        technology = request.data.get('technology', '').strip()
        
        if not technology:
            return Response(
                {'error': 'Technology field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not project.technologies:
            project.technologies = []
        
        if technology not in project.technologies:
            project.technologies.append(technology)
            project.save()
        
        return Response({
            'message': f'Technology "{technology}" added successfully!',
            'technologies': project.technologies
        })

    @action(detail=True, methods=['post'])
    def remove_technology(self, request, pk=None):
        """Remove a technology from project"""
        project = self.get_object()
        technology = request.data.get('technology', '').strip()
        
        if not technology:
            return Response(
                {'error': 'Technology field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if project.technologies and technology in project.technologies:
            project.technologies.remove(technology)
            project.save()
        
        return Response({
            'message': f'Technology "{technology}" removed successfully!',
            'technologies': project.technologies
        })

    @action(detail=True, methods=['delete'])
    def remove_image(self, request, pk=None):
        """Remove project image"""
        project = self.get_object()
        
        if project.image:
            try:
                cloudinary.uploader.destroy(project.image.public_id)
                project.image = None
                project.save()
                
                return Response({'message': 'Project image removed successfully!'})
            except Exception as e:
                return Response(
                    {'error': f'Failed to remove image: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response({'message': 'No image to remove'})