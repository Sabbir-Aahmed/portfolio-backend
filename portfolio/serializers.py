from rest_framework import serializers
from .models import Resume, Experience, Education, Skill, ResumeProject, PortfolioProject
import cloudinary


class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = '__all__'
        read_only_fields = ['id']

class EducationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Education
        fields = '__all__'
        read_only_fields = ['id']

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = '__all__'
        read_only_fields = ['id']

class ResumeProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResumeProject
        fields = '__all__'
        read_only_fields = ['id']

class ResumeSerializer(serializers.ModelSerializer):
    experiences = ExperienceSerializer(many=True, read_only=True)
    educations = EducationSerializer(many=True, read_only=True)
    skills = SkillSerializer(many=True, read_only=True)
    resume_projects = ResumeProjectSerializer(many=True, read_only=True)
    pdf_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Resume
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'pdf_file']
    
    def get_pdf_url(self, obj):
        """
        Safely construct the PDF URL from multiple possible stored shapes:
         - obj.pdf_file may be a public_id string (preferred)
         - or an object with .public_id (older CloudinaryField)
         - or a dict (legacy) with 'public_id' or 'url'
        """
        public_id = None

        pdf_field = getattr(obj, 'pdf_file', None)

        if isinstance(pdf_field, str):
            public_id = pdf_field

        elif hasattr(pdf_field, 'public_id'):
            try:
                public_id = pdf_field.public_id
            except Exception:
                public_id = None

        elif isinstance(pdf_field, dict):
            public_id = pdf_field.get('public_id') or pdf_field.get('publicId') or None
            if not public_id:
                url = pdf_field.get('url') or pdf_field.get('secure_url')
                return url

        if public_id:
            try:
                url = cloudinary.utils.cloudinary_url(public_id, resource_type='raw', format='pdf')[0]
                return url
            except Exception:
                return None

        return None

class ResumeCreateSerializer(serializers.ModelSerializer):
    pdf_file = serializers.FileField(required=False) 
    class Meta:
        model = Resume
        fields = ['name', 'email', 'phone', 'location', 'summary', 
                 'github_url', 'linkedin_url', 'portfolio_url', 'pdf_file']

class PortfolioProjectSerializer(serializers.ModelSerializer):
    # technologies_display = serializers.SerializerMethodField()
    
    class Meta:
        model = PortfolioProject
        fields = [
            'id', 'title', 'description', 'short_description', 'image', 
            'technologies',  'live_link', 'github_client','github_server', 'featured', 'completed_date'
        ]
        read_only_fields = ['id']

    # def get_technologies_display(self, obj):
    #     return obj.get_technologies_display()

    def validate_technologies(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError("Technologies must be a list of strings.")
        return value

    def validate_title(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Title must be at least 2 characters long.")
        return value.strip()

    def validate_description(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Description must be at least 10 characters long.")
        return value.strip()

class PortfolioProjectCreateSerializer(serializers.ModelSerializer):
    image = serializers.ImageField()
    class Meta:
        model = PortfolioProject
        fields = [
            'title', 'description', 'short_description', 'image', 
            'technologies', 'live_link', 'github_client','github_server', 'featured', 'completed_date'
        ]

class PortfolioProjectUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioProject
        fields = [
            'title', 'description', 'short_description', 'image', 
            'technologies', 'live_link', 'github_client','github_server', 'featured', 'completed_date'
        ]
        extra_kwargs = {
            'title': {'required': False},
            'description': {'required': False},
        }