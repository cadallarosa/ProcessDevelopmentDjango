"""
USP Media Tracking App
Complete media preparation system with component library and process-based recipes
"""

import dash
from dash import dcc, html, Input, Output, State, dash_table, no_update, ALL, MATCH
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
import pandas as pd
import json
from datetime import datetime, date, timedelta
from django.db import transaction
from plotly_integration.models import (
    USPMediaPrep, USPMediaComponent, USPExperiment, USPMediaRecipe,
    USPMediaRecipeStep, USPMediaComponentLibrary
)


app = DjangoDash("USPMediaTrackingApp", external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
], suppress_callback_exceptions=True)

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
            'id': recipe.id,  # Add database ID for editing
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
            'actions': f'[✏️ Edit](edit-recipe-{recipe.id})',
        })
    return data

def get_experiment_options():
    """Get available experiments for dropdown"""
    experiments = USPExperiment.objects.all().order_by('-created_date')
    return [{'label': f"{exp.experiment_id} - {exp.experiment_name}", 'value': exp.experiment_id}
            for exp in experiments]

def get_media_prep_data():
    """Get all media preparations for the table"""
    media_preps = USPMediaPrep.objects.all().select_related('experiment', 'recipe').prefetch_related('components').order_by('-preparation_date')
    data = []
    for prep in media_preps:
        components = prep.components.all()
        component_count = components.count()

        data.append({
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
        })
    return data

def calculate_scaled_process(recipe_id, batch_volume):
    """Calculate scaled process steps based on recipe and batch volume"""
    if not recipe_id or not batch_volume:
        return [], 1.0

    try:
        recipe = USPMediaRecipe.objects.get(id=recipe_id)
        all_steps = USPMediaRecipeStep.objects.filter(recipe=recipe).order_by('step_number')

        # Calculate scaling factor
        scaling_factor = batch_volume / recipe.base_volume

        scaled_steps = []
        for step in all_steps:
            step_info = {
                'step_number': step.step_number,
                'step_type': step.step_type,
                'step_type_display': step.get_step_type_display(),
                'scaling_factor': scaling_factor,
            }

            if step.step_type == 'add_component' and step.component:
                scaled_amount = step.amount_per_liter * batch_volume
                step_info.update({
                    'component_id': step.component.id,
                    'component_name': step.component.component_name,
                    'catalog_number': step.component.catalog_number or '',
                    'vendor': step.component.vendor or '',
                    'target_amount': round(scaled_amount, 3),
                    'unit': step.amount_unit or step.component.typical_units,
                    'original_amount_per_liter': step.amount_per_liter,
                })

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

            elif step.step_type == 'add_water' and step.target_volume:
                scaled_water = step.target_volume * scaling_factor
                step_info.update({
                    'water_volume': round(scaled_water, 1)
                })

            elif step.step_type in ['stir', 'heat', 'cool']:
                step_info.update({
                    'duration_minutes': step.duration_minutes,
                    'temperature': step.temperature
                })

            elif step.step_type in ['measure_ph', 'adjust_ph']:
                step_info.update({
                    'target_ph': step.target_ph or step.instructions
                })

            elif step.step_type in ['measure_osmolality', 'adjust_osmolality']:
                step_info.update({
                    'target_osmolality': step.instructions
                })

            if step.instructions:
                step_info['instructions'] = step.instructions

            scaled_steps.append(step_info)

        return scaled_steps, scaling_factor
    except Exception as e:
        print(f"Error calculating scaled process: {e}")
        return [], 1.0

# Main Layout
app.layout = dbc.Container([
    dcc.Store(id="step-counter-store", data={'counter': 0}),
    dcc.Store(id="refresh-trigger-store"),
    dcc.Store(id="calculated-targets-store"),

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

    # Tabs
    dbc.Tabs([
        dbc.Tab(label="Media Preparations", tab_id="prep-tab"),
        dbc.Tab(label="Recipe Management", tab_id="recipe-tab"),
        dbc.Tab(label="Component Library", tab_id="component-tab"),
    ], id="main-tabs", active_tab="prep-tab"),

    html.Div(id="tab-content", className="mt-4"),

    # Modals
    html.Div(id="modals-container"),

    # Alerts
    html.Div(id="alerts-container")

], fluid=True, className="p-4")

# Tab Content Callback
@app.callback(
    Output("tab-content", "children"),
    Input("main-tabs", "active_tab")
)
def render_tab_content(active_tab):
    if active_tab == "prep-tab":
        return html.Div([
            dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col([
                            html.H5([html.I(className="fas fa-list me-2"), "Media Preparations"],
                                   className="mb-0")
                        ], width="auto"),
                        dbc.Col([
                            dbc.Button(
                                [html.I(className="fas fa-plus me-2"), "New Media Prep"],
                                id="open-prep-modal-btn",
                                color="success",
                                size="sm"
                            )
                        ], width="auto", className="ms-auto")
                    ])
                ]),
                dbc.CardBody([
                    dash_table.DataTable(
                        id="media-table",
                        data=get_media_prep_data(),
                        columns=[
                            {'name': 'Media ID', 'id': 'media_id'},
                            {'name': 'Name', 'id': 'media_name'},
                            {'name': 'Type', 'id': 'media_type'},
                            {'name': 'Recipe', 'id': 'recipe'},
                            {'name': 'Batch Size', 'id': 'batch_size'},
                            {'name': 'Prep Date', 'id': 'preparation_date'},
                            {'name': 'Exp Date', 'id': 'expiration_date'},
                            {'name': 'Prepared By', 'id': 'prepared_by'},
                            {'name': 'Experiment', 'id': 'experiment'},
                            {'name': '# Comp', 'id': 'component_count', 'type': 'numeric'},
                            {'name': 'pH', 'id': 'ph', 'type': 'numeric'},
                            {'name': 'Osm', 'id': 'osmolality', 'type': 'numeric'},
                            {'name': 'Sterile', 'id': 'sterility'},
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
            ])
        ])

    elif active_tab == "recipe-tab":
        return html.Div([
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
                    dash_table.DataTable(
                        id="recipe-table",
                        data=get_all_recipes(),
                        columns=[
                            {'name': 'Recipe ID', 'id': 'recipe_id'},
                            {'name': 'Recipe Name', 'id': 'recipe_name'},
                            {'name': 'Type', 'id': 'recipe_type'},
                            {'name': 'Version', 'id': 'version'},
                            {'name': 'Base Vol', 'id': 'base_volume'},
                            {'name': 'pH Target', 'id': 'ph_target', 'type': 'numeric'},
                            {'name': 'Osm Target', 'id': 'osmolality_target', 'type': 'numeric'},
                            {'name': '# Steps', 'id': 'step_count', 'type': 'numeric'},
                            {'name': 'Storage', 'id': 'storage_temp'},
                            {'name': 'Shelf Life', 'id': 'shelf_life'},
                            {'name': 'Created', 'id': 'created_date'},
                            {'name': 'Actions', 'id': 'actions', 'presentation': 'markdown'},
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
            ])
        ])

    elif active_tab == "component-tab":
        return html.Div([
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
            ])
        ])

