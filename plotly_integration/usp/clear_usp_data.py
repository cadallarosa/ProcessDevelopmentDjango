"""
Script to clear USP Experiments, Seed Trains, and Vessels from database
WARNING: This will permanently delete all data in these tables
"""

import os
import sys
import django

# Setup Django environment
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
django.setup()

from plotly_integration.models import USPExperiment, USPProcessStep, USPVessel, USPSeedTrain


def clear_usp_data():
    """Clear all USP data from database"""

    print("=" * 60)
    print("USP DATA CLEANUP SCRIPT")
    print("=" * 60)
    print("\nWARNING: This will permanently delete the following data:")
    print("  - All USP Experiments")
    print("  - All USP Process Steps")
    print("  - All USP Seed Trains")
    print("  - All USP Vessels (Fed Batch)")
    print("\nThis action CANNOT be undone!")
    print("=" * 60)

    # Get current counts
    experiment_count = USPExperiment.objects.count()
    step_count = USPProcessStep.objects.count()
    seed_train_count = USPSeedTrain.objects.count()
    vessel_count = USPVessel.objects.count()

    print(f"\nCurrent database counts:")
    print(f"  - Experiments: {experiment_count}")
    print(f"  - Process Steps: {step_count}")
    print(f"  - Seed Trains: {seed_train_count}")
    print(f"  - Vessels: {vessel_count}")
    print()

    # Ask for confirmation
    response = input("Do you want to DELETE ALL this data? Type 'YES' to confirm: ")

    if response != "YES":
        print("\nOperation cancelled. No data was deleted.")
        return

    # Double confirmation
    response2 = input("\nAre you absolutely sure? Type 'DELETE ALL' to proceed: ")

    if response2 != "DELETE ALL":
        print("\nOperation cancelled. No data was deleted.")
        return

    print("\nDeleting data...")

    try:
        # Delete in order to respect foreign key constraints
        # Delete vessels first (they reference seed trains and process steps)
        deleted_vessels = USPVessel.objects.all().delete()
        print(f"✓ Deleted {deleted_vessels[0]} vessels")

        # Delete seed trains (they reference process steps)
        deleted_seed_trains = USPSeedTrain.objects.all().delete()
        print(f"✓ Deleted {deleted_seed_trains[0]} seed trains")

        # Delete process steps (they reference experiments)
        deleted_steps = USPProcessStep.objects.all().delete()
        print(f"✓ Deleted {deleted_steps[0]} process steps")

        # Delete experiments last
        deleted_experiments = USPExperiment.objects.all().delete()
        print(f"✓ Deleted {deleted_experiments[0]} experiments")

        print("\n" + "=" * 60)
        print("SUCCESS: All USP data has been cleared from the database!")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ ERROR: Failed to delete data")
        print(f"Error message: {str(e)}")
        import traceback
        traceback.print_exc()
        return


if __name__ == "__main__":
    clear_usp_data()
