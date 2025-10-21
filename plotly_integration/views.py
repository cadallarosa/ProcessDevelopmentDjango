# views.py
from django.http import JsonResponse
from django.shortcuts import render
from datetime import datetime
import traceback
# from plotly_integration.process_development.downstream_processing.akta.opcua_server.read_historical_data import process_opcua_node_ids
#
# def trigger_opc_import(request):
#     try:
#         start_time = "2013-01-01T00:00:00"
#         end_time = datetime.now().isoformat()
#         process_opcua_node_ids(start_time, end_time)
#         return JsonResponse({"success": True, "message": "✅ OPC import completed."})
#     except Exception as e:
#         return JsonResponse({
#             "success": False,
#             "error": str(e),
#             "trace": traceback.format_exc()
#         }, status=500)


def pd_dashboard_view(request):
    """View to embed the PD Dashboard app"""
    return render(request, 'pd_dashboard.html')


def octet_analysis_view(request):
    """View for Octet Biolayer Interferometry Analysis App"""
    return render(request, 'plotly_integration/octet_analysis.html')


def octet_analysis_v2_view(request):
    """View for Octet Biolayer Interferometry Analysis App V2 (Modernized)"""
    return render(request, 'plotly_integration/octet_analysis_v2.html')


def octet_kinetics_view(request):
    """View for Octet Kinetics Dashboard"""
    return render(request, 'plotly_integration/octet_kinetics.html')