# Modals Container Callback
@app.callback(
    Output("modals-container", "children"),
    Input("main-tabs", "active_tab")
)
def render_modals(active_tab):
    """Render appropriate modals based on active tab"""
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
            ], style={"padding": "2rem", "minHeight": "500px"}),
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
            ], style={'maxHeight': '85vh', 'overflowY': 'auto', 'padding': '2rem', 'paddingBottom': '150px'}),
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
                "Create New Recipe"
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
            ], style={'maxHeight': '75vh', 'overflowY': 'auto', 'padding': '2rem', 'paddingBottom': '100px'}),
            dbc.ModalFooter([
                dbc.Button("Cancel", id="cancel-recipe-btn", color="secondary", outline=True),
                dbc.Button([html.I(className="fas fa-save me-2"), "Save Recipe"],
                          id="save-recipe-btn", color="primary"),
            ])
        ], id="recipe-modal", is_open=False, backdrop="static", fullscreen=True)
    )

    return modals

# Media Prep Modal Callbacks
@app.callback(
    [Output("prep-modal", "is_open"),
     Output("prep-media-id-input", "value"),
     Output("prep-recipe-dropdown", "options"),
],
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
        return True, generate_media_id(), get_recipe_options()
    elif trigger_id in ["cancel-prep-btn", "save-prep-btn"]:
        return False, "", []

    return is_open, no_update, no_update

@app.callback(
    Output("scaled-process-container", "children"),
    Input("calculate-scaled-amounts-btn", "n_clicks"),
    [State("prep-recipe-dropdown", "value"),
     State("prep-batch-volume-input", "value")],
    prevent_initial_call=True
)
def display_scaled_process(n_clicks, recipe_id, batch_volume):
    if not recipe_id or not batch_volume:
        return dbc.Alert("Please select a recipe and enter batch volume", color="warning")

    scaled_steps, scaling_factor = calculate_scaled_process(recipe_id, batch_volume)

    if not scaled_steps:
        return dbc.Alert("No steps found for this recipe", color="info")

    # Get recipe info
    try:
        recipe = USPMediaRecipe.objects.get(id=recipe_id)
        recipe_info = dbc.Alert([
            html.H6(f"Recipe: {recipe.recipe_name} v{recipe.version}", className="mb-2"),
            html.P(f"Scaling: {recipe.base_volume}L → {batch_volume}L (×{scaling_factor:.2f})", className="mb-0")
        ], color="info")
    except:
        recipe_info = html.Div()

    # Create process steps display
    steps_content = [recipe_info]

    for i, step in enumerate(scaled_steps):
        step_card = dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Strong(f"Step {step['step_number']}: {step['step_type_display']}", className="text-primary")
                    ], width=12),
                ]),

                # Component addition step
                *([dbc.Row([
                    dbc.Col([f"Component: {step.get('component_name', 'Unknown')}"], width=4),
                    dbc.Col([f"Catalog: {step.get('catalog_number', 'N/A')}"], width=2),
                    dbc.Col([f"Target: {step.get('target_amount', 0)} {step.get('unit', '')}"], width=2, className="fw-bold text-success"),
                    dbc.Col([
                        dbc.InputGroup([
                            dbc.Input(
                                type="number",
                                id={'type': 'actual-amount-prep', 'index': i},
                                placeholder="Actual",
                                value=step.get('target_amount', 0)
                            ),
                            dbc.InputGroupText(step.get('unit', ''))
                        ], size="sm")
                    ], width=2),
                    dbc.Col([
                        dbc.Input(
                            id={'type': 'lot-number-prep', 'index': i},
                            placeholder="Lot #",
                            size="sm"
                        )
                    ], width=2),
                ], className="mt-2")] if step['step_type'] == 'add_component' else []),

                # Water steps
                *([dbc.Row([
                    dbc.Col([f"Volume: {step.get('water_volume', 0)} mL ({step.get('percentage', 0)}%)"], width=6, className="fw-bold text-info"),
                ], className="mt-2")] if step['step_type'] in ['initial_water_fill', 'final_water_fill'] else []),

                # Custom water
                *([dbc.Row([
                    dbc.Col([f"Volume: {step.get('water_volume', 0)} mL"], width=4, className="fw-bold text-info"),
                ], className="mt-2")] if step['step_type'] == 'add_water' else []),

                # Time-based steps
                *([dbc.Row([
                    dbc.Col([f"Duration: {step.get('duration_minutes', 0)} minutes"], width=4),
                    *([dbc.Col([f"Temperature: {step.get('temperature', 0)}°C"], width=4)] if step.get('temperature') else []),
                ], className="mt-2")] if step['step_type'] in ['stir', 'heat', 'cool'] else []),

                # pH/Osmolality steps
                *([dbc.Row([
                    dbc.Col([f"Target: {step.get('target_ph', 0)}"], width=3, className="fw-bold text-warning"),
                    dbc.Col([
                        dbc.Input(
                            type="number",
                            step=0.01,
                            id={'type': 'actual-ph-prep', 'index': i},
                            placeholder="Actual pH",
                            size="sm"
                        )
                    ], width=3),
                    *([dbc.Col([
                        dcc.Dropdown(
                            id={'type': 'ph-component-prep', 'index': i},
                            options=get_component_options_by_type('acid') + get_component_options_by_type('base'),
                            placeholder="Select acid/base used...",
                            style={'fontSize': '12px'}
                        )
                    ], width=6)] if step['step_type'] == 'adjust_ph' else []),
                ], className="mt-2")] if step['step_type'] in ['measure_ph', 'adjust_ph'] and step.get('target_ph') else []),

                # Instructions
                *([dbc.Row([
                    dbc.Col([step['instructions']], width=12, className="text-muted small"),
                ], className="mt-2")] if step.get('instructions') else []),
            ])
        ], className="mb-2", color="light", outline=True)

        steps_content.append(step_card)

    return steps_content

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


