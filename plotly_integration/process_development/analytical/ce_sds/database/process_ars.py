import os
import shutil
import hashlib
from datetime import datetime
from django.db import transaction
from django.utils import timezone
from plotly_integration.models import SampleMetadata, PeakResults


def generate_result_id(date_acquired, sample_name):
    """
    Generate a unique result_id using composite key of date and sample name
    Must match the same algorithm used in process_arw.py
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


def parse_ars_file(file_path):
    """
    Parse .ars report file containing CE SDS peak results and metadata
    Returns parsed metadata dictionary
    """
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
    
    # Initialize metadata
    system_name = "CE SDS"  # Default system name as requested
    sample_name = ""
    date_acquired = None
    project_name = ""
    sample_type = "Unknown"
    run_time = None
    injection_id = None
    instrument_method_name = ""
    
    # Parse metadata from ARS file
    for line in lines:
        line = line.strip()
        
        # Look for key metadata fields
        if 'Sample Name:' in line:
            # Extract sample name after the colon
            parts = line.split('Sample Name:')
            if len(parts) > 1:
                sample_name = parts[1].strip().strip('"')
        
        elif 'Date Acquired:' in line:
            # Extract date after the colon
            parts = line.split('Date Acquired:')
            if len(parts) > 1:
                date_str = parts[1].strip().strip('"').strip()  # Extra strip() to handle trailing spaces
                try:
                    # Parse date - format: "9/5/2025 1:05:32 AM"
                    date_acquired = datetime.strptime(date_str, '%m/%d/%Y %I:%M:%S %p')
                    # Make timezone aware
                    date_acquired = timezone.make_aware(date_acquired, timezone.get_default_timezone())
                except ValueError:
                    try:
                        date_acquired = datetime.strptime(date_str, '%m/%d/%Y %H:%M:%S')
                        # Make timezone aware
                        date_acquired = timezone.make_aware(date_acquired, timezone.get_default_timezone())
                    except ValueError:
                        print(f"  Warning: Could not parse date '{date_str}' from ARS file (length: {len(date_str)})")
                        pass
        
        elif 'Project Name:' in line:
            # Extract project name
            parts = line.split('Project Name:')
            if len(parts) > 1:
                project_name = parts[1].strip().strip('"')
                # Clean up project name
                project_name = project_name.replace('\\', '/').strip()
        
        elif 'Run Time:' in line:
            # Extract run time
            parts = line.split('Run Time:')
            if len(parts) > 1:
                run_time_str = parts[1].strip()
                # Parse run time (e.g., "30.01 Minutes")
                if 'Minutes' in run_time_str:
                    try:
                        run_time = float(run_time_str.replace('Minutes', '').strip())
                    except ValueError:
                        pass
        
        elif 'Injection Id:' in line:
            # Extract injection ID
            parts = line.split('Injection Id:')
            if len(parts) > 1:
                try:
                    injection_id = int(parts[1].strip())
                except ValueError:
                    pass
        
        elif 'Instrument Method Name:' in line:
            # Extract instrument method name
            parts = line.split('Instrument Method Name:')
            if len(parts) > 1:
                instrument_method_name = parts[1].strip().strip('"')
    
    # Fallback: extract sample name from filename if not found
    if not sample_name:
        sample_name = os.path.basename(file_path).replace('.ars', '').replace('CAD_export_report', 'CESDS_')
    
    # Date should always be found in the file
    if not date_acquired:
        raise ValueError(f"Could not find or parse 'Date Acquired' field in file {file_path}")
    
    # Generate the same result_id as ARW file would generate
    result_id = generate_result_id(date_acquired, sample_name)
    
    # Parse sample prefix (R or NR)
    sample_prefix = None
    if sample_name:
        if sample_name.startswith('NR'):
            sample_prefix = 'NR'
        elif sample_name.startswith('R'):
            sample_prefix = 'R'
    
    return {
        'result_id': result_id,
        'system_name': system_name,
        'sample_name': sample_name,
        'sample_prefix': sample_prefix,
        'project_name': project_name,
        'date_acquired': date_acquired,
        'run_time': run_time,
        'injection_id': injection_id,
        'instrument_method_name': instrument_method_name,
        'analysis_type': 3,  # CE-SDS
        'file_name': os.path.basename(file_path)
    }


def extract_peak_results(file_path, result_id, system_name):
    """
    Extract peak results from ARS file
    CE SDS specific peak extraction based on Empower logic
    """
    import csv
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        reader = csv.reader(f, delimiter='\t')
        data = [row for row in reader]
    
    peak_results = []
    peak_section_started = False
    check = False  # Flag to start reading after the header
    
    for row in data:
        row = [col.strip().strip('"') for col in row]  # Remove extra spaces and quotes
        
        # Look for the "Peak Results:" marker first
        if "Peak Results:" in row:
            peak_section_started = True
            continue
        
        # Only process after we've found the peak results section
        if not peak_section_started:
            continue
            
        # Look for peak results header - CE-SDS uses "% Area" as indicator
        if "% Area" in row and "RT" in row and "Area" in row:
            check = True
            continue  # Skip the header row
        
        elif "(min)" in row:
            continue  # Skip the units row
        
        # Start collecting peak data after header is found
        elif check and len(row) >= 3:
            # Look for actual peak data rows - they should have numeric data
            # Skip empty rows or non-data rows
            if not row[0] or 'Error Log' in ' '.join(row) or 'Page:' in ' '.join(row):
                if 'Error Log' in ' '.join(row) or 'Page:' in ' '.join(row):
                    check = False  # Stop processing when we hit these markers
                continue
                
            try:
                # CE-SDS format can have two layouts:
                # Layout 1: [Peak#, Channel, Name, RT, Area, %Area, Height, Asym@10, Plate Count, Res (HH), Start Time, End Time]
                # Layout 2: ["#", Peak#, Channel, Name, RT, Area, %Area, Height, Asym@10, Plate Count, Res (HH), Start Time, End Time]
                
                # Determine the format based on first column
                if row[0] == '#' and len(row) > 1 and row[1].isdigit():
                    # Layout 2: First column is "#", second column is peak number
                    peak_number = row[1]
                    channel_name = row[2] if len(row) > 2 and row[2] else 'Ch1'
                    peak_name = row[3] if len(row) > 3 and row[3] else f"Peak_{peak_number}"
                    rt_idx, area_idx, percent_area_idx, height_idx = 4, 5, 6, 7
                    start_time_idx, end_time_idx = 11, 12
                elif row[0].isdigit():
                    # Layout 1: First column is peak number
                    peak_number = row[0]
                    channel_name = row[1] if len(row) > 1 and row[1] else 'Ch1'
                    peak_name = row[2] if len(row) > 2 and row[2] else f"Peak_{peak_number}"
                    rt_idx, area_idx, percent_area_idx, height_idx = 3, 4, 5, 6
                    start_time_idx, end_time_idx = 10, 11
                else:
                    # Skip rows that don't match either format
                    continue
                
                # Extract numeric values with error handling
                rt = float(row[rt_idx]) if len(row) > rt_idx and row[rt_idx] and row[rt_idx] != '' else None
                area = int(float(row[area_idx])) if len(row) > area_idx and row[area_idx] and row[area_idx] != '' else None
                percent_area = float(row[percent_area_idx]) if len(row) > percent_area_idx and row[percent_area_idx] and row[percent_area_idx] != '' else None
                height = int(float(row[height_idx])) if len(row) > height_idx and row[height_idx] and row[height_idx] != '' else None
                start_time = float(row[start_time_idx]) if len(row) > start_time_idx and row[start_time_idx] and row[start_time_idx] != '' else None
                end_time = float(row[end_time_idx]) if len(row) > end_time_idx and row[end_time_idx] and row[end_time_idx] != '' else None
                
                # Only add if we have valid retention time (essential field)
                if rt is not None:
                    # Use peak number if no name provided
                    final_peak_name = peak_name if peak_name and peak_name.strip() else f"Peak_{peak_number}"
                    
                    peak_data = {
                        'result_id': result_id,
                        'system_name': system_name,
                        'channel_name': channel_name,  # Use actual channel name from file
                        'peak_name': final_peak_name,
                        'peak_retention_time': rt,
                        'area': area,
                        'percent_area': percent_area,
                        'height': height,
                        'peak_start_time': start_time,
                        'peak_end_time': end_time,
                    }
                    peak_results.append(peak_data)
                    
            except (ValueError, IndexError) as e:
                # Skip rows that can't be parsed
                continue
    
    if len(peak_results) == 0:
        print(f"  No peak results found in ARS file - this may be a metadata-only file")
        # Print first few rows for debugging
        print(f"  File preview (first 3 rows): {data[:3] if data else 'No data'}")
    else:
        print(f"  Extracted {len(peak_results)} peak results from ARS file")
    
    return peak_results


def save_ars_to_db(file_path):
    """
    Process and save ARS file data to database
    Updates existing SampleMetadata and adds PeakResults if available
    """
    data = parse_ars_file(file_path)
    
    with transaction.atomic():
        # Check if corresponding ARW data exists (should have same result_id)
        existing = SampleMetadata.objects.filter(result_id=data['result_id']).first()
        
        if existing:
            # Update existing record with additional metadata from ARS
            if data.get('project_name'):
                existing.project_name = data['project_name']
            if data.get('run_time'):
                existing.run_time = data['run_time']
            if data.get('instrument_method_name'):
                existing.instrument_method_name = data['instrument_method_name']
            existing.save()
            
            print(f"  Updated metadata for result_id {data['result_id']} from ARS file")
            
            # Delete existing peak results and replace with new ones
            PeakResults.objects.filter(result_id=data['result_id']).delete()
            print(f"  Deleted existing peak results for result_id {data['result_id']}")
            
            # Extract and save peak results
            peak_results = extract_peak_results(file_path, data['result_id'], data['system_name'])
            
            if peak_results:
                # Create PeakResults entries
                peak_objects = [
                    PeakResults(
                        result_id=pr['result_id'],
                        system_name=pr['system_name'],
                        channel_name=pr['channel_name'],
                        peak_name=pr['peak_name'],
                        peak_retention_time=pr['peak_retention_time'],
                        area=pr['area'],
                        percent_area=pr['percent_area'],
                        height=pr['height'],
                        peak_start_time=pr['peak_start_time'],
                        peak_end_time=pr['peak_end_time']
                    )
                    for pr in peak_results
                ]
                
                PeakResults.objects.bulk_create(peak_objects, batch_size=1000)
                print(f"  Created {len(peak_objects)} peak results for result_id {data['result_id']}")
            else:
                print(f"  No peak results to create for result_id {data['result_id']} (metadata-only file)")
                
        else:
            # No matching ARW data, create new SampleMetadata entry
            print(f"  No matching ARW data for ARS file, creating new entry for result_id {data['result_id']}")
            
            SampleMetadata.objects.create(
                result_id=data['result_id'],
                system_name=data['system_name'],
                sample_name=data['sample_name'],
                sample_prefix=data['sample_prefix'],
                project_name=data['project_name'],
                date_acquired=data['date_acquired'],
                run_time=data['run_time'],
                analysis_type=data['analysis_type'],
                sample_type=3,  # CE-SDS sample type
                injection_id=data['injection_id'],
                instrument_method_name=data['instrument_method_name']
            )
            
            # Extract and save peak results
            peak_results = extract_peak_results(file_path, data['result_id'], data['system_name'])
            
            if peak_results:
                peak_objects = [
                    PeakResults(**pr)
                    for pr in peak_results
                ]
                PeakResults.objects.bulk_create(peak_objects, ignore_conflicts=True)
                print(f"  Created {len(peak_objects)} peak results")
            else:
                print(f"  No peak results to create for result_id {data['result_id']} (metadata-only file)")
    
    return data['result_id']


def process_files(directory, reported_folder):
    """
    Process all CE SDS ARS files in directory and move to reported folder
    This matches the Empower processing pattern
    """
    # Ensure reported folder exists
    os.makedirs(reported_folder, exist_ok=True)
    
    # Get all ARS files
    ars_files = [f for f in os.listdir(directory) if f.lower().endswith('.ars')]
    
    # List to hold files that need to be moved
    files_to_move = []
    
    files_processed = False
    if len(ars_files) == 0:
        print("No ARS files to process")
        files_processed = True
        return 0
    else:
        files_processed = False
    
    successful = 0
    failed = 0
    
    print(f"Processing {len(ars_files)} CE SDS ARS files...")
    
    while not files_processed:
        for filename in ars_files:
            file_path = os.path.join(directory, filename)
            
            try:
                print(f"Processing ARS file: {filename}")
                result_id = save_ars_to_db(file_path)
                
                if result_id:
                    successful += 1
                    print(f"  ✓ Successfully processed with result_id {result_id}")
                else:
                    successful += 1  # Still count as successful since file was processed
                    print(f"  ✓ File processed (no peak data found)")
                    
                # Add the file to the list of files to move
                files_to_move.append(file_path)
                    
            except Exception as e:
                failed += 1
                print(f"  ✗ Failed to process {filename}: {e}")
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
    
    print(f"CE SDS ARS processing complete: {successful} successful, {failed} failed")
    return successful