"""
Verify UPFB number updates
"""
import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
django.setup()

from plotly_integration.models import USPVessel, ViCellData, NovaFlex2

old_ids = [
    'UPFB0003', 'UPFB0004', 'UPFB0005', 'UPFB0007', 'UPFB0008', 'UPFB0009',
    'UPFB0010', 'UPFB0011', 'UPFB0012', 'UPFB0013', 'UPFB0014',
    'UPFB0015', 'UPFB0016', 'UPFB0017', 'UPFB0018'
]

new_ids = {
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

print('='*80)
print('UPFB Number Update Verification')
print('='*80)

print('\n--- Checking for old UPFB IDs ---')
has_old_ids = False
for old_id in old_ids:
    vc_count = ViCellData.objects.filter(sample_id__icontains=old_id).count()
    nf_count = NovaFlex2.objects.filter(sample_id__icontains=old_id).count()
    v_count = USPVessel.objects.filter(vessel_id=old_id).count()
    total = vc_count + nf_count + v_count

    if total > 0:
        print(f'{old_id}: ViCell={vc_count}, Nova={nf_count}, Vessel={v_count}')
        has_old_ids = True

if not has_old_ids:
    print('  No old UPFB IDs found - all updated!')

print('\n--- Checking for new UPFB IDs ---')
for old_id, new_id in new_ids.items():
    vc_count = ViCellData.objects.filter(sample_id__icontains=new_id).count()
    nf_count = NovaFlex2.objects.filter(sample_id__icontains=new_id).count()
    v_count = USPVessel.objects.filter(vessel_id=new_id).count()
    total = vc_count + nf_count + v_count

    if total > 0:
        print(f'{new_id} (was {old_id}): ViCell={vc_count}, Nova={nf_count}, Vessel={v_count}')

print('\n' + '='*80)
if not has_old_ids:
    print('SUCCESS: All UPFB numbers have been updated!')
else:
    print('WARNING: Some old UPFB numbers still exist')
print('='*80)