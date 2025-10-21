"""
Create sample media preparations with various statuses
Run with: python create_sample_media_preps.py
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
django.setup()

from datetime import date, timedelta
from plotly_integration.models import (
    USPMediaPrep, USPMediaComponent, USPMediaRecipe,
    USPMediaComponentLibrary
)

print("=" * 80)
print("Creating Sample Media Preparations")
print("=" * 80)

# Delete existing sample media preps (UPMP0001-UPMP0005)
print("\nDeleting existing sample media preps...")
USPMediaPrep.objects.filter(media_id__in=['UPMP0001', 'UPMP0002', 'UPMP0003', 'UPMP0004', 'UPMP0005']).delete()
print("Deleted existing samples")

# Get recipes
try:
    maxfa_recipe = USPMediaRecipe.objects.get(recipe_id='RCP0002')  # CHO MaxFA
    maxfb_recipe = USPMediaRecipe.objects.get(recipe_id='RCP0003')  # CHO MaxFB
    maxx_recipe = USPMediaRecipe.objects.get(recipe_id='RCP0004')   # CHO MaxX
except USPMediaRecipe.DoesNotExist:
    print("ERROR: Recipes not found. Please run import_excel_recipes.py first.")
    exit(1)

# Get components
try:
    maxfa_powder = USPMediaComponentLibrary.objects.get(component_name='CHO MaxFA Dry Powder')
    maxfb_powder = USPMediaComponentLibrary.objects.get(component_name='CHO MaxFB Dry Powder')
    maxx_powder = USPMediaComponentLibrary.objects.get(component_name='CHO MaxX Dry Powder')
    naoh = USPMediaComponentLibrary.objects.get(component_name='10N NaOH')
    sodium_bicarb = USPMediaComponentLibrary.objects.get(component_name='Sodium Bicarbonate')
except USPMediaComponentLibrary.DoesNotExist:
    print("ERROR: Components not found. Please run import_excel_recipes.py first.")
    exit(1)

today = date.today()

# Sample 1: CHO MaxFA (4L) - Available, not expired (GREEN)
print("\n1. Creating CHO MaxFA 4L batch - Available (GREEN)")
prep1 = USPMediaPrep.objects.create(
    media_id='UPMP0001',
    recipe=maxfa_recipe,
    media_name='CHO MaxFA',
    media_type='Feed A',
    batch_size=4.0,
    preparation_date=today - timedelta(days=10),
    expiration_date=today + timedelta(days=20),  # Expires in 20 days
    prepared_by='John Doe',
    ph_actual=6.75,
    osmolality_actual=275,
    sterility_check=True,
    storage_location='4C Cold Room, Shelf A',
    is_used_up=False,
    notes='Batch for Experiment EXP001'
)
# Add main component
USPMediaComponent.objects.create(
    media_prep=prep1,
    component_type='base_powder',
    component_name='CHO MaxFA Dry Powder',
    lot_number='MB231212A01',
    target_amount=720.0,
    actual_amount=720.0,
    unit='g',
    vendor='Manufacturer'
)
# Add pH adjustment
USPMediaComponent.objects.create(
    media_prep=prep1,
    component_type='base',
    component_name='10N NaOH',
    lot_number='245169',
    target_amount=72.0,
    actual_amount=68.0,
    unit='mL',
    vendor='Vendor',
    notes='pH adjustment'
)
print(f"  Created: {prep1.media_id} - Expires: {prep1.expiration_date}")

# Sample 2: CHO MaxFB (0.5L) - Available, but EXPIRED (RED)
print("\n2. Creating CHO MaxFB 0.5L batch - Expired (RED)")
prep2 = USPMediaPrep.objects.create(
    media_id='UPMP0002',
    recipe=maxfb_recipe,
    media_name='CHO MaxFB',
    media_type='Feed B',
    batch_size=0.5,
    preparation_date=today - timedelta(days=45),
    expiration_date=today - timedelta(days=5),  # Expired 5 days ago
    prepared_by='Jane Smith',
    ph_actual=11.3,
    osmolality_actual=210,
    sterility_check=True,
    storage_location='4C Cold Room, Shelf B',
    is_used_up=False,  # Not used up, but expired
    notes='Old batch - should be discarded'
)
USPMediaComponent.objects.create(
    media_prep=prep2,
    component_type='base_powder',
    component_name='CHO MaxFB Dry Powder',
    lot_number='MB240128A02',
    target_amount=47.25,
    actual_amount=47.3,
    unit='g',
    vendor='Manufacturer'
)
USPMediaComponent.objects.create(
    media_prep=prep2,
    component_type='base',
    component_name='10N NaOH',
    lot_number='245169',
    target_amount=40.0,
    actual_amount=44.0,
    unit='mL',
    vendor='Vendor',
    notes='pH adjustment'
)
print(f"  Created: {prep2.media_id} - Expired: {prep2.expiration_date}")

# Sample 3: CHO MaxX (6L) - USED UP (GRAY)
print("\n3. Creating CHO MaxX 6L batch - Used Up (GRAY)")
prep3 = USPMediaPrep.objects.create(
    media_id='UPMP0003',
    recipe=maxx_recipe,
    media_name='CHO MaxX Medium',
    media_type='Growth Media',
    batch_size=6.0,
    preparation_date=today - timedelta(days=20),
    expiration_date=today + timedelta(days=10),  # Still valid, but used up
    prepared_by='John Doe',
    ph_actual=6.95,
    osmolality_actual=285,
    sterility_check=True,
    storage_location='4C Cold Room, Shelf C',
    is_used_up=True,
    date_used_up=today - timedelta(days=2),
    notes='Used for bioreactor run BR-2025-001'
)
USPMediaComponent.objects.create(
    media_prep=prep3,
    component_type='base_powder',
    component_name='CHO MaxX Dry Powder',
    lot_number='MB240628A01',
    target_amount=123.6,
    actual_amount=123.3,
    unit='g',
    vendor='Manufacturer'
)
USPMediaComponent.objects.create(
    media_prep=prep3,
    component_type='buffer',
    component_name='Sodium Bicarbonate',
    lot_number='183343',
    target_amount=10.8,
    actual_amount=10.8,
    unit='g',
    vendor='Vendor'
)
USPMediaComponent.objects.create(
    media_prep=prep3,
    component_type='base',
    component_name='10N NaOH',
    lot_number='231478',
    target_amount=25.0,
    actual_amount=25.0,
    unit='mL',
    vendor='Vendor',
    notes='pH adjustment'
)
print(f"  Created: {prep3.media_id} - Used up on: {prep3.date_used_up}")

# Sample 4: CHO MaxFA (2L) - Available, not expired (GREEN)
print("\n4. Creating CHO MaxFA 2L batch - Available (GREEN)")
prep4 = USPMediaPrep.objects.create(
    media_id='UPMP0004',
    recipe=maxfa_recipe,
    media_name='CHO MaxFA',
    media_type='Feed A',
    batch_size=2.0,
    preparation_date=today - timedelta(days=5),
    expiration_date=today + timedelta(days=25),
    prepared_by='Jane Smith',
    ph_actual=6.82,
    osmolality_actual=268,
    sterility_check=True,
    storage_location='4C Cold Room, Shelf A',
    is_used_up=False,
    notes='Small batch for testing'
)
USPMediaComponent.objects.create(
    media_prep=prep4,
    component_type='base_powder',
    component_name='CHO MaxFA Dry Powder',
    lot_number='MB231212A01',
    target_amount=360.0,
    actual_amount=360.0,
    unit='g',
    vendor='Manufacturer'
)
USPMediaComponent.objects.create(
    media_prep=prep4,
    component_type='base',
    component_name='10N NaOH',
    lot_number='245169',
    target_amount=36.0,
    actual_amount=34.0,
    unit='mL',
    vendor='Vendor',
    notes='pH adjustment'
)
print(f"  Created: {prep4.media_id} - Expires: {prep4.expiration_date}")

# Sample 5: CHO MaxX (3L) - Available, but EXPIRED (RED)
print("\n5. Creating CHO MaxX 3L batch - Expired (RED)")
prep5 = USPMediaPrep.objects.create(
    media_id='UPMP0005',
    recipe=maxx_recipe,
    media_name='CHO MaxX Medium',
    media_type='Growth Media',
    batch_size=3.0,
    preparation_date=today - timedelta(days=35),
    expiration_date=today - timedelta(days=1),  # Expired yesterday
    prepared_by='John Doe',
    ph_actual=7.02,
    osmolality_actual=295,
    sterility_check=True,
    storage_location='4C Cold Room, Shelf C',
    is_used_up=False,
    notes='Prepare fresh batch'
)
USPMediaComponent.objects.create(
    media_prep=prep5,
    component_type='base_powder',
    component_name='CHO MaxX Dry Powder',
    lot_number='MB240628A01',
    target_amount=61.8,
    actual_amount=61.7,
    unit='g',
    vendor='Manufacturer'
)
USPMediaComponent.objects.create(
    media_prep=prep5,
    component_type='buffer',
    component_name='Sodium Bicarbonate',
    lot_number='183343',
    target_amount=5.4,
    actual_amount=5.4,
    unit='g',
    vendor='Vendor'
)
USPMediaComponent.objects.create(
    media_prep=prep5,
    component_type='base',
    component_name='10N NaOH',
    lot_number='231478',
    target_amount=12.5,
    actual_amount=13.0,
    unit='mL',
    vendor='Vendor',
    notes='pH adjustment'
)
print(f"  Created: {prep5.media_id} - Expired: {prep5.expiration_date}")

print("\n" + "=" * 80)
print("SUCCESS! Sample media preparations created")
print("=" * 80)

# Summary
total_preps = USPMediaPrep.objects.count()
available = USPMediaPrep.objects.filter(is_used_up=False, expiration_date__gt=today).count()
expired = USPMediaPrep.objects.filter(expiration_date__lte=today).count()
used_up = USPMediaPrep.objects.filter(is_used_up=True).count()

print(f"\nDatabase Summary:")
print(f"  Total Media Preps: {total_preps}")
print(f"  Available (GREEN): {available}")
print(f"  Expired (RED): {expired}")
print(f"  Used Up (GRAY): {used_up}")

print("\nColor coding in the app:")
print("  GREEN rows: Available and not expired")
print("  RED rows: Expired")
print("  GRAY rows: Used up/discarded")
