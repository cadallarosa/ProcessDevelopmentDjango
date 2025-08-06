# plotly_integration/tasks.py
# Combined Celery tasks for AKTA, Empower, and ViCell imports
import os
import hashlib
import json
import logging
import re
import requests
import time
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.db import IntegrityError, transaction
from plotly_integration.models import ViCellData
from plotly_integration.process_development.cell_culture.vicell.vicell_import_monitor import run_vicell_import
from plotly_integration.process_development.cell_culture.vicell.sample_id_parsing import parse_sample_id_complete
from pathlib import Path
from plotly_integration.models import NovaFlex2

logger = logging.getLogger(__name__)

# ========== AKTA CONFIGURATION ==========
NODEJS_SERVER = "http://localhost:3000"
CHECK_INTERVAL = 30  # Check every 30 seconds
MAX_WAIT_TIME = 3600  # Maximum 1 hour wait for traversal

# ========== EMPOWER CONFIGURATION ==========
EMPOWER_IMPORT_FOLDER = "/mnt/fs2/Chris Dallarosa/Database Imports"
EMPOWER_REPORTED_FOLDER = "/mnt/fs2/Chris Dallarosa/Database Imported"
EMPOWER_PROCESSED_FILES_LOG = os.path.join(settings.BASE_DIR, 'empower_processed_files.txt')

# ========== VICELL CONFIGURATION ==========
VICELL_FILE = "/mnt/fs2/Vi-Blue_Unsorted/Summary_DECEMBER.csv"  # Specific file path


# ========== AKTA TASKS ==========
@shared_task(name='plotly_integration.run_complete_pipeline' , bind=True)
def run_complete_import_pipeline():
    """
    Run the complete import pipeline:
    1. Start OPC UA traversal
    2. Wait for traversal to complete
    3. Run historical data import
    """
    results = {
        "start_time": datetime.now().isoformat(),
        "traversal": {},
        "import": {},
        "status": "started"
    }

    # Step 1 & 2: Traversal
    try:
        # Start the traversal
        print("🚀 Starting OPC UA traversal...")
        start_response = requests.post(
            f"{NODEJS_SERVER}/api/traverse/start-optimized",
            timeout=30
        )
        start_response.raise_for_status()

        if not start_response.json().get('success'):
            raise Exception("Failed to start traversal")

        results["traversal"]["started_at"] = datetime.now().isoformat()
        print("✅ Traversal started successfully")

        # Wait for traversal to complete
        print("⏳ Waiting for traversal to complete...")
        elapsed = 0
        last_processed = 0

        while elapsed < MAX_WAIT_TIME:
            time.sleep(CHECK_INTERVAL)
            elapsed += CHECK_INTERVAL

            try:
                status_response = requests.get(
                    f"{NODEJS_SERVER}/api/traverse/stats",
                    timeout=10
                )
                status_response.raise_for_status()
                stats = status_response.json()

                is_active = stats.get('active', False)
                processed = stats.get('processedFolders', 0)
                total = stats.get('totalFolders', 0)
                errors = stats.get('errors', 0)
                inserted = stats.get('insertedRecords', 0)

                # Check if manually stopped
                if stats.get('manuallyStopped', False):
                    print("⚠️ Traversal was manually stopped")
                    results["traversal"]["manually_stopped"] = True
                    results["status"] = "stopped"
                    return results

                # Log progress
                if processed != last_processed:
                    print(f"📊 Progress: {processed}/{total} folders, {inserted} records inserted, {errors} errors")
                    last_processed = processed

                if not is_active:
                    # Traversal completed!
                    results["traversal"]["completed_at"] = datetime.now().isoformat()
                    results["traversal"]["stats"] = stats
                    results["traversal"]["duration_seconds"] = elapsed
                    print(f"✅ Traversal completed! Processed {processed} folders, inserted {inserted} records")
                    break

            except Exception as e:
                print(f"⚠️ Error checking status: {e}")

        else:
            # Timeout reached
            results["error"] = f"Traversal did not complete within {MAX_WAIT_TIME} seconds"
            results["status"] = "timeout"
            return results

    except Exception as e:
        # Traversal failed
        print(f"❌ Traversal failed: {e}")
        results["traversal"]["error"] = str(e)
        results["status"] = "traversal_failed"
        return results

    # Step 3: Run the Python import
    print("\n🔄 Starting historical data import...")
    results["import"]["started_at"] = datetime.now().isoformat()

    try:
        # Import and run the function directly
        from plotly_integration.process_development.downstream_processing.akta.opcua_server.read_historical_data import \
            process_opcua_node_ids

        start_time = "2013-01-01T00:00:00"
        end_time = datetime.now().isoformat()

        # Run the import
        process_opcua_node_ids(start_time, end_time)

        results["import"]["completed_at"] = datetime.now().isoformat()
        results["import"]["status"] = "success"
        results["status"] = "completed"
        print("✅ Historical data import completed successfully")

    except Exception as e:
        results["import"]["error"] = str(e)
        results["import"]["status"] = "failed"
        results["status"] = "import_failed"
        print(f"❌ Import failed: {e}")

    results["completed_at"] = datetime.now().isoformat()

    # Log final summary
    duration = (datetime.fromisoformat(results["completed_at"]) -
                datetime.fromisoformat(results["start_time"])).total_seconds()
    print(f"\n{'=' * 60}")
    print(f"Pipeline completed in {duration:.1f} seconds")
    print(f"Status: {results['status']}")
    print(f"{'=' * 60}")

    return results


