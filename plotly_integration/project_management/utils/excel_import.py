"""
Excel Import Utility for Project Management Dashboard

One-time utility to import initial project data from Excel into database.
"""
import pandas as pd
from datetime import datetime
from typing import Dict, List, Tuple
from django.db import transaction
from plotly_integration.models import Project, ProjectMetrics
from ..config import EXCEL_FILE_PATH, EXCEL_COLUMNS
from .scoring_engine import calculate_and_update_metrics


def load_excel_data(file_path: str = None) -> pd.DataFrame:
    """
    Load project data from Excel file.

    Args:
        file_path: Path to Excel file (uses default from config if not provided)

    Returns:
        DataFrame with Excel data
    """
    if file_path is None:
        file_path = EXCEL_FILE_PATH

    try:
        df = pd.read_excel(file_path)
        print(f"✓ Loaded {len(df)} rows from Excel file")
        return df
    except FileNotFoundError:
        print(f"✗ Excel file not found: {file_path}")
        return pd.DataFrame()
    except Exception as e:
        print(f"✗ Error loading Excel file: {e}")
        return pd.DataFrame()


def clean_and_validate_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and validate Excel data before import.

    Args:
        df: Raw DataFrame from Excel

    Returns:
        Cleaned DataFrame
    """
    if df.empty:
        return df

    # Rename columns to match our model fields
    column_mapping = {v: k for k, v in EXCEL_COLUMNS.items()}
    df = df.rename(columns=column_mapping)

    # Convert date columns to datetime
    date_cols = ['creation_date', 'cloning_finish_date', 'purification_finish_date']
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Fill missing priority_set with default value of 2 (medium)
    if 'priority_set' in df.columns:
        df['priority_set'] = df['priority_set'].fillna(2).astype(int)

    # Remove rows without molecule_id
    if 'molecule_id' in df.columns:
        initial_count = len(df)
        df = df[df['molecule_id'].notna()]
        removed = initial_count - len(df)
        if removed > 0:
            print(f"  Removed {removed} rows without molecule ID")

    # Remove duplicates
    if 'molecule_id' in df.columns:
        initial_count = len(df)
        df = df.drop_duplicates(subset=['molecule_id'], keep='first')
        removed = initial_count - len(df)
        if removed > 0:
            print(f"  Removed {removed} duplicate rows")

    print(f"✓ Cleaned data: {len(df)} valid rows")
    return df


def import_projects_from_dataframe(df: pd.DataFrame,
                                   skip_existing: bool = True) -> Tuple[int, int, List[str]]:
    """
    Import projects from DataFrame into database.

    Args:
        df: Cleaned DataFrame with project data
        skip_existing: If True, skip projects that already exist

    Returns:
        Tuple of (created_count, skipped_count, error_messages)
    """
    created_count = 0
    skipped_count = 0
    error_messages = []

    if df.empty:
        return 0, 0, ["No data to import"]

    print(f"\nImporting {len(df)} projects...")

    for idx, row in df.iterrows():
        try:
            molecule_id = row.get('molecule_id')

            if not molecule_id:
                skipped_count += 1
                continue

            # Check if project already exists
            if skip_existing and Project.objects.filter(molecule_id=molecule_id).exists():
                skipped_count += 1
                continue

            # Prepare project data
            project_data = {
                'molecule_id': str(molecule_id),
                'priority_set': int(row.get('priority_set', 2)),
                'status': 'Active',  # Default status for new imports
            }

            # Add dates if available
            if pd.notna(row.get('creation_date')):
                project_data['creation_date'] = row['creation_date'].date()

            if pd.notna(row.get('cloning_finish_date')):
                project_data['cloning_finish_date'] = row['cloning_finish_date'].date()

            if pd.notna(row.get('purification_finish_date')):
                project_data['purification_finish_date'] = row['purification_finish_date'].date()

            # Create project
            with transaction.atomic():
                project = Project.objects.create(**project_data)

                # Calculate and create metrics
                calculate_and_update_metrics(project)

                created_count += 1

                if created_count % 10 == 0:
                    print(f"  Imported {created_count} projects...")

        except Exception as e:
            error_msg = f"Error importing {row.get('molecule_id', 'Unknown')}: {str(e)}"
            error_messages.append(error_msg)
            print(f"  ✗ {error_msg}")

    print(f"\n✓ Import complete: {created_count} created, {skipped_count} skipped, {len(error_messages)} errors")
    return created_count, skipped_count, error_messages


def import_excel_to_database(file_path: str = None,
                             skip_existing: bool = True) -> Dict[str, any]:
    """
    Main function to import Excel data into database.

    Args:
        file_path: Path to Excel file (uses default from config if not provided)
        skip_existing: If True, skip projects that already exist

    Returns:
        Dictionary with import results
    """
    print("=" * 60)
    print("PROJECT MANAGEMENT EXCEL IMPORT")
    print("=" * 60)

    # Load data
    df = load_excel_data(file_path)
    if df.empty:
        return {
            'success': False,
            'message': 'Failed to load Excel data',
            'created': 0,
            'skipped': 0,
            'errors': []
        }

    # Clean and validate
    df = clean_and_validate_data(df)
    if df.empty:
        return {
            'success': False,
            'message': 'No valid data after cleaning',
            'created': 0,
            'skipped': 0,
            'errors': []
        }

    # Import
    created, skipped, errors = import_projects_from_dataframe(df, skip_existing)

    success = created > 0

    return {
        'success': success,
        'message': f'Imported {created} projects successfully',
        'created': created,
        'skipped': skipped,
        'errors': errors,
        'total_rows': len(df)
    }


def preview_excel_data(file_path: str = None, n_rows: int = 5) -> pd.DataFrame:
    """
    Preview Excel data without importing.

    Args:
        file_path: Path to Excel file
        n_rows: Number of rows to preview

    Returns:
        DataFrame with preview data
    """
    df = load_excel_data(file_path)
    if df.empty:
        return df

    print("\n" + "=" * 60)
    print("EXCEL DATA PREVIEW")
    print("=" * 60)
    print(f"Total rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    print(f"\nFirst {n_rows} rows:")
    print(df.head(n_rows))

    return df.head(n_rows)


def clear_all_projects(confirm: bool = False):
    """
    Delete all projects from database.
    USE WITH CAUTION - this is irreversible!

    Args:
        confirm: Must be True to actually delete
    """
    if not confirm:
        print("✗ Must confirm deletion by passing confirm=True")
        return

    count = Project.objects.count()

    if count == 0:
        print("No projects to delete")
        return

    print(f"⚠️  WARNING: About to delete {count} projects!")
    print("This action cannot be undone.")

    user_input = input("Type 'DELETE' to confirm: ")

    if user_input == 'DELETE':
        Project.objects.all().delete()
        print(f"✓ Deleted {count} projects")
    else:
        print("✗ Deletion cancelled")


# ========================================
# Django Management Command Helper
# ========================================

def run_import_command():
    """
    Helper function that can be called from a Django management command.
    """
    print("\nStarting Excel import process...")

    # Preview first
    print("\n1. Previewing data...")
    preview_excel_data(n_rows=3)

    # Ask for confirmation
    user_input = input("\nProceed with import? (yes/no): ")

    if user_input.lower() not in ['yes', 'y']:
        print("Import cancelled")
        return

    # Run import
    print("\n2. Importing data...")
    result = import_excel_to_database(skip_existing=True)

    # Print results
    print("\n" + "=" * 60)
    print("IMPORT RESULTS")
    print("=" * 60)
    print(f"Success: {result['success']}")
    print(f"Message: {result['message']}")
    print(f"Created: {result['created']}")
    print(f"Skipped: {result['skipped']}")
    print(f"Errors: {len(result['errors'])}")

    if result['errors']:
        print("\nErrors:")
        for error in result['errors']:
            print(f"  - {error}")


if __name__ == "__main__":
    # This allows running the import directly from command line
    # python -m plotly_integration.project_management.utils.excel_import
    run_import_command()
