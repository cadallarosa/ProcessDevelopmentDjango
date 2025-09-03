"""
Callbacks for statistical analysis and summary views
"""

from dash import Input, Output, State, dash_table, html
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np

from ..formulation_stability_app import app, COLOR_PALETTE, STORAGE_CONDITIONS
from ..utils.data_processing import calculate_stability_score, create_comparison_dataframe

@app.callback(
    Output('formulation-composition-table', 'children'),
    Input('formulation-data-store', 'data'),
    prevent_initial_call=True
)
def update_formulation_composition_table(formulation_data):
    """Create formulation composition table"""
    if not formulation_data:
        return html.Div("No formulation data available")
    
    try:
        rows = []
        
        for formulation_id, formulation_info in formulation_data.items():
            info = formulation_info['formulation_info']
            
            # Get formulation details from database
            from plotly_integration.models import FormulationCondition
            formulation = FormulationCondition.objects.get(id=formulation_id)
            
            row = {
                'Formulation': info['number'],
                'Study': info['study'],
                'Buffer': info['buffer_type'] or 'N/A',
                'pH': info['ph'],
                'Arg·HCl (mg/mL)': formulation.arginine_hcl or 0,
                'Sucrose (mg/mL)': formulation.sucrose or 0,
                'Sorbitol (mg/mL)': formulation.sorbitol or 0,
                'Trehalose (mg/mL)': formulation.trehalose or 0,
                'Glycine (mg/mL)': formulation.glycine or 0,
                'PS80 (mg/mL)': formulation.polysorbate_80 or 0,
                'Osmolality (mOsm/kg)': formulation.osmolality or 'N/A'
            }
            rows.append(row)
        
        if not rows:
            return html.Div("No composition data available")
        
        df = pd.DataFrame(rows)
        
        return dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{'name': col, 'id': col, 'type': 'numeric' if col not in ['Formulation', 'Study', 'Buffer'] else 'text'} 
                    for col in df.columns],
            style_cell={
                'textAlign': 'center',
                'padding': '10px',
                'fontFamily': 'Arial, sans-serif',
                'fontSize': '12px',
                'minWidth': '80px'
            },
            style_header={
                'backgroundColor': COLOR_PALETTE['info'],
                'color': 'white',
                'fontWeight': 'bold',
                'textAlign': 'center'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': COLOR_PALETTE['light']
                },
                {
                    'if': {'column_id': 'pH'},
                    'backgroundColor': COLOR_PALETTE['accent'],
                    'color': 'white'
                }
            ],
            sort_action='native',
            export_format='xlsx'
        )
        
    except Exception as e:
        print(f"Error creating composition table: {e}")
        return html.Div(f"Error creating table: {str(e)}")

