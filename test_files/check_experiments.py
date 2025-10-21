from plotly_integration.models import USPExperiment, USPProcessStep, USPVessel

print(f'Total USP Experiments: {USPExperiment.objects.count()}')
print('Recent experiments:')
for exp in USPExperiment.objects.all()[:5]:
    print(f'  {exp.experiment_id} - {exp.experiment_name} ({exp.status})')
    steps = exp.process_steps.count()
    vessels = USPVessel.objects.filter(process_step__experiment=exp).count()
    print(f'    Steps: {steps}, Vessels: {vessels}')