# Recipe Table Click Handler for Editing
@app.callback(
    [Output("recipe-modal", "is_open"),
     Output("new-recipe-id", "value"),
     Output("new-recipe-name", "value"),
     Output("new-recipe-type", "value"),
     Output("new-recipe-version", "value"),
     Output("new-recipe-base-volume", "value"),
     Output("new-recipe-ph", "value"),
     Output("new-recipe-osm", "value"),
     Output("new-recipe-storage", "value"),
     Output("new-recipe-shelf-life", "value"),
     Output("new-recipe-description", "value"),
     Output("current-recipe-steps", "data")],
    [Input("recipe-table", "active_cell"),
     Input("open-recipe-modal-btn", "n_clicks"),
     Input("cancel-recipe-btn", "n_clicks")],
    [State("recipe-table", "data")]
)
def handle_recipe_table_click(active_cell, new_btn, cancel_btn, table_data):
    ctx = dash.callback_context
    if not ctx.triggered:
        return False, "", "", "", "1.0", 1.0, "", "", "", "", "", []


# Save Media Prep Callback
@app.callback(
    [Output("alerts-container", "children", allow_duplicate=True),
     Output("prep-table", "data", allow_duplicate=True)],
    Input("save-prep-btn", "n_clicks"),
    [State("prep-media-id-input", "value"),
     State("prep-recipe-dropdown", "value"),
     State("prep-batch-volume-input", "value"),
     State("prep-date-input", "value"),
     State("prep-prepared-by-input", "value"),
     State("prep-ph-input", "value"),
     State("prep-osmolality-input", "value"),
     State("prep-storage-input", "value"),
     State("prep-notes-input", "value"),
     State({"type": "actual-amount-prep", "index": ALL}, "value"),
     State({"type": "lot-number-prep", "index": ALL}, "value"),
     State({"type": "actual-ph-prep", "index": ALL}, "value"),
     State({"type": "ph-component-prep", "index": ALL}, "value")],
    prevent_initial_call=True
)
def save_media_prep(n_clicks, media_id, recipe_id, batch_volume, prep_date,
                    prepared_by, ph_actual, osm_actual, storage_location, notes,
                    actual_amounts, lot_numbers, actual_phs, ph_components):
    if not n_clicks or not media_id or not recipe_id or not batch_volume or not prepared_by:
        return no_update, no_update

    try:
        with transaction.atomic():
            # Get recipe
            recipe = USPMediaRecipe.objects.get(id=recipe_id)

            # Create media prep
            media_prep = USPMediaPrep.objects.create(
                media_id=media_id,
                media_name=f"{recipe.recipe_name} ({batch_volume}L)",
                media_type=recipe.recipe_type,
                batch_size=batch_volume,
                preparation_date=prep_date,
                prepared_by=prepared_by,
                ph_actual=ph_actual if ph_actual else None,
                osmolality_actual=osm_actual if osm_actual else None,
                storage_location=storage_location,
                notes=notes,
                recipe=recipe
            )

            # Create components from actual amounts entered
            steps = recipe.process_steps.filter(step_type='add_component').order_by('step_number')
            for i, step in enumerate(steps):
                if i < len(actual_amounts) and actual_amounts[i]:
                    USPMediaComponent.objects.create(
                        media_prep=media_prep,
                        component_type=step.component.component_type,
                        component_name=step.component.component_name,
                        lot_number=lot_numbers[i] if i < len(lot_numbers) else '',
                        target_amount=step.amount_per_liter * batch_volume,
                        actual_amount=actual_amounts[i],
                        unit=step.amount_unit or step.component.typical_units,
                        vendor=step.component.vendor or ''
                    )

            alert = dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Media prep {media_id} saved successfully!"
            ], color="success", dismissable=True, duration=4000)

            return alert, get_media_prep_data()

    except Exception as e:
        alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error saving media prep: {str(e)}"
        ], color="danger", dismissable=True)
        return alert, no_update

    trigger = ctx.triggered[0]['prop_id']

    if trigger == "cancel-recipe-btn.n_clicks" and cancel_btn:
        return False, "", "", "", "1.0", 1.0, "", "", "", "", "", []


