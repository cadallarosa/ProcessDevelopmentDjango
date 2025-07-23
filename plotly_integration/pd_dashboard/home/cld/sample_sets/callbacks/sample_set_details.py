# plotly_integration/pd_dashboard/home/cld/sample_sets/callbacks/sample_set_details.py

from dash import callback, Input, Output, State, ctx, no_update, ALL
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from dash import html, dash_table
import json
from datetime import datetime

# Import from the main app
from plotly_integration.pd_dashboard.main_app import app

# Import models
from plotly_integration.models import (
    LimsSampleSet, LimsSampleSetMembership, LimsSampleAnalysis,
    LimsSecResult, LimsTiterResult, LimsCiefResult, LimsCeSdsResult,
    LimsUpstreamSamples, Report
)


# Main page load callback
@app.callback(
    [Output("sample-set-basic-info", "children"),
     Output("analysis-cards-container", "children")],
    [Input("current-sample-set-id", "data"),
     Input("refresh-sample-set-details-btn", "n_clicks")]
)
def load_sample_set_details(sample_set_id, refresh_clicks):
    """Load sample set basic info and analysis cards"""
    if not sample_set_id:
        return html.Div("No sample set selected"), html.Div()

    try:
        sample_set = LimsSampleSet.objects.get(id=sample_set_id)

        # Create basic info header
        basic_info = html.Div([
            html.H3(sample_set.set_name, className="mb-2"),
            html.P([
                html.Span(f"Project: {sample_set.project_id}", className="me-3"),
                html.Span(f"Samples: {sample_set.sample_count}", className="me-3"),
                html.Span(f"Created: {sample_set.created_at.strftime('%Y-%m-%d')}")
            ], className="text-muted")
        ])

        # Get sample IDs for this set
        sample_ids = list(
            sample_set.members.values_list('sample__sample_id', flat=True)
        )

        # Create analysis cards
        analysis_cards = create_analysis_cards(sample_set_id, sample_ids)

        return basic_info, analysis_cards

    except Exception as e:
        return html.Div(f"Error loading sample set: {str(e)}", className="text-danger"), html.Div()


