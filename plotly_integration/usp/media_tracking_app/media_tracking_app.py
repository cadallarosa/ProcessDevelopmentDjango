"""
USP Media Tracking App
Complete media preparation system with component library and process-based recipes
"""

import dash
from dash import dcc, html, Input, Output, State, dash_table, no_update, ALL, MATCH, callback_context
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
import pandas as pd
import json
from datetime import datetime, date, timedelta
from django.db import transaction
from plotly_integration.models import (
    USPMediaPrep, USPMediaComponent, USPExperiment, USPMediaRecipe,
    USPMediaRecipeStep, USPMediaComponentLibrary, USPMediaRecipeStepParameter
)


app = DjangoDash("USPMediaTrackingApp", external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
], suppress_callback_exceptions=True)

# Add custom CSS for print
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            @media print {
                /* When printing, hide everything except the modal */
                body.printing-modal > div:not(#react-entry-point) {
                    display: none !important;
                }

                body.printing-modal #react-entry-point > div > div:not(.modal) {
                    display: none !important;
                }

                /* Hide modal backdrop and chrome */
                body.printing-modal .modal-backdrop {
                    display: none !important;
                }

                body.printing-modal .modal-header,
                body.printing-modal .modal-footer {
                    display: none !important;
                }

                /* Make modal full page */
                body.printing-modal .modal {
                    position: absolute !important;
                    left: 0 !important;
                    top: 0 !important;
                    width: 100% !important;
                    height: 100% !important;
                    overflow: visible !important;
                }

                body.printing-modal .modal-dialog {
                    position: absolute !important;
                    left: 0 !important;
                    top: 0 !important;
                    width: 100% !important;
                    max-width: 100% !important;
                    margin: 0 !important;
                    padding: 0 !important;
                    height: auto !important;
                }

                body.printing-modal .modal-content {
                    position: relative !important;
                    border: none !important;
                    box-shadow: none !important;
                    border-radius: 0 !important;
                }

                body.printing-modal .modal-body {
                    padding: 20px !important;
                }

                /* Page break settings */
                .card {
                    page-break-inside: avoid;
                    break-inside: avoid;
                }

                /* Ensure tables don't break badly */
                table {
                    page-break-inside: auto;
                }

                tr {
                    page-break-inside: avoid;
                    page-break-after: auto;
                }
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# Constants
RECIPE_TYPES = [
    {'label': 'Growth Media', 'value': 'Growth Media'},
    {'label': 'Feed A', 'value': 'Feed A'},
    {'label': 'Feed B', 'value': 'Feed B'},
    {'label': 'Basal Media', 'value': 'Basal Media'},
    {'label': 'Supplement', 'value': 'Supplement'},
    {'label': 'Custom', 'value': 'Custom'},
]

COMPONENT_TYPES = [
    {'label': 'Base Powder', 'value': 'base_powder'},
    {'label': 'Glucose', 'value': 'glucose'},
    {'label': 'Glutamine', 'value': 'glutamine'},
    {'label': 'Amino Acid', 'value': 'amino_acid'},
    {'label': 'Vitamin', 'value': 'vitamin'},
    {'label': 'Salt', 'value': 'salt'},
    {'label': 'Growth Factor', 'value': 'growth_factor'},
    {'label': 'Antibiotic', 'value': 'antibiotic'},
    {'label': 'Buffer', 'value': 'buffer'},
    {'label': 'Serum', 'value': 'serum'},
    {'label': 'Supplement', 'value': 'supplement'},
    {'label': 'Acid (pH adjustment)', 'value': 'acid'},
    {'label': 'Base (pH adjustment)', 'value': 'base'},
    {'label': 'Water', 'value': 'water'},
    {'label': 'Other', 'value': 'other'},
]

STEP_TYPES = [
    {'label': 'Add Component', 'value': 'add_component'},
    {'label': 'Initial MilliQ Water Fill (80%)', 'value': 'initial_water_fill'},
    {'label': 'Add Water (Custom)', 'value': 'add_water'},
    {'label': 'Final Water Fill (to 100%)', 'value': 'final_water_fill'},
    {'label': 'Stir', 'value': 'stir'},
    {'label': 'Heat', 'value': 'heat'},
    {'label': 'Cool', 'value': 'cool'},
    {'label': 'Measure pH', 'value': 'measure_ph'},
    {'label': 'Adjust pH', 'value': 'adjust_ph'},
    {'label': 'Measure Osmolality', 'value': 'measure_osmolality'},
    {'label': 'Adjust Osmolality', 'value': 'adjust_osmolality'},
    {'label': 'Filter Sterilize', 'value': 'filter_sterilize'},
    {'label': 'Autoclave', 'value': 'autoclave'},
    {'label': 'Aliquot', 'value': 'aliquot'},
    {'label': 'Note/Instruction', 'value': 'note'},
]

UNIT_OPTIONS = [
    {'label': 'g', 'value': 'g'},
    {'label': 'mg', 'value': 'mg'},
    {'label': 'L', 'value': 'L'},
    {'label': 'mL', 'value': 'mL'},
    {'label': 'µL', 'value': 'µL'},
    {'label': 'g/L', 'value': 'g/L'},
    {'label': 'mg/L', 'value': 'mg/L'},
    {'label': 'mL/L', 'value': 'mL/L'},
    {'label': 'µL/L', 'value': 'µL/L'},
]

# ID Generation Functions
def generate_media_id():
    """Generate the next Media ID in format UPMP####"""
    try:
        last_media = USPMediaPrep.objects.filter(
            media_id__startswith='UPMP'
        ).order_by('-media_id').first()
        if last_media:
            last_number = int(last_media.media_id[4:])
            next_number = last_number + 1
        else:
            next_number = 1
        return f"UPMP{next_number:04d}"
    except:
        return "UPMP0001"

def generate_recipe_id():
    """Generate the next Recipe ID in format RCP####"""
    try:
        last_recipe = USPMediaRecipe.objects.filter(
            recipe_id__startswith='RCP'
        ).order_by('-recipe_id').first()
        if last_recipe:
            last_number = int(last_recipe.recipe_id[3:])
            next_number = last_number + 1
        else:
            next_number = 1
        return f"RCP{next_number:04d}"
    except:
        return "RCP0001"

# Data Retrieval Functions
def get_all_components():
    """Get all components from library"""
    components = USPMediaComponentLibrary.objects.filter(active=True).order_by('component_type', 'component_name')
    data = []
    for comp in components:
        data.append({
            'id': comp.id,
            'component_type': dict(COMPONENT_TYPES).get(comp.component_type, comp.component_type),
            'component_name': comp.component_name,
            'catalog_number': comp.catalog_number or '',
            'vendor': comp.vendor or '',
            'typical_units': comp.typical_units,
            'storage': comp.storage_conditions or '',
        })
    return data

def get_component_options_by_type(component_type=None):
    """Get component options for dropdown, optionally filtered by type"""
    if component_type:
        components = USPMediaComponentLibrary.objects.filter(
            active=True, component_type=component_type
        ).order_by('component_name')
    else:
        components = USPMediaComponentLibrary.objects.filter(active=True).order_by('component_name')

    return [{'label': f"{c.component_name} ({c.catalog_number})" if c.catalog_number else c.component_name,
             'value': c.id} for c in components]

def get_recipe_options():
    """Get available recipes for dropdown"""
    recipes = USPMediaRecipe.objects.filter(active=True).order_by('recipe_type', 'recipe_name')
    return [{'label': f"{rec.recipe_name} v{rec.version} ({rec.recipe_type})", 'value': rec.id}
            for rec in recipes]

def get_all_recipes():
    """Get all recipes for display"""
    recipes = USPMediaRecipe.objects.filter(active=True).prefetch_related('process_steps').order_by('-created_date')
    data = []
    for recipe in recipes:
        steps = recipe.process_steps.all()
        step_count = steps.count()

        data.append({
            'recipe_id': recipe.recipe_id,
            'recipe_name': recipe.recipe_name,
            'recipe_type': recipe.recipe_type,
            'version': recipe.version,
            'base_volume': f"{recipe.base_volume} L",
            'ph_target': recipe.ph_target or '',
            'osmolality_target': recipe.osmolality_target or '',
            'step_count': step_count,
            'storage_temp': recipe.storage_temp or '',
            'shelf_life': f"{recipe.shelf_life_days} days" if recipe.shelf_life_days else '',
            'created_date': recipe.created_date.strftime('%Y-%m-%d') if recipe.created_date else '',
        })
    return data

def get_experiment_options():
    """Get available experiments for dropdown"""
    experiments = USPExperiment.objects.all().order_by('-created_date')
    return [{'label': f"{exp.experiment_id} - {exp.experiment_name}", 'value': exp.experiment_id}
            for exp in experiments]

def get_media_prep_data():
    """Get all media preparations for the table with status"""
    from datetime import date
    media_preps = USPMediaPrep.objects.all().select_related('experiment', 'recipe').prefetch_related('components').order_by('-preparation_date')
    data = []
    for prep in media_preps:
        components = prep.components.all()
        component_count = components.count()

        # Determine status for display
        if prep.is_used_up:
            status = 'Used Up'
        else:
            status = 'Available'

        data.append({
            'id': prep.id,  # Add ID for editing
            'media_id': prep.media_id,
            'media_name': prep.media_name,
            'media_type': prep.media_type,
            'recipe': prep.recipe.recipe_name if prep.recipe else 'Manual',
            'batch_size': f"{prep.batch_size} L",
            'preparation_date': prep.preparation_date.strftime('%Y-%m-%d') if prep.preparation_date else '',
            'expiration_date': prep.expiration_date.strftime('%Y-%m-%d') if prep.expiration_date else '',
            'prepared_by': prep.prepared_by,
            'experiment': prep.experiment.experiment_id if prep.experiment else 'Not linked',
            'component_count': component_count,
            'ph': prep.ph_actual or '',
            'osmolality': prep.osmolality_actual or '',
            'sterility': '✓' if prep.sterility_check else '✗',
            'storage': prep.storage_location or '',
            'status': status,
        })
    return data

def calculate_scaled_process(recipe_id, batch_volume):
    """Calculate scaled process steps based on recipe and batch volume - reads from parameter table"""
    if not recipe_id or not batch_volume:
        return [], 1.0

    try:
        recipe = USPMediaRecipe.objects.get(id=recipe_id)
        all_steps = USPMediaRecipeStep.objects.filter(recipe=recipe).prefetch_related('parameters').order_by('step_number')

        # Calculate scaling factor
        scaling_factor = batch_volume / recipe.base_volume

        scaled_steps = []
        for step in all_steps:
            # Get all parameters for this step
            params = {p.parameter_key: p for p in step.parameters.all()}

            step_info = {
                'step_number': step.step_number,
                'step_type': step.step_type,
                'step_type_display': step.get_step_type_display(),
                'scaling_factor': scaling_factor,
            }

            if step.step_type == 'add_component':
                # Read from parameters table
                component_id = params.get('component_id')
                amount_per_liter = params.get('amount_per_liter')
                amount_unit = params.get('amount_unit')

                if component_id and amount_per_liter:
                    try:
                        component = USPMediaComponentLibrary.objects.get(id=int(component_id.value_text))
                        scaled_amount = float(amount_per_liter.value_text) * batch_volume

                        step_info.update({
                            'component_id': component.id,
                            'component_name': component.component_name,
                            'catalog_number': component.catalog_number or '',
                            'vendor': component.vendor or '',
                            'target_amount': round(scaled_amount, 3),
                            'unit': amount_unit.value_text if amount_unit else component.typical_units,
                            'original_amount_per_liter': float(amount_per_liter.value_text),
                        })
                    except Exception as e:
                        print(f"Error processing component step: {e}")

            elif step.step_type == 'initial_water_fill':
                water_volume = batch_volume * 1000 * 0.8  # 80% in mL
                step_info.update({
                    'water_volume': round(water_volume, 1),
                    'percentage': 80
                })

            elif step.step_type == 'final_water_fill':
                water_volume = batch_volume * 1000  # 100% in mL
                step_info.update({
                    'water_volume': round(water_volume, 1),
                    'percentage': 100
                })

            elif step.step_type == 'add_water':
                target_volume = params.get('target_volume')
                if target_volume:
                    scaled_water = float(target_volume.value_text) * scaling_factor
                    step_info.update({
                        'water_volume': round(scaled_water, 1)
                    })

            elif step.step_type in ['stir', 'heat', 'cool']:
                duration = params.get('duration_minutes')
                temperature = params.get('temperature')

                step_info.update({
                    'duration_minutes': int(duration.value_text) if duration else None,
                    'temperature': float(temperature.value_text) if temperature else None
                })

            elif step.step_type in ['measure_ph', 'adjust_ph']:
                target_ph = params.get('target_ph')
                step_info.update({
                    'target_ph': target_ph.value_text if target_ph else step.instructions
                })

            elif step.step_type in ['measure_osmolality', 'adjust_osmolality']:
                target_osm = params.get('target_osmolality')
                step_info.update({
                    'target_osmolality': target_osm.value_text if target_osm else step.instructions
                })

            # Add instructions if available
            instructions_param = params.get('instructions')
            if instructions_param:
                step_info['instructions'] = instructions_param.value_text
            elif step.instructions:
                step_info['instructions'] = step.instructions

            scaled_steps.append(step_info)

        return scaled_steps, scaling_factor
    except Exception as e:
        print(f"Error calculating scaled process: {e}")
        import traceback
        traceback.print_exc()
        return [], 1.0

