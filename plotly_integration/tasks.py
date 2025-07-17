# plotly_integration/tasks.py
# Combined Celery tasks for AKTA, Empower, and ViCell imports

import os
import hashlib
import json
import logging
import requests
import time
from datetime import datetime as dt, timedelta
import pandas as pd
import numpy as np
from celery import shared_task
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.db import IntegrityError, transaction
from plotly_integration.models import ViCellData
from plotly_integration.process_development.cell_culture.vicell.vicell_import_monitor import process_vicell_file_from_end

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
@shared_task(name='plotly_integration.trigger_import_task')
def trigger_import_task():
    """Trigger AKTA import task"""
    try:
        response = requests.post("http://django.systimmune.net:3000/api/traverse/start", timeout=20)
        if response.status_code == 200:
            return "✅ Import triggered successfully."
        return f"⚠️ Server responded with: {response.status_code} - {response.text}"
    except Exception as e:
        return f"❌ Error triggering import: {e}"


@shared_task(name='plotly_integration.trigger_auto_traversal')
def trigger_auto_traversal():
    """Trigger automatic AKTA traversal"""
    try:
        response = requests.post("http://localhost:3000/api/traverse/start-auto", timeout=300)  # 5 min timeout
        response.raise_for_status()
        return {
            "status": "success",
            "message": response.json()
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "error",
            "message": str(e)
        }


@shared_task(name='plotly_integration.test_scheduled_print')
def test_scheduled_print():
    """Test task for debugging scheduled tasks"""
    import datetime
    print(f"🕒 Test task ran at {datetime.datetime.now()}")
    return f"Test task completed at {datetime.datetime.now()}"


@shared_task(name='plotly_integration.run_complete_pipeline')
def run_complete_import_pipeline():
    """
    Run the complete AKTA import pipeline:
    1. Start OPC UA traversal
    2. Wait for traversal to complete
    3. Import the results
    """
    try:
        # Start traversal
        logger.info("Starting OPC UA traversal...")
        response = requests.post(f"{NODEJS_SERVER}/start-traversal")

        if response.status_code != 200:
            return f"Failed to start traversal: {response.text}"

        result = response.json()

        if not result.get('success'):
            return f"Traversal failed: {result.get('message', 'Unknown error')}"

        # Wait for completion
        logger.info("Waiting for traversal to complete...")
        start_time = time.time()

        while time.time() - start_time < MAX_WAIT_TIME:
            response = requests.get(f"{NODEJS_SERVER}/status")
            if response.status_code == 200:
                status = response.json()
                if status.get('isTraversing') == False:
                    logger.info("Traversal completed!")
                    break

            time.sleep(CHECK_INTERVAL)
        else:
            return "Traversal timed out"

        # Import results
        logger.info("Importing traversal results...")
        response = requests.post(f"{NODEJS_SERVER}/import-to-database")

        if response.status_code != 200:
            return f"Import failed: {response.text}"

        import_result = response.json()
        return f"Pipeline completed: {import_result.get('message', 'Success')}"

    except Exception as e:
        logger.error(f"Pipeline error: {str(e)}")
        return f"Pipeline error: {str(e)}"


# ========== EMPOWER TASKS ==========
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


@shared_task(name='plotly_integration.import_empower_files')
def import_empower_files():
    """Import Empower .ars and .arw files"""
    # Keep existing EMPOWER implementation
    pass


def get_empower_import_status():
    """Get current Empower import status"""
    status = {
        'folder': EMPOWER_IMPORT_FOLDER,
        'last_import': cache.get('empower_last_import'),
        'is_locked': cache.get('empower_import_lock') is not None
    }

    if os.path.isdir(EMPOWER_IMPORT_FOLDER):
        processed_files = load_empower_processed_files()
        all_files = os.listdir(EMPOWER_IMPORT_FOLDER)

        status['pending_ars'] = len([f for f in all_files if f.endswith('.ars') and f not in processed_files])
        status['pending_arw'] = len([f for f in all_files if f.endswith('.arw') and f not in processed_files])
        status['total_processed'] = len(processed_files)
    else:
        status['error'] = 'Import folder not accessible'

    return status


# ========== VICELL TASKS ==========
@shared_task(name='plotly_integration.import_vicell_data', bind=True)
def import_vicell_data(self):
    """
    Celery task to import ViCell data using the import function from vicell_import_monitor.
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
        logger.info(f"Processing file: {filename}")

        # Update task state
        self.update_state(state='PROGRESS', meta={'message': 'Starting import...'})

        # Process the file using the imported function
        result = process_vicell_file_from_end()

        if 'error' in result:
            return {
                "status": "error",
                "message": result['message'],
                "details": result
            }

        # Store detailed results in cache
        cache.set('vicell_last_import', {
            'timestamp': dt.now().isoformat(),
            'task_id': self.request.id,
            'method': 'database-based-single-file',
            'imported': result['imported'],
            'failed': result['failed'],
            'skipped_invalid': result['skipped_invalid'],
            'latest_imported': result.get('latest_imported').isoformat() if result.get('latest_imported') else None,
            'details': result
        }, 3600)

        return {
            "status": "success",
            "message": result['message'],
            "imported": result['imported'],
            "failed": result['failed'],
            "details": result
        }

    except Exception as e:
        error_msg = f"Fatal error in ViCell import: {str(e)}"
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