@app.callback(
    Output('stability-ranking-plot', 'figure'),
    Input('formulation-data-store', 'data'),
    Input('ranking-criteria', 'value'),
    prevent_initial_call=True
)
def update_stability_ranking_plot(formulation_data, ranking_criteria):
    """Create stability ranking bar chart"""
    if not formulation_data:
        return go.Figure()
    
    try:
        ranking_data = []
        
        for formulation_id, formulation_info in formulation_data.items():
            formulation_number = formulation_info['formulation_info']['number']
            stability_scores = calculate_stability_score(formulation_info)
            
            for condition, scores in stability_scores.items():
                condition_label = STORAGE_CONDITIONS.get(condition, {"label": condition})["label"]
                
                if ranking_criteria == 'stability_score':
                    value = scores['stability_score']
                    title = 'Stability Score'
                    y_axis = 'Stability Score (0-100)'
                elif ranking_criteria == 'main_retention':
                    value = -scores['main_degradation_rate'] if scores['main_degradation_rate'] else 0
                    title = 'Main Peak Retention (Higher = Better)'
                    y_axis = 'Retention Rate (%/month)'
                elif ranking_criteria == 'hmw_formation':
                    value = -scores['hmw_increase_rate'] if scores['hmw_increase_rate'] else 0
                    title = 'HMW Formation Resistance (Higher = Better)'
                    y_axis = 'Resistance Score'
                else:  # temperature
                    # For temperature, we'll use a placeholder - would need Tm data
                    value = 70  # Placeholder
                    title = 'Temperature Stability'
                    y_axis = 'Temperature (°C)'
                
                ranking_data.append({
                    'formulation': f"Form {formulation_number}",
                    'condition': condition_label,
                    'value': value,
                    'label': f"Form {formulation_number} - {condition_label}"
                })
        
        if not ranking_data:
            return go.Figure()
        
        df = pd.DataFrame(ranking_data)
        df_sorted = df.sort_values('value', ascending=False)
        
        # Create color scale based on values
        colors = ['#d62728' if v < 50 else '#ff7f0e' if v < 70 else '#2ca02c' 
                 for v in df_sorted['value']]
        
        fig = go.Figure(data=go.Bar(
            x=df_sorted['label'],
            y=df_sorted['value'],
            marker_color=colors,
            hovertemplate='<b>%{x}</b><br>' + f'{title}: %{{y:.1f}}<extra></extra>'
        ))
        
        fig.update_layout(
            title=f'Formulation Ranking: {title}',
            xaxis_title='Formulation - Storage Condition',
            yaxis_title=y_axis,
            template='plotly_white',
            xaxis=dict(tickangle=-45)
        )
        
        return fig
        
    except Exception as e:
        print(f"Error creating ranking plot: {e}")
        return go.Figure().add_annotation(
            text=f"Error creating plot: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )

@app.callback(
    Output('top-performers-list', 'children'),
    Input('formulation-data-store', 'data'),
    Input('ranking-criteria', 'value'),
    prevent_initial_call=True
)
def update_top_performers(formulation_data, ranking_criteria):
    """Create top performers list"""
    if not formulation_data:
        return html.Div("No data available")
    
    try:
        performers = []
        
        for formulation_id, formulation_info in formulation_data.items():
            formulation_number = formulation_info['formulation_info']['number']
            composition = formulation_info['formulation_info']['composition']
            stability_scores = calculate_stability_score(formulation_info)
            
            # Calculate average score across conditions
            scores = [s['stability_score'] for s in stability_scores.values()]
            avg_score = np.mean(scores) if scores else 0
            
            performers.append({
                'formulation': formulation_number,
                'composition': composition,
                'score': avg_score
            })
        
        # Sort by score
        performers.sort(key=lambda x: x['score'], reverse=True)
        
        # Create list items
        list_items = []
        for i, performer in enumerate(performers[:5]):  # Top 5
            badge_color = "success" if i == 0 else "primary" if i < 3 else "secondary"
            
            list_item = dbc.ListGroupItem([
                html.Div([
                    dbc.Badge(f"#{i+1}", color=badge_color, className="me-2"),
                    html.Strong(f"Formulation {performer['formulation']}"),
                    html.Br(),
                    html.Small(performer['composition'], className="text-muted"),
                    dbc.Badge(f"{performer['score']:.1f}", 
                             color=badge_color, className="float-end")
                ])
            ])
            list_items.append(list_item)
        
        return dbc.ListGroup(list_items)
        
    except Exception as e:
        print(f"Error creating top performers list: {e}")
        return html.Div(f"Error: {str(e)}")

@app.callback(
    Output('statistical-analysis-table', 'children'),
    Input('formulation-data-store', 'data'),
    prevent_initial_call=True
)
def update_statistical_analysis_table(formulation_data):
    """Create comprehensive statistical analysis table"""
    if not formulation_data:
        return html.Div("No statistical data available")
    
    try:
        comparison_df = create_comparison_dataframe(formulation_data)
        
        if comparison_df.empty:
            return html.Div("No statistical data available")
        
        return dash_table.DataTable(
            data=comparison_df.to_dict('records'),
            columns=[
                {'name': 'Formulation', 'id': 'Formulation_Number'},
                {'name': 'Storage', 'id': 'Storage_Condition'},
                {'name': 'Stability Score', 'id': 'Stability_Score', 'type': 'numeric', 'format': {'specifier': '.1f'}},
                {'name': 'Main Rate (%/month)', 'id': 'Main_Degradation_Rate_per_month', 'type': 'numeric', 'format': {'specifier': '.3f'}},
                {'name': 'HMW Rate (%/month)', 'id': 'HMW_Increase_Rate_per_month', 'type': 'numeric', 'format': {'specifier': '.3f'}},
                {'name': 'Main R²', 'id': 'Main_R_Squared', 'type': 'numeric', 'format': {'specifier': '.3f'}},
                {'name': 'Shelf Life (months)', 'id': 'Estimated_Shelf_Life_months', 'type': 'numeric', 'format': {'specifier': '.1f'}}
            ],
            style_cell={
                'textAlign': 'center',
                'padding': '10px',
                'fontFamily': 'Arial, sans-serif',
                'fontSize': '12px',
                'minWidth': '100px'
            },
            style_header={
                'backgroundColor': COLOR_PALETTE['dark'],
                'color': 'white',
                'fontWeight': 'bold',
                'textAlign': 'center'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': COLOR_PALETTE['light']
                },
                {
                    'if': {
                        'filter_query': '{Stability_Score} > 80',
                        'column_id': 'Stability_Score'
                    },
                    'backgroundColor': COLOR_PALETTE['success'],
                    'color': 'white'
                },
                {
                    'if': {
                        'filter_query': '{Stability_Score} < 60',
                        'column_id': 'Stability_Score'
                    },
                    'backgroundColor': COLOR_PALETTE['secondary'],
                    'color': 'white'
                }
            ],
            sort_action='native',
            filter_action='native',
            export_format='xlsx',
            page_size=20
        )
        
    except Exception as e:
        print(f"Error creating statistical analysis table: {e}")
        return html.Div(f"Error creating table: {str(e)}")

