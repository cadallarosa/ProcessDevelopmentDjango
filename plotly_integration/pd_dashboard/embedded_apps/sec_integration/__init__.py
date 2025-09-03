# cld_dashboard/embedded_apps/sec_integration/__init__.py
"""SEC Integration Module for CLD Dashboard"""

print("SEC Integration module loading...")

# Import the main components
try:
    from . import sec_embedder
    print("Success: sec_embedder imported successfully")
except Exception as e:
    print(f"Error: sec_embedder import failed: {e}")

try:
    from . import sec_callbacks
    print("Success: sec_callbacks imported successfully")
except Exception as e:
    print(f"Error: sec_callbacks import failed: {e}")

try:
    from . import sec_dashboard
    print("Success: sec_dashboard imported successfully")
except Exception as e:
    print(f"Error: sec_dashboard import failed: {e}")

__all__ = ['sec_embedder', 'sec_callbacks', 'sec_dashboard']