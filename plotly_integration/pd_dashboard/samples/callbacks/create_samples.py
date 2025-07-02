# cld_dashboard/samples/callbacks/create_samples.py - Fixed syntax errors
from dash import Input, Output, State, no_update, html, dcc, ctx
import dash_bootstrap_components as dbc
import pandas as pd
from plotly_integration.models import LimsUpstreamSamples, LimsSampleAnalysis, LimsProjectInformation
import json
import base64
import io
from dash.exceptions import PreventUpdate
from django.db.models import Max
from datetime import datetime
from plotly_integration.cld_dashboard.main_app import app

print("🔧 Registering create_samples callbacks...")


# ✅ MAIN CALLBACK FOR CREATION METHOD CONTENT
@app.callback(
    Output("creation-method-content", "children"),
    Input("creation-method", "value"),
    prevent_initial_call=False  # Allow initial call to populate content
)
def update_creation_method_content(method):
    """Update content based on selected creation method"""
    print(f"🔄 Creation method changed to: {method}")

    if method == "manual":
        from ..layouts.create_samples import create_manual_entry_section
        return create_manual_entry_section()
    elif method == "template":
        from ..layouts.create_samples import create_template_import_section
        return create_template_import_section()
    elif method == "upload":
        from ..layouts.create_samples import create_bulk_upload_section
        return create_bulk_upload_section()

    # Default fallback
    return html.Div([
        dbc.Alert([
            html.I(className="fas fa-info-circle me-2"),
            "Please select a creation method to continue."
        ], color="info")
    ])


