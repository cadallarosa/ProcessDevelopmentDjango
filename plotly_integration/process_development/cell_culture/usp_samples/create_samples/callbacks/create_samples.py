from dash import Input, Output, State, no_update, html, dcc, ctx
import dash_bootstrap_components as dbc
import pandas as pd
from plotly_integration.models import LimsUpstreamSamples, LimsSampleAnalysis, LimsProjectInformation, UspSampleSet, UspSampleSetMembership
import json
import base64
import io
from dash.exceptions import PreventUpdate
from django.db.models import Max
from datetime import datetime

print("🔧 Registering USP create_samples callbacks...")


def register_callbacks(app):
    """Register all USP create samples callbacks"""
    
    # ✅ MAIN CALLBACK FOR CREATION METHOD CONTENT
    @app.callback(
        Output("usp-creation-method-content", "children"),
        Input("usp-creation-method", "value"),
        prevent_initial_call=False
    )
    def update_creation_method_content(method):
        """Update content based on selected creation method"""
        print(f"🔄 USP Creation method changed to: {method}")

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

    # ✅ TEMPLATE DOWNLOAD CALLBACK
    @app.callback(
        Output("usp-download-template-file", "data"),
        [Input("usp-download-template-btn", "n_clicks"),
         Input("usp-download-excel-template-btn", "n_clicks")],
        prevent_initial_call=True
    )
    def download_template(csv_clicks, excel_clicks):
        """Generate and download template file"""
        print("📥 Template download requested")
        
        if not csv_clicks and not excel_clicks:
            return no_update
            
        # Create template data for USP samples
        template_data = {
            'sample_number': ['', '', ''],
            'project': ['', '', ''],
            'cell_line': ['', '', ''],
            'experiment_number': ['', '', ''],
            'culture_duration': ['', '', ''],
            'vessel_type': ['', '', ''],
            'description': ['', '', ''],
            'development_stage': ['', '', ''],
            'analyst': ['', '', ''],
            'harvest_date': ['', '', ''],
            'unifi_number': ['', '', '']
        }
        
        df = pd.DataFrame(template_data)
        
        # Determine file format
        if excel_clicks:
            # Excel format
            output = io.BytesIO()
            df.to_excel(output, index=False, engine='openpyxl')
            data = base64.b64encode(output.getvalue()).decode()
            filename = f"usp_samples_template_{datetime.now().strftime('%Y%m%d')}.xlsx"
            return dcc.send_bytes(base64.b64decode(data), filename)
        else:
            # CSV format
            csv_string = df.to_csv(index=False)
            filename = f"usp_samples_template_{datetime.now().strftime('%Y%m%d')}.csv"
            return dict(content=csv_string, filename=filename)

    # ✅ MANUAL SAMPLE CREATION CALLBACK
    @app.callback(
        [Output("usp-manual-creation-status", "children"),
         Output("usp-sample-number-input", "value"),
         Output("usp-project-input", "value"),
         Output("usp-cell-line-input", "value"),
         Output("usp-experiment-number-input", "value"),
         Output("usp-culture-duration-input", "value"),
         Output("usp-vessel-type-input", "value"),
         Output("usp-description-input", "value"),
         Output("usp-development-stage-input", "value"),
         Output("usp-analyst-input", "value"),
         Output("usp-harvest-date-input", "value"),
         Output("usp-unifi-number-input", "value")],
        Input("usp-create-manual-sample-btn", "n_clicks"),
        [State("usp-sample-number-input", "value"),
         State("usp-project-input", "value"),
         State("usp-cell-line-input", "value"),
         State("usp-experiment-number-input", "value"),
         State("usp-culture-duration-input", "value"),
         State("usp-vessel-type-input", "value"),
         State("usp-description-input", "value"),
         State("usp-development-stage-input", "value"),
         State("usp-analyst-input", "value"),
         State("usp-harvest-date-input", "value"),
         State("usp-unifi-number-input", "value")],
        prevent_initial_call=True
    )
    def create_manual_sample(n_clicks, sample_number, project, cell_line, experiment_number,
                           culture_duration, vessel_type, description, development_stage,
                           analyst, harvest_date, unifi_number):
        """Create a single sample manually"""
        
        if not n_clicks:
            return no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
        
        try:
            # Validation
            if not sample_number or not project:
                return dbc.Alert("Sample number and project are required!", color="danger"), no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
            
            # Check if sample already exists
            if LimsUpstreamSamples.objects.filter(sample_type=1, sample_number=int(sample_number)).exists():
                return dbc.Alert(f"Sample UP{sample_number} already exists!", color="warning"), no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
            
            # Parse harvest date if provided
            harvest_date_obj = None
            if harvest_date:
                try:
                    harvest_date_obj = datetime.strptime(harvest_date, '%Y-%m-%d').date()
                except ValueError:
                    return dbc.Alert("Invalid harvest date format! Use YYYY-MM-DD.", color="danger"), no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update
            
            # Create the sample
            sample = LimsUpstreamSamples.objects.create(
                sample_type=1,  # UP sample
                sample_number=int(sample_number),
                project=project,
                cell_line=cell_line,
                experiment_number=int(experiment_number) if experiment_number else None,
                culture_duration=int(culture_duration) if culture_duration else None,
                vessel_type=vessel_type,
                description=description,
                development_stage=development_stage,
                analyst=analyst,
                harvest_date=harvest_date_obj,
                unifi_number=unifi_number
            )
            
            success_msg = dbc.Alert([
                html.I(className="fas fa-check-circle me-2"),
                f"Successfully created sample UP{sample_number}!"
            ], color="success", dismissable=True, duration=4000)
            
            # Clear form fields
            return success_msg, "", "", "", "", "", "", "", "", "", "", ""
            
        except Exception as e:
            error_msg = dbc.Alert([
                html.I(className="fas fa-exclamation-triangle me-2"),
                f"Error creating sample: {str(e)}"
            ], color="danger", dismissable=True)
            
            return error_msg, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update, no_update

    # ✅ BULK UPLOAD CALLBACK
    @app.callback(
        [Output("usp-upload-status", "children"),
         Output("usp-upload-preview", "children")],
        [Input("usp-upload-data", "contents"),
         Input("usp-process-upload-btn", "n_clicks")],
        [State("usp-upload-data", "filename"),
         State("usp-upload-preview-store", "data")],
        prevent_initial_call=True
    )
    def handle_bulk_upload(contents, process_clicks, filename, preview_data):
        """Handle bulk upload of USP samples"""
        
        if not contents and not process_clicks:
            return no_update, no_update
        
        ctx_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if ctx_id == "usp-upload-data" and contents:
            # File uploaded - show preview
            try:
                content_type, content_string = contents.split(',')
                decoded = base64.b64decode(content_string)
                
                # Read file based on extension
                if 'csv' in filename.lower():
                    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
                elif 'xlsx' in filename.lower() or 'xls' in filename.lower():
                    df = pd.read_excel(io.BytesIO(decoded))
                else:
                    return dbc.Alert("Unsupported file format! Please use CSV or Excel.", color="danger"), ""
                
                # Validate required columns
                required_cols = ['sample_number', 'project']
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                if missing_cols:
                    return dbc.Alert(f"Missing required columns: {missing_cols}", color="danger"), ""
                
                # Show preview
                preview = html.Div([
                    html.H6(f"Preview of {filename} ({len(df)} rows)"),
                    html.Div(df.head(10).to_html(classes='table table-striped', table_id='preview-table'), 
                            dangerously_allow_html=True),
                    dbc.Button("Process Upload", id="usp-process-upload-btn", color="primary", className="mt-2"),
                    dcc.Store(id="usp-upload-preview-store", data=df.to_dict('records'))
                ])
                
                return "", preview
                
            except Exception as e:
                return dbc.Alert(f"Error reading file: {str(e)}", color="danger"), ""
        
        elif ctx_id == "usp-process-upload-btn" and process_clicks and preview_data:
            # Process the upload
            try:
                created_count = 0
                errors = []
                
                for idx, row in enumerate(preview_data):
                    try:
                        # Check if sample exists
                        sample_number = int(row['sample_number'])
                        if LimsUpstreamSamples.objects.filter(sample_type=1, sample_number=sample_number).exists():
                            errors.append(f"Row {idx+1}: Sample UP{sample_number} already exists")
                            continue
                        
                        # Parse harvest date if provided
                        harvest_date_obj = None
                        if row.get('harvest_date'):
                            try:
                                harvest_date_obj = datetime.strptime(str(row['harvest_date']), '%Y-%m-%d').date()
                            except:
                                pass  # Skip invalid dates
                        
                        # Create sample
                        LimsUpstreamSamples.objects.create(
                            sample_type=1,  # UP sample
                            sample_number=sample_number,
                            project=row['project'],
                            cell_line=row.get('cell_line'),
                            experiment_number=int(row['experiment_number']) if row.get('experiment_number') else None,
                            culture_duration=int(row['culture_duration']) if row.get('culture_duration') else None,
                            vessel_type=row.get('vessel_type'),
                            description=row.get('description'),
                            development_stage=row.get('development_stage'),
                            analyst=row.get('analyst'),
                            harvest_date=harvest_date_obj,
                            unifi_number=row.get('unifi_number')
                        )
                        created_count += 1
                        
                    except Exception as e:
                        errors.append(f"Row {idx+1}: {str(e)}")
                
                # Build result message
                status_elements = []
                
                if created_count > 0:
                    status_elements.append(
                        dbc.Alert([
                            html.I(className="fas fa-check-circle me-2"),
                            f"Successfully created {created_count} USP samples!"
                        ], color="success")
                    )
                
                if errors:
                    status_elements.append(
                        dbc.Alert([
                            html.I(className="fas fa-exclamation-triangle me-2"),
                            html.Div([
                                html.P("Some errors occurred:"),
                                html.Ul([html.Li(error) for error in errors[:10]])  # Show first 10 errors
                            ])
                        ], color="warning")
                    )
                
                return status_elements, ""
                
            except Exception as e:
                return dbc.Alert(f"Error processing upload: {str(e)}", color="danger"), ""
        
        return no_update, no_update

    print("✅ USP Create Samples callbacks registered successfully")