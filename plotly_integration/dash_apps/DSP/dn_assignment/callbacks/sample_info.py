"""Callbacks for Sample Info sub-tab (within Edit DN)."""
import re
from datetime import datetime
import dash
from dash import Input, Output, State
from dash.exceptions import PreventUpdate
from plotly_integration.models import LimsSampleAnalysis, LimsDnAssignment


def register_sample_info_callbacks(app):
    """Register callbacks for Sample Info sub-tab functionality."""

    @app.callback(
        Output("existing-sample-table", "data"),
        Input("refresh-existing-samples", "n_clicks"),
        Input("dn-context", "data"),
        prevent_initial_call=True
    )
    def load_existing_samples(n_clicks, dn_context):
        """Load existing PD samples linked to the DN."""
        if not dn_context or dn_context.get("mode") != "edit":
            raise PreventUpdate

        dn_value = dn_context.get("dn")
        try:
            dn = LimsDnAssignment.objects.get(dn=dn_value)

            samples = LimsSampleAnalysis.objects.filter(dn=dn)
            sample_rows = [{
                "sample_id": s.sample_id,
                "sample_date": s.sample_date.strftime("%Y-%m-%d") if s.sample_date else "",
                "description": s.description,
                "a280_result": s.a280_result,
                "notes": s.notes
            } for s in samples]

            return sample_rows

        except LimsDnAssignment.DoesNotExist:
            return []

    @app.callback(
        Output("save-existing-samples", "children", allow_duplicate=True),
        Input("save-existing-samples", "n_clicks"),
        State("existing-sample-table", "data"),
        prevent_initial_call=True
    )
    def save_existing_pd_samples(n_clicks, table_data):
        """Save updates to existing PD samples."""
        if not table_data:
            raise PreventUpdate

        updated = 0
        for row in table_data:
            sample_id = row.get("sample_id")
            if not sample_id:
                continue

            try:
                sample = LimsSampleAnalysis.objects.get(sample_id=sample_id)
            except LimsSampleAnalysis.DoesNotExist:
                continue

            try:
                sample.sample_date = datetime.strptime(
                    row.get("sample_date", ""), "%Y-%m-%d"
                ).date() if row.get("sample_date") else None
            except Exception:
                sample.sample_date = None

            sample.description = row.get("description", "")
            sample.a280_result = row.get("a280_result") or None
            sample.notes = row.get("notes", "")

            sample.save()
            updated += 1

        return f"✅ {updated} sample(s) updated"

    @app.callback(
        Output("new-sample-table", "data"),
        Input("add-sample-row", "n_clicks"),
        Input("clear-sample-btn", "n_clicks"),
        State("new-sample-table", "data"),
        prevent_initial_call=True
    )
    def handle_new_sample_buttons(add_clicks, clear_clicks, current_data):
        """Handle add/clear buttons for new sample table."""
        if current_data is None:
            current_data = []

        ctx = dash.callback_context
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]

        if button_id == "clear-sample-btn":
            return []

        if button_id == "add-sample-row":
            # Get all existing PD numbers
            existing_ids = list(
                LimsSampleAnalysis.objects.filter(sample_id__startswith="PD")
                .values_list("sample_id", flat=True)
            )
            current_ids = [row["sample_id"] for row in current_data if row.get("sample_id", "").startswith("PD")]

            all_ids = existing_ids + current_ids
            suffixes = [
                int(re.sub(r"\D", "", sid))
                for sid in all_ids
                if re.match(r"PD\d+$", sid)
            ]
            next_num = max(suffixes, default=0) + 1

            current_data.append({
                "sample_id": f"PD{next_num}",
                "sample_date": datetime.now().strftime("%Y-%m-%d"),
                "description": "",
                "a280_result": "",
                "notes": ""
            })

            return current_data

        raise PreventUpdate

    @app.callback(
        Output("save_samples_status", "children"),
        Output("new-sample-table", "data", allow_duplicate=True),
        Input("save-samples-btn", "n_clicks"),
        State("new-sample-table", "data"),
        State("dn-context", "data"),
        prevent_initial_call=True
    )
    def save_new_samples(n_clicks, sample_data, dn_context):
        """Save new PD samples linked to current DN."""
        if not sample_data or not dn_context:
            raise PreventUpdate

        dn_value = dn_context.get("dn")
        dn_obj = LimsDnAssignment.objects.filter(dn=dn_value).first()

        if not dn_obj:
            return "❌ No DN found", sample_data

        saved = 0
        for row in sample_data:
            sample_id = row.get("sample_id")
            if not sample_id:
                continue

            try:
                sample_date = datetime.strptime(
                    row.get("sample_date", ""), "%Y-%m-%d"
                ).date() if row.get("sample_date") else None
            except Exception:
                sample_date = None

            LimsSampleAnalysis.objects.update_or_create(
                sample_id=sample_id,
                defaults={
                    "sample_type": 3,  # PD type
                    "sample_date": sample_date,
                    "project_id": dn_obj.project_id,
                    "description": row.get("description", ""),
                    "a280_result": row.get("a280_result") or None,
                    "notes": row.get("notes", ""),
                    "dn": dn_obj,
                    "status": "in_progress"
                }
            )
            saved += 1

        return f"✅ {saved} sample(s) created", []
