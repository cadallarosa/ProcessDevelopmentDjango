"""
Check for UPFB numbers with double zeros (UPFB00010-UPFB00018)
"""
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
django.setup()

from plotly_integration.models import USPVessel, ViCellData, NovaFlex2

print('='*80)
print('Checking for UPFB00010-UPFB00018 (double-zero format)')
print('='*80)

for num in range(10, 19):
    old_id = f'UPFB000{num}'
    vc_count = ViCellData.objects.filter(sample_id__icontains=old_id).count()
    nf_count = NovaFlex2.objects.filter(sample_id__icontains=old_id).count()
    v_count = USPVessel.objects.filter(vessel_id=old_id).count()
    total = vc_count + nf_count + v_count

    if total > 0:
        print(f'{old_id}: ViCell={vc_count}, Nova={nf_count}, Vessel={v_count}')

print('\nAlso checking UPFB0010-UPFB0018 (single-zero format)')
print('-'*80)

for num in range(10, 19):
    old_id = f'UPFB00{num}'
    vc_count = ViCellData.objects.filter(sample_id__icontains=old_id).count()
    nf_count = NovaFlex2.objects.filter(sample_id__icontains=old_id).count()
    v_count = USPVessel.objects.filter(vessel_id=old_id).count()
    total = vc_count + nf_count + v_count

    if total > 0:
        print(f'{old_id}: ViCell={vc_count}, Nova={nf_count}, Vessel={v_count}')

print('='*80)
