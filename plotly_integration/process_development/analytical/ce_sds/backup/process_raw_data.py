import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# === FULL SCRIPT TO OPEN, PARSE, AND PLOT ASC FILE ===

def parse_and_plot_asc(file_path):
    # Read lines
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    # Parse metadata (clean commas and spaces)
    metadata = {}
    for line in lines:
        if ':' in line:
            key, value = line.split(':', 1)
            clean_value = value.strip().lstrip(',').rstrip(',')
            metadata[key.strip()] = clean_value
        else:
            break

    # Safely extract multipliers
    try:
        x_multiplier = float(metadata.get('X Axis Multiplier', '1').split(',')[0])
        y_multipliers = [float(v) for v in metadata.get('Y Axis Multiplier', '1,1,1').split(',') if v.strip()]
    except Exception:
        x_multiplier = 1.0
        y_multipliers = [1.0, 1.0, 1.0]

    # Find where data starts
    data_start_idx = next(i for i, line in enumerate(lines) if not ':' in line)

    # Parse numerical data
    numeric_lines = []
    for line in lines[data_start_idx:]:
        numbers = [n.strip() for n in line.strip().split(',') if n.strip()]
        numeric_lines.extend(numbers)

    numeric_array = np.array([float(num) for num in numeric_lines])

    # Determine channels and points
    num_channels = int(metadata.get('Maxchannels', 3))
    num_points = len(numeric_array) // num_channels

    channels = {}
    for ch in range(num_channels):
        channels[ch] = numeric_array[ch*num_points : (ch+1)*num_points]

    # Build DataFrame
    # time = np.arange(num_points) * x_multiplier
    sampling_rate = float(metadata.get('Sampling Rate', '2').split(',')[0])
    time = np.arange(num_points) * (1 / sampling_rate) / 60
    df = pd.DataFrame({
        'Time (min)': time,
        'Channel 1 (AU)': channels[0] * y_multipliers[0],
        'Channel 2 (KV)': channels[1] * y_multipliers[1],
        'Channel 3 (A)': channels[2] * y_multipliers[2],
    })

    # Plot Channel 1
    plt.figure(figsize=(10, 5))
    plt.plot(df['Time (min)'], df['Channel 1 (AU)'])
    plt.title('Channel 1 (AU) vs Time')
    plt.xlabel('Time (min)')
    plt.ylabel('Channel 1 (AU)')
    plt.grid(True)
    plt.show()

    # Plot Channel 2
    plt.figure(figsize=(10, 5))
    plt.plot(df['Time (min)'], df['Channel 2 (KV)'])
    plt.title('Channel 2 (KV) vs Time')
    plt.xlabel('Time (min)')
    plt.ylabel('Channel 2 (KV)')
    plt.grid(True)
    plt.show()

    # Plot Channel 3
    plt.figure(figsize=(10, 5))
    plt.plot(df['Time (min)'], df['Channel 3 (A)'])
    plt.title('Channel 3 (A) vs Time')
    plt.xlabel('Time (min)')
    plt.ylabel('Channel 3 (A)')
    plt.grid(True)
    plt.show()

    return df

# Example usage:
df = parse_and_plot_asc('../test_files/test_data/R PD3181 4-8-2025 7-33-00 PM.dat.asc')
