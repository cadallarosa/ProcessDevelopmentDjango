import os
import pandas as pd

# Original base directory
base_directory = r"S:\Shared\Chris Dallarosa\CE SDS Raw Data\New Imports"

# New base directory to replace in the paths
new_base_directory = r"C:\32Karat\projects\IgG Purity\Data\Raw Data\2025"

# Ensure base directory exists
if not os.path.exists(base_directory):
    raise ValueError(f"Base directory not found: {base_directory}")

# Collect and replace paths
dat_files = []
for root, dirs, files in os.walk(base_directory):
    for file in files:
        if file.lower().endswith(".dat"):
            full_path = os.path.join(root, file)
            relative_path = os.path.relpath(full_path, base_directory)
            new_path = os.path.join(new_base_directory, relative_path)
            dat_files.append(new_path)
        else:
            print(f"Skipping non-dat file: {file}")

# Create a DataFrame
df = pd.DataFrame(dat_files, columns=[".dat File Paths"])

# Output Excel
output_file = "dat_files_list.xlsx"
df.to_excel(output_file, index=False)

print(f"✅ Rebased {len(dat_files)} .dat file paths. Output written to {output_file}")