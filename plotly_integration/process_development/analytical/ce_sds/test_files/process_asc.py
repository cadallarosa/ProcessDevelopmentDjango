import os
import shutil
import hashlib
import pandas as pd
from datetime import datetime
from plotly_integration.models import CESDSTimeSeries, CESDSMetadata

def parse_asc_file(file_path):
    """
    Parse .asc file with vertical channel blocks based on 'Total Data Points' metadata.
    Each channel's data is stacked vertically (ch1, ch2, ch3).
    """
    import pandas as pd

    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    metadata = {}
    data_lines = []
    for line in lines:
        if ':' in line:
            parts = line.strip().split(':', 1)
            key = parts[0].strip()
            value_str = parts[1].strip()

            # Detect delimiter (comma or tab)
            if ',' in value_str:
                rest = value_str.split(',')
            else:
                rest = value_str.split('\t')

            value = [v.strip() for v in rest if v.strip()]
            metadata[key] = value
        else:
            data_lines.append(line.strip())

    # Parse numeric values from data lines
    numeric_values = []
    for line in data_lines:
        try:
            numeric_values.append(float(line))
        except ValueError:
            continue

    # Get number of channels and points per channel
    try:
        num_channels = int(metadata.get('Maxchannels', ['3'])[0])
        points_per_channel = int(metadata.get('Total Data Points', ['0'])[0])  # <-- from metadata
        sampling_rate = float(metadata.get('Sampling Rate', ['2'])[0])
    except Exception as e:
        raise ValueError(f"Failed to parse required metadata fields: {e}")

    expected_length = num_channels * points_per_channel
    if len(numeric_values) < expected_length:
        raise ValueError(f"Expected {expected_length} values, found {len(numeric_values)}")

    # Slice vertically
    ch1 = numeric_values[0:points_per_channel]
    ch2 = numeric_values[points_per_channel:2*points_per_channel]
    ch3 = numeric_values[2*points_per_channel:3*points_per_channel]

    # Time vector in minutes
    time_step_min = (1 / sampling_rate) / 60
    time = pd.Series(range(points_per_channel)) * time_step_min

    # Build DataFrame
    df = pd.DataFrame({
        'time_min': time,
        'channel_1': ch1,
        'channel_2': ch2,
        'channel_3': ch3
    })
    print(df)

    return metadata, df


def generate_sample_set_id(sample_set_name):
    return int(hashlib.sha1(sample_set_name.encode('utf-8')).hexdigest(), 16) % (10**10)


