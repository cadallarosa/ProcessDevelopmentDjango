from django_plotly_dash import DjangoDash
from dash import html, dcc
from .layout.layout import embedded_app_layout

# Create the embedded app
app = DjangoDash("SecReportEmbeddedApp", external_stylesheets=[])
app.layout = embedded_app_layout

# Import callbacks - order matters for registration
from .callbacks import report_loading
from .callbacks import plotting
from .callbacks import save_settings
from .callbacks import standard_analysis
from .callbacks import table_data
from .callbacks import utils
from .callbacks import lims_sample_linking