"""
Formulation Dashboard App
Overview dashboard and reporting features for formulation experiments
"""

import dash
from dash import dcc, html, Input, Output, State, dash_table, no_update
import dash
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from django.db.models import Count, Avg, Q
from plotly_integration.models import (
    FormulationExperiment, 
    FormulationMatrix, 
    FormulationComponent, 
    FormulationSample
)

app = DjangoDash("FormulationDashboardApp", external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
], suppress_callback_exceptions=True)

def get_dashboard_statistics():
    """Get overall statistics for dashboard"""
    stats = {
        'total_experiments': FormulationExperiment.objects.count(),
        'total_formulations': FormulationMatrix.objects.count(),
        'total_samples': FormulationSample.objects.count(),
        'analyzed_samples': FormulationSample.objects.filter(hmw__isnull=False).count(),
        'active_experiments': FormulationExperiment.objects.filter(
            formulations__samples__pull_date__gte=datetime.now().date() - timedelta(days=90)
        ).distinct().count()
    }
    
    # Calculate analysis completion rate
    if stats['total_samples'] > 0:
        stats['completion_rate'] = round((stats['analyzed_samples'] / stats['total_samples']) * 100, 1)
    else:
        stats['completion_rate'] = 0
    
    return stats

def get_recent_experiments():
    """Get recent experiments with details"""
    experiments = FormulationExperiment.objects.annotate(
        formulation_count=Count('formulations'),
        sample_count=Count('formulations__samples'),
        analyzed_count=Count('formulations__samples', filter=Q(formulations__samples__hmw__isnull=False))
    ).order_by('-created_date')[:10]
    
    data = []
    for exp in experiments:
        completion_rate = 0
        if exp.sample_count > 0:
            completion_rate = round((exp.analyzed_count / exp.sample_count) * 100, 1)
        
        data.append({
            'experiment_id': exp.experiment_id,
            'name': exp.name,
            'molecule': exp.molecule,
            'formulations': exp.formulation_count,
            'samples': exp.sample_count,
            'analyzed': exp.analyzed_count,
            'completion': f"{completion_rate}%",
            'created_date': exp.created_date.strftime('%Y-%m-%d'),
            'status': 'Active' if exp.sample_count > exp.analyzed_count else 'Complete'
        })
    
    return data

def get_stability_trends_data(experiment_id=None):
    """Get stability data for trending analysis"""
    query = FormulationSample.objects.filter(
        hmw__isnull=False, 
        main__isnull=False,
        time_point_months__isnull=False
    ).select_related('formulation__experiment')
    
    if experiment_id:
        query = query.filter(formulation__experiment_id=experiment_id)
    
    samples = query.order_by('time_point_months')
    
    data = []
    for sample in samples:
        data.append({
            'experiment_id': sample.formulation.experiment_id,
            'experiment_name': sample.formulation.experiment.name,
            'formulation_number': sample.formulation.formulation_number,
            'formulation_ph': sample.formulation.target_ph,
            'storage_condition': sample.storage_condition,
            'time_point_months': sample.time_point_months,
            'hmw': sample.hmw,
            'main': sample.main,
            'lmw': sample.lmw,
            'tm_celsius': sample.tm_celsius,
            'sample_id': sample.sample_id
        })
    
    return pd.DataFrame(data)

