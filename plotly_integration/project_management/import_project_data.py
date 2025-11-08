"""
One-time script to import project data from Excel into the Project model.
File: S:\\Shared\\DjangoRawData\\ProjectManagement\\PE_coformulation_production_forecast.xlsx
"""

import os
import sys
import django
import pandas as pd
from datetime import datetime

# Setup Django environment
sys.path.append(r'/')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
django.setup()

from plotly_integration.models import Project
from django.contrib.auth.models import User

# Path to the Excel file
EXCEL_PATH = r'S:\Shared\DjangoRawData\ProjectManagement\PE_coformulation_production_forecast.xlsx'


def parse_date(date_value):
    """Parse date from Excel - handles various formats."""
    if pd.isna(date_value):
        return None

    if isinstance(date_value, pd.Timestamp):
        return date_value.date()

    if isinstance(date_value, str):
        # Try common date formats
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d']:
            try:
                return datetime.strptime(date_value, fmt).date()
            except ValueError:
                continue

    return None


def import_projects():
    """Import project data from Excel into the database."""
    print("=" * 80)
    print("IMPORTING PROJECT DATA FROM FULL_DETAILS SHEET")
    print("=" * 80)

    # Read the Excel file - using 'full_details' sheet for comprehensive data
    df = pd.read_excel(EXCEL_PATH, sheet_name='full_details')

    print(f"\nFound {len(df)} rows to import")
    print(f"Columns available: {df.columns.tolist()}\n")

    # Get or create a default user for imports
    default_user, _ = User.objects.get_or_create(
        username='data_import',
        defaults={'first_name': 'Data', 'last_name': 'Import'}
    )

    imported_count = 0
    updated_count = 0
    error_count = 0

    for idx, row in df.iterrows():
        try:
            # Extract data from row based on actual Excel column names
            molecule_id = str(row.get('Molecule ID', ''))

            if not molecule_id or pd.isna(molecule_id) or molecule_id == 'nan':
                print(f"Row {idx}: Skipping - no molecule ID")
                continue

            # Parse priority set (handle NaN)
            priority_set = row.get('Priority Set', 1)
            if pd.isna(priority_set):
                priority_set = 1
            else:
                priority_set = int(priority_set)

            # Parse dates from full_details sheet
            creation_date = parse_date(row.get('Molecule Creation Date'))
            cloning_finish_date = parse_date(row.get('Cloning Finish Date'))

            # Use 'Purification Date' if available, otherwise 'Finish Purification'
            purification_finish_date = parse_date(row.get('Purification Date'))
            if not purification_finish_date:
                purification_finish_date = parse_date(row.get('Finish Purification'))

            # Build notes from SIP information
            notes_parts = []
            for sip_num in [1, 2, 3]:
                sip_status = row.get(f'SIP-{sip_num}')
                sip_est_date = parse_date(row.get(f'SIP-{sip_num} Estimated Date'))
                sip_finish_date = parse_date(row.get(f'SIP-{sip_num} Finish Date'))

                if pd.notna(sip_status) or sip_est_date or sip_finish_date:
                    sip_info = f"SIP-{sip_num}: {sip_status if pd.notna(sip_status) else 'N/A'}"
                    if sip_est_date:
                        sip_info += f" (Est: {sip_est_date})"
                    if sip_finish_date:
                        sip_info += f" (Finished: {sip_finish_date})"
                    notes_parts.append(sip_info)

            # Add other milestone information
            tr_date = parse_date(row.get('TR Date'))
            trans_date = parse_date(row.get('Trans. Date'))
            est_tr_date = parse_date(row.get('Estimated TR Date'))
            est_trans_date = parse_date(row.get('Estimated Trans. Date'))
            est_pur_date = parse_date(row.get('Estimated Pur. Date'))

            if tr_date:
                notes_parts.append(f"TR Date: {tr_date}")
            elif est_tr_date:
                notes_parts.append(f"Estimated TR Date: {est_tr_date}")

            if trans_date:
                notes_parts.append(f"Trans. Date: {trans_date}")
            elif est_trans_date:
                notes_parts.append(f"Estimated Trans. Date: {est_trans_date}")

            if est_pur_date:
                notes_parts.append(f"Estimated Pur. Date: {est_pur_date}")

            notes = "\n".join(notes_parts)

            # Prepare project data
            project_data = {
                'molecule_id': molecule_id,
                'priority_set': priority_set,
                'status': 'Active',  # Default status
                'creation_date': creation_date,
                'cloning_finish_date': cloning_finish_date,
                'purification_finish_date': purification_finish_date,
                'notes': notes,
                'created_by': default_user,
                'assigned_to': default_user,
            }

            # Create or update project
            project, created = Project.objects.update_or_create(
                molecule_id=molecule_id,
                defaults=project_data
            )

            if created:
                imported_count += 1
                print(f"Row {idx}: Created project {molecule_id} (Priority: {priority_set})")
            else:
                updated_count += 1
                print(f"Row {idx}: Updated project {molecule_id} (Priority: {priority_set})")

        except Exception as e:
            error_count += 1
            print(f"Row {idx}: ERROR - {str(e)}")
            import traceback
            traceback.print_exc()
            continue

    print("\n" + "=" * 80)
    print("IMPORT SUMMARY")
    print("=" * 80)
    print(f"Created: {imported_count}")
    print(f"Updated: {updated_count}")
    print(f"Errors: {error_count}")
    print(f"Total processed: {imported_count + updated_count}")


if __name__ == '__main__':
    import_projects()
