# SAVE ALL ROWS WITH CONFLICT DETECTION
from dash import Input, Output, callback, no_update, html, State, callback_context
import dash_bootstrap_components as dbc
from plotly_integration.models import LimsUpstreamSamples
from plotly_integration.cld_dashboard.main_app import app
from datetime import datetime
import pandas as pd
import io

print("🚀 Loading SAVE ALL ROWS with CONFLICT DETECTION...")

# Track original data from database
_original_data = {}  # Original values from database when page loaded


# MAIN DATA LOADING
@app.callback(
    [Output("view-sample-table", "data"),
     Output("filtered-sample-data", "data"),
     Output("original-data-store", "data")],
    [Input("parsed-pathname", "data"),
     Input("refresh-btn", "n_clicks"),
     Input("samples-search", "value"),
     Input("samples-project-filter", "value"),
     Input("samples-stage-filter", "value")],
    prevent_initial_call=False
)
def load_samples_main(pathname, n_clicks, search_term, project_filter, stage_filter):
    """Main data loading callback - stores original snapshot"""
    global _original_data

    if pathname != "/samples/view":
        return [], [], {}

    try:
        # Query database with filters
        samples_query = LimsUpstreamSamples.objects.filter(sample_type=2)

        if project_filter and project_filter != "all":
            samples_query = samples_query.filter(project__icontains=project_filter)
        if stage_filter and stage_filter != "all":
            samples_query = samples_query.filter(development_stage__icontains=stage_filter)
        if search_term:
            from django.db.models import Q
            search_query = Q(sample_number__icontains=search_term) | \
                           Q(project__icontains=search_term) | \
                           Q(cell_line__icontains=search_term) | \
                           Q(sip_number__icontains=search_term) | \
                           Q(analyst__icontains=search_term)
            samples_query = samples_query.filter(search_query)

        samples = samples_query.order_by("-sample_number")  # Load ALL samples, no limit

        data = []
        original_snapshot = {}

        for s in samples:
            row = build_sample_row_with_recoveries(s)
            data.append(row)

            # Store original for comparison during save
            sample_key = str(s.sample_number)
            original_snapshot[sample_key] = row.copy()

        _original_data = original_snapshot
        print(f"✅ Loaded {len(data)} samples with original snapshot")
        return data, data, original_snapshot

    except Exception as e:
        print(f"❌ Error loading: {e}")
        return [], [], {}


# ENABLE/DISABLE SAVE BUTTON
@app.callback(
    [Output("save-btn", "disabled"),
     Output("save-btn", "children")],
    [Input("view-sample-table", "data")],
    prevent_initial_call=True
)
def update_save_button(current_data):
    """Enable save button when there's data"""
    if current_data and len(current_data) > 0:
        return False, [
            html.I(className="fas fa-save me-1"),
            "Save"
        ]
    else:
        return True, [
            html.I(className="fas fa-save me-1"),
            "Save"
        ]


