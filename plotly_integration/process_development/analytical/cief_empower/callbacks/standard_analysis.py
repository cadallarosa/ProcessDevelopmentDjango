from dash import Input, Output, State, html, callback_context
import numpy as np
from scipy.stats import linregress
import plotly.graph_objects as go

from ..app import app

@app.callback(
    Output("main-tabs", "style"),
    Output("sample-analysis-content", "style"), 
    Output("standard-analysis-content", "style"),
    Input("main-tabs", "value"),
    State('tab-visibility-store', 'data')
)
def toggle_tab_content(active_tab, tab_visibility):
    # Base tab style
    tab_style = {'marginTop': '10px'}
    
    if active_tab == "sample-analysis":
        sample_style = {'display': 'block', 'padding': '20px'}
        standard_style = {'display': 'none', 'padding': '20px'}
    else:  # standard-analysis
        sample_style = {'display': 'none', 'padding': '20px'}
        standard_style = {'display': 'block', 'padding': '20px'}
    
    return tab_style, sample_style, standard_style

@app.callback(
    Output("pi-regression-data", "data"),
    Output("regression-results", "children"),
    Input("calc-regression-btn", "n_clicks"),
    State("peak-results-table", "data"),
    prevent_initial_call=True
)
def calculate_pi_regression(n_clicks, table_data):
    if not n_clicks or not table_data:
        return {'slope': 0, 'intercept': 0, 'r_squared': 0}, html.Div([
            html.P("No data available for regression analysis", style={'color': '#e74c3c'})
        ])
    
    # Extract pI markers from table
    pi_markers = []
    for row in table_data:
        if row.get('is_pi_marker') == 'Yes':
            retention_time = row.get('retention_time')
            # You'll need to get the actual pI value - for now using default markers
            # This should be enhanced to allow user input of pI values
            if retention_time is not None:
                pi_markers.append({
                    'time': retention_time,
                    'pi': None  # To be filled based on user selection
                })
    
    if len(pi_markers) < 2:
        return {'slope': 0, 'intercept': 0, 'r_squared': 0}, html.Div([
            html.P("⚠️ Need at least 2 pI markers selected for regression", style={'color': '#e74c3c'})
        ])
    
    # For now, use default pI values - this should be enhanced
    default_pis = [10.0, 9.5, 5.5, 4.0]
    times = [marker['time'] for marker in pi_markers[:len(default_pis)]]
    pis = default_pis[:len(pi_markers)]
    
    if len(times) != len(pis):
        return {'slope': 0, 'intercept': 0, 'r_squared': 0}, html.Div([
            html.P("⚠️ Mismatch between selected markers and pI values", style={'color': '#e74c3c'})
        ])
    
    # Perform linear regression
    slope, intercept, r_value, p_value, std_err = linregress(times, pis)
    r_squared = r_value ** 2
    
    # Create results display
    results = html.Div([
        html.H4("Linear Regression Results", style={'color': '#2563eb', 'marginBottom': '15px'}),
        html.Div(
            style={'display': 'grid', 'gridTemplateColumns': 'repeat(3, 1fr)', 'gap': '20px'},
            children=[
                html.Div([
                    html.P("Slope:", style={'fontSize': '12px', 'color': '#666', 'marginBottom': '5px'}),
                    html.P(f"{slope:.4f}", style={'fontSize': '20px', 'fontWeight': 'bold', 'color': '#333'})
                ]),
                html.Div([
                    html.P("Intercept:", style={'fontSize': '12px', 'color': '#666', 'marginBottom': '5px'}),
                    html.P(f"{intercept:.4f}", style={'fontSize': '20px', 'fontWeight': 'bold', 'color': '#333'})
                ]),
                html.Div([
                    html.P("R²:", style={'fontSize': '12px', 'color': '#666', 'marginBottom': '5px'}),
                    html.P(f"{r_squared:.4f}", style={'fontSize': '20px', 'fontWeight': 'bold', 'color': '#333'})
                ])
            ]
        ),
        html.Div([
            html.P(f"pI = {slope:.4f} × retention_time + {intercept:.4f}", 
                  style={'marginTop': '15px', 'padding': '15px', 'backgroundColor': '#e8f4fd', 
                        'borderRadius': '8px', 'fontFamily': 'monospace', 'textAlign': 'center',
                        'fontSize': '16px', 'fontWeight': '600'})
        ]),
        html.Div([
            html.P(f"Markers used: {len(pi_markers)} | P-value: {p_value:.6f} | Std Error: {std_err:.4f}",
                  style={'marginTop': '10px', 'fontSize': '12px', 'color': '#666', 'textAlign': 'center'})
        ])
    ])
    
    return {'slope': slope, 'intercept': intercept, 'r_squared': r_squared, 'p_value': p_value, 'std_err': std_err}, results

@app.callback(
    Output("pi-calibration-plot", "figure"),
    Input("pi-regression-data", "data"),
    State("peak-results-table", "data")
)
def update_calibration_plot(regression_data, table_data):
    fig = go.Figure()
    
    if not regression_data or regression_data.get('slope') == 0:
        fig.update_layout(
            title="pI Calibration Curve - No regression data available",
            xaxis_title="Retention Time (min)",
            yaxis_title="pI",
            height=400,
            template="plotly_white"
        )
        return fig
    
    # Extract pI markers from table
    marker_times = []
    marker_pis = []
    
    if table_data:
        # Use default pI values for selected markers
        default_pis = [10.0, 9.5, 5.5, 4.0]
        pi_idx = 0
        
        for row in table_data:
            if row.get('is_pi_marker') == 'Yes' and pi_idx < len(default_pis):
                marker_times.append(row.get('retention_time', 0))
                marker_pis.append(default_pis[pi_idx])
                pi_idx += 1
    
    if marker_times and marker_pis:
        # Add marker points
        fig.add_trace(
            go.Scatter(
                x=marker_times, 
                y=marker_pis,
                mode='markers', 
                name='pI Markers',
                marker=dict(color='blue', size=12, symbol='diamond')
            )
        )
        
        # Add regression line
        slope = regression_data.get('slope', 0)
        intercept = regression_data.get('intercept', 0)
        r_squared = regression_data.get('r_squared', 0)
        
        x_range = np.linspace(min(marker_times) - 1, max(marker_times) + 1, 100)
        y_range = slope * x_range + intercept
        
        fig.add_trace(
            go.Scatter(
                x=x_range, 
                y=y_range,
                mode='lines', 
                name=f'Linear Fit (R² = {r_squared:.4f})',
                line=dict(color='red', dash='dash', width=2)
            )
        )
        
        # Add equation annotation
        fig.add_annotation(
            x=0.05, y=0.95,
            xref='paper', yref='paper',
            text=f'pI = {slope:.4f} × RT + {intercept:.4f}<br>R² = {r_squared:.4f}',
            showarrow=False,
            bgcolor='white',
            bordercolor='black',
            borderwidth=1,
            font=dict(size=12)
        )
    
    fig.update_layout(
        title="pI Calibration Curve",
        xaxis_title="Retention Time (min)",
        yaxis_title="pI",
        height=400,
        template="plotly_white",
        showlegend=True
    )
    
    return fig