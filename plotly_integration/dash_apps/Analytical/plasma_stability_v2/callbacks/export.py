"""
Export Callbacks
Handle PowerPoint export functionality
"""

import base64
from dash import Input, Output, State, no_update
from dash.exceptions import PreventUpdate
from datetime import datetime

from ..utils.ppt_export import create_powerpoint


def register_export_callbacks(app):
    """Register PowerPoint export callbacks"""

    @app.callback(
        Output('download-ppt', 'data'),
        Input('export-ppt-btn', 'n_clicks'),
        [State('template-data-store', 'data'),
         State('analysis-results-store', 'data')],
        prevent_initial_call=True
    )
    def export_to_powerpoint(n_clicks, template_data, analysis_data):
        """
        Export analysis to PowerPoint

        Args:
            n_clicks: Button clicks
            template_data: Original template data
            analysis_data: Analysis results and settings

        Returns:
            Download dict for PowerPoint file
        """
        print("\n" + "="*80)
        print("EXPORT TO POWERPOINT CALLBACK")
        print("="*80)

        if not template_data or not analysis_data:
            print("✗ No data available for export")
            print("="*80 + "\n")
            raise PreventUpdate

        try:
            print(f"✓ Exporting {len(analysis_data.get('molecules', []))} molecules")

            # Generate PowerPoint
            ppt_bytes = create_powerpoint(template_data, analysis_data)

            # Create filename with timestamp
            filename = f'Plasma_Stability_Report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pptx'
            print(f"✓ PowerPoint generated: {filename}")
            print(f"  File size: {len(ppt_bytes)} bytes")
            print("="*80 + "\n")

            return {
                'content': base64.b64encode(ppt_bytes).decode(),
                'filename': filename,
                'base64': True,
                'type': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
            }

        except Exception as e:
            error_msg = f"Error exporting PowerPoint: {str(e)}"
            print(f"✗ {error_msg}")
            import traceback
            traceback.print_exc()
            print("="*80 + "\n")
            raise