# Modals Container - Render once on page load
def get_all_modals():
    """Get all modals - called once to avoid re-rendering on tab switch"""
    modals = []

    # Component Modal (always available)
    modals.append(
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle([
                html.I(className="fas fa-flask me-2"),
                "Add New Component"
            ])),
            dbc.ModalBody([
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Component Type *"),
                        dcc.Dropdown(
                            id="new-comp-type",
                            options=COMPONENT_TYPES,
                            placeholder="Select type..."
                        ),
                    ], width=4),
                    dbc.Col([
                        dbc.Label("Component Name *"),
                        dbc.Input(id="new-comp-name", placeholder="e.g., CD FortiCHO Powder"),
                    ], width=8),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Catalog Number"),
                        dbc.Input(id="new-comp-catalog", placeholder="e.g., A12345"),
                    ], width=4),
                    dbc.Col([
                        dbc.Label("Vendor"),
                        dbc.Input(id="new-comp-vendor", placeholder="e.g., Cytiva"),
                    ], width=4),
                    dbc.Col([
                        dbc.Label("Typical Units *"),
                        dcc.Dropdown(
                            id="new-comp-units",
                            options=UNIT_OPTIONS,
                            placeholder="Select units..."
                        ),
                    ], width=4),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Storage Conditions"),
                        dbc.Input(id="new-comp-storage", placeholder="e.g., 4°C, protected from light"),
                    ], width=12),
                ], className="mb-3"),
                dbc.Label("Notes"),
                dbc.Textarea(id="new-comp-notes", placeholder="Additional information...", rows=2),
            ], style={"padding": "3rem"}),
            dbc.ModalFooter([
                dbc.Button("Cancel", id="cancel-component-btn", color="secondary", outline=True),
                dbc.Button([html.I(className="fas fa-save me-2"), "Save Component"],
                          id="save-component-btn", color="info"),
            ])
        ], id="component-modal", is_open=False, backdrop="static", fullscreen=True)
    )

    # Media Prep Modal
    modals.append(
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle([
                html.I(className="fas fa-vial me-2"),
                "Create New Media Preparation"
            ])),
            dbc.ModalBody([
                # Step 1: Select Recipe and Volume
                dbc.Card([
                    dbc.CardHeader([html.H6("Step 1: Select Recipe and Batch Volume", className="mb-0")]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Select Recipe *"),
                                dcc.Dropdown(
                                    id="prep-recipe-dropdown",
                                    options=[],
                                    placeholder="Select a recipe...",
                                    style={'marginBottom': '50px'}
                                ),
                            ], width=8, style={'paddingBottom': '30px'}),
                            dbc.Col([
                                dbc.Label("Batch Volume (L) *"),
                                dbc.Input(
                                    id="prep-batch-volume-input",
                                    type="number",
                                    step=0.1,
                                    placeholder="e.g., 2.0"
                                ),
                            ], width=4),
                        ], style={'marginBottom': '30px'}),
                        html.Div(className="mt-3"),
                        dbc.Button(
                            [html.I(className="fas fa-calculator me-2"), "Calculate Scaled Amounts"],
                            id="calculate-scaled-amounts-btn",
                            color="primary",
                            outline=True,
                            className="w-100"
                        ),
                    ])
                ], className="mb-3"),

                # Step 2: Review Scaled Process
                dbc.Card([
                    dbc.CardHeader([html.H6("Step 2: Review Scaled Process & Enter Actual Amounts", className="mb-0")]),
                    dbc.CardBody([
                        html.Div(id="scaled-process-container"),
                    ])
                ], className="mb-3"),

                # Step 3: Media Details
                dbc.Card([
                    dbc.CardHeader([html.H6("Step 3: Preparation Details", className="mb-0")]),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("Media ID"),
                                dbc.Input(id="prep-media-id-input", disabled=True),
                            ], width=3),
                            dbc.Col([
                                dbc.Label("Preparation Date *"),
                                dbc.Input(id="prep-date-input", type="date", value=date.today().strftime('%Y-%m-%d')),
                            ], width=3),
                            dbc.Col([
                                dbc.Label("Prepared By *"),
                                dbc.Input(id="prep-prepared-by-input", placeholder="Your name"),
                            ], width=3),
                            dbc.Col([
                                dbc.Label("Link to Experiment"),
                                dcc.Dropdown(
                                    id="prep-experiment-dropdown",
                                    options=[],
                                    placeholder="Optional...",
                                    style={'marginBottom': '50px'}
                                ),
                            ], width=3, style={'paddingBottom': '30px'}),
                        ], className="mb-3"),
                        dbc.Row([
                            dbc.Col([
                                dbc.Label("pH (Actual)"),
                                dbc.Input(id="prep-ph-input", type="number", step=0.01),
                            ], width=3),
                            dbc.Col([
                                dbc.Label("Osmolality (Actual)"),
                                dbc.Input(id="prep-osmolality-input", type="number"),
                            ], width=3),
                            dbc.Col([
                                dbc.Label("Storage Location"),
                                dbc.Input(id="prep-storage-input", placeholder="e.g., 4°C Cold Room"),
                            ], width=3),
                            dbc.Col([
                                dbc.Label("Sterility Check"),
                                dbc.Checklist(
                                    options=[{"label": "Passed", "value": 1}],
                                    value=[],
                                    id="prep-sterility-check",
                                    switch=True,
                                ),
                            ], width=3),
                        ]),
                    ])
                ]),
            ], style={'maxHeight': '85vh', 'overflowY': 'auto', 'padding': '3rem', 'paddingBottom': '150px'}),
            dbc.ModalFooter([
                dbc.Button("Cancel", id="cancel-prep-btn", color="secondary", outline=True),
                dbc.Button([html.I(className="fas fa-save me-2"), "Save Media Prep"],
                          id="save-prep-btn", color="success"),
            ])
        ], id="prep-modal", is_open=False, backdrop="static", fullscreen=True)
    )

    # Recipe Modal
    modals.append(
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle([
                html.I(className="fas fa-book me-2"),
                html.Span("Create New Recipe", id="recipe-modal-title")
            ])),
            dbc.ModalBody([
                # Basic Info
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Recipe ID"),
                        dbc.Input(id="new-recipe-id", disabled=True),
                    ], width=3),
                    dbc.Col([
                        dbc.Label("Recipe Name *"),
                        dbc.Input(id="new-recipe-name", placeholder="e.g., CD FortiCHO + Feeds"),
                    ], width=5),
                    dbc.Col([
                        dbc.Label("Recipe Type *"),
                        dcc.Dropdown(
                            id="new-recipe-type",
                            options=RECIPE_TYPES,
                            placeholder="Select type..."
                        ),
                    ], width=4),
                ], className="mb-3"),
                dbc.Row([
                    dbc.Col([
                        dbc.Label("Version"),
                        dbc.Input(id="new-recipe-version", value="1.0"),
                    ], width=2),
                    dbc.Col([
                        dbc.Label("Base Volume (L)"),
                        dbc.Input(id="new-recipe-base-volume", type="number", value=1.0),
                    ], width=2),
                    dbc.Col([
                        dbc.Label("Target pH"),
                        dbc.Input(id="new-recipe-ph", type="number", step=0.1),
                    ], width=2),
                    dbc.Col([
                        dbc.Label("Target Osm"),
                        dbc.Input(id="new-recipe-osm", type="number"),
                    ], width=2),
                    dbc.Col([
                        dbc.Label("Storage"),
                        dbc.Input(id="new-recipe-storage", placeholder="4°C"),
                    ], width=2),
                    dbc.Col([
                        dbc.Label("Shelf Life (days)"),
                        dbc.Input(id="new-recipe-shelf-life", type="number"),
                    ], width=2),
                ], className="mb-3"),

                html.Hr(),
                html.H6("Process Steps"),
                html.P("Build the step-by-step process for making this media", className="text-muted small"),

                # Steps container
                html.Div(id="recipe-steps-container", children=[]),

                dbc.Button(
                    [html.I(className="fas fa-plus me-2"), "Add Step"],
                    id="add-recipe-step-btn",
                    color="success",
                    outline=True,
                    size="sm",
                    className="mt-2"
                ),
            ], style={'maxHeight': '75vh', 'overflowY': 'auto', 'padding': '3rem', 'paddingBottom': '100px'}),
            dbc.ModalFooter([
                html.Div([
                    html.Small(id="save-recipe-note", className="text-muted me-3", style={'fontStyle': 'italic'})
                ], style={'marginRight': 'auto'}),
                dbc.Button("Cancel", id="cancel-recipe-btn", color="secondary", outline=True, className="me-2"),
                dbc.Button([html.I(className="fas fa-save me-2"), "Update Recipe"],
                          id="update-recipe-btn", color="warning", className="me-2",
                          style={'display': 'none'}),  # Hidden by default, shown when editing
                dbc.Button([html.I(className="fas fa-save me-2"), "Save as New Version"],
                          id="save-recipe-btn", color="primary"),
            ])
        ], id="recipe-modal", is_open=False, backdrop="static", fullscreen=True)
    )

    # SEPARATE View/Edit Recipe Modal (NO CONFLICTS!)
    modals.append(
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle([
                html.I(className="fas fa-book me-2"),
                html.Span("View Recipe", id="view-recipe-modal-title")
            ])),
            dbc.ModalBody([
                # Recipe Info Section
                dbc.Card([
                    dbc.CardHeader(html.H6("Recipe Information", className="mb-0")),
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Strong("Recipe ID: "),
                                html.Span(id="view-recipe-id-display")
                            ], width=3),
                            dbc.Col([
                                html.Strong("Recipe Name: "),
                                html.Span(id="view-recipe-name-display")
                            ], width=5),
                            dbc.Col([
                                html.Strong("Version: "),
                                html.Span(id="view-recipe-version-display")
                            ], width=2),
                            dbc.Col([
                                html.Strong("Type: "),
                                html.Span(id="view-recipe-type-display")
                            ], width=2),
                        ], className="mb-2"),
                        dbc.Row([
                            dbc.Col([
                                html.Strong("Base Volume: "),
                                html.Span(id="view-recipe-volume-display")
                            ], width=2),
                            dbc.Col([
                                html.Strong("Target pH: "),
                                html.Span(id="view-recipe-ph-display")
                            ], width=2),
                            dbc.Col([
                                html.Strong("Target Osm: "),
                                html.Span(id="view-recipe-osm-display")
                            ], width=2),
                            dbc.Col([
                                html.Strong("Storage: "),
                                html.Span(id="view-recipe-storage-display")
                            ], width=3),
                            dbc.Col([
                                html.Strong("Shelf Life: "),
                                html.Span(id="view-recipe-shelf-display")
                            ], width=3),
                        ])
                    ])
                ], className="mb-3"),

                # Process Steps Section - SIMPLE DIV CONTAINER
                html.Div(id="view-recipe-steps-display")

            ], style={'maxHeight': '75vh', 'overflowY': 'auto', 'padding': '2rem'}),
            dbc.ModalFooter([
                dbc.Button("Close", id="close-view-recipe-btn", color="secondary", outline=True)
            ])
        ], id="view-recipe-modal", is_open=False, backdrop="static", size="xl")
    )

    # View/Edit Media Prep Details Modal
    modals.append(
        dbc.Modal([
            dbc.ModalHeader(dbc.ModalTitle([
                html.I(className="fas fa-eye me-2"),
                "Media Preparation Details"
            ])),
            dbc.ModalBody([
                html.Div(id="view-media-content", style={"padding": "2rem"})
            ], id="printable-media-details"),
            dbc.ModalFooter([
                dbc.Button([html.I(className="fas fa-print me-2"), "Print"],
                          id="print-media-btn", color="primary", outline=True, className="me-2"),
                dbc.Button("Close", id="close-view-modal-btn", color="secondary"),
            ])
        ], id="view-media-modal", is_open=False, size="xl", scrollable=True)
    )

    return modals

