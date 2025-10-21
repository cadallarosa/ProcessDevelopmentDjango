# Octet Kinetics Analysis Application

Centralized module for Octet kinetics data import, processing, and visualization.

## Directory Structure

```
kinetic_analysis/
├── dashboard/                          # Dash visualization application
│   ├── octet_kinetics_dash_app.py     # Main Dash app for kinetics data
│   └── dashboard_processing.py         # Signal processing functions
│
├── data_import/                        # Data import from FRD files
│   ├── import_command.py              # Core import logic (KineticsImporter class)
│   ├── frd_importer.py                # FRD file processing
│   ├── frd_parser.py                  # Low-level FRD XML parser
│   └── htsettings_parser.py           # HTSettings.efrd parser
│
├── models/                             # Model references
│   └── __init__.py                    # Points to plotly_integration.models
│
└── README.md                          # This file
```

## Database Models

The kinetics data uses optimized Django models defined in `plotly_integration/models.py`:

### OctetKineticsExperiment
One record per experiment, stores:
- Experiment metadata (name, description, dates)
- Instrument info (machine name, sensor type)
- Analysis parameters (binding model, association/dissociation windows)
- File paths (original folder, HTSettings, analysis Excel)

### OctetKineticsSensor
One record per antibody×concentration, stores:
- Sensor identification (FRD file, cycle number, location)
- Sample info (antibody ID, analyte ID, concentration)
- Well locations (loading, baseline, association, dissociation)
- **Time series data as JSON** (loading, baseline, association, dissociation steps)
- Kinetic parameters (KD, ka, kdis, Rmax, R²)
- Reference sensor links

**Key Advantage**: Stores ALL time series data in JSON fields instead of individual rows.
- Old system: 672k rows across 4 tables
- New system: 192 rows with embedded JSON
- **40-50x faster queries!**

## Usage

### 1. Import Data from FRD Files

**Django Management Command:**
```bash
python manage.py import_kinetics_optimized \
    --experiment_name OE292 \
    --data_dir "C:/path/to/OE292/folder" \
    --description "Optional description" \
    --created_by your_username \
    --clear_existing  # Optional: delete existing data first
```

**Python API:**
```python
from plotly_integration.process_development.analytical.octet.apps.kinetic_analysis.data_import.import_command import import_kinetics_data

experiment = import_kinetics_data(
    experiment_name='OE292',
    data_dir='C:/path/to/OE292/folder',
    description='Optional description',
    created_by='your_username',
    clear_existing=False
)
```

### 2. View Data in Dashboard

**Access the dashboard** at:
```
/plotly_integration/octet_kinetics_dashboard/
```

**Features:**
- Grid view: All antibodies as subplots
- Single view: One antibody with all concentrations
- Configurable grid layout (1-8 columns)
- Signal processing:
  - Baseline alignment (auto-calculated from middle third of baseline)
  - Reference subtraction (0 nM concentration as baseline)
  - Savitzky-Golay smoothing filter
- Interactive zoom and pan
- Display KD values
- Show/hide experimental steps

### 3. Query Data Programmatically

```python
from plotly_integration.models import OctetKineticsExperiment, OctetKineticsSensor
import numpy as np

# Get experiment
experiment = OctetKineticsExperiment.objects.get(experiment_name='OE292')

# Get all sensors for one antibody
sensors = OctetKineticsSensor.objects.filter(
    experiment=experiment,
    antibody_id='SI-157C11_P5158'
).order_by('concentration_nm')

# Get time series data for one sensor
sensor = sensors.first()
time, response = sensor.get_full_timeseries()  # Returns numpy arrays

# Get just association phase
assoc_time, assoc_response = sensor.get_association_data()

# Get just dissociation phase
dissoc_time, dissoc_response = sensor.get_dissociation_data()

# Apply signal processing
from plotly_integration.process_development.analytical.octet.apps.kinetic_analysis.dashboard.dashboard_processing import process_sensor_data

time_processed, response_processed = process_sensor_data(
    time, response,
    baseline_align=True,
    baseline_start=-50,
    baseline_end=-10,
    apply_filter=True,
    filter_window=11
)
```

## Required Files for Import

The data directory must contain:

1. **FRD files** (`*.frd`): Raw data files from Octet instrument
2. **FRD_Analysis.xlsx**: Sample mapping with sheets:
   - `All_Cycles`: Maps FRD files to antibodies/concentrations
   - `Processing_Parameters`: Optional processing settings
3. **HTSettings.efrd** (optional): Vendor analysis parameters

## Signal Processing Pipeline

The dashboard applies processing in this order:

1. **Time Normalization**: Association phase starts at time = 0
2. **Baseline Alignment**: Subtract average of baseline window
3. **Reference Subtraction**: Subtract 0 nM concentration from all samples
4. **Savitzky-Golay Filter**: Polynomial smoothing (optional)

## Integration Points

### Django URLs
The dashboard is registered in `plotly_integration/urls.py`:
```python
path('octet_kinetics_dashboard/', octet_kinetics_dash_app.app.as_view(), name='octet_kinetics_dashboard')
```

### Templates
Access via template:
```html
{% load plotly_dash %}
{% plotly_app name="OctetKineticsDashboard" %}
```

## Development

### Adding New Features

**Dashboard modifications:**
- Edit `dashboard/octet_kinetics_dash_app.py`
- Signal processing: `dashboard/dashboard_processing.py`

**Import modifications:**
- Core logic: `data_import/import_command.py`
- FRD parsing: `data_import/frd_parser.py`
- HTSettings: `data_import/htsettings_parser.py`

### Model Changes

Models are defined in `plotly_integration/models.py`. After changes:
```bash
python manage.py makemigrations
python manage.py migrate
```

## Troubleshooting

**Import fails with "FRD file not found":**
- Check that FRD files are in the correct directory
- Verify FRD_Analysis.xlsx has correct file paths

**Dashboard shows no data:**
- Verify experiment was imported successfully
- Check Django logs for errors
- Ensure models match (OctetKineticsExperiment, not old OctetExperiment)

**Reference subtraction doesn't work:**
- Ensure 0.0 nM concentration exists for each antibody
- Check that `is_reference` flag is set correctly

## Performance Notes

- **Query optimization**: Use `.select_related('experiment')` when querying sensors
- **JSON data**: Time series stored as JSON is much faster than individual rows
- **Indexing**: Key fields are indexed for fast lookups (antibody_id, concentration_nm, etc.)
- **Caching**: Consider caching expensive calculations in dashboard

## Version History

- **v2.0**: New optimized JSON-based models (Current)
- **v1.0**: Original 4-table structure (Deprecated)

---

For questions or issues, contact the development team.