def create_analysis_cards(sample_set_id, sample_ids):
    """Create collapsible cards for each analysis type"""
    cards = []

    # Analysis types with their configurations
    analysis_configs = [
        {
            'type': 'SEC',
            'title': 'SEC Analysis',
            'icon': 'fa-chart-line',
            'color': 'primary',
            'model': LimsSecResult,
            'table_fields': [
                {'name': 'Sample ID', 'id': 'sample_id'},
                {'name': 'Main Peak (%)', 'id': 'main_peak', 'type': 'numeric', 'format': {'specifier': '.2f'}},
                {'name': 'HMW (%)', 'id': 'hmw', 'type': 'numeric', 'format': {'specifier': '.2f'}},
                {'name': 'LMW (%)', 'id': 'lmw', 'type': 'numeric', 'format': {'specifier': '.2f'}},
                {'name': 'QC Pass', 'id': 'qc_pass'},
                {'name': 'Status', 'id': 'status'},
                {'name': 'Analysis Date', 'id': 'created_at', 'type': 'datetime'}
            ]
        },
        {
            'type': 'Titer',
            'title': 'Titer Analysis',
            'icon': 'fa-vial',
            'color': 'success',
            'model': LimsTiterResult,
            'table_fields': [
                {'name': 'Sample ID', 'id': 'sample_id'},
                {'name': 'Titer (mg/mL)', 'id': 'titer', 'type': 'numeric', 'format': {'specifier': '.2f'}},
                {'name': 'QC Pass', 'id': 'qc_pass'},
                {'name': 'Status', 'id': 'status'},
                {'name': 'Analysis Date', 'id': 'created_at', 'type': 'datetime'}
            ]
        },
        {
            'type': 'cIEF',
            'title': 'cIEF Analysis',
            'icon': 'fa-flask',
            'color': 'info',
            'model': LimsCiefResult,
            'table_fields': [
                {'name': 'Sample ID', 'id': 'sample_id'},
                {'name': 'Main Peak (%)', 'id': 'main_peak', 'type': 'numeric', 'format': {'specifier': '.2f'}},
                {'name': 'Acidic Variants (%)', 'id': 'acidic_variants', 'type': 'numeric',
                 'format': {'specifier': '.2f'}},
                {'name': 'Basic Variants (%)', 'id': 'basic_variants', 'type': 'numeric',
                 'format': {'specifier': '.2f'}},
                {'name': 'Status', 'id': 'status'},
                {'name': 'Analysis Date', 'id': 'created_at', 'type': 'datetime'}
            ]
        },
        {
            'type': 'CE-SDS',
            'title': 'CE-SDS Analysis',
            'icon': 'fa-chart-bar',
            'color': 'warning',
            'model': LimsCeSdsResult,
            'table_fields': [
                {'name': 'Sample ID', 'id': 'sample_id'},
                {'name': 'Methods', 'id': 'methods_available'},
                # Reduced method columns
                {'name': 'R: LMW (%)', 'id': 'reduced_lmw', 'type': 'numeric', 'format': {'specifier': '.1f'}},
                {'name': 'R: Light Chain (%)', 'id': 'reduced_light_chain', 'type': 'numeric',
                 'format': {'specifier': '.1f'}},
                {'name': 'R: Heavy Chain (%)', 'id': 'reduced_heavy_chain', 'type': 'numeric',
                 'format': {'specifier': '.1f'}},
                {'name': 'R: HMW (%)', 'id': 'reduced_hmw', 'type': 'numeric', 'format': {'specifier': '.1f'}},
                # Non-reduced method columns
                {'name': 'NR: LMW (%)', 'id': 'nonreduced_lmw', 'type': 'numeric', 'format': {'specifier': '.1f'}},
                {'name': 'NR: Light Chain (%)', 'id': 'nonreduced_light_chain', 'type': 'numeric',
                 'format': {'specifier': '.1f'}},
                {'name': 'NR: Intact (%)', 'id': 'nonreduced_intact', 'type': 'numeric',
                 'format': {'specifier': '.1f'}},
                {'name': 'NR: HMW (%)', 'id': 'nonreduced_hmw', 'type': 'numeric', 'format': {'specifier': '.1f'}},
                # KEY ADDITION: Only Intact MW (most important)
                {'name': 'Intact MW (kDa)', 'id': 'intact_mw', 'type': 'numeric', 'format': {'specifier': '.1f'}},
                {'name': 'Purity (%)', 'id': 'purity', 'type': 'numeric', 'format': {'specifier': '.1f'}},
                {'name': 'Status', 'id': 'status'},
                {'name': 'Analysis Date', 'id': 'created_at', 'type': 'datetime'}
            ]
        }
    ]

    for config in analysis_configs:
        # Check if data exists
        has_data = check_analysis_data(config['model'], sample_ids)

        card = create_single_analysis_card(
            config=config,
            sample_set_id=sample_set_id,
            sample_ids=sample_ids,
            has_data=has_data
        )
        cards.append(card)

    return html.Div(cards)