# SAVE ALL ROWS WITH CONFLICT DETECTION
@app.callback(
    [Output("update-up-view-status", "children"),
     Output("view-sample-table", "data", allow_duplicate=True),
     Output("original-data-store", "data", allow_duplicate=True)],
    Input("save-btn", "n_clicks"),
    [State("view-sample-table", "data"),
     State("original-data-store", "data"),
     State("view-sample-table", "page_current"),
     State("view-sample-table", "page_size")],
    prevent_initial_call=True
)
def save_all_with_conflict_detection(n_clicks, current_data, original_data, page_current, page_size):
    """Save ALL rows on the current page with conflict detection"""
    global _original_data

    if not n_clicks or not current_data:
        return no_update, no_update, no_update

    # Calculate which rows are on the current page
    page_current = page_current or 0
    page_size = page_size or 25

    start_idx = page_current * page_size
    end_idx = start_idx + page_size

    # Get only the rows from the current page
    page_data = current_data[start_idx:end_idx]

    print(f"🔄 Starting save for {len(page_data)} samples on page {page_current + 1}")

    # Process only rows from current page
    conflicts = []
    saved_successfully = []
    save_errors = []
    no_changes = []

    for row in page_data:  # Now this only contains rows from the current page!
        sample_num = str(row.get('sample_number', ''))
        if not sample_num:
            continue

        try:
            # Get current database state
            db_sample = LimsUpstreamSamples.objects.filter(
                sample_number=int(sample_num),
                sample_type=2
            ).first()

            if not db_sample:
                save_errors.append(f"FB{sample_num} not found in database")
                continue

            # Get original snapshot
            original_row = original_data.get(sample_num, {})

            # Check if database has changed since page load
            if has_database_changed(db_sample, original_row):
                # Conflict detected - someone else changed this sample
                conflicts.append({
                    'sample_num': sample_num,
                    'fields_changed': get_changed_fields(db_sample, original_row)
                })
                print(f"⚠️ Conflict detected for FB{sample_num}")
            else:
                # No conflict - check if user made changes
                if has_row_changed(row, original_row):
                    # User made changes - save them
                    if save_single_sample(row):
                        saved_successfully.append(sample_num)
                        print(f"✅ Saved FB{sample_num} (user changes)")
                    else:
                        save_errors.append(f"FB{sample_num} save failed")
                else:
                    # No changes from user - but still "save" to catch copy/paste
                    if save_single_sample(row):
                        no_changes.append(sample_num)
                        print(f"✅ Saved FB{sample_num} (no changes/copy-paste check)")
                    else:
                        save_errors.append(f"FB{sample_num} save failed")

        except Exception as e:
            save_errors.append(f"FB{sample_num}: {str(e)}")
            print(f"❌ Error processing FB{sample_num}: {e}")

    # Create status message
    total_processed = len(saved_successfully) + len(no_changes) + len(conflicts) + len(save_errors)

    status_parts = []
    if saved_successfully:
        status_parts.append(f"✅ {len(saved_successfully)} samples with changes saved")
    if no_changes:
        status_parts.append(f"✅ {len(no_changes)} unchanged samples verified")
    if conflicts:
        status_parts.append(f"⚠️ {len(conflicts)} samples had conflicts")
    if save_errors:
        status_parts.append(f"❌ {len(save_errors)} errors")

    # Build detailed status alert
    alert_children = [
        html.H6(f"Save Operation Complete - {len(page_data)} samples processed from page {page_current + 1}",
                className="alert-heading"),
        html.P(" | ".join(status_parts) if status_parts else "No samples processed")
    ]

    # Add conflict details if any
    if conflicts:
        alert_children.extend([
            html.Hr(),
            html.P("The following samples were modified by another user and were NOT saved:", className="mb-2 fw-bold")
        ])

        for conflict in conflicts[:5]:  # Show first 5
            alert_children.extend([
                html.P([
                    html.Strong(f"FB{conflict['sample_num']}: "),
                    f"Changed fields: {', '.join(conflict['fields_changed'])}"
                ], className="mb-1 small")
            ])

        if len(conflicts) > 5:
            alert_children.append(html.P(f"... and {len(conflicts) - 5} more conflicts", className="small text-muted"))

        alert_children.append(html.P("Click 'Refresh' to see the latest values.", className="mb-0 mt-2"))

    # Add error details if any
    if save_errors:
        alert_children.extend([
            html.Hr(),
            html.P("Errors:", className="mb-2 fw-bold"),
            html.Ul([html.Li(err, className="small") for err in save_errors[:5]]),
            html.P(f"... and {len(save_errors) - 5} more errors", className="small") if len(save_errors) > 5 else ""
        ])

    # Determine alert color
    if conflicts and not saved_successfully and not no_changes:
        alert_color = "danger"
    elif conflicts:
        alert_color = "warning"
    elif save_errors:
        alert_color = "warning"
    else:
        alert_color = "success"

    status_alert = dbc.Alert(alert_children, color=alert_color, dismissable=True)

    # Refresh data if there were conflicts
    if conflicts:
        # Reload from database to show latest values
        print("🔄 Reloading data due to conflicts")
        samples = LimsUpstreamSamples.objects.filter(
            sample_number__in=[int(row['sample_number']) for row in current_data]
        ).order_by("-sample_number")

        fresh_data = []
        new_original = {}

        for s in samples:
            row = build_sample_row_with_recoveries(s)
            fresh_data.append(row)
            new_original[str(s.sample_number)] = row.copy()

        _original_data = new_original

        return status_alert, fresh_data, new_original
    else:
        # Update original data for all rows (since we saved everything)
        new_original = {}
        for row in current_data:
            sample_num = str(row.get('sample_number', ''))
            if sample_num:
                new_original[sample_num] = row.copy()

        _original_data = new_original

        return status_alert, no_update, new_original