# Save Media Prep Callback
@app.callback(
    [Output("alerts-container", "children", allow_duplicate=True),
     Output("prep-table", "data", allow_duplicate=True)],
    Input("save-prep-btn", "n_clicks"),
    [State("prep-media-id-input", "value"),
     State("prep-recipe-dropdown", "value"),
     State("prep-batch-volume-input", "value"),
     State("prep-date-input", "value"),
     State("prep-prepared-by-input", "value"),
     State("prep-ph-input", "value"),
     State("prep-osmolality-input", "value"),
     State("prep-storage-input", "value"),
     State("prep-notes-input", "value"),
     State({"type": "actual-amount-prep", "index": ALL}, "value"),
     State({"type": "lot-number-prep", "index": ALL}, "value"),
     State({"type": "actual-ph-prep", "index": ALL}, "value"),
     State({"type": "ph-component-prep", "index": ALL}, "value")],
    prevent_initial_call=True
)
def save_media_prep(n_clicks, media_id, recipe_id, batch_volume, prep_date,
                    prepared_by, ph_actual, osm_actual, storage_location, notes,
                    actual_amounts, lot_numbers, actual_phs, ph_components):
    if not n_clicks or not media_id or not recipe_id or not batch_volume or not prepared_by:
        return no_update, no_update

    try:
        with transaction.atomic():
            # Get recipe
            recipe = USPMediaRecipe.objects.get(id=recipe_id)

            # Create media prep
            media_prep = USPMediaPrep.objects.create(
                media_id=media_id,
                media_name=f"{recipe.recipe_name} ({batch_volume}L)",
                media_type=recipe.recipe_type,
                batch_size=batch_volume,
                preparation_date=prep_date,
                prepared_by=prepared_by,
                ph_actual=ph_actual if ph_actual else None,
                osmolality_actual=osm_actual if osm_actual else None,
                storage_location=storage_location,
                notes=notes,
                recipe=recipe
            )

            # Create components from actual amounts entered
            steps = recipe.process_steps.filter(step_type='add_component').order_by('step_number')
            for i, step in enumerate(steps):
                if i < len(actual_amounts) and actual_amounts[i]:
                    USPMediaComponent.objects.create(
                        media_prep=media_prep,
                        component_type=step.component.component_type,
                        component_name=step.component.component_name,
                        lot_number=lot_numbers[i] if i < len(lot_numbers) else '',
                        target_amount=step.amount_per_liter * batch_volume,
                        actual_amount=actual_amounts[i],
                        unit=step.amount_unit or step.component.typical_units,
                        vendor=step.component.vendor or ''
                    )

            alert = dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Media prep {media_id} saved successfully!"
            ], color="success", dismissable=True, duration=4000)

            return alert, get_media_prep_data()

    except Exception as e:
        alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error saving media prep: {str(e)}"
        ], color="danger", dismissable=True)
        return alert, no_update

    if trigger == "open-recipe-modal-btn.n_clicks" and new_btn:
        # Generate new recipe ID
        existing_count = USPMediaRecipe.objects.count()
        new_recipe_id = f"UMR{existing_count + 1:04d}"
        return True, new_recipe_id, "", "", "1.0", 1.0, "", "", "", "", "", []

    if trigger == "recipe-table.active_cell" and active_cell and table_data:
        row_index = active_cell['row']
        col_id = active_cell['column_id']

        if col_id == 'actions' and row_index < len(table_data):
            # Get recipe ID from table data
            recipe_db_id = table_data[row_index]['id']

            try:
                recipe = USPMediaRecipe.objects.get(id=recipe_db_id)

                # Get recipe steps
                steps = list(recipe.process_steps.all().order_by('step_number'))
                steps_data = []
                for step in steps:
                    step_data = {
                        'step_number': step.step_number,
                        'step_type': step.step_type,
                        'component_id': step.component.id if step.component else None,
                        'amount_per_liter': step.amount_per_liter,
                        'amount_unit': step.amount_unit,
                        'duration_minutes': step.duration_minutes,
                        'temperature': step.temperature,
                        'target_ph': step.target_ph,
                        'target_volume': step.target_volume,
                        'instructions': step.instructions,
                    }
                    steps_data.append(step_data)

                return (True, recipe.recipe_id, recipe.recipe_name, recipe.recipe_type,
                        recipe.version, recipe.base_volume, recipe.ph_target or "",
                        recipe.osmolality_target or "", recipe.storage_temp or "",
                        recipe.shelf_life_days or "", recipe.description or "",
                        steps_data)

            except Exception as e:
                print(f"Error loading recipe: {e}")
                return False, "", "", "", "1.0", 1.0, "", "", "", "", "", []


# Save Media Prep Callback
@app.callback(
    [Output("alerts-container", "children", allow_duplicate=True),
     Output("prep-table", "data", allow_duplicate=True)],
    Input("save-prep-btn", "n_clicks"),
    [State("prep-media-id-input", "value"),
     State("prep-recipe-dropdown", "value"),
     State("prep-batch-volume-input", "value"),
     State("prep-date-input", "value"),
     State("prep-prepared-by-input", "value"),
     State("prep-ph-input", "value"),
     State("prep-osmolality-input", "value"),
     State("prep-storage-input", "value"),
     State("prep-notes-input", "value"),
     State({"type": "actual-amount-prep", "index": ALL}, "value"),
     State({"type": "lot-number-prep", "index": ALL}, "value"),
     State({"type": "actual-ph-prep", "index": ALL}, "value"),
     State({"type": "ph-component-prep", "index": ALL}, "value")],
    prevent_initial_call=True
)
def save_media_prep(n_clicks, media_id, recipe_id, batch_volume, prep_date,
                    prepared_by, ph_actual, osm_actual, storage_location, notes,
                    actual_amounts, lot_numbers, actual_phs, ph_components):
    if not n_clicks or not media_id or not recipe_id or not batch_volume or not prepared_by:
        return no_update, no_update

    try:
        with transaction.atomic():
            # Get recipe
            recipe = USPMediaRecipe.objects.get(id=recipe_id)

            # Create media prep
            media_prep = USPMediaPrep.objects.create(
                media_id=media_id,
                media_name=f"{recipe.recipe_name} ({batch_volume}L)",
                media_type=recipe.recipe_type,
                batch_size=batch_volume,
                preparation_date=prep_date,
                prepared_by=prepared_by,
                ph_actual=ph_actual if ph_actual else None,
                osmolality_actual=osm_actual if osm_actual else None,
                storage_location=storage_location,
                notes=notes,
                recipe=recipe
            )

            # Create components from actual amounts entered
            steps = recipe.process_steps.filter(step_type='add_component').order_by('step_number')
            for i, step in enumerate(steps):
                if i < len(actual_amounts) and actual_amounts[i]:
                    USPMediaComponent.objects.create(
                        media_prep=media_prep,
                        component_type=step.component.component_type,
                        component_name=step.component.component_name,
                        lot_number=lot_numbers[i] if i < len(lot_numbers) else '',
                        target_amount=step.amount_per_liter * batch_volume,
                        actual_amount=actual_amounts[i],
                        unit=step.amount_unit or step.component.typical_units,
                        vendor=step.component.vendor or ''
                    )

            alert = dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Media prep {media_id} saved successfully!"
            ], color="success", dismissable=True, duration=4000)

            return alert, get_media_prep_data()

    except Exception as e:
        alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error saving media prep: {str(e)}"
        ], color="danger", dismissable=True)
        return alert, no_update

    return False, "", "", "", "1.0", 1.0, "", "", "", "", "", []