def create_summary_cards():
    """Create summary statistics cards"""
    stats = get_dashboard_statistics()
    
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(stats['total_experiments'], className="text-primary mb-0"),
                    html.P("Total Experiments", className="text-muted mb-0"),
                    html.I(className="fas fa-flask fa-2x text-primary position-absolute top-0 end-0 mt-3 me-3")
                ], className="position-relative")
            ])
        ], md=2),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(stats['active_experiments'], className="text-success mb-0"),
                    html.P("Active Experiments", className="text-muted mb-0"),
                    html.I(className="fas fa-play-circle fa-2x text-success position-absolute top-0 end-0 mt-3 me-3")
                ], className="position-relative")
            ])
        ], md=2),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(stats['total_formulations'], className="text-info mb-0"),
                    html.P("Formulations", className="text-muted mb-0"),
                    html.I(className="fas fa-vial fa-2x text-info position-absolute top-0 end-0 mt-3 me-3")
                ], className="position-relative")
            ])
        ], md=2),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(stats['total_samples'], className="text-warning mb-0"),
                    html.P("Total Samples", className="text-muted mb-0"),
                    html.I(className="fas fa-test-tube fa-2x text-warning position-absolute top-0 end-0 mt-3 me-3")
                ], className="position-relative")
            ])
        ], md=2),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(stats['analyzed_samples'], className="text-success mb-0"),
                    html.P("Analyzed", className="text-muted mb-0"),
                    html.I(className="fas fa-chart-line fa-2x text-success position-absolute top-0 end-0 mt-3 me-3")
                ], className="position-relative")
            ])
        ], md=2),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H3(f"{stats['completion_rate']}%", className="text-secondary mb-0"),
                    html.P("Complete", className="text-muted mb-0"),
                    html.I(className="fas fa-percentage fa-2x text-secondary position-absolute top-0 end-0 mt-3 me-3")
                ], className="position-relative")
            ])
        ], md=2)
    ], className="mb-4")

# Layout
app.layout = dbc.Container([
    dcc.Store(id="selected-experiment-store"),
    dcc.Interval(id="dashboard-refresh", interval=60000, n_intervals=0),  # Refresh every minute
    
    # Header
    dbc.Row([
        dbc.Col([
            html.H1([
                html.I(className="fas fa-chart-pie text-primary me-3"),
                "Formulation Dashboard"
            ], className="mb-3"),
            html.P("Overview of formulation experiments, progress, and stability trends", 
                   className="lead text-muted")
        ], width=8),
        dbc.Col([
            dbc.Button(
                [html.I(className="fas fa-sync me-2"), "Refresh"],
                id="refresh-dashboard-btn",
                color="secondary",
                outline=True,
                className="mt-3"
            )
        ], width=4, className="text-end")
    ]),
    
    # Summary Cards
    html.Div(id="summary-cards-container"),
    
    # Main Dashboard Content
    dbc.Row([
        # Recent Experiments Table
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H5([html.I(className="fas fa-list me-2"), "Recent Experiments"], className="mb-0")
                ]),
                dbc.CardBody([
                    html.Div(id="recent-experiments-table")
                ])
            ])
        ], width=7),
        
        # Quick Actions
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H5([html.I(className="fas fa-rocket me-2"), "Quick Actions"], className="mb-0")
                ]),
                dbc.CardBody([
                    dbc.ListGroup([
                        dbc.ListGroupItem([
                            html.I(className="fas fa-plus me-3"),
                            html.Span("Create New Experiment"),
                        ], action=True, id="quick-new-experiment", 
                           style={"cursor": "pointer"}),
                        dbc.ListGroupItem([
                            html.I(className="fas fa-vials me-3"),
                            html.Span("Design Formulations"),
                        ], action=True, id="quick-design-formulations",
                           style={"cursor": "pointer"}),
                        dbc.ListGroupItem([
                            html.I(className="fas fa-calendar-plus me-3"),
                            html.Span("Generate Samples"),
                        ], action=True, id="quick-generate-samples",
                           style={"cursor": "pointer"}),
                        dbc.ListGroupItem([
                            html.I(className="fas fa-table me-3"),
                            html.Span("Enter Analytical Data"),
                        ], action=True, id="quick-data-entry",
                           style={"cursor": "pointer"}),
                        dbc.ListGroupItem([
                            html.I(className="fas fa-chart-line me-3"),
                            html.Span("View Stability Analysis"),
                        ], action=True, id="quick-stability-analysis",
                           style={"cursor": "pointer"}),
                        dbc.ListGroupItem([
                            html.I(className="fas fa-flask me-3"),
                            html.Span("Experiment Manager"),
                        ], action=True, id="quick-experiment-manager",
                           style={"cursor": "pointer"}),
                    ], flush=True)
                ])
            ])
        ], width=5)
    ], className="mb-4"),
    
    # Stability Trends Section
    dbc.Card([
        dbc.CardHeader([
            dbc.Row([
                dbc.Col([
                    html.H5([html.I(className="fas fa-chart-line me-2"), "Stability Trends Overview"], className="mb-0")
                ], width=6),
                dbc.Col([
                    dcc.Dropdown(
                        id="trend-experiment-filter",
                        placeholder="All experiments",
                        className="mb-0"
                    )
                ], width=6)
            ])
        ]),
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id="hmw-trends-plot")
                ], width=6),
                dbc.Col([
                    dcc.Graph(id="main-trends-plot")
                ], width=6)
            ]),
            dbc.Row([
                dbc.Col([
                    dcc.Graph(id="thermal-stability-plot")
                ], width=6),
                dbc.Col([
                    html.Div(id="stability-summary-stats")
                ], width=6)
            ])
        ])
    ], className="mb-4"),
    
    # Alerts
    html.Div(id="dashboard-alerts")
    
], fluid=True)

