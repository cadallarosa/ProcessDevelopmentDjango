from django.urls import path
from . import views
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
# from .views import trigger_opc_import

urlpatterns = [
    # path('plotly_dash/', views.plotly_dash_view, name='plotly_dash_view'),
    # path("api/trigger-opc-import/", trigger_opc_import, name="trigger_opc_import"),
    path('dash-app/', include('django_plotly_dash.urls')),
    path('octet-analysis/', views.octet_analysis_view, name='octet_analysis'),
    path('octet-analysis-v2/', views.octet_analysis_v2_view, name='octet_analysis_v2'),
    path('octet-kinetics/', views.octet_kinetics_view, name='octet_kinetics'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
