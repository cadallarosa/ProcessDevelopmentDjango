"""
Layout Helper Functions
Utility functions for processing table data and generating image layouts
"""

from collections import defaultdict
from typing import List, Dict, Tuple
import os
import random
import requests
from functools import lru_cache


@lru_cache(maxsize=1)
def _check_server_accessible() -> bool:
    """Check if the image server is accessible (cached for performance)"""
    try:
        response = requests.head("http://fs2.systimmune.net/", timeout=5)
        return response.status_code < 400
    except:
        return False


def get_local_image_path(molecule_id: str = None, project_id: str = None) -> str:
    """Get a local image path for testing purposes"""
    local_dir = r"C:\Users\Chris\PycharmProjects\PythonProject5\project_images"

    # Available local images
    local_images = [
        "milstein-antibodies-m3.png",
        "download.png",
        "test3.png"
    ]

    # Use a deterministic selection based on the ID to ensure consistency
    img_id = molecule_id if molecule_id else project_id
    if img_id:
        # Use hash of ID to select image consistently
        index = hash(img_id) % len(local_images)
        selected_image = local_images[index]
    else:
        # Default to first image
        selected_image = local_images[0]

    # Return file:// URL for local image
    local_path = os.path.join(local_dir, selected_image)
    return f"file:///{local_path.replace(os.sep, '/')}"


def get_image_url(molecule_id: str = None, project_id: str = None, use_local: bool = None) -> str:
    """
    Generate the image URL for a given molecule ID or project ID
    With intelligent fallback to local images for testing

    Args:
        molecule_id: The molecule identifier (optional, will use project_id if not provided)
        project_id: The project identifier (used as fallback for molecule_id)
        use_local: Force use of local images (if None, auto-detects server availability)

    Returns:
        str: The full URL to the image or path to local image
    """
    # Check if we should force local images
    force_local = os.getenv('USE_LOCAL_IMAGES', 'false').lower() == 'true'

    if use_local is True or force_local:
        return get_local_image_path(molecule_id, project_id)

    # If use_local is False, try server first
    if use_local is False:
        img_id = molecule_id if molecule_id else project_id
        server_url = f"http://fs2.systimmune.net/imgs/{img_id}.png"

        # Check if server is available
        if _check_server_accessible():
            return server_url
        else:
            print(f"Server not available, falling back to local image for {img_id}")
            return get_local_image_path(molecule_id, project_id)

    # Default behavior: Try server first, fallback to local
    img_id = molecule_id if molecule_id else project_id
    server_url = f"http://fs2.systimmune.net/imgs/{img_id}.png"

    # Check if server is available
    if _check_server_accessible():
        return server_url
    else:
        print(f"Server not available, using local image for {img_id}")
        return get_local_image_path(molecule_id, project_id)


def validate_table_data(data: List[Dict]) -> Tuple[bool, List[str]]:
    """
    Validate the configuration table data

    Args:
        data: List of row dictionaries from the DataTable

    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []

    if not data or len(data) == 0:
        errors.append("No data rows configured")
        return False, errors

    for idx, row in enumerate(data):
        row_num = idx + 1

        # Check required fields
        if not row.get('project_id'):
            errors.append(f"Row {row_num}: Project ID is required")

        if not row.get('phase'):
            errors.append(f"Row {row_num}: Phase is required")

        if not row.get('group'):
            errors.append(f"Row {row_num}: Group is required")

        if not row.get('subset'):
            errors.append(f"Row {row_num}: Subset is required")

    is_valid = len(errors) == 0
    return is_valid, errors


def group_images_by_group_and_subset(data: List[Dict]) -> Dict:
    """
    Group image data by group and subset

    Args:
        data: List of row dictionaries from the DataTable

    Returns:
        Dict: Nested dictionary organized by group and subset
        Structure: {group: {subset: [image_data_list]}}
    """
    grouped = defaultdict(lambda: defaultdict(list))

    for row in data:
        group = row.get('group', 'Ungrouped')
        subset = row.get('subset', 'Default')

        # Add image URL to the row data
        row_with_url = row.copy()
        row_with_url['image_url'] = get_image_url(
            molecule_id=row.get('molecule_id'),
            project_id=row.get('project_id')
        )

        grouped[group][subset].append(row_with_url)

    return dict(grouped)


def calculate_stats(data: List[Dict]) -> Dict:
    """
    Calculate statistics about the configuration

    Args:
        data: List of row dictionaries from the DataTable

    Returns:
        Dict: Statistics dictionary
    """
    if not data:
        return {
            'total_images': 0,
            'total_groups': 0,
            'total_phases': 0,
            'total_projects': 0,
            'groups': [],
            'phases': [],
            'projects': []
        }

    groups = set()
    phases = set()
    projects = set()

    for row in data:
        if row.get('group'):
            groups.add(row['group'])
        if row.get('phase'):
            phases.add(row['phase'])
        if row.get('project_id'):
            projects.add(row['project_id'])

    return {
        'total_images': len(data),
        'total_groups': len(groups),
        'total_phases': len(phases),
        'total_projects': len(projects),
        'groups': sorted(list(groups)),
        'phases': sorted(list(phases)),
        'projects': sorted(list(projects))
    }


def get_phase_color(phase: str) -> str:
    """
    Get a consistent color for each phase

    Args:
        phase: Phase name

    Returns:
        str: Bootstrap color name
    """
    phase_colors = {
        'Sequence Design': 'primary',
        'Plasmid Design': 'success',
        'Transfection Purification': 'warning',
        'UCOE Clone': 'info',
        'CLD Development': 'danger'
    }
    return phase_colors.get(phase, 'secondary')