# RECOVERY CALCULATIONS
@app.callback(
    Output("view-sample-table", "data", allow_duplicate=True),
    Input("view-sample-table", "data"),
    prevent_initial_call=True
)
def calculate_recoveries(data):
    """Calculate recovery fields when data changes"""
    if not data:
        return no_update

    updated_data = []
    for row in data:
        updated_row = row.copy()

        # Calculate Fast ProA Recovery
        try:
            hf_titer = float(row.get("pro_aqa_hf_titer") or 0)
            e_titer = float(row.get("pro_aqa_e_titer") or 0)
            if hf_titer > 0 and e_titer > 0:
                recovery = round((e_titer / hf_titer) * 100, 1)
                updated_row["fast_pro_a_recovery"] = recovery
            else:
                updated_row["fast_pro_a_recovery"] = ""
        except:
            updated_row["fast_pro_a_recovery"] = ""

        # Calculate A280 Recovery
        try:
            loading_vol = float(row.get("hccf_loading_volume") or 0)
            eluate_vol = float(row.get("proa_eluate_volume") or 0)
            octet_titer = float(row.get("hf_octet_titer") or 0)
            a280_conc = float(row.get("proa_eluate_a280_conc") or 0)

            if all([loading_vol > 0, eluate_vol > 0, octet_titer > 0, a280_conc > 0]):
                total_load = loading_vol * octet_titer
                total_elute = eluate_vol * a280_conc
                recovery = round((total_elute / total_load) * 100, 1)
                updated_row["purification_recovery_a280"] = recovery
            else:
                updated_row["purification_recovery_a280"] = ""
        except:
            updated_row["purification_recovery_a280"] = ""

        updated_data.append(updated_row)

    return updated_data


# PROJECT FILTER
@app.callback(
    Output("samples-project-filter", "options"),
    Input("parsed-pathname", "data"),
    prevent_initial_call=False
)
def populate_projects(pathname):
    """Populate project dropdown"""
    if pathname != "/samples/view":
        return []

    try:
        projects = LimsUpstreamSamples.objects.filter(
            sample_type=2
        ).values_list('project', flat=True).distinct()

        options = [{"label": "All Projects", "value": "all"}]
        for p in sorted(set(p for p in projects if p)):
            options.append({"label": p, "value": p})

        return options
    except:
        return [{"label": "All Projects", "value": "all"}]


# EXPORT TO EXCEL
@app.callback(
    Output("download-excel", "data"),
    Input("export-samples-btn", "n_clicks"),
    State("view-sample-table", "data"),
    prevent_initial_call=True
)
def export_excel(n_clicks, data):
    """Export current page data to Excel"""
    if not n_clicks or not data:
        return no_update

    try:
        df = pd.DataFrame(data)
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Samples', index=False)

        output.seek(0)
        filename = f"samples_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"

        from dash import dcc
        return dcc.send_bytes(output.read(), filename)
    except Exception as e:
        print(f"❌ Error exporting: {e}")
        return no_update