# ✅ FIXED TEMPLATE DOWNLOAD CALLBACK - NO CONTEXT USAGE
@app.callback(
    Output("download-template-file", "data"),
    [Input("download-template-btn", "n_clicks"),
     Input("download-excel-template-btn", "n_clicks")],
    prevent_initial_call=True
)
def download_sample_template(download_btn_clicks, excel_btn_clicks):
    """Generate and download Excel template for sample creation"""
    # Simple check - if either button was clicked
    if not download_btn_clicks and not excel_btn_clicks:
        return no_update

    try:
        print(f"📥 Generating template download")

        # Create template dataframe with detailed instructions
        template_data = {
            "Clone": ["CHO-K1-001", "CHO-K1-002", "CHO-K1-003", "", ""],
            "Harvest Date": ["2025-01-15", "2025-01-16", "2025-01-17", "", ""],
            "HF Octet Titer": [5.2, 4.8, 5.5, "", ""],
            "ProAqa HF Titer": [5.1, 4.7, 5.4, "", ""],
            "ProAqa E Titer": [4.5, 4.2, 4.8, "", ""],
            "Eluate A280": [25.3, 22.1, 24.8, "", ""],
            "HF Volume (mL)": [250, 250, 250, "", ""],
            "Eluate Volume (mL)": [25, 25, 25, "", ""],
            "Note": ["Good recovery", "Check pH", "Standard run", "", ""]
        }

        df = pd.DataFrame(template_data)

        # Create Excel file in memory - try different engines
        output = io.BytesIO()
        excel_engine = None

        # Try xlsxwriter first, then openpyxl, then fallback to CSV
        try:
            excel_engine = 'xlsxwriter'
            with pd.ExcelWriter(output, engine=excel_engine) as writer:
                # Write sample data sheet
                df.to_excel(writer, sheet_name='Sample_Data', index=False)

                # Get workbook and worksheet objects
                workbook = writer.book
                worksheet = writer.sheets['Sample_Data']

                # Create formats (only for xlsxwriter)
                header_format = workbook.add_format({
                    'bold': True,
                    'bg_color': '#1976d2',
                    'font_color': 'white',
                    'border': 1,
                    'align': 'center'
                })

                example_format = workbook.add_format({
                    'bg_color': '#fff3cd',
                    'border': 1
                })

                # Format header row
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)

                # Format example rows
                for row in range(1, 4):  # First 3 data rows are examples
                    for col in range(len(df.columns)):
                        worksheet.write(row, col, df.iloc[row - 1, col], example_format)

                # Set column widths
                worksheet.set_column('A:A', 15)  # Clone
                worksheet.set_column('B:B', 15)  # Harvest Date
                worksheet.set_column('C:H', 15)  # Numeric columns
                worksheet.set_column('I:I', 30)  # Note

                # Add instructions sheet
                instructions_data = [
                    ["CLD Sample Creation Template - Instructions", ""],
                    ["", ""],
                    ["IMPORTANT NOTES:", ""],
                    ["1. Column Headers", "Do not modify column headers - they must match exactly"],
                    ["2. Sample Numbers", "Will be auto-generated - do not include them"],
                    ["3. Titer Units", "All titer values should be in g/L"],
                    ["4. Volume Units", "All volumes should be in mL"],
                    ["5. Date Format", "Use YYYY-MM-DD format for dates"],
                    ["6. Recovery Calculations", "Will be calculated automatically upon upload"],
                    ["", ""],
                    ["COLUMN DESCRIPTIONS:", ""],
                    ["Clone", "Cell line or clone identifier (required)"],
                    ["Harvest Date", "Date of harvest in YYYY-MM-DD format"],
                    ["HF Octet Titer", "Harvest fluid titer measured by Octet (g/L)"],
                    ["ProAqa HF Titer", "Harvest fluid titer measured by ProA HPLC (g/L)"],
                    ["ProAqa E Titer", "Eluate titer measured by ProA HPLC (g/L)"],
                    ["Eluate A280", "Eluate concentration by A280 measurement (g/L)"],
                    ["HF Volume (mL)", "Volume of harvest fluid loaded (mL)"],
                    ["Eluate Volume (mL)", "Volume of eluate collected (mL)"],
                    ["Note", "Any additional notes or comments"],
                    ["", ""],
                    ["EXAMPLE DATA:", ""],
                    ["The first 3 rows contain example data", "Delete these before adding your real data"],
                    ["", ""],
                    ["CALCULATIONS PERFORMED:", ""],
                    ["ProA Recovery %", "= (ProAqa E Titer / ProAqa HF Titer) × 100"],
                    ["A280 Recovery %", "= (Eluate A280 × Eluate Volume) / (HF Octet Titer × HF Volume) × 100"]
                ]

                df_instructions = pd.DataFrame(instructions_data, columns=['Instruction', 'Details'])
                df_instructions.to_excel(writer, sheet_name='Instructions', index=False)

                # Format instructions sheet
                inst_worksheet = writer.sheets['Instructions']
                inst_worksheet.set_column('A:A', 40)
                inst_worksheet.set_column('B:B', 60)

                # Title format for instructions
                title_format = workbook.add_format({
                    'bold': True,
                    'font_size': 14,
                    'bg_color': '#1976d2',
                    'font_color': 'white',
                    'align': 'center'
                })

        except ImportError:
            # Try openpyxl engine
            try:
                excel_engine = 'openpyxl'
                output = io.BytesIO()  # Reset output buffer
                with pd.ExcelWriter(output, engine=excel_engine) as writer:
                    # Write sample data sheet
                    df.to_excel(writer, sheet_name='Sample_Data', index=False)

                    # Add instructions sheet
                    instructions_data = [
                        ["CLD Sample Creation Template - Instructions", ""],
                        ["", ""],
                        ["IMPORTANT NOTES:", ""],
                        ["1. Column Headers", "Do not modify column headers - they must match exactly"],
                        ["2. Sample Numbers", "Will be auto-generated - do not include them"],
                        ["3. Titer Units", "All titer values should be in g/L"],
                        ["4. Volume Units", "All volumes should be in mL"],
                        ["5. Date Format", "Use YYYY-MM-DD format for dates"],
                        ["6. Recovery Calculations", "Will be calculated automatically upon upload"],
                        ["", ""],
                        ["COLUMN DESCRIPTIONS:", ""],
                        ["Clone", "Cell line or clone identifier (required)"],
                        ["Harvest Date", "Date of harvest in YYYY-MM-DD format"],
                        ["HF Octet Titer", "Harvest fluid titer measured by Octet (g/L)"],
                        ["ProAqa HF Titer", "Harvest fluid titer measured by ProA HPLC (g/L)"],
                        ["ProAqa E Titer", "Eluate titer measured by ProA HPLC (g/L)"],
                        ["Eluate A280", "Eluate concentration by A280 measurement (g/L)"],
                        ["HF Volume (mL)", "Volume of harvest fluid loaded (mL)"],
                        ["Eluate Volume (mL)", "Volume of eluate collected (mL)"],
                        ["Note", "Any additional notes or comments"],
                        ["", ""],
                        ["CALCULATIONS PERFORMED:", ""],
                        ["ProA Recovery %", "= (ProAqa E Titer / ProAqa HF Titer) × 100"],
                        ["A280 Recovery %", "= (Eluate A280 × Eluate Volume) / (HF Octet Titer × HF Volume) × 100"]
                    ]

                    df_instructions = pd.DataFrame(instructions_data, columns=['Instruction', 'Details'])
                    df_instructions.to_excel(writer, sheet_name='Instructions', index=False)

            except ImportError:
                # Fallback to CSV if no Excel engines available
                print("⚠️ No Excel engines available, falling back to CSV")
                output = io.BytesIO()  # Reset output buffer
                csv_content = df.to_csv(index=False)
                output.write(csv_content.encode('utf-8'))
                filename = f"CLD_sample_template_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"

                output.seek(0)
                print(f"✅ CSV template generated: {filename}")

                return dcc.send_bytes(
                    output.read(),
                    filename=filename
                )

        # If we got here, Excel generation was successful
        output.seek(0)
        filename = f"CLD_sample_template_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"

        print(f"✅ Excel template generated with {excel_engine}: {filename}")

        return dcc.send_bytes(
            output.read(),
            filename=filename
        )

    except Exception as e:
        print(f"❌ Error generating template: {e}")
        import traceback
        traceback.print_exc()
        return no_update


