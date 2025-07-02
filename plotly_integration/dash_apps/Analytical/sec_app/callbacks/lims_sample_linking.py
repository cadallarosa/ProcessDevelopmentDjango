import re

from django.utils import timezone
from ..app import app
from plotly_integration.models import Report, SampleMetadata, PeakResults
from dash import Input, Output, State, ctx
from plotly_integration.models import Report, LimsSampleAnalysis, LimsSecResult


@app.callback(
    Output("link-samples-status", "children"),
    Input("link-samples-btn", "n_clicks"),
    State("hmw-table", "data"),
    State("selected-report", "data"),
    prevent_initial_call=True
)
def link_sec_results_to_lims(n_clicks, table_data, report_id):
    if not table_data or not report_id:
        return "❌ No data or report selected."

    report = Report.objects.filter(report_id=report_id).first()
    if not report:
        return f"❌ Report {report_id} not found."

    success_count = 0
    failed_samples = []

    for row in table_data:
        sample_id = str(row.get("Sample Name")).strip()

        def safe_float(value):
            try:
                cleaned = re.sub(r"[^\d.]+", "", str(value))  # removes all but digits and dots
                return float(cleaned)
            except (ValueError, TypeError):
                return 0.0
        try:
            hmw = safe_float(row.get("HMW", 0))
            main_peak = safe_float(row.get("Main Peak", 0))
            lmw = safe_float(row.get("LMW", 0))
        except (ValueError, TypeError):
            failed_samples.append(sample_id)
            continue

        try:
            sample = LimsSampleAnalysis.objects.get(sample_id=sample_id)

            sec_result, _ = LimsSecResult.objects.update_or_create(
                sample_id=sample,
                defaults={
                    "main_peak": main_peak,
                    "hmw": hmw,
                    "lmw": lmw,
                    "report": report,
                    "status": "complete",
                    "updated_at": timezone.now(),
                }
            )

            sample.sec_result = sec_result
            sample.save()
            success_count += 1

        except LimsSampleAnalysis.DoesNotExist:
            failed_samples.append(sample_id)

    if success_count == 0:
        return f"❌ No SEC results linked. Missing samples: {', '.join(failed_samples)}"

    msg = f"✅ Linked {success_count} SEC result(s) to LIMS."
    if failed_samples:
        msg += f" ⚠️ Failed for: {', '.join(failed_samples)}"
    return msg