# UTILITY FUNCTIONS
def has_database_changed(db_sample, original_row):
    """Compare current database state to original snapshot"""
    # Check text fields
    text_fields = [
        ("cell_line", "cell_line"),
        ("sip_number", "sip_number"),
        ("development_stage", "development_stage"),
        ("analyst", "analyst"),
        ("unifi_number", "unifi_number"),
        ("note", "note")
    ]

    for db_field, row_field in text_fields:
        db_value = getattr(db_sample, db_field, None) or ""
        original_value = original_row.get(row_field, "")

        if str(db_value) != str(original_value):
            return True

    # Check numeric fields
    numeric_fields = [
        ("hf_octet_titer", "hf_octet_titer"),
        ("pro_aqa_hf_titer", "pro_aqa_hf_titer"),
        ("pro_aqa_e_titer", "pro_aqa_e_titer"),
        ("proa_eluate_a280_conc", "proa_eluate_a280_conc"),
        ("hccf_loading_volume", "hccf_loading_volume"),
        ("proa_eluate_volume", "proa_eluate_volume")
    ]

    for db_field, row_field in numeric_fields:
        db_value = getattr(db_sample, db_field, None)
        original_value = original_row.get(row_field, "")

        # Convert to comparable format
        if db_value is None:
            db_str = ""
        else:
            db_str = str(db_value).rstrip('0').rstrip('.') if '.' in str(db_value) else str(db_value)

        original_str = str(original_value).rstrip('0').rstrip('.') if original_value and '.' in str(
            original_value) else str(original_value)

        if db_str != original_str:
            return True

    # Check date field
    db_date = db_sample.harvest_date
    original_date_str = original_row.get("harvest_date", "")

    if db_date:
        db_date_str = db_date.strftime("%Y-%m-%d")
    else:
        db_date_str = ""

    if db_date_str != original_date_str:
        return True

    return False


def get_changed_fields(db_sample, original_row):
    """Get list of fields that changed in database"""
    changed_fields = []

    # Check all fields and collect changes
    fields_to_check = [
        ("cell_line", "cell_line", "Clone"),
        ("sip_number", "sip_number", "SIP"),
        ("development_stage", "development_stage", "Stage"),
        ("analyst", "analyst", "Analyst"),
        ("harvest_date", "harvest_date", "Harvest Date"),
        ("unifi_number", "unifi_number", "Unifi"),
        ("hf_octet_titer", "hf_octet_titer", "HF Titer"),
        ("pro_aqa_hf_titer", "pro_aqa_hf_titer", "ProAqa HF"),
        ("pro_aqa_e_titer", "pro_aqa_e_titer", "ProAqa E"),
        ("proa_eluate_a280_conc", "proa_eluate_a280_conc", "A280"),
        ("hccf_loading_volume", "hccf_loading_volume", "HF Vol"),
        ("proa_eluate_volume", "proa_eluate_volume", "Eluate Vol"),
        ("note", "note", "Note")
    ]

    for db_field, row_field, display_name in fields_to_check:
        if db_field == "harvest_date":
            db_value = getattr(db_sample, db_field, None)
            db_str = db_value.strftime("%Y-%m-%d") if db_value else ""
            original_str = original_row.get(row_field, "")

            if db_str != original_str:
                changed_fields.append(display_name)
        else:
            db_value = getattr(db_sample, db_field, None)
            original_value = original_row.get(row_field, "")

            # Normalize for comparison
            if db_value is None:
                db_str = ""
            elif isinstance(db_value, (int, float)):
                db_str = str(db_value).rstrip('0').rstrip('.') if '.' in str(db_value) else str(db_value)
            else:
                db_str = str(db_value)

            original_str = str(original_value).rstrip('0').rstrip('.') if original_value and '.' in str(
                original_value) else str(original_value)

            if db_str != original_str:
                changed_fields.append(display_name)

    return changed_fields


def has_row_changed(current_row, original_row):
    """Check if user has changed any values in the row"""
    fields_to_check = [
        "cell_line", "sip_number", "development_stage", "analyst",
        "harvest_date", "unifi_number", "note",
        "hf_octet_titer", "pro_aqa_hf_titer", "pro_aqa_e_titer",
        "proa_eluate_a280_conc", "hccf_loading_volume", "proa_eluate_volume"
    ]

    for field in fields_to_check:
        current_val = str(current_row.get(field, '')).strip()
        original_val = str(original_row.get(field, '')).strip()

        if current_val != original_val:
            return True

    return False