# Main Layout
app.layout = dbc.Container([
    dcc.Store(id="step-counter-store", data={'counter': 0}),
    dcc.Store(id="refresh-trigger-store"),
    dcc.Store(id="calculated-targets-store"),
    dcc.Store(id="copied-recipe-id-store"),  # Store original recipe ID when copying
    dcc.Store(id="edit-recipe-data-store"),  # Store recipe step data when editing

    # Header
    dbc.Row([
        dbc.Col([
            html.H1([
                html.I(className="fas fa-flask text-primary me-3"),
                "USP Media Tracking System"
            ], className="mb-3"),
            html.P("Complete media preparation with component library and process-based recipes",
                   className="lead text-muted")
        ], width=12),
    ], className="mb-4"),

    # Modals (rendered once, not dependent on callbacks)
    html.Div(get_all_modals()),

    # Tabs with pre-rendered content
    dbc.Tabs([
        dbc.Tab(label="Media Preparations", tab_id="prep-tab", children=[
            dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col([
                            html.H5([html.I(className="fas fa-list me-2"), "Media Preparations"],
                                   className="mb-0")
                        ], width="auto"),
                        dbc.Col([
                            dbc.ButtonGroup([
                                dbc.Button(
                                    [html.I(className="fas fa-save me-2"), "Save Status Changes"],
                                    id="save-media-status-btn",
                                    color="primary",
                                    size="sm",
                                    className="me-2"
                                ),
                                dbc.Button(
                                    [html.I(className="fas fa-plus me-2"), "New Media Prep"],
                                    id="open-prep-modal-btn",
                                    color="success",
                                    size="sm"
                                )
                            ])
                        ], width="auto", className="ms-auto")
                    ])
                ]),
                dbc.CardBody([
                    html.Div(id="media-table-container")
                ])
            ], className="mt-4")
        ]),

        dbc.Tab(label="Recipe Management", tab_id="recipe-tab", children=[
            dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col([
                            html.H5([html.I(className="fas fa-book me-2"), "Recipe Library"],
                                   className="mb-0")
                        ], width="auto"),
                        dbc.Col([
                            dbc.Button(
                                [html.I(className="fas fa-plus me-2"), "New Recipe"],
                                id="open-recipe-modal-btn",
                                color="primary",
                                size="sm"
                            )
                        ], width="auto", className="ms-auto")
                    ])
                ]),
                dbc.CardBody([
                    html.Div(id="recipe-table-container")
                ])
            ], className="mt-4")
        ]),

        dbc.Tab(label="Component Library", tab_id="component-tab", children=[
            dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col([
                            html.H5([html.I(className="fas fa-flask me-2"), "Component Library"],
                                   className="mb-0")
                        ], width="auto"),
                        dbc.Col([
                            dbc.Button(
                                [html.I(className="fas fa-plus me-2"), "New Component"],
                                id="open-component-modal-btn",
                                color="info",
                                size="sm"
                            )
                        ], width="auto", className="ms-auto")
                    ])
                ]),
                dbc.CardBody([
                    dash_table.DataTable(
                        id="component-table",
                        data=get_all_components(),
                        columns=[
                            {'name': 'Type', 'id': 'component_type'},
                            {'name': 'Component Name', 'id': 'component_name'},
                            {'name': 'Catalog #', 'id': 'catalog_number'},
                            {'name': 'Vendor', 'id': 'vendor'},
                            {'name': 'Typical Units', 'id': 'typical_units'},
                            {'name': 'Storage', 'id': 'storage'},
                        ],
                        style_cell={'textAlign': 'left', 'fontSize': '12px', 'padding': '8px'},
                        style_header={'backgroundColor': 'rgb(230, 230, 230)', 'fontWeight': 'bold'},
                        style_data_conditional=[
                            {'if': {'row_index': 'odd'}, 'backgroundColor': 'rgb(248, 248, 248)'}
                        ],
                        page_size=15,
                        sort_action="native",
                        filter_action="native",
                    )
                ])
            ], className="mt-4")
        ]),
    ], id="main-tabs", active_tab="prep-tab"),

    # Alerts
    html.Div(id="alerts-container")

], fluid=True, className="p-4")

# Media Prep Modal Callbacks
@app.callback(
    [Output("prep-modal", "is_open"),
     Output("prep-media-id-input", "value"),
     Output("prep-recipe-dropdown", "options"),
     Output("prep-experiment-dropdown", "options")],
    [Input("open-prep-modal-btn", "n_clicks"),
     Input("cancel-prep-btn", "n_clicks"),
     Input("save-prep-btn", "n_clicks")],
    State("prep-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_prep_modal(open_clicks, cancel_clicks, save_clicks, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open, no_update, no_update, no_update

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == "open-prep-modal-btn":
        return True, generate_media_id(), get_recipe_options(), get_experiment_options()
    elif trigger_id in ["cancel-prep-btn", "save-prep-btn"]:
        return False, "", [], []

    return is_open, no_update, no_update, no_update

# Render Media Table with Status Dropdowns
@app.callback(
    Output("media-table-container", "children"),
    [Input("save-media-status-btn", "n_clicks"),
     Input("save-prep-btn", "n_clicks")],
    prevent_initial_call=False
)
def render_media_table(save_clicks, prep_save_clicks):
    """Render media preparations table with status dropdowns and color coding"""

    from datetime import date
    today = date.today()

    media_preps = USPMediaPrep.objects.all().select_related('experiment', 'recipe').prefetch_related('components').order_by('-media_id')

    table_rows = []
    for prep in media_preps:
        components = prep.components.all()
        component_count = components.count()

        # Determine row color based on status and expiration
        if not prep.is_used_up and prep.expiration_date and prep.expiration_date > today:
            row_style = {'backgroundColor': '#d4edda'}  # Light green - Available
        elif prep.expiration_date and prep.expiration_date <= today:
            row_style = {'backgroundColor': '#f8d7da'}  # Light red - Expired
        elif prep.is_used_up:
            row_style = {'backgroundColor': '#e2e3e5'}  # Light gray - Used up
        else:
            row_style = {}

        # Create status dropdown
        status_dropdown = dbc.Select(
            id={'type': 'media-status-dropdown', 'index': prep.id},
            options=[
                {'label': 'Available', 'value': 'available'},
                {'label': 'Used Up', 'value': 'used_up'},
            ],
            value='available' if not prep.is_used_up else 'used_up',
            size='sm'
        )

        # Create row (View button moved to left)
        row = html.Tr([
            html.Td([
                dbc.Button("View", size="sm", color="info",
                          id={'type': 'view-media-btn', 'index': prep.id})
            ]),
            html.Td(prep.media_id),
            html.Td(prep.media_name),
            html.Td(prep.media_type),
            html.Td(prep.recipe.recipe_name if prep.recipe else 'Manual'),
            html.Td(f"{prep.batch_size} L"),
            html.Td(prep.preparation_date.strftime('%Y-%m-%d') if prep.preparation_date else ''),
            html.Td(prep.expiration_date.strftime('%Y-%m-%d') if prep.expiration_date else ''),
            html.Td(status_dropdown),
            html.Td(prep.prepared_by),
            html.Td(prep.experiment.experiment_id if prep.experiment else 'Not linked'),
            html.Td(str(component_count)),
            html.Td(str(prep.ph_actual) if prep.ph_actual else ''),
            html.Td(str(prep.osmolality_actual) if prep.osmolality_actual else ''),
            html.Td('✓' if prep.sterility_check else '✗'),
        ], style=row_style)
        table_rows.append(row)

    # Build table
    table = html.Table(
        className="table table-sm table-hover table-striped",
        children=[
            html.Thead([
                html.Tr([
                    html.Th("Actions"),
                    html.Th("Media ID"),
                    html.Th("Name"),
                    html.Th("Type"),
                    html.Th("Recipe"),
                    html.Th("Batch Size"),
                    html.Th("Prep Date"),
                    html.Th("Exp Date"),
                    html.Th("Status"),
                    html.Th("Prepared By"),
                    html.Th("Experiment"),
                    html.Th("# Comp"),
                    html.Th("pH"),
                    html.Th("Osm"),
                    html.Th("Sterile"),
                ], style={'position': 'sticky', 'top': '0', 'backgroundColor': '#f8f9fa', 'zIndex': '10'})
            ]),
            html.Tbody(table_rows)
        ],
        style={'fontSize': '0.9rem'}
    )

    return table

# Render Recipe Table
@app.callback(
    Output("recipe-table-container", "children"),
    Input("save-recipe-btn", "n_clicks"),
    prevent_initial_call=False
)
def render_recipe_table(save_clicks):
    """Render recipe table with pattern-matching buttons"""

    recipes = USPMediaRecipe.objects.filter(active=True).prefetch_related('process_steps').order_by('-recipe_id')

    table_rows = []
    for recipe in recipes:
        steps = recipe.process_steps.all()
        step_count = steps.count()

        # Create action button - View opens the editable modal
        view_btn = dbc.Button("View", size="sm", color="info",
                             id={'type': 'view-recipe-btn', 'index': recipe.id})

        row = html.Tr([
            html.Td([view_btn]),
            html.Td(recipe.recipe_id),
            html.Td(recipe.recipe_name),
            html.Td(recipe.recipe_type),
            html.Td(recipe.version),
            html.Td(f"{recipe.base_volume} L"),
            html.Td(str(recipe.ph_target) if recipe.ph_target else ''),
            html.Td(str(recipe.osmolality_target) if recipe.osmolality_target else ''),
            html.Td(str(step_count)),
            html.Td(recipe.storage_temp or ''),
            html.Td(f"{recipe.shelf_life_days} days" if recipe.shelf_life_days else ''),
            html.Td(recipe.created_date.strftime('%Y-%m-%d') if recipe.created_date else ''),
        ])
        table_rows.append(row)

    # Build table
    table = html.Table(
        className="table table-sm table-hover table-striped",
        children=[
            html.Thead([
                html.Tr([
                    html.Th("Actions"),
                    html.Th("Recipe ID"),
                    html.Th("Recipe Name"),
                    html.Th("Type"),
                    html.Th("Version"),
                    html.Th("Base Vol"),
                    html.Th("pH Target"),
                    html.Th("Osm Target"),
                    html.Th("# Steps"),
                    html.Th("Storage"),
                    html.Th("Shelf Life"),
                    html.Th("Created"),
                ], style={'position': 'sticky', 'top': '0', 'backgroundColor': '#f8f9fa', 'zIndex': '10'})
            ]),
            html.Tbody(table_rows)
        ],
        style={'fontSize': '0.9rem'}
    )

    return table

# Save Media Status Changes
@app.callback(
    Output("alerts-container", "children", allow_duplicate=True),
    Input("save-media-status-btn", "n_clicks"),
    [State({'type': 'media-status-dropdown', 'index': ALL}, 'value'),
     State({'type': 'media-status-dropdown', 'index': ALL}, 'id')],
    prevent_initial_call=True
)
def save_media_status_changes(n_clicks, status_values, dropdown_ids):
    """Save status changes for all media preps"""
    if not n_clicks:
        return no_update

    try:
        from datetime import date
        updated_count = 0

        for status_value, dropdown_id in zip(status_values, dropdown_ids):
            media_prep_id = dropdown_id['index']
            is_used_up = (status_value == 'used_up')

            prep = USPMediaPrep.objects.get(id=media_prep_id)

            # Update status
            if prep.is_used_up != is_used_up:
                prep.is_used_up = is_used_up
                if is_used_up and not prep.date_used_up:
                    prep.date_used_up = date.today()
                elif not is_used_up:
                    prep.date_used_up = None
                prep.save()
                updated_count += 1

        if updated_count > 0:
            alert = dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Successfully updated status for {updated_count} media prep(s)!"
            ], color="success", dismissable=True, duration=4000)
        else:
            alert = dbc.Alert([
                html.I(className="fas fa-info-circle me-2"),
                "No changes to save."
            ], color="info", dismissable=True, duration=3000)

        return alert

    except Exception as e:
        alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error saving status: {str(e)}"
        ], color="danger", dismissable=True)
        return alert

