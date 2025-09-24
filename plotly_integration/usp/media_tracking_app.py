"""
USP Media Tracking App
Recipe-based interface for tracking media preparations with automatic target calculations
"""

import dash
from dash import dcc, html, Input, Output, State, dash_table, no_update, ALL, MATCH, ctx
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
import pandas as pd
import json
from datetime import datetime, date, timedelta
from django.db import transaction
from plotly_integration.models import USPMediaPrep, USPMediaComponent, USPExperiment, USPMediaRecipe, USPMediaRecipeComponent

app = DjangoDash("USPMediaTrackingApp", external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
], suppress_callback_exceptions=True)

# Recipe type options
RECIPE_TYPES = [
    {'label': 'Growth Media', 'value': 'Growth Media'},
    {'label': 'Feed A', 'value': 'Feed A'},
    {'label': 'Feed B', 'value': 'Feed B'},
    {'label': 'Basal Media', 'value': 'Basal Media'},
    {'label': 'Supplement', 'value': 'Supplement'},
    {'label': 'Custom', 'value': 'Custom'},
]

# Component types for recipes
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
    {'label': 'Other', 'value': 'other'},
]

# Units for recipe components (per liter basis)
RECIPE_UNIT_OPTIONS = [
    {'label': 'g/L', 'value': 'g/L'},
    {'label': 'mg/L', 'value': 'mg/L'},
    {'label': 'mL/L', 'value': 'mL/L'},
    {'label': 'µL/L', 'value': 'µL/L'},
    {'label': 'mM', 'value': 'mM'},
    {'label': 'µM', 'value': 'µM'},
    {'label': '%', 'value': '%'},
]

# Units for actual prep components
PREP_UNIT_OPTIONS = [
    {'label': 'g', 'value': 'g'},
    {'label': 'mg', 'value': 'mg'},
    {'label': 'L', 'value': 'L'},
    {'label': 'mL', 'value': 'mL'},
    {'label': 'µL', 'value': 'µL'},
]

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

def get_recipe_options():
    """Get available recipes for dropdown"""
    recipes = USPMediaRecipe.objects.filter(active=True).order_by('recipe_type', 'recipe_name')
    options = []
    for rec in recipes:
        options.append({
            'label': f"{rec.recipe_name} v{rec.version} ({rec.recipe_type})",
            'value': rec.id
        })
    return options

