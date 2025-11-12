from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

router = DefaultRouter()
router.register('resumes', views.ResumeViewSet, basename='resume')
router.register('experiences', views.ExperienceViewSet, basename='experience')
router.register('educations', views.EducationViewSet, basename='education')
router.register('skills', views.SkillViewSet, basename='skill')
router.register('resume-projects', views.ResumeProjectViewSet, basename='resume-project')
router.register('portfolio-projects', views.PortfolioProjectViewSet, basename='portfolio-project')

urlpatterns = [
    path('api/', include(router.urls)),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]