@app.callback(
    Output('physical-properties-chart', 'figure'),
    Input('formulation-data-store', 'data'),
    prevent_initial_call=True
)
def update_physical_properties_chart(formulation_data):
    """Create physical properties comparison chart"""
    if not formulation_data:
        return go.Figure()
    
    try:
        from plotly_integration.models import FormulationCondition
        
        formulations = []
        ph_values = []
        osmolality_values = []
        
        for formulation_id, formulation_info in formulation_data.items():
            formulation_number = formulation_info['formulation_info']['number']
            formulation = FormulationCondition.objects.get(id=formulation_id)
            
            formulations.append(f"Form {formulation_number}")
            ph_values.append(formulation.ph)
            osmolality_values.append(formulation.osmolality if formulation.osmolality else 0)
        
        fig = go.Figure()
        
        # Add pH bars
        fig.add_trace(go.Bar(
            name='pH',
            x=formulations,
            y=ph_values,
            yaxis='y1',
            marker_color=COLOR_PALETTE['primary']
        ))
        
        # Add osmolality bars on secondary y-axis
        fig.add_trace(go.Bar(
            name='Osmolality (mOsm/kg)',
            x=formulations,
            y=osmolality_values,
            yaxis='y2',
            marker_color=COLOR_PALETTE['warning'],
            opacity=0.7
        ))
        
        fig.update_layout(
            title='Formulation Physical Properties',
            xaxis_title='Formulation',
            yaxis=dict(
                title='pH',
                side='left',
                color=COLOR_PALETTE['primary']
            ),
            yaxis2=dict(
                title='Osmolality (mOsm/kg)',
                side='right',
                overlaying='y',
                color=COLOR_PALETTE['warning']
            ),
            template='plotly_white',
            barmode='group'
        )
        
        return fig
        
    except Exception as e:
        print(f"Error creating physical properties chart: {e}")
        return go.Figure().add_annotation(
            text=f"Error creating chart: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )