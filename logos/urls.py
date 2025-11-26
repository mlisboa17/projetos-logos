"""
URL configuration for logos project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts import views as accounts_views
from accounts.api_views import OrganizationViewSet, UserViewSet, AuthViewSet
from erp_hub.api_views import ERPIntegrationViewSet, StoreViewSet, SyncLogViewSet
from cameras.api_views import (
    CameraViewSet, EventViewSet, AlertViewSet,
    CameraScheduleViewSet, AIModelViewSet
)

# Router para APIs REST
router = DefaultRouter()
router.register(r'organizations', OrganizationViewSet, basename='organization')
router.register(r'users', UserViewSet, basename='user')
router.register(r'auth', AuthViewSet, basename='auth')
router.register(r'erp-integrations', ERPIntegrationViewSet, basename='erp-integration')
router.register(r'stores', StoreViewSet, basename='store')
router.register(r'sync-logs', SyncLogViewSet, basename='sync-log')
router.register(r'cameras', CameraViewSet, basename='camera')
router.register(r'events', EventViewSet, basename='event')
router.register(r'alerts', AlertViewSet, basename='alert')
router.register(r'camera-schedules', CameraScheduleViewSet, basename='camera-schedule')
router.register(r'ai-models', AIModelViewSet, basename='ai-model')

urlpatterns = [
    # Frontend URLs
    path('', accounts_views.home, name='home'),
    path('login/', accounts_views.user_login, name='login'),
    path('logout/', accounts_views.user_logout, name='logout'),
    path('api-test/', accounts_views.api_test, name='api_test'),
    path('cadastro/', accounts_views.register, name='register'),
    path('cadastro/pendente/', accounts_views.registration_pending, name='registration_pending'),
    path('admin/pending-users/', accounts_views.pending_users, name='pending_users'),
    path('admin/approve-user/<int:user_id>/', accounts_views.approve_user, name='approve_user'),
    path('admin/reject-user/<int:user_id>/', accounts_views.reject_user, name='reject_user'),
    
    # Trocar organizaÃ§Ã£o
    path('switch-org/<int:org_id>/', accounts_views.switch_organization, name='switch_organization'),
    
    # VerifiK URLs
    path('verifik/', include('verifik.urls')),

    # VerifiK API (Detecção)
    path('api/verifik/', include('verifik.api_urls')),
    
    # Django Admin
    path('admin/', admin.site.urls),
    
    # API URLs
    path('api/', include(router.urls)),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
        path('solar/', include('solar_monitor.urls')),
    path('fuel/', include('fuel_prices.urls')),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