def save_asc_to_db(file_path):
    metadata_dict, timeseries_df = parse_asc_file(file_path)

    # Extract folder name as sample set - FIX: Handle both forward and back slashes
    data_file_path = metadata_dict.get('Data File', [''])[0]

    # Normalize path separators to handle cross-platform compatibility
    normalized_path = data_file_path.replace('\\', '/')

    # Extract the folder name from the normalized path
    if normalized_path:
        path_parts = normalized_path.split('/')
        # Get the parent directory name (second to last part)
        sample_set_name = path_parts[-2] if len(path_parts) >= 2 else ''
    else:
        sample_set_name = ''

    # Add debug logging to see what we're extracting
    print(f"Original path: {data_file_path}")
    print(f"Normalized path: {normalized_path}")
    print(f"Extracted sample set name: '{sample_set_name}'")

    sample_set_id = generate_sample_set_id(sample_set_name) if sample_set_name else 0

    # Fix here
    sample_id_full = metadata_dict.get('Sample ID', ['Unknown'])[0]
    parts = sample_id_full.split(' ', 1)
    sample_prefix = parts[0] if parts else 'Unknown'
    sample_id_clean = parts[1] if len(parts) > 1 else sample_id_full

    # Fix acquisition datetime
    acq_dt_str = metadata_dict.get('Acquisition Date and Time', [''])[0]
    try:
        acquisition_datetime = datetime.strptime(acq_dt_str, '%m/%d/%Y %I:%M:%S %p')
    except Exception:
        acquisition_datetime = None

    # Simple logic: Check if file already processed using original_file_name
    original_file_name = os.path.basename(file_path)
    
    try:
        existing_metadata = CESDSMetadata.objects.filter(original_file_name=original_file_name).first()
        
        if existing_metadata:
            # File already processed - skip
            print(f"✓ File already processed: {original_file_name}")
            print(f"  Sample ID: {existing_metadata.sample_id_full} (Metadata ID: {existing_metadata.id})")
            print(f"  Skipping data insertion, will move file to processed folder")
            return existing_metadata.id  # Return the existing ID
        
        # Create new metadata record
        print(f"Creating new metadata record for file: {original_file_name}")
        print(f"  Sample ID: {sample_id_full}")
        
        metadata = CESDSMetadata.objects.create(
            original_file_name=original_file_name,
            sample_id_full=sample_id_full,
            sample_id_clean=sample_id_clean,
            sample_prefix=sample_prefix,
            sample_set_id=sample_set_id,
            sample_set_name=sample_set_name,
            data_file_path=metadata_dict.get('Data File', [''])[0],
            method_path=metadata_dict.get('Method', [''])[0],
            user_name=metadata_dict.get('User Name', [''])[0],
            acquisition_datetime=acquisition_datetime,
            sampling_rate=float(metadata_dict.get('Sampling Rate', ['2'])[0]),
            total_data_points=int(metadata_dict.get('Total Data Points', ['0'])[0]),
            x_axis_title=', '.join(metadata_dict.get('X Axis Title', [])),
            y_axis_title=', '.join(metadata_dict.get('Y Axis Title', [])),
            x_axis_multiplier=float(metadata_dict.get('X Axis Multiplier', ['1'])[0]),
            y_axis_multiplier=float(metadata_dict.get('Y Axis Multiplier', ['1'])[0])
        )
        print(f"✓ Created new metadata record ID: {metadata.id}")
        
    except Exception as e:
        print(f"✗ Error handling metadata record: {e}")
        import traceback
        traceback.print_exc()
        raise

    # Verify we have a valid metadata ID
    if not metadata.id:
        raise ValueError(f"Metadata record does not have a valid ID: {metadata}")

    print(f"Using metadata ID: {metadata.id} for time series creation")

    # Bulk insert timeseries using metadata_id directly
    timeseries_objects = [
        CESDSTimeSeries(
            metadata_id=metadata.id,  # Use metadata_id instead of metadata object
            time_min=row['time_min'],
            channel_1=row['channel_1'],
            channel_2=row['channel_2'],
            channel_3=row['channel_3']
        )
        for _, row in timeseries_df.iterrows()
    ]

    CESDSTimeSeries.objects.bulk_create(timeseries_objects)
    print(f"Created {len(timeseries_objects)} time series records for metadata ID: {metadata.id}")

    return metadata.id


def move_file_to_processed(file_path, processed_folder):
    """
    Move a file to the processed folder with comprehensive error handling and logging
    """
    try:
        # Check if source file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Source file does not exist: {file_path}")

        # Check if source is actually a file
        if not os.path.isfile(file_path):
            raise ValueError(f"Source path is not a file: {file_path}")

        # Create destination folder if it doesn't exist
        if not os.path.exists(processed_folder):
            os.makedirs(processed_folder, exist_ok=True)
            print(f"Created processed folder: {processed_folder}")

        # Get the filename from the source path
        filename = os.path.basename(file_path)
        destination_path = os.path.join(processed_folder, filename)

        # Check if destination file already exists
        if os.path.exists(destination_path):
            print(f"Warning: Destination file already exists: {destination_path}")
            # Option 1: Overwrite (remove existing file first)
            os.remove(destination_path)
            print(f"Removed existing file: {destination_path}")

            # Option 2: Create unique filename (uncomment if preferred)
            # base, ext = os.path.splitext(filename)
            # counter = 1
            # while os.path.exists(destination_path):
            #     new_filename = f"{base}_{counter}{ext}"
            #     destination_path = os.path.join(processed_folder, new_filename)
            #     counter += 1
            # print(f"Using unique filename: {os.path.basename(destination_path)}")

        # Perform the move
        print(f"Moving file from: {file_path}")
        print(f"Moving file to: {destination_path}")

        shutil.move(file_path, destination_path)

        # Verify the move was successful
        if os.path.exists(destination_path) and not os.path.exists(file_path):
            print(f"Successfully moved {filename} to processed folder")
            return True
        else:
            raise RuntimeError(
                f"File move verification failed. Source still exists: {os.path.exists(file_path)}, Destination exists: {os.path.exists(destination_path)}")

    except PermissionError as e:
        print(f"Permission error moving file {file_path}: {e}")
        print(f"Check file/folder permissions for: {file_path} and {processed_folder}")
        raise
    except OSError as e:
        print(f"OS error moving file {file_path}: {e}")
        print(f"Possible causes: disk full, network drive issues, file locked")
        raise
    except Exception as e:
        print(f"Unexpected error moving file {file_path}: {e}")
        print(f"Source exists: {os.path.exists(file_path) if 'file_path' in locals() else 'Unknown'}")
        print(
            f"Destination folder exists: {os.path.exists(processed_folder) if 'processed_folder' in locals() else 'Unknown'}")
        raise


