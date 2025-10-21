"""
Fix models.py by removing incomplete OctetKinetics models and adding complete ones
"""
from pathlib import Path

# Read the complete model definitions
kinetics_models_file = Path(__file__).parent / "octet_kinetics_models.py"
with open(kinetics_models_file, 'r', encoding='utf-8') as f:
    kinetics_content = f.read()

# Extract just the model classes (remove the usage examples at the end)
# Find where the models end (before the usage examples comment block)
models_end = kinetics_content.find('# ============================================================================\n# USAGE EXAMPLES')
if models_end == -1:
    # No usage examples found, use everything
    models_only = kinetics_content
else:
    models_only = kinetics_content[:models_end].rstrip()

# Read the current models.py
models_file = Path(__file__).parent.parent.parent.parent / "models.py"
with open(models_file, 'r', encoding='utf-8') as f:
    current_content = f.read()

# Find where OctetKinetics models start
kinetics_start_marker = "# OCTET KINETICS MODELS (NEW OPTIMIZED ARCHITECTURE)"
kinetics_start = current_content.find(kinetics_start_marker)

if kinetics_start == -1:
    print("OctetKinetics models not found in models.py - adding them at the end")
    # Add header and models
    new_content = current_content.rstrip() + "\n\n"
    new_content += "# " + "=" * 76 + "\n"
    new_content += "# OCTET KINETICS MODELS (NEW OPTIMIZED ARCHITECTURE)\n"
    new_content += "# " + "=" * 76 + "\n"
    new_content += "# These are the new optimized models for kinetics data\n"
    new_content += "# Prefix: OctetKinetics (to distinguish from old Octet models)\n"
    new_content += "# Architecture: 2 tables instead of 4\n"
    new_content += "#   - OctetKineticsExperiment: One per experiment\n"
    new_content += "#   - OctetKineticsSensor: One per antibody×concentration (stores time series as JSON)\n"
    new_content += "# " + "=" * 76 + "\n\n"

    # Add the model classes (skip the header comments from the kinetics file)
    models_start = models_only.find('class OctetKineticsExperiment')
    new_content += models_only[models_start:].rstrip() + "\n"
else:
    print(f"Found OctetKinetics models at position {kinetics_start}")
    # Find the line before the marker
    lines_before_marker = current_content[:kinetics_start].rstrip()

    # Keep everything up to (but not including) the OctetKinetics section
    new_content = lines_before_marker + "\n\n"

    # Add the new section
    new_content += "# " + "=" * 76 + "\n"
    new_content += "# OCTET KINETICS MODELS (NEW OPTIMIZED ARCHITECTURE)\n"
    new_content += "# " + "=" * 76 + "\n"
    new_content += "# These are the new optimized models for kinetics data\n"
    new_content += "# Prefix: OctetKinetics (to distinguish from old Octet models)\n"
    new_content += "# Architecture: 2 tables instead of 4\n"
    new_content += "#   - OctetKineticsExperiment: One per experiment\n"
    new_content += "#   - OctetKineticsSensor: One per antibody×concentration (stores time series as JSON)\n"
    new_content += "# " + "=" * 76 + "\n\n"

    # Add the model classes (skip the header comments from the kinetics file)
    models_start = models_only.find('class OctetKineticsExperiment')
    new_content += models_only[models_start:].rstrip() + "\n"

# Backup original
backup_file = models_file.parent / "models.py.backup"
with open(backup_file, 'w', encoding='utf-8') as f:
    f.write(current_content)
print(f"Created backup: {backup_file}")

# Write the fixed content
with open(models_file, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"Successfully updated {models_file}")
print(f"Original length: {len(current_content)} characters")
print(f"New length: {len(new_content)} characters")
print(f"Lines added/modified: ~{len(new_content.splitlines()) - len(current_content.splitlines())}")