def create_single_analysis_card(config, sample_set_id, sample_ids, has_data):
    """Create a single analysis card with button and collapsible content"""
    card_id = config['type'].lower().replace('-', '')

    # Create link button based on analysis type
    if config['type'] == 'SEC':
        # Check for existing SEC reports
        sec_reports = Report.objects.filter(
            analysis_type=1,
            project_id=LimsSampleSet.objects.get(id=sample_set_id).project_id
        ).order_by('-date_created')

        if sec_reports.exists():
            latest_report = sec_reports.first()
            button_href = f"/plotly_dash/sec_report_embedded/?report_id={latest_report.report_id}"
            button_text = "View SEC Report"
            button_color = "success"
            button_target = "_blank"
        else:
            # For new SEC analysis
            button_href = f"/plotly_dash/sec_report_embedded/?sample_set_id={sample_set_id}"
            button_text = "Launch SEC Analysis"
            button_color = "primary"
            button_target = "_blank"
    else:
        # Generic button for other analysis types - adjust these URLs based on your actual embedded apps
        button_href = f"/plotly_dash/{card_id}_embedded/?sample_set_id={sample_set_id}"
        button_text = f"Launch {config['title']}"
        button_color = config['color']
        button_target = "_blank"

    return dbc.Card([
        dbc.CardHeader([
            dbc.Row([
                dbc.Col([
                    html.H5([
                        html.I(className=f"fas {config['icon']} me-2"),
                        config['title']
                    ], className="mb-0")
                ], width=8),
                dbc.Col([
                    dbc.Button(
                        button_text,
                        href=button_href,
                        color=button_color,
                        size="sm",
                        className="me-2",
                        target=button_target if 'button_target' in locals() else None
                    ),
                    dbc.Button(
                        html.I(className="fas fa-chevron-down"),
                        id={"type": "analysis-card-toggle", "index": card_id},
                        color="light",
                        size="sm",
                        style={"width": "40px"}
                    )
                ], width=4, className="text-end")
            ])
        ]),
        dbc.Collapse(
            dbc.CardBody(
                id={"type": "analysis-card-content", "index": card_id}
            ),
            id={"type": "analysis-card-collapse", "index": card_id},
            is_open=True  # Default to expanded
        )
    ], className="mb-3")


def check_analysis_data(model, sample_ids):
    """Check if analysis data exists for samples"""
    if not model or not hasattr(model, 'objects'):
        return False

    try:
        return model.objects.filter(sample_id__sample_id__in=sample_ids).exists()
    except:
        return False


# Callback for loading analysis table data
@app.callback(
    Output({"type": "analysis-card-content", "index": ALL}, "children"),
    Input("analysis-cards-container", "children"),
    State("current-sample-set-id", "data")
)
def load_all_analysis_tables(cards_rendered, sample_set_id):
    """Load data tables for all analysis cards"""
    if not sample_set_id:
        return [no_update] * 4

    try:
        # Get sample IDs
        sample_ids = list(
            LimsSampleSetMembership.objects.filter(
                sample_set_id=sample_set_id
            ).values_list('sample__sample_id', flat=True)
        )

        # Load data for each analysis type
        sec_table = create_analysis_table('SEC', LimsSecResult, sample_ids)
        titer_table = create_analysis_table('Titer', LimsTiterResult, sample_ids)
        cief_table = create_analysis_table('cIEF', LimsCiefResult, sample_ids)
        cesds_table = create_analysis_table('CE-SDS', LimsCeSdsResult, sample_ids)

        return [sec_table, titer_table, cief_table, cesds_table]

    except Exception as e:
        print(f"Error loading analysis tables: {e}")
        return [html.Div("Error loading data")] * 4