@shared_task(name='plotly_integration.run_import_only', bind=True)
def run_import_only(self):
    """
    Run only the Python import script.
    Use this when you already have traversal data and just want to import unprocessed records.
    """
    try:
        print("🚀 Starting OPC UA historical data import...")
        from plotly_integration.process_development.downstream_processing.akta.opcua_server.read_historical_data import process_opcua_node_ids
        from plotly_integration.models import AktaNodeIds

        # Check how many need import
        unimported_count = AktaNodeIds.objects.filter(imported=False).count()
        print(f"📊 Found {unimported_count} unimported records")

        if unimported_count == 0:
            return {
                "status": "success",
                "message": "No unimported records found",
                "timestamp": datetime.now().isoformat()
            }

        start_time = "2013-01-01T00:00:00"
        end_time = datetime.now().isoformat()

        # Run the import
        process_opcua_node_ids(start_time, end_time)

        # Check results
        still_unimported = AktaNodeIds.objects.filter(imported=False).count()
        imported_count = unimported_count - still_unimported

        return {
            "status": "success",
            "message": f"Imported {imported_count} records successfully",
            "processed": imported_count,
            "remaining": still_unimported,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        traceback.print_exc()

        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@shared_task(name='plotly_integration.run_traversal_only', bind=True)
def run_traversal_only():
    """
    Run only the traversal part.
    Use this to discover new OPC UA nodes without importing historical data.
    """
    try:
        print("🚀 Starting OPC UA traversal...")

        response = requests.post(
            f"{NODEJS_SERVER}/api/traverse/start-optimized",
            timeout=30
        )
        response.raise_for_status()

        if response.json().get('success'):
            print("✅ Traversal started successfully")
            return {
                "status": "started",
                "response": response.json(),
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "status": "error",
                "error": "Failed to start traversal",
                "response": response.json(),
                "timestamp": datetime.now().isoformat()
            }

    except Exception as e:
        print(f"❌ Failed to start traversal: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@shared_task(name='plotly_integration.check_traversal_status', bind=True)
def check_traversal_status():
    """Check current traversal status"""
    try:
        response = requests.get(
            f"{NODEJS_SERVER}/api/traverse/stats",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e), "timestamp": datetime.now().isoformat()}


@shared_task(name='plotly_integration.stop_traversal', bind=True)
def stop_traversal():
    """Stop the currently running traversal"""
    try:
        response = requests.post(
            f"{NODEJS_SERVER}/api/traverse/stop",
            timeout=10
        )
        response.raise_for_status()
        print("🛑 Traversal stop requested")
        return {"status": "stopped", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        return {"error": str(e), "timestamp": datetime.now().isoformat()}


@shared_task(name='plotly_integration.check_import_status', bind=True)
def check_import_status():
    """
    Check how many records need import.
    Useful for monitoring and deciding when to run imports.
    """
    from plotly_integration.models import AktaNodeIds, AktaResult

    total_nodes = AktaNodeIds.objects.count()
    imported_nodes = AktaNodeIds.objects.filter(imported=True).count()
    unimported_nodes = AktaNodeIds.objects.filter(imported=False).count()
    total_results = AktaResult.objects.count()

    percentage = round((imported_nodes / total_nodes * 100), 2) if total_nodes > 0 else 0

    status_msg = f"📊 Import Status: {imported_nodes}/{total_nodes} imported ({percentage}%)"
    if unimported_nodes > 0:
        status_msg += f" - {unimported_nodes} remaining"

    print(status_msg)

    return {
        "total_nodes": total_nodes,
        "imported": imported_nodes,
        "unimported": unimported_nodes,
        "percentage": percentage,
        "total_results": total_results,
        "status_message": status_msg,
        "timestamp": datetime.now().isoformat()
    }


@shared_task(name='plotly_integration.cleanup_old_results')
def cleanup_old_results(days_to_keep=30):
    """
    Optional task to clean up old task results from django_celery_results.
    Schedule this weekly to keep the database clean.
    """
    try:
        from django_celery_results.models import TaskResult
        from django.utils import timezone
        from datetime import timedelta

        cutoff_date = timezone.now() - timedelta(days=days_to_keep)

        # Count before deletion
        old_results = TaskResult.objects.filter(date_created__lt=cutoff_date)
        count = old_results.count()

        # Delete old results
        old_results.delete()

        print(f"🧹 Cleaned up {count} task results older than {days_to_keep} days")

        return {
            "status": "success",
            "deleted_count": count,
            "cutoff_date": cutoff_date.isoformat(),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


@shared_task(name='plotly_integration.health_check', bind=True)
def health_check():
    """
    Simple health check task to verify Celery is working.
    Can be scheduled every hour to ensure the system is running.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "message": "Celery worker is running"
    }


# ========== EMPOWER TASKS ==========
import shutil
from django.conf import settings
import plotly_integration.process_development.downstream_processing.empower.database.process_ars as process_ars
import plotly_integration.process_development.downstream_processing.empower.database.process_arw as process_arw
from plotly_integration.process_development.downstream_processing.empower.database.column_logbook import (
    populate_column_logbook,
    transfer_column_names,
    update_total_injections,
    assign_column_ids_to_samples,
    update_most_recent_injections,
    backfill_missing_pressure_data
)


def load_empower_processed_files():
    """Load list of already processed Empower files"""
    if os.path.exists(EMPOWER_PROCESSED_FILES_LOG):
        with open(EMPOWER_PROCESSED_FILES_LOG, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    return set()


def save_empower_processed_file(filename):
    """Mark an Empower file as processed"""
    with open(EMPOWER_PROCESSED_FILES_LOG, 'a') as f:
        f.write(f"{filename}\n")


@shared_task(name='plotly_integration.import_empower_files', bind=True)
def import_empower_files(self):
    """Import Empower .ars and .arw files"""

    # Get database name from settings
    db_name = settings.DATABASES['default']['NAME']

    # Check if import is already running
    if cache.get('empower_import_lock'):
        logger.warning("Empower import already in progress")
        return "Import already in progress"

    # Set lock
    cache.set('empower_import_lock', True, timeout=3600)  # 1 hour timeout

    try:
        # Update task state
        self.update_state(state='PROGRESS', meta={'current': 0, 'total': 100, 'status': 'Starting import...'})

        # Validate directories
        if not os.path.isdir(EMPOWER_IMPORT_FOLDER):
            raise Exception(f"Import folder '{EMPOWER_IMPORT_FOLDER}' does not exist")

        if not os.path.isdir(EMPOWER_REPORTED_FOLDER):
            raise Exception(f"Reported folder '{EMPOWER_REPORTED_FOLDER}' does not exist")

        if not os.path.isfile(db_name):
            raise Exception(f"Database file '{db_name}' does not exist")

        # Get list of files to process
        processed_files = load_empower_processed_files()
        all_files = os.listdir(EMPOWER_IMPORT_FOLDER)

        ars_files = [f for f in all_files if f.endswith('.ars') and f not in processed_files]
        arw_files = [f for f in all_files if f.endswith('.arw') and f not in processed_files]

        total_files = len(ars_files) + len(arw_files)

        if total_files == 0:
            return "No new files to process"

        logger.info(f"Found {len(ars_files)} .ars files and {len(arw_files)} .arw files to process")

        # Process .ars files
        # Note: The process_files function processes ALL files in the directory at once
        # So we only need to call it once, not in a loop
        if ars_files:
            self.update_state(state='PROGRESS', meta={'current': 10, 'total': 100,
                                                      'status': f'Processing {len(ars_files)} .ars files...'})
            process_ars.process_files(directory=EMPOWER_IMPORT_FOLDER, reported_folder=EMPOWER_REPORTED_FOLDER)

            # Mark all ars files as processed
            for filename in ars_files:
                save_empower_processed_file(filename)

        # Process .arw files
        # Similarly, process_files handles all files at once
        if arw_files:
            self.update_state(state='PROGRESS', meta={'current': 40, 'total': 100,
                                                      'status': f'Processing {len(arw_files)} .arw files...'})
            process_arw.process_files(directory=EMPOWER_IMPORT_FOLDER, reported_folder=EMPOWER_REPORTED_FOLDER)

            # Mark all arw files as processed
            for filename in arw_files:
                save_empower_processed_file(filename)

        # Run column processing functions AFTER file import completes
        self.update_state(state='PROGRESS', meta={'current': 70, 'total': 100, 'status': 'Processing column data...'})

        logger.info("Running column processing functions...")
        populate_column_logbook()
        transfer_column_names()
        update_total_injections()
        assign_column_ids_to_samples()
        update_most_recent_injections()
        backfill_missing_pressure_data()

        # Update last import time
        cache.set('empower_last_import', timezone.now().isoformat())

        # Complete
        self.update_state(state='SUCCESS', meta={'current': 100, 'total': 100, 'status': 'Import completed'})

        result_message = f"File import completed successfully! Processed {total_files} files ({len(ars_files)} .ars, {len(arw_files)} .arw)"
        logger.info(result_message)
        return result_message

    except Exception as e:
        logger.error(f"Empower import error: {str(e)}")
        self.update_state(state='FAILURE', meta={'exc': str(e)})
        raise

    finally:
        # Always remove lock
        cache.delete('empower_import_lock')


def get_empower_import_status():
    """Get current Empower import status"""
    status = {
        'folder': EMPOWER_IMPORT_FOLDER,
        'reported_folder': EMPOWER_REPORTED_FOLDER,
        'last_import': cache.get('empower_last_import'),
        'is_locked': cache.get('empower_import_lock') is not None
    }

    if os.path.isdir(EMPOWER_IMPORT_FOLDER):
        processed_files = load_empower_processed_files()
        all_files = os.listdir(EMPOWER_IMPORT_FOLDER)

        status['pending_ars'] = len([f for f in all_files if f.endswith('.ars') and f not in processed_files])
        status['pending_arw'] = len([f for f in all_files if f.endswith('.arw') and f not in processed_files])
        status['total_processed'] = len(processed_files)
        status['files_exist'] = status['pending_ars'] > 0 or status['pending_arw'] > 0
    else:
        status['error'] = 'Import folder not accessible'
        status['files_exist'] = False

    return status


def reset_empower_import_tracking():
    """
    Reset Empower import tracking.
    This clears the processed files log and cache.
    """
    # Clear processed files log
    if os.path.exists(EMPOWER_PROCESSED_FILES_LOG):
        os.remove(EMPOWER_PROCESSED_FILES_LOG)

    # Clear cache
    cache.delete('empower_last_import')
    cache.delete('empower_import_lock')

    return "Empower import tracking reset"

# ========== VICELL TASKS ==========
@shared_task(name='plotly_integration.import_vicell_data', bind=True)
def import_vicell_data(self):
    """
    Celery task to import ViCell data using the import function from vicell_import_monitor.
    """
    return run_vicell_import()


# ========== UTILITY FUNCTIONS ==========
def get_vicell_import_status():
    """Get current ViCell import status"""
    status = {
        'file_path': VICELL_FILE,
        'file_exists': os.path.exists(VICELL_FILE),
        'last_import': cache.get('vicell_last_import'),
        'is_locked': cache.get('vicell_import_lock') is not None,
        'database_info': {}
    }

    try:
        # Get database info
        total_records = ViCellData.objects.count()
        latest_record = ViCellData.objects.order_by('-date_time').first()

        status['database_info'] = {
            'total_records': total_records,
            'latest_datetime': latest_record.date_time.isoformat() if latest_record else None
        }

    except Exception as e:
        status['database_info'] = {'error': str(e)}

    return status


def reset_vicell_import_tracking():
    """
    Reset ViCell import tracking.
    This clears the cache for fresh start.
    """
    cache.delete('vicell_last_import')
    cache.delete('vicell_import_lock')
    return "ViCell import tracking reset"

@shared_task(name='plotly_integration.import_vicell_data_complete', bind=True)
def import_vicell_data_complete(self):
    """
    Complete ViCell data import - imports ALL records from file, skipping only duplicates.
    Uses the same logic as the manual import app to ensure all records are processed.
    """
    lock_id = 'vicell_import_lock'

    # Try to acquire lock
    if not cache.add(lock_id, 'locked', 300):  # 5 minute timeout
        logger.info("ViCell import task already running")
        return {
            "status": "error",
            "message": "ViCell import task already running"
        }

    try:
        # Verify file exists
        if not os.path.exists(VICELL_FILE):
            logger.error(f"ViCell file not found: {VICELL_FILE}")
            return {
                "status": "error",
                "message": f"ViCell file not found: {VICELL_FILE}"
            }

        filename = os.path.basename(VICELL_FILE)
        logger.info(f"Processing complete file: {filename}")

        # Update task state
        self.update_state(state='PROGRESS', meta={'message': 'Reading file...'})

        # Read and process the file using the same logic as manual import
        df = pd.read_csv(VICELL_FILE)
        logger.info(f"Total rows in file: {len(df)}")

        # Column mapping (same as manual import app)
        column_mapping = {
            "Sample ID": "sample_id",
            "Analysis date/time": "date_time",
            "Cell count": "cell_count",
            "Viable cells": "viable_cells",
            "Total (x10^6) cells/mL": "total_cells_per_ml",
            "Viable (x10^6) cells/mL": "viable_cells_per_ml",
            "Viability (%)": "viability",
            "Average diameter (µm)": "average_diameter",
            "Average viable diameter (µm)": "average_viable_diameter",
            "Average circularity": "average_circularity",
            "Average viable circularity": "average_viable_circularity"
        }

        # Select and rename columns
        relevant_columns = list(column_mapping.keys())
        available_columns = [col for col in relevant_columns if col in df.columns]
        df_cleaned = df[available_columns].copy()
        df_cleaned.rename(columns=column_mapping, inplace=True)

        # Convert date column to datetime
        df_cleaned["date_time"] = pd.to_datetime(df_cleaned["date_time"], errors="coerce")

        # Make datetimes timezone-aware (same as manual import)
        df_cleaned["date_time"] = df_cleaned["date_time"].apply(
            lambda x: timezone.make_aware(x, timezone.get_default_timezone())
            if pd.notna(x) and x.tzinfo is None else x
        )

        # Ensure numeric columns are properly converted
        numeric_columns = [
            "cell_count", "viable_cells", "total_cells_per_ml", "viable_cells_per_ml",
            "viability", "average_diameter", "average_viable_diameter",
            "average_circularity", "average_viable_circularity"
        ]
        for col in numeric_columns:
            if col in df_cleaned.columns:
                df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors="coerce")

        # Replace NaN values with None (same as manual import)
        df_cleaned = df_cleaned.replace({np.nan: None})

        # Update task state
        self.update_state(state='PROGRESS', meta={'message': 'Processing records...'})

        new_records = []
        skipped_records = []

        # Parse sample names using the comprehensive parser

        for idx, row in df_cleaned.iterrows():
            # Skip rows without valid date_time
            if pd.isna(row["date_time"]) or row["date_time"] is None:
                skipped_records.append(row["sample_id"])
                continue

            # Use the comprehensive parser
            parsed_sample = parse_sample_id_complete(row["sample_id"])

            new_records.append(ViCellData(
                sample_id=row["sample_id"],
                date_time=row["date_time"],
                cell_count=row.get("cell_count"),
                viable_cells=row.get("viable_cells"),
                total_cells_per_ml=row.get("total_cells_per_ml"),
                viable_cells_per_ml=row.get("viable_cells_per_ml"),
                viability=row.get("viability"),
                average_diameter=row.get("average_diameter"),
                average_viable_diameter=row.get("average_viable_diameter"),
                average_circularity=row.get("average_circularity"),
                average_viable_circularity=row.get("average_viable_circularity"),
                # Parsed fields from comprehensive parser
                experiment=parsed_sample["experiment"],
                day=parsed_sample["day"],
                reactor_type=parsed_sample["reactor_type"],
                reactor_number=parsed_sample["reactor_number"],
                special=parsed_sample["special"],
                sample_type=parsed_sample["sample_type"]  # Use parser's sample_type instead of row's
            ))

            # Update progress every 500 records
            if len(new_records) % 500 == 0:
                self.update_state(state='PROGRESS', meta={'message': f'Processed {len(new_records)} records...'})

        # Update task state
        self.update_state(state='PROGRESS', meta={'message': 'Importing to database...'})

        # Perform bulk insert (same logic as manual import)
        created_count = 0
        duplicate_samples = []

        if new_records:
            # Get existing sample IDs to check for duplicates
            existing_sample_ids = set(ViCellData.objects.values_list('sample_id', flat=True))

            # Separate new and duplicate records
            records_to_create = []
            for record in new_records:
                if record.sample_id in existing_sample_ids:
                    duplicate_samples.append(record.sample_id)
                else:
                    records_to_create.append(record)

            # Bulk create only truly new records
            if records_to_create:
                created_records = ViCellData.objects.bulk_create(records_to_create, ignore_conflicts=True)
                created_count = len(created_records)

        # Store detailed results in cache
        cache.set('vicell_last_import', {
            'timestamp': datetime.now().isoformat(),
            'task_id': self.request.id,
            'method': 'complete-file-import',
            'imported': created_count,
            'failed': 0,
            'skipped_invalid': len(skipped_records),
            'duplicates_skipped': len(duplicate_samples),
            'total_processed': len(new_records),
            'details': {
                'total_file_rows': len(df),
                'valid_records': len(new_records),
                'skipped_no_date': len(skipped_records),
                'duplicates': len(duplicate_samples)
            }
        }, 3600)

        # Build status message
        status_message = f"Complete import: {created_count} new records imported"
        if duplicate_samples:
            status_message += f", {len(duplicate_samples)} duplicates skipped"
        if skipped_records:
            status_message += f", {len(skipped_records)} invalid records skipped"

        logger.info(status_message)

        return {
            "status": "success",
            "message": status_message,
            "imported": created_count,
            "failed": 0,
            "skipped_invalid": len(skipped_records),
            "duplicates_skipped": len(duplicate_samples),
            "total_processed": len(new_records),
            "details": {
                "total_file_rows": len(df),
                "valid_records": len(new_records),
                "skipped_no_date": len(skipped_records),
                "duplicates": len(duplicate_samples)
            }
        }

    except Exception as e:
        error_msg = f"Fatal error in ViCell complete import: {str(e)}"
        logger.error(error_msg)
        return {
            "status": "error",
            "message": error_msg
        }

    finally:
        # Release lock
        cache.delete(lock_id)


# Legacy task name for backward compatibility
@shared_task(name='plotly_integration.check_and_import_vicell_files', bind=True)
def check_and_import_vicell_files(self):
    """Legacy task name - redirects to new simplified import"""
    return import_vicell_data.apply_async()

# ========== Nova Flex II ==========
# /mnt/windows-share/Results

@shared_task
def import_nova_flex2_files():
    """
    Scheduled task to import Nova Flex 2 files from mounted network folder
    """
    # Define source folders - modify these paths as needed
    source_folders = [
        '/mnt/windows-share/Results',  # Primary mount point
    ]

    results = {
        'total_processed': 0,
        'total_successful': 0,
        'total_failed': 0,
        'total_records_created': 0,
        'total_records_updated': 0,
        'errors': [],
        'processed_files': []
    }

    # Helper functions
    def parse_sample_id(sample_id):
        """Parse sample ID to extract experiment, day, reactor info, and special markers"""
        patterns = {
            'experiment': r'SI\d+P\d+',
            'day': r'D(\d+)',
            'reactor_type': r'(BR|STR)',
            'reactor_number': r'(?:BR|STR)(\d+)',
            'special': r'(UP|CLD)'
        }

        parsed_info = {
            'experiment': None,
            'day': None,
            'reactor_type': None,
            'reactor_number': None,
            'special': None,
            'sample_type': 3  # Default to uncategorized
        }

        if pd.isna(sample_id) or not sample_id:
            return parsed_info

        sample_id_str = str(sample_id).strip()

        # Extract experiment
        exp_match = re.search(patterns['experiment'], sample_id_str)
        if exp_match:
            parsed_info['experiment'] = exp_match.group(0)

        # Extract day
        day_match = re.search(patterns['day'], sample_id_str)
        if day_match:
            parsed_info['day'] = int(day_match.group(1))

        # Extract reactor type
        reactor_type_match = re.search(patterns['reactor_type'], sample_id_str)
        if reactor_type_match:
            parsed_info['reactor_type'] = reactor_type_match.group(0)

        # Extract reactor number
        reactor_num_match = re.search(patterns['reactor_number'], sample_id_str)
        if reactor_num_match:
            parsed_info['reactor_number'] = int(reactor_num_match.group(1))

        # Extract special markers (UP/CLD)
        special_match = re.search(patterns['special'], sample_id_str)
        if special_match:
            parsed_info['special'] = special_match.group(0)
            if parsed_info['special'] == 'UP':
                parsed_info['sample_type'] = 1
            elif parsed_info['special'] == 'CLD':
                parsed_info['sample_type'] = 2

        return parsed_info

    def clean_numeric(value):
        """Clean numeric values, handling NaN and non-numeric strings"""
        if pd.isna(value):
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def adjust_datetime(dt):
        """Adjust datetime by subtracting 7 hours"""
        if pd.isna(dt) or dt is None:
            return None
        return dt - timedelta(hours=7)

    def process_excel_file(file_path):
        """Process Nova Flex 2 Excel file"""
        df = pd.read_excel(file_path, engine='xlrd' if file_path.endswith('.xls') else None)
        df.columns = df.columns.str.strip()

        # Handle both old and new formats
        if 'Date & Time' in df.columns:
            column_mapping = {
                'Date & Time': 'date_time',
                'Sample ID': 'sample_id',
                'Gln': 'gln',
                'Glu': 'glu',
                'Gluc': 'gluc',
                'Lac': 'lac',
                'NH4+': 'nh4',
                'pH': 'pH',
                'PO2': 'po2',
                'PCO2': 'pco2',
                'Osm': 'osm'
            }
        else:
            column_mapping = {
                'Date/Time': 'date_time',
                'Sample ID': 'sample_id',
                'Gln (mM)': 'gln',
                'Glu (g/L)': 'glu',
                'Gluc (g/L)': 'gluc',
                'Lac (g/L)': 'lac',
                'NH4+ (mM)': 'nh4',
                'pH': 'pH',
                'pO2 (%)': 'po2',
                'pCO2 (%)': 'pco2',
                'Osm (mOsm/kg)': 'osm'
            }

        df.rename(columns=column_mapping, inplace=True)
        relevant_cols = list(column_mapping.values())
        df = df[[col for col in relevant_cols if col in df.columns]]

        # Convert numeric columns
        numeric_columns = ['gln', 'glu', 'gluc', 'lac', 'nh4', 'pH', 'po2', 'pco2', 'osm']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        if 'date_time' in df.columns:
            df['date_time'] = pd.to_datetime(df['date_time'], errors='coerce')
            # Adjust datetime by subtracting 7 hours
            df['date_time'] = df['date_time'].apply(adjust_datetime)

        return df

    def process_csv_file(file_path):
        """Process Nova Flex 2 CSV file"""
        df = pd.read_csv(file_path)
        df.columns = df.columns.str.strip()

        if 'Date & Time' in df.columns:
            column_mapping = {
                'Date & Time': 'date_time',
                'Sample ID': 'sample_id',
                'Gln': 'gln',
                'Glu': 'glu',
                'Gluc': 'gluc',
                'Lac': 'lac',
                'NH4+': 'nh4',
                'pH': 'pH',
                'PO2': 'po2',
                'PCO2': 'pco2',
                'Osm': 'osm'
            }
        elif 'Viable cells' in df.columns:
            return None  # Skip cell viability CSV
        else:
            column_mapping = {
                'Date/Time': 'date_time',
                'Sample ID': 'sample_id',
                'Gln (mM)': 'gln',
                'Glu (g/L)': 'glu',
                'Gluc (g/L)': 'gluc',
                'Lac (g/L)': 'lac',
                'NH4+ (mM)': 'nh4',
                'pH': 'pH',
                'pO2 (%)': 'po2',
                'pCO2 (%)': 'pco2',
                'Osm (mOsm/kg)': 'osm'
            }

        df.rename(columns=column_mapping, inplace=True)

        numeric_columns = ['gln', 'glu', 'gluc', 'lac', 'nh4', 'pH', 'po2', 'pco2', 'osm']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        if 'date_time' in df.columns:
            df['date_time'] = pd.to_datetime(df['date_time'], errors='coerce')
            # Adjust datetime by subtracting 7 hours
            df['date_time'] = df['date_time'].apply(adjust_datetime)

        return df

    # Process each source folder
    for source_folder in source_folders:
        if not os.path.exists(source_folder):
            results['errors'].append(f"Source folder not found: {source_folder}")
            continue

        # Create imported folder
        imported_folder = os.path.join(source_folder, "imported")
        os.makedirs(imported_folder, exist_ok=True)

        # Get all files
        excel_files = list(Path(source_folder).glob('*.xls')) + list(Path(source_folder).glob('*.xlsx'))
        csv_files = list(Path(source_folder).glob('*.csv'))
        all_files = excel_files + csv_files

        # Process each file
        for file_path in all_files:
            file_name = file_path.name

            # Skip if already in imported folder
            if 'imported' in str(file_path):
                continue

            try:
                # Process based on file type
                if file_path.suffix in ['.xls', '.xlsx']:
                    df = process_excel_file(str(file_path))
                else:  # CSV
                    df = process_csv_file(str(file_path))

                if df is None or df.empty:
                    continue

                # Import to database
                records_created = 0
                records_updated = 0

                with transaction.atomic():
                    for _, row in df.iterrows():
                        if pd.isna(row.get('sample_id', None)):
                            continue

                        # Parse sample ID
                        parsed_info = parse_sample_id(row['sample_id'])

                        # Prepare data
                        data = {
                            'date_time': row.get('date_time'),  # Already adjusted by -7 hours
                            'sample_id': row.get('sample_id'),
                            'sample_type': parsed_info['sample_type'],
                            'gln': clean_numeric(row.get('gln')),
                            'glu': clean_numeric(row.get('glu')),
                            'gluc': clean_numeric(row.get('gluc')),
                            'lac': clean_numeric(row.get('lac')),
                            'nh4': clean_numeric(row.get('nh4')),
                            'pH': clean_numeric(row.get('pH')),
                            'po2': clean_numeric(row.get('po2')),
                            'pco2': clean_numeric(row.get('pco2')),
                            'osm': clean_numeric(row.get('osm')),
                            'experiment': parsed_info['experiment'],
                            'day': parsed_info['day'],
                            'reactor_type': parsed_info['reactor_type'],
                            'reactor_number': parsed_info['reactor_number'],
                            'special': parsed_info['special']
                        }

                        if pd.isna(data['date_time']) or pd.isna(data['sample_id']):
                            continue

                        obj, created = NovaFlex2.objects.update_or_create(
                            date_time=data['date_time'],
                            sample_id=data['sample_id'],
                            defaults=data
                        )

                        if created:
                            records_created += 1
                        else:
                            records_updated += 1

                results['total_processed'] += 1
                results['total_successful'] += 1
                results['total_records_created'] += records_created
                results['total_records_updated'] += records_updated
                results['processed_files'].append({
                    'file': file_name,
                    'created': records_created,
                    'updated': records_updated,
                    'status': 'success'
                })

                # Move file to imported folder
                shutil.move(str(file_path), os.path.join(imported_folder, file_name))

            except Exception as e:
                results['total_failed'] += 1
                results['errors'].append(f"{file_name}: {str(e)}")
                results['processed_files'].append({
                    'file': file_name,
                    'error': str(e),
                    'status': 'failed'
                })

    # Log summary
    print(f"Nova Flex 2 Import Task Completed at {datetime.now()}")
    print(f"Files processed: {results['total_processed']}")
    print(f"Successful: {results['total_successful']}")
    print(f"Failed: {results['total_failed']}")
    print(f"Records created: {results['total_records_created']}")
    print(f"Records updated: {results['total_records_updated']}")

    return results


# ========== CESDS Import ==========
from plotly_integration.process_development.analytical.ce_sds.process_asc import save_asc_to_db, move_file_to_processed
import os

# Configuration - adjust these paths as needed
CESDS_IMPORT_FOLDER = "/mnt/fs2/DjangoRawData/CESDS/Imports"
CESDS_PROCESSED_FOLDER = "/mnt/fs2/DjangoRawData/CESDS/Imported"


@shared_task(name='plotly_integration.import_cesds_files', bind=True)
def import_cesds_files(self):
    """Import CESDS .asc files from incoming folder to database"""

    # Ensure folders exist
    os.makedirs(CESDS_PROCESSED_FOLDER, exist_ok=True)

    # Get files to process
    processed_files = set(os.listdir(CESDS_PROCESSED_FOLDER))
    asc_files = [
        f for f in os.listdir(CESDS_IMPORT_FOLDER)
        if f.lower().endswith(".asc")
           and "dat-pda - 220nm" not in f.lower()
           and f not in processed_files
    ]

    if not asc_files:
        return "No new files to import"

    # Process files
    successful = 0
    failed = 0

    for i, filename in enumerate(asc_files):
        file_path = os.path.join(CESDS_IMPORT_FOLDER, filename)

        try:
            save_asc_to_db(file_path)
            move_file_to_processed(file_path, CESDS_PROCESSED_FOLDER)
            successful += 1
        except Exception as e:
            failed += 1
            print(f"Failed to import {filename}: {e}")

    return f"Import completed. Success: {successful}, Failed: {failed}"


# ========== cIEF Import ==========
from plotly_integration.process_development.analytical.cief.process_asc import save_asc_to_db, move_file_to_processed
import os

# Configuration - adjust these paths as needed
CIEF_IMPORT_FOLDER = "/mnt/fs2/DjangoRawData/cIEF/Imports"
CIEF_PROCESSED_FOLDER = "/mnt/fs2/DjangoRawData/cIEF/Imported"


@shared_task(name='plotly_integration.import_cief_files', bind=True)
def import_cief_files(self):
    """Import cief .asc files from incoming folder to database"""

    # Ensure folders exist
    os.makedirs(CIEF_PROCESSED_FOLDER, exist_ok=True)

    # Get files to process
    processed_files = set(os.listdir(CIEF_PROCESSED_FOLDER))
    asc_files = [
        f for f in os.listdir(CIEF_IMPORT_FOLDER)
        if f.lower().endswith(".asc")
           and "dat-pda - 220nm" not in f.lower()
           and f not in processed_files
    ]

    if not asc_files:
        return "No new files to import"

    # Process files
    successful = 0
    failed = 0

    for i, filename in enumerate(asc_files):
        file_path = os.path.join(CIEF_IMPORT_FOLDER, filename)

        try:
            save_asc_to_db(file_path)
            move_file_to_processed(file_path, CIEF_PROCESSED_FOLDER)
            successful += 1
        except Exception as e:
            failed += 1
            print(f"Failed to import {filename}: {e}")

    return f"Import completed. Success: {successful}, Failed: {failed}"