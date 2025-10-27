"""
Export ALL decoded FRD data to a text file
Shows every single decoded time and response value
"""

import xml.etree.ElementTree as ET
import base64
import struct
import numpy as np

# Path to the FRD file
frd_path = r"C:\Users\cdallarosa\DataAlchemy\djangoProject\plotly_integration\process_development\analytical\octet\data\Kinetics\OE292\251013_001.frd"
output_path = r"C:\Users\cdallarosa\DataAlchemy\djangoProject\plotly_integration\process_development\analytical\octet\data\Kinetics\OE292\ALL_DECODED_RAW_DATA.txt"

def decode_base64_floats(base64_string, num_points):
    """Decode Base64-encoded float array"""
    if not base64_string:
        return np.array([])

    binary_data = base64.b64decode(base64_string)
    float_format = f'<{num_points}f'
    floats = struct.unpack(float_format, binary_data)
    return np.array(floats)

# Parse XML
tree = ET.parse(frd_path)
root = tree.getroot()

# Get experiment info
exp_info = root.find('ExperimentInfo')

# Open output file
with open(output_path, 'w') as f:
    f.write("="*80 + "\n")
    f.write("COMPLETE RAW DECODED FRD DATA - ALL VALUES\n")
    f.write("="*80 + "\n\n")
    f.write(f"File: {frd_path}\n")
    f.write(f"Experiment: {exp_info.get('Name')}\n")
    f.write(f"Run ID: {exp_info.findtext('RunID')}\n")
    f.write(f"Date: {exp_info.findtext('StartDateTime')}\n")
    f.write(f"Sensor: {exp_info.findtext('SensorName')}\n")
    f.write(f"Sensor Type: {exp_info.findtext('SensorType')}\n\n")

    # Find all steps
    steps = root.findall('.//KineticsData/Step')
    f.write(f"Total Steps: {len(steps)}\n")
    f.write("="*80 + "\n\n")

    # Process each step
    for i, step in enumerate(steps, 1):
        common_data = step.find('CommonData')
        step_type = step.findtext('StepType')
        step_name = step.findtext('StepName')
        sample_id = common_data.findtext('SampleID')
        sample_location = common_data.findtext('SampleLocation')
        concentration = common_data.findtext('Concentration')
        actual_time = step.findtext('ActualTime')

        f.write("="*80 + "\n")
        f.write(f"STEP {i}: {step_name}\n")
        f.write("="*80 + "\n")
        f.write(f"Type: {step_type}\n")
        f.write(f"Sample: {sample_id} (Well {sample_location})\n")
        f.write(f"Concentration: {concentration} µg/ml\n")
        f.write(f"Duration: {actual_time} seconds\n\n")

        # Get time series data
        x_data_elem = step.find('AssayXData')
        y_data_elem = step.find('AssayYData')

        if x_data_elem is not None and y_data_elem is not None:
            num_points = int(x_data_elem.get('Points', 0))

            # Show raw Base64
            x_base64 = x_data_elem.text
            y_base64 = y_data_elem.text

            f.write(f"RAW BASE64 DATA (first 100 chars):\n")
            f.write(f"X: {x_base64[:100]}...\n")
            f.write(f"Y: {y_base64[:100]}...\n\n")

            # Decode
            time_array = decode_base64_floats(x_base64, num_points)
            response_array = decode_base64_floats(y_base64, num_points)

            f.write(f"DECODED DATA ({num_points} points):\n")
            f.write("-"*80 + "\n")
            f.write(f"{'Point':<8} {'Time (s)':<15} {'Response (nm)':<15}\n")
            f.write("-"*80 + "\n")

            # Write ALL values
            for j in range(num_points):
                f.write(f"{j+1:<8} {time_array[j]:<15.6f} {response_array[j]:<15.6f}\n")

            f.write("\n")
            f.write(f"STATISTICS:\n")
            f.write(f"  Time range: {time_array.min():.6f} - {time_array.max():.6f} seconds\n")
            f.write(f"  Response range: {response_array.min():.6f} - {response_array.max():.6f} nm\n")
            f.write(f"  Mean response: {response_array.mean():.6f} nm\n")
            f.write(f"  Std dev: {response_array.std():.6f} nm\n")
            f.write("\n\n")
        else:
            f.write("No time series data found.\n\n")

    f.write("="*80 + "\n")
    f.write("END OF DECODED DATA\n")
    f.write("="*80 + "\n")

print(f"Complete decoded data exported to:")
print(output_path)
print("\nThis file contains EVERY decoded time/response value from all 132 steps.")
