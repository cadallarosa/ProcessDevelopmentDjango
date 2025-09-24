# USP Sample Management App

## Overview

The USP (Upstream Process) Sample Management App is a dedicated application for managing upstream process samples from cell culture experiments. This app is organized as a separate module following the same patterns as the CLD samples but with USP-specific functionality and grouping logic.

## Key Features

### 1. Sample Creation
- **Manual Entry**: Create individual USP samples with detailed metadata
- **Template Import**: Download templates and bulk import sample data
- **Bulk Upload**: Upload CSV/Excel files with multiple samples

### 2. Sample Viewing & Management
- **Filterable Table**: Search and filter samples by project, cell line, vessel type, etc.
- **Export Functionality**: Export filtered results to CSV
- **Batch Operations**: Select multiple samples for batch operations

### 3. Sample Sets (Project + Reactor Grouping)
- **Automated Grouping**: Group samples by project and reactor type
- **Analysis Tracking**: Track analysis requests and completion status
- **Set Management**: Create, view, and manage sample sets

## Database Models

### Core USP Models (Existing)
- `LimsUpstreamSamples`: Individual USP samples with cell culture metadata
- Uses existing `LimsSampleAnalysis` for analysis data linking

### New USP Sample Sets Models
- `UspSampleSet`: Groups samples by project and reactor type
- `UspSampleSetMembership`: Links individual samples to sets
- `UspAnalysisRequest`: Tracks analysis requests for sample sets

## Directory Structure

```
usp_samples/
├── __init__.py
├── usp_samples_app.py              # Main app entry point
├── README.md                       # This documentation
├── create_samples/
│   ├── __init__.py
│   ├── callbacks/
│   │   ├── __init__.py
│   │   └── create_samples.py       # Sample creation callbacks
│   └── layouts/
│       ├── __init__.py
│       └── create_samples.py       # Sample creation layouts
├── view_samples/
│   ├── __init__.py
│   ├── callbacks/
│   │   ├── __init__.py
│   │   └── view_samples.py         # Sample viewing callbacks
│   └── layouts/
│       ├── __init__.py
│       └── view_samples.py         # Sample viewing layouts
└── sample_sets/
    ├── __init__.py
    ├── callbacks/
    │   ├── __init__.py
    │   └── sample_sets.py          # Sample sets callbacks
    └── layouts/
        ├── __init__.py
        └── sample_sets.py          # Sample sets layouts
```

## Usage

### Creating Samples
1. Navigate to the USP samples app
2. Choose "Create Samples"
3. Select creation method:
   - **Manual**: Fill form for individual samples
   - **Template**: Download template, fill it, and upload
   - **Upload**: Upload existing CSV/Excel files

### Viewing Samples
1. Use filters to narrow down samples:
   - Project ID
   - Cell Line
   - Vessel Type
   - Development Stage
   - Date Range
   - Text Search
2. Export filtered results as needed

### Managing Sample Sets
1. Sample sets are automatically created based on:
   - Project ID
   - Reactor Type
   - Experiment Number
2. Each set tracks:
   - Sample count and range
   - Analysis requests and status
   - Creation and modification dates

## Sample Set Grouping Logic

Unlike CLD samples (grouped by project/SIP/dev stage), USP samples are grouped by:
- **Project ID**: The main project identifier
- **Reactor Type**: Bioreactor, Shake Flask, Ambr250, etc.
- **Experiment Number**: Optional numeric identifier for experiment runs

This grouping makes sense for upstream processes where the reactor type and experimental conditions are key organizational factors.

## Integration Points

### Database Integration
- Uses existing `LimsUpstreamSamples` model
- Links to `LimsSampleAnalysis` for analysis results
- New USP-specific sample sets models

### Analysis Integration
- Ready for integration with USP-specific analysis types:
  - SEC (Size Exclusion Chromatography)
  - AKTA (Chromatography)
  - Titer assays
  - Viability measurements
  - Metabolite analysis
  - Flow cytometry
  - HPLC analysis

### Navigation
- Integrated with main process development navigation
- Cross-links between create, view, and sets functionality

## Migration

The app includes a Django migration (`0111_add_usp_sample_sets_models`) that creates the new USP sample sets models. Run:

```bash
python manage.py migrate plotly_integration
```

## Future Enhancements

1. **Analysis Results Integration**: Connect with specific USP analysis result models
2. **Advanced Filtering**: Time-series filtering, batch comparisons
3. **Reporting**: Automated report generation for sample sets
4. **Integration**: Connect with bioreactor data and process parameters
5. **User Management**: Add user permissions and ownership tracking

## Comparison with CLD Samples

| Aspect | CLD Samples | USP Samples |
|--------|-------------|-------------|
| Location | `pd_dashboard/home/cld/` | `process_development/cell_culture/usp_samples/` |
| Grouping | Project + SIP + Dev Stage | Project + Reactor Type + Experiment # |
| Sample Type | Fed Batch (FB) | Upstream Process (UP) |
| Analysis Types | SEC, AKTA, Titer, CE-SDS, etc. | SEC, AKTA, Titer, Viability, Metabolites, Flow Cytometry |
| Data Model | `LimsSampleSet` | `UspSampleSet` |

This separation allows for specialized functionality while maintaining code reuse and consistency across the platform.