# Sample Creation - connected to CLD database
@app.callback(
    Output("up-project-dropdown", "options"),
    Input("parsed-pathname", "data"),
    prevent_initial_call=False
)
def populate_project_dropdown(pathname):
    """Populate project dropdown from CLD database"""
    if pathname != "/samples/create":
        raise PreventUpdate

    try:
        # Get unique projects from existing samples and project information
        existing_projects = LimsUpstreamSamples.objects.values_list('project', flat=True).distinct()
        project_info = LimsProjectInformation.objects.all().order_by("protein", "molecule_type")

        options = []

        # Add projects from LimsProjectInformation if available
        for p in project_info:
            if p.protein and p.molecule_type:
                options.append({
                    "label": f"🧬 {p.protein} - {p.molecule_type}",
                    "value": f"{p.protein}"
                })

        # Add any existing projects not in LimsProjectInformation
        for project in existing_projects:
            if project and not any(opt["value"] == project for opt in options):
                options.append({
                    "label": f"📊 {project} (Existing)",
                    "value": project
                })

        # Remove duplicates and sort
        seen = set()
        unique_options = []
        for opt in options:
            if opt["value"] not in seen:
                seen.add(opt["value"])
                unique_options.append(opt)

        return sorted(unique_options, key=lambda x: x["label"])

    except Exception as e:
        print(f"Error loading projects: {e}")
        return [{"label": "❌ Error loading projects", "value": ""}]


# ✅ FIXED SAMPLE TABLE CALLBACK - NO CALLBACK CONTEXT
@app.callback(
    Output("up-sample-table", "data"),
    [Input("add-up-row", "n_clicks"),
     Input("clear-up-table", "n_clicks")],
    [State("up-sample-table", "data")],
    prevent_initial_call=True
)
def modify_sample_table(add_clicks, clear_clicks, current_data):
    """Modify sample table - NO CONTEXT USAGE"""
    if current_data is None:
        current_data = []

    # ✅ SIMPLE CHECK - No context needed
    if clear_clicks and (not add_clicks or clear_clicks > add_clicks):
        print("🧹 Clearing table")
        return []

    if add_clicks:
        try:
            print("➕ Adding new row")
            # Get max sample number from CLD database
            db_max = LimsUpstreamSamples.objects.filter(sample_type=2).aggregate(Max("sample_number"))
            max_sample_number = db_max["sample_number__max"] or 0

            # Check in-memory data for higher numbers
            current_numbers = []
            for row in current_data:
                try:
                    num = int(row.get("sample_number", 0))
                    current_numbers.append(num)
                except (ValueError, TypeError):
                    pass

            if current_numbers:
                max_sample_number = max(max_sample_number, max(current_numbers))

            next_sample_number = max_sample_number + 1

            # Create new row with default values
            new_row = {
                "sample_number": next_sample_number,
                "cell_line": "",
                "harvest_date": datetime.now().strftime("%Y-%m-%d"),  # Default to today
                "hf_octet_titer": "",
                "pro_aqa_hf_titer": "",
                "pro_aqa_e_titer": "",
                "proa_eluate_a280_conc": "",
                "hccf_loading_volume": "",
                "proa_eluate_volume": "",
                "fast_pro_a_recovery": "",
                "purification_recovery_a280": "",
                "note": ""
            }

            current_data.append(new_row)
            print(f"✅ Added sample {next_sample_number}, total rows: {len(current_data)}")
            return current_data

        except Exception as e:
            print(f"❌ Error adding row: {e}")
            import traceback
            traceback.print_exc()
            return current_data

    return current_data


@app.callback(
    [Output("up-sample-table", "data", allow_duplicate=True),
     Output("recovery-calculation-status", "children")],
    [Input("up-sample-table", "data")],
    prevent_initial_call=True
)
def calculate_recoveries_on_change(table_data):
    """Calculate recoveries when data changes"""
    if not table_data:
        return table_data, ""

    try:
        updated_data = []
        calculations_made = 0

        for row in table_data:
            updated_row = row.copy()

            # Calculate Fast ProA Recovery
            try:
                hf_titer = float(row.get("pro_aqa_hf_titer") or 0)
                e_titer = float(row.get("pro_aqa_e_titer") or 0)
                if hf_titer > 0 and e_titer > 0:
                    fast_pro_a = round((e_titer / hf_titer) * 100, 2)
                    updated_row["fast_pro_a_recovery"] = fast_pro_a
                    calculations_made += 1
                else:
                    updated_row["fast_pro_a_recovery"] = ""
            except (ValueError, TypeError):
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
                    a280_recovery = round((total_elute / total_load) * 100, 2)
                    updated_row["purification_recovery_a280"] = a280_recovery
                    calculations_made += 1
                else:
                    updated_row["purification_recovery_a280"] = ""
            except (ValueError, TypeError):
                updated_row["purification_recovery_a280"] = ""

            updated_data.append(updated_row)

        status_msg = ""
        if calculations_made > 0:
            status_msg = f"🧮 Calculated {calculations_made} recovery values"

        return updated_data, status_msg

    except Exception as e:
        print(f"Error calculating recoveries: {e}")
        return table_data, f"❌ Calculation error: {str(e)}"

#
# @app.callback(
#     Output("save-up-status", "children"),
#     Input("save-up-table", "n_clicks"),
#     [State("up-sample-table", "data"),
#      State("up-project-dropdown", "value"),
#      State("up-vessel-type", "value"),
#      State("cld-dev-stage", "value"),
#      State("cld-analyst", "value"),
#      State("sip-number", "value"),
#      State("unifi-number", "value")],
#     prevent_initial_call=True
# )
# def save_up_samples(n_clicks, table_data, project, vessel_type, dev_stage, analyst, sip_number, unifi_number):
#     """Save UP samples to CLD database"""
#     if not n_clicks:
#         return no_update
#
#     if not table_data:
#         return dbc.Alert("❌ No data to save.", color="warning", dismissable=True)
#     if not project or not vessel_type:
#         return dbc.Alert("⚠️ Please fill in Project and Vessel Type.", color="warning", dismissable=True)
#
#     print(f"💾 Saving UP samples for project '{project}' | vessel: {vessel_type}")
#
#     created, updated, skipped, errors = 0, 0, 0, 0
#     error_details = []
#
#     for row in table_data:
#         try:
#             sample_number = row.get("sample_number")
#             if not sample_number:
#                 skipped += 1
#                 continue
#
#             # Prepare data for saving
#             sample_data = {
#                 "project": project,
#                 "vessel_type": vessel_type,
#                 "sip_number": sip_number,
#                 "unifi_number": unifi_number,
#                 "development_stage": dev_stage,
#                 "analyst": analyst,
#                 "cell_line": row.get("cell_line") or "",
#                 "note": row.get("note") or "",
#             }
#
#             # Handle numeric fields
#             numeric_fields = [
#                 "hf_octet_titer", "pro_aqa_hf_titer", "pro_aqa_e_titer",
#                 "proa_eluate_a280_conc", "hccf_loading_volume", "proa_eluate_volume"
#             ]
#
#             for field in numeric_fields:
#                 value = row.get(field)
#                 if value and str(value).strip():
#                     try:
#                         sample_data[field] = float(value)
#                     except (ValueError, TypeError):
#                         sample_data[field] = None
#                 else:
#                     sample_data[field] = None
#
#             # Handle date field
#             harvest_date = row.get("harvest_date")
#             if harvest_date and str(harvest_date).strip():
#                 try:
#                     sample_data["harvest_date"] = datetime.strptime(harvest_date, "%Y-%m-%d").date()
#                 except ValueError:
#                     sample_data["harvest_date"] = None
#             else:
#                 sample_data["harvest_date"] = None
#
#             # Save to database
#             sample, created_flag = LimsUpstreamSamples.objects.update_or_create(
#                 sample_number=sample_number,
#                 sample_type=2,
#                 defaults=sample_data
#             )
#
#             # Create/update analysis record
#             LimsSampleAnalysis.objects.update_or_create(
#                 sample_id=f'FB{sample_number}',
#                 sample_type=2,
#                 defaults={
#                     "sample_date": sample_data["harvest_date"],
#                     "project_id": project,
#                     "description": row.get("description", ""),
#                     "notes": sample_data["note"],
#                     "dn": None,
#                     "a280_result": sample_data.get("proa_eluate_a280_conc")
#                 }
#             )
#
#             if created_flag:
#                 created += 1
#             else:
#                 updated += 1
#
#         except Exception as e:
#             error_msg = f"Sample {row.get('sample_number', 'Unknown')}: {str(e)}"
#             error_details.append(error_msg)
#             print(f"❌ Error saving sample {row.get('sample_number')}: {e}")
#             errors += 1
#
#     # Create comprehensive status message
#     if errors == 0:
#         return dbc.Alert([
#             html.H6("✅ Save Successful!", className="alert-heading"),
#             html.P([
#                 f"📝 Created: {created} samples | ",
#                 f"🔄 Updated: {updated} samples | ",
#                 f"⏭️ Skipped: {skipped} empty rows"
#             ], className="mb-0")
#         ], color="success", dismissable=True)
#     else:
#         return dbc.Alert([
#             html.H6("⚠️ Save Completed with Issues", className="alert-heading"),
#             html.P([
#                 f"✅ Created: {created} | 🔄 Updated: {updated} | ",
#                 f"❌ Errors: {errors} | ⏭️ Skipped: {skipped}"
#             ]),
#             html.Hr(),
#             html.H6("Error Details:", className="small"),
#             html.Ul([html.Li(error, className="small") for error in error_details[:5]]),
#             html.P(f"... and {len(error_details) - 5} more errors", className="small text-muted") if len(
#                 error_details) > 5 else ""
#         ], color="warning", dismissable=True)

@app.callback(
    Output("save-up-status", "children"),
    Input("save-up-table", "n_clicks"),
    [State("up-sample-table", "data"),
     State("up-project-dropdown", "value"),
     State("up-vessel-type", "value"),
     State("cld-dev-stage", "value"),
     State("cld-analyst", "value"),
     State("sip-number", "value"),
     State("unifi-number", "value")],
    prevent_initial_call=True
)
def save_up_samples(n_clicks, table_data, project, vessel_type, dev_stage, analyst, sip_number, unifi_number):
    """Save UP samples to CLD database"""
    if not n_clicks:
        return no_update

    if not table_data:
        return dbc.Alert("❌ No data to save.", color="warning", dismissable=True)
    if not project or not vessel_type:
        return dbc.Alert("⚠️ Please fill in Project and Vessel Type.", color="warning", dismissable=True)

    print(f"💾 Saving UP samples for project '{project}' | vessel: {vessel_type}")

    created, updated, skipped, errors = 0, 0, 0, 0
    error_details = []
    saved_sample_ids = []  # Track successfully saved samples for set creation

    for row in table_data:
        try:
            sample_number = row.get("sample_number")
            if not sample_number:
                skipped += 1
                continue

            # Prepare data for saving
            sample_data = {
                "project": project,
                "vessel_type": vessel_type,
                "sip_number": sip_number,
                "unifi_number": unifi_number,
                "development_stage": dev_stage,
                "analyst": analyst,
                "cell_line": row.get("cell_line") or "",
                "note": row.get("note") or "",
            }

            # Handle numeric fields
            numeric_fields = [
                "hf_octet_titer", "pro_aqa_hf_titer", "pro_aqa_e_titer",
                "proa_eluate_a280_conc", "hccf_loading_volume", "proa_eluate_volume"
            ]

            for field in numeric_fields:
                value = row.get(field)
                if value and str(value).strip():
                    try:
                        sample_data[field] = float(value)
                    except (ValueError, TypeError):
                        sample_data[field] = None
                else:
                    sample_data[field] = None

            # Handle date field
            harvest_date = row.get("harvest_date")
            if harvest_date and str(harvest_date).strip():
                try:
                    sample_data["harvest_date"] = datetime.strptime(harvest_date, "%Y-%m-%d").date()
                except ValueError:
                    sample_data["harvest_date"] = None
            else:
                sample_data["harvest_date"] = None

            # Save to database
            sample, created_flag = LimsUpstreamSamples.objects.update_or_create(
                sample_number=sample_number,
                sample_type=2,
                defaults=sample_data
            )

            # Create/update analysis record
            sample_analysis, _ = LimsSampleAnalysis.objects.update_or_create(
                sample_id=f'FB{sample_number}',
                sample_type=2,
                defaults={
                    "sample_date": sample_data["harvest_date"],
                    "project_id": project,
                    "description": row.get("description", ""),
                    "notes": sample_data["note"],
                    "analyst": analyst or "",
                    "dn": None,
                    "a280_result": sample_data.get("proa_eluate_a280_conc")
                }
            )

            saved_sample_ids.append(f'FB{sample_number}')

            if created_flag:
                created += 1
            else:
                updated += 1

        except Exception as e:
            error_msg = f"Sample {row.get('sample_number', 'Unknown')}: {str(e)}"
            error_details.append(error_msg)
            print(f"❌ Error saving sample {row.get('sample_number')}: {e}")
            errors += 1

    # Create/update sample set if samples were saved successfully
    set_created = False
    set_name = ""

    if saved_sample_ids and (created > 0 or updated > 0):
        try:
            # Generate sample set name
            set_name_parts = [project]
            if sip_number:
                set_name_parts.append(f"SIP{sip_number}")
            if dev_stage:
                set_name_parts.append(dev_stage)
            set_name = "_".join(set_name_parts)

            # Create or get sample set
            from plotly_integration.models import LimsSampleSet, LimsSampleSetMembership

            sample_set, set_created = LimsSampleSet.objects.get_or_create(
                project_id=project,
                sip_number=sip_number or "",
                development_stage=dev_stage or "",
                defaults={
                    'set_name': set_name,
                    'created_by': analyst or "system"
                }
            )

            # Add samples to set membership
            membership_created = 0
            for sample_id in saved_sample_ids:
                try:
                    sample_analysis = LimsSampleAnalysis.objects.get(sample_id=sample_id)
                    _, was_created = LimsSampleSetMembership.objects.get_or_create(
                        sample_set=sample_set,
                        sample=sample_analysis
                    )
                    if was_created:
                        membership_created += 1
                except LimsSampleAnalysis.DoesNotExist:
                    print(f"Warning: LimsSampleAnalysis not found for {sample_id}")

            # Update sample count
            sample_set.sample_count = sample_set.members.count()
            sample_set.save()

            print(
                f"✅ Sample set '{set_name}' {'created' if set_created else 'updated'} with {sample_set.sample_count} samples")

        except Exception as e:
            print(f"Error creating/updating sample set: {e}")
            # Don't fail the whole operation if sample set creation fails

    # Create comprehensive status message
    if errors == 0:
        status_parts = [
            html.H6("✅ Save Successful!", className="alert-heading"),
            html.P([
                f"📝 Created: {created} samples | ",
                f"🔄 Updated: {updated} samples | ",
                f"⏭️ Skipped: {skipped} empty rows"
            ], className="mb-0")
        ]

        if set_created:
            status_parts.append(html.Hr())
            status_parts.append(html.P([
                html.I(className="fas fa-layer-group me-2"),
                f"Created new sample set: {set_name}"
            ], className="text-success mb-0"))

        return dbc.Alert(status_parts, color="success", dismissable=True)
    else:
        return dbc.Alert([
            html.H6("⚠️ Save Completed with Issues", className="alert-heading"),
            html.P([
                f"✅ Created: {created} | 🔄 Updated: {updated} | ",
                f"❌ Errors: {errors} | ⏭️ Skipped: {skipped}"
            ]),
            html.Hr(),
            html.H6("Error Details:", className="small"),
            html.Ul([html.Li(error, className="small") for error in error_details[:5]]),
            html.P(f"... and {len(error_details) - 5} more errors", className="small text-muted") if len(
                error_details) > 5 else ""
        ], color="warning", dismissable=True)


