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
import cloudinary.uploader

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

    def perform_update(self, serializer):
        """Override update to regenerate PDF when resume is modified"""
        instance = serializer.save()
        # Regenerate PDF when resume properties are updated
        self.regenerate_resume_pdf(instance)

    def regenerate_resume_pdf(self, resume):
        """Helper method to regenerate PDF for a resume"""
        pdf_generator = ResumePDFGenerator()
        pdf_buffer = pdf_generator.generate_resume_pdf(resume)
        
        # Save PDF to file
        filename = f"resume_{resume.id}_{resume.name.replace(' ', '_')}.pdf"
        resume.pdf_file.save(filename, ContentFile(pdf_buffer.read()))
        resume.save()
        return resume.pdf_file

    @action(detail=True, methods=['get'])
    def download_pdf(self, request, pk=None):
        resume = self.get_object()
        
        # Check if PDF needs regeneration
        needs_regeneration = (
            not resume.pdf_file or 
            request.GET.get('regenerate') or
            self.has_resume_changed(resume)
        )
        
        if needs_regeneration:
            self.regenerate_resume_pdf(resume)
        
        # Return PDF file
        response = FileResponse(
            resume.pdf_file.open('rb'),
            content_type='application/pdf'
        )
        response['Content-Disposition'] = f'attachment; filename="resume_{resume.name.replace(" ", "_")}.pdf"'
        return response

    def has_resume_changed(self, resume):
        """
        Check if resume data has changed since last PDF generation
        by comparing updated_at timestamp with PDF file modification time
        """
        if not resume.pdf_file:
            return True
        
        try:
            pdf_mtime = resume.pdf_file.storage.get_modified_time(resume.pdf_file.name)
            return resume.updated_at > pdf_mtime
        except:
            # If we can't determine, regenerate to be safe
            return True

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
        
        Resume.objects.all().update(is_active=False)
        resume.is_active = True
        resume.save()
        
        return Response({
            'message': f'Resume "{resume.name}" set as active successfully!',
            'resume': ResumeSerializer(resume).data
        })


class ExperienceViewSet(viewsets.ModelViewSet):
    queryset = Experience.objects.all()
    serializer_class = ExperienceSerializer
    permission_classes = [IsAuthenticated]

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

    def regenerate_related_resume_pdf(self, resume):
        pdf_generator = ResumePDFGenerator()
        pdf_buffer = pdf_generator.generate_resume_pdf(resume)
        
        filename = f"resume_{resume.id}_{resume.name.replace(' ', '_')}.pdf"
        resume.pdf_file.save(filename, ContentFile(pdf_buffer.read()))
        resume.save()


class EducationViewSet(viewsets.ModelViewSet):
    queryset = Education.objects.all()
    serializer_class = EducationSerializer
    permission_classes = [IsAuthenticated]

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

    def regenerate_related_resume_pdf(self, resume):
        pdf_generator = ResumePDFGenerator()
        pdf_buffer = pdf_generator.generate_resume_pdf(resume)
        
        filename = f"resume_{resume.id}_{resume.name.replace(' ', '_')}.pdf"
        resume.pdf_file.save(filename, ContentFile(pdf_buffer.read()))
        resume.save()


class SkillViewSet(viewsets.ModelViewSet):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [IsAuthenticated]

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

    def regenerate_related_resume_pdf(self, resume):
        pdf_generator = ResumePDFGenerator()
        pdf_buffer = pdf_generator.generate_resume_pdf(resume)
        
        filename = f"resume_{resume.id}_{resume.name.replace(' ', '_')}.pdf"
        resume.pdf_file.save(filename, ContentFile(pdf_buffer.read()))
        resume.save()


class ResumeProjectViewSet(viewsets.ModelViewSet):
    queryset = ResumeProject.objects.all()
    serializer_class = ResumeProjectSerializer
    permission_classes = [IsAuthenticated]

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

    def regenerate_related_resume_pdf(self, resume):
        pdf_generator = ResumePDFGenerator()
        pdf_buffer = pdf_generator.generate_resume_pdf(resume)
        
        filename = f"resume_{resume.id}_{resume.name.replace(' ', '_')}.pdf"
        resume.pdf_file.save(filename, ContentFile(pdf_buffer.read()))
        resume.save()


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
        
        # Filter by technologies if provided
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
        
        # Delete image from Cloudinary if exists
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
                # Delete image from Cloudinary
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

