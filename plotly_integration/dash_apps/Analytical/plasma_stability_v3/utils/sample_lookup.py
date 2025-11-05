"""
Sample ID Lookup Utilities

This module provides functions to look up Result IDs from Sample IDs and validate
Sample ID / Result ID pairs against the database.
"""

from plotly_integration.models import SampleMetadata
from django.db.models import Q


def lookup_result_ids_by_sample_id(sample_id):
    """
    Look up all Result IDs associated with a given Sample ID.

    Args:
        sample_id (str): Sample ID to search for (e.g., 'FD-009-068')

    Returns:
        list: List of dictionaries containing:
            - result_id: The result ID
            - date_acquired: Date the sample was acquired
            - acquired_by: Person who acquired the sample
            - system_name: Instrument system name
    """
    if not sample_id or sample_id.strip() == '':
        return []

    try:
        matches = SampleMetadata.objects.filter(
            sample_name__iexact=sample_id.strip()
        ).values(
            'result_id',
            'date_acquired',
            'acquired_by',
            'system_name'
        ).order_by('-date_acquired')  # Most recent first

        return list(matches)
    except Exception as e:
        print(f"Error looking up sample ID '{sample_id}': {e}")
        return []


def lookup_sample_info_by_result_id(result_id):
    """
    Look up sample information for a given Result ID.

    Args:
        result_id (int or str): Result ID to search for

    Returns:
        dict or None: Dictionary containing sample information if found:
            - sample_name: The sample ID/name
            - date_acquired: Date acquired
            - acquired_by: Person who acquired
            - system_name: Instrument system
    """
    if not result_id:
        return None

    try:
        result_id_int = int(result_id)
        sample = SampleMetadata.objects.filter(
            result_id=result_id_int
        ).values(
            'sample_name',
            'date_acquired',
            'acquired_by',
            'system_name'
        ).first()

        return sample
    except (ValueError, TypeError) as e:
        print(f"Invalid result ID '{result_id}': {e}")
        return None
    except Exception as e:
        print(f"Error looking up result ID '{result_id}': {e}")
        return None


def validate_sample_result_pair(sample_id, result_id):
    """
    Validate that a Sample ID and Result ID belong together.

    Args:
        sample_id (str): Sample ID (e.g., 'FD-009-068')
        result_id (int or str): Result ID

    Returns:
        tuple: (is_valid: bool, message: str)
    """
    if not sample_id or not result_id:
        return False, "Both Sample ID and Result ID must be provided"

    try:
        result_id_int = int(result_id)
        sample_info = lookup_sample_info_by_result_id(result_id_int)

        if not sample_info:
            return False, f"Result ID {result_id} not found in database"

        db_sample_name = sample_info['sample_name']
        if db_sample_name and db_sample_name.strip().upper() == sample_id.strip().upper():
            return True, "Sample ID and Result ID match confirmed"
        else:
            return False, f"Mismatch: Result ID {result_id} belongs to sample '{db_sample_name}', not '{sample_id}'"

    except (ValueError, TypeError):
        return False, f"Invalid Result ID format: '{result_id}'"
    except Exception as e:
        return False, f"Validation error: {str(e)}"


def batch_lookup_samples(sample_ids):
    """
    Perform batch lookup of multiple Sample IDs for efficiency.

    Args:
        sample_ids (list): List of sample IDs to look up

    Returns:
        dict: Dictionary mapping sample_id -> list of result info dicts
    """
    if not sample_ids:
        return {}

    # Clean and deduplicate sample IDs
    cleaned_ids = [sid.strip() for sid in sample_ids if sid and sid.strip()]
    unique_ids = list(set(cleaned_ids))

    if not unique_ids:
        return {}

    try:
        # Build Q objects for case-insensitive matching
        query = Q()
        for sid in unique_ids:
            query |= Q(sample_name__iexact=sid)

        matches = SampleMetadata.objects.filter(query).values(
            'sample_name',
            'result_id',
            'date_acquired',
            'acquired_by',
            'system_name'
        ).order_by('sample_name', '-date_acquired')

        # Group by sample name (case-insensitive)
        results = {}
        for match in matches:
            sample_name = match['sample_name']
            if sample_name:
                # Use uppercase as the key for consistency
                key = sample_name.strip().upper()
                if key not in results:
                    results[key] = []
                results[key].append({
                    'result_id': match['result_id'],
                    'date_acquired': match['date_acquired'],
                    'acquired_by': match['acquired_by'],
                    'system_name': match['system_name']
                })

        return results
    except Exception as e:
        print(f"Error in batch lookup: {e}")
        return {}


