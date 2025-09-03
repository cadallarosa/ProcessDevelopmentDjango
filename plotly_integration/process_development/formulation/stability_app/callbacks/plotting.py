"""
Callbacks for plotting and visualization
"""

from dash import Input, Output, State, dash_table, html
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import pandas as pd
import numpy as np
from scipy import stats

from ..formulation_stability_app import app, COLOR_PALETTE, STORAGE_CONDITIONS
from ..utils.data_processing import calculate_degradation_rates, calculate_stability_score

@app.callback(
    Output('stability-trends-plot', 'figure'),
    Input('formulation-data-store', 'data'),
    Input('parameter-selector', 'value'),
    Input('show-trendlines', 'value'),
    prevent_initial_call=True
)
def update_stability_trends_plot(formulation_data, selected_parameter, show_trendlines):
    """Create stability trends plot"""
    if not formulation_data:
        return go.Figure()
    
    try:
        fig = go.Figure()
        
        parameter_mapping = {
            'main': {'field': 'main_values', 'title': 'Main Peak (%)', 'yaxis': 'Main Peak (%)'},
            'hmw': {'field': 'hmw_values', 'title': 'HMW Aggregates (%)', 'yaxis': 'HMW (%)'},
            'lmw': {'field': 'lmw_values', 'title': 'LMW Fragments (%)', 'yaxis': 'LMW (%)'},
            'tm': {'field': 'tm_values', 'title': 'Melting Temperature (°C)', 'yaxis': 'Tm (°C)'},
            'scattering': {'field': 'scattering_onset_values', 'title': 'Scattering Onset (°C)', 'yaxis': 'Scattering Onset (°C)'}
        }
        
        param_info = parameter_mapping.get(selected_parameter, parameter_mapping['main'])
        
        colors = px.colors.qualitative.Set1
        formulation_colors = {}
        color_index = 0
        
        for formulation_id, formulation_info in formulation_data.items():
            formulation_number = formulation_info['formulation_info']['number']
            base_color = colors[color_index % len(colors)]
            formulation_colors[formulation_id] = base_color
            color_index += 1
            
            for storage_condition, data in formulation_info['storage_conditions'].items():
                if not data['time_points'] or not data.get(param_info['field']):
                    continue
                
                x_values = data['time_points']
                y_values = data[param_info['field']]
                
                # Filter out None values
                valid_pairs = [(x, y) for x, y in zip(x_values, y_values) if y is not None]
                if not valid_pairs:
                    continue
                
                x_filtered, y_filtered = zip(*valid_pairs)
                
                condition_info = STORAGE_CONDITIONS.get(storage_condition, {"label": storage_condition, "color": base_color})
                
                # Add scatter plot
                fig.add_trace(go.Scatter(
                    x=x_filtered,
                    y=y_filtered,
                    mode='markers+lines',
                    name=f'Form {formulation_number} - {condition_info["label"]}',
                    marker=dict(
                        color=base_color,
                        size=8,
                        symbol='circle' if storage_condition == '25C' else 'square' if storage_condition == '40C' else 'diamond'
                    ),
                    line=dict(color=base_color, width=2),
                    hovertemplate=f'<b>Formulation {formulation_number}</b><br>' +
                                 f'{condition_info["label"]}<br>' +
                                 f'Time: %{{x}} months<br>' +
                                 f'{param_info["title"]}: %{{y}}<br>' +
                                 '<extra></extra>'
                ))
                
                # Add trend line if requested
                if show_trendlines and len(x_filtered) >= 2:
                    trend_stats = calculate_degradation_rates(list(x_filtered), list(y_filtered), selected_parameter)
                    
                    if trend_stats and trend_stats['r_squared'] > 0.1:  # Only show meaningful trends
                        x_trend = np.linspace(min(x_filtered), max(x_filtered), 100)
                        y_trend = trend_stats['slope'] * x_trend + trend_stats['intercept']
                        
                        fig.add_trace(go.Scatter(
                            x=x_trend,
                            y=y_trend,
                            mode='lines',
                            name=f'Trend - Form {formulation_number} ({condition_info["label"]})',
                            line=dict(
                                color=base_color,
                                width=1,
                                dash='dash'
                            ),
                            showlegend=False,
                            hovertemplate=f'<b>Trend Line</b><br>' +
                                         f'Slope: {trend_stats["slope"]:.3f} per month<br>' +
                                         f'R²: {trend_stats["r_squared"]:.3f}<br>' +
                                         '<extra></extra>'
                        ))
        
        fig.update_layout(
            title=dict(
                text=f'Stability Trends: {param_info["title"]}',
                x=0.5,
                font=dict(size=18, color=COLOR_PALETTE["dark"])
            ),
            xaxis_title="Time (months)",
            yaxis_title=param_info["yaxis"],
            hovermode='closest',
            template='plotly_white',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            margin=dict(t=80)
        )
        
        return fig
        
    except Exception as e:
        print(f"Error creating stability trends plot: {e}")
        return go.Figure().add_annotation(
            text=f"Error creating plot: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )

@app.callback(
    Output('degradation-rates-table', 'children'),
    Input('formulation-data-store', 'data'),
    prevent_initial_call=True
)
def update_degradation_rates_table(formulation_data):
    """Create degradation rates table"""
    if not formulation_data:
        return html.Div("No data available")
    
    try:
        rows = []
        
        for formulation_id, formulation_info in formulation_data.items():
            formulation_number = formulation_info['formulation_info']['number']
            study_id = formulation_info['formulation_info']['study']
            
            for storage_condition, data in formulation_info['storage_conditions'].items():
                if not data['time_points'] or not data['main_values']:
                    continue
                
                # Calculate degradation rates
                main_stats = calculate_degradation_rates(
                    data['time_points'], data['main_values'], 'main_percent'
                )
                hmw_stats = calculate_degradation_rates(
                    data['time_points'], data['hmw_values'], 'hmw_percent'
                )
                lmw_stats = calculate_degradation_rates(
                    data['time_points'], data['lmw_values'], 'lmw_percent'
                )
                
                condition_label = STORAGE_CONDITIONS.get(storage_condition, {"label": storage_condition})["label"]
                
                row = {
                    'Study': study_id,
                    'Formulation': formulation_number,
                    'Storage Condition': condition_label,
                    'Main Degradation (%/month)': f"{main_stats['slope']:.3f}" if main_stats else "N/A",
                    'Main R²': f"{main_stats['r_squared']:.3f}" if main_stats else "N/A",
                    'HMW Increase (%/month)': f"{hmw_stats['slope']:.3f}" if hmw_stats else "N/A",
                    'HMW R²': f"{hmw_stats['r_squared']:.3f}" if hmw_stats else "N/A",
                    'LMW Increase (%/month)': f"{lmw_stats['slope']:.3f}" if lmw_stats else "N/A",
                    'LMW R²': f"{lmw_stats['r_squared']:.3f}" if lmw_stats else "N/A",
                    'Half Life (months)': f"{main_stats['half_life_months']:.1f}" if main_stats and main_stats['half_life_months'] else "N/A"
                }
                rows.append(row)
        
        if not rows:
            return html.Div("No degradation data available")
        
        df = pd.DataFrame(rows)
        
        return dash_table.DataTable(
            data=df.to_dict('records'),
            columns=[{'name': col, 'id': col} for col in df.columns],
            style_cell={
                'textAlign': 'center',
                'padding': '10px',
                'fontFamily': 'Arial, sans-serif',
                'fontSize': '14px'
            },
            style_header={
                'backgroundColor': COLOR_PALETTE['primary'],
                'color': 'white',
                'fontWeight': 'bold',
                'textAlign': 'center'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': COLOR_PALETTE['light']
                }
            ],
            sort_action='native',
            filter_action='native',
            export_format='xlsx',
            export_headers='display'
        )
        
    except Exception as e:
        print(f"Error creating degradation rates table: {e}")
        return html.Div(f"Error creating table: {str(e)}")

