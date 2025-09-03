"""
Test if the import app loads correctly with Django
"""
import os
import sys
import django

# Setup Django
sys.path.append(r'C:\Users\cdallarosa\DataAlchemy\djangoProject')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
django.setup()

try:
    print("Testing import app loading...")
    import dasgip_import_app
    print("SUCCESS: Import app loaded!")
    
    # Check if the app is registered
    from django_plotly_dash.models import DashApp
    apps = DashApp.objects.all()
    print(f"Registered Dash apps: {[app.app_name for app in apps]}")
    
    # Check callback registration
    print("Checking callback registration...")
    app = dasgip_import_app.app
    print(f"App object: {type(app)}")
    
    # Check if callbacks are registered
    if hasattr(app, 'callback_map'):
        print(f"Callbacks: {len(app.callback_map)}")
    else:
        print("No callback_map attribute found")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()