# Save Media Prep Callback
@app.callback(
    [Output("alerts-container", "children", allow_duplicate=True),
     Output("prep-table", "data", allow_duplicate=True)],
    Input("save-prep-btn", "n_clicks"),
    [State("prep-media-id-input", "value"),
     State("prep-recipe-dropdown", "value"),
     State("prep-batch-volume-input", "value"),
     State("prep-date-input", "value"),
     State("prep-prepared-by-input", "value"),
     State("prep-ph-input", "value"),
     State("prep-osmolality-input", "value"),
     State("prep-storage-input", "value"),
     State("prep-notes-input", "value"),
     State({"type": "actual-amount-prep", "index": ALL}, "value"),
     State({"type": "lot-number-prep", "index": ALL}, "value"),
     State({"type": "actual-ph-prep", "index": ALL}, "value"),
     State({"type": "ph-component-prep", "index": ALL}, "value")],
    prevent_initial_call=True
)
def save_media_prep(n_clicks, media_id, recipe_id, batch_volume, prep_date,
                    prepared_by, ph_actual, osm_actual, storage_location, notes,
                    actual_amounts, lot_numbers, actual_phs, ph_components):
    if not n_clicks or not media_id or not recipe_id or not batch_volume or not prepared_by:
        return no_update, no_update

    try:
        with transaction.atomic():
            # Get recipe
            recipe = USPMediaRecipe.objects.get(id=recipe_id)

            # Create media prep
            media_prep = USPMediaPrep.objects.create(
                media_id=media_id,
                media_name=f"{recipe.recipe_name} ({batch_volume}L)",
                media_type=recipe.recipe_type,
                batch_size=batch_volume,
                preparation_date=prep_date,
                prepared_by=prepared_by,
                ph_actual=ph_actual if ph_actual else None,
                osmolality_actual=osm_actual if osm_actual else None,
                storage_location=storage_location,
                notes=notes,
                recipe=recipe
            )

            # Create components from actual amounts entered
            steps = recipe.process_steps.filter(step_type='add_component').order_by('step_number')
            for i, step in enumerate(steps):
                if i < len(actual_amounts) and actual_amounts[i]:
                    USPMediaComponent.objects.create(
                        media_prep=media_prep,
                        component_type=step.component.component_type,
                        component_name=step.component.component_name,
                        lot_number=lot_numbers[i] if i < len(lot_numbers) else '',
                        target_amount=step.amount_per_liter * batch_volume,
                        actual_amount=actual_amounts[i],
                        unit=step.amount_unit or step.component.typical_units,
                        vendor=step.component.vendor or ''
                    )

            alert = dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Media prep {media_id} saved successfully!"
            ], color="success", dismissable=True, duration=4000)

            return alert, get_media_prep_data()

    except Exception as e:
        alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error saving media prep: {str(e)}"
        ], color="danger", dismissable=True)
        return alert, no_update

