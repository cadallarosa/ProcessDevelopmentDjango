"""
Image Arrangement Views
Django views for the image arrangement app (HTMX version)
"""

from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods, require_POST, require_GET
import json

from development.utils.sample_data import SAMPLE_DATA_SINGLE_GROUP, SAMPLE_DATA_MULTI_GROUP, PHASE_OPTIONS
from development.utils.layout_helpers import validate_table_data, group_images_by_group_and_subset, calculate_stats, get_image_url


def index(request):
    """Main page for image arrangement app"""
    from dashboard.models import NavigationSection

    context = {
        'phase_options': PHASE_OPTIONS,
        'layout_modes': ['Comparison Mode', 'Simple Grid Mode'],
    }

    # Check if request is from HTMX (sidebar navigation)
    if request.headers.get('HX-Request'):
        # Return just the content (for dashboard navigation)
        return render(request, 'development/image_arrangement/content.html', context)
    else:
        # Return dashboard wrapper with sidebar (for direct access or bookmarks)
        # Add navigation data for sidebar
        context['navigation_sections'] = NavigationSection.objects.filter(is_active=True).prefetch_related('items')
        return render(request, 'development/image_arrangement/wrapper.html', context)


@require_POST
def add_row(request):
    """
    Add a new empty row to the table
    Returns HTML fragment for a new table row
    """
    # Get current row count from session to assign a unique ID
    table_data = request.session.get('table_data', [])
    row_id = len(table_data)

    # Create empty row
    new_row = {
        'id': row_id,
        'project_id': '',
        'phase': '',
        'group': '',
        'subset': '',
        'annotations': ''
    }

    # Add to session
    table_data.append(new_row)
    request.session['table_data'] = table_data

    # Return HTML fragment for the new row
    context = {
        'row': new_row,
        'row_index': row_id,
        'phase_options': PHASE_OPTIONS,
    }
    return render(request, 'development/image_arrangement/partials/table_row.html', context)


@require_POST
def load_sample(request):
    """
    Load single group sample data (9 molecules)
    Returns JSON for Tabulator.js or HTML for HTMX
    """
    # Store in session
    request.session['table_data'] = SAMPLE_DATA_SINGLE_GROUP
    request.session['layout_mode'] = 'comparison'

    # Check if request wants JSON (for Tabulator.js)
    if request.headers.get('Accept') == 'application/json' or request.content_type == 'application/json':
        return JsonResponse({
            'status': 'success',
            'table_data': SAMPLE_DATA_SINGLE_GROUP
        })

    # Return HTML fragment for HTMX
    context = {
        'rows': SAMPLE_DATA_SINGLE_GROUP,
        'phase_options': PHASE_OPTIONS,
    }
    return render(request, 'development/image_arrangement/partials/table_body.html', context)


@require_POST
def load_multi_group(request):
    """
    Load multi-group sample data (16 molecules, 4 groups)
    Returns JSON for Tabulator.js or HTML for HTMX
    """
    # Store in session
    request.session['table_data'] = SAMPLE_DATA_MULTI_GROUP
    request.session['layout_mode'] = 'comparison'

    # Check if request wants JSON (for Tabulator.js)
    if request.headers.get('Accept') == 'application/json' or request.content_type == 'application/json':
        return JsonResponse({
            'status': 'success',
            'table_data': SAMPLE_DATA_MULTI_GROUP
        })

    # Return HTML fragment for HTMX
    context = {
        'rows': SAMPLE_DATA_MULTI_GROUP,
        'phase_options': PHASE_OPTIONS,
    }
    return render(request, 'development/image_arrangement/partials/table_body.html', context)


@require_POST
def clear_all(request):
    """
    Clear all table data
    Returns empty table HTML
    """
    # Clear session
    request.session['table_data'] = []
    request.session['grouped_data'] = None

    # Return empty table
    context = {
        'rows': [],
        'phase_options': PHASE_OPTIONS,
    }
    return render(request, 'development/image_arrangement/partials/table_body.html', context)


