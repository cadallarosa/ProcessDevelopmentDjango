"""
Django management command to update UPFB vessel IDs based on the mapping from
20251014_One_Time_UPFB_Number_Adjustment.xlsx

This command updates UPFB numbers across all related tables including:
- usp_vessel
- usp_seed_train
- vicell_data
- nova_flex_2
- usp_media_prep
- And any other tables with UPFB references
"""
from django.core.management.base import BaseCommand
from django.db import transaction, connection


class Command(BaseCommand):
    help = 'Update UPFB vessel IDs based on the one-time adjustment mapping'

    # Mapping from old to new UPFB numbers
    UPFB_MAPPING = {
        'UPFB0003': 'UPFB0497',
        'UPFB0004': 'UPFB0495',
        'UPFB0005': 'UPFB0496',
        'UPFB0007': 'UPFB0500',
        'UPFB0008': 'UPFB0501',
        'UPFB0009': 'UPFB0502',
        'UPFB0010': 'UPFB0503',
        'UPFB0011': 'UPFB0504',
        'UPFB0012': 'UPFB0505',
        'UPFB0013': 'UPFB0506',
        'UPFB0014': 'UPFB0507',
        'UPFB0015': 'UPFB0508',
        'UPFB0016': 'UPFB0509',
        'UPFB0017': 'UPFB0510',
        'UPFB0018': 'UPFB0511',
    }

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('\n' + '='*80))
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
            self.stdout.write(self.style.WARNING('='*80 + '\n'))

        total_updates = 0

        # Update USPVessel
        self.stdout.write(self.style.SUCCESS('\n--- Updating usp_vessel table ---'))
        vessel_updates = self._update_vessels(dry_run)
        total_updates += vessel_updates

        # Update USPSeedTrain
        self.stdout.write(self.style.SUCCESS('\n--- Updating usp_seed_train table ---'))
        seed_train_updates = self._update_seed_trains(dry_run)
        total_updates += seed_train_updates

        # Update ViCellData
        self.stdout.write(self.style.SUCCESS('\n--- Updating vicell_data table ---'))
        vicell_updates = self._update_vicell_data(dry_run)
        total_updates += vicell_updates

        # Update NovaFlex2
        self.stdout.write(self.style.SUCCESS('\n--- Updating nova_flex_2 table ---'))
        nova_updates = self._update_nova_data(dry_run)
        total_updates += nova_updates

        # Update USPMediaPrep
        self.stdout.write(self.style.SUCCESS('\n--- Updating usp_media_prep table ---'))
        media_prep_updates = self._update_media_prep(dry_run)
        total_updates += media_prep_updates

        # Update any other tables that might reference UPFB numbers
        self.stdout.write(self.style.SUCCESS('\n--- Checking other tables ---'))
        other_updates = self._update_other_tables(dry_run)
        total_updates += other_updates

        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'DRY RUN: Would update {total_updates} total records'
                )
            )
            self.stdout.write(self.style.WARNING('Run without --dry-run to apply changes'))
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully updated {total_updates} total records'
                )
            )
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))

    @transaction.atomic
    def _update_vessels(self, dry_run):
        """Update usp_vessel records"""
        count = 0
        cursor = connection.cursor()

        for old_id, new_id in self.UPFB_MAPPING.items():
            # Check how many records would be updated
            cursor.execute(
                "SELECT COUNT(*) FROM usp_vessel WHERE vessel_id = %s",
                [old_id]
            )
            vessel_count = cursor.fetchone()[0]

            if vessel_count > 0:
                self.stdout.write(f'  vessel_id: {old_id} -> {new_id} ({vessel_count} records)')

                if not dry_run:
                    cursor.execute(
                        "UPDATE usp_vessel SET vessel_id = %s WHERE vessel_id = %s",
                        [new_id, old_id]
                    )

                count += vessel_count

        if count == 0:
            self.stdout.write('  No records to update')

        return count

    @transaction.atomic
    def _update_seed_trains(self, dry_run):
        """Update usp_seed_train records - seed_train_id field"""
        count = 0
        cursor = connection.cursor()

        for old_id, new_id in self.UPFB_MAPPING.items():
            # Check seed_train_id field containing the old UPFB number
            cursor.execute(
                "SELECT COUNT(*) FROM usp_seed_train WHERE seed_train_id LIKE %s",
                [f'%{old_id}%']
            )
            seed_train_count = cursor.fetchone()[0]

            if seed_train_count > 0:
                self.stdout.write(f'  seed_train_id: {old_id} -> {new_id} ({seed_train_count} records)')

                if not dry_run:
                    # Use REPLACE function to update the seed_train_id
                    cursor.execute(
                        "UPDATE usp_seed_train SET seed_train_id = REPLACE(seed_train_id, %s, %s) WHERE seed_train_id LIKE %s",
                        [old_id, new_id, f'%{old_id}%']
                    )

                count += seed_train_count

        if count == 0:
            self.stdout.write('  No records to update')

        return count

    @transaction.atomic
    def _update_vicell_data(self, dry_run):
        """Update vicell_data records - sample_id field"""
        count = 0
        cursor = connection.cursor()

        for old_id, new_id in self.UPFB_MAPPING.items():
            # Check sample_id field containing the old UPFB number
            cursor.execute(
                "SELECT COUNT(*) FROM vicell_data WHERE sample_id LIKE %s",
                [f'%{old_id}%']
            )
            vicell_count = cursor.fetchone()[0]

            if vicell_count > 0:
                self.stdout.write(f'  sample_id: {old_id} -> {new_id} ({vicell_count} records)')

                if not dry_run:
                    # Use REPLACE function to update the sample_id
                    cursor.execute(
                        "UPDATE vicell_data SET sample_id = REPLACE(sample_id, %s, %s) WHERE sample_id LIKE %s",
                        [old_id, new_id, f'%{old_id}%']
                    )

                count += vicell_count

        if count == 0:
            self.stdout.write('  No records to update')

        return count

    @transaction.atomic
    def _update_nova_data(self, dry_run):
        """Update nova_flex_2 records - sample_id field"""
        count = 0
        cursor = connection.cursor()

        for old_id, new_id in self.UPFB_MAPPING.items():
            # Check sample_id field containing the old UPFB number
            cursor.execute(
                "SELECT COUNT(*) FROM nova_flex_2 WHERE sample_id LIKE %s",
                [f'%{old_id}%']
            )
            nova_count = cursor.fetchone()[0]

            if nova_count > 0:
                self.stdout.write(f'  sample_id: {old_id} -> {new_id} ({nova_count} records)')

                if not dry_run:
                    # Use REPLACE function to update the sample_id
                    cursor.execute(
                        "UPDATE nova_flex_2 SET sample_id = REPLACE(sample_id, %s, %s) WHERE sample_id LIKE %s",
                        [old_id, new_id, f'%{old_id}%']
                    )

                count += nova_count

        if count == 0:
            self.stdout.write('  No records to update')

        return count

    @transaction.atomic
    def _update_media_prep(self, dry_run):
        """Update usp_media_prep records - media_id field if it contains UPFB"""
        count = 0
        cursor = connection.cursor()

        for old_id, new_id in self.UPFB_MAPPING.items():
            # Check media_id field containing the old UPFB number
            cursor.execute(
                "SELECT COUNT(*) FROM usp_media_prep WHERE media_id LIKE %s",
                [f'%{old_id}%']
            )
            media_prep_count = cursor.fetchone()[0]

            if media_prep_count > 0:
                self.stdout.write(f'  media_id: {old_id} -> {new_id} ({media_prep_count} records)')

                if not dry_run:
                    # Use REPLACE function to update the media_id
                    cursor.execute(
                        "UPDATE usp_media_prep SET media_id = REPLACE(media_id, %s, %s) WHERE media_id LIKE %s",
                        [old_id, new_id, f'%{old_id}%']
                    )

                count += media_prep_count

        if count == 0:
            self.stdout.write('  No records to update')

        return count

    @transaction.atomic
    def _update_other_tables(self, dry_run):
        """Check and update any other tables that might reference UPFB numbers"""
        count = 0
        cursor = connection.cursor()

        # Check usp_experiment table for project_id field
        for old_id, new_id in self.UPFB_MAPPING.items():
            cursor.execute(
                "SELECT COUNT(*) FROM usp_experiment WHERE project_id LIKE %s",
                [f'%{old_id}%']
            )
            exp_count = cursor.fetchone()[0]

            if exp_count > 0:
                self.stdout.write(f'  usp_experiment.project_id: {old_id} -> {new_id} ({exp_count} records)')

                if not dry_run:
                    cursor.execute(
                        "UPDATE usp_experiment SET project_id = REPLACE(project_id, %s, %s) WHERE project_id LIKE %s",
                        [old_id, new_id, f'%{old_id}%']
                    )

                count += exp_count

        # Check titer_data if it exists
        cursor.execute("SHOW TABLES LIKE 'titer_data'")
        if cursor.fetchone():
            for old_id, new_id in self.UPFB_MAPPING.items():
                cursor.execute(
                    "SELECT COUNT(*) FROM titer_data WHERE sample_id LIKE %s",
                    [f'%{old_id}%']
                )
                titer_count = cursor.fetchone()[0]

                if titer_count > 0:
                    self.stdout.write(f'  titer_data.sample_id: {old_id} -> {new_id} ({titer_count} records)')

                    if not dry_run:
                        cursor.execute(
                            "UPDATE titer_data SET sample_id = REPLACE(sample_id, %s, %s) WHERE sample_id LIKE %s",
                            [old_id, new_id, f'%{old_id}%']
                        )

                    count += titer_count

        if count == 0:
            self.stdout.write('  No records to update')

        return count