"""
Settings Callbacks
Handle settings modal for channel selection and peak display options
"""

from dash import Input, Output, State, no_update


def register_settings_callbacks(app):
    """Register settings modal callbacks"""

    @app.callback(
        Output('settings-modal', 'is_open'),
        Input('open-settings-modal-btn', 'n_clicks'),
        State('settings-modal', 'is_open'),
        prevent_initial_call=True
    )
    def toggle_modal(n_clicks, is_open):
        """Toggle settings modal open/close"""
        return not is_open

    @app.callback(
        [Output('channel-settings-store', 'data'),
         Output('show-trend-store', 'data'),
         Output('x-axis-range-store', 'data'),
         Output('image-height-store', 'data'),
         Output('plot-width-store', 'data'),
         Output('settings-modal', 'is_open', allow_duplicate=True)],
        Input('apply-settings-btn', 'n_clicks'),
        [State('channel-checklist-ps', 'value'),
         State('display-options-ps', 'value'),
         State('x-axis-min-input', 'value'),
         State('x-axis-max-input', 'value'),
         State('image-height-input', 'value'),
         State('plot-height-input', 'value')],
        prevent_initial_call=True
    )
    def save_settings(n_clicks, channels, display_options, x_min, x_max, image_height, plot_height):
        """
        Save settings when Apply button is clicked

        Args:
            n_clicks: Apply button clicks
            channels: Selected channels
            display_options: Display options (show_trend, etc.)
            x_min: X-axis minimum value
            x_max: X-axis maximum value
            image_height: Molecule image height
            plot_height: Plot height

        Returns:
            Tuple of (saved_channels, show_trend, x_axis_range, image_height, plot_height, modal_closed)
        """
        # Save settings and close modal
        show_trend = 'show_trend' in (display_options or [])
        x_axis_range = [x_min or 4, x_max or 12]
        img_height = image_height or 225
        plt_height = plot_height or 600

        print(f"Settings saved:")
        print(f"  Channels: {channels}")
        print(f"  Show Trend: {show_trend}")
        print(f"  X-Axis Range: {x_axis_range}")
        print(f"  Image Height: {img_height}px")
        print(f"  Plot Height: {plt_height}px")

        return channels, show_trend, x_axis_range, img_height, plt_height, False
