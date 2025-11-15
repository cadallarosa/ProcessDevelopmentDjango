"""
SEC (Size Exclusion Chromatography) Views
Django views for SEC visualization app (HTMX + Plotly.js)
"""

from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
import json
import logging
import time

from ..utils.sec_plotting import (
    analyze_samples,
    create_sec_plot,
    fetch_sample_metadata,
    fetch_time_series_data
)
from plotly_integration.models import Report, SampleMetadata
from analytical.models import EmpowerReport


logger = logging.getLogger(__name__)


def index(request):
    """Main SEC app page"""
    from dashboard.models import NavigationSection

    # Get report_id from query parameter
    report_id = request.GET.get('report_id', None)

    context = {
        'app_title': 'SEC Chromatography Visualization',
        'initial_report_id': report_id  # Pass report_id to template
    }

    # Check if request is from HTMX (sidebar navigation)
    if request.headers.get('HX-Request'):
        # Return just the content (for dashboard navigation)
        return render(request, 'analytical/sec/content.html', context)
    else:
        # Return dashboard wrapper with sidebar (for direct access or bookmarks)
        # Add navigation data for sidebar
        context['navigation_sections'] = NavigationSection.objects.filter(is_active=True).prefetch_related('items')
        return render(request, 'analytical/sec/wrapper.html', context)


@require_POST
def update_plot(request):
    """
    HTMX endpoint: Update SEC plot based on user settings
    Returns HTML fragment with Plotly.js chart
    """
    try:
        # Get form data
        report_id = request.POST.get('report_id')

        if not report_id:
            return render(request, 'analytical/sec/partials/error.html', {
                'error_message': 'No report ID provided'
            })

        # Get plot settings
        show_uv280 = request.POST.get('channel_uv280') == '1'
        show_uv260 = request.POST.get('channel_uv260') == '1'
        show_pressure = request.POST.get('channel_pressure') == '1'

        # Peak detection settings
        peak_mode = request.POST.get('peak_mode', 'rt')
        main_peak_rt = float(request.POST.get('main_peak_rt', 10.5))
        low_mw_cutoff = float(request.POST.get('low_mw_cutoff', 12))
        use_std_curve = request.POST.get('use_std_curve') == '1'

        # Load report
        report = Report.objects.filter(report_id=report_id).first()
        if not report:
            return render(request, 'analytical/sec/partials/error.html', {
                'error_message': f'Report {report_id} not found'
            })

        # Parse result IDs
        result_ids = [rid.strip() for rid in report.selected_result_ids.split(',') if rid.strip()]

        if not result_ids:
            return render(request, 'analytical/sec/partials/error.html', {
                'error_message': 'No samples found in report'
            })

        # Limit to first 10 samples for performance
        result_ids = result_ids[:10]

        # Analyze samples
        logger.info(f"Analyzing {len(result_ids)} samples: {result_ids}")
        analysis_data = analyze_samples(
            result_ids=result_ids,
            peak_mode=peak_mode,
            main_peak_rt=main_peak_rt,
            low_mw_cutoff=low_mw_cutoff,
            use_std_curve=use_std_curve
        )

        # Log data fetching results
        logger.info(f"Time series fetched: {len(analysis_data['time_series'])} samples")
        for rid, df in analysis_data['time_series'].items():
            logger.info(f"  Sample {rid}: {len(df)} data points")
        logger.info(f"Metadata fetched: {len(analysis_data['metadata'])} samples")
        logger.info(f"Analysis results: {len(analysis_data['analysis_results'])} samples")

        # Create plot
        plot_json = create_sec_plot(
            time_series_dict=analysis_data['time_series'],
            metadata_dict=analysis_data['metadata'],
            analysis_results=analysis_data['analysis_results'],
            show_uv280=show_uv280,
            show_uv260=show_uv260,
            show_pressure=show_pressure
        )

        # Render template
        context = {
            'plot_json': plot_json,
            'analysis_results': analysis_data['analysis_results'],
            'sample_count': len(result_ids)
        }

        return render(request, 'analytical/sec/partials/plot_area.html', context)

    except Exception as e:
        logger.error(f"Error updating plot: {str(e)}", exc_info=True)
        return render(request, 'analytical/sec/partials/error.html', {
            'error_message': f'Error: {str(e)}'
        })


