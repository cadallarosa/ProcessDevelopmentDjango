# # cld_dashboard/samples/callbacks/analysis_requests.py
# import dash
# from dash import Input, Output, State, callback, no_update, ctx, html
# import dash_bootstrap_components as dbc
# from plotly_integration.models import LimsUpstreamSamples
# from datetime import datetime
#
#
# @callback(
#     Output("analysis-request-status", "children"),
#     [Input({"type": "request-sec-btn", "index": dash.dependencies.ALL}, "n_clicks")],
#     prevent_initial_call=True
# )
# def handle_sec_analysis_request(n_clicks_list):
#     """Handle SEC analysis requests from sample set cards"""
#     if not any(n_clicks_list):
#         return no_update
#
#     # Find which button was clicked
#     ctx_triggered = ctx.triggered[0]['prop_id'].split('.')[0]
#     sample_set_name = eval(ctx_triggered)['index']
#
#     try:
#         # Create analysis request logic here
#         # This would involve creating AnalysisRequest record
#
#         return dbc.Toast([
#             html.P(f"SEC analysis requested for {sample_set_name}", className="mb-0")
#         ],
#             header="Analysis Requested",
#             icon="success",
#             duration=4000,
#             is_open=True,
#             style={"position": "fixed", "top": 66, "right": 10, "width": 350})
#
#     except Exception as e:
#         return dbc.Toast([
#             html.P(f"Error requesting analysis: {str(e)}", className="mb-0")
#         ],
#             header="Request Failed",
#             icon="danger",
#             duration=4000,
#             is_open=True,
#             style={"position": "fixed", "top": 66, "right": 10, "width": 350})