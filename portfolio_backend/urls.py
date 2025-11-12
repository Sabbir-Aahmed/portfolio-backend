
from django.contrib import admin
from django.urls import path
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from portfolio.views import api_root_view


schema_view = get_schema_view(
   openapi.Info(
      title="Portfolio API",
      default_version='v1',
      description="It is a vaccination system API",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="mdsabbir5820@gmail.com"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    
    path('', api_root_view),
    path('', include('portfolio.urls'), name='api-root'),
    path('api/swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
