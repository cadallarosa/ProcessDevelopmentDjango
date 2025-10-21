import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
django.setup()

from plotly_integration.models import LimsTiterResult, LimsSampleAnalysis, USPExperiment

# Get sample titer results to understand the data pattern
print("Sample Titer Results:")
print("-" * 80)
titer_samples = LimsTiterResult.objects.select_related('sample_id').filter(
    sample_id__sample_id__icontains='UP'
)[:20]

for result in titer_samples:
    print(f"Sample: {result.sample_id.sample_id}, Titer: {result.titer}, Date: {result.sample_id.sample_date}")

print("\n\nSample patterns:")
print("-" * 80)
# Look for samples with UPFB pattern
upfb_samples = LimsSampleAnalysis.objects.filter(
    sample_id__icontains='UPFB'
)[:20]

for sample in upfb_samples:
    print(f"Sample ID: {sample.sample_id}, Type: {sample.sample_type}, Date: {sample.sample_date}")

print("\n\nUSP Experiments:")
print("-" * 80)
experiments = USPExperiment.objects.all()[:10]
for exp in experiments:
    print(f"Experiment: {exp.experiment_id} - {exp.experiment_name}, Start: {exp.start_date}")