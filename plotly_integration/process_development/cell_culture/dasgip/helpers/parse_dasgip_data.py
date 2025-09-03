import pandas as pd
import numpy as np
import re
from pathlib import Path

def downsample_and_consolidate(df, target_frequency_seconds=5):
    """
    Downsample data to target frequency and consolidate measurements from same timeframe.
    
    Args:
        df: DataFrame with timestamp and measurement data
        target_frequency_seconds: Target sampling frequency in seconds (default: 5)
    
    Returns:
        DataFrame with downsampled and consolidated data
    """
    print(f"Downsampling data to {target_frequency_seconds} second intervals...")
    
    # Create bins for every N seconds
    df = df.copy()
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    
    # Round timestamps to nearest target frequency
    # Get the start time and create regular intervals
    start_time = df['Timestamp'].min()
    start_time = start_time.floor(f'{target_frequency_seconds}s')
    
    # Calculate seconds since start
    df['seconds_since_start'] = (df['Timestamp'] - start_time).dt.total_seconds()
    
    # Group into regular intervals
    df['interval_index'] = (df['seconds_since_start'] // target_frequency_seconds).astype(int)
    df['TimeGroup'] = start_time + pd.to_timedelta(df['interval_index'] * target_frequency_seconds, unit='s')
    
    print(f"Original data points: {len(df)}")
    print(f"Unique time groups: {df['TimeGroup'].nunique()}")
    
    # Group by time bins and aggregate
    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Remove TimeGroup and Duration from numeric columns if present
    numeric_columns = [col for col in numeric_columns if col not in ['TimeGroup']]
    
    agg_dict = {}
    
    # For Duration, take the first value in each group (represents time from start)
    if 'Duration' in df.columns:
        agg_dict['Duration'] = 'first'
    
    # For all other numeric columns, use mean to consolidate multiple measurements
    # but ignore NaN values in the aggregation
    for col in numeric_columns:
        if col != 'Duration':
            agg_dict[col] = 'mean'
    
    # Group by time bins and aggregate
    grouped = df.groupby('TimeGroup').agg(agg_dict).reset_index()
    
    # Rename TimeGroup back to Timestamp
    grouped = grouped.rename(columns={'TimeGroup': 'Timestamp'})
    
    # Remove helper columns
    columns_to_drop = ['seconds_since_start', 'interval_index']
    grouped = grouped.drop(columns=[col for col in columns_to_drop if col in grouped.columns])
    
    # Sort by timestamp
    grouped = grouped.sort_values('Timestamp')
    
    print(f"Downsampled data points: {len(grouped)}")
    
    return grouped

def parse_dasgip_csv(file_path, downsample_seconds=None):
    """
    Parse DASGIP bioreactor CSV file and extract clean data.
    DASGIP files have a complex structure with metadata at the top and data at the bottom.
    """
    
    # Read the file to find where the actual data starts
    print("Analyzing file structure...")
    
    # First, find where the track definitions end and data begins
    data_start_line = None
    header_columns = []
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line_num, line in enumerate(f):
            # Look for lines that start with timestamp format (YYYY-MM-DD)
            if re.match(r'^\d{4}-\d{2}-\d{2}', line.strip().strip('"')):
                data_start_line = line_num
                print(f"Found data starting at line {line_num + 1}")
                break
    
    if data_start_line is None:
        print("Could not find data section in file")
        return None
    
    # Now we need to build the column headers from the track definitions
    print("Extracting column headers from track definitions...")
    
    # Read track definitions to build proper column names
    track_columns = ['Timestamp', 'Duration']  # First two columns are always these
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()
        
        # Look for track definitions (lines that start with "Track" followed by a number)
        for line in lines[:data_start_line]:
            if re.match(r'"Track\d+";', line):
                parts = line.strip().split(';')
                if len(parts) >= 4:
                    # Extract the column name (4th field, remove quotes)
                    col_name = parts[3].strip('"')
                    track_columns.append(col_name)
    
    print(f"Found {len(track_columns)} columns")
    print("Sample columns:", track_columns[:10])
    
    # Now read the actual data starting from the identified line
    print("Reading data...")
    
    try:
        # Read data starting from the identified line
        df = pd.read_csv(file_path, 
                        skiprows=data_start_line,
                        sep=';',
                        header=None,
                        quotechar='"',
                        encoding='utf-8',
                        on_bad_lines='skip')
        
        # Assign column names
        if len(track_columns) <= len(df.columns):
            df.columns = track_columns + [f'Unknown_{i}' for i in range(len(track_columns), len(df.columns))]
        else:
            # If we have more expected columns than actual columns, trim the list
            df.columns = track_columns[:len(df.columns)]
        
        print(f"Loaded data with shape: {df.shape}")
        
        # Clean up the data
        print("Cleaning data...")
        
        # Convert timestamp column
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], errors='coerce')
        
        # Convert duration to numeric (it's in days as decimal)
        df['Duration'] = pd.to_numeric(df['Duration'], errors='coerce')
        
        # Convert numeric columns
        numeric_columns = df.columns[2:]  # Skip Timestamp and Duration
        for col in numeric_columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Remove rows where timestamp is null
        df = df.dropna(subset=['Timestamp'])
        
        # Sort by timestamp
        df = df.sort_values('Timestamp')
        
        print(f"Clean data shape: {df.shape}")
        print(f"Date range: {df['Timestamp'].min()} to {df['Timestamp'].max()}")
        
        # Apply downsampling if requested
        if downsample_seconds:
            print(f"\nApplying downsampling to {downsample_seconds} second intervals...")
            df = downsample_and_consolidate(df, downsample_seconds)
            print(f"Final downsampled data shape: {df.shape}")
        
        return df
        
    except Exception as e:
        print(f"Error reading data: {e}")
        return None

def export_clean_data(df, output_path):
    """Export cleaned data to CSV"""
    df.to_csv(output_path, index=False)
    print(f"Exported clean data to: {output_path}")

if __name__ == "__main__":
    # Input file path
    input_file = r"C:\Users\cdallarosa\DataAlchemy\djangoProject\plotly_integration\process_development\cell_culture\dasgip\raw_data\CTPCNK808814.E59BRX.Control.csv"
    
    # Output file path
    output_file = r"/plotly_integration/process_development/cell_culture/dasgip/cleaned_data/CTPCNK808814_E59BRX_Control_clean_5s.csv"
    
    # Parse the file with 5-second downsampling
    df = parse_dasgip_csv(input_file, downsample_seconds=5)
    
    if df is not None:
        # Show some info about the data
        print("\nData Info:")
        print(f"Columns: {list(df.columns)}")
        print(f"\nFirst few rows:")
        print(df.head())
        
        print(f"\nData types:")
        print(df.dtypes)
        
        print(f"\nSummary statistics for numeric columns:")
        print(df.describe())
        
        # Export clean data
        export_clean_data(df, output_file)
        
        print(f"\nData successfully parsed and exported!")
        print(f"Original file: {input_file}")
        print(f"Clean file: {output_file}")
    else:
        print("Failed to parse the file")