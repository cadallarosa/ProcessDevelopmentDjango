import os
import time
import logging
from datetime import datetime
from django.core.management.base import BaseCommand
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

# Configure logging
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Monitors Empower import folder and automatically processes new files'

    # Hardcoded paths
    IMPORT_FOLDER = "/mnt/fs2/Chris Dallarosa/Database Imports"
    REPORTED_FOLDER = "/mnt/fs2/Chris Dallarosa/Database Imported"

    # File to track processed files
    PROCESSED_FILES_LOG = os.path.join(settings.BASE_DIR, 'empower_processed_files.txt')

    def __init__(self):
        super().__init__()
        self.processed_files = self.load_processed_files()

    def add_arguments(self, parser):
        parser.add_argument(
            '--interval',
            type=int,
            default=30,
            help='Check interval in seconds (default: 30)'
        )
        parser.add_argument(
            '--once',
            action='store_true',
            help='Run once and exit (for cron jobs)'
        )

    def load_processed_files(self):
        """Load list of already processed files"""
        if os.path.exists(self.PROCESSED_FILES_LOG):
            with open(self.PROCESSED_FILES_LOG, 'r') as f:
                return set(line.strip() for line in f if line.strip())
        return set()

    def save_processed_file(self, filename):
        """Add a file to the processed list"""
        self.processed_files.add(filename)
        with open(self.PROCESSED_FILES_LOG, 'a') as f:
            f.write(f"{filename}\n")

    def get_unprocessed_files(self):
        """Get list of files that haven't been processed yet"""
        if not os.path.isdir(self.IMPORT_FOLDER):
            logger.error(f"Import folder not accessible: {self.IMPORT_FOLDER}")
            return [], []

        all_files = os.listdir(self.IMPORT_FOLDER)

        # Filter for unprocessed .ars and .arw files
        ars_files = [f for f in all_files if f.endswith('.ars') and f not in self.processed_files]
        arw_files = [f for f in all_files if f.endswith('.arw') and f not in self.processed_files]

        return ars_files, arw_files

    def process_files(self):
        """Process all unprocessed files"""
        ars_files, arw_files = self.get_unprocessed_files()
        total_files = len(ars_files) + len(arw_files)

        if total_files == 0:
            return 0

        self.stdout.write(
            f"\n{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - Found {total_files} new file(s) to process")
        self.stdout.write(f"  .ars files: {len(ars_files)}")
        self.stdout.write(f"  .arw files: {len(arw_files)}")

        processed_count = 0

        try:
            # Process .ars files
            if ars_files:
                self.stdout.write("\nProcessing .ars files...")
                for file in ars_files:
                    self.stdout.write(f"  Processing: {file}")
                    try:
                        process_ars.process_files(
                            directory=self.IMPORT_FOLDER,
                            reported_folder=self.REPORTED_FOLDER
                        )
                        self.save_processed_file(file)
                        processed_count += 1
                    except Exception as e:
                        logger.error(f"Error processing {file}: {str(e)}")
                        self.stderr.write(f"  ERROR processing {file}: {str(e)}")

            # Process .arw files
            if arw_files:
                self.stdout.write("\nProcessing .arw files...")
                for file in arw_files:
                    self.stdout.write(f"  Processing: {file}")
                    try:
                        process_arw.process_files(
                            directory=self.IMPORT_FOLDER,
                            reported_folder=self.REPORTED_FOLDER
                        )
                        self.save_processed_file(file)
                        processed_count += 1
                    except Exception as e:
                        logger.error(f"Error processing {file}: {str(e)}")
                        self.stderr.write(f"  ERROR processing {file}: {str(e)}")

            # Run column processing functions if files were processed
            if processed_count > 0:
                self.stdout.write("\nRunning column processing functions...")
                populate_column_logbook()
                transfer_column_names()
                update_total_injections()
                assign_column_ids_to_samples()
                update_most_recent_injections()
                backfill_missing_pressure_data()
                self.stdout.write("Column processing completed!")

            self.stdout.write(self.style.SUCCESS(
                f"\n✓ Successfully processed {processed_count}/{total_files} files"
            ))

        except Exception as e:
            logger.error(f"Critical error during processing: {str(e)}")
            self.stderr.write(self.style.ERROR(f"Critical error: {str(e)}"))

        return processed_count

    def handle(self, *args, **options):
        interval = options['interval']
        run_once = options['once']

        self.stdout.write(self.style.SUCCESS(
            f"Starting Empower Auto Import Monitor"
        ))
        self.stdout.write(f"Import folder: {self.IMPORT_FOLDER}")
        self.stdout.write(f"Processed folder: {self.REPORTED_FOLDER}")
        self.stdout.write(f"Check interval: {interval} seconds")
        self.stdout.write(f"Mode: {'Run once' if run_once else 'Continuous monitoring'}\n")

        # Verify folders exist
        if not os.path.isdir(self.IMPORT_FOLDER):
            self.stderr.write(self.style.ERROR(
                f"Import folder does not exist: {self.IMPORT_FOLDER}"
            ))
            return

        if not os.path.isdir(self.REPORTED_FOLDER):
            self.stderr.write(self.style.ERROR(
                f"Reported folder does not exist: {self.REPORTED_FOLDER}"
            ))
            return

        # Main loop
        try:
            while True:
                # Check and process files
                processed = self.process_files()

                if run_once:
                    break

                # Wait for next check
                if processed == 0:
                    self.stdout.write(f"{datetime.now().strftime('%H:%M:%S')} - No new files found")

                time.sleep(interval)

        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING("\n\nStopping monitor..."))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"\nFatal error: {str(e)}"))
            logger.exception("Fatal error in auto import")
