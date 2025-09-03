#!/usr/bin/env python
"""
Test the DataTable UP number mapping functionality
"""

# Simulate the DataTable data structure
test_table_data = [
    {'unit_number': 1, 'setup_name': 'Unit 1', 'up_number': 'TEST_UP_001'},
    {'unit_number': 2, 'setup_name': 'Unit 2', 'up_number': 'TEST_UP_002'},
    {'unit_number': 3, 'setup_name': 'Unit 3', 'up_number': 'TEST_UP_003'}
]

# Test the mapping extraction logic
def extract_up_mapping(up_table_data):
    """Extract UP mapping from DataTable data"""
    up_mapping = {}
    
    if up_table_data:
        print(f"Processing UP mapping from table...")
        for row in up_table_data:
            unit_no = row.get('unit_number')
            up_number = row.get('up_number', '').strip()
            if unit_no and up_number:
                up_mapping[unit_no] = up_number
                print(f"Unit {unit_no} -> UP {up_number}")
    
    return up_mapping

# Test the function
print("Testing DataTable UP number mapping:")
print("=====================================")

mapping = extract_up_mapping(test_table_data)
print(f"\nFinal mapping: {mapping}")

# Verify all units are mapped
expected_units = [1, 2, 3]
missing_units = [unit for unit in expected_units if unit not in mapping]

if not missing_units:
    print("✓ All units successfully mapped!")
else:
    print(f"✗ Missing mappings for units: {missing_units}")

print(f"\nMapped {len(mapping)} units:")
for unit, up in mapping.items():
    print(f"  Unit {unit}: {up}")