@require_POST
def load_report(request):
    """
    HTMX endpoint: Load report and display samples
    Returns HTML fragment with report info
    """
    try:
        report_id = request.POST.get('report_id')

        if not report_id:
            return render(request, 'analytical/sec/partials/report_info.html', {
                'error': 'Please enter a report ID'
            })

        # Load report
        report = Report.objects.filter(report_id=report_id).first()

        if not report:
            return render(request, 'analytical/sec/partials/report_info.html', {
                'error': f'Report {report_id} not found in database'
            })

        # Parse result IDs
        result_ids = [rid.strip() for rid in report.selected_result_ids.split(',') if rid.strip()]

        if not result_ids:
            return render(request, 'analytical/sec/partials/report_info.html', {
                'error': 'No samples found in this report'
            })

        # Fetch sample metadata
        metadata_dict = fetch_sample_metadata(result_ids[:10])  # Limit to 10 for display

        # Convert to list for template
        samples = [
            {'sample_name': meta.get('sample_name', f'Sample {rid}')}
            for rid, meta in metadata_dict.items()
        ]

        context = {
            'report': report,
            'sample_count': len(result_ids),
            'samples': samples
        }

        return render(request, 'analytical/sec/partials/report_info.html', context)

    except Exception as e:
        logger.error(f"Error loading report: {str(e)}", exc_info=True)
        return render(request, 'analytical/sec/partials/report_info.html', {
            'error': f'Error: {str(e)}'
        })


# ============================================================================
# JSON API Endpoints for Tiered Loading
# ============================================================================

