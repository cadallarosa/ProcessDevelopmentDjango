"""
Template Upload Callbacks
Handle Excel template download and upload processing
"""

from dash import Input, Output, State, html, no_update
from dash.exceptions import PreventUpdate
import pandas as pd
import io
import base64
from datetime import datetime
import os


def register_upload_callbacks(app):
    """Register template upload and download callbacks"""

    @app.callback(
        Output('download-template', 'data'),
        Input('download-template-btn', 'n_clicks'),
        prevent_initial_call=True
    )
    def download_template(n_clicks):
        """Provide template file for download"""
        print("\n" + "="*80)
        print("DOWNLOAD TEMPLATE CALLBACK")
        print("="*80)

        try:
            # Get template path
            template_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'template'
            )
            template_path = os.path.join(template_dir, 'Plasma_Stability_Template.xlsx')

            # Check if file exists
            if not os.path.exists(template_path):
                print(f"✗ Template not found at {template_path}")
                raise FileNotFoundError(f"Template not found at {template_path}")

            print(f"✓ Template found: {template_path}")

            # Read template
            with open(template_path, 'rb') as f:
                template_content = f.read()

            filename = f'Plasma_Stability_Template_{datetime.now().strftime("%Y%m%d")}.xlsx'
            print(f"✓ Sending download: {filename}")
            print("="*80 + "\n")

            return {
                'content': template_content,
                'filename': filename,
                'type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            }

        except Exception as e:
            print(f"✗ Error in download_template: {str(e)}")
            import traceback
            traceback.print_exc()
            print("="*80 + "\n")
            raise

    @app.callback(
        [Output('template-data-store', 'data'),
         Output('upload-status', 'children')],
        Input('upload-template', 'contents'),
        State('upload-template', 'filename'),
        prevent_initial_call=True
    )
    def process_template(contents, filename):
        """Process uploaded template file"""
        print("\n" + "="*80)
        print("PROCESS TEMPLATE CALLBACK")
        print(f"Filename: {filename}")
        print("="*80)

        if contents is None:
            raise PreventUpdate

        try:
            # Decode uploaded file
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            print(f"✓ File decoded: {len(decoded)} bytes")

            # Read Excel file
            df = pd.read_excel(
                io.BytesIO(decoded),
                sheet_name='Sample Configuration',
                header=1
            )
            print(f"✓ Excel read: {df.shape}")
            print(f"  Columns: {list(df.columns)}")

            # Clean up the dataframe
            df = df.dropna(how='all')
            print(f"✓ After cleanup: {df.shape}")

            # Validate required columns
            required_cols = ['Instrument', 'Result ID', 'Molecule ID', 'Matrix', 'Day', 'Peak RT Type']
            missing_cols = [col for col in required_cols if col not in df.columns]

            if missing_cols:
                error_msg = f"Missing required columns: {', '.join(missing_cols)}"
                print(f"✗ {error_msg}")
                print("="*80 + "\n")
                return None, html.Div(
                    error_msg,
                    style={'color': '#dc2626', 'fontWeight': '600', 'padding': '12px',
                           'backgroundColor': '#fee2e2', 'borderRadius': '8px', 'marginTop': '12px'}
                )

            # Remove example rows (containing #)
            df = df[~df['Result ID'].astype(str).str.contains('#', na=False)]
            print(f"✓ After removing examples: {len(df)} rows")

            if len(df) == 0:
                error_msg = "No valid data found in template"
                print(f"✗ {error_msg}")
                print("="*80 + "\n")
                return None, html.Div(
                    error_msg,
                    style={'color': '#dc2626', 'fontWeight': '600', 'padding': '12px',
                           'backgroundColor': '#fee2e2', 'borderRadius': '8px', 'marginTop': '12px'}
                )

            # Convert to records
            template_data = df.to_dict('records')

            # Get summary info
            molecules = df['Molecule ID'].unique()
            print(f"✓ Found {len(molecules)} molecules: {list(molecules)}")

            # Summary by molecule
            for mol in molecules:
                mol_df = df[df['Molecule ID'] == mol]
                print(f"  {mol}: {len(mol_df)} samples, {len(mol_df['Matrix'].unique())} conditions")

            # Create success status with generate button
            status = html.Div([
                html.Div([
                    html.I(className='fas fa-check-circle', style={
                        'color': '#10b981', 'fontSize': '20px', 'marginRight': '8px'
                    }),
                    html.Span(
                        f"Template loaded successfully! Found {len(molecules)} molecule(s): {', '.join(molecules)}",
                        style={'color': '#10b981', 'fontWeight': '600'}
                    ),
                ], style={'marginTop': '12px'}),
                html.Div([
                    html.P(
                        f"Total samples: {len(template_data)}",
                        style={'color': '#6b7280', 'fontSize': '14px', 'margin': '8px 0'}
                    ),
                    html.Button(
                        "Generate Analysis",
                        id='generate-from-template-btn',
                        n_clicks=0,
                        style={
                            'backgroundColor': '#2563eb',
                            'color': 'white',
                            'border': 'none',
                            'padding': '14px 36px',
                            'fontSize': '16px',
                            'cursor': 'pointer',
                            'borderRadius': '10px',
                            'fontWeight': '700',
                            'marginTop': '16px',
                            'boxShadow': '0 4px 12px rgba(37, 99, 235, 0.4)',
                            'transition': 'all 0.2s'
                        }
                    )
                ])
            ])

            print("✓ Template processed successfully")
            print("="*80 + "\n")

            return template_data, status

        except Exception as e:
            error_msg = f"Error processing template: {str(e)}"
            print(f"✗ {error_msg}")
            import traceback
            traceback.print_exc()
            print("="*80 + "\n")

            return None, html.Div(
                error_msg,
                style={'color': '#dc2626', 'fontWeight': '600', 'padding': '12px',
                       'backgroundColor': '#fee2e2', 'borderRadius': '8px', 'marginTop': '12px'}
            )