# View Media Prep Details Modal - Simplified with direct pattern matching
@app.callback(
    [Output("view-media-modal", "is_open"),
     Output("view-media-content", "children")],
    Input({'type': 'view-media-btn', 'index': ALL}, 'n_clicks'),
    [State("view-media-modal", "is_open"),
     State({'type': 'view-media-btn', 'index': ALL}, 'id')],
    prevent_initial_call=True
)
def open_view_media_modal(view_clicks, is_open, button_ids):
    """Open view modal and populate with media prep details"""
    ctx = dash.callback_context

    if not ctx.triggered or not view_clicks or not any(view_clicks):
        return no_update, no_update

    # Check if this is a real click (not just a re-render)
    if ctx.triggered[0]['value'] is None:
        print("DEBUG open_view_media_modal: Returning no_update - value is None (re-render, not a click)")
        return no_update, no_update

    # Get the clicked button's index directly from context
    trigger = ctx.triggered[0]['prop_id']
    if '.' not in trigger:
        return no_update, no_update

    trigger_id = trigger.split('.')[0]

    try:
        media_prep_id = eval(trigger_id)['index']
        print(f"DEBUG: Opening media prep details, media_prep_id={media_prep_id}")

        prep = USPMediaPrep.objects.select_related('recipe', 'experiment').prefetch_related('components').get(id=media_prep_id)

        # Get scaled process if recipe exists
        if prep.recipe:
            scaled_steps, scaling_factor = calculate_scaled_process(prep.recipe.id, prep.batch_size)
        else:
            scaled_steps = []
            scaling_factor = 1.0

        # Build process steps table if we have a recipe
        process_table = None
        if scaled_steps:
            table_rows = []
            for step in scaled_steps:
                step_type = step['step_type']

                # Find matching component data from prep
                if step_type == 'add_component' and step.get('component_name'):
                    # Find the actual component from the prep
                    matching_comp = None
                    for comp in prep.components.all():
                        if comp.component_name == step.get('component_name'):
                            matching_comp = comp
                            break

                    row = html.Tr([
                        html.Td(step.get('component_name', 'N/A'), style={'fontWeight': '500'}),
                        html.Td(f"{step.get('target_amount', 0)} {step.get('unit', '')}",
                               style={'textAlign': 'right', 'color': '#28a745', 'fontWeight': '600'}),
                        html.Td(f"{matching_comp.actual_amount:.2f} {matching_comp.unit}" if matching_comp else '—',
                               style={'textAlign': 'right', 'fontWeight': '600'}),
                        html.Td(matching_comp.lot_number if matching_comp and matching_comp.lot_number else '—'),
                        html.Td(step.get('catalog_number', ''), style={'fontSize': '0.85rem', 'color': '#6c757d'}),
                        html.Td(step.get('instructions', ''), style={'fontSize': '0.85rem', 'color': '#6c757d'}),
                    ])

                elif step_type == 'initial_water_fill':
                    row = html.Tr([
                        html.Td(f"Initial MilliQ Water ({step.get('percentage', 80)}% Batch Weight)",
                               style={'fontWeight': '500'}),
                        html.Td(f"{step.get('water_volume', 0)} mL",
                               style={'textAlign': 'right', 'color': '#17a2b8', 'fontWeight': '600'}),
                        html.Td('—', style={'textAlign': 'right'}),
                        html.Td('—'),
                        html.Td('—'),
                        html.Td(step.get('instructions', ''), style={'fontSize': '0.85rem', 'color': '#6c757d'}),
                    ])

                elif step_type == 'final_water_fill':
                    row = html.Tr([
                        html.Td("Add MilliQ to Target Mass", style={'fontWeight': '500'}),
                        html.Td(f"{step.get('water_volume', 0)} mL",
                               style={'textAlign': 'right', 'color': '#17a2b8', 'fontWeight': '600'}),
                        html.Td('—', style={'textAlign': 'right'}),
                        html.Td('—'),
                        html.Td('—'),
                        html.Td(step.get('instructions', ''), style={'fontSize': '0.85rem', 'color': '#6c757d'}),
                    ])

                elif step_type == 'add_water':
                    row = html.Tr([
                        html.Td("Add MilliQ Water", style={'fontWeight': '500'}),
                        html.Td(f"{step.get('water_volume', 0)} mL",
                               style={'textAlign': 'right', 'color': '#17a2b8', 'fontWeight': '600'}),
                        html.Td('—', style={'textAlign': 'right'}),
                        html.Td('—'),
                        html.Td('—'),
                        html.Td(step.get('instructions', ''), style={'fontSize': '0.85rem', 'color': '#6c757d'}),
                    ])

                elif step_type in ['measure_ph', 'adjust_ph']:
                    target = step.get('target_ph', step.get('instructions', ''))
                    actual_ph = str(prep.ph_actual) if prep.ph_actual else '—'

                    # For adjust_ph, look for pH adjustment components
                    ph_adjustment = ''
                    if step_type == 'adjust_ph':
                        for comp in prep.components.all():
                            if comp.notes and 'pH adjustment' in comp.notes:
                                ph_adjustment = f"{comp.component_name}: {comp.actual_amount} {comp.unit}"
                                if comp.lot_number:
                                    ph_adjustment += f" (Lot: {comp.lot_number})"

                    row = html.Tr([
                        html.Td(step['step_type_display'], style={'fontWeight': '500'}),
                        html.Td(f"Target: {target}", style={'textAlign': 'right', 'color': '#ffc107', 'fontWeight': '600'}),
                        html.Td(f"Measured: {actual_ph}" if step_type == 'measure_ph' else ph_adjustment,
                               style={'textAlign': 'right', 'fontWeight': '600'}),
                        html.Td('—'),
                        html.Td('—'),
                        html.Td(step.get('instructions', ''), style={'fontSize': '0.85rem', 'color': '#6c757d'}),
                    ])

                elif step_type in ['measure_osmolality', 'adjust_osmolality']:
                    target = step.get('target_osmolality', step.get('instructions', ''))
                    actual_osm = str(prep.osmolality_actual) if prep.osmolality_actual else '—'

                    # For adjust_osmolality, look for osmolality adjustment components
                    osm_adjustment = ''
                    if step_type == 'adjust_osmolality':
                        for comp in prep.components.all():
                            if comp.notes and 'Osmolality adjustment' in comp.notes:
                                osm_adjustment = f"{comp.component_name}: {comp.actual_amount} {comp.unit}"
                                if comp.lot_number:
                                    osm_adjustment += f" (Lot: {comp.lot_number})"

                    row = html.Tr([
                        html.Td(step['step_type_display'], style={'fontWeight': '500'}),
                        html.Td(f"Target: {target}", style={'textAlign': 'right', 'color': '#ffc107', 'fontWeight': '600'}),
                        html.Td(f"Measured: {actual_osm}" if step_type == 'measure_osmolality' else osm_adjustment,
                               style={'textAlign': 'right', 'fontWeight': '600'}),
                        html.Td('—'),
                        html.Td('—'),
                        html.Td(step.get('instructions', ''), style={'fontSize': '0.85rem', 'color': '#6c757d'}),
                    ])

                elif step_type in ['stir', 'heat', 'cool']:
                    details = []
                    if step.get('duration_minutes'):
                        details.append(f"{step['duration_minutes']} minutes")
                    if step.get('temperature'):
                        details.append(f"{step['temperature']}°C")
                    detail_text = ", ".join(details) if details else "—"

                    row = html.Tr([
                        html.Td(step['step_type_display'], style={'fontWeight': '500'}),
                        html.Td(detail_text, style={'textAlign': 'right', 'color': '#6c757d'}),
                        html.Td('—', style={'textAlign': 'right'}),
                        html.Td('—'),
                        html.Td('—'),
                        html.Td(step.get('instructions', ''), style={'fontSize': '0.85rem', 'color': '#6c757d'}),
                    ])

                else:
                    # Generic step (filter, autoclave, aliquot, note, etc.)
                    row = html.Tr([
                        html.Td(step['step_type_display'], style={'fontWeight': '500'}),
                        html.Td('—'),
                        html.Td('—', style={'textAlign': 'right'}),
                        html.Td('—'),
                        html.Td('—'),
                        html.Td(step.get('instructions', ''), style={'fontSize': '0.85rem', 'color': '#6c757d'}),
                    ])

                table_rows.append(row)

            process_table = dbc.Table([
                html.Thead([
                    html.Tr([
                        html.Th("Step Description", style={'width': '25%', 'backgroundColor': '#f8f9fa'}),
                        html.Th("Target Amount", style={'width': '15%', 'textAlign': 'right', 'backgroundColor': '#f8f9fa'}),
                        html.Th("Measured Amount", style={'width': '15%', 'textAlign': 'right', 'backgroundColor': '#f8f9fa'}),
                        html.Th("Lot Number", style={'width': '15%', 'backgroundColor': '#f8f9fa'}),
                        html.Th("Catalog #", style={'width': '12%', 'backgroundColor': '#f8f9fa'}),
                        html.Th("Notes", style={'width': '18%', 'backgroundColor': '#f8f9fa'}),
                    ])
                ], style={'position': 'sticky', 'top': '0', 'zIndex': '10'}),
                html.Tbody(table_rows)
            ], bordered=True, hover=True, responsive=True, striped=True,
               style={'fontSize': '0.9rem', 'marginBottom': '0'})

        # Build detailed view matching prep modal form exactly
        details = html.Div([
            # Step 1: Recipe and Batch Volume (matching prep modal)
            dbc.Card([
                dbc.CardHeader([html.H6("Step 1: Select Recipe and Batch Volume", className="mb-0")]),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Select Recipe *"),
                            dbc.Input(value=prep.recipe.recipe_name if prep.recipe else 'Manual', disabled=True),
                        ], width=8),
                        dbc.Col([
                            dbc.Label("Batch Volume (L) *"),
                            dbc.Input(value=f"{prep.batch_size}", disabled=True),
                        ], width=4),
                    ]),
                ])
            ], className="mb-3"),

            # Step 2: Review Scaled Process (matching prep modal step 2)
            dbc.Card([
                dbc.CardHeader([html.H6("Step 2: Review Scaled Process & Enter Actual Amounts", className="mb-0")]),
                dbc.CardBody([
                    process_table if process_table else html.P("No recipe steps available", className="text-muted")
                ])
            ], className="mb-3"),

            # Step 3: Preparation Details (matching prep modal step 3)
            dbc.Card([
                dbc.CardHeader([html.H6("Step 3: Preparation Details", className="mb-0")]),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Media ID"),
                            dbc.Input(value=prep.media_id, disabled=True),
                        ], width=3),
                        dbc.Col([
                            dbc.Label("Preparation Date *"),
                            dbc.Input(value=prep.preparation_date.strftime('%Y-%m-%d') if prep.preparation_date else '', disabled=True),
                        ], width=3),
                        dbc.Col([
                            dbc.Label("Prepared By *"),
                            dbc.Input(value=prep.prepared_by, disabled=True),
                        ], width=3),
                        dbc.Col([
                            dbc.Label("Link to Experiment"),
                            dbc.Input(value=prep.experiment.experiment_id if prep.experiment else 'Not linked', disabled=True),
                        ], width=3),
                    ], className="mb-3"),
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("pH (Actual)"),
                            dbc.Input(value=str(prep.ph_actual) if prep.ph_actual else '', disabled=True),
                        ], width=3),
                        dbc.Col([
                            dbc.Label("Osmolality (Actual)"),
                            dbc.Input(value=str(prep.osmolality_actual) if prep.osmolality_actual else '', disabled=True),
                        ], width=3),
                        dbc.Col([
                            dbc.Label("Storage Location"),
                            dbc.Input(value=prep.storage_location or '', disabled=True),
                        ], width=3),
                        dbc.Col([
                            dbc.Label("Sterility Check"),
                            dbc.Input(value='Passed' if prep.sterility_check else 'Not checked', disabled=True),
                        ], width=3),
                    ]),
                ])
            ]),
        ])

        return True, details

    except USPMediaPrep.DoesNotExist:
        error_msg = dbc.Alert("Media preparation not found.", color="danger")
        return True, error_msg
    except Exception as e:
        print(f"Error in open_view_media_modal: {e}")
        return no_update, no_update

# Close View Media Prep Modal
@app.callback(
    Output("view-media-modal", "is_open", allow_duplicate=True),
    Input("close-view-modal-btn", "n_clicks"),
    prevent_initial_call=True
)
def close_view_media_modal(n_clicks):
    """Close the view media prep modal"""
    if n_clicks:
        return False
    return no_update

# Print Media Prep Details (Clientside)
app.clientside_callback(
    """
    function(n_clicks) {
        if (n_clicks) {
            // Get the content to print
            var printContent = document.getElementById('view-media-content');

            if (!printContent) {
                console.error('Print content not found');
                return window.dash_clientside.no_update;
            }

            // Clone the content
            var clonedContent = printContent.cloneNode(true);

            // Fix input values - copy value attributes for disabled inputs
            var originalInputs = printContent.querySelectorAll('input, textarea');
            var clonedInputs = clonedContent.querySelectorAll('input, textarea');

            for (var i = 0; i < originalInputs.length; i++) {
                if (originalInputs[i].value) {
                    clonedInputs[i].setAttribute('value', originalInputs[i].value);
                    // For textareas, set the text content
                    if (originalInputs[i].tagName === 'TEXTAREA') {
                        clonedInputs[i].textContent = originalInputs[i].value;
                    }
                }
            }

            // Create a new window for printing
            var printWindow = window.open('', '_blank', 'width=800,height=600');

            // Write the content to the new window
            printWindow.document.write('<html><head><title>Media Preparation Details</title>');

            // Copy all stylesheets
            var styles = document.getElementsByTagName('style');
            for (var i = 0; i < styles.length; i++) {
                printWindow.document.write(styles[i].outerHTML);
            }

            var links = document.getElementsByTagName('link');
            for (var i = 0; i < links.length; i++) {
                if (links[i].rel === 'stylesheet') {
                    printWindow.document.write(links[i].outerHTML);
                }
            }

            // Add Bootstrap CSS directly
            printWindow.document.write('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css">');

            printWindow.document.write('</head><body style="padding: 20px;">');
            printWindow.document.write(clonedContent.innerHTML);
            printWindow.document.write('</body></html>');

            printWindow.document.close();

            // Wait for content to load, then print
            printWindow.onload = function() {
                setTimeout(function() {
                    printWindow.print();
                    printWindow.close();
                }, 250);
            };
        }
        return window.dash_clientside.no_update;
    }
    """,
    Output("print-media-btn", "n_clicks"),
    Input("print-media-btn", "n_clicks"),
    prevent_initial_call=True
)

