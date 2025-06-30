from django.urls import path
from django_plotly_dash.views import add_to_session
from . import app

urlpatterns = [
    # This will serve the embedded app at /sec-embedded/
    path('', add_to_session, {'dash_app_name': 'SecReportEmbeddedApp'}, name='sec_embedded'),
]