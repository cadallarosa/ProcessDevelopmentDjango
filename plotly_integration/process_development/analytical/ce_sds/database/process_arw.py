import os
import shutil
import hashlib
from datetime import datetime
from django.db import transaction
from django.utils import timezone
from plotly_integration.models import SampleMetadata, ChromMetadata, TimeSeriesData


def generate_result_id(date_acquired, sample_name):
    """
    Generate a unique result_id using composite key of date and sample name
    Returns an integer hash that fits in IntegerField
    """
    if not date_acquired:
        date_acquired = datetime.now()
    
    # Create composite key string
    date_str = date_acquired.strftime("%Y%m%d%H%M%S") if isinstance(date_acquired, datetime) else str(date_acquired)
    composite_key = f"CESDS_{date_str}_{sample_name}"
    
    # Generate hash and convert to positive integer
    hash_object = hashlib.md5(composite_key.encode())
    hash_hex = hash_object.hexdigest()
    # Take first 8 hex chars and convert to int (ensures it fits in IntegerField)
    result_id = int(hash_hex[:8], 16) % 2147483647  # Ensure it fits in a 32-bit signed integer
    
    return result_id


def parse_arw_file(file_path):
    """
    Parse .arw file containing CE SDS time series data
    Returns parsed metadata and time series data
    """
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    # Initialize metadata with CE SDS defaults
    system_name = "CE SDS"  # Default system name as requested
    sample_name = ""
    date_acquired = None
    sample_set_id = None
    sample_set_name = ""
    injection_id = None
    
    # Parse header information
    if len(lines) < 2:
        raise ValueError(f"Invalid ARW file format in {file_path}")
    
    header_line = lines[0].strip()
    header_parts = header_line.split('\t')
    
    # Parse the metadata line (second line)
    if len(lines) > 1:
        metadata_line = lines[1].strip()
        metadata_parts = metadata_line.split('\t')
        
        # Create header mapping
        header_map = {}
        for i, header in enumerate(header_parts):
            if i < len(metadata_parts):
                header_map[header.strip('"').strip()] = metadata_parts[i].strip('"').strip()
        
        # Extract metadata
        sample_name = header_map.get('SampleName', '')
        sample_set_name = header_map.get('Sample Set Name', '')
        
        # Parse sample set ID
        sample_set_id_str = header_map.get('Sample Set Id', '')
        if sample_set_id_str:
            try:
                sample_set_id = int(sample_set_id_str)
            except ValueError:
                sample_set_id = None
        
        # Parse injection ID
        injection_id_str = header_map.get('Injection Id', '')
        if injection_id_str:
            try:
                injection_id = int(injection_id_str)
            except ValueError:
                injection_id = None
        
        # Parse date acquired
        date_str = header_map.get('Date Acquired', '')
        if date_str:
            # Try to parse date - format: "9/5/2025 1:05:32 AM"
            try:
                date_acquired = datetime.strptime(date_str.strip(), '%m/%d/%Y %I:%M:%S %p')
                # Make timezone aware
                date_acquired = timezone.make_aware(date_acquired, timezone.get_default_timezone())
            except ValueError:
                try:
                    date_acquired = datetime.strptime(date_str.strip(), '%m/%d/%Y %H:%M:%S')
                    # Make timezone aware
                    date_acquired = timezone.make_aware(date_acquired, timezone.get_default_timezone())
                except ValueError:
                    print(f"  Warning: Could not parse date '{date_str}' from file")
                    date_acquired = None
    
    # Fallback: extract sample name from filename if not found
    if not sample_name:
        sample_name = os.path.basename(file_path).replace('.arw', '').replace('CAD_export', 'CESDS_')
    
    # Date should always be found in the file
    if not date_acquired:
        raise ValueError(f"Could not find or parse 'Date Acquired' field in file {file_path}")
    
    # Generate unique result_id
    result_id = generate_result_id(date_acquired, sample_name)
    
    # Parse time series data (CE SDS uses only channel 1)
    time_series_data = []
    data_start_idx = 2  # Data typically starts from line 3 (index 2)
    
    for i in range(data_start_idx, len(lines)):
        line = lines[i].strip()
        if not line:
            continue
        
        parts = line.split('\t')
        if len(parts) >= 2:
            try:
                time_val = float(parts[0])
                channel_1_val = float(parts[1])
                
                time_series_data.append({
                    'time': time_val,
                    'channel_1': channel_1_val
                })
            except ValueError:
                continue
    
    return {
        'result_id': result_id,
        'system_name': system_name,
        'sample_name': sample_name,
        'sample_set_id': sample_set_id,
        'sample_set_name': sample_set_name,
        'date_acquired': date_acquired,
        'injection_id': injection_id,
        'time_series_data': time_series_data,
        'analysis_type': 3,  # CE-SDS
        'file_name': os.path.basename(file_path)
    }


