# cld_dashboard/samples/callbacks/file_upload_handlers.py - Simple version
from dash import Input, Output, State, html, no_update, dcc
import dash_bootstrap_components as dbc
import pandas as pd
import base64
import io
from datetime import datetime
from plotly_integration.cld_dashboard.main_app import app

print("🔧 Registering file upload handlers...")


# Template upload handler
@app.callback(
    [Output("template-upload-status", "children"),
     Output("up-sample-table", "data", allow_duplicate=True),
     Output("creation-method", "value", allow_duplicate=True)],
    Input("upload-template-file", "contents"),
    [State("upload-template-file", "filename"),
     State("up-sample-table", "data")],
    prevent_initial_call=True
)
def process_template_upload(contents, filename, existing_data):
    """Process uploaded template file"""
    if not contents:
        return no_update, no_update, no_update

    try:
        print(f"📤 Processing template upload: {filename}")

        # Decode file
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        # Read Excel file
        if filename.endswith('.xlsx') or filename.endswith('.xls'):
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-circle me-2"),
                "Please upload an Excel file (.xlsx or .xls)"
            ], color="danger"), no_update, no_update

        print(f"📊 Excel file loaded: {len(df)} rows, {len(df.columns)} columns")

        # Process the data into sample table format
        new_data = []

        # Get starting sample number
        from plotly_integration.models import LimsUpstreamSamples
        from django.db.models import Max

        db_max = LimsUpstreamSamples.objects.filter(sample_type=2).aggregate(Max("sample_number"))
        next_sample_number = (db_max["sample_number__max"] or 0) + 1

        # Process each row
        for idx, row in df.iterrows():
            # Skip empty rows
            if pd.isna(row.get("Clone")) and pd.isna(row.get("HF Octet Titer")):
                continue

            # Parse harvest date
            harvest_date = ""
            if pd.notna(row.get("Harvest Date")):
                try:
                    date_val = pd.to_datetime(row["Harvest Date"])
                    harvest_date = date_val.strftime("%Y-%m-%d")
                except:
                    harvest_date = str(row["Harvest Date"])

            sample_data = {
                "sample_number": next_sample_number + idx,
                "cell_line": str(row.get("Clone", "")) if pd.notna(row.get("Clone")) else "",
                "harvest_date": harvest_date,
                "hf_octet_titer": row.get("HF Octet Titer") if pd.notna(row.get("HF Octet Titer")) else "",
                "pro_aqa_hf_titer": row.get("ProAqa HF Titer") if pd.notna(row.get("ProAqa HF Titer")) else "",
                "pro_aqa_e_titer": row.get("ProAqa E Titer") if pd.notna(row.get("ProAqa E Titer")) else "",
                "proa_eluate_a280_conc": row.get("Eluate A280") if pd.notna(row.get("Eluate A280")) else "",
                "hccf_loading_volume": row.get("HF Volume (mL)") if pd.notna(row.get("HF Volume (mL)")) else "",
                "proa_eluate_volume": row.get("Eluate Volume (mL)") if pd.notna(row.get("Eluate Volume (mL)")) else "",
                "fast_pro_a_recovery": "",  # Will be calculated
                "purification_recovery_a280": "",  # Will be calculated
                "note": str(row.get("Note", "")) if pd.notna(row.get("Note")) else ""
            }

            new_data.append(sample_data)

        if not new_data:
            return dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                "No valid data found in the uploaded file"
            ], color="warning"), no_update, no_update

        # Success message
        status = dbc.Alert([
            html.H6([
                html.I(className="fas fa-check-circle me-2"),
                "Template uploaded successfully!"
            ], className="alert-heading"),
            html.P(f"Loaded {len(new_data)} samples from {filename}"),
            html.Hr(),
            html.P("Switched to manual entry mode. You can now edit the data before saving.",
                   className="mb-0")
        ], color="success", dismissable=True)

        # Merge with existing data if any
        combined_data = existing_data + new_data if existing_data else new_data

        print(f"✅ Template processed: {len(new_data)} samples loaded")
        return status, combined_data, "manual"

    except Exception as e:
        print(f"❌ Error processing template: {e}")
        error_msg = dbc.Alert([
            html.H6("Upload Error", className="alert-heading"),
            html.P(f"Failed to process {filename}: {str(e)}"),
            html.P("Please check your file format and try again.", className="small")
        ], color="danger", dismissable=True)

        return error_msg, no_update, no_update


# Bulk upload preview handler
@app.callback(
    [Output("bulk-upload-preview", "children"),
     Output("bulk-upload-status", "children")],
    Input("bulk-upload-area", "contents"),
    [State("bulk-upload-area", "filename")],
    prevent_initial_call=True
)
def handle_bulk_upload(contents, filename):
    """Handle bulk upload with preview"""
    if not contents:
        return no_update, no_update

    try:
        print(f"📤 Processing bulk upload: {filename}")

        # Decode file
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        # Read file based on extension
        if filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(decoded))
        elif filename.endswith('.xlsx') or filename.endswith('.xls'):
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            return "", dbc.Alert(
                "Unsupported file format. Please upload CSV or Excel files.",
                color="danger"
            )

        print(f"📊 File loaded: {len(df)} rows, {len(df.columns)} columns")

        # Create simple preview
        preview_card = dbc.Card([
            dbc.CardHeader([
                html.H5([
                    html.I(className="fas fa-file-alt me-2"),
                    f"Preview: {filename}"
                ], className="mb-0")
            ]),
            dbc.CardBody([
                html.P(f"Found {len(df)} rows and {len(df.columns)} columns"),
                html.H6("First 5 rows:"),
                dbc.Table.from_dataframe(
                    df.head(),
                    striped=True,
                    bordered=True,
                    hover=True,
                    responsive=True,
                    size="sm"
                ),
                html.Hr(),
                dbc.Alert([
                    html.I(className="fas fa-info-circle me-2"),
                    "Bulk upload functionality is coming soon! For now, please use the template import method."
                ], color="info")
            ])
        ], className="shadow-sm")

        return preview_card, ""

    except Exception as e:
        print(f"❌ Error processing bulk upload: {e}")
        return "", dbc.Alert([
            html.H6("Upload Error"),
            html.P(f"Failed to read {filename}: {str(e)}")
        ], color="danger")


print("✅ File upload handlers registered successfully")