@app.callback(
    Output("scaled-process-container", "children"),
    Input("calculate-scaled-amounts-btn", "n_clicks"),
    [State("prep-recipe-dropdown", "value"),
     State("prep-batch-volume-input", "value")],
    prevent_initial_call=True
)
def display_scaled_process(n_clicks, recipe_id, batch_volume):
    """Calculate and display scaled process in clean table format"""
    if not recipe_id or not batch_volume:
        return dbc.Alert("Please select a recipe and enter batch volume", color="warning")

    scaled_steps, scaling_factor = calculate_scaled_process(recipe_id, batch_volume)

    if not scaled_steps:
        return dbc.Alert("No steps found for this recipe", color="info")

    try:
        recipe = USPMediaRecipe.objects.get(id=recipe_id)
        recipe_info = dbc.Alert([
            html.H6(f"Recipe: {recipe.recipe_name} v{recipe.version}", className="mb-2"),
            html.P(f"Scaling: {recipe.base_volume}L → {batch_volume}L (×{scaling_factor:.2f})", className="mb-0")
        ], color="info")
    except:
        recipe_info = html.Div()

    # Build table rows for each step
    table_rows = []
    component_index = 0  # Track components separately for indexing

    for step_num, step in enumerate(scaled_steps):
        step_type = step['step_type']

        # Different row layouts based on step type
        if step_type == 'add_component' and step.get('component_name'):
            # Component row with all details
            row = html.Tr([
                html.Td(step.get('component_name', 'N/A'), style={'fontWeight': '500'}),
                html.Td(f"{step.get('target_amount', 0)} {step.get('unit', '')}",
                       style={'textAlign': 'right', 'color': '#28a745', 'fontWeight': '600'}),
                html.Td([
                    dbc.InputGroup([
                        dbc.Input(
                            id={'type': 'component-actual-amount', 'index': component_index},
                            type="number",
                            value=step.get('target_amount', 0),
                            step="any",
                            style={'textAlign': 'right'}
                        ),
                        dbc.InputGroupText(step.get('unit', ''), style={'fontSize': '0.85rem'})
                    ], size="sm")
                ], style={'minWidth': '140px'}),
                html.Td([
                    dbc.Input(
                        id={'type': 'component-lot-number', 'index': component_index},
                        placeholder="Enter lot #",
                        size="sm"
                    )
                ], style={'minWidth': '150px'}),
                html.Td(step.get('catalog_number', ''),
                       style={'fontSize': '0.85rem', 'color': '#6c757d'}),
                html.Td(step.get('instructions', ''),
                       style={'fontSize': '0.85rem', 'color': '#6c757d'}),
                # Hidden metadata
                html.Td([
                    html.Div(
                        id={'type': 'component-metadata', 'index': component_index},
                        **{'data-component-id': step.get('component_id', ''),
                           'data-component-name': step.get('component_name', ''),
                           'data-catalog-number': step.get('catalog_number', ''),
                           'data-vendor': step.get('vendor', ''),
                           'data-target-amount': step.get('target_amount', 0),
                           'data-unit': step.get('unit', '')},
                        style={'display': 'none'}
                    )
                ], style={'display': 'none'})
            ])
            component_index += 1

        elif step_type == 'initial_water_fill':
            # Water fill step
            row = html.Tr([
                html.Td(f"Initial MilliQ Water ({step.get('percentage', 80)}% Batch Weight)",
                       style={'fontWeight': '500'}),
                html.Td(f"{step.get('water_volume', 0)} mL",
                       style={'textAlign': 'right', 'color': '#17a2b8', 'fontWeight': '600'}),
                html.Td([
                    dbc.InputGroup([
                        dbc.Input(
                            type="number",
                            value=step.get('water_volume', 0),
                            step="any",
                            size="sm",
                            style={'textAlign': 'right'}
                        ),
                        dbc.InputGroupText('mL', style={'fontSize': '0.85rem'})
                    ], size="sm")
                ], style={'minWidth': '140px'}),
                html.Td('—'),
                html.Td('—'),
                html.Td(step.get('instructions', ''), style={'fontSize': '0.85rem', 'color': '#6c757d'}),
            ])

        elif step_type == 'final_water_fill':
            row = html.Tr([
                html.Td("Add MilliQ to Target Mass", style={'fontWeight': '500'}),
                html.Td(f"{step.get('water_volume', 0)} mL",
                       style={'textAlign': 'right', 'color': '#17a2b8', 'fontWeight': '600'}),
                html.Td([
                    dbc.InputGroup([
                        dbc.Input(
                            type="number",
                            value=step.get('water_volume', 0),
                            step="any",
                            size="sm",
                            style={'textAlign': 'right'}
                        ),
                        dbc.InputGroupText('mL', style={'fontSize': '0.85rem'})
                    ], size="sm")
                ], style={'minWidth': '140px'}),
                html.Td('—'),
                html.Td('—'),
                html.Td(step.get('instructions', ''), style={'fontSize': '0.85rem', 'color': '#6c757d'}),
            ])

        elif step_type == 'add_water':
            row = html.Tr([
                html.Td("Add MilliQ Water", style={'fontWeight': '500'}),
                html.Td(f"{step.get('water_volume', 0)} mL",
                       style={'textAlign': 'right', 'color': '#17a2b8', 'fontWeight': '600'}),
                html.Td([
                    dbc.InputGroup([
                        dbc.Input(
                            type="number",
                            value=step.get('water_volume', 0),
                            step="any",
                            size="sm",
                            style={'textAlign': 'right'}
                        ),
                        dbc.InputGroupText('mL', style={'fontSize': '0.85rem'})
                    ], size="sm")
                ], style={'minWidth': '140px'}),
                html.Td('—'),
                html.Td('—'),
                html.Td(step.get('instructions', ''), style={'fontSize': '0.85rem', 'color': '#6c757d'}),
            ])

        elif step_type in ['measure_ph', 'adjust_ph']:
            target = step.get('target_ph', step.get('instructions', ''))

            if step_type == 'adjust_ph':
                # For pH adjustment, provide inputs for titrant and amount
                # Use dbc.Select instead of dcc.Dropdown for better table rendering
                titrant_options = get_component_options_by_type('acid') + get_component_options_by_type('base')
                row = html.Tr([
                    html.Td(step['step_type_display'], style={'fontWeight': '500'}),
                    html.Td(f"Target: {target}", style={'textAlign': 'right', 'color': '#ffc107', 'fontWeight': '600'}),
                    html.Td([
                        dbc.Select(
                            id={'type': 'adjust-ph-titrant', 'index': step_num},
                            options=titrant_options,
                            placeholder="Select titrant...",
                            size="sm",
                            className="mb-1"
                        ),
                        dbc.InputGroup([
                            dbc.Input(
                                type="number",
                                id={'type': 'adjust-ph-amount', 'index': step_num},
                                placeholder="Amount (mL)",
                                step="0.1",
                                size="sm",
                                style={'textAlign': 'right'}
                            ),
                            dbc.InputGroupText('mL', style={'fontSize': '0.75rem'})
                        ], size="sm")
                    ], style={'minWidth': '180px'}),
                    html.Td([
                        dbc.Input(
                            type="text",
                            id={'type': 'adjust-ph-lot', 'index': step_num},
                            placeholder="Lot #",
                            size="sm"
                        )
                    ]),
                    html.Td('—', style={'fontSize': '0.85rem', 'color': '#6c757d'}),
                    html.Td([
                        dbc.Input(
                            type="number",
                            id={'type': 'actual-ph-prep', 'index': step_num},
                            placeholder="Final pH",
                            step="0.01",
                            size="sm",
                            style={'textAlign': 'right'}
                        )
                    ], style={'fontSize': '0.85rem', 'color': '#6c757d'}),
                ])
            else:
                # For pH measurement only
                row = html.Tr([
                    html.Td(step['step_type_display'], style={'fontWeight': '500'}),
                    html.Td(f"Target: {target}", style={'textAlign': 'right', 'color': '#ffc107', 'fontWeight': '600'}),
                    html.Td([
                        dbc.Input(
                            type="number",
                            id={'type': 'actual-ph-prep', 'index': step_num},
                            placeholder="Measured pH",
                            step="0.01",
                            size="sm",
                            style={'textAlign': 'right'}
                        )
                    ], style={'minWidth': '140px'}),
                    html.Td('—'),
                    html.Td('—'),
                    html.Td(step.get('instructions', ''), style={'fontSize': '0.85rem', 'color': '#6c757d'}),
                ])

        elif step_type in ['measure_osmolality', 'adjust_osmolality']:
            target = step.get('target_osmolality', step.get('instructions', ''))

            if step_type == 'adjust_osmolality':
                # For osmolality adjustment, provide inputs for component and amount
                # Use dbc.Select instead of dcc.Dropdown for better table rendering
                osm_component_options = get_component_options_by_type()
                row = html.Tr([
                    html.Td(step['step_type_display'], style={'fontWeight': '500'}),
                    html.Td(f"Target: {target}", style={'textAlign': 'right', 'color': '#ffc107', 'fontWeight': '600'}),
                    html.Td([
                        dbc.Select(
                            id={'type': 'adjust-osm-component', 'index': step_num},
                            options=osm_component_options,
                            placeholder="Select component...",
                            size="sm",
                            className="mb-1"
                        ),
                        dbc.InputGroup([
                            dbc.Input(
                                type="number",
                                id={'type': 'adjust-osm-amount', 'index': step_num},
                                placeholder="Amount",
                                step="0.1",
                                size="sm",
                                style={'textAlign': 'right'}
                            ),
                            dbc.InputGroupText('g/mL', style={'fontSize': '0.75rem'})
                        ], size="sm")
                    ], style={'minWidth': '180px'}),
                    html.Td([
                        dbc.Input(
                            type="text",
                            id={'type': 'adjust-osm-lot', 'index': step_num},
                            placeholder="Lot #",
                            size="sm"
                        )
                    ]),
                    html.Td('—', style={'fontSize': '0.85rem', 'color': '#6c757d'}),
                    html.Td([
                        dbc.Input(
                            type="number",
                            id={'type': 'actual-osm-prep', 'index': step_num},
                            placeholder="Final Osm",
                            step="1",
                            size="sm",
                            style={'textAlign': 'right'}
                        )
                    ], style={'fontSize': '0.85rem', 'color': '#6c757d'}),
                ])
            else:
                # For osmolality measurement only
                row = html.Tr([
                    html.Td(step['step_type_display'], style={'fontWeight': '500'}),
                    html.Td(f"Target: {target}", style={'textAlign': 'right', 'color': '#ffc107', 'fontWeight': '600'}),
                    html.Td([
                        dbc.Input(
                            type="number",
                            id={'type': 'actual-osm-prep', 'index': step_num},
                            placeholder="Measured value",
                            step="1",
                            size="sm",
                            style={'textAlign': 'right'}
                        )
                    ], style={'minWidth': '140px'}),
                    html.Td('—'),
                    html.Td('—'),
                    html.Td(step.get('instructions', ''), style={'fontSize': '0.85rem', 'color': '#6c757d'}),
                ])

        elif step_type in ['stir', 'heat', 'cool']:
            details = []
            if step.get('duration_minutes'):
                details.append(f"{step['duration_minutes']} minutes")
            if step.get('temperature'):
                details.append(f"{step['temperature']}°C")
            detail_text = ", ".join(details) if details else "—"

            row = html.Tr([
                html.Td(step['step_type_display'], style={'fontWeight': '500'}),
                html.Td(detail_text, style={'textAlign': 'right', 'color': '#6c757d'}),
                html.Td([
                    dbc.Input(
                        type="number",
                        placeholder="Actual time (min)" if step_type == 'stir' else "Actual value",
                        size="sm",
                        style={'textAlign': 'right'}
                    )
                ], style={'minWidth': '140px'}),
                html.Td('—'),
                html.Td('—'),
                html.Td(step.get('instructions', ''), style={'fontSize': '0.85rem', 'color': '#6c757d'}),
            ])

        else:
            # Generic step (filter, autoclave, aliquot, note, etc.)
            row = html.Tr([
                html.Td(step['step_type_display'], style={'fontWeight': '500'}),
                html.Td('—'),
                html.Td('—'),
                html.Td('—'),
                html.Td('—'),
                html.Td(step.get('instructions', ''), style={'fontSize': '0.85rem', 'color': '#6c757d'}),
            ])

        table_rows.append(row)

    # Build the table
    steps_table = dbc.Table([
        html.Thead([
            html.Tr([
                html.Th("Step Description", style={'width': '25%', 'backgroundColor': '#f8f9fa'}),
                html.Th("Target Amount", style={'width': '15%', 'textAlign': 'right', 'backgroundColor': '#f8f9fa'}),
                html.Th("Measured Amount", style={'width': '15%', 'backgroundColor': '#f8f9fa'}),
                html.Th("Lot Number", style={'width': '15%', 'backgroundColor': '#f8f9fa'}),
                html.Th("Catalog #", style={'width': '12%', 'backgroundColor': '#f8f9fa'}),
                html.Th("Notes", style={'width': '18%', 'backgroundColor': '#f8f9fa'}),
            ])
        ], style={'position': 'sticky', 'top': '0', 'zIndex': '10'}),
        html.Tbody(table_rows)
    ], bordered=True, hover=True, responsive=True, striped=True,
       style={'fontSize': '0.9rem', 'marginBottom': '0'})

    return [recipe_info, steps_table]

