from django_plotly_dash import DjangoDash
from dash import html, dcc
from .layout.layout import app_layout

app = DjangoDash("SecReportApp2")
app.layout = app_layout

from .callbacks import report_selection
from .callbacks import save_settings
from.callbacks import plotting
from.callbacks import standard_analysis
from .callbacks import table_data
from .callbacks import utils
from .callbacks import lims_sample_linking