def create_analysis_table(analysis_type, model, sample_ids):
    """Create a data table for analysis results"""
    # Get table fields from config
    table_configs = {
        'SEC': [
            {'name': 'Sample ID', 'id': 'sample_id'},
            {'name': 'Main Peak (%)', 'id': 'main_peak', 'type': 'numeric', 'format': {'specifier': '.2f'}},
            {'name': 'HMW (%)', 'id': 'hmw', 'type': 'numeric', 'format': {'specifier': '.2f'}},
            {'name': 'LMW (%)', 'id': 'lmw', 'type': 'numeric', 'format': {'specifier': '.2f'}},
            {'name': 'QC Pass', 'id': 'qc_pass'},
            {'name': 'Status', 'id': 'status'}
        ],
        'Titer': [
            {'name': 'Sample ID', 'id': 'sample_id'},
            {'name': 'Titer (mg/mL)', 'id': 'titer', 'type': 'numeric', 'format': {'specifier': '.2f'}},
            {'name': 'QC Pass', 'id': 'qc_pass'},
            {'name': 'Status', 'id': 'status'}
        ],
        'cIEF': [
            {'name': 'Sample ID', 'id': 'sample_id'},
            {'name': 'Main Peak (%)', 'id': 'main_peak', 'type': 'numeric', 'format': {'specifier': '.2f'}},
            {'name': 'Acidic (%)', 'id': 'acidic_variants', 'type': 'numeric', 'format': {'specifier': '.2f'}},
            {'name': 'Basic (%)', 'id': 'basic_variants', 'type': 'numeric', 'format': {'specifier': '.2f'}},
            {'name': 'Status', 'id': 'status'}
        ],
        'CE-SDS': [
            {'name': 'Sample ID', 'id': 'sample_id'},
            {'name': 'Methods', 'id': 'methods_available'},
            # Reduced method columns
            {'name': 'R: LMW (%)', 'id': 'reduced_lmw', 'type': 'numeric', 'format': {'specifier': '.1f'}},
            {'name': 'R: Light Chain (%)', 'id': 'reduced_light_chain', 'type': 'numeric',
             'format': {'specifier': '.1f'}},
            {'name': 'R: Heavy Chain (%)', 'id': 'reduced_heavy_chain', 'type': 'numeric',
             'format': {'specifier': '.1f'}},
            {'name': 'R: HMW (%)', 'id': 'reduced_hmw', 'type': 'numeric', 'format': {'specifier': '.1f'}},
            # Non-reduced method columns
            {'name': 'NR: LMW (%)', 'id': 'nonreduced_lmw', 'type': 'numeric', 'format': {'specifier': '.1f'}},
            {'name': 'NR: Light Chain (%)', 'id': 'nonreduced_light_chain', 'type': 'numeric',
             'format': {'specifier': '.1f'}},
            {'name': 'NR: Intact (%)', 'id': 'nonreduced_intact', 'type': 'numeric',
             'format': {'specifier': '.1f'}},
            {'name': 'NR: HMW (%)', 'id': 'nonreduced_hmw', 'type': 'numeric', 'format': {'specifier': '.1f'}},
            # KEY ADDITION: Only Intact MW (most important)
            {'name': 'Intact MW (kDa)', 'id': 'intact_mw', 'type': 'numeric', 'format': {'specifier': '.1f'}},
            {'name': 'Purity (%)', 'id': 'purity', 'type': 'numeric', 'format': {'specifier': '.1f'}},
            {'name': 'Status', 'id': 'status'},
            {'name': 'Analysis Date', 'id': 'created_at', 'type': 'datetime'}
        ]
    }

    columns = table_configs.get(analysis_type, [])

    # Get data
    try:
        if model and hasattr(model, 'objects'):
            results = model.objects.filter(
                sample_id__sample_id__in=sample_ids
            ).select_related('sample_id')

            data = []
            for result in results:
                row = {'sample_id': result.sample_id.sample_id}

                # Add fields based on model
                if analysis_type == 'SEC':
                    row.update({
                        'main_peak': result.main_peak,
                        'hmw': result.hmw,
                        'lmw': result.lmw,
                        'qc_pass': 'Pass' if result.qc_pass else 'Fail',
                        'status': result.status
                    })
                elif analysis_type == 'Titer':
                    row.update({
                        'titer': result.titer,
                        'qc_pass': 'Pass' if result.qc_pass else 'Fail',
                        'status': result.status
                    })
                elif analysis_type == 'cIEF':
                    row.update({
                        'main_peak': result.main_peak,
                        'acidic_variants': result.acidic_variants,
                        'basic_variants': result.basic_variants,
                        'status': result.status
                    })
                elif analysis_type == 'CE-SDS':
                    # Parse band_pattern JSON to extract method-specific data
                    band_pattern = result.band_pattern or {}
                    methods = band_pattern.get('methods', {})

                    # Determine which methods are available
                    available_methods = []
                    if 'reduced' in methods:
                        available_methods.append('R')
                    if 'non_reduced' in methods:
                        available_methods.append('NR')

                    # Extract reduced method data
                    reduced_data = methods.get('reduced', {}).get('peaks', {})

                    # Extract non-reduced method data
                    nonreduced_data = methods.get('non_reduced', {}).get('peaks', {})

                    # NEW: Get ONLY intact molecular weight from non-reduced data
                    intact_mw = None
                    if 'Intact' in nonreduced_data:
                        intact_mw = nonreduced_data['Intact'].get('molecular_weight')

                    row.update({
                        'methods_available': ' + '.join(available_methods) if available_methods else 'None',
                        'reduced_lmw': reduced_data.get('LMW', {}).get('value', None),
                        'reduced_light_chain': reduced_data.get('Light Chain', {}).get('value', None),
                        'reduced_heavy_chain': reduced_data.get('Heavy Chain', {}).get('value', None),
                        'reduced_hmw': reduced_data.get('HMW', {}).get('value', None),
                        'nonreduced_lmw': nonreduced_data.get('LMW', {}).get('value', None),
                        'nonreduced_light_chain': nonreduced_data.get('Light Chain', {}).get('value', None),
                        'nonreduced_intact': nonreduced_data.get('Intact', {}).get('value', None),
                        'nonreduced_hmw': nonreduced_data.get('HMW', {}).get('value', None),
                        'intact_mw': intact_mw,  # ONLY Intact MW (key value)
                        'purity': result.purity,
                        'status': result.status
                    })

                data.append(row)

            if data:
                # Build style conditions
                style_data_conditional = [
                    {
                        'if': {'column_id': 'qc_pass', 'filter_query': '{qc_pass} = "Pass"'},
                        'color': 'green'
                    },
                    {
                        'if': {'column_id': 'qc_pass', 'filter_query': '{qc_pass} = "Fail"'},
                        'color': 'red'
                    }
                ]

                # Add color gradient for SEC main peak
                if analysis_type == 'SEC' and any(row.get('main_peak') for row in data):
                    main_peak_values = [row.get('main_peak', 0) for row in data if row.get('main_peak') is not None]
                    if main_peak_values:
                        min_val = min(main_peak_values)
                        max_val = max(main_peak_values)

                        for i, row in enumerate(data):
                            if row.get('main_peak') is not None:
                                # Calculate color intensity (0-1 scale)
                                normalized = (row['main_peak'] - min_val) / (
                                            max_val - min_val) if max_val > min_val else 1
                                # Natural red to green gradient with muted colors
                                if normalized < 0.5:
                                    # Red to yellow range
                                    red = 220
                                    green = int(150 * (normalized * 2))
                                    blue = 100
                                else:
                                    # Yellow to green range
                                    red = int(220 - 120 * ((normalized - 0.5) * 2))
                                    green = 150 + int(50 * ((normalized - 0.5) * 2))
                                    blue = 100 + int(50 * ((normalized - 0.5) * 2))

                                style_data_conditional.append({
                                    'if': {'row_index': i, 'column_id': 'main_peak'},
                                    'backgroundColor': f'rgb({red}, {green}, {blue})',
                                    'color': 'black'
                                })

                # Add color gradient for Titer values
                if analysis_type == 'Titer' and any(row.get('titer') for row in data):
                    titer_values = [row.get('titer', 0) for row in data if row.get('titer') is not None]
                    if titer_values:
                        min_val = min(titer_values)
                        max_val = max(titer_values)

                        for i, row in enumerate(data):
                            if row.get('titer') is not None:
                                # Calculate color intensity (0-1 scale)
                                normalized = (row['titer'] - min_val) / (max_val - min_val) if max_val > min_val else 1
                                # Natural red to green gradient with muted colors
                                if normalized < 0.5:
                                    # Red to yellow range
                                    red = 220
                                    green = int(150 * (normalized * 2))
                                    blue = 100
                                else:
                                    # Yellow to green range
                                    red = int(220 - 120 * ((normalized - 0.5) * 2))
                                    green = 150 + int(50 * ((normalized - 0.5) * 2))
                                    blue = 100 + int(50 * ((normalized - 0.5) * 2))

                                style_data_conditional.append({
                                    'if': {'row_index': i, 'column_id': 'titer'},
                                    'backgroundColor': f'rgb({red}, {green}, {blue})',
                                    'color': 'black'
                                })

                return dash_table.DataTable(
                    columns=columns,
                    data=data,
                    style_table={'overflowX': 'auto'},
                    style_cell={
                        'textAlign': 'left',
                        'padding': '10px'
                    },
                    style_header={
                        'backgroundColor': 'rgb(230, 230, 230)',
                        'fontWeight': 'bold'
                    },
                    style_data_conditional=style_data_conditional,
                    # Remove pagination - show all rows
                    page_action="none",
                    sort_action="native",
                    filter_action="native"
                )
            else:
                return html.Div([
                    html.P(f"No {analysis_type} results available", className="text-muted text-center py-3")
                ])
        else:
            return html.Div([
                html.P(f"No {analysis_type} results available", className="text-muted text-center py-3")
            ])
    except Exception as e:
        print(f"Error creating {analysis_type} table: {e}")
        return html.Div([
            html.P(f"Error loading {analysis_type} results", className="text-danger text-center py-3")
        ])