def process_sample_lookup(sample_id, result_id):
    """
    Process a single sample row and determine the lookup/validation status.

    Args:
        sample_id (str or None): Sample ID from template
        result_id (str/int or None): Result ID from template

    Returns:
        dict: Processing result containing:
            - status: 'Match Confirmed' | 'Found' | 'Multiple Matches' | 'Not Found' | 'Validation Error' | 'Missing Data'
            - found_result_ids: List of found result IDs
            - duplicate_flag: 'Yes' | 'No'
            - duplicate_count: Number of matches
            - validation_notes: Human-readable message
            - date_acquired: Pipe-separated dates
            - acquired_by: Pipe-separated names
    """
    result = {
        'status': 'Missing Data',
        'found_result_ids': [],
        'duplicate_flag': 'No',
        'duplicate_count': 0,
        'validation_notes': '',
        'date_acquired': '',
        'acquired_by': ''
    }

    # Case 1: Both Sample ID and Result ID provided - Validate they match
    if sample_id and result_id:
        is_valid, message = validate_sample_result_pair(sample_id, result_id)
        if is_valid:
            result['status'] = 'Match Confirmed'
            result['found_result_ids'] = [str(result_id)]
            result['duplicate_count'] = 1
            result['validation_notes'] = message
            # Get additional info
            info = lookup_sample_info_by_result_id(result_id)
            if info:
                result['date_acquired'] = str(info.get('date_acquired', ''))
                result['acquired_by'] = str(info.get('acquired_by', ''))
        else:
            result['status'] = 'Validation Error'
            result['validation_notes'] = message

    # Case 2: Only Sample ID provided - Look up Result ID(s)
    elif sample_id:
        matches = lookup_result_ids_by_sample_id(sample_id)
        if not matches:
            result['status'] = 'Not Found'
            result['validation_notes'] = f"No results found for sample '{sample_id}'"
        elif len(matches) == 1:
            result['status'] = 'Found'
            result['found_result_ids'] = [str(matches[0]['result_id'])]
            result['duplicate_count'] = 1
            result['date_acquired'] = str(matches[0].get('date_acquired', ''))
            result['acquired_by'] = str(matches[0].get('acquired_by', ''))
            result['validation_notes'] = f"Found 1 match for sample '{sample_id}'"
        else:
            result['status'] = 'Multiple Matches'
            result['duplicate_flag'] = 'Yes'
            result['found_result_ids'] = [str(m['result_id']) for m in matches]
            result['duplicate_count'] = len(matches)
            result['date_acquired'] = '|'.join([str(m.get('date_acquired', '')) for m in matches])
            result['acquired_by'] = '|'.join([str(m.get('acquired_by', '')) for m in matches])
            result['validation_notes'] = f"Found {len(matches)} matches for sample '{sample_id}' - please select one"

    # Case 3: Only Result ID provided - Verify it exists
    elif result_id:
        info = lookup_sample_info_by_result_id(result_id)
        if info:
            result['status'] = 'Found'
            result['found_result_ids'] = [str(result_id)]
            result['duplicate_count'] = 1
            result['date_acquired'] = str(info.get('date_acquired', ''))
            result['acquired_by'] = str(info.get('acquired_by', ''))
            result['validation_notes'] = f"Result ID {result_id} verified (sample: {info.get('sample_name', 'N/A')})"
        else:
            result['status'] = 'Not Found'
            result['validation_notes'] = f"Result ID {result_id} not found in database"

    # Case 4: Neither provided
    else:
        result['validation_notes'] = 'No Sample ID or Result ID provided'

    return result