def save_arw_to_db(file_path):
    """
    Process and save ARW file data to database
    Uses SampleMetadata, ChromMetadata, and TimeSeriesData tables
    """
    data = parse_arw_file(file_path)
    
    with transaction.atomic():
        # Parse sample prefix (R or NR)
        sample_prefix = None
        if data['sample_name']:
            if data['sample_name'].startswith('NR'):
                sample_prefix = 'NR'
            elif data['sample_name'].startswith('R'):
                sample_prefix = 'R'
        
        # Use update_or_create for SampleMetadata
        sample_metadata, created = SampleMetadata.objects.update_or_create(
            result_id=data['result_id'],
            defaults={
                'system_name': data['system_name'],
                'sample_name': data['sample_name'],
                'sample_prefix': sample_prefix,
                'sample_set_id': data['sample_set_id'],
                'sample_set_name': data['sample_set_name'] or '',
                'date_acquired': data['date_acquired'],
                'analysis_type': data['analysis_type'],
                'sample_type': 3,  # CE-SDS sample type
                'injection_id': data['injection_id']
            }
        )
        
        action = "Created" if created else "Updated"
        print(f"  {action} SampleMetadata for result_id {data['result_id']}")
        
        # Use update_or_create for ChromMetadata
        chrom_metadata, created = ChromMetadata.objects.update_or_create(
            result_id=data['result_id'],
            defaults={
                'system_name': data['system_name'],
                'sample_name': data['sample_name'],
                'sample_set_id': data['sample_set_id'],
                'sample_set_name': data['sample_set_name'] or '',
                'channel_1': 'CE-SDS Data',
                'channel_2': None,
                'channel_3': None
            }
        )
        
        # For time series data, we need to delete existing and create new since there can be many records
        # Delete existing time series data for this result_id
        existing_ts_count = TimeSeriesData.objects.filter(result_id=data['result_id']).count()
        if existing_ts_count > 0:
            TimeSeriesData.objects.filter(result_id=data['result_id']).delete()
            print(f"  Deleted {existing_ts_count} existing time series records for result_id {data['result_id']}")
        
        # Bulk create new time series data (only channel 1)
        time_series_objects = [
            TimeSeriesData(
                result_id=data['result_id'],
                system_name=data['system_name'],
                time=point['time'],
                channel_1=point['channel_1'],
                channel_2=None,  # CE SDS only uses channel 1
                channel_3=None
            )
            for point in data['time_series_data']
        ]
        
        TimeSeriesData.objects.bulk_create(time_series_objects, batch_size=1000)
        
        print(f"  Created {len(time_series_objects)} time series records for result_id {data['result_id']}")
    
    return data['result_id']


def process_files(directory, reported_folder):
    """
    Process all CE SDS ARW files in directory and move to reported folder
    This matches the Empower processing pattern
    """
    # Ensure reported folder exists
    os.makedirs(reported_folder, exist_ok=True)
    
    # Get all ARW files
    arw_files = [f for f in os.listdir(directory) if f.lower().endswith('.arw')]
    
    # List to hold files that need to be moved
    files_to_move = []
    
    files_processed = False
    if len(arw_files) == 0:
        print("No ARW files to process")
        files_processed = True
        return 0
    else:
        files_processed = False
    
    successful = 0
    failed = 0
    
    print(f"Processing {len(arw_files)} CE SDS ARW files...")
    
    while not files_processed:
        for filename in arw_files:
            file_path = os.path.join(directory, filename)
            
            try:
                print(f"Processing ARW file: {filename}")
                result_id = save_arw_to_db(file_path)
                
                if result_id:
                    successful += 1
                    print(f"  ✓ Successfully imported with result_id {result_id}")
                else:
                    successful += 1
                    print(f"  ✓ File processed")
                    
                # Add the file to the list of files to move
                files_to_move.append(file_path)
                    
            except Exception as e:
                failed += 1
                print(f"  ✗ Failed to import {filename}: {e}")
                import traceback
                traceback.print_exc()
        
        files_processed = True
    
    # Move all processed files to the reported folder in bulk
    for file_path in files_to_move:
        try:
            shutil.move(file_path, os.path.join(reported_folder, os.path.basename(file_path)))
            print(f"  → Moved {os.path.basename(file_path)} to processed folder")
        except Exception as move_error:
            print(f"  ✗ Could not move file {os.path.basename(file_path)}: {move_error}")
    
    print(f"CE SDS ARW processing complete: {successful} successful, {failed} failed")
    return successful