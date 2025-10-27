"""
FRD File Decoder Example
Demonstrates how Base64 data in FRD files is decoded to actual time series values
"""

import xml.etree.ElementTree as ET
import base64
import struct
import numpy as np
from pathlib import Path

# Path to the FRD file
frd_path = r"C:\Users\cdallarosa\DataAlchemy\djangoProject\plotly_integration\process_development\analytical\octet\data\Kinetics\OE292\251013_001.frd"

print("=" * 80)
print("FRD FILE DECODER - DEMONSTRATION")
print("=" * 80)
print(f"File: {frd_path}")
print()

# Parse the XML file
tree = ET.parse(frd_path)
root = tree.getroot()

# Get experiment info
exp_info = root.find('ExperimentInfo')
print("EXPERIMENT INFORMATION")
print("-" * 80)
print(f"Name:           {exp_info.get('Name')}")
print(f"Run ID:         {exp_info.findtext('RunID')}")
print(f"Experiment:     {exp_info.findtext('ExperimentType')}")
print(f"Start DateTime: {exp_info.findtext('StartDateTime')}")
print(f"Machine:        {exp_info.findtext('MachineName')}")
print(f"Sensor Name:    {exp_info.findtext('SensorName')}")
print(f"Sensor Type:    {exp_info.findtext('SensorType')}")
print()

# Find all steps
steps = root.findall('.//KineticsData/Step')
print(f"TOTAL STEPS: {len(steps)}")
print("-" * 80)

# Function to decode Base64 data
def decode_base64_floats(base64_string, num_points):
    """Decode Base64-encoded float array"""
    if not base64_string:
        return np.array([])

    # Decode base64 to binary
    binary_data = base64.b64decode(base64_string)

    # Unpack as floats (little-endian, 4 bytes each)
    float_format = f'<{num_points}f'
    floats = struct.unpack(float_format, binary_data)

    return np.array(floats)

# Analyze first few steps in detail
print("\nDETAILED STEP ANALYSIS")
print("=" * 80)

for i, step in enumerate(steps[:5], 1):
    print(f"\nSTEP {i}")
    print("-" * 80)

    # Get step metadata
    common_data = step.find('CommonData')
    step_type = step.findtext('StepType')
    step_name = step.findtext('StepName')
    sample_id = common_data.findtext('SampleID')
    sample_location = common_data.findtext('SampleLocation')
    well_type = common_data.findtext('WellType')
    concentration = common_data.findtext('Concentration')
    conc_units = common_data.findtext('ConcentrationUnits')
    actual_time = step.findtext('ActualTime')

    print(f"Step Type:      {step_type}")
    print(f"Step Name:      {step_name}")
    print(f"Sample ID:      {sample_id}")
    print(f"Location:       Well {sample_location}")
    print(f"Well Type:      {well_type}")
    print(f"Concentration:  {concentration} {conc_units}")
    print(f"Actual Time:    {actual_time} seconds")

    # Get time series data
    x_data_elem = step.find('AssayXData')
    y_data_elem = step.find('AssayYData')

    if x_data_elem is not None and y_data_elem is not None:
        num_points = int(x_data_elem.get('Points', 0))

        print(f"\nTIME SERIES DATA:")
        print(f"  Data Points:  {num_points}")

        # Show raw Base64 (first 60 chars)
        x_base64 = x_data_elem.text
        y_base64 = y_data_elem.text
        print(f"  X Base64 (first 60 chars): {x_base64[:60]}...")
        print(f"  Y Base64 (first 60 chars): {y_base64[:60]}...")

        # Decode to floats
        time_array = decode_base64_floats(x_base64, num_points)
        response_array = decode_base64_floats(y_base64, num_points)

        print(f"\n  DECODED VALUES:")
        print(f"  First 10 time points (seconds):")
        print(f"    {time_array[:10]}")
        print(f"  First 10 response values (nm):")
        print(f"    {response_array[:10]}")

        print(f"\n  STATISTICS:")
        print(f"    Time range:     {time_array.min():.2f} - {time_array.max():.2f} seconds")
        print(f"    Response range: {response_array.min():.4f} - {response_array.max():.4f} nm")
        print(f"    Mean response:  {response_array.mean():.4f} nm")
        print(f"    Std response:   {response_array.std():.4f} nm")

# Find and analyze Loading step (typically step 7 in this file)
print("\n" + "=" * 80)
print("LOADING STEP ANALYSIS (Antibody Loading)")
print("=" * 80)

loading_step = None
for i, step in enumerate(steps, 1):
    if step.findtext('StepType') == 'LOADING':
        loading_step = step
        print(f"Found Loading step at position {i}")
        break

if loading_step:
    common_data = loading_step.find('CommonData')
    sample_id = common_data.findtext('SampleID')
    concentration = common_data.findtext('Concentration')
    conc_units = common_data.findtext('ConcentrationUnits')
    actual_time = loading_step.findtext('ActualTime')

    print(f"\nAntibody: {sample_id}")
    print(f"Concentration: {concentration} {conc_units}")
    print(f"Duration: {actual_time} seconds")

    # Decode data
    x_data_elem = loading_step.find('AssayXData')
    y_data_elem = loading_step.find('AssayYData')
    num_points = int(x_data_elem.get('Points', 0))

    time_array = decode_base64_floats(x_data_elem.text, num_points)
    response_array = decode_base64_floats(y_data_elem.text, num_points)

    print(f"\nTime series: {num_points} points")
    print(f"Time range: {time_array[0]:.2f} - {time_array[-1]:.2f} seconds")
    print(f"Response range: {response_array.min():.4f} - {response_array.max():.4f} nm")
    print(f"Signal increase: {response_array[-1] - response_array[0]:.4f} nm")

    # Show evenly spaced samples
    indices = np.linspace(0, len(time_array)-1, 20, dtype=int)
    print(f"\nEvenly spaced samples (every ~{len(time_array)//20} points):")
    print(f"{'Index':<8} {'Time (s)':<12} {'Response (nm)':<15}")
    print("-" * 40)
    for idx in indices:
        print(f"{idx:<8} {time_array[idx]:<12.2f} {response_array[idx]:<15.4f}")

# Summary of all steps
print("\n" + "=" * 80)
print("SUMMARY OF ALL STEPS")
print("=" * 80)
print(f"{'#':<4} {'Step Type':<20} {'Step Name':<20} {'Sample ID':<25} {'Points':<8}")
print("-" * 80)

for i, step in enumerate(steps, 1):
    common_data = step.find('CommonData')
    step_type = step.findtext('StepType')
    step_name = step.findtext('StepName')
    sample_id = common_data.findtext('SampleID')

    x_data_elem = step.find('AssayXData')
    num_points = int(x_data_elem.get('Points', 0)) if x_data_elem is not None else 0

    print(f"{i:<4} {step_type:<20} {step_name:<20} {sample_id:<25} {num_points:<8}")

print("\n" + "=" * 80)
print("DECODING DEMONSTRATION COMPLETE")
print("=" * 80)
print("\nKEY TAKEAWAYS:")
print("1. FRD files are XML with Base64-encoded binary float data")
print("2. Each step contains time (X) and response (Y) arrays")
print("3. Data is decoded: Base64 -> Binary -> IEEE 754 Floats -> NumPy arrays")
print("4. Typical experiment has multiple cycles of regeneration, loading, and binding")
print("5. Loading step shows antibody binding to sensor")
print("6. Response measured in nanometers (nm) of optical thickness change")
print()