@app.callback(
    [Output("summary-cards-container", "children"),
     Output("recent-experiments-table", "children"),
     Output("trend-experiment-filter", "options")],
    [Input("dashboard-refresh", "n_intervals"),
     Input("refresh-dashboard-btn", "n_clicks")]
)
def update_dashboard_data(n_intervals, refresh_clicks):
    # Summary cards
    summary_cards = create_summary_cards()
    
    # Recent experiments table
    recent_data = get_recent_experiments()
    recent_table = dash_table.DataTable(
        data=recent_data,
        columns=[
            {'name': 'Experiment ID', 'id': 'experiment_id'},
            {'name': 'Name', 'id': 'name'},
            {'name': 'Molecule', 'id': 'molecule'},
            {'name': 'Forms', 'id': 'formulations', 'type': 'numeric'},
            {'name': 'Samples', 'id': 'samples', 'type': 'numeric'},
            {'name': 'Analyzed', 'id': 'analyzed', 'type': 'numeric'},
            {'name': 'Complete', 'id': 'completion'},
            {'name': 'Status', 'id': 'status'},
            {'name': 'Created', 'id': 'created_date'}
        ],
        style_cell={'textAlign': 'left'},
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': 'rgb(248, 248, 248)'
            },
            {
                'if': {'filter_query': '{status} = Active', 'column_id': 'status'},
                'backgroundColor': '#d4edda',
                'color': 'black',
            },
            {
                'if': {'filter_query': '{status} = Complete', 'column_id': 'status'},
                'backgroundColor': '#b3e5fc',
                'color': 'black',
            }
        ],
        page_size=8,
        sort_action="native"
    )
    
    # Experiment filter options
    experiments = FormulationExperiment.objects.all().order_by('-created_date')
    experiment_options = [{'label': f"{exp.experiment_id} - {exp.name}", 'value': exp.experiment_id} 
                         for exp in experiments]
    
    return summary_cards, recent_table, experiment_options