@app.callback(
    [Output("sample-validation-results", "children"),
     Output("save-up-table", "disabled")],
    [Input("up-sample-table", "data"),
     Input("up-project-dropdown", "value")]
)
def validate_sample_data(table_data, project):
    """Validate sample data before saving"""
    if not table_data or not project:
        return "", True

    try:
        validation_issues = []
        warning_count = 0
        error_count = 0

        for i, row in enumerate(table_data):
            row_issues = []

            # Check required fields
            if not row.get("sample_number"):
                row_issues.append("Missing sample number")
                error_count += 1

            # Check for duplicate sample numbers in table
            sample_num = row.get("sample_number")
            if sample_num:
                duplicates = [j for j, r in enumerate(table_data) if r.get("sample_number") == sample_num and j != i]
                if duplicates:
                    row_issues.append(f"Duplicate sample number (also in row {duplicates[0] + 1})")
                    error_count += 1

                # Check if sample already exists in database
                if LimsUpstreamSamples.objects.filter(sample_number=sample_num, sample_type=2).exists():
                    row_issues.append("Sample already exists (will be updated)")
                    warning_count += 1

            # Check data consistency
            if row.get("pro_aqa_hf_titer") and row.get("pro_aqa_e_titer"):
                try:
                    hf = float(row["pro_aqa_hf_titer"])
                    e = float(row["pro_aqa_e_titer"])
                    if e > hf:
                        row_issues.append("Eluate titer > HF titer (unusual)")
                        warning_count += 1
                except:
                    pass

            if row_issues:
                validation_issues.append(f"Row {i + 1}: {'; '.join(row_issues)}")

        if not validation_issues:
            return dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"✅ All {len(table_data)} samples validated successfully"
            ], color="success"), False

        alert_color = "danger" if error_count > 0 else "warning"
        can_save = error_count == 0

        return dbc.Alert([
            html.H6(f"⚠️ Validation Issues Found", className="alert-heading"),
            html.P(f"🚨 Errors: {error_count} | ⚠️ Warnings: {warning_count}"),
            html.Hr(),
            html.Ul([html.Li(issue, className="small") for issue in validation_issues[:10]]),
            html.P(f"... and {len(validation_issues) - 10} more issues", className="small") if len(
                validation_issues) > 10 else ""
        ], color=alert_color), not can_save

    except Exception as e:
        return dbc.Alert(f"❌ Validation error: {str(e)}", color="danger"), True


@app.callback(
    Output("project-info-display", "children"),
    Input("up-project-dropdown", "value")
)
def display_project_info(project):
    """Display project information when selected"""
    if not project:
        return ""

    try:
        # Get project info from database
        project_info = LimsProjectInformation.objects.filter(protein=project).first()

        if project_info:
            return dbc.Alert([
                html.H6(f"🧬 Project: {project}", className="alert-heading"),
                html.P([
                    f"🔬 Molecule Type: {project_info.molecule_type or 'N/A'} | ",
                    f"⚖️ MW: {project_info.molecular_weight / 1000:.1f} kDa" if project_info.molecular_weight else "MW: N/A"
                ], className="mb-0 small")
            ], color="info")
        else:
            # Check if project exists in samples
            sample_count = LimsUpstreamSamples.objects.filter(project=project).count()
            if sample_count > 0:
                return dbc.Alert([
                    html.P([
                        f"📊 Existing project with {sample_count} samples"
                    ], className="mb-0 small")
                ], color="secondary")

        return ""

    except Exception as e:
        return dbc.Alert(f"Error loading project info: {str(e)}", color="warning")


@app.callback(
    Output("analyst-suggestions", "children"),
    Input("cld-analyst", "value")
)
def show_analyst_suggestions(analyst):
    """Show suggestions or stats for selected analyst"""
    if not analyst:
        return ""

    try:
        # Get recent samples by this analyst
        recent_samples = LimsUpstreamSamples.objects.filter(
            analyst=analyst,
            sample_type=2
        ).order_by('-created_at')[:5]

        if recent_samples:
            return dbc.Alert([
                html.H6(f"👨‍🔬 Recent samples by {analyst}:", className="small"),
                html.Ul([
                    html.Li(
                        f"FB{s.sample_number} - {s.project} ({s.created_at.strftime('%Y-%m-%d') if s.created_at else 'No date'})",
                        className="small")
                    for s in recent_samples
                ])
            ], color="light")

        return ""

    except Exception as e:
        return ""


print("✅ create_samples callbacks registered successfully")