# Component Modal Callbacks
@app.callback(
    [Output("component-modal", "is_open"),
     Output("new-comp-type", "value"),
     Output("new-comp-name", "value"),
     Output("new-comp-catalog", "value"),
     Output("new-comp-vendor", "value"),
     Output("new-comp-units", "value"),
     Output("new-comp-storage", "value"),
     Output("new-comp-notes", "value")],
    [Input("open-component-modal-btn", "n_clicks"),
     Input("cancel-component-btn", "n_clicks"),
     Input("save-component-btn", "n_clicks")],
    State("component-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_component_modal(open_clicks, cancel_clicks, save_clicks, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open, no_update, no_update, no_update, no_update, no_update, no_update, no_update

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == "open-component-modal-btn":
        # Clear all fields when opening modal
        return True, None, "", "", "", None, "", ""
    elif trigger_id in ["cancel-component-btn", "save-component-btn"]:
        # Clear all fields when closing modal
        return False, None, "", "", "", None, "", ""

    return is_open, no_update, no_update, no_update, no_update, no_update, no_update, no_update

@app.callback(
    [Output("alerts-container", "children", allow_duplicate=True),
     Output("component-table", "data")],
    Input("save-component-btn", "n_clicks"),
    [State("new-comp-type", "value"),
     State("new-comp-name", "value"),
     State("new-comp-catalog", "value"),
     State("new-comp-vendor", "value"),
     State("new-comp-units", "value"),
     State("new-comp-storage", "value"),
     State("new-comp-notes", "value")],
    prevent_initial_call=True
)
def save_component(n_clicks, comp_type, name, catalog, vendor, units, storage, notes):
    if not n_clicks or not comp_type or not name or not units:
        return no_update, no_update

    try:
        USPMediaComponentLibrary.objects.create(
            component_type=comp_type,
            component_name=name,
            catalog_number=catalog if catalog else None,
            vendor=vendor if vendor else None,
            typical_units=units,
            storage_conditions=storage if storage else None,
            notes=notes if notes else None,
            active=True
        )

        alert = dbc.Alert([
            html.I(className="fas fa-check-circle me-2"),
            f"Component '{name}' added successfully!"
        ], color="success", dismissable=True, duration=4000)

        return alert, get_all_components()
    except Exception as e:
        alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error: {str(e)}"
        ], color="danger", dismissable=True)
        return alert, no_update

# Helper function to create recipe step form skeleton
def create_recipe_step_skeleton(step_index, display_step_number, step_type=None):
    """Create a recipe step form row skeleton - step-details will be populated by callback"""

    # Build the complete step row with only step number, type dropdown, and empty details div
    return dbc.Row([
        dbc.Col([
            html.Strong(f"Step {display_step_number}", className="d-flex align-items-center",
                       style={'height': '38px'}),
        ], width="auto", style={'minWidth': '70px'}),
        dbc.Col([
            dcc.Dropdown(
                options=STEP_TYPES,
                value=step_type,  # This will trigger update_step_details callback
                placeholder="Select step type...",
                id={'type': 'step-type', 'index': step_index}
            )
        ], width=3),
        dbc.Col([
            html.Div(id={'type': 'step-details', 'index': step_index})  # Empty - will be populated by callback
        ], width="auto", className="flex-fill"),
        dbc.Col([
            dbc.Button(
                html.I(className="fas fa-trash"),
                id={'type': 'remove-recipe-step', 'index': step_index},
                color="danger",
                size="sm"
            )
        ], width="auto")
    ], className="mb-2 align-items-start", id={'type': 'recipe-step-row', 'index': step_index})

# Recipe Modal Callbacks

# NEW SIMPLE VIEW RECIPE MODAL CALLBACK
@app.callback(
    [Output("view-recipe-modal", "is_open"),
     Output("view-recipe-modal-title", "children"),
     Output("view-recipe-id-display", "children"),
     Output("view-recipe-name-display", "children"),
     Output("view-recipe-version-display", "children"),
     Output("view-recipe-type-display", "children"),
     Output("view-recipe-volume-display", "children"),
     Output("view-recipe-ph-display", "children"),
     Output("view-recipe-osm-display", "children"),
     Output("view-recipe-storage-display", "children"),
     Output("view-recipe-shelf-display", "children"),
     Output("view-recipe-steps-display", "children")],
    [Input({'type': 'view-recipe-btn', 'index': ALL}, 'n_clicks'),
     Input("close-view-recipe-btn", "n_clicks")],
    [State("view-recipe-modal", "is_open"),
     State({'type': 'view-recipe-btn', 'index': ALL}, 'id')],
    prevent_initial_call=True
)
def toggle_view_recipe_modal(view_clicks, close_clicks, is_open, button_ids):
    """Simple modal to view recipe - NO CONFLICTS!"""
    ctx = dash.callback_context

    if not ctx.triggered or ctx.triggered[0]['value'] is None:
        return [no_update] * 12

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == "close-view-recipe-btn":
        # Close the modal
        return [False] + [no_update] * 11

    if 'view-recipe-btn' in trigger_id:
        # Extract recipe ID
        recipe_id = eval(trigger_id)['index']
        print(f"VIEW MODAL: Opening recipe {recipe_id}")

        try:
            recipe = USPMediaRecipe.objects.prefetch_related('process_steps__parameters').get(id=recipe_id)

            # Build steps table in media prep format
            steps = recipe.process_steps.all().order_by('step_number')
            table_rows = []

            for step in steps:
                params = step.get_params()
                step_desc = step.get_step_type_display()

                # Build row based on step type (like media prep does)
                if step.step_type == 'add_component':
                    component = params.get('component_id')
                    if component:
                        amount = params.get('amount_per_liter', 0)
                        unit = params.get('amount_unit', '')

                        row = html.Tr([
                            html.Td(component.component_name, style={'fontWeight': '500'}),
                            html.Td(f"{amount} {unit}/L",
                                   style={'textAlign': 'right', 'color': '#28a745', 'fontWeight': '600'}),
                            html.Td(component.catalog_number or "—",
                                   style={'fontSize': '0.85rem', 'color': '#6c757d'}),
                            html.Td(step.instructions or "—",
                                   style={'fontSize': '0.85rem', 'color': '#6c757d'})
                        ])
                        table_rows.append(row)

                elif step.step_type == 'initial_water_fill':
                    row = html.Tr([
                        html.Td("Initial MilliQ Water (80% Batch Weight)",
                               style={'fontWeight': '500'}),
                        html.Td("Calculated",
                               style={'textAlign': 'right', 'color': '#17a2b8', 'fontWeight': '600'}),
                        html.Td("—", style={'fontSize': '0.85rem', 'color': '#6c757d'}),
                        html.Td(step.instructions or "—",
                               style={'fontSize': '0.85rem', 'color': '#6c757d'})
                    ])
                    table_rows.append(row)

                elif step.step_type == 'final_water_fill':
                    row = html.Tr([
                        html.Td("Add MilliQ to Target Mass",
                               style={'fontWeight': '500'}),
                        html.Td("To 1000g/L",
                               style={'textAlign': 'right', 'color': '#17a2b8', 'fontWeight': '600'}),
                        html.Td("—", style={'fontSize': '0.85rem', 'color': '#6c757d'}),
                        html.Td(step.instructions or "—",
                               style={'fontSize': '0.85rem', 'color': '#6c757d'})
                    ])
                    table_rows.append(row)

                elif step.step_type in ['measure_ph', 'adjust_ph']:
                    target_ph = params.get('target_ph', '—')
                    row = html.Tr([
                        html.Td(step_desc, style={'fontWeight': '500'}),
                        html.Td(f"Target: {target_ph}",
                               style={'textAlign': 'right', 'color': '#ffc107', 'fontWeight': '600'}),
                        html.Td("—", style={'fontSize': '0.85rem', 'color': '#6c757d'}),
                        html.Td(step.instructions or "—",
                               style={'fontSize': '0.85rem', 'color': '#6c757d'})
                    ])
                    table_rows.append(row)

                elif step.step_type in ['measure_osmolality', 'adjust_osmolality']:
                    target_osm = params.get('target_osmolality', '—')
                    row = html.Tr([
                        html.Td(step_desc, style={'fontWeight': '500'}),
                        html.Td(f"Target: {target_osm}",
                               style={'textAlign': 'right', 'color': '#ffc107', 'fontWeight': '600'}),
                        html.Td("—", style={'fontSize': '0.85rem', 'color': '#6c757d'}),
                        html.Td(step.instructions or "—",
                               style={'fontSize': '0.85rem', 'color': '#6c757d'})
                    ])
                    table_rows.append(row)

                elif step.step_type == 'filter_sterilize':
                    row = html.Tr([
                        html.Td("Filter Sterilize", style={'fontWeight': '500'}),
                        html.Td("0.22 μm",
                               style={'textAlign': 'right', 'color': '#6c757d', 'fontWeight': '600'}),
                        html.Td("—", style={'fontSize': '0.85rem', 'color': '#6c757d'}),
                        html.Td(step.instructions or "—",
                               style={'fontSize': '0.85rem', 'color': '#6c757d'})
                    ])
                    table_rows.append(row)

                elif step.step_type in ['stir', 'heat', 'cool']:
                    duration = params.get('duration_minutes', '—')
                    temp = params.get('temperature')
                    target = f"{duration} min"
                    if temp:
                        target += f" @ {temp}°C"

                    row = html.Tr([
                        html.Td(step_desc, style={'fontWeight': '500'}),
                        html.Td(target,
                               style={'textAlign': 'right', 'color': '#17a2b8', 'fontWeight': '600'}),
                        html.Td("—", style={'fontSize': '0.85rem', 'color': '#6c757d'}),
                        html.Td(step.instructions or "—",
                               style={'fontSize': '0.85rem', 'color': '#6c757d'})
                    ])
                    table_rows.append(row)

                else:
                    # Generic step
                    row = html.Tr([
                        html.Td(step_desc, style={'fontWeight': '500'}),
                        html.Td("—", style={'textAlign': 'right'}),
                        html.Td("—", style={'fontSize': '0.85rem', 'color': '#6c757d'}),
                        html.Td(step.instructions or "—",
                               style={'fontSize': '0.85rem', 'color': '#6c757d'})
                    ])
                    table_rows.append(row)

            # Create table in same format as media prep
            steps_table = dbc.Table([
                html.Thead(html.Tr([
                    html.Th("Component / Step", style={'width': '30%'}),
                    html.Th("Amount / Target", style={'width': '20%', 'textAlign': 'right'}),
                    html.Th("Catalog #", style={'width': '15%'}),
                    html.Th("Instructions", style={'width': '35%'})
                ], style={'backgroundColor': '#f8f9fa'})),
                html.Tbody(table_rows)
            ], bordered=True, hover=True, striped=True, size="sm", style={'marginTop': '1rem'})

            print(f"VIEW MODAL: Built table with {len(table_rows)} rows")

            return [
                True,  # is_open
                f"View Recipe: {recipe.recipe_name}",  # title
                recipe.recipe_id or "—",
                recipe.recipe_name or "—",
                f"v{recipe.version}" if recipe.version else "—",
                recipe.recipe_type or "—",  # Just use recipe_type directly
                f"{recipe.base_volume}L" if recipe.base_volume else "—",
                str(recipe.ph_target) if recipe.ph_target else "—",
                str(recipe.osmolality_target) if recipe.osmolality_target else "—",
                recipe.storage_temp or "—",
                f"{recipe.shelf_life_days} days" if recipe.shelf_life_days else "—",
                steps_table
            ]

        except Exception as e:
            print(f"VIEW MODAL ERROR: {e}")
            import traceback
            traceback.print_exc()
            return [True, "Error", "Error loading recipe", "", "", "", "", "", "", "", "",
                   dbc.Alert(f"Error: {str(e)}", color="danger")]

    return [no_update] * 12

# Control Update vs Save as New button visibility
@app.callback(
    [Output("update-recipe-btn", "style"),
     Output("save-recipe-note", "children")],
    Input("copied-recipe-id-store", "data"),
    prevent_initial_call=False
)
def toggle_save_buttons(copied_recipe_id):
    """Show/hide Update button based on whether we're editing an existing recipe"""
    if copied_recipe_id:
        # Editing existing recipe - show Update button
        return {'display': 'inline-block'}, "You can update the existing recipe or save as a new version"
    else:
        # Creating new recipe - hide Update button
        return {'display': 'none'}, "Saving will create a new recipe"

