from dash import Input, Output, State, html, dcc, dash_table, callback_context
from django_plotly_dash import DjangoDash
import json
from plotly_integration.models import Report

# Get the app instance
from ..app import app

@app.callback(
    Output("report-modal", "style"),
    Output("report-tab-content", "children"),
    Input("select-create-report-btn", "n_clicks"),
    Input("close-report-modal-btn", "n_clicks"),
    Input("report-tabs", "value"),
    State("report-modal", "style"),
    prevent_initial_call=True
)
def toggle_modal_and_content(open_clicks, close_clicks, tab_value, current_style):
    ctx = callback_context
    
    if not ctx.triggered:
        return {'display': 'none'}, html.Div()
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Handle modal visibility
    if trigger_id == "close-report-modal-btn":
        return {'display': 'none'}, html.Div()
    
    modal_style = current_style.copy() if current_style else {}
    
    if trigger_id == "select-create-report-btn":
        modal_style['display'] = 'block'
    
    # Generate tab content
    if tab_value == "select":
        # Fetch existing reports
        reports = Report.objects.all().order_by('-created_at')[:50]
        
        if reports:
            report_data = [
                {
                    'id': r.id,
                    'name': r.report_name,
                    'sample_set': r.sample_set,
                    'created': r.created_at.strftime('%Y-%m-%d %H:%M'),
                    'modified': r.modified_at.strftime('%Y-%m-%d %H:%M') if r.modified_at else '-'
                }
                for r in reports
            ]
            
            content = html.Div([
                dash_table.DataTable(
                    id='report-selection-table',
                    columns=[
                        {'name': 'ID', 'id': 'id'},
                        {'name': 'Report Name', 'id': 'name'},
                        {'name': 'Sample Set', 'id': 'sample_set'},
                        {'name': 'Created', 'id': 'created'},
                        {'name': 'Modified', 'id': 'modified'}
                    ],
                    data=report_data,
                    row_selectable='single',
                    selected_rows=[],
                    style_cell={'textAlign': 'center', 'padding': '10px'},
                    style_header={'backgroundColor': '#3f51b5', 'color': 'white', 'fontWeight': 'bold'},
                    style_data={'backgroundColor': '#fafafa'},
                    style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': '#f5f5f5'}]
                ),
                html.Button("Load Selected Report", id="load-report-btn", 
                           style={'marginTop': '20px', 'padding': '10px 20px', 
                                 'backgroundColor': '#2563eb', 'color': 'white',
                                 'border': 'none', 'borderRadius': '5px', 'cursor': 'pointer'})
            ])
        else:
            content = html.Div([
                html.P("No reports found. Please create a new report.", 
                      style={'color': '#666', 'padding': '20px', 'textAlign': 'center'})
            ])
    
    else:  # Create new report
        content = html.Div([
            html.Div([
                html.Label("Report Name:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                dcc.Input(id="new-report-name", type="text", placeholder="Enter report name",
                         style={'width': '100%', 'padding': '10px', 'borderRadius': '5px', 
                               'border': '1px solid #ddd', 'marginBottom': '15px'})
            ]),
            html.Div([
                html.Label("Sample Set:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                dcc.Input(id="new-sample-set", type="text", placeholder="Enter sample set identifier",
                         style={'width': '100%', 'padding': '10px', 'borderRadius': '5px', 
                               'border': '1px solid #ddd', 'marginBottom': '15px'})
            ]),
            html.Div([
                html.Label("Description:", style={'fontWeight': 'bold', 'marginBottom': '5px'}),
                dcc.Textarea(id="new-report-description", placeholder="Enter description (optional)",
                            style={'width': '100%', 'padding': '10px', 'borderRadius': '5px', 
                                  'border': '1px solid #ddd', 'height': '100px', 'marginBottom': '15px'})
            ]),
            html.Button("Create Report", id="create-report-btn",
                       style={'padding': '10px 20px', 'backgroundColor': '#059669', 
                             'color': 'white', 'border': 'none', 'borderRadius': '5px', 
                             'cursor': 'pointer'})
        ])
    
    return modal_style, content

@app.callback(
    Output("selected-report", "data"),
    Output("current-report-text", "children"),
    Output("report-modal", "style", allow_duplicate=True),
    Input("load-report-btn", "n_clicks"),
    Input("create-report-btn", "n_clicks"),
    State("report-selection-table", "selected_rows"),
    State("report-selection-table", "data"),
    State("new-report-name", "value"),
    State("new-sample-set", "value"),
    State("new-report-description", "value"),
    prevent_initial_call=True
)
def handle_report_selection(load_clicks, create_clicks, selected_rows, table_data,
                           new_name, new_sample_set, new_description):
    ctx = callback_context
    
    if not ctx.triggered:
        return None, "No report selected", {'display': 'none'}
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == "load-report-btn" and selected_rows:
        selected_report = table_data[selected_rows[0]]
        report_id = selected_report['id']
        report_name = selected_report['name']
        
        return report_id, f"Report: {report_name}", {'display': 'none'}
    
    elif trigger_id == "create-report-btn" and new_name and new_sample_set:
        # Create new report
        new_report = Report.objects.create(
            report_name=new_name,
            sample_set=new_sample_set,
            description=new_description or "",
            report_type='cief'  # Specify this is a cIEF report
        )
        
        return new_report.id, f"Report: {new_name}", {'display': 'none'}
    
    return None, "No report selected", {'display': 'none'}