# Individual card toggle callbacks
@app.callback(
    [Output({"type": "analysis-card-collapse", "index": "sec"}, "is_open"),
     Output({"type": "analysis-card-toggle", "index": "sec"}, "children")],
    [Input({"type": "analysis-card-toggle", "index": "sec"}, "n_clicks")],
    [State({"type": "analysis-card-collapse", "index": "sec"}, "is_open")],
    prevent_initial_call=True
)
def toggle_sec_card(n_clicks, is_open):
    """Toggle SEC card"""
    new_is_open = not is_open
    icon = html.I(className=f"fas fa-chevron-{'up' if new_is_open else 'down'}")
    return new_is_open, icon


@app.callback(
    [Output({"type": "analysis-card-collapse", "index": "titer"}, "is_open"),
     Output({"type": "analysis-card-toggle", "index": "titer"}, "children")],
    [Input({"type": "analysis-card-toggle", "index": "titer"}, "n_clicks")],
    [State({"type": "analysis-card-collapse", "index": "titer"}, "is_open")],
    prevent_initial_call=True
)
def toggle_titer_card(n_clicks, is_open):
    """Toggle Titer card"""
    new_is_open = not is_open
    icon = html.I(className=f"fas fa-chevron-{'up' if new_is_open else 'down'}")
    return new_is_open, icon