# Recipe Modal Callbacks
@app.callback(
    [Output("recipe-modal", "is_open"),
     Output("new-recipe-id", "value"),
     Output("recipe-steps-container", "children", allow_duplicate=True),
     Output("step-counter-store", "data", allow_duplicate=True)],
    [Input("open-recipe-modal-btn", "n_clicks"),
     Input("cancel-recipe-btn", "n_clicks"),
     Input("save-recipe-btn", "n_clicks")],
    State("recipe-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_recipe_modal(open_clicks, cancel_clicks, save_clicks, is_open):
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open, no_update, no_update, no_update

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == "open-recipe-modal-btn":
        # Reset the steps container and counter when opening modal
        return True, generate_recipe_id(), [], {'counter': 0}
    elif trigger_id in ["cancel-recipe-btn", "save-recipe-btn"]:
        return False, "", [], {'counter': 0}

    return is_open, no_update, no_update, no_update

@app.callback(
    [Output("recipe-steps-container", "children"),
     Output("step-counter-store", "data")],
    [Input("add-recipe-step-btn", "n_clicks"),
     Input({'type': 'remove-recipe-step', 'index': ALL}, "n_clicks")],
    [State("recipe-steps-container", "children"),
     State("step-counter-store", "data")],
    prevent_initial_call=True
)
def manage_recipe_steps(add_clicks, remove_clicks, current_steps, counter_data):
    ctx = dash.callback_context
    if not ctx.triggered:
        return current_steps, counter_data

    trigger = ctx.triggered[0]['prop_id']

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

    elif 'remove-recipe-step' in trigger:
        trigger_info = json.loads(trigger.split('.')[0])
        remove_index = trigger_info['index']
        # Filter out the step with the matching index
        current_steps = [
            step for step in current_steps
            if step.get('props', {}).get('id', {}).get('index') != remove_index
        ]

    return current_steps, counter_data

@app.callback(
    Output({'type': 'step-details', 'index': MATCH}, 'children'),
    Input({'type': 'step-type', 'index': MATCH}, 'value'),
    State({'type': 'step-details', 'index': MATCH}, 'id'),
    prevent_initial_call=True
)
def update_step_details(step_type, step_details_id):
    """Dynamically show relevant fields based on step type"""
    if not step_type:
        return html.Div()

    # Get the index from the step_details_id
    step_index = step_details_id['index']

    if step_type == 'add_component':
        return dbc.Row([
            dbc.Col([
                dcc.Dropdown(
                    options=COMPONENT_TYPES,
                    placeholder="Component type...",
                    id={'type': 'step-component-type', 'index': step_index}
                )
            ], width=2),
            dbc.Col([
                dcc.Dropdown(
                    options=[],
                    placeholder="Select type first...",
                    id={'type': 'step-component', 'index': step_index}
                )
            ], width=4),
            dbc.Col([
                dbc.Input(
                    type="number",
                    placeholder="Amount/L",
                    id={'type': 'step-amount', 'index': step_index}
                )
            ], width=2),
            dbc.Col([
                dcc.Dropdown(
                    options=UNIT_OPTIONS,
                    placeholder="Unit",
                    value="g",
                    id={'type': 'step-unit', 'index': step_index}
                )
            ], width=2),
        ])

    elif step_type in ['stir', 'heat', 'cool']:
        return dbc.Row([
            dbc.Col([
                dbc.Input(
                    type="number",
                    placeholder="Duration (min)",
                    id={'type': 'step-duration', 'index': step_index}
                )
            ], width=4),
            dbc.Col([
                dbc.Input(
                    type="number",
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
                    placeholder="Volume (mL)",
                    id={'type': 'step-volume', 'index': step_index}
                )
            ], width=4),
        ])

    elif step_type in ['note', 'filter_sterilize', 'autoclave', 'aliquot']:
        return dbc.Input(
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
    Input("save-recipe-btn", "n_clicks"),
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
     State({'type': 'step-instructions', 'index': ALL}, 'value')],
    prevent_initial_call=True
)
def save_recipe(n_clicks, recipe_id, name, recipe_type, version, base_volume, ph, osm, storage, shelf_life,
                step_types, step_component_types, step_components, step_amounts, step_units, step_durations, step_temps,
                step_phs, step_volumes, step_instructions):
    if not n_clicks or not name or not recipe_type:
        return no_update, no_update

    try:
        with transaction.atomic():
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

            # Create steps
            for i, step_type in enumerate(step_types):
                if step_type:
                    step_data = {
                        'recipe': recipe,
                        'step_number': i + 1,
                        'step_type': step_type,
                    }

                    if step_type == 'add_component' and i < len(step_components) and step_components[i]:
                        step_data['component_id'] = step_components[i]
                        step_data['amount_per_liter'] = step_amounts[i] if i < len(step_amounts) else None
                        step_data['amount_unit'] = step_units[i] if i < len(step_units) else None

                    elif step_type in ['stir', 'heat', 'cool']:
                        step_data['duration_minutes'] = step_durations[i] if i < len(step_durations) else None
                        if step_type in ['heat', 'cool'] and i < len(step_temps):
                            step_data['temperature'] = step_temps[i]

                    elif step_type in ['measure_ph', 'adjust_ph']:
                        step_data['target_ph'] = step_phs[i] if i < len(step_phs) else None

                    elif step_type == 'add_water':
                        step_data['target_volume'] = step_volumes[i] if i < len(step_volumes) else None

                    if i < len(step_instructions) and step_instructions[i]:
                        step_data['instructions'] = step_instructions[i]

                    USPMediaRecipeStep.objects.create(**step_data)

            alert = dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Recipe {recipe_id} saved with {len([s for s in step_types if s])} steps!"
            ], color="success", dismissable=True, duration=4000)

            return alert, get_all_recipes()

    except Exception as e:
        alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error: {str(e)}"
        ], color="danger", dismissable=True)
        return alert, no_update


# Recipe Table Click Handler for Editing
@app.callback(
    [Output("recipe-modal", "is_open"),
     Output("new-recipe-id", "value"),
     Output("new-recipe-name", "value"),
     Output("new-recipe-type", "value"),
     Output("new-recipe-version", "value"),
     Output("new-recipe-base-volume", "value"),
     Output("new-recipe-ph", "value"),
     Output("new-recipe-osm", "value"),
     Output("new-recipe-storage", "value"),
     Output("new-recipe-shelf-life", "value"),
     Output("new-recipe-description", "value"),
     Output("current-recipe-steps", "data")],
    [Input("recipe-table", "active_cell"),
     Input("open-recipe-modal-btn", "n_clicks"),
     Input("cancel-recipe-btn", "n_clicks")],
    [State("recipe-table", "data")]
)
def handle_recipe_table_click(active_cell, new_btn, cancel_btn, table_data):
    ctx = dash.callback_context
    if not ctx.triggered:
        return False, "", "", "", "1.0", 1.0, "", "", "", "", "", []


