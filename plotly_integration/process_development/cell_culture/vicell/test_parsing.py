# Comprehensive Sample Parser - Run this in Django console: python manage.py shell

import re
from django.db import transaction
from plotly_integration.models import ViCellData


def parse_sample_id_complete(sample_id):
    """
    Complete parser that extracts:
    - Project ID: SI-##Letter# (e.g., SI-50E15, SI-126C2, SI-139R8)
    - Clone ID: #letter## (e.g., 1B2, 25H8, 49T5)
    - Experiment: E## (first char or after space)
    - Day: D## (after E or before space)
    - Reactor Type & Number: BRX/SF + number
    - Special markers

    Based on real data patterns like:
    - SI-50E15 P9 6D8
    - E58 SI49T5 1B2 D1 BXR2
    - SI-82P6 E19D03SF05
    - E581B2 D6PF BXR2
    """

    parsed_info = {
        'project_id': None,
        'clone_id': None,
        'experiment': None,
        'day': None,
        'reactor_type': None,
        'reactor_number': None,
        'special': None,
        'sample_type': 3  # Default to uncategorized
    }

    if not sample_id:
        return parsed_info

    sample_id_str = str(sample_id).strip().upper()

    # Step 1: Extract Project ID (SI-##Letter# or SI##Letter#)
    project_match = re.search(r'SI-?(\d+[A-Z]+\d*)', sample_id_str)
    if project_match:
        parsed_info['project_id'] = f"SI-{project_match.group(1)}"

    # Step 2: Extract Clone ID (#letter##)
    # Look for patterns like 1B2, 25H8, 49T5 - but be careful not to match reactor numbers
    clone_match = re.search(r'\b(\d+[A-Z]+\d+)\b', sample_id_str)
    if clone_match:
        # Make sure it's not a reactor pattern (BRX, BXR, etc.)
        potential_clone = clone_match.group(1)
        if not re.match(r'(BRX|BXR|BR|SF|STR)\d+', potential_clone):
            parsed_info['clone_id'] = potential_clone

    # Step 3: Extract Experiment (E## - first char or after space)
    # Priority: E at start, then E after space
    exp_match = re.match(r'^E(\d+)', sample_id_str)  # E at start
    if not exp_match:
        exp_match = re.search(r'\s+E(\d+)', sample_id_str)  # E after space

    if exp_match:
        parsed_info['experiment'] = f"E{exp_match.group(1)}"
        experiment_num = exp_match.group(1)

        # Step 4: Extract Day - only look for D immediately after this E or in close context
        # Must be D## that makes sense with the E we found
        e_pos = exp_match.start()
        e_end = exp_match.end()

        # Look for D immediately after E (E##D##)
        day_match = re.search(r'E' + experiment_num + r'D(\d+)', sample_id_str)

        if not day_match:
            # Look for D in the section after this E, but before any reactor info
            remaining_str = sample_id_str[e_end:]
            # Find D that comes before reactor info
            day_match = re.search(r'D(\d+)(?=.*(?:BXR|BRX|BR|SF|STR))', remaining_str)

        if day_match:
            parsed_info['day'] = int(day_match.group(1))

    # Step 5: Extract Reactor Type and Number
    reactor_patterns = [
        r'(BXR)(\d+)',  # BXR06
        r'(BRX)(\d+)',  # BRX02
        r'(BR)(\d+)',  # BR05
        r'(SF)(\d+)',  # SF13
        r'(STR)(\d+)'  # STR03
    ]

    for pattern in reactor_patterns:
        reactor_match = re.search(pattern, sample_id_str)
        if reactor_match:
            reactor_type = reactor_match.group(1)
            reactor_number = int(reactor_match.group(2))

            # Standardize reactor types: BXR/BR -> BRX, SF stays SF
            if reactor_type in ['BXR', 'BR']:
                parsed_info['reactor_type'] = 'BRX'
            else:
                parsed_info['reactor_type'] = reactor_type

            parsed_info['reactor_number'] = reactor_number
            break

    # Step 6: Extract Special markers
    special_match = re.search(r'(PRECUT|PREFEED|POSTFEED|PREINOC|POSTINOC|PRE|POST|UP|CLD)', sample_id_str)
    if special_match:
        parsed_info['special'] = special_match.group(1)

    # Step 7: Set sample type
    if parsed_info['experiment']:
        parsed_info['sample_type'] = 1  # E samples are UP
    elif parsed_info['special'] == 'CLD':
        parsed_info['sample_type'] = 2  # CLD
    # else stays 3 (uncategorized)

    return parsed_info


