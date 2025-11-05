"""
Molecule Image Helper
Handles fetching molecule structure images
"""

import os
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


def get_local_image_path(molecule_id: str) -> str:
    """
    Get a local fallback image path

    Args:
        molecule_id: The molecule identifier

    Returns:
        str: Path to local placeholder image
    """
    # Use a placeholder image in the template folder
    template_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'template'
    )
    placeholder = os.path.join(template_dir, 'img.png')

    if os.path.exists(placeholder):
        return f"file:///{placeholder.replace(os.sep, '/')}"

    # Return a data URL placeholder if file doesn't exist
    return "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='200' height='200'%3E%3Crect width='200' height='200' fill='%23f3f4f6'/%3E%3Ctext x='50%25' y='50%25' text-anchor='middle' dy='.3em' fill='%239ca3af' font-family='Arial' font-size='14'%3ENo Image%3C/text%3E%3C/svg%3E"


def get_molecule_image_url(molecule_id: str, use_local: bool = None) -> str:
    """
    Generate the image URL for a given molecule ID
    With intelligent fallback to local images

    Args:
        molecule_id: The molecule identifier
        use_local: Force use of local images (if None, auto-detects server availability)

    Returns:
        str: The full URL to the molecule image
    """
    if not molecule_id:
        return get_local_image_path("unknown")

    # Check if we should force local images
    force_local = os.getenv('USE_LOCAL_IMAGES', 'false').lower() == 'true'

    if use_local is True or force_local:
        return get_local_image_path(molecule_id)

    # Try server first
    server_url = f"http://fs2.systimmune.net/imgs/{molecule_id}.png"

    # Check if server is available
    if _check_server_accessible():
        return server_url
    else:
        print(f"Server not available, using local image for {molecule_id}")
        return get_local_image_path(molecule_id)