def get_all_recipes():
    """Get all recipes for display"""
    recipes = USPMediaRecipe.objects.filter(active=True).prefetch_related('recipe_components').order_by('-created_date')
    data = []
    for recipe in recipes:
        components = recipe.recipe_components.all()
        component_count = components.count()

        # Create brief component list
        component_summary = []
        for comp in components[:3]:
            component_summary.append(f"{comp.component_name} ({comp.concentration_per_liter}{comp.unit})")
        if component_count > 3:
            component_summary.append(f"... +{component_count - 3} more")

        data.append({
            'recipe_id': recipe.recipe_id,
            'recipe_name': recipe.recipe_name,
            'recipe_type': recipe.recipe_type,
            'version': recipe.version,
            'base_volume': f"{recipe.base_volume} L",
            'ph_target': recipe.ph_target or '',
            'osmolality_target': recipe.osmolality_target or '',
            'component_count': component_count,
            'components': ', '.join(component_summary),
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
    """Get all media preparations for the table"""
    media_preps = USPMediaPrep.objects.all().select_related('experiment', 'recipe').prefetch_related('components').order_by('-preparation_date')

    data = []
    for prep in media_preps:
        # Get component summary
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

def calculate_target_amounts(recipe_id, batch_volume):
    """Calculate target amounts based on recipe and volume"""
    if not recipe_id or not batch_volume:
        return []

    try:
        recipe = USPMediaRecipe.objects.get(id=recipe_id)
        components = USPMediaRecipeComponent.objects.filter(recipe=recipe).order_by('order_index')

        target_components = []
        for comp in components:
            # Calculate target amount based on batch volume
            if comp.unit in ['g/L', 'mg/L', 'mL/L', 'µL/L']:
                # Direct volume scaling
                base_unit = comp.unit.split('/')[0]  # Get g, mg, mL, or µL
                target_amount = comp.concentration_per_liter * batch_volume

                target_components.append({
                    'component_type': comp.component_type,
                    'component_name': comp.component_name,
                    'catalog_number': comp.catalog_number or '',
                    'vendor': comp.vendor or '',
                    'target_amount': round(target_amount, 3),
                    'unit': base_unit,
                    'preparation_notes': comp.preparation_notes or ''
                })
            elif comp.unit == '%':
                # Percentage calculation (assuming % v/v for liquids)
                target_amount = (comp.concentration_per_liter / 100) * batch_volume * 1000  # Convert to mL
                target_components.append({
                    'component_type': comp.component_type,
                    'component_name': comp.component_name,
                    'catalog_number': comp.catalog_number or '',
                    'vendor': comp.vendor or '',
                    'target_amount': round(target_amount, 3),
                    'unit': 'mL',
                    'preparation_notes': comp.preparation_notes or ''
                })
            else:
                # For mM, µM - would need molecular weight for conversion
                # For now, just pass through as a note
                target_components.append({
                    'component_type': comp.component_type,
                    'component_name': comp.component_name,
                    'catalog_number': comp.catalog_number or '',
                    'vendor': comp.vendor or '',
                    'target_amount': comp.concentration_per_liter,
                    'unit': comp.unit,
                    'preparation_notes': f"Target: {comp.concentration_per_liter} {comp.unit} final concentration"
                })

        return target_components
    except Exception as e:
        print(f"Error calculating targets: {e}")
        return []

def create_recipe_component_row(index):
    """Create a row for entering recipe component data"""
    return dbc.Row([
        dbc.Col([
            dcc.Dropdown(
                options=COMPONENT_TYPES,
                placeholder="Type...",
                id={'type': 'recipe-comp-type', 'index': index}
            )
        ], width=2),
        dbc.Col([
            dbc.Input(
                placeholder="Component name",
                id={'type': 'recipe-comp-name', 'index': index}
            )
        ], width=3),
        dbc.Col([
            dbc.Input(
                placeholder="Catalog #",
                id={'type': 'recipe-catalog', 'index': index}
            )
        ], width=2),
        dbc.Col([
            dbc.Input(
                type="number",
                placeholder="Conc/L",
                id={'type': 'recipe-concentration', 'index': index}
            )
        ], width=2),
        dbc.Col([
            dcc.Dropdown(
                options=RECIPE_UNIT_OPTIONS,
                value="g/L",
                id={'type': 'recipe-unit', 'index': index}
            )
        ], width=2),
        dbc.Col([
            dbc.Button(
                html.I(className="fas fa-trash"),
                color="danger",
                size="sm",
                id={'type': 'remove-recipe-comp', 'index': index}
            )
        ], width=1)
    ], className="mb-2", id={'type': 'recipe-comp-row', 'index': index})

# Main Layout
app.layout = dbc.Container([
    dcc.Store(id="component-counter-store", data={'counter': 0}),
    dcc.Store(id="recipe-component-counter-store", data={'counter': 0}),
    dcc.Store(id="refresh-trigger-store"),
    dcc.Store(id="calculated-targets-store"),

    # Header with tabs
    dbc.Row([
        dbc.Col([
            html.H1([
                html.I(className="fas fa-flask text-primary me-3"),
                "USP Media Tracking"
            ], className="mb-3"),
            html.P("Recipe-based media preparation and tracking system", className="lead text-muted")
        ], width=12),
    ], className="mb-4"),

    # Tabs for different sections
    dbc.Tabs([
        dbc.Tab(label="Media Preparations", tab_id="prep-tab"),
        dbc.Tab(label="Recipe Management", tab_id="recipe-tab"),
    ], id="main-tabs", active_tab="prep-tab"),

    html.Div(id="tab-content", className="mt-4"),

    # Modal for new media prep
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
                                id="recipe-dropdown",
                                options=[],
                                placeholder="Select a recipe..."
                            ),
                        ], width=8),
                        dbc.Col([
                            dbc.Label("Batch Volume (L) *"),
                            dbc.Input(
                                id="batch-volume-input",
                                type="number",
                                step=0.1,
                                placeholder="e.g., 2.0"
                            ),
                        ], width=4),
                    ]),
                    html.Div(className="mt-3"),
                    dbc.Button(
                        [html.I(className="fas fa-calculator me-2"), "Calculate Target Amounts"],
                        id="calculate-targets-btn",
                        color="primary",
                        outline=True,
                        className="w-100"
                    ),
                ])
            ], className="mb-3"),

            # Step 2: Review and Adjust Components
            dbc.Card([
                dbc.CardHeader([html.H6("Step 2: Review Components and Enter Actual Amounts", className="mb-0")]),
                dbc.CardBody([
                    html.Div(id="calculated-components-container"),
                ])
            ], className="mb-3"),

            # Step 3: Media Details
            dbc.Card([
                dbc.CardHeader([html.H6("Step 3: Media Preparation Details", className="mb-0")]),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Media ID"),
                            dbc.Input(id="media-id-input", disabled=True),
                        ], width=3),
                        dbc.Col([
                            dbc.Label("Preparation Date *"),
                            dbc.Input(id="prep-date-input", type="date", value=date.today().strftime('%Y-%m-%d')),
                        ], width=3),
                        dbc.Col([
                            dbc.Label("Expiration Date"),
                            dbc.Input(id="exp-date-input", type="date"),
                        ], width=3),
                        dbc.Col([
                            dbc.Label("Prepared By *"),
                            dbc.Input(id="prepared-by-input", placeholder="Your name"),
                        ], width=3),
                    ], className="mb-3"),

                    dbc.Row([
                        dbc.Col([
                            dbc.Label("pH (Actual)"),
                            dbc.Input(id="ph-input", type="number", step=0.01, placeholder="e.g., 7.00"),
                        ], width=3),
                        dbc.Col([
                            dbc.Label("Osmolality (mOsm/kg)"),
                            dbc.Input(id="osmolality-input", type="number", placeholder="e.g., 290"),
                        ], width=3),
                        dbc.Col([
                            dbc.Label("Storage Location"),
                            dbc.Input(id="storage-input", placeholder="e.g., 4°C Cold Room"),
                        ], width=3),
                        dbc.Col([
                            dbc.Label("Sterility Check"),
                            dbc.Checklist(
                                options=[{"label": "Passed", "value": 1}],
                                value=[],
                                id="sterility-check",
                                switch=True,
                            ),
                        ], width=3),
                    ], className="mb-3"),

                    dbc.Row([
                        dbc.Col([
                            dbc.Label("Link to Experiment"),
                            dcc.Dropdown(
                                id="experiment-dropdown",
                                options=[],
                                placeholder="Select experiment (optional)..."
                            ),
                        ], width=12),
                    ], className="mb-3"),

                    dbc.Label("Notes"),
                    dbc.Textarea(
                        id="notes-input",
                        placeholder="Any additional notes...",
                        rows=2
                    ),
                ])
            ]),
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="cancel-btn", color="secondary", outline=True),
            dbc.Button([html.I(className="fas fa-save me-2"), "Save Media Prep"],
                      id="save-media-btn", color="primary"),
        ])
    ],
    id="media-modal",
    size="xl",
    is_open=False,
    backdrop="static"
    ),

    # Modal for new recipe
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle([
            html.I(className="fas fa-book me-2"),
            "Create New Recipe"
        ])),
        dbc.ModalBody([
            dbc.Row([
                dbc.Col([
                    dbc.Label("Recipe ID"),
                    dbc.Input(id="new-recipe-id", disabled=True),
                ], width=3),
                dbc.Col([
                    dbc.Label("Recipe Name *"),
                    dbc.Input(id="new-recipe-name", placeholder="e.g., CD FortiCHO"),
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
                    dbc.Label("Storage Temp"),
                    dbc.Input(id="new-recipe-storage", placeholder="e.g., 4°C"),
                ], width=2),
                dbc.Col([
                    dbc.Label("Shelf Life (days)"),
                    dbc.Input(id="new-recipe-shelf-life", type="number"),
                ], width=2),
            ], className="mb-3"),

            html.Hr(),
            html.H6("Recipe Components (per liter basis)"),

            # Component header
            dbc.Row([
                dbc.Col("Type", width=2, className="fw-bold"),
                dbc.Col("Component", width=3, className="fw-bold"),
                dbc.Col("Catalog #", width=2, className="fw-bold"),
                dbc.Col("Conc/L", width=2, className="fw-bold"),
                dbc.Col("Unit", width=2, className="fw-bold"),
            ], className="border-bottom pb-2 mb-2"),

            # Dynamic component rows
            html.Div(id="recipe-components-container", children=[
                create_recipe_component_row(0)
            ]),

            dbc.Button(
                [html.I(className="fas fa-plus me-2"), "Add Component"],
                id="add-recipe-component-btn",
                color="success",
                outline=True,
                size="sm",
                className="mt-2"
            ),
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="cancel-recipe-btn", color="secondary", outline=True),
            dbc.Button([html.I(className="fas fa-save me-2"), "Save Recipe"],
                      id="save-recipe-btn", color="primary"),
        ])
    ],
    id="recipe-modal",
    size="lg",
    is_open=False,
    backdrop="static"
    ),

    # Alerts container
    html.Div(id="alerts-container")

], fluid=True, className="p-4")