@app.callback(
    Output('performance-heatmap', 'figure'),
    Input('formulation-data-store', 'data'),
    prevent_initial_call=True
)
def update_performance_heatmap(formulation_data):
    """Create performance heatmap"""
    if not formulation_data:
        return go.Figure()
    
    try:
        # Prepare data for heatmap
        formulations = []
        conditions = []
        scores = []
        
        for formulation_id, formulation_info in formulation_data.items():
            formulation_number = formulation_info['formulation_info']['number']
            stability_scores = calculate_stability_score(formulation_info)
            
            for condition, score_info in stability_scores.items():
                formulations.append(f"Formulation {formulation_number}")
                conditions.append(STORAGE_CONDITIONS.get(condition, {"label": condition})["label"])
                scores.append(score_info['stability_score'])
        
        if not scores:
            return go.Figure()
        
        # Create pivot table for heatmap
        df = pd.DataFrame({
            'Formulation': formulations,
            'Condition': conditions,
            'Score': scores
        })
        
        pivot_df = df.pivot(index='Formulation', columns='Condition', values='Score')
        
        fig = go.Figure(data=go.Heatmap(
            z=pivot_df.values,
            x=pivot_df.columns,
            y=pivot_df.index,
            colorscale='RdYlGn',
            text=pivot_df.values.round(1),
            texttemplate="%{text}",
            textfont={"size": 12},
            hovertemplate='<b>%{y}</b><br>%{x}<br>Score: %{z:.1f}<extra></extra>'
        ))
        
        fig.update_layout(
            title='Formulation Stability Performance Heatmap',
            xaxis_title='Storage Condition',
            yaxis_title='Formulation',
            template='plotly_white'
        )
        
        return fig
        
    except Exception as e:
        print(f"Error creating performance heatmap: {e}")
        return go.Figure().add_annotation(
            text=f"Error creating heatmap: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )