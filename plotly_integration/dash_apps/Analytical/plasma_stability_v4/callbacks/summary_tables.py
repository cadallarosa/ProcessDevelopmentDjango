"""
Summary Tables Callback
Generates summary tables from analysis results
"""

from dash import Input, Output, State, html
from dash.exceptions import PreventUpdate

from ..components.summary_tables import create_summary_tables


def register_callbacks(app):
    """Register summary tables callbacks."""

    @app.callback(
        Output('summary-tables-container', 'children'),
        [Input('main-tabs', 'value'),
         Input('analysis-results-store', 'data')],
        prevent_initial_call=False
    )
    def generate_summary_tables(active_tab, analysis_results):
        """
        Generate summary tables when Summary Tables tab is selected.

        Args:
            active_tab: Currently active tab value
            analysis_results: Stored analysis results with molecule_data

        Returns:
            Summary tables component or placeholder message
        """
        # Only generate if on the summary tab
        if active_tab != 'tab-summary':
            raise PreventUpdate

        # Check if we have analysis results
        if not analysis_results:
            return html.Div(
                style={'textAlign': 'center', 'padding': '60px', 'color': '#6b7280'},
                children=[
                    html.I(className="fas fa-info-circle fa-3x mb-3", style={'color': '#cbd5e1'}),
                    html.P("No analysis results available. Please upload and analyze template data first.",
                           style={'fontSize': '16px', 'margin': '0'})
                ]
            )

        # Extract molecule_data
        molecule_data = analysis_results.get('molecule_data', {})

        if not molecule_data:
            return html.Div(
                style={'textAlign': 'center', 'padding': '60px', 'color': '#dc2626'},
                children=[
                    html.I(className="fas fa-exclamation-triangle fa-3x mb-3", style={'color': '#fca5a5'}),
                    html.P("Analysis results found but no molecule data available.",
                           style={'fontSize': '16px', 'margin': '0'}),
                    html.P("This may be due to an older analysis. Please re-run the analysis.",
                           style={'fontSize': '13px', 'margin': '8px 0 0 0', 'color': '#6b7280'})
                ]
            )

        try:
            # Generate summary tables
            print("\n" + "="*80)
            print("GENERATING SUMMARY TABLES")
            print("="*80)
            print(f"Molecules to process: {list(molecule_data.keys())}")

            # Create 4 summary tables
            summary_tables = create_summary_tables(molecule_data)

            print("✓ Summary tables generated successfully")
            print("="*80 + "\n")

            return summary_tables

        except Exception as e:
            print(f"\n✗ Error generating summary tables: {str(e)}")
            import traceback
            traceback.print_exc()
            print("="*80 + "\n")

            return html.Div(
                style={'padding': '20px', 'backgroundColor': '#fee2e2', 'borderRadius': '12px',
                       'border': '2px solid #fca5a5'},
                children=[
                    html.H5("Error Generating Summary Tables", style={'color': '#dc2626', 'marginBottom': '12px'}),
                    html.P(f"An error occurred: {str(e)}", style={'color': '#991b1b', 'marginBottom': '8px'}),
                    html.P("Please check the console for more details.", style={'color': '#6b7280', 'fontSize': '13px'})
                ]
            )
