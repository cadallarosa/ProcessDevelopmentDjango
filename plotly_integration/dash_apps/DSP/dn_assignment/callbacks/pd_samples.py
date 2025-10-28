"""Callbacks for PD sample management."""
from datetime import datetime
from dash import Input, Output, State
from dash.exceptions import PreventUpdate
from plotly_integration.models import LimsSampleAnalysis, LimsDnAssignment
from ..utils.data_helpers import get_all_pd_samples, get_pd_table_style_conditional, get_next_pd_number


def register_pd_sample_callbacks(app):
    """Register callbacks for PD sample functionality."""

    @app.callback(
        Output("view-pd-table", "data"),
        Output("view-pd-table", "style_data_conditional"),
        Input("refresh-pd-table", "n_clicks"),
        Input("dn-tabs", "value"),
        prevent_initial_call=False
    )
    def load_pd_table(n_clicks, tab):
        """Load PD samples table."""
        if tab != "view-pd-tab":
            raise PreventUpdate

        data = get_all_pd_samples()
        style_conditional = get_pd_table_style_conditional()

        return data, style_conditional

    @app.callback(
        Output("update-pd-table", "children"),
        Output("reset-save-pd-timer", "disabled"),
        Input("update-pd-table", "n_clicks_timestamp"),
        Input("reset-save-pd-timer", "n_intervals"),
        State("reset-save-pd-timer", "disabled"),
        State("view-pd-table", "derived_virtual_data"),
        State("view-pd-table", "page_current"),
        State("view-pd-table", "page_size"),
        prevent_initial_call=True
    )
    def save_or_reset_button(save_ts, interval_n, interval_disabled, visible_data, page_current, page_size):
        """Save PD sample changes with auto-reset button."""
        if not interval_disabled:
            return "💾 Save", True

        if not visible_data:
            return "💾 Save", True

        start = page_current * page_size
        end = start + page_size
        page_rows = visible_data[start:end]

        created, updated, skipped, errors = 0, 0, 0, 0

        for row in page_rows:
            try:
                sample_id = row.get("sample_id")
                if not sample_id:
                    skipped += 1
                    continue

                existing = LimsSampleAnalysis.objects.filter(sample_id=sample_id).first()
                dn_val = row.get("dn")
                dn_obj = LimsDnAssignment.objects.filter(dn=dn_val).first() if dn_val else None

                sample_date = row.get("sample_date")
                if sample_date and isinstance(sample_date, str):
                    try:
                        sample_date = datetime.fromisoformat(sample_date).date()
                    except ValueError:
                        sample_date = None

                new_data = {
                    "sample_type": 3,
                    "sample_date": sample_date if hasattr(sample_date, 'year') else None,
                    "project_id": row.get("project_id") or "",
                    "description": row.get("description", ""),
                    "analyst": row.get("analyst", ""),
                    "a280_result": float(row.get("a280")) if row.get("a280") not in [None, ""] else None,
                    "notes": row.get("notes", ""),
                    "dn": dn_obj,
                    "status": row.get("status", "in_progress"),
                }

                if existing:
                    has_changes = any(getattr(existing, k) != v for k, v in new_data.items())
                    if has_changes:
                        for k, v in new_data.items():
                            setattr(existing, k, v)
                        existing.save()
                        updated += 1
                    else:
                        skipped += 1
                else:
                    LimsSampleAnalysis.objects.create(sample_id=sample_id, **new_data)
                    created += 1

            except Exception as e:
                print(f"❌ Error saving PD sample {sample_id}: {e}")
                errors += 1

        return f"✅ Saved! ({created} new, {updated} updated)", False

    @app.callback(
        Output("pd-bulk-table", "data"),
        Input("clear-pd-btn", "n_clicks"),
        State("pd-bulk-table", "data"),
        prevent_initial_call=True
    )
    def handle_pd_sample_buttons(clear_clicks, current_data):
        """Handle clear button for PD bulk table."""
        if current_data is None:
            current_data = []

        default_row = {
            "sample_date": datetime.now().strftime("%Y-%m-%d"),
            "description": "",
            "a280": "",
            "notes": "",
            "dn": "",
            "project_id": "",
            "analyst": "",
            "status": "in_progress"
        }

        return [default_row]

    @app.callback(
        Output("save-pd-status", "children"),
        Output("pd-bulk-table", "data", allow_duplicate=True),
        Input("save-pd-btn", "n_clicks"),
        State("pd-bulk-table", "data"),
        prevent_initial_call=True
    )
    def save_pd_samples(n_clicks, table_data):
        """Save new PD samples from bulk creation table."""
        if not table_data:
            raise PreventUpdate

        # Get the current highest PD number
        next_pd_num = get_next_pd_number()

        saved = 0
        for row in table_data:
            # Increment for each sample
            next_pd_num += 1
            pd_id = f"PD{next_pd_num}"

            try:
                sample_date = datetime.strptime(row.get("sample_date", ""), "%Y-%m-%d").date()
            except Exception:
                sample_date = None

            project_id = row.get("project_id", "").strip()
            analyst = row.get("analyst", "").strip()
            status = row.get("status", "in_progress")

            dn_value = row.get("dn")
            dn_obj = LimsDnAssignment.objects.filter(dn=dn_value).first() if dn_value else None

            LimsSampleAnalysis.objects.update_or_create(
                sample_id=pd_id,
                defaults={
                    "sample_type": 3,
                    "sample_date": sample_date,
                    "project_id": project_id,
                    "description": row.get("description", ""),
                    "analyst": analyst,
                    "dn": dn_obj,
                    "a280_result": row.get("a280") or None,
                    "notes": row.get("notes", ""),
                    "status": status
                }
            )
            saved += 1

        return f"✅ {saved} PD sample(s) created.", [{
            "sample_id": "",
            "sample_date": datetime.now().strftime("%Y-%m-%d"),
            "description": "",
            "a280": "",
            "notes": "",
            "dn": "",
            "project_id": "",
            "analyst": "",
            "status": "in_progress"
        }]