def parse_all_sample_ids_complete():
    """
    Parse ALL sample_id values with the complete parser.
    Extracts Project ID, Clone ID, Experiment, Day, Reactor info, and Special markers.
    """

    # Get all records
    all_records = ViCellData.objects.all()
    total_count = all_records.count()

    print(f"Processing {total_count} records with complete parser...")
    print("Extracting: Project ID, Clone ID, Experiment, Day, Reactor, Special markers")
    print("-" * 70)

    updated_count = 0
    batch_size = 1000

    # Statistics
    stats = {
        'parsed_experiments': 0,
        'found_project_ids': 0,
        'found_clone_ids': 0,
        'found_reactors': 0,
        'cleared_records': 0
    }

    # Process in batches for better performance
    for i in range(0, total_count, batch_size):
        batch = all_records[i:i + batch_size]
        batch_updates = []

        for record in batch:
            # Parse the sample_id
            parsed = parse_sample_id_complete(record.sample_id)

            # Always update to ensure we clear old incorrect data
            record.experiment = parsed['experiment']
            record.day = parsed['day']
            record.reactor_type = parsed['reactor_type']
            record.reactor_number = parsed['reactor_number']
            record.special = parsed['special']
            record.sample_type = parsed['sample_type']

            # Note: You'll need to add project_id and clone_id fields to your model
            # record.project_id = parsed['project_id']
            # record.clone_id = parsed['clone_id']

            batch_updates.append(record)
            updated_count += 1

            # Update statistics
            if parsed['experiment']:
                stats['parsed_experiments'] += 1
            if parsed['project_id']:
                stats['found_project_ids'] += 1
            if parsed['clone_id']:
                stats['found_clone_ids'] += 1
            if parsed['reactor_type']:
                stats['found_reactors'] += 1

            # Show results (limit output to avoid spam)
            if any(parsed[key] is not None for key in ['experiment', 'day', 'reactor_type', 'reactor_number']) or \
                    parsed['project_id'] or parsed['clone_id']:
                if updated_count <= 100:  # Show first 100 detailed results
                    print(f"{record.sample_id}")
                    print(
                        f"  -> project:{parsed['project_id']}, clone:{parsed['clone_id']}, exp:{parsed['experiment']}, day:{parsed['day']}, reactor:{parsed['reactor_type']}{parsed['reactor_number']}, special:{parsed['special']}")
            else:
                stats['cleared_records'] += 1
                if stats['cleared_records'] <= 20:  # Show first 20 cleared
                    print(f"{record.sample_id} -> CLEARED")

        # Bulk update this batch
        if batch_updates:
            with transaction.atomic():
                ViCellData.objects.bulk_update(
                    batch_updates,
                    ['experiment', 'day', 'reactor_type', 'reactor_number', 'special', 'sample_type']
                    # Add 'project_id', 'clone_id' when you add those fields to model
                )

        # Progress update
        processed = min(i + batch_size, total_count)
        if processed % 5000 == 0:  # Every 5000 records
            print(f"Processed: {processed}/{total_count}")

    print("\n" + "=" * 70)
    print("COMPLETE PARSING FINISHED!")
    print(f"Total records: {total_count}")
    print(f"Found experiments (E##): {stats['parsed_experiments']}")
    print(f"Found project IDs (SI-##): {stats['found_project_ids']}")
    print(f"Found clone IDs (#Letter#): {stats['found_clone_ids']}")
    print(f"Found reactor info: {stats['found_reactors']}")
    print(f"Cleared (no pattern): {stats['cleared_records']}")
    print("=" * 70)


def test_complete_parser():
    """Test the complete parser with various real patterns"""
    test_cases = [
        # Real examples from your data
        "SI50E15 P9 6D8",  # SI without dash
        "SI-126C2 P2D4",  # SI with dash
        "SI139R8_1 P6D4",  # SI without dash
        "E58 SI49T5 1B2 D1 BXR2",
        "SI-82P6 E19D03SF05",
        "E581B2 D6PF BXR2",
        "E58 1B2 D7 BXR6",
        "SI49T5 1B2 P6D3 F1",
        "169R1 FB D1403",

        # Edge cases
        "SI-83E9 E18D02BRX02",  # Multiple E numbers
        "E43D07BRX03 PRECUT",

        # Should be cleared
        "RANDOM SAMPLE",
        "123 TEST",
    ]

    print("Testing Complete Parser:")
    print("=" * 70)
    print("Format: project_id | clone_id | experiment | day | reactor | special")
    print("-" * 70)

    for sample_id in test_cases:
        parsed = parse_sample_id_complete(sample_id)

        # Build reactor info string
        reactor_info = ""
        if parsed['reactor_type'] and parsed['reactor_number']:
            reactor_info = f"{parsed['reactor_type']}{parsed['reactor_number']}"

        result_line = f"{parsed['project_id'] or 'None':<12} | {parsed['clone_id'] or 'None':<8} | {parsed['experiment'] or 'None':<10} | {str(parsed['day'] or 'None'):<3} | {reactor_info:<6} | {parsed['special'] or ''}"

        if any(parsed[key] is not None for key in ['project_id', 'clone_id', 'experiment', 'day', 'reactor_type']):
            print(f"✅ '{sample_id}'")
            print(f"   {result_line}")
        else:
            print(f"❌ '{sample_id}' -> CLEARED")
        print()


# MAIN FUNCTION TO RUN
def parse_all_sample_ids():
    """
    Main function to parse all sample IDs with the comprehensive parser.
    Run this in Django console: parse_all_sample_ids()
    """
    return parse_all_sample_ids_complete()


# Quick test function
def test_parser():
    """Quick test of the parser"""
    return test_complete_parser()

# Just run this:
# parse_all_sample_ids()