# Tab content callback
@app.callback(
    Output("tab-content", "children"),
    Input("main-tabs", "active_tab")
)
def render_tab_content(active_tab):
    if active_tab == "prep-tab":
        # Media Preparations Tab
        return html.Div([
            dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col([
                            html.H5([html.I(className="fas fa-list me-2"), "Media Preparations"], className="mb-0")
                        ], width="auto"),
                        dbc.Col([
                            dbc.Button(
                                [html.I(className="fas fa-plus me-2"), "New Media Prep"],
                                id="open-modal-btn",
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
                        style_cell={
                            'textAlign': 'left',
                            'fontSize': '12px',
                            'padding': '8px',
                        },
                        style_header={
                            'backgroundColor': 'rgb(230, 230, 230)',
                            'fontWeight': 'bold'
                        },
                        style_data_conditional=[
                            {
                                'if': {'row_index': 'odd'},
                                'backgroundColor': 'rgb(248, 248, 248)'
                            }
                        ],
                        page_size=15,
                        sort_action="native",
                        filter_action="native",
                    )
                ])
            ])
        ])

    elif active_tab == "recipe-tab":
        # Recipe Management Tab
        return html.Div([
            dbc.Card([
                dbc.CardHeader([
                    dbc.Row([
                        dbc.Col([
                            html.H5([html.I(className="fas fa-book me-2"), "Recipe Library"], className="mb-0")
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
                            {'name': '# Components', 'id': 'component_count', 'type': 'numeric'},
                            {'name': 'Components', 'id': 'components'},
                            {'name': 'Storage', 'id': 'storage_temp'},
                            {'name': 'Shelf Life', 'id': 'shelf_life'},
                            {'name': 'Created', 'id': 'created_date'},
                        ],
                        style_cell={
                            'textAlign': 'left',
                            'fontSize': '12px',
                            'padding': '8px',
                        },
                        style_header={
                            'backgroundColor': 'rgb(230, 230, 230)',
                            'fontWeight': 'bold'
                        },
                        style_data_conditional=[
                            {
                                'if': {'row_index': 'odd'},
                                'backgroundColor': 'rgb(248, 248, 248)'
                            }
                        ],
                        page_size=15,
                        sort_action="native",
                        filter_action="native",
                    )
                ])
            ])
        ])

# Modal control callbacks
@app.callback(
    [Output("media-modal", "is_open"),
     Output("media-id-input", "value"),
     Output("recipe-dropdown", "options"),
     Output("experiment-dropdown", "options")],
    [Input("open-modal-btn", "n_clicks"),
     Input("cancel-btn", "n_clicks"),
     Input("save-media-btn", "n_clicks")],
    [State("media-modal", "is_open")],
    prevent_initial_call=True
)
def toggle_media_modal(open_clicks, cancel_clicks, save_clicks, is_open):
    trigger_id = ctx.triggered_id

    if trigger_id == "open-modal-btn":
        new_media_id = generate_media_id()
        recipe_options = get_recipe_options()
        experiment_options = get_experiment_options()
        return True, new_media_id, recipe_options, experiment_options
    elif trigger_id in ["cancel-btn", "save-media-btn"]:
        return False, "", [], []

    return is_open, no_update, no_update, no_update

@app.callback(
    [Output("recipe-modal", "is_open"),
     Output("new-recipe-id", "value")],
    [Input("open-recipe-modal-btn", "n_clicks"),
     Input("cancel-recipe-btn", "n_clicks"),
     Input("save-recipe-btn", "n_clicks")],
    [State("recipe-modal", "is_open")],
    prevent_initial_call=True
)
def toggle_recipe_modal(open_clicks, cancel_clicks, save_clicks, is_open):
    trigger_id = ctx.triggered_id

    if trigger_id == "open-recipe-modal-btn":
        new_recipe_id = generate_recipe_id()
        return True, new_recipe_id
    elif trigger_id in ["cancel-recipe-btn", "save-recipe-btn"]:
        return False, ""

    return is_open, no_update

# Calculate target amounts callback
@app.callback(
    [Output("calculated-components-container", "children"),
     Output("calculated-targets-store", "data")],
    [Input("calculate-targets-btn", "n_clicks")],
    [State("recipe-dropdown", "value"),
     State("batch-volume-input", "value")],
    prevent_initial_call=True
)
def display_calculated_targets(n_clicks, recipe_id, batch_volume):
    if not recipe_id or not batch_volume:
        return dbc.Alert("Please select a recipe and enter batch volume", color="warning"), []

    targets = calculate_target_amounts(recipe_id, batch_volume)

    if not targets:
        return dbc.Alert("No components found for this recipe", color="info"), []

    # Create table of components with target amounts and input fields for actuals
    rows = []
    rows.append(
        dbc.Row([
            dbc.Col("Component", width=3, className="fw-bold"),
            dbc.Col("Vendor", width=2, className="fw-bold"),
            dbc.Col("Target Amount", width=2, className="fw-bold"),
            dbc.Col("Actual Amount", width=2, className="fw-bold"),
            dbc.Col("Lot Number", width=2, className="fw-bold"),
            dbc.Col("Notes", width=1, className="fw-bold"),
        ], className="border-bottom pb-2 mb-2")
    )

    for i, comp in enumerate(targets):
        rows.append(
            dbc.Row([
                dbc.Col([
                    html.Div(comp['component_name'], className="fw-semibold"),
                    html.Small(f"Type: {comp['component_type']}", className="text-muted")
                ], width=3),
                dbc.Col(comp['vendor'] or '-', width=2),
                dbc.Col(f"{comp['target_amount']} {comp['unit']}", width=2, className="fw-semibold text-primary"),
                dbc.Col([
                    dbc.InputGroup([
                        dbc.Input(
                            type="number",
                            id={'type': 'actual-amount', 'index': i},
                            placeholder="Actual",
                            value=comp['target_amount']
                        ),
                        dbc.InputGroupText(comp['unit'])
                    ], size="sm")
                ], width=2),
                dbc.Col([
                    dbc.Input(
                        id={'type': 'lot-number', 'index': i},
                        placeholder="Lot #",
                        size="sm"
                    )
                ], width=2),
                dbc.Col([
                    dbc.Button(
                        html.I(className="fas fa-info-circle"),
                        id={'type': 'comp-notes', 'index': i},
                        color="info",
                        outline=True,
                        size="sm",
                        title=comp.get('preparation_notes', '')
                    ) if comp.get('preparation_notes') else html.Div()
                ], width=1)
            ], className="mb-2 py-2 border-bottom")
        )

    # Get recipe info for display
    try:
        recipe = USPMediaRecipe.objects.get(id=recipe_id)
        recipe_info = dbc.Alert([
            html.H6(f"Recipe: {recipe.recipe_name} v{recipe.version}", className="mb-2"),
            html.P(f"Batch Volume: {batch_volume} L", className="mb-0")
        ], color="info")

        return [recipe_info] + rows, targets
    except:
        return rows, targets

# Recipe component management
@app.callback(
    [Output("recipe-components-container", "children"),
     Output("recipe-component-counter-store", "data")],
    [Input("add-recipe-component-btn", "n_clicks"),
     Input({'type': 'remove-recipe-comp', 'index': ALL}, "n_clicks")],
    [State("recipe-components-container", "children"),
     State("recipe-component-counter-store", "data")],
    prevent_initial_call=True
)
def manage_recipe_components(add_clicks, remove_clicks, current_components, counter_data):
    trigger_id = ctx.triggered_id

    if trigger_id == "add-recipe-component-btn":
        counter_data['counter'] += 1
        new_component = create_recipe_component_row(counter_data['counter'])
        current_components.append(new_component)
    elif trigger_id and 'type' in trigger_id:
        if trigger_id['type'] == 'remove-recipe-comp':
            remove_index = trigger_id['index']
            current_components = [
                comp for comp in current_components
                if comp['props']['id']['index'] != remove_index
            ]

    return current_components, counter_data

# Save recipe callback
@app.callback(
    [Output("alerts-container", "children", allow_duplicate=True),
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
     State({'type': 'recipe-comp-type', 'index': ALL}, "value"),
     State({'type': 'recipe-comp-name', 'index': ALL}, "value"),
     State({'type': 'recipe-catalog', 'index': ALL}, "value"),
     State({'type': 'recipe-concentration', 'index': ALL}, "value"),
     State({'type': 'recipe-unit', 'index': ALL}, "value")],
    prevent_initial_call=True
)
def save_recipe(n_clicks, recipe_id, name, recipe_type, version, base_volume, ph, osm, storage, shelf_life,
                comp_types, comp_names, catalogs, concentrations, units):
    if not n_clicks or not name or not recipe_type:
        return no_update, no_update

    try:
        with transaction.atomic():
            # Create recipe
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

            # Create components
            for i, (comp_type, comp_name, catalog, conc, unit) in enumerate(
                zip(comp_types, comp_names, catalogs, concentrations, units)
            ):
                if comp_name and conc is not None:
                    USPMediaRecipeComponent.objects.create(
                        recipe=recipe,
                        component_type=comp_type or 'other',
                        component_name=comp_name,
                        catalog_number=catalog if catalog else None,
                        concentration_per_liter=conc,
                        unit=unit or 'g/L',
                        order_index=i
                    )

            alert = dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Recipe {recipe_id} saved successfully!"
            ], color="success", dismissable=True)

            return alert, get_all_recipes()

    except Exception as e:
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error saving recipe: {str(e)}"
        ], color="danger", dismissable=True), no_update