@app.callback(
    [Output("hmw-trends-plot", "figure"),
     Output("main-trends-plot", "figure"),
     Output("thermal-stability-plot", "figure"),
     Output("stability-summary-stats", "children")],
    Input("trend-experiment-filter", "value")
)
def update_stability_trends(selected_experiment):
    # Get stability data
    df = get_stability_trends_data(selected_experiment)
    
    if df.empty:
        empty_fig = go.Figure()
        empty_fig.add_annotation(text="No data available", 
                               xref="paper", yref="paper",
                               x=0.5, y=0.5, showarrow=False)
        empty_fig.update_layout(showlegend=False)
        
        return empty_fig, empty_fig, empty_fig, html.P("No data available", className="text-muted")
    
    # HMW trends plot
    hmw_fig = px.scatter(df, 
                        x='time_point_months', 
                        y='hmw',
                        color='storage_condition',
                        symbol='formulation_number',
                        hover_data=['experiment_id', 'sample_id'],
                        title="High Molecular Weight % Over Time")
    hmw_fig.update_layout(xaxis_title="Time (months)", yaxis_title="HMW %")
    
    # Main peak trends plot  
    main_fig = px.scatter(df,
                         x='time_point_months',
                         y='main', 
                         color='storage_condition',
                         symbol='formulation_number',
                         hover_data=['experiment_id', 'sample_id'],
                         title="Main Peak % Over Time")
    main_fig.update_layout(xaxis_title="Time (months)", yaxis_title="Main %")
    
    # Thermal stability plot
    thermal_df = df.dropna(subset=['tm_celsius'])
    if not thermal_df.empty:
        thermal_fig = px.scatter(thermal_df,
                                x='time_point_months',
                                y='tm_celsius',
                                color='storage_condition', 
                                symbol='formulation_number',
                                hover_data=['experiment_id', 'sample_id'],
                                title="Thermal Stability (Tm) Over Time")
        thermal_fig.update_layout(xaxis_title="Time (months)", yaxis_title="Tm (°C)")
    else:
        thermal_fig = go.Figure()
        thermal_fig.add_annotation(text="No thermal data available",
                                  xref="paper", yref="paper",
                                  x=0.5, y=0.5, showarrow=False)
        thermal_fig.update_layout(showlegend=False, title="Thermal Stability (Tm) Over Time")
    
    # Summary statistics
    summary_stats = []
    
    # Calculate averages by storage condition
    condition_stats = df.groupby('storage_condition').agg({
        'hmw': 'mean',
        'main': 'mean',
        'tm_celsius': 'mean'
    }).round(2)
    
    for condition in condition_stats.index:
        stats = condition_stats.loc[condition]
        summary_stats.append(
            dbc.ListGroupItem([
                html.H6(f"{condition} Storage", className="mb-1"),
                html.P([
                    f"Avg HMW: {stats['hmw']:.1f}% | ",
                    f"Avg Main: {stats['main']:.1f}% | ",
                    f"Avg Tm: {stats['tm_celsius']:.1f}°C" if not pd.isna(stats['tm_celsius']) else "No Tm data"
                ], className="mb-1 small text-muted")
            ])
        )
    
    summary_component = dbc.ListGroup(summary_stats, flush=True) if summary_stats else html.P("No data to summarize", className="text-muted")
    
    return hmw_fig, main_fig, thermal_fig, summary_component

# Client-side callback to handle navigation to parent window
app.clientside_callback(
    """
    function(n1, n2, n3, n4, n5, n6) {
        // Get the triggered element
        const triggered = dash_clientside.callback_context.triggered[0];
        if (!triggered || triggered.value === undefined) {
            return window.dash_clientside.no_update;
        }
        
        // Map button IDs to their target routes
        const routes = {
            'quick-new-experiment': '#!/formulation/create-experiment',
            'quick-design-formulations': '#!/formulation/design',
            'quick-generate-samples': '#!/formulation/samples',
            'quick-data-entry': '#!/formulation/data-entry',
            'quick-stability-analysis': '#!/formulation/stability',
            'quick-experiment-manager': '#!/formulation/experiment-manager'
        };
        
        // Get the route for the clicked button
        const buttonId = triggered.prop_id.split('.')[0];
        const targetRoute = routes[buttonId];
        
        if (targetRoute) {
            // Check if we're in an iframe
            if (window.parent !== window) {
                // Navigate the parent window
                window.parent.location.href = window.parent.location.pathname + targetRoute;
            } else {
                // Navigate the current window
                window.location.href = window.location.pathname + targetRoute;
            }
        }
        
        return window.dash_clientside.no_update;
    }
    """,
    Output("quick-new-experiment", "n_clicks_timestamp"),
    [Input("quick-new-experiment", "n_clicks"),
     Input("quick-design-formulations", "n_clicks"),
     Input("quick-generate-samples", "n_clicks"),
     Input("quick-data-entry", "n_clicks"),
     Input("quick-stability-analysis", "n_clicks"),
     Input("quick-experiment-manager", "n_clicks")],
    prevent_initial_call=True
)