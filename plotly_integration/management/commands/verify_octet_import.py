"""
Django management command to verify Octet data import
"""
from django.core.management.base import BaseCommand
from plotly_integration.models import (
    OctetExperiment, OctetSensorData, OctetStepData,
    OctetTimeSeriesData, OctetSensorLayout, OctetSampleLayout
)


class Command(BaseCommand):
    help = 'Verify Octet data import'

    def add_arguments(self, parser):
        parser.add_argument(
            '--id',
            type=int,
            default=1,
            help='Experiment ID to verify (default: 1)'
        )

    def handle(self, *args, **options):
        exp_id = options['id']

        self.stdout.write("=" * 70)
        self.stdout.write("OCTET DATA VERIFICATION")
        self.stdout.write("=" * 70)

        try:
            exp = OctetExperiment.objects.get(id=exp_id)
        except OctetExperiment.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"\nExperiment with ID {exp_id} not found"))
            return

        self.stdout.write(f"\nExperiment Details:")
        self.stdout.write(f"  Name: {exp.experiment_name}")
        self.stdout.write(f"  Type: {exp.experiment_type} - {exp.experiment_subtype}")
        self.stdout.write(f"  Run ID: {exp.run_id}")
        self.stdout.write(f"  Date: {exp.start_datetime}")
        self.stdout.write(f"  Temperature: {exp.temperature}°C")
        self.stdout.write(f"  Imported by: {exp.imported_by}")

        self.stdout.write(f"\nRecord Counts:")
        sensor_count = exp.sensors.count()
        self.stdout.write(f"  Sensors: {sensor_count}")
        self.stdout.write(f"  Sensor Layout: {exp.sensor_layout.count()}")
        self.stdout.write(f"  Sample Layout: {exp.sample_layout.count()}")
        self.stdout.write(f"  Step Sequence: {exp.step_sequence.count()}")

        # Count steps
        total_steps = sum(s.steps.count() for s in exp.sensors.all())
        self.stdout.write(f"  Total Steps: {total_steps}")

        # Sample time series count
        self.stdout.write(f"\nTime Series Counts (sampling first 3 sensors):")
        for sensor in exp.sensors.all()[:3]:
            ts_count = sum(step.time_series.count() for step in sensor.steps.all())
            self.stdout.write(f"  Sensor {sensor.sensor_location}: {ts_count} points")

        self.stdout.write(f"\nSensor Data (First 5 sensors):")
        self.stdout.write(f"  {'Location':<10} {'Sample ID':<30} {'Response (nm)':<15} {'Concentration'}")
        self.stdout.write(f"  {'-'*10} {'-'*30} {'-'*15} {'-'*15}")

        for sensor in exp.sensors.all()[:5]:
            response_str = f"{sensor.response:.4f}" if sensor.response else "N/A"
            conc_str = f"{sensor.concentration}" if sensor.concentration else "N/A"
            sample_id = sensor.sample_id[:30] if sensor.sample_id else "N/A"
            self.stdout.write(f"  {sensor.sensor_location:<10} {sample_id:<30} {response_str:<15} {conc_str}")

        self.stdout.write(f"\nStep Sequence:")
        for step_seq in exp.step_sequence.all():
            self.stdout.write(f"  {step_seq.step_order}. {step_seq.step_name:<20} ({step_seq.assay_time}s @ {step_seq.flow_rate} RPM)")

        # Sample time series data for one sensor
        self.stdout.write(f"\nTime Series Sample (Sensor A1, Association Step):")
        try:
            sensor_a1 = exp.sensors.get(sensor_location='A1')
            assoc_step = sensor_a1.steps.filter(step_name__icontains='Association').first()

            if assoc_step:
                ts_count = assoc_step.time_series.count()
                self.stdout.write(f"  Step: {assoc_step.step_name}")
                self.stdout.write(f"  Total points: {ts_count}")
                self.stdout.write(f"  Start time: {assoc_step.start_time}s")
                self.stdout.write(f"  Duration: {assoc_step.assay_time}s")

                # Show first 5 points
                self.stdout.write(f"\n  First 5 time points:")
                self.stdout.write(f"    {'Time (s)':<12} {'Response (nm)'}")
                self.stdout.write(f"    {'-'*12} {'-'*15}")
                for ts in assoc_step.time_series.all()[:5]:
                    self.stdout.write(f"    {ts.time:<12.2f} {ts.response:.4f}")

                # Show last 5 points
                last_5 = assoc_step.time_series.all()[ts_count-5:ts_count]
                self.stdout.write(f"\n  Last 5 time points:")
                self.stdout.write(f"    {'Time (s)':<12} {'Response (nm)'}")
                self.stdout.write(f"    {'-'*12} {'-'*15}")
                for ts in last_5:
                    self.stdout.write(f"    {ts.time:<12.2f} {ts.response:.4f}")
            else:
                self.stdout.write(self.style.WARNING("  Association step not found"))

        except OctetSensorData.DoesNotExist:
            self.stdout.write(self.style.WARNING("  Sensor A1 not found"))

        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(self.style.SUCCESS("VERIFICATION COMPLETE"))
        self.stdout.write("=" * 70)
        self.stdout.write(f"\nAdmin URL: http://localhost:8000/admin/plotly_integration/octetexperiment/{exp.id}/")
