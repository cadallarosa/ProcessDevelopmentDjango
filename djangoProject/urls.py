"""
URL configuration for djangoProject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.hometest, name='hometest')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='hometest')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.urls import path
from plotly_integration.views import pd_dashboard_view


urlpatterns = [
    path('admin/', admin.site.urls),

    path('plotly_integration/', include('plotly_integration.urls')),

    # Root URL embeds PD Dashboard
    path('', pd_dashboard_view, name='pd_dashboard'),

    # Shortcut to PD Dashboard
    path('dashboard/', pd_dashboard_view, name='pd_dashboard_alt'),




]

from django.conf import settings
from django.conf.urls.static import static

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
