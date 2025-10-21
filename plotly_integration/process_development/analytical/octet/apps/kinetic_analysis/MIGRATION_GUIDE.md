# Migration Guide: Centralized Kinetics Analysis Structure

## Overview

All Octet kinetics files have been centralized into:
```
plotly_integration/process_development/analytical/octet/apps/kinetic_analysis/
```

This document describes what changed and what you need to update.

---

## What Changed

### Before (Old Structure)
```
plotly_integration/
├── process_development/analytical/octet/
│   ├── octet_kinetics_dash_app.py          # Dashboard (OLD LOCATION)
│   ├── dashboard_processing.py              # Signal processing (OLD LOCATION)
│   ├── data_import/
│   │   ├── frd_importer.py                 # (OLD LOCATION)
│   │   └── htsettings_parser.py            # (OLD LOCATION)
│   └── kinetic_analysis/
│       └── frd_parser.py                    # (OLD LOCATION)
└── management/commands/
    └── import_kinetics_optimized.py         # Complex 300+ line file
```

### After (New Structure)
```
plotly_integration/
├── process_development/analytical/octet/apps/kinetic_analysis/
│   ├── dashboard/
│   │   ├── octet_kinetics_dash_app.py     # NEW LOCATION
│   │   └── dashboard_processing.py         # NEW LOCATION
│   ├── data_import/
│   │   ├── import_command.py              # NEW: Core logic
│   │   ├── frd_importer.py                # MOVED HERE
│   │   ├── frd_parser.py                  # MOVED HERE
│   │   └── htsettings_parser.py           # MOVED HERE
│   ├── models/
│   │   └── __init__.py                    # Model references
│   └── README.md
└── management/commands/
    └── import_kinetics_optimized.py        # NOW: Simple 87-line wrapper
```

---

## Import Path Changes

### Dashboard Access

**Old:**
```python
from plotly_integration.process_development.analytical.octet.octet_kinetics_dash_app import app
```

**New:**
```python
from plotly_integration.process_development.analytical.octet.apps.kinetic_analysis.dashboard.octet_kinetics_dash_app import app
```

### Signal Processing

**Old:**
```python
from plotly_integration.process_development.analytical.octet.dashboard_processing import process_sensor_data
```

**New:**
```python
from plotly_integration.process_development.analytical.octet.apps.kinetic_analysis.dashboard.dashboard_processing import process_sensor_data
```

### Data Import (Python API)

**Old:**
```python
# No clean Python API existed - had to use Django management command
```

**New:**
```python
from plotly_integration.process_development.analytical.octet.apps.kinetic_analysis.data_import.import_command import import_kinetics_data

experiment = import_kinetics_data(
    experiment_name='OE292',
    data_dir='/path/to/data',
    created_by='username'
)
```

### FRD Parser

**Old:**
```python
from plotly_integration.process_development.analytical.octet.kinetic_analysis.frd_parser import FRDParser
```

**New:**
```python
from plotly_integration.process_development.analytical.octet.apps.kinetic_analysis.data_import.frd_parser import FRDParser
```

---

## Django Management Command

### Usage (UNCHANGED)

The command usage remains exactly the same:

```bash
python manage.py import_kinetics_optimized \
    --experiment_name OE292 \
    --data_dir "C:/path/to/OE292" \
    --description "Description" \
    --created_by username \
    --clear_existing
```

### Internal Changes

- **Before**: 367 lines with all logic in command file
- **After**: 87 lines - delegates to `KineticsImporter` class

---

## URL/View Registration

### Django URLs (If registered)

**Old:**
```python
# urls.py
from plotly_integration.process_development.analytical.octet.octet_kinetics_dash_app import app as kinetics_app

urlpatterns = [
    path('kinetics/', kinetics_app.as_view(), name='kinetics'),
]
```

**New:**
```python
# urls.py
from plotly_integration.process_development.analytical.octet.apps.kinetic_analysis.dashboard.octet_kinetics_dash_app import app as kinetics_app

urlpatterns = [
    path('kinetics/', kinetics_app.as_view(), name='kinetics'),
]
```

---

## Benefits of New Structure

### 1. **Better Organization**
- All kinetics files in one place
- Clear separation: dashboard vs. data_import vs. models
- Easier to find and maintain code

### 2. **Reusable Python API**
- Can import data from Python scripts without Django command
- Useful for automated workflows, Jupyter notebooks, etc.

### 3. **Simplified Management Command**
- Command is now just a thin wrapper
- Core logic in `KineticsImporter` class is reusable
- Easier to test import logic independently

### 4. **Clear Dependencies**
- `dashboard_processing.py` is in same package as dashboard
- `frd_parser.py` is with other import logic
- No scattered files across multiple directories

---

## Migration Checklist

If you have code that uses the old paths, update as follows:

- [ ] Update dashboard imports
- [ ] Update signal processing imports
- [ ] Update FRD parser imports
- [ ] Update URL registrations (if any)
- [ ] Test dashboard functionality
- [ ] Test data import
- [ ] Update any documentation/scripts with old paths

---

## File Locations Reference

### Dashboard Files
```
apps/kinetic_analysis/dashboard/
├── octet_kinetics_dash_app.py    # Main Dash application
└── dashboard_processing.py        # Signal processing (baseline, filter, etc.)
```

### Import Files
```
apps/kinetic_analysis/data_import/
├── import_command.py             # KineticsImporter class + standalone function
├── frd_importer.py               # FRD file processing logic
├── frd_parser.py                 # Low-level FRD XML parsing
└── htsettings_parser.py          # HTSettings.efrd parser
```

### Models (Reference Only)
```
apps/kinetic_analysis/models/
└── __init__.py                   # Points to plotly_integration.models
```

Actual models are in: `plotly_integration/models.py`
- `OctetKineticsExperiment`
- `OctetKineticsSensor`

---

## Testing

### Test Dashboard
```bash
python manage.py runserver
# Navigate to: http://localhost:8000/plotly_integration/octet_kinetics_dashboard/
```

### Test Import
```bash
python manage.py import_kinetics_optimized \
    --experiment_name TEST \
    --data_dir "C:/path/to/test/data"
```

### Test Python API
```python
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
import django
django.setup()

from plotly_integration.process_development.analytical.octet.apps.kinetic_analysis.data_import.import_command import import_kinetics_data

exp = import_kinetics_data(
    experiment_name='TEST',
    data_dir='/path/to/data',
    created_by='test_user'
)
print(f"Created: {exp.experiment_name}")
```

---

## Rollback (If Needed)

The old files still exist in their original locations (we copied, not moved). If you need to rollback:

1. Update imports to use old paths
2. Revert `import_kinetics_optimized.py` to old version (check git history)
3. The database and models are unchanged, so no data migration needed

---

## Questions?

See `README.md` in the same directory for detailed usage documentation.

Contact the development team for assistance.