@app.callback(
    [Output("recipe-modal", "is_open"),
     Output("recipe-modal-title", "children"),  # Add modal title output
     Output("new-recipe-id", "value"),
     Output("new-recipe-name", "value"),
     Output("new-recipe-type", "value"),
     Output("new-recipe-version", "value"),
     Output("new-recipe-base-volume", "value"),
     Output("new-recipe-ph", "value"),
     Output("new-recipe-osm", "value"),
     Output("new-recipe-storage", "value"),
     Output("new-recipe-shelf-life", "value"),
     Output("edit-recipe-data-store", "data", allow_duplicate=True),  # Set data store BEFORE steps
     Output("recipe-steps-container", "children", allow_duplicate=True),
     Output("step-counter-store", "data", allow_duplicate=True),
     Output("copied-recipe-id-store", "data")],
    [Input("open-recipe-modal-btn", "n_clicks"),
     # REMOVED view-recipe-btn - now handled by separate view modal
     Input("cancel-recipe-btn", "n_clicks"),
     Input("save-recipe-btn", "n_clicks"),
     Input("update-recipe-btn", "n_clicks")],  # Handle update button
    [State("recipe-modal", "is_open")],
    prevent_initial_call=True
)
def toggle_recipe_modal(open_clicks, cancel_clicks, save_clicks, update_clicks, is_open):
    ctx = dash.callback_context
    print(f"DEBUG toggle_recipe_modal: ctx.triggered={ctx.triggered}")

    if not ctx.triggered or ctx.triggered[0]['prop_id'] == '.':
        print("DEBUG: Returning no_update - empty trigger")
        return [is_open] + [no_update] * 14

    # Check if this is a real click (not just a re-render)
    if ctx.triggered[0]['value'] is None:
        print("DEBUG: Returning no_update - value is None (re-render, not a click)")
        return [is_open] + [no_update] * 14

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    print(f"DEBUG: trigger_id={trigger_id}")

    if trigger_id == "open-recipe-modal-btn":
        # Open new blank recipe modal - no edit data
        return [True, "Create New Recipe", generate_recipe_id(), "", None, "1.0", 1.0, None, None, "", None, None, [], {'counter': 0}, None]

    elif 'view-recipe-btn' in trigger_id:
        # This should never fire - view button now handled by separate modal
        print("WARNING: Old view-recipe-btn code should not be called!")
        return [no_update] * 15
        # View/Edit existing recipe - get ID directly from button context
        try:
            recipe_id = eval(trigger_id)['index']
            print(f"DEBUG: Opening recipe for editing, recipe_id={recipe_id}")

            recipe = USPMediaRecipe.objects.prefetch_related('process_steps').get(id=recipe_id)

            # When viewing/editing, show the existing recipe ID
            display_recipe_id = recipe.recipe_id

            # Get the base name (without version suffix) and increment version
            base_name = recipe.recipe_name
            # Remove version suffix like "v1.0" or "v2" if present
            import re
            base_name = re.sub(r'\s+v\d+(\.\d+)?$', '', base_name)

            # Find highest version for this base name
            existing_versions = USPMediaRecipe.objects.filter(
                recipe_name__startswith=base_name
            ).values_list('version', flat=True)

            if existing_versions:
                max_version = max(existing_versions)
                new_version = str(float(max_version) + 1.0)
            else:
                new_version = "1.0"

            # Get recipe steps from database
            steps = recipe.process_steps.all().prefetch_related('parameters').order_by('step_number')

            # BUILD STEPS AS A TABLE (like media prep does - this works!)
            table_rows = []
            for step in steps:
                params = step.get_params()

                # Build step description
                step_desc = step.get_step_type_display()

                # Build step details based on type
                step_details = []
                if step.step_type == 'add_component':
                    component = params.get('component_id')
                    if component:
                        step_details.append(f"{component.component_name}")
                        amount = params.get('amount_per_liter')
                        unit = params.get('amount_unit')
                        if amount and unit:
                            step_details.append(f"{amount} {unit}/L")

                elif step.step_type in ['measure_ph', 'adjust_ph']:
                    target_ph = params.get('target_ph')
                    if target_ph:
                        step_details.append(f"Target pH: {target_ph}")

                elif step.step_type in ['measure_osmolality', 'adjust_osmolality']:
                    target_osm = params.get('target_osmolality')
                    if target_osm:
                        step_details.append(f"Target Osm: {target_osm}")

                elif step.step_type in ['stir', 'heat', 'cool']:
                    duration = params.get('duration_minutes')
                    if duration:
                        step_details.append(f"{duration} min")
                    temp = params.get('temperature')
                    if temp:
                        step_details.append(f"{temp}°C")

                details_text = ", ".join(step_details) if step_details else "—"

                row = html.Tr([
                    html.Td(step.step_number, style={'fontWeight': 'bold'}),
                    html.Td(step_desc),
                    html.Td(details_text),
                    html.Td(step.instructions or "—", style={'fontSize': '0.9em', 'color': '#666'})
                ])
                table_rows.append(row)

            steps_table = dbc.Table([
                html.Thead([
                    html.Tr([
                        html.Th("#", style={'width': '50px'}),
                        html.Th("Step Type", style={'width': '200px'}),
                        html.Th("Details", style={'width': '250px'}),
                        html.Th("Instructions")
                    ])
                ]),
                html.Tbody(table_rows)
            ], bordered=True, hover=True, striped=True, size="sm")

            # Wrap in a card for better presentation
            steps_display = dbc.Card([
                dbc.CardHeader(html.H6("Recipe Process Steps", className="mb-0")),
                dbc.CardBody(steps_table)
            ])

            print(f"DEBUG: Built table with {len(table_rows)} rows for recipe {recipe_id}")

            return [
                True,  # is_open
                f"View / Edit Recipe: {recipe.recipe_name}",  # modal title
                display_recipe_id,  # existing recipe ID (not a new one)
                recipe.recipe_name,  # name (user can edit)
                recipe.recipe_type,  # type
                new_version,  # incremented version
                recipe.base_volume,  # base volume
                recipe.ph_target,  # pH
                recipe.osmolality_target,  # osmolality
                recipe.storage_temp,  # storage
                recipe.shelf_life_days,  # shelf life
                None,  # edit-recipe-data-store - not needed for table view
                steps_display,  # TABLE DISPLAY instead of individual components
                {'counter': 0},  # step counter - reset for table view
                recipe_id  # store original recipe ID for updating
            ]

        except USPMediaRecipe.DoesNotExist:
            return [True, "Create New Recipe", generate_recipe_id(), "", None, "1.0", 1.0, None, None, "", None, None, [], {'counter': 0}, None]
        except Exception as e:
            print(f"Error in toggle_recipe_modal: {e}")
            return [no_update] + [no_update] * 14

    elif trigger_id in ["cancel-recipe-btn", "save-recipe-btn", "update-recipe-btn"]:
        # Close and reset modal (actual save logic is in save_recipe callback)
        return [False, "Create New Recipe", "", "", None, "1.0", 1.0, None, None, "", None, None, [], {'counter': 0}, None]

    return [is_open] + [no_update] * 14

@app.callback(
    [Output("recipe-steps-container", "children"),
     Output("step-counter-store", "data")],
    [Input("add-recipe-step-btn", "n_clicks")],
     # TEMPORARILY REMOVED remove button to test: Input({'type': 'remove-recipe-step', 'index': ALL}, "n_clicks")
    [State("recipe-steps-container", "children"),
     State("step-counter-store", "data")],
    prevent_initial_call=True
)
def manage_recipe_steps(add_clicks, current_steps, counter_data):
    ctx = dash.callback_context

    print(f"DEBUG manage_recipe_steps: CALLED with ctx.triggered={ctx.triggered}")
    print(f"DEBUG manage_recipe_steps: current_steps length={len(current_steps) if current_steps else 0}")

    if not ctx.triggered:
        print("DEBUG manage_recipe_steps: No trigger - returning current_steps")
        return current_steps, counter_data

    # Check if the triggered value is None (happens during button creation)
    if ctx.triggered[0]['value'] is None:
        print("DEBUG manage_recipe_steps: Triggered value is None - returning no_update")
        return no_update, no_update

    trigger = ctx.triggered[0]['prop_id']
    print(f"DEBUG manage_recipe_steps: trigger={trigger}")

    if 'add-recipe-step-btn' in trigger:
        counter_data['counter'] += 1
        step_index = counter_data['counter']

        # Calculate the display step number (should be 1-indexed based on current steps)
        display_step_number = len(current_steps) + 1

        new_step = dbc.Row([
            dbc.Col([
                html.Strong(f"Step {display_step_number}", className="d-flex align-items-center", style={'height': '38px'}),
            ], width="auto", style={'minWidth': '70px'}),
            dbc.Col([
                dcc.Dropdown(
                    options=STEP_TYPES,
                    placeholder="Select step type...",
                    id={'type': 'step-type', 'index': step_index}
                )
            ], width=3),
            dbc.Col([
                html.Div(id={'type': 'step-details', 'index': step_index})
            ], width="auto", className="flex-fill"),
            dbc.Col([
                dbc.Button(
                    html.I(className="fas fa-trash"),
                    id={'type': 'remove-recipe-step', 'index': step_index},
                    color="danger",
                    size="sm"
                )
            ], width="auto")
        ], className="mb-2 align-items-start", id={'type': 'recipe-step-row', 'index': step_index})

        current_steps.append(new_step)
        return current_steps, counter_data

    # REMOVE FUNCTIONALITY TEMPORARILY DISABLED
    # elif 'remove-recipe-step' in trigger:
    #     trigger_info = json.loads(trigger.split('.')[0])
    #     remove_index = trigger_info['index']
    #     current_steps = [
    #         step for step in current_steps
    #         if step.get('props', {}).get('id', {}).get('index') != remove_index
    #     ]

    return no_update, no_update

@app.callback(
    Output({'type': 'step-details', 'index': MATCH}, 'children'),
    Input({'type': 'step-type', 'index': MATCH}, 'value'),
    [State({'type': 'step-details', 'index': MATCH}, 'id'),
     State("edit-recipe-data-store", "data")],
    prevent_initial_call=False  # Allow to fire when step-type is initially set
)
def update_step_details(step_type, step_details_id, edit_data):
    """Dynamically show relevant fields based on step type, with optional pre-populated values"""
    if not step_type:
        return html.Div()

    # Get the index from the step_details_id
    step_index = step_details_id['index']

    # Check if we have prepopulated data for this step
    prepop = {}
    if edit_data and str(step_index) in edit_data:
        prepop = edit_data[str(step_index)]
        print(f"DEBUG update_step_details: step {step_index}, prepop data: {prepop}")

    if step_type == 'add_component':
        return dbc.Row([
            dbc.Col([
                dcc.Dropdown(
                    options=COMPONENT_TYPES,
                    value=prepop.get('component_type'),  # Use prepopulated value
                    placeholder="Component type...",
                    id={'type': 'step-component-type', 'index': step_index}
                )
            ], width=2),
            dbc.Col([
                dcc.Dropdown(
                    options=[{'label': prepop.get('component_name'), 'value': prepop.get('component_name')}] if prepop.get('component_name') else [],
                    value=prepop.get('component_name'),  # Use prepopulated value
                    placeholder="Select type first...",
                    id={'type': 'step-component', 'index': step_index}
                )
            ], width=4),
            dbc.Col([
                dbc.Input(
                    type="number",
                    value=prepop.get('amount_per_liter'),  # Use prepopulated value
                    placeholder="Amount/L",
                    id={'type': 'step-amount', 'index': step_index}
                )
            ], width=2),
            dbc.Col([
                dcc.Dropdown(
                    options=UNIT_OPTIONS,
                    value=prepop.get('amount_unit') or "g",  # Use prepopulated value or default
                    placeholder="Unit",
                    id={'type': 'step-unit', 'index': step_index}
                )
            ], width=2),
        ])

    elif step_type in ['stir', 'heat', 'cool']:
        return dbc.Row([
            dbc.Col([
                dbc.Input(
                    type="number",
                    value=prepop.get('duration_minutes'),  # Use prepopulated value
                    placeholder="Duration (min)",
                    id={'type': 'step-duration', 'index': step_index}
                )
            ], width=4),
            dbc.Col([
                dbc.Input(
                    type="number",
                    value=prepop.get('temperature'),  # Use prepopulated value
                    placeholder="Temperature (°C)" if step_type in ['heat', 'cool'] else "",
                    id={'type': 'step-temp', 'index': step_index}
                ) if step_type in ['heat', 'cool'] else html.Div()
            ], width=4),
        ])

    elif step_type in ['measure_ph', 'adjust_ph']:
        return dbc.Row([
            dbc.Col([
                dbc.Input(
                    type="text",
                    value=prepop.get('target_ph'),  # Use prepopulated value
                    placeholder="Target pH (e.g., 7.0 or 7.0-7.2)" if step_type == 'adjust_ph' else "Expected pH",
                    id={'type': 'step-ph', 'index': step_index}
                )
            ], width=6),
        ])

    elif step_type in ['measure_osmolality', 'adjust_osmolality']:
        return dbc.Row([
            dbc.Col([
                dbc.Input(
                    type="text",
                    value=prepop.get('target_osmolality'),  # Use prepopulated value
                    placeholder="Target Osm (e.g., 290 or 280-300)",
                    id={'type': 'step-osm', 'index': step_index}
                )
            ], width=6),
        ])

    elif step_type == 'initial_water_fill':
        return dbc.Row([
            dbc.Col([
                html.P("Fill to 80% of base volume (auto-calculated)", className="text-muted small mb-0")
            ], width=12),
        ])

    elif step_type == 'final_water_fill':
        return dbc.Row([
            dbc.Col([
                html.P("Fill to 100% final volume (auto-calculated)", className="text-muted small mb-0")
            ], width=12),
        ])

    elif step_type == 'add_water':
        return dbc.Row([
            dbc.Col([
                dbc.Input(
                    type="number",
                    value=prepop.get('target_volume'),  # Use prepopulated value
                    placeholder="Volume (mL)",
                    id={'type': 'step-volume', 'index': step_index}
                )
            ], width=4),
        ])

    elif step_type in ['note', 'filter_sterilize', 'autoclave', 'aliquot']:
        return dbc.Input(
            value=prepop.get('instructions'),  # Use prepopulated value
            placeholder="Instructions/Notes",
            id={'type': 'step-instructions', 'index': step_index}
        )

    return html.Div()

# Filter components by type in recipe steps
@app.callback(
    Output({'type': 'step-component', 'index': MATCH}, 'options'),
    Input({'type': 'step-component-type', 'index': MATCH}, 'value'),
    prevent_initial_call=True
)
def filter_components_by_type(component_type):
    """Filter component options based on selected type"""
    if not component_type:
        return []
    return get_component_options_by_type(component_type)