def save_single_sample(row_data):
    """Save a single sample to database"""
    try:
        sample_num = row_data.get('sample_number')
        if not sample_num:
            return False

        # Prepare update data
        update_data = {
            'cell_line': row_data.get('cell_line', ''),
            'sip_number': row_data.get('sip_number', ''),
            'development_stage': row_data.get('development_stage', ''),
            'analyst': row_data.get('analyst', ''),
            'unifi_number': row_data.get('unifi_number', ''),
            'note': row_data.get('note', ''),
        }

        # Handle date field
        harvest_date_str = row_data.get('harvest_date', '')
        if harvest_date_str:
            try:
                update_data['harvest_date'] = datetime.strptime(harvest_date_str, "%Y-%m-%d").date()
            except:
                update_data['harvest_date'] = None
        else:
            update_data['harvest_date'] = None

        # Handle numeric fields
        numeric_fields = [
            'hf_octet_titer', 'pro_aqa_hf_titer', 'pro_aqa_e_titer',
            'proa_eluate_a280_conc', 'hccf_loading_volume', 'proa_eluate_volume'
        ]

        for field in numeric_fields:
            value = row_data.get(field, '')
            if value and str(value).strip():
                try:
                    update_data[field] = float(value)
                except (ValueError, TypeError):
                    update_data[field] = None
            else:
                update_data[field] = None

        # Use update_or_create
        sample, created = LimsUpstreamSamples.objects.update_or_create(
            sample_number=int(sample_num),
            sample_type=2,
            defaults=update_data
        )

        return True

    except Exception as e:
        print(f"❌ Error saving sample {sample_num}: {e}")
        return False


def build_sample_row_with_recoveries(sample_obj):
    """Build a row dictionary from a sample object with calculated recoveries"""
    # Calculate recoveries
    fast_recovery = ""
    a280_recovery = ""

    try:
        if sample_obj.pro_aqa_hf_titer and sample_obj.pro_aqa_e_titer and sample_obj.pro_aqa_hf_titer > 0:
            fast_recovery = round((sample_obj.pro_aqa_e_titer / sample_obj.pro_aqa_hf_titer) * 100, 1)
    except:
        pass

    try:
        if all([sample_obj.hccf_loading_volume, sample_obj.proa_eluate_volume,
                sample_obj.hf_octet_titer, sample_obj.proa_eluate_a280_conc]):
            if all([x > 0 for x in [sample_obj.hccf_loading_volume, sample_obj.proa_eluate_volume,
                                    sample_obj.hf_octet_titer, sample_obj.proa_eluate_a280_conc]]):
                total_load = sample_obj.hccf_loading_volume * sample_obj.hf_octet_titer
                total_elute = sample_obj.proa_eluate_volume * sample_obj.proa_eluate_a280_conc
                a280_recovery = round((total_elute / total_load) * 100, 1)
    except:
        pass

    return {
        "project": sample_obj.project or "",
        "sample_number": sample_obj.sample_number,
        "cell_line": sample_obj.cell_line or "",
        "sip_number": sample_obj.sip_number or "",
        "development_stage": sample_obj.development_stage or "",
        "analyst": sample_obj.analyst or "",
        "harvest_date": sample_obj.harvest_date.strftime("%Y-%m-%d") if sample_obj.harvest_date else "",
        "unifi_number": sample_obj.unifi_number or "",
        "hf_octet_titer": sample_obj.hf_octet_titer if sample_obj.hf_octet_titer is not None else "",
        "pro_aqa_hf_titer": sample_obj.pro_aqa_hf_titer if sample_obj.pro_aqa_hf_titer is not None else "",
        "pro_aqa_e_titer": sample_obj.pro_aqa_e_titer if sample_obj.pro_aqa_e_titer is not None else "",
        "proa_eluate_a280_conc": sample_obj.proa_eluate_a280_conc if sample_obj.proa_eluate_a280_conc is not None else "",
        "hccf_loading_volume": sample_obj.hccf_loading_volume if sample_obj.hccf_loading_volume is not None else "",
        "proa_eluate_volume": sample_obj.proa_eluate_volume if sample_obj.proa_eluate_volume is not None else "",
        "note": sample_obj.note or "",
        "fast_pro_a_recovery": fast_recovery,
        "purification_recovery_a280": a280_recovery
    }


print("✅ SAVE ALL ROWS with CONFLICT DETECTION ready!")
print("   ✅ Saves ALL samples on current page (catches copy/paste)")
print("   ✅ Conflict detection only happens when you save")
print("   ✅ Clear reporting: changed, unchanged, conflicts, errors")
print("   ✅ Shows which fields were changed in conflicts")