# Save media prep callback
@app.callback(
    [Output("alerts-container", "children"),
     Output("media-table", "data")],
    Input("save-media-btn", "n_clicks"),
    [State("media-id-input", "value"),
     State("recipe-dropdown", "value"),
     State("batch-volume-input", "value"),
     State("prep-date-input", "value"),
     State("exp-date-input", "value"),
     State("prepared-by-input", "value"),
     State("ph-input", "value"),
     State("osmolality-input", "value"),
     State("storage-input", "value"),
     State("sterility-check", "value"),
     State("experiment-dropdown", "value"),
     State("notes-input", "value"),
     State("calculated-targets-store", "data"),
     State({'type': 'actual-amount', 'index': ALL}, "value"),
     State({'type': 'lot-number', 'index': ALL}, "value")],
    prevent_initial_call=True
)
def save_media_prep(n_clicks, media_id, recipe_id, batch_volume, prep_date, exp_date, prepared_by,
                   ph, osmolality, storage, sterility, experiment_id, notes, targets,
                   actual_amounts, lot_numbers):

    if not n_clicks or not recipe_id or not batch_volume or not prep_date or not prepared_by:
        return dbc.Alert("Please fill in all required fields", color="danger", dismissable=True), no_update

    try:
        with transaction.atomic():
            # Get recipe info
            recipe = USPMediaRecipe.objects.get(id=recipe_id)

            # Calculate expiration date if not provided
            if not exp_date and recipe.shelf_life_days:
                exp_date_obj = datetime.strptime(prep_date, '%Y-%m-%d').date() + timedelta(days=recipe.shelf_life_days)
                exp_date = exp_date_obj.strftime('%Y-%m-%d')

            # Create media prep
            media_prep = USPMediaPrep.objects.create(
                media_id=media_id or generate_media_id(),
                recipe=recipe,
                media_name=recipe.recipe_name,
                media_type=recipe.recipe_type,
                batch_size=batch_volume,
                preparation_date=prep_date,
                expiration_date=exp_date if exp_date else None,
                prepared_by=prepared_by,
                ph_actual=ph if ph else None,
                osmolality_actual=osmolality if osmolality else None,
                storage_location=storage if storage else recipe.storage_temp,
                sterility_check=1 in sterility if sterility else False,
                experiment_id=experiment_id if experiment_id else None,
                notes=notes if notes else ''
            )

            # Create components with actual amounts
            components_created = 0
            for i, target in enumerate(targets):
                if i < len(actual_amounts) and actual_amounts[i] is not None:
                    USPMediaComponent.objects.create(
                        media_prep=media_prep,
                        component_type=target['component_type'],
                        component_name=target['component_name'],
                        lot_number=lot_numbers[i] if i < len(lot_numbers) and lot_numbers[i] else None,
                        target_amount=target['target_amount'],
                        actual_amount=actual_amounts[i],
                        unit=target['unit'],
                        vendor=target.get('vendor', None)
                    )
                    components_created += 1

            alert = dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Media prep {media_id} saved successfully with {components_created} components!"
            ], color="success", dismissable=True)

            return alert, get_media_prep_data()

    except Exception as e:
        return dbc.Alert([
            html.I(className="fas fa-exclamation-triangle me-2"),
            f"Error saving media prep: {str(e)}"
        ], color="danger", dismissable=True), no_update