# Save Media Prep Callback
@app.callback(
    [Output("alerts-container", "children", allow_duplicate=True),
     Output("prep-table", "data", allow_duplicate=True)],
    Input("save-prep-btn", "n_clicks"),
    [State("prep-media-id-input", "value"),
     State("prep-recipe-dropdown", "value"),
     State("prep-batch-volume-input", "value"),
     State("prep-date-input", "value"),
     State("prep-prepared-by-input", "value"),
     State("prep-ph-input", "value"),
     State("prep-osmolality-input", "value"),
     State("prep-storage-input", "value"),
     State("prep-notes-input", "value"),
     State({"type": "actual-amount-prep", "index": ALL}, "value"),
     State({"type": "lot-number-prep", "index": ALL}, "value"),
     State({"type": "actual-ph-prep", "index": ALL}, "value"),
     State({"type": "ph-component-prep", "index": ALL}, "value")],
    prevent_initial_call=True
)
def save_media_prep(n_clicks, media_id, recipe_id, batch_volume, prep_date,
                    prepared_by, ph_actual, osm_actual, storage_location, notes,
                    actual_amounts, lot_numbers, actual_phs, ph_components):
    if not n_clicks or not media_id or not recipe_id or not batch_volume or not prepared_by:
        return no_update, no_update

    try:
        with transaction.atomic():
            # Get recipe
            recipe = USPMediaRecipe.objects.get(id=recipe_id)

            # Create media prep
            media_prep = USPMediaPrep.objects.create(
                media_id=media_id,
                media_name=f"{recipe.recipe_name} ({batch_volume}L)",
                media_type=recipe.recipe_type,
                batch_size=batch_volume,
                preparation_date=prep_date,
                prepared_by=prepared_by,
                ph_actual=ph_actual if ph_actual else None,
                osmolality_actual=osm_actual if osm_actual else None,
                storage_location=storage_location,
                notes=notes,
                recipe=recipe
            )

            # Create components from actual amounts entered
            steps = recipe.process_steps.filter(step_type='add_component').order_by('step_number')
            for i, step in enumerate(steps):
                if i < len(actual_amounts) and actual_amounts[i]:
                    USPMediaComponent.objects.create(
                        media_prep=media_prep,
                        component_type=step.component.component_type,
                        component_name=step.component.component_name,
                        lot_number=lot_numbers[i] if i < len(lot_numbers) else '',
                        target_amount=step.amount_per_liter * batch_volume,
                        actual_amount=actual_amounts[i],
                        unit=step.amount_unit or step.component.typical_units,
                        vendor=step.component.vendor or ''
                    )

            alert = dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Media prep {media_id} saved successfully!"
            ], color="success", dismissable=True, duration=4000)

            return alert, get_media_prep_data()

    except Exception as e:
        alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error saving media prep: {str(e)}"
        ], color="danger", dismissable=True)
        return alert, no_update

    trigger = ctx.triggered[0]['prop_id']

    if trigger == "cancel-recipe-btn.n_clicks" and cancel_btn:
        return False, "", "", "", "1.0", 1.0, "", "", "", "", "", []


# Save Media Prep Callback
@app.callback(
    [Output("alerts-container", "children", allow_duplicate=True),
     Output("prep-table", "data", allow_duplicate=True)],
    Input("save-prep-btn", "n_clicks"),
    [State("prep-media-id-input", "value"),
     State("prep-recipe-dropdown", "value"),
     State("prep-batch-volume-input", "value"),
     State("prep-date-input", "value"),
     State("prep-prepared-by-input", "value"),
     State("prep-ph-input", "value"),
     State("prep-osmolality-input", "value"),
     State("prep-storage-input", "value"),
     State("prep-notes-input", "value"),
     State({"type": "actual-amount-prep", "index": ALL}, "value"),
     State({"type": "lot-number-prep", "index": ALL}, "value"),
     State({"type": "actual-ph-prep", "index": ALL}, "value"),
     State({"type": "ph-component-prep", "index": ALL}, "value")],
    prevent_initial_call=True
)
def save_media_prep(n_clicks, media_id, recipe_id, batch_volume, prep_date,
                    prepared_by, ph_actual, osm_actual, storage_location, notes,
                    actual_amounts, lot_numbers, actual_phs, ph_components):
    if not n_clicks or not media_id or not recipe_id or not batch_volume or not prepared_by:
        return no_update, no_update

    try:
        with transaction.atomic():
            # Get recipe
            recipe = USPMediaRecipe.objects.get(id=recipe_id)

            # Create media prep
            media_prep = USPMediaPrep.objects.create(
                media_id=media_id,
                media_name=f"{recipe.recipe_name} ({batch_volume}L)",
                media_type=recipe.recipe_type,
                batch_size=batch_volume,
                preparation_date=prep_date,
                prepared_by=prepared_by,
                ph_actual=ph_actual if ph_actual else None,
                osmolality_actual=osm_actual if osm_actual else None,
                storage_location=storage_location,
                notes=notes,
                recipe=recipe
            )

            # Create components from actual amounts entered
            steps = recipe.process_steps.filter(step_type='add_component').order_by('step_number')
            for i, step in enumerate(steps):
                if i < len(actual_amounts) and actual_amounts[i]:
                    USPMediaComponent.objects.create(
                        media_prep=media_prep,
                        component_type=step.component.component_type,
                        component_name=step.component.component_name,
                        lot_number=lot_numbers[i] if i < len(lot_numbers) else '',
                        target_amount=step.amount_per_liter * batch_volume,
                        actual_amount=actual_amounts[i],
                        unit=step.amount_unit or step.component.typical_units,
                        vendor=step.component.vendor or ''
                    )

            alert = dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Media prep {media_id} saved successfully!"
            ], color="success", dismissable=True, duration=4000)

            return alert, get_media_prep_data()

    except Exception as e:
        alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error saving media prep: {str(e)}"
        ], color="danger", dismissable=True)
        return alert, no_update

    if trigger == "open-recipe-modal-btn.n_clicks" and new_btn:
        # Generate new recipe ID
        existing_count = USPMediaRecipe.objects.count()
        new_recipe_id = f"UMR{existing_count + 1:04d}"
        return True, new_recipe_id, "", "", "1.0", 1.0, "", "", "", "", "", []

    if trigger == "recipe-table.active_cell" and active_cell and table_data:
        row_index = active_cell['row']
        col_id = active_cell['column_id']

        if col_id == 'actions' and row_index < len(table_data):
            # Get recipe ID from table data
            recipe_db_id = table_data[row_index]['id']

            try:
                recipe = USPMediaRecipe.objects.get(id=recipe_db_id)

                # Get recipe steps
                steps = list(recipe.process_steps.all().order_by('step_number'))
                steps_data = []
                for step in steps:
                    step_data = {
                        'step_number': step.step_number,
                        'step_type': step.step_type,
                        'component_id': step.component.id if step.component else None,
                        'amount_per_liter': step.amount_per_liter,
                        'amount_unit': step.amount_unit,
                        'duration_minutes': step.duration_minutes,
                        'temperature': step.temperature,
                        'target_ph': step.target_ph,
                        'target_volume': step.target_volume,
                        'instructions': step.instructions,
                    }
                    steps_data.append(step_data)

                return (True, recipe.recipe_id, recipe.recipe_name, recipe.recipe_type,
                        recipe.version, recipe.base_volume, recipe.ph_target or "",
                        recipe.osmolality_target or "", recipe.storage_temp or "",
                        recipe.shelf_life_days or "", recipe.description or "",
                        steps_data)

            except Exception as e:
                print(f"Error loading recipe: {e}")
                return False, "", "", "", "1.0", 1.0, "", "", "", "", "", []


