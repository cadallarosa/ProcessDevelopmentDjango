"""
Simplified Callbacks Module for CE-SDS Analysis App
Unified callback approach for chromatogram generation.
"""

from dash import Input, Output, State, callback_context
from dash.exceptions import PreventUpdate
import pandas as pd
from .data_access import get_metadata_from_source, get_timeseries_data, split_result_ids_by_prefix
from .plotting import generate_unified_chromatogram, plot_standard_chromatogram


def register_callbacks(app):
    """Register all callbacks with the Dash app"""
    
    @app.callback(
        [
            Output("reduced-chromatogram-plot", "figure"),
            Output("reduced-peak-table", "data"),
        ],
        [
            Input("reduced-result-ids", "data"),
            Input("marker-rt", "value"),
            Input("marker-label", "value"),
            Input("light-chain-time", "value"),
            Input("standard-regression-params", "data"),
            Input("reduced-y-axis-scaling", "value"),
            Input("reduced-subplot-vertical-spacing", "value"),
            Input("reduced-show-mw-checklist", "value"),
            Input("reduced-annotation-positioning", "value"),
            Input("main-tabs", "value"),
            Input("selected-report", "data"),
        ]
    )
    def update_reduced_chromatogram(result_ids, marker_rt, marker_label, light_chain_time,
                                  regression_params, y_scale, subplot_vertical_spacing, 
                                  show_mw_checklist, annotation_positioning, active_tab, selected_report):
        """Unified callback for reduced chromatograms"""
        
        if not result_ids or active_tab != "tab-reduced":
            return {}, []

        # Get metadata and populate with timeseries data
        result_df_by_id = get_metadata_from_source(result_ids)
        for mid in result_df_by_id:
            result_df_by_id[mid]["data"] = get_timeseries_data(mid)

        # Extract regression parameters
        slope = regression_params.get('slope') if regression_params else None
        intercept = regression_params.get('intercept') if regression_params else None
        
        # Determine if MW should be shown
        show_mw = show_mw_checklist and len(show_mw_checklist) > 0

        # Generate chromatogram
        fig, table_data = generate_unified_chromatogram(
            result_df_by_id=result_df_by_id,
            title="Reduced Chromatograms",
            marker_rt=marker_rt,
            marker_label=marker_label,
            light_chain_time=light_chain_time,
            regression_slope=slope,
            regression_intercept=intercept,
            y_scale=y_scale,
            subplot_vertical_spacing=subplot_vertical_spacing,
            show_mw_in_annotations=show_mw,
            annotation_positioning=annotation_positioning,
            sample_type='reduced'
        )

        return fig, table_data

    @app.callback(
        [
            Output("nonreduced-chromatogram-plot", "figure"),
            Output("nonreduced-peak-table", "data"),
        ],
        [
            Input("nonreduced-result-ids", "data"),
            Input("marker-rt", "value"),
            Input("marker-label", "value"),
            Input("standard-regression-params", "data"),
            Input("nonreduced-y-axis-scaling", "value"),
            Input("nonreduced-subplot-vertical-spacing", "value"),
            Input("nonreduced-show-mw-checklist", "value"),
            Input("nonreduced-annotation-positioning", "value"),
            Input("main-tabs", "value"),
            Input("selected-report", "data"),
        ]
    )
    def update_nonreduced_chromatogram(result_ids, marker_rt, marker_label, regression_params, 
                                     y_scale, subplot_vertical_spacing, show_mw_checklist, 
                                     annotation_positioning, active_tab, selected_report):
        """Unified callback for non-reduced chromatograms"""
        
        if not result_ids or active_tab != "tab-nonreduced":
            return {}, []

        # Get metadata and populate with timeseries data  
        result_df_by_id = get_metadata_from_source(result_ids)
        for mid in result_df_by_id:
            result_df_by_id[mid]["data"] = get_timeseries_data(mid)

        # Extract regression parameters
        slope = regression_params.get('slope') if regression_params else None
        intercept = regression_params.get('intercept') if regression_params else None
        
        # Determine if MW should be shown
        show_mw = show_mw_checklist and len(show_mw_checklist) > 0

        # Generate chromatogram
        fig, table_data = generate_unified_chromatogram(
            result_df_by_id=result_df_by_id,
            title="Non-Reduced Chromatograms",
            marker_rt=marker_rt,
            marker_label=marker_label,
            regression_slope=slope,
            regression_intercept=intercept,
            y_scale=y_scale,
            subplot_vertical_spacing=subplot_vertical_spacing,
            show_mw_in_annotations=show_mw,
            annotation_positioning=annotation_positioning,
            sample_type='nonreduced'
        )

        return fig, table_data

    @app.callback(
        [
            Output("standard-peak-plot", "figure"),
            Output("std-detected-peak-table", "data")
        ],
        [
            Input("standard-id-dropdown", "value"),
            State("num-std-peaks", "value")
        ]
    )
    def update_standard_chromatogram(metadata_id, num_to_keep):
        """Callback for standard chromatogram plotting"""
        if not metadata_id:
            return {}, []
        
        fig, table_data = plot_standard_chromatogram(metadata_id, num_to_keep or 7)
        return fig, table_data

    @app.callback(
        Output("selected-result-ids", "data"),
        Output("reduced-result-ids", "data"),  
        Output("nonreduced-result-ids", "data"),
        [Input("load-once", "n_intervals")],
        [State('url', 'search'), State("selected-report", "data")]
    )
    def split_and_populate_result_ids(n_intervals, search, selected_report):
        """Split result IDs into reduced and non-reduced categories"""
        if not selected_report or not selected_report.get('result_ids'):
            return [], [], []
            
        result_ids = selected_report['result_ids']
        reduced_ids, nonreduced_ids = split_result_ids_by_prefix(result_ids)
        
        return result_ids, reduced_ids, nonreduced_ids

    # Additional utility callbacks can be added here as needed
    # (URL parsing, modal handling, data export, etc.)