@require_POST
def generate_layout(request):
    """
    Generate the image layout based on table data
    Returns HTML fragment with the layout

    This is the MAIN callback equivalent - replaces Dash's generate_image_layout callback
    """
    # Get table data from session
    table_data = request.session.get('table_data', [])
    layout_mode = request.session.get('layout_mode', 'comparison')
    control_title = request.session.get('control_title', 'Control')

    # Validate data
    is_valid, errors = validate_table_data(table_data)

    if not is_valid:
        # Return error message
        context = {'errors': errors}
        return render(request, 'development/image_arrangement/partials/error_alert.html', context)

    # Calculate stats
    stats = calculate_stats(table_data)

    # Generate layout based on mode
    if layout_mode == 'simple_grid':
        # Simple grid mode: 5-column grid
        context = {
            'molecules': table_data,
            'stats': stats,
        }
        template = 'development/image_arrangement/partials/simple_grid_layout.html'
    else:
        # Comparison mode: grouped layout
        grouped_data = group_images_by_group_and_subset(table_data)

        # Store grouped data for export
        request.session['grouped_data'] = grouped_data

        context = {
            'grouped_data': grouped_data,
            'control_title': control_title,
            'stats': stats,
        }
        template = 'development/image_arrangement/partials/comparison_layout.html'

    return render(request, template, context)


@require_GET
def preview_image(request, project_id):
    """
    Preview a single image in a modal
    Returns HTML fragment for modal content
    """
    # Get the image data from table
    table_data = request.session.get('table_data', [])

    # Find the matching row
    image_data = None
    for row in table_data:
        if row.get('project_id') == project_id:
            image_data = row
            break

    if not image_data:
        return HttpResponse('<p>Image not found</p>', status=404)

    # Add image URL
    image_data['image_url'] = get_image_url(project_id=project_id)

    context = {'image': image_data}
    return render(request, 'development/image_arrangement/modals/image_preview.html', context)


@require_POST
def export_ppt(request):
    """
    Export layout to PowerPoint
    Returns file download

    NOTE: PowerPoint export requires python-pptx library
    For now, this is a placeholder showing the pattern
    """
    from django.http import FileResponse
    from datetime import datetime
    import io

    # Get data from session
    table_data = request.session.get('table_data', [])
    grouped_data = request.session.get('grouped_data', {})
    layout_mode = request.session.get('layout_mode', 'comparison')

    # TODO: Implement actual PowerPoint generation
    # For now, return a simple response
    response_text = f"PowerPoint export would generate file with {len(table_data)} images\n"
    response_text += f"Layout mode: {layout_mode}\n"
    response_text += f"Groups: {len(grouped_data)}\n"

    # Create a simple text file as placeholder
    buffer = io.BytesIO()
    buffer.write(response_text.encode('utf-8'))
    buffer.seek(0)

    filename = f"image_arrangement_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

    response = FileResponse(buffer, as_attachment=True, filename=filename)
    response['Content-Type'] = 'text/plain'

    return response


def table_comparison(request):
    """
    Comparison page showing Plotly.js vs Tabulator.js tables
    """
    # Sample data for comparison (from the Dash app)
    sample_data = [
        {
            'project_id': 'SI-207X6',
            'phase': 'Sequence Design',
            'group': 'K-1 EGFR (Cetux.) Alternatives',
            'subset': 'K-1 (Cetux.)',
            'notes': 'Control - Original design',
        },
        {
            'project_id': 'SI-207X3',
            'phase': 'Sequence Design',
            'group': 'K-1 EGFR (Cetux.) Alternatives',
            'subset': 'Cetux, scFv H-L',
            'notes': 'Modified CDR1',
        },
        {
            'project_id': 'SI-207X4',
            'phase': 'Sequence Design',
            'group': 'K-1 EGFR (Cetux.) Alternatives',
            'subset': 'Cetux, scFv H-L',
            'notes': 'Modified CDR2',
        },
        {
            'project_id': 'SI-207X5',
            'phase': 'Sequence Design',
            'group': 'K-1 EGFR (Cetux.) Alternatives',
            'subset': 'Cetux, scFv H-L',
            'notes': 'Vector control',
        },
        {
            'project_id': 'SI-207X10',
            'phase': 'Sequence Design',
            'group': 'K-1 EGFR (Cetux.) Alternatives',
            'subset': 'Cetux, scFv L-H',
            'notes': 'Optimized expression',
        },
    ]
    
    context = {
        'sample_data': sample_data,
        'phase_options': PHASE_OPTIONS,
    }
    return render(request, 'development/table_comparison.html', context)


@require_POST
def save_table(request):
    """
    Save table data to session from Tabulator.js
    Receives JSON with table_data, layout_mode, control_title
    Returns JSON confirmation
    """
    try:
        data = json.loads(request.body)

        # Save to session
        request.session['table_data'] = data.get('table_data', [])
        request.session['layout_mode'] = data.get('layout_mode', 'comparison')
        request.session['control_title'] = data.get('control_title', 'Control')

        return JsonResponse({
            'status': 'success',
            'saved_rows': len(data.get('table_data', []))
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)