@app.callback(
    [Output({"type": "analysis-card-collapse", "index": "cief"}, "is_open"),
     Output({"type": "analysis-card-toggle", "index": "cief"}, "children")],
    [Input({"type": "analysis-card-toggle", "index": "cief"}, "n_clicks")],
    [State({"type": "analysis-card-collapse", "index": "cief"}, "is_open")],
    prevent_initial_call=True
)
def toggle_cief_card(n_clicks, is_open):
    """Toggle cIEF card"""
    new_is_open = not is_open
    icon = html.I(className=f"fas fa-chevron-{'up' if new_is_open else 'down'}")
    return new_is_open, icon


@app.callback(
    [Output({"type": "analysis-card-collapse", "index": "cesds"}, "is_open"),
     Output({"type": "analysis-card-toggle", "index": "cesds"}, "children")],
    [Input({"type": "analysis-card-toggle", "index": "cesds"}, "n_clicks")],
    [State({"type": "analysis-card-collapse", "index": "cesds"}, "is_open")],
    prevent_initial_call=True
)
def toggle_cesds_card(n_clicks, is_open):
    """Toggle CE-SDS card"""
    new_is_open = not is_open
    icon = html.I(className=f"fas fa-chevron-{'up' if new_is_open else 'down'}")
    return new_is_open, icon