@app.callback(
    [Output("alerts-container", "children"),
     Output("recipe-table", "data")],
    [Input("save-recipe-btn", "n_clicks"),
     Input("update-recipe-btn", "n_clicks")],
    [State("new-recipe-id", "value"),
     State("new-recipe-name", "value"),
     State("new-recipe-type", "value"),
     State("new-recipe-version", "value"),
     State("new-recipe-base-volume", "value"),
     State("new-recipe-ph", "value"),
     State("new-recipe-osm", "value"),
     State("new-recipe-storage", "value"),
     State("new-recipe-shelf-life", "value"),
     State({'type': 'step-type', 'index': ALL}, 'value'),
     State({'type': 'step-component-type', 'index': ALL}, 'value'),
     State({'type': 'step-component', 'index': ALL}, 'value'),
     State({'type': 'step-amount', 'index': ALL}, 'value'),
     State({'type': 'step-unit', 'index': ALL}, 'value'),
     State({'type': 'step-duration', 'index': ALL}, 'value'),
     State({'type': 'step-temp', 'index': ALL}, 'value'),
     State({'type': 'step-ph', 'index': ALL}, 'value'),
     State({'type': 'step-volume', 'index': ALL}, 'value'),
     State({'type': 'step-instructions', 'index': ALL}, 'value'),
     State({'type': 'step-osm', 'index': ALL}, 'value'),  # Added missing osmolality
     State("copied-recipe-id-store", "data")],  # To know which recipe to update
    prevent_initial_call=True
)
def save_recipe(save_clicks, update_clicks, recipe_id, name, recipe_type, version, base_volume, ph, osm, storage, shelf_life,
                step_types, step_component_types, step_components, step_amounts, step_units, step_durations, step_temps,
                step_phs, step_volumes, step_instructions, step_osms, copied_recipe_id):

    ctx = dash.callback_context
    if not ctx.triggered:
        return no_update, no_update

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if not name or not recipe_type:
        return no_update, no_update

    try:
        with transaction.atomic():
            # Determine if we're updating or creating new
            is_update = (trigger_id == "update-recipe-btn" and copied_recipe_id)

            if is_update:
                # Update existing recipe
                recipe = USPMediaRecipe.objects.get(id=copied_recipe_id)
                recipe.recipe_name = name
                recipe.recipe_type = recipe_type
                recipe.version = version or "1.0"
                recipe.base_volume = base_volume or 1.0
                recipe.ph_target = ph if ph else None
                recipe.osmolality_target = osm if osm else None
                recipe.storage_temp = storage if storage else None
                recipe.shelf_life_days = shelf_life if shelf_life else None
                recipe.save()

                # Delete old steps and parameters
                recipe.process_steps.all().delete()

                action_msg = f"Recipe '{name}' updated successfully!"
            else:
                # Create a new recipe
                recipe = USPMediaRecipe.objects.create(
                    recipe_id=recipe_id or generate_recipe_id(),
                    recipe_name=name,
                    recipe_type=recipe_type,
                    version=version or "1.0",
                    base_volume=base_volume or 1.0,
                    ph_target=ph if ph else None,
                    osmolality_target=osm if osm else None,
                    storage_temp=storage if storage else None,
                    shelf_life_days=shelf_life if shelf_life else None,
                    active=True
                )

                action_msg = f"Recipe '{name}' created successfully!"

            # Create steps and their parameters
            for i, step_type in enumerate(step_types):
                if step_type:
                    # Create the step with basic info only
                    step = USPMediaRecipeStep.objects.create(
                        recipe=recipe,
                        step_number=i + 1,
                        step_type=step_type,
                        instructions=step_instructions[i] if i < len(step_instructions) and step_instructions[i] else None
                    )

                    # Create step parameters in USPMediaRecipeStepParameter table
                    if step_type == 'add_component' and i < len(step_components) and step_components[i]:
                        # Store component_id
                        USPMediaRecipeStepParameter.objects.create(
                            step=step,
                            parameter_key='component_id',
                            parameter_type='fk_component',
                            value_text=str(step_components[i]),
                            value_int=step_components[i]
                        )
                        # Store amount_per_liter
                        if i < len(step_amounts) and step_amounts[i]:
                            USPMediaRecipeStepParameter.objects.create(
                                step=step,
                                parameter_key='amount_per_liter',
                                parameter_type='float',
                                value_text=str(step_amounts[i]),
                                value_float=step_amounts[i]
                            )
                        # Store amount_unit
                        if i < len(step_units) and step_units[i]:
                            USPMediaRecipeStepParameter.objects.create(
                                step=step,
                                parameter_key='amount_unit',
                                parameter_type='string',
                                value_text=step_units[i]
                            )

                    elif step_type in ['stir', 'heat', 'cool']:
                        # Store duration_minutes
                        if i < len(step_durations) and step_durations[i]:
                            USPMediaRecipeStepParameter.objects.create(
                                step=step,
                                parameter_key='duration_minutes',
                                parameter_type='integer',
                                value_text=str(step_durations[i]),
                                value_int=int(step_durations[i])
                            )
                        # Store temperature for heat/cool
                        if step_type in ['heat', 'cool'] and i < len(step_temps) and step_temps[i]:
                            USPMediaRecipeStepParameter.objects.create(
                                step=step,
                                parameter_key='temperature',
                                parameter_type='float',
                                value_text=str(step_temps[i]),
                                value_float=float(step_temps[i])
                            )

                    elif step_type in ['measure_ph', 'adjust_ph']:
                        # Store target_ph
                        if i < len(step_phs) and step_phs[i]:
                            USPMediaRecipeStepParameter.objects.create(
                                step=step,
                                parameter_key='target_ph',
                                parameter_type='string',
                                value_text=str(step_phs[i])
                            )

                    elif step_type in ['measure_osmolality', 'adjust_osmolality']:
                        # Store target_osmolality from step-osm field
                        if i < len(step_instructions) and step_instructions[i]:
                            USPMediaRecipeStepParameter.objects.create(
                                step=step,
                                parameter_key='target_osmolality',
                                parameter_type='string',
                                value_text=step_instructions[i]
                            )

                    elif step_type == 'add_water':
                        # Store target_volume
                        if i < len(step_volumes) and step_volumes[i]:
                            USPMediaRecipeStepParameter.objects.create(
                                step=step,
                                parameter_key='target_volume',
                                parameter_type='float',
                                value_text=str(step_volumes[i]),
                                value_float=float(step_volumes[i])
                            )

                    # Store instructions as parameter if provided
                    if i < len(step_instructions) and step_instructions[i]:
                        USPMediaRecipeStepParameter.objects.create(
                            step=step,
                            parameter_key='instructions',
                            parameter_type='string',
                            value_text=step_instructions[i]
                        )

            alert = dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"{action_msg} {len([s for s in step_types if s])} steps saved."
            ], color="success", dismissable=True, duration=4000)

            return alert, get_all_recipes()

    except Exception as e:
        alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error: {str(e)}"
        ], color="danger", dismissable=True)
        return alert, no_update

# Save Media Prep Callback
@app.callback(
    Output("alerts-container", "children", allow_duplicate=True),
    Input("save-prep-btn", "n_clicks"),
    [State("prep-media-id-input", "value"),
     State("prep-recipe-dropdown", "value"),
     State("prep-batch-volume-input", "value"),
     State("prep-date-input", "value"),
     State("prep-prepared-by-input", "value"),
     State("prep-experiment-dropdown", "value"),
     State("prep-ph-input", "value"),
     State("prep-osmolality-input", "value"),
     State("prep-storage-input", "value"),
     State("prep-sterility-check", "value"),
     State({'type': 'component-actual-amount', 'index': ALL}, 'value'),
     State({'type': 'component-lot-number', 'index': ALL}, 'value'),
     State({'type': 'component-metadata', 'index': ALL}, 'data-component-id'),
     State({'type': 'component-metadata', 'index': ALL}, 'data-component-name'),
     State({'type': 'component-metadata', 'index': ALL}, 'data-catalog-number'),
     State({'type': 'component-metadata', 'index': ALL}, 'data-vendor'),
     State({'type': 'component-metadata', 'index': ALL}, 'data-target-amount'),
     State({'type': 'component-metadata', 'index': ALL}, 'data-unit'),
     State({'type': 'adjust-ph-titrant', 'index': ALL}, 'value'),
     State({'type': 'adjust-ph-amount', 'index': ALL}, 'value'),
     State({'type': 'adjust-ph-lot', 'index': ALL}, 'value'),
     State({'type': 'adjust-osm-component', 'index': ALL}, 'value'),
     State({'type': 'adjust-osm-amount', 'index': ALL}, 'value'),
     State({'type': 'adjust-osm-lot', 'index': ALL}, 'value')],
    prevent_initial_call=True
)
def save_media_prep(n_clicks, media_id, recipe_id, batch_volume, prep_date, prepared_by,
                    experiment_id, ph_actual, osm_actual, storage_location, sterility_check,
                    actual_amounts, lot_numbers, component_ids, component_names, catalog_numbers,
                    vendors, target_amounts, units,
                    ph_titrants, ph_amounts, ph_lots,
                    osm_components, osm_amounts, osm_lots):
    print(f"[SAVE MEDIA PREP] Called with n_clicks={n_clicks}, prepared_by={prepared_by}, batch_volume={batch_volume}")

    if not n_clicks or not prepared_by or not batch_volume:
        print(f"[SAVE MEDIA PREP] Validation failed - returning no_update")
        return no_update

    print(f"[SAVE MEDIA PREP] Starting save process for media_id={media_id}, recipe_id={recipe_id}")
    try:
        with transaction.atomic():
            # Get recipe and experiment if provided
            recipe = None
            if recipe_id:
                recipe = USPMediaRecipe.objects.get(id=recipe_id)

            experiment = None
            if experiment_id:
                experiment = USPExperiment.objects.get(experiment_id=experiment_id)

            # Create media prep
            prep = USPMediaPrep.objects.create(
                media_id=media_id or generate_media_id(),
                media_name=recipe.recipe_name if recipe else "Manual Prep",
                media_type=recipe.recipe_type if recipe else "Custom",
                recipe=recipe,
                batch_size=batch_volume,
                preparation_date=prep_date if prep_date else date.today(),
                expiration_date=(datetime.strptime(prep_date, '%Y-%m-%d').date() + timedelta(days=recipe.shelf_life_days)) if prep_date and recipe and recipe.shelf_life_days else None,
                prepared_by=prepared_by,
                experiment=experiment,
                ph_actual=ph_actual if ph_actual else None,
                osmolality_actual=osm_actual if osm_actual else None,
                sterility_check=bool(sterility_check),
                storage_location=storage_location if storage_location else None
            )

            # Save components with actual amounts and lot numbers
            if component_ids and len(component_ids) > 0:
                for i in range(len(component_ids)):
                    if component_ids[i]:
                        try:
                            comp_library = USPMediaComponentLibrary.objects.get(id=int(component_ids[i]))

                            # Determine component type from library or use stored value
                            component_type = comp_library.component_type

                            USPMediaComponent.objects.create(
                                media_prep=prep,
                                component_type=component_type,
                                component_name=component_names[i] if i < len(component_names) else comp_library.component_name,
                                lot_number=lot_numbers[i] if i < len(lot_numbers) and lot_numbers[i] else None,
                                target_amount=float(target_amounts[i]) if i < len(target_amounts) else 0,
                                actual_amount=float(actual_amounts[i]) if i < len(actual_amounts) and actual_amounts[i] else 0,
                                unit=units[i] if i < len(units) else comp_library.typical_units,
                                vendor=vendors[i] if i < len(vendors) else comp_library.vendor
                            )
                        except Exception as comp_error:
                            print(f"Error saving component {i}: {comp_error}")

            # Save pH adjustment titrants
            if ph_titrants and len(ph_titrants) > 0:
                for i in range(len(ph_titrants)):
                    if ph_titrants[i] and ph_amounts[i]:
                        try:
                            titrant = USPMediaComponentLibrary.objects.get(id=int(ph_titrants[i]))
                            USPMediaComponent.objects.create(
                                media_prep=prep,
                                component_type=titrant.component_type,
                                component_name=titrant.component_name,
                                lot_number=ph_lots[i] if i < len(ph_lots) and ph_lots[i] else None,
                                target_amount=0,  # No target for adjustments
                                actual_amount=float(ph_amounts[i]),
                                unit='mL',
                                vendor=titrant.vendor,
                                notes='pH adjustment'
                            )
                        except Exception as e:
                            print(f"Error saving pH titrant {i}: {e}")

            # Save osmolality adjustment components
            if osm_components and len(osm_components) > 0:
                for i in range(len(osm_components)):
                    if osm_components[i] and osm_amounts[i]:
                        try:
                            osm_comp = USPMediaComponentLibrary.objects.get(id=int(osm_components[i]))
                            USPMediaComponent.objects.create(
                                media_prep=prep,
                                component_type=osm_comp.component_type,
                                component_name=osm_comp.component_name,
                                lot_number=osm_lots[i] if i < len(osm_lots) and osm_lots[i] else None,
                                target_amount=0,  # No target for adjustments
                                actual_amount=float(osm_amounts[i]),
                                unit=osm_comp.typical_units,
                                vendor=osm_comp.vendor,
                                notes='Osmolality adjustment'
                            )
                        except Exception as e:
                            print(f"Error saving osmolality component {i}: {e}")

            alert = dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Media Prep {prep.media_id} saved successfully!"
            ], color="success", dismissable=True, duration=4000)

            print(f"[SAVE MEDIA PREP] Successfully saved media prep {prep.media_id}")
            return alert

    except Exception as e:
        print(f"[SAVE MEDIA PREP] Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()
        alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error: {str(e)}"
        ], color="danger", dismissable=True)
        return alert