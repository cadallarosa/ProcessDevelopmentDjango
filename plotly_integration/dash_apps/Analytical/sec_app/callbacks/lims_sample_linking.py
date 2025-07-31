import re
import dash
from django.utils import timezone
from ..app import app
from plotly_integration.models import Report, SampleMetadata, PeakResults
from dash import Input, Output, State, ctx, dcc
from plotly_integration.models import Report, LimsSampleAnalysis, LimsSecResult


@app.callback(
    [Output("status-message", "children", allow_duplicate=True),
     Output("status-message", "style", allow_duplicate=True),
     Output("button-success-trigger", "data"),
     Output("button-reset-interval", "disabled")],
     Input("report-results-btn", "n_clicks"),
    [State("hmw-table", "data"),
     State("selected-report", "data"),
     State("button-success-trigger", "data")],
    prevent_initial_call=True
)
def link_sec_results_to_lims(n_clicks, table_data, report_id, current_trigger):
    if not table_data or not report_id:
        return "❌ No data or report selected.", {
            "display": "block",
            "backgroundColor": "#f8d7da",
            "color": "#721c24",
            "border": "1px solid #f5c6cb",
            "padding": "10px 20px",
            "margin": "10px 0",
            "borderRadius": "5px"
        }, current_trigger, True

    report = Report.objects.filter(report_id=report_id).first()
    if not report:
        return f"❌ Report {report_id} not found.", {
            "display": "block",
            "backgroundColor": "#f8d7da",
            "color": "#721c24",
            "border": "1px solid #f5c6cb",
            "padding": "10px 20px",
            "margin": "10px 0",
            "borderRadius": "5px"
        }, current_trigger, True

    success_count = 0
    updated_count = 0
    created_count = 0
    failed_samples = []

    def safe_float(value):
        try:
            cleaned = re.sub(r"[^\d.]+", "", str(value))  # removes all but digits and dots
            return float(cleaned)
        except (ValueError, TypeError):
            return 0.0

    for row in table_data:
        sample_id = str(row.get("Sample Name")).strip()

        try:
            hmw = safe_float(row.get("HMW", 0))
            main_peak = safe_float(row.get("Main Peak", 0))
            lmw = safe_float(row.get("LMW", 0))
        except (ValueError, TypeError):
            failed_samples.append(f"{sample_id} (data parsing error)")
            continue

        try:
            # Check if sample exists
            sample = LimsSampleAnalysis.objects.get(sample_id=sample_id)

            # Check if SEC result already exists
            existing_result = LimsSecResult.objects.filter(sample_id=sample).first()

            # Use update_or_create with explicit sample_id lookup
            sec_result, created = LimsSecResult.objects.update_or_create(
                sample_id=sample,  # This is the lookup field (OneToOne primary key)
                defaults={
                    "main_peak": main_peak,
                    "hmw": hmw,
                    "lmw": lmw,
                    "report": report,
                    "status": "complete",
                    "updated_at": timezone.now(),
                }
            )

            # Update the sample's foreign key relationship
            sample.sec_result = sec_result
            sample.save()

            success_count += 1
            if created:
                created_count += 1
            else:
                updated_count += 1

        except LimsSampleAnalysis.DoesNotExist:
            failed_samples.append(f"{sample_id} (not found in LIMS)")
        except Exception as e:
            failed_samples.append(f"{sample_id} (error: {str(e)})")

    # Determine message and style based on results
    if success_count == 0:
        # Complete failure
        message = f"❌ No SEC results linked. Failed samples: {', '.join(failed_samples)}"
        style = {
            "display": "block",
            "backgroundColor": "#f8d7da",
            "color": "#721c24",
            "border": "1px solid #f5c6cb",
            "padding": "10px 20px",
            "margin": "10px 0",
            "borderRadius": "5px"
        }
    elif failed_samples:
        # Partial success
        if updated_count > 0 and created_count > 0:
            detail = f"Updated {updated_count}, created {created_count}"
        elif updated_count > 0:
            detail = f"Updated {updated_count} existing result(s)"
        elif created_count > 0:
            detail = f"Created {created_count} new result(s)"
        else:
            detail = f"Processed {success_count} result(s)"

        message = f"⚠️ Linked {success_count} SEC result(s) to LIMS ({detail}). Failed: {', '.join(failed_samples)}"
        style = {
            "display": "block",
            "backgroundColor": "#fff3cd",
            "color": "#856404",
            "border": "1px solid #ffeeba",
            "padding": "10px 20px",
            "margin": "10px 0",
            "borderRadius": "5px"
        }
    else:
        # Complete success
        if updated_count > 0 and created_count > 0:
            detail = f"Updated {updated_count}, created {created_count}"
        elif updated_count > 0:
            detail = f"Updated {updated_count} existing result(s)"
        elif created_count > 0:
            detail = f"Created {created_count} new result(s)"
        else:
            detail = f"Processed {success_count} result(s)"

        message = f"✅ Successfully linked {success_count} SEC result(s) to LIMS ({detail})!"
        style = {
            "display": "block",
            "backgroundColor": "#d4edda",
            "color": "#155724",
            "border": "1px solid #c3e6cb",
            "padding": "10px 20px",
            "margin": "10px 0",
            "borderRadius": "5px"
        }

    # Trigger button color change and start timer
    return message, style, current_trigger + 1, False

# New callback to handle button color change
@app.callback(
    Output("report-results-btn", "style"),
    [Input("button-success-trigger", "data"),
     Input("button-reset-interval", "n_intervals")],
    [State("link-samples-status", "style")],
    prevent_initial_call=True
)
def update_button_style(success_trigger, reset_intervals, status_style):
    ctx = dash.callback_context
    if not ctx.triggered:
        # Default button style
        return {
            'backgroundColor': '#0056b3',
            'color': 'white',
            'border': 'none',
            'padding': '12px 24px',
            'fontSize': '16px',
            'cursor': 'pointer',
            'borderRadius': '8px',
            'fontWeight': '500',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
            'display': 'block',
            'margin': '0 auto'
        }

    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]

    if trigger_id == "button-success-trigger":
        # Change button color based on status
        if status_style and "backgroundColor" in status_style:
            bg_color = status_style["backgroundColor"]
            if bg_color == "#d4edda":  # Success (green)
                button_color = "#28a745"
            elif bg_color == "#fff3cd":  # Warning (yellow)
                button_color = "#ffc107"
            elif bg_color == "#f8d7da":  # Error (red)
                button_color = "#dc3545"
            else:
                button_color = "#0056b3"  # Default
        else:
            button_color = "#28a745"  # Default to success

        return {
            'backgroundColor': button_color,
            'color': 'white',
            'border': 'none',
            'padding': '12px 24px',
            'fontSize': '16px',
            'cursor': 'pointer',
            'borderRadius': '8px',
            'fontWeight': '500',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
            'display': 'block',
            'margin': '0 auto'
        }

    elif trigger_id == "button-reset-interval":
        # Reset to default after timer
        return {
            'backgroundColor': '#0056b3',
            'color': 'white',
            'border': 'none',
            'padding': '12px 24px',
            'fontSize': '16px',
            'cursor': 'pointer',
            'borderRadius': '8px',
            'fontWeight': '500',
            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)',
            'display': 'block',
            'margin': '0 auto'
        }

    return dash.no_update