# Load sample details table
@app.callback(
    [Output("sample-set-details-table-container", "children"),
     Output("sample-set-summary-stats", "children")],
    [Input("sample-set-detail-tabs", "active_tab"),
     Input("current-sample-set-id", "data")]
)
def update_sample_details_table(active_tab, sample_set_id):
    """Update the sample details table when overview tab is active"""
    if active_tab != "overview" or not sample_set_id:
        return no_update, no_update

    try:
        # Get sample set and samples
        sample_set = LimsSampleSet.objects.get(id=sample_set_id)
        memberships = LimsSampleSetMembership.objects.filter(
            sample_set_id=sample_set_id
        ).select_related(
            'sample',
            'sample__up'
        )

        # Build table data with correct fields
        data = []
        for membership in memberships:
            sample = membership.sample
            up_data = sample.up if hasattr(sample, 'up') and sample.up else None

            row = {
                'project': sample.project_id,
                'sample_number': sample.sample_id,
                'cell_line': up_data.cell_line if up_data else '',
                'sip_number': sample_set.sip_number or '',
                'development_stage': sample_set.development_stage or '',
                'analyst': sample.analyst or '',
                'harvest_date': up_data.harvest_date.strftime('%Y-%m-%d') if up_data and up_data.harvest_date else '',
                'unifi_number': up_data.unifi_number if up_data else '',
                'hf_octet_titer': up_data.hf_octet_titer if up_data else '',
                'pro_aqa_hf_titer': up_data.pro_aqa_hf_titer if up_data else '',
                'pro_aqa_e_titer': up_data.pro_aqa_e_titer if up_data else '',
                'proa_eluate_a280_conc': up_data.proa_eluate_a280_conc if up_data else '',
                'hccf_loading_volume': up_data.hccf_loading_volume if up_data else '',
                'proa_eluate_volume': up_data.proa_eluate_volume if up_data else '',
                'fast_pro_a_recovery': up_data.fast_pro_a_recovery if up_data else '',
                'purification_recovery_a280': up_data.purification_recovery_a280 if up_data else '',
                'note': up_data.note if up_data else ''
            }
            data.append(row)

        # Create summary stats with more info
        total_samples = len(data)
        unique_cell_lines = len(set(row['cell_line'] for row in data if row['cell_line']))

        summary = dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Total Samples", className="text-muted"),
                        html.H4(total_samples)
                    ])
                ])
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Project", className="text-muted"),
                        html.H4(sample_set.project_id)
                    ])
                ])
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("SIP", className="text-muted"),
                        html.H4(sample_set.sip_number or 'N/A')
                    ])
                ])
            ], width=3),
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6("Cell Lines", className="text-muted"),
                        html.H4(unique_cell_lines)
                    ])
                ])
            ], width=3)
        ], className="mb-3")

        # Return updated table
        from plotly_integration.pd_dashboard.home.cld.sample_sets.layouts.sample_set_details import \
            create_sample_set_details_table
        table = create_sample_set_details_table()
        table.data = data

        return table, summary

    except Exception as e:
        print(f"Error updating sample details: {e}")
        return html.Div("Error loading samples"), html.Div()


