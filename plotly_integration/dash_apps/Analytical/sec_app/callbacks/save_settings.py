# Saving All Settings to JSON
from ..app import app
from dash import Output, Input, State
import dash
from plotly_integration.models import Report


@app.callback(
    Output("save-plot-settings", "children"),
    Output("reset-save-settings-timer", "disabled"),
    Input("save-plot-settings", "n_clicks"),
    Input("reset-save-settings-timer", "n_intervals"),
    State("reset-save-settings-timer", "disabled"),
    State("selected-report", "data"),
    # Plot Settings
    State("channel-checklist", "value"),
    State("plot-type-dropdown", "value"),
    State("shading-checklist", "value"),
    State("peak-label-checklist", "value"),
    State("main-peak-rt-input", "value"),
    State("low-mw-cutoff-input", "value"),
    State("num-cols-input", "value"),
    State("vertical-spacing-input", "value"),
    State("horizontal-spacing-input", "value"),
    State("hmw-column-selector", "value"),
    # Standard Settings
    State("standard-id-dropdown", "value"),
    State("standard-table", "selected_rows"),
    State("rt-input", "value"),
    prevent_initial_call=True
)
def save_settings_and_reset(save_clicks, interval_n, interval_disabled, report_id,
                            channels, plot_type, shading, peak_labels,
                            main_rt, low_mw_cutoff, num_cols, v_spacing, h_spacing, hmw_cols,
                            std_id, std_rows, rt_input):
    from dash.exceptions import PreventUpdate

    triggered = dash.callback_context.triggered
    triggered_id = triggered[0]["prop_id"].split(".")[0] if triggered else None

    if triggered_id == "reset-save-settings-timer" and not interval_disabled:
        # ⏱ Reset button label
        return "💾 Save Plot Settings", True

    # 💾 Save logic
    report = Report.objects.filter(report_id=report_id).first()
    if not report:
        return "❌ Report not found", True

    report.plot_settings = {
        "channel_checklist": channels,
        "plot_type": plot_type,
        "enable_shading": "enable_shading" in (shading or []),
        "enable_peak_labeling": "enable_peak_labeling" in (peak_labels or []),
        "main_peak_rt": main_rt,
        "low_mw_cutoff": low_mw_cutoff,
        "num_cols": num_cols,
        "vertical_spacing": v_spacing,
        "horizontal_spacing": h_spacing,
        "hmw_columns": hmw_cols,
        "std_result_id": std_id,
        "std_selected_rows": std_rows,
        "rt_input": rt_input
    }
    report.save()

    return "✅ Settings Saved", False  # Start timer to reset text


@app.callback(
    Output("report-settings", "data"),
    Input("selected-report", "data"),
    prevent_initial_call=True
)
def fetch_report_settings(report_id):
    if not report_id:
        raise dash.exceptions.PreventUpdate

    report = Report.objects.filter(report_id=report_id).first()
    if not report or not report.plot_settings:
        return {}
    print(f'{report.plot_settings}report.plot_settings')
    return report.plot_settings


from dash import Input, Output
from dash.exceptions import PreventUpdate


@app.callback(
    Output("plot-type-dropdown", "value"),
    Input("selected-report", "data"),
    prevent_initial_call=True
)
def apply_rt_and_cutoff_settings(report_id):
    print(report_id)
    if not report_id:
        print('No Report ID')
        raise PreventUpdate

    report = Report.objects.filter(report_id=report_id).first()
    if not report or not report.plot_settings:
        return "subplots"

    settings = report.plot_settings
    print(f"⚙️ Applying RT/Cutoff Settings: {settings}")
    plot_type = settings.get("plot_type", None)
    print(f"Plot Type:{plot_type}")
    return (
        plot_type  # input field

    )