@require_POST
def load_initial_data(request, report_id):
    """
    JSON API: Load initial UV280 data with metadata
    Returns JSON with UV280 traces, layout, and metadata
    """
    try:
        start_time = time.time()
        print(f"\n{'='*80}")
        print(f"⏱️ [0ms] load_initial_data({report_id}) started")

        # Parse settings from JSON body
        parse_start = time.time()
        data = json.loads(request.body)
        peak_mode = data.get('peakMode', 'rt')
        main_peak_rt = float(data.get('mainPeakRt', 10.5))
        low_mw_cutoff = float(data.get('lowMwCutoff', 12))
        use_std_curve = data.get('useStdCurve', False)
        show_shading = data.get('showShading', True)
        batch_size = int(data.get('batchSize', 20))  # Number of samples to load at once
        batch_offset = int(data.get('batchOffset', 0))  # Starting index for batch
        parse_end = time.time()
        print(f"⏱️ [{int((parse_end - start_time) * 1000)}ms] Settings parsed ({int((parse_end - parse_start) * 1000)}ms)")

        # Load report (try EmpowerReport first, fallback to old Report)
        db_start = time.time()
        report = EmpowerReport.objects.filter(report_id=report_id, report_type='SEC').first()
        if not report:
            # Fallback to old Report model for backward compatibility
            old_report = Report.objects.filter(report_id=report_id).first()
            if not old_report:
                return JsonResponse({'error': f'Report {report_id} not found'}, status=404)
            # Parse old format
            result_ids = [rid.strip() for rid in old_report.selected_result_ids.split(',') if rid.strip()]
            sample_data = old_report.group_configuration if hasattr(old_report, 'group_configuration') else None
        else:
            # New EmpowerReport format
            result_ids = report.get_result_ids()
            sample_data = report.sample_data

        if not result_ids:
            return JsonResponse({'error': 'No samples found in report'}, status=404)

        # Get total count before batching
        total_samples = len(result_ids)

        # Apply batching for lazy loading
        end_index = min(batch_offset + batch_size, total_samples)
        result_ids_batch = result_ids[batch_offset:end_index]

        db_end = time.time()
        print(f"⏱️ [{int((db_end - start_time) * 1000)}ms] Report loaded, result_ids parsed ({int((db_end - db_start) * 1000)}ms, batch {batch_offset}-{end_index} of {total_samples} samples)")

        # Analyze samples
        from ..utils.sec_plotting import (
            analyze_samples, create_channel_traces, create_plot_layout
        )

        analyze_start = time.time()
        analysis_data = analyze_samples(
            result_ids=result_ids_batch,
            peak_mode=peak_mode,
            main_peak_rt=main_peak_rt,
            low_mw_cutoff=low_mw_cutoff,
            use_std_curve=use_std_curve
        )
        analyze_end = time.time()
        print(f"⏱️ [{int((analyze_end - start_time) * 1000)}ms] analyze_samples() completed ({int((analyze_end - analyze_start) * 1000)}ms) ⚠️ THIS IS THE CRITICAL PATH")

        # Create UV280 traces only
        traces_start = time.time()
        uv280_traces = create_channel_traces(
            time_series_dict=analysis_data['time_series'],
            metadata_dict=analysis_data['metadata'],
            channel='uv280',
            analysis_results=analysis_data['analysis_results']
        )
        traces_end = time.time()
        print(f"⏱️ [{int((traces_end - start_time) * 1000)}ms] UV280 traces created ({int((traces_end - traces_start) * 1000)}ms, {len(uv280_traces)} traces)")

        # Create layout
        layout_start = time.time()
        layout = create_plot_layout(
            show_shading=show_shading,
            analysis_results=analysis_data['analysis_results'],
            time_series_dict=analysis_data['time_series']
        )
        layout_end = time.time()
        print(f"⏱️ [{int((layout_end - start_time) * 1000)}ms] Layout created ({int((layout_end - layout_start) * 1000)}ms)")

        # Return JSON response
        json_start = time.time()
        response = JsonResponse({
            'uv280_traces': uv280_traces,
            'layout': layout,
            'metadata': {
                'report_id': report_id,
                'sample_count': len(result_ids_batch),
                'total_samples': total_samples,
                'batch_offset': batch_offset,
                'batch_size': len(result_ids_batch),
                'has_more': end_index < total_samples,
                'result_ids': result_ids_batch,
                'group_configuration': sample_data  # sample_data from EmpowerReport or old group_configuration
            }
        })
        json_end = time.time()

        total_time = (json_end - start_time) * 1000
        print(f"✅ load_initial_data() TOTAL: {int(total_time)}ms (parse: {int((parse_end - parse_start) * 1000)}ms, db: {int((db_end - db_start) * 1000)}ms, analyze: {int((analyze_end - analyze_start) * 1000)}ms, traces: {int((traces_end - traces_start) * 1000)}ms, layout: {int((layout_end - layout_start) * 1000)}ms, json: {int((json_end - json_start) * 1000)}ms)")
        print(f"{'='*80}\n")

        return response

    except Exception as e:
        logger.error(f"Error loading initial data: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
def load_channel_data(request, report_id, channel):
    """
    JSON API: Load specific channel data
    Returns JSON with traces for the requested channel
    OPTIMIZED: Only fetches time series data, doesn't re-run analysis
    """
    try:
        start_time = time.time()
        print(f"\n{'='*80}")
        print(f"⏱️ [0ms] load_channel_data({report_id}, {channel}) started")

        # Validate channel
        if channel not in ['uv260', 'pressure']:
            return JsonResponse({'error': 'Invalid channel'}, status=400)

        # Load report (try EmpowerReport first, fallback to old Report)
        db_start = time.time()
        report = EmpowerReport.objects.filter(report_id=report_id, report_type='SEC').first()
        if report:
            # New EmpowerReport format
            result_ids = report.get_result_ids()
        else:
            # Fallback to old Report model for backward compatibility
            old_report = Report.objects.filter(report_id=report_id).first()
            if not old_report:
                return JsonResponse({'error': f'Report {report_id} not found'}, status=404)
            # Parse old format
            result_ids = [rid.strip() for rid in old_report.selected_result_ids.split(',') if rid.strip()]

        if not result_ids:
            return JsonResponse({'error': 'No samples found in report'}, status=404)

        # No longer limiting - load all samples for background channels
        db_end = time.time()
        print(f"⏱️ [{int((db_end - start_time) * 1000)}ms] Report loaded ({int((db_end - db_start) * 1000)}ms, {len(result_ids)} samples)")

        # OPTIMIZED: Only fetch what we need (time series + metadata), no analysis
        from ..utils.sec_plotting import (
            fetch_time_series_data, fetch_sample_metadata, create_channel_traces
        )

        ts_start = time.time()
        time_series_dict = fetch_time_series_data(result_ids)
        ts_end = time.time()
        print(f"⏱️ [{int((ts_end - start_time) * 1000)}ms] fetch_time_series_data() took {int((ts_end - ts_start) * 1000)}ms")

        meta_start = time.time()
        metadata_dict = fetch_sample_metadata(result_ids)
        meta_end = time.time()
        print(f"⏱️ [{int((meta_end - start_time) * 1000)}ms] fetch_sample_metadata() took {int((meta_end - meta_start) * 1000)}ms")

        # Create channel traces (no analysis_results needed for UV260/pressure)
        traces_start = time.time()
        traces = create_channel_traces(
            time_series_dict=time_series_dict,
            metadata_dict=metadata_dict,
            channel=channel,
            analysis_results=None  # Not needed for background channels
        )
        traces_end = time.time()
        print(f"⏱️ [{int((traces_end - start_time) * 1000)}ms] create_channel_traces() took {int((traces_end - traces_start) * 1000)}ms, {len(traces)} traces")

        total_time = (time.time() - start_time) * 1000
        print(f"✅ load_channel_data() TOTAL: {int(total_time)}ms (OPTIMIZED - no analysis re-run)")
        print(f"{'='*80}\n")

        return JsonResponse({
            'traces': traces,
            'channel': channel
        })

    except Exception as e:
        logger.error(f"Error loading channel data: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
def load_results_table(request, report_id):
    """
    JSON API: Load results table data
    Returns JSON with formatted analysis results
    """
    try:
        # Parse settings from JSON body
        data = json.loads(request.body)
        peak_mode = data.get('peakMode', 'rt')
        main_peak_rt = float(data.get('mainPeakRt', 10.5))
        low_mw_cutoff = float(data.get('lowMwCutoff', 12))
        use_std_curve = data.get('useStdCurve', False)

        # Load report (try EmpowerReport first, fallback to old Report)
        report = EmpowerReport.objects.filter(report_id=report_id, report_type='SEC').first()
        if report:
            # New EmpowerReport format
            result_ids = report.get_result_ids()
        else:
            # Fallback to old Report model for backward compatibility
            old_report = Report.objects.filter(report_id=report_id).first()
            if not old_report:
                return JsonResponse({'error': f'Report {report_id} not found'}, status=404)
            # Parse old format
            result_ids = [rid.strip() for rid in old_report.selected_result_ids.split(',') if rid.strip()]

        if not result_ids:
            return JsonResponse({'error': 'No samples found in report'}, status=404)

        # No longer limiting - load all samples for results table

        # Analyze samples
        from ..utils.sec_plotting import (
            analyze_samples, format_results_for_table
        )

        analysis_data = analyze_samples(
            result_ids=result_ids,
            peak_mode=peak_mode,
            main_peak_rt=main_peak_rt,
            low_mw_cutoff=low_mw_cutoff,
            use_std_curve=use_std_curve
        )

        # Format for table
        table_data = format_results_for_table(
            analysis_results=analysis_data['analysis_results'],
            metadata_dict=analysis_data['metadata']
        )

        return JsonResponse(table_data)

    except Exception as e:
        logger.error(f"Error loading results table: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
def load_std_analysis(request, report_id):
    """
    JSON API: Load standard curve analysis data
    Returns JSON with standard curve plot and regression info
    """
    try:
        # For now, return placeholder indicating STD analysis not available
        # This can be implemented later when standard curve data is available

        return JsonResponse({
            'available': False,
            'message': 'Standard curve analysis not implemented yet'
        })

    except Exception as e:
        logger.error(f"Error loading STD analysis: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
def save_settings(request):
    """
    JSON API: Save current settings to session
    """
    try:
        data = json.loads(request.body)

        # Save to session
        request.session['sec_settings'] = {
            'peakMode': data.get('peakMode', 'rt'),
            'mainPeakRt': data.get('mainPeakRt', 10.5),
            'lowMwCutoff': data.get('lowMwCutoff', 12),
            'useStdCurve': data.get('useStdCurve', False),
            'showShading': data.get('showShading', True)
        }

        return JsonResponse({'status': 'success', 'message': 'Settings saved'})

    except Exception as e:
        logger.error(f"Error saving settings: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
def export_excel(request, report_id):
    """
    JSON API: Export results to Excel
    """
    try:
        import io
        from openpyxl import Workbook
        from openpyxl.styles import Font, PatternFill

        # Parse settings
        data = json.loads(request.body)
        peak_mode = data.get('peakMode', 'rt')
        main_peak_rt = float(data.get('mainPeakRt', 10.5))
        low_mw_cutoff = float(data.get('lowMwCutoff', 12))

        # Load and analyze data
        report = Report.objects.filter(report_id=report_id).first()
        if not report:
            return JsonResponse({'error': 'Report not found'}, status=404)

        result_ids = [rid.strip() for rid in report.selected_result_ids.split(',') if rid.strip()][:10]

        from ..utils.sec_plotting import analyze_samples, format_results_for_table

        analysis_data = analyze_samples(
            result_ids=result_ids,
            peak_mode=peak_mode,
            main_peak_rt=main_peak_rt,
            low_mw_cutoff=low_mw_cutoff
        )

        table_data = format_results_for_table(
            analysis_results=analysis_data['analysis_results'],
            metadata_dict=analysis_data['metadata']
        )

        # Create Excel workbook
        wb = Workbook()
        ws = wb.active
        ws.title = "SEC Results"

        # Header row
        headers = ['Sample Name', 'Sample Set', 'HMW (%)', 'Main (%)', 'LMW (%)', 'Main Peak RT (min)']
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill(start_color="0056B3", end_color="0056B3", fill_type="solid")

        # Data rows
        for row_idx, result in enumerate(table_data['results'], start=2):
            ws.cell(row=row_idx, column=1, value=result['sample_name'])
            ws.cell(row=row_idx, column=2, value=result['sample_set_name'])
            ws.cell(row=row_idx, column=3, value=result['hmw_percent'])
            ws.cell(row=row_idx, column=4, value=result['main_percent'])
            ws.cell(row=row_idx, column=5, value=result['lmw_percent'])
            ws.cell(row=row_idx, column=6, value=result['main_peak_rt'])

        # Auto-adjust column widths
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(cell.value)
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width

        # Save to bytes
        excel_file = io.BytesIO()
        wb.save(excel_file)
        excel_file.seek(0)

        # Return as file download
        response = HttpResponse(
            excel_file.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = f'attachment; filename=sec_results_{report_id}.xlsx'
        return response

    except Exception as e:
        logger.error(f"Error exporting to Excel: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
def export_ppt(request, report_id):
    """
    JSON API: Export results to PowerPoint
    """
    try:
        # Placeholder - PPT export can be implemented later
        return JsonResponse({
            'error': 'PowerPoint export not implemented yet'
        }, status=501)

    except Exception as e:
        logger.error(f"Error exporting to PPT: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


@require_GET
def list_reports(request):
    """
    JSON API: List all SEC reports for selection
    Returns JSON with report data for Tabulator table
    """
    try:
        start_time = time.time()
        logger.info("⏱️ [0ms] list_reports() started")

        # Query reports from EmpowerReport (SEC type only)
        query_start = time.time()
        reports = EmpowerReport.objects.filter(
            report_type='SEC'
        ).order_by('-created_at').values(
            'report_id',
            'report_name',
            'project_id',
            'user_initials',
            'created_at'
        )[:100]  # Limit to 100 most recent
        query_end = time.time()
        logger.info(f"⏱️ [{int((query_end - start_time) * 1000)}ms] DB query completed ({int((query_end - query_start) * 1000)}ms)")

        # Format for Tabulator
        format_start = time.time()
        reports_list = []
        for report in reports:
            date_str = None
            if report['created_at']:
                try:
                    date_str = report['created_at'].isoformat()
                except:
                    date_str = str(report['created_at'])

            reports_list.append({
                'report_id': report['report_id'],
                'report_name': report['report_name'],
                'project_id': report['project_id'],
                'user_id': report['user_initials'] or 'N/A',
                'date_created': date_str
            })
        format_end = time.time()
        logger.info(f"⏱️ [{int((format_end - start_time) * 1000)}ms] Formatting completed ({int((format_end - format_start) * 1000)}ms, {len(reports_list)} reports)")

        json_start = time.time()
        response = JsonResponse({
            'reports': reports_list,
            'count': len(reports_list)
        })
        json_end = time.time()

        total_time = (json_end - start_time) * 1000
        logger.info(f"✅ list_reports() TOTAL: {int(total_time)}ms (query: {int((query_end - query_start) * 1000)}ms, format: {int((format_end - format_start) * 1000)}ms, json: {int((json_end - json_start) * 1000)}ms)")

        return response

    except Exception as e:
        logger.error(f"Error listing reports: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)


@require_POST
def get_chromatograms(request):
    """
    JSON API: Fetch UV280 chromatogram data for preview modal

    Accepts:
        POST body: {"result_ids": [123, 456, 789]}

    Returns:
        JSON: {
            "traces": [
                {
                    "x": [time values],
                    "y": [UV280 values],
                    "name": "Sample Name",
                    "type": "scatter",
                    "mode": "lines"
                }
            ]
        }
    """
    try:
        # Parse request body
        body = json.loads(request.body)
        result_ids = body.get('result_ids', [])

        if not result_ids:
            return JsonResponse({'error': 'No result_ids provided'}, status=400)

        logger.info(f"Fetching chromatograms for {len(result_ids)} samples: {result_ids}")

        # Fetch time series data (UV280 is channel_1)
        time_series_data = fetch_time_series_data(result_ids)

        # Fetch sample metadata for names
        metadata = fetch_sample_metadata(result_ids)

        # Build Plotly traces
        traces = []
        for result_id in result_ids:
            # Get time series dataframe
            df = time_series_data.get(result_id)
            if df is None or df.empty:
                logger.warning(f"No time series data found for result_id {result_id}")
                continue

            # Get sample metadata
            meta = metadata.get(result_id, {})
            sample_name = meta.get('sample_name', f'Result {result_id}')

            # Create trace for UV280 (channel_1)
            trace = {
                'x': df['time'].tolist(),
                'y': df['channel_1'].tolist(),  # UV280 is channel_1
                'name': sample_name,
                'type': 'scatter',
                'mode': 'lines',
                'hovertemplate': f'<b>{sample_name}</b><br>Time: %{{x:.2f}} min<br>UV280: %{{y:.2f}} mAU<extra></extra>'
            }
            traces.append(trace)

        logger.info(f"Successfully created {len(traces)} chromatogram traces")

        return JsonResponse({
            'traces': traces,
            'count': len(traces)
        })

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in request body: {str(e)}")
        return JsonResponse({'error': 'Invalid JSON in request body'}, status=400)

    except Exception as e:
        logger.error(f"Error fetching chromatograms: {str(e)}", exc_info=True)
        return JsonResponse({'error': str(e)}, status=500)