# Load top clones ranking table
@app.callback(
    Output("top-clones-table-container", "children"),
    [Input("sample-set-detail-tabs", "active_tab"),
     Input("current-sample-set-id", "data")]
)
def update_top_clones_table(active_tab, sample_set_id):
    """Create and update the top clones ranking table"""
    if active_tab != "top-clones" or not sample_set_id:
        return no_update

    try:
        # Get samples in this set
        sample_ids = list(
            LimsSampleSetMembership.objects.filter(
                sample_set_id=sample_set_id
            ).values_list('sample__sample_id', flat=True)
        )

        # Get SEC and Titer results
        sec_results = {
            r.sample_id.sample_id: r.main_peak
            for r in LimsSecResult.objects.filter(
                sample_id__sample_id__in=sample_ids
            ).select_related('sample_id')
            if r.main_peak is not None
        }

        titer_results = {
            r.sample_id.sample_id: r.titer
            for r in LimsTiterResult.objects.filter(
                sample_id__sample_id__in=sample_ids
            ).select_related('sample_id')
            if r.titer is not None
        }

        # Build ranking data
        ranking_data = []

        # Get samples that have both SEC and Titer results
        samples_with_both = set(sec_results.keys()) & set(titer_results.keys())

        if not samples_with_both:
            return html.Div([
                html.P("No samples with both SEC and Titer results available for ranking.",
                       className="text-muted text-center py-5")
            ])

        # Get min/max for normalization
        sec_values = [sec_results[s] for s in samples_with_both]
        titer_values = [titer_results[s] for s in samples_with_both]

        sec_min, sec_max = min(sec_values), max(sec_values)
        titer_min, titer_max = min(titer_values), max(titer_values)

        # Calculate scores for each sample
        for sample_id in samples_with_both:
            sec_value = sec_results[sample_id]
            titer_value = titer_results[sample_id]

            # Normalize to 0-100 scale
            sec_normalized = ((sec_value - sec_min) / (sec_max - sec_min) * 100) if sec_max > sec_min else 100
            titer_normalized = (
                        (titer_value - titer_min) / (titer_max - titer_min) * 100) if titer_max > titer_min else 100

            # Calculate composite score (40% SEC, 60% Titer)
            composite_score = (0.4 * sec_normalized) + (0.6 * titer_normalized)

            ranking_data.append({
                'rank': 0,  # Will be assigned after sorting
                'sample_id': sample_id,
                'sec_main_peak': sec_value,
                'sec_normalized': sec_normalized,
                'titer': titer_value,
                'titer_normalized': titer_normalized,
                'composite_score': composite_score
            })

        # Sort by composite score (descending) and assign ranks
        ranking_data.sort(key=lambda x: x['composite_score'], reverse=True)
        for i, item in enumerate(ranking_data):
            item['rank'] = i + 1

        # Create the ranking table
        columns = [
            {'name': 'Rank', 'id': 'rank', 'type': 'numeric'},
            {'name': 'Sample ID', 'id': 'sample_id'},
            {'name': 'SEC Main Peak (%)', 'id': 'sec_main_peak', 'type': 'numeric', 'format': {'specifier': '.2f'}},
            {'name': 'SEC Score', 'id': 'sec_normalized', 'type': 'numeric', 'format': {'specifier': '.1f'}},
            {'name': 'Titer (mg/mL)', 'id': 'titer', 'type': 'numeric', 'format': {'specifier': '.2f'}},
            {'name': 'Titer Score', 'id': 'titer_normalized', 'type': 'numeric', 'format': {'specifier': '.1f'}},
            {'name': 'Composite Score', 'id': 'composite_score', 'type': 'numeric', 'format': {'specifier': '.1f'}}
        ]

        # Style conditions for the table
        style_data_conditional = []

        # Highlight top 3 ranks
        for i in range(min(3, len(ranking_data))):
            if i == 0:  # Gold for 1st
                bg_color = 'rgba(255, 215, 0, 0.2)'
            elif i == 1:  # Silver for 2nd
                bg_color = 'rgba(192, 192, 192, 0.2)'
            else:  # Bronze for 3rd
                bg_color = 'rgba(205, 127, 50, 0.2)'

            style_data_conditional.append({
                'if': {'row_index': i},
                'backgroundColor': bg_color,
                'fontWeight': 'bold'
            })

        # Add color coding for composite score
        for i, row in enumerate(ranking_data):
            score_normalized = row['composite_score'] / 100
            if score_normalized < 0.5:
                # Red to yellow range
                red = 220
                green = int(150 * (score_normalized * 2))
                blue = 100
            else:
                # Yellow to green range
                red = int(220 - 120 * ((score_normalized - 0.5) * 2))
                green = 150 + int(50 * ((score_normalized - 0.5) * 2))
                blue = 100 + int(50 * ((score_normalized - 0.5) * 2))

            style_data_conditional.append({
                'if': {'row_index': i, 'column_id': 'composite_score'},
                'backgroundColor': f'rgb({red}, {green}, {blue})',
                'color': 'black',
                'fontWeight': 'bold'
            })

        return dash_table.DataTable(
            columns=columns,
            data=ranking_data,
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '10px'
            },
            style_header={
                'backgroundColor': 'rgb(230, 230, 230)',
                'fontWeight': 'bold'
            },
            style_data_conditional=style_data_conditional,
            page_action="none",
            sort_action="native",
            filter_action="native"
        )

    except Exception as e:
        print(f"Error creating top clones table: {e}")
        return html.Div(f"Error loading rankings: {str(e)}", className="text-danger")