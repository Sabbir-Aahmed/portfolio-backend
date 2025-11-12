from rest_framework import serializers
from .models import Resume, Experience, Education, Skill, ResumeProject, PortfolioProject



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
        if obj.pdf_file:
            return obj.pdf_file.url
        return None

class ResumeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resume
        fields = ['name', 'email', 'phone', 'location', 'summary', 
                 'github_url', 'linkedin_url', 'portfolio_url']

class PortfolioProjectSerializer(serializers.ModelSerializer):
    technologies_display = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = PortfolioProject
        fields = [
            'id', 'title', 'description', 'short_description', 'image', 
            'image_url', 'technologies', 'technologies_display', 'live_link', 
            'github_link', 'featured', 'completed_date'
        ]
        read_only_fields = ['id', 'image_url']

    def get_technologies_display(self, obj):
        return obj.get_technologies_display()

    def get_image_url(self, obj):
        if obj.image:
            return obj.image.url
        return None

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
    class Meta:
        model = PortfolioProject
        fields = [
            'title', 'description', 'short_description', 'image', 
            'technologies', 'live_link', 'github_link', 'featured', 'completed_date'
        ]

class PortfolioProjectUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioProject
        fields = [
            'title', 'description', 'short_description', 'image', 
            'technologies', 'live_link', 'github_link', 'featured', 'completed_date'
        ]
        extra_kwargs = {
            'title': {'required': False},
            'description': {'required': False},
        }