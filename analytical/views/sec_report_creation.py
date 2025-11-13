"""
SEC Report Creation Views
Additional views for creating reports with group configuration
"""

from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.utils import timezone
import json
import time
import logging

from plotly_integration.models import Report, SampleMetadata
from analytical.models import EmpowerReport

logger = logging.getLogger(__name__)


@require_GET
def list_samples(request):
    """
    JSON API: List available SEC samples for report creation
    Returns JSON with sample data for Tabulator table
    """
    try:
        start_time = time.time()
        logger.info("list_samples() started")

        # Get optional prefix filter from query params
        prefix_filter = request.GET.get('prefix', None)

        # Query samples - don't filter by analysis_type as it's mostly null
        # Filter by sample_prefix instead (FD, FB, UP, UPFB, PD)
        query_start = time.time()
        queryset = SampleMetadata.objects.filter(sample_type=1).all()

        # Apply prefix filter if provided
        if prefix_filter and prefix_filter != 'ALL':
            if prefix_filter == 'UPFB':
                # UPFB samples have UP prefix but name starts with UPFB
                queryset = queryset.filter(sample_prefix='UP', sample_name__istartswith='UPFB')
            else:
                queryset = queryset.filter(sample_prefix=prefix_filter)

        samples = queryset.order_by("-date_acquired").values(
            "result_id",
            "sample_name",
            "sample_prefix",
            "system_name",
            "sample_set_name",
            "date_acquired"
        )[:500]  # Limit to 500 most recent
        query_end = time.time()
        logger.info(f"DB query completed ({int((query_end - query_start) * 1000)}ms)")

        # Format for Tabulator
        format_start = time.time()
        samples_list = []
        for sample in samples:
            date_str = None
            if sample["date_acquired"]:
                try:
                    date_str = sample["date_acquired"].isoformat()
                except:
                    date_str = str(sample["date_acquired"])

            samples_list.append({
                "result_id": sample["result_id"],
                "sample_name": sample["sample_name"] or f"Sample {sample['result_id']}",
                "sample_prefix": sample["sample_prefix"] or "N/A",
                "system_name": sample["system_name"] or "N/A",
                "sample_set_name": sample["sample_set_name"] or "N/A",
                "date_acquired": date_str
            })
        format_end = time.time()
        logger.info(f"Formatting completed ({int((format_end - format_start) * 1000)}ms, {len(samples_list)} samples)")

        total_time = (time.time() - start_time) * 1000
        logger.info(f"list_samples() TOTAL: {int(total_time)}ms")

        return JsonResponse({
            "samples": samples_list,
            "count": len(samples_list)
        })

    except Exception as e:
        logger.error(f"Error listing samples: {str(e)}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)


@require_POST
def create_report_api(request):
    """
    JSON API: Create a new SEC report using EmpowerReport model
    Expects: report_name, project_id, user_initials, sample_data
    sample_data format: [{"result_id": 123, "sample_name": "FB1429", "group": "Control"}]
    """
    try:
        start_time = time.time()
        logger.info("create_report_api() started")

        # Parse request data
        data = json.loads(request.body)

        report_name = data.get("report_name")
        project_id = data.get("project_id")
        user_initials = data.get("user_initials")
        sample_data = data.get("sample_data", [])

        # Validation
        if not report_name or not project_id or not user_initials:
            return JsonResponse({"error": "Missing required fields"}, status=400)

        if not sample_data or len(sample_data) == 0:
            return JsonResponse({"error": "No samples selected"}, status=400)

        # Create EmpowerReport
        report = EmpowerReport.objects.create(
            report_name=report_name,
            project_id=project_id,
            user_initials=user_initials,
            report_type='SEC',
            sample_data=sample_data
        )

        total_time = (time.time() - start_time) * 1000
        logger.info(f"create_report_api() TOTAL: {int(total_time)}ms, report_id={report.report_id}")

        return JsonResponse({
            "status": "success",
            "report_id": report.report_id,
            "message": "Report created successfully"
        })

    except Exception as e:
        logger.error(f"Error creating report: {str(e)}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)


@require_GET
def get_report(request, report_id):
    """
    JSON API: Get report details including sample data
    Returns report metadata and sample list
    """
    try:
        report = EmpowerReport.objects.get(report_id=report_id)

        return JsonResponse({
            "report_id": report.report_id,
            "report_name": report.report_name,
            "project_id": report.project_id,
            "user_initials": report.user_initials,
            "report_type": report.report_type,
            "date_created": report.date_created.isoformat() if report.date_created else None,
            "samples": report.sample_data or []
        })
    except EmpowerReport.DoesNotExist:
        return JsonResponse({"error": "Report not found"}, status=404)
    except Exception as e:
        logger.error(f"Error fetching report {report_id}: {str(e)}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)


@require_POST
def update_report_api(request, report_id):
    """
    JSON API: Update an existing SEC report
    Expects: report_name, project_id, user_initials, sample_data
    sample_data format: [{"result_id": 123, "sample_name": "FB1429", "group": "Control"}]
    """
    try:
        start_time = time.time()
        logger.info(f"update_report_api() started for report_id={report_id}")

        # Parse request data
        data = json.loads(request.body)

        report_name = data.get("report_name")
        project_id = data.get("project_id")
        user_initials = data.get("user_initials")
        sample_data = data.get("sample_data", [])

        # Validation
        if not report_name or not project_id or not user_initials:
            return JsonResponse({"error": "Missing required fields"}, status=400)

        if not sample_data or len(sample_data) == 0:
            return JsonResponse({"error": "No samples selected"}, status=400)

        # Get existing report
        try:
            report = EmpowerReport.objects.get(report_id=report_id)
        except EmpowerReport.DoesNotExist:
            return JsonResponse({"error": "Report not found"}, status=404)

        # Update report
        report.report_name = report_name
        report.project_id = project_id
        report.user_initials = user_initials
        report.sample_data = sample_data
        report.save()

        total_time = (time.time() - start_time) * 1000
        logger.info(f"update_report_api() TOTAL: {int(total_time)}ms, report_id={report.report_id}")

        return JsonResponse({
            "status": "success",
            "report_id": report.report_id,
            "message": "Report updated successfully"
        })

    except Exception as e:
        logger.error(f"Error updating report {report_id}: {str(e)}", exc_info=True)
        return JsonResponse({"error": str(e)}, status=500)


def create_report_page(request):
    """
    Render the report creation page
    """
    from dashboard.models import NavigationSection

    context = {
        "app_title": "Create SEC Report",
    }

    # Check if request is from HTMX (sidebar navigation)
    if request.headers.get("HX-Request"):
        # Return just the content (for dashboard navigation)
        return render(request, "analytical/sec/create_report_v2.html", context)
    else:
        # Return full page with sidebar (for direct access or bookmarks)
        context["navigation_sections"] = NavigationSection.objects.filter(is_active=True).prefetch_related("items")
        return render(request, "analytical/sec/create_report_v2.html", context)