# Save Media Prep Callback
@app.callback(
    [Output("alerts-container", "children", allow_duplicate=True),
     Output("prep-table", "data", allow_duplicate=True)],
    Input("save-prep-btn", "n_clicks"),
    [State("prep-media-id-input", "value"),
     State("prep-recipe-dropdown", "value"),
     State("prep-batch-volume-input", "value"),
     State("prep-date-input", "value"),
     State("prep-prepared-by-input", "value"),
     State("prep-ph-input", "value"),
     State("prep-osmolality-input", "value"),
     State("prep-storage-input", "value"),
     State("prep-notes-input", "value"),
     State({"type": "actual-amount-prep", "index": ALL}, "value"),
     State({"type": "lot-number-prep", "index": ALL}, "value"),
     State({"type": "actual-ph-prep", "index": ALL}, "value"),
     State({"type": "ph-component-prep", "index": ALL}, "value")],
    prevent_initial_call=True
)
def save_media_prep(n_clicks, media_id, recipe_id, batch_volume, prep_date,
                    prepared_by, ph_actual, osm_actual, storage_location, notes,
                    actual_amounts, lot_numbers, actual_phs, ph_components):
    if not n_clicks or not media_id or not recipe_id or not batch_volume or not prepared_by:
        return no_update, no_update

    try:
        with transaction.atomic():
            # Get recipe
            recipe = USPMediaRecipe.objects.get(id=recipe_id)

            # Create media prep
            media_prep = USPMediaPrep.objects.create(
                media_id=media_id,
                media_name=f"{recipe.recipe_name} ({batch_volume}L)",
                media_type=recipe.recipe_type,
                batch_size=batch_volume,
                preparation_date=prep_date,
                prepared_by=prepared_by,
                ph_actual=ph_actual if ph_actual else None,
                osmolality_actual=osm_actual if osm_actual else None,
                storage_location=storage_location,
                notes=notes,
                recipe=recipe
            )

            # Create components from actual amounts entered
            steps = recipe.process_steps.filter(step_type='add_component').order_by('step_number')
            for i, step in enumerate(steps):
                if i < len(actual_amounts) and actual_amounts[i]:
                    USPMediaComponent.objects.create(
                        media_prep=media_prep,
                        component_type=step.component.component_type,
                        component_name=step.component.component_name,
                        lot_number=lot_numbers[i] if i < len(lot_numbers) else '',
                        target_amount=step.amount_per_liter * batch_volume,
                        actual_amount=actual_amounts[i],
                        unit=step.amount_unit or step.component.typical_units,
                        vendor=step.component.vendor or ''
                    )

            alert = dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Media prep {media_id} saved successfully!"
            ], color="success", dismissable=True, duration=4000)

            return alert, get_media_prep_data()

    except Exception as e:
        alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error saving media prep: {str(e)}"
        ], color="danger", dismissable=True)
        return alert, no_update

    return False, "", "", "", "1.0", 1.0, "", "", "", "", "", []


# Save Media Prep Callback
@app.callback(
    [Output("alerts-container", "children", allow_duplicate=True),
     Output("prep-table", "data", allow_duplicate=True)],
    Input("save-prep-btn", "n_clicks"),
    [State("prep-media-id-input", "value"),
     State("prep-recipe-dropdown", "value"),
     State("prep-batch-volume-input", "value"),
     State("prep-date-input", "value"),
     State("prep-prepared-by-input", "value"),
     State("prep-ph-input", "value"),
     State("prep-osmolality-input", "value"),
     State("prep-storage-input", "value"),
     State("prep-notes-input", "value"),
     State({"type": "actual-amount-prep", "index": ALL}, "value"),
     State({"type": "lot-number-prep", "index": ALL}, "value"),
     State({"type": "actual-ph-prep", "index": ALL}, "value"),
     State({"type": "ph-component-prep", "index": ALL}, "value")],
    prevent_initial_call=True
)
def save_media_prep(n_clicks, media_id, recipe_id, batch_volume, prep_date,
                    prepared_by, ph_actual, osm_actual, storage_location, notes,
                    actual_amounts, lot_numbers, actual_phs, ph_components):
    if not n_clicks or not media_id or not recipe_id or not batch_volume or not prepared_by:
        return no_update, no_update

    try:
        with transaction.atomic():
            # Get recipe
            recipe = USPMediaRecipe.objects.get(id=recipe_id)

            # Create media prep
            media_prep = USPMediaPrep.objects.create(
                media_id=media_id,
                media_name=f"{recipe.recipe_name} ({batch_volume}L)",
                media_type=recipe.recipe_type,
                batch_size=batch_volume,
                preparation_date=prep_date,
                prepared_by=prepared_by,
                ph_actual=ph_actual if ph_actual else None,
                osmolality_actual=osm_actual if osm_actual else None,
                storage_location=storage_location,
                notes=notes,
                recipe=recipe
            )

            # Create components from actual amounts entered
            steps = recipe.process_steps.filter(step_type='add_component').order_by('step_number')
            for i, step in enumerate(steps):
                if i < len(actual_amounts) and actual_amounts[i]:
                    USPMediaComponent.objects.create(
                        media_prep=media_prep,
                        component_type=step.component.component_type,
                        component_name=step.component.component_name,
                        lot_number=lot_numbers[i] if i < len(lot_numbers) else '',
                        target_amount=step.amount_per_liter * batch_volume,
                        actual_amount=actual_amounts[i],
                        unit=step.amount_unit or step.component.typical_units,
                        vendor=step.component.vendor or ''
                    )

            alert = dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Media prep {media_id} saved successfully!"
            ], color="success", dismissable=True, duration=4000)

            return alert, get_media_prep_data()

    except Exception as e:
        alert = dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error saving media prep: {str(e)}"
        ], color="danger", dismissable=True)
        return alert, no_update