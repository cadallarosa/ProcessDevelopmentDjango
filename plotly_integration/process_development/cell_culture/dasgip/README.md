# DASGIP Bioreactor Data Processing

## Overview
This module provides functionality for importing and analyzing DASGIP bioreactor data files.

## Folder Structure

### Main Applications
- `dasgip_import_app.py` - Main Dash application for uploading and importing DASGIP CSV files
- `dasgip_report_app.py` - Application for viewing and analyzing imported data
- `dasgip_report_app v2.py` - Alternative report application

### Helper Utilities (`helpers/`)
- `dasgip_parser.py` - Main parser class (DasgipFinalParser) for processing DASGIP CSV files
- `dasgip_parser_v1.py` - Original parser (legacy)
- `dasgip_parser_v2.py` - Second iteration parser (legacy)
- `dasgip_simple_parser.py` - Simplified parser (legacy)
- `dasgip_simple_parser_v3.py` - Third iteration simple parser (legacy)
- `parse_dasgip_data.py` - Utility functions for data processing
- `visualize_dasgip_data.py` - Data visualization utilities

### Test Files (`tests/`)
- Various test scripts for debugging and validation
- `test_simple_import.py` - Test the complete import process
- `test_app_loading.py` - Test Dash app loading
- Other test files for parser validation

### Data Folders
- `raw_data/` - Original DASGIP CSV export files
- `cleaned_data/` - Processed data files
- HTML files - DASGIP process overview and performance reports

## Usage

### Import Data
1. Navigate to: `http://localhost:8000/plotly_integration/dash-app/app/dasgip_import/`
2. Upload DASGIP CSV file
3. Review detected units and data preview
4. Click "Import Data to Database" to save to database

### Database Schema
Uses simplified 2-table structure:
- `usp_bioreactor_runs` - Metadata for each bioreactor run (keyed by UP number)
- `usp_timeseries_data` - Time series process parameters linked to runs

### Process Parameters Stored
- Dissolved Oxygen (DO): PV, SP, Output
- pH: PV, SP, Output  
- Temperature: PV, SP, Output
- RPM: PV, SP
- Volume: PV
- Air Flow: PV, SP
- Feed A/B Flow: PV, SP
- O2/CO2 Concentration: PV, SP

## Development Notes
- Uses DasgipFinalParser for reliable multi-unit detection
- Handles NaN values properly for MySQL compatibility
- Auto-generates UP numbers if not provided
- Includes comprehensive error handling and logging