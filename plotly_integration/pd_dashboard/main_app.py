# plotly_integration/pd_dashboard/main_app.py
# Main application file with updated imports for refactored home/cld structure

from django_plotly_dash import DjangoDash
from dash import html, dcc, Input, Output
import dash_bootstrap_components as dbc
from .core.routing_layouts_v1 import create_page_router
from .shared.styles.common_styles import CONTENT_STYLE

print("Starting PD Dashboard initialization...")

# Create the main dashboard app with suppress_callback_exceptions=True
app = DjangoDash("PDDashboardApp",
                 external_stylesheets=[
                     dbc.themes.BOOTSTRAP,
                     "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
                 ],
                 title="PD Dashboard",
                 suppress_callback_exceptions=True)

# Set the main layout with updated styles
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Store(id="app-state", data={}),
    dcc.Store(id="user-settings", data={}),
    # Add a store for the parsed pathname
    dcc.Store(id="parsed-pathname", data="/"),

    # Sidebar navigation
    html.Div(id="sidebar-nav"),

    # Main content area with lighter background
    html.Div([
        # Page content
        html.Div(id="page-content")

    ], style=CONTENT_STYLE)
], style={"backgroundColor": "#fafbfc", "minHeight": "100vh"})

# Client-side callback to handle hash routing
app.clientside_callback(
    """
    function(href) {
        if (!href) {
            return '/';
        }

        console.log('Current href:', href);

        // Check if URL contains hash routing
        if (href.includes('#!')) {
            try {
                const hashPart = href.split('#!')[1];
                if (!hashPart) {
                    return '/';
                }

                // Remove query parameters from pathname
                const pathname = hashPart.split('?')[0];
                const cleanPath = pathname ? '/' + pathname.replace(/^\/+/, '') : '/';

                console.log('Parsed pathname from hash:', cleanPath);
                return cleanPath;
            } catch (error) {
                console.error('Error parsing hash:', error);
                return '/';
            }
        }

        // For non-hash URLs, extract pathname normally
        try {
            const url = new URL(href);
            const pathname = url.pathname === '/' ? '/' : url.pathname;
            console.log('Parsed pathname from URL:', pathname);
            return pathname;
        } catch (error) {
            console.error('Error parsing URL:', error);
            return '/';
        }
    }
    """,
    Output("parsed-pathname", "data"),
    Input("url", "href"),
    prevent_initial_call=False
)

# Client-side callback to trigger sidebar initialization
app.clientside_callback(
    """
    function(pathname) {
        // Trigger sidebar initialization after a short delay
        setTimeout(function() {
            const initButton = document.getElementById('sidebar-init-button');
            if (initButton && initButton.click) {
                initButton.click();
                console.log('Sidebar initialized via client callback');
            }
        }, 100);
        return pathname;
    }
    """,
    Output("sidebar-init-button", "n_clicks"),
    Input("parsed-pathname", "data"),
    prevent_initial_call=False
)

# Initialize routing
print("Initializing routing...")
create_page_router(app)

# Register sidebar callbacks
print("Registering sidebar callbacks...")
try:
    from .core.sidebar_navigation import register_sidebar_callbacks
    register_sidebar_callbacks(app)
    print("Success: Sidebar callbacks registered successfully")
except Exception as e:
    print(f"Error: Sidebar callbacks registration failed: {e}")

# Import all callbacks to register them
print("Loading core callbacks...")

# Test callback imports individually with updated paths
print("Testing callback imports one by one...")

# Updated imports to match refactored home/cld structure
try:
    print("Testing create_samples import...")
    from .home.cld.create_samples.callbacks import create_samples
    print("Success: create_samples imported successfully")
except Exception as e:
    print(f"Error: create_samples import failed: {e}")

try:
    print("Testing view_samples import...")
    from .home.cld.view_samples.callbacks import view_samples
    print("Success: view_samples imported successfully")
except Exception as e:
    print(f"Error: view_samples import failed: {e}")

try:
    print("Testing sample_sets import...")
    from .home.cld.sample_sets.callbacks import sample_sets,sample_set_details
    print("Success: sample_sets imported successfully")
except Exception as e:
    print(f"Error: sample_sets import failed: {e}")

try:
    print("Testing file_upload_handlers import...")
    from .home.cld.create_samples.callbacks import file_upload_handlers
    print("Success: file_upload_handlers imported successfully")
except Exception as e:
    print(f"Error: file_upload_handlers import failed: {e}")

try:
    print("Testing analysis_requests import...")
    from .home.cld.create_samples.callbacks import analysis_requests
    print("Success: analysis_requests imported successfully")
except Exception as e:
    print(f"Error: analysis_requests import failed: {e}")

# Import USP callbacks
try:
    print("Testing USP create_samples import...")
    from .home.usp.create_samples.callbacks import create_samples
    print("Success: USP create_samples imported successfully")
except Exception as e:
    print(f"Error: USP create_samples import failed: {e}")

try:
    print("Testing USP view_samples import...")
    from .home.usp.view_samples.callbacks import view_samples
    print("Success: USP view_samples imported successfully")
except Exception as e:
    print(f"Error: USP view_samples import failed: {e}")

try:
    print("Testing USP sample_sets import...")
    from .home.usp.sample_sets.callbacks import sample_sets
    print("Success: USP sample_sets imported successfully")
except Exception as e:
    print(f"Error: USP sample_sets import failed: {e}")

# Import dashboard home
try:
    print("Testing dashboard_home import...")
    from .core import dashboard_home
    print("Success: dashboard_home imported successfully")
except Exception as e:
    print(f"Error: dashboard_home import failed: {e}")

# Import SEC integration callbacks
try:
    print("Testing sec_callbacks import...")
    from .embedded_apps.sec_integration import sec_callbacks
    print("Success: sec_callbacks imported successfully")
except Exception as e:
    print(f"Error: sec_callbacks import failed: {e}")

# Register global error handler
@app.callback(
    Output("app-state", "data", allow_duplicate=True),
    Input("app-state", "data"),
    prevent_initial_call=True
)
def handle_app_errors(app_state):
    """Global error handler for the application"""
    try:
        if not app_state:
            app_state = {"initialized": True, "errors": []}
        return app_state
    except Exception as e:
        print(f"Error: App error: {e}")
        return {"initialized": False, "errors": [str(e)]}


print("PD Dashboard initialization complete!")
print("   Success: App created with suppress_callback_exceptions=True")
print("   Success: Layout set")
print("   Success: Routing initialized")
print("   Check above for callback import results")