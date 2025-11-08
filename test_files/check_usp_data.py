import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
django.setup()

from plotly_integration.models import USPExperiment, USPProcessStep, USPSeedTrain, USPVessel

# Check if USP0004 experiment exists
exp = USPExperiment.objects.filter(experiment_id='USP0004').first()
print(f'USP0004 experiment exists: {exp is not None}')

if exp:
    print(f'Experiment name: {exp.experiment_name}')
    steps = USPProcessStep.objects.filter(experiment=exp)
    print(f'Process steps for USP0004: {steps.count()}')

    for step in steps:
        print(f'  - Step: {step.step_type}, ID: {step.id}')
        seed_trains = USPSeedTrain.objects.filter(process_step=step)
        vessels = USPVessel.objects.filter(process_step=step)
        print(f'    Seed trains: {seed_trains.count()}')
        print(f'    Vessels: {vessels.count()}')
else:
    print('USP0004 experiment was also deleted!')

print('\n' + '='*50)
print('All existing seed train IDs:')
for st in USPSeedTrain.objects.all().values('id', 'seed_train_id', 'process_step__experiment__experiment_id'):
    print(f"  {st}")

print('\nAll existing vessel IDs:')
for v in USPVessel.objects.all().values('id', 'vessel_id', 'process_step__experiment__experiment_id'):
    print(f"  {v}")

print('\n' + '='*50)
print('All existing experiments:')
for exp in USPExperiment.objects.all().values('experiment_id', 'experiment_name'):
    print(f"  {exp}")
