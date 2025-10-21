"""
Test script to clear existing data and create a comprehensive test recipe
Run with: python manage.py shell < test_recipe_creation.py
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
django.setup()

from plotly_integration.models import (
    USPMediaPrep, USPMediaComponent, USPMediaRecipe,
    USPMediaRecipeStep, USPMediaComponentLibrary, USPMediaRecipeStepParameter
)

print("=" * 80)
print("STEP 1: Clearing existing data...")
print("=" * 80)

# Clear existing data
USPMediaComponent.objects.all().delete()
USPMediaPrep.objects.all().delete()
USPMediaRecipeStepParameter.objects.all().delete()
USPMediaRecipeStep.objects.all().delete()
USPMediaRecipe.objects.all().delete()

print("Cleared all media preps, recipes, and steps")

print("\n" + "=" * 80)
print("STEP 2: Creating test components...")
print("=" * 80)

# Create test components if they don't exist
components_data = [
    {'type': 'base_powder', 'name': 'CD FortiCHO Powder', 'catalog': 'A1234501', 'vendor': 'Cytiva', 'units': 'g'},
    {'type': 'glucose', 'name': 'D-Glucose', 'catalog': 'G7021', 'vendor': 'Sigma', 'units': 'g'},
    {'type': 'glutamine', 'name': 'L-Glutamine', 'catalog': 'G7513', 'vendor': 'Sigma', 'units': 'g'},
    {'type': 'buffer', 'name': 'Sodium Bicarbonate', 'catalog': 'S5761', 'vendor': 'Sigma', 'units': 'g'},
    {'type': 'acid', 'name': '1M HCl', 'catalog': 'H1758', 'vendor': 'Sigma', 'units': 'mL'},
    {'type': 'base', 'name': '1M NaOH', 'catalog': 'S2770', 'vendor': 'Sigma', 'units': 'mL'},
]

created_components = {}
for comp_data in components_data:
    comp, created = USPMediaComponentLibrary.objects.get_or_create(
        component_name=comp_data['name'],
        defaults={
            'component_type': comp_data['type'],
            'catalog_number': comp_data['catalog'],
            'vendor': comp_data['vendor'],
            'typical_units': comp_data['units'],
            'active': True
        }
    )
    created_components[comp_data['name']] = comp
    print(f"{'Created' if created else 'Found'}: {comp.component_name}")

print("\n" + "=" * 80)
print("STEP 3: Creating comprehensive test recipe with ALL step types...")
print("=" * 80)

# Create recipe
recipe = USPMediaRecipe.objects.create(
    recipe_id='RCP0001',
    recipe_name='Comprehensive Test Recipe - All Steps',
    recipe_type='Growth Media',
    version='1.0',
    base_volume=1.0,  # 1L base
    ph_target=7.2,
    osmolality_target=290,
    storage_temp='4°C',
    shelf_life_days=30,
    active=True
)
print(f"Created recipe: {recipe.recipe_id} - {recipe.recipe_name}")

# Define all steps with their parameters
steps_data = [
    {
        'step_type': 'initial_water_fill',
        'instructions': 'Add 80% of final volume as MilliQ water',
        'params': {}
    },
    {
        'step_type': 'add_component',
        'instructions': 'Add base media powder slowly while stirring',
        'params': {
            'component_id': ('fk_component', str(created_components['CD FortiCHO Powder'].id)),
            'amount_per_liter': ('float', '13.5'),
            'amount_unit': ('string', 'g')
        }
    },
    {
        'step_type': 'stir',
        'instructions': 'Stir until completely dissolved',
        'params': {
            'duration_minutes': ('integer', '30')
        }
    },
    {
        'step_type': 'add_component',
        'instructions': 'Add glucose supplement',
        'params': {
            'component_id': ('fk_component', str(created_components['D-Glucose'].id)),
            'amount_per_liter': ('float', '4.5'),
            'amount_unit': ('string', 'g')
        }
    },
    {
        'step_type': 'add_component',
        'instructions': 'Add glutamine supplement',
        'params': {
            'component_id': ('fk_component', str(created_components['L-Glutamine'].id)),
            'amount_per_liter': ('float', '0.876'),
            'amount_unit': ('string', 'g')
        }
    },
    {
        'step_type': 'add_component',
        'instructions': 'Add sodium bicarbonate buffer',
        'params': {
            'component_id': ('fk_component', str(created_components['Sodium Bicarbonate'].id)),
            'amount_per_liter': ('float', '3.7'),
            'amount_unit': ('string', 'g')
        }
    },
    {
        'step_type': 'stir',
        'instructions': 'Mix thoroughly',
        'params': {
            'duration_minutes': ('integer', '15')
        }
    },
    {
        'step_type': 'add_water',
        'instructions': 'Add additional water to reach 95% of target',
        'params': {
            'target_volume': ('float', '950')  # in mL for 1L base
        }
    },
    {
        'step_type': 'heat',
        'instructions': 'Heat to dissolve components',
        'params': {
            'duration_minutes': ('integer', '10'),
            'temperature': ('float', '37')
        }
    },
    {
        'step_type': 'cool',
        'instructions': 'Cool to room temperature',
        'params': {
            'duration_minutes': ('integer', '20'),
            'temperature': ('float', '25')
        }
    },
    {
        'step_type': 'measure_ph',
        'instructions': 'Measure pH before adjustment',
        'params': {
            'target_ph': ('string', '7.2')
        }
    },
    {
        'step_type': 'adjust_ph',
        'instructions': 'Adjust pH to target range using HCl or NaOH',
        'params': {
            'target_ph': ('string', '7.1-7.3')
        }
    },
    {
        'step_type': 'final_water_fill',
        'instructions': 'Add MilliQ water to final volume',
        'params': {}
    },
    {
        'step_type': 'measure_osmolality',
        'instructions': 'Measure osmolality',
        'params': {
            'target_osmolality': ('string', '280-300')
        }
    },
    {
        'step_type': 'adjust_osmolality',
        'instructions': 'Adjust if outside range',
        'params': {
            'target_osmolality': ('string', '280-300')
        }
    },
    {
        'step_type': 'filter_sterilize',
        'instructions': 'Filter through 0.22µm filter',
        'params': {}
    },
    {
        'step_type': 'aliquot',
        'instructions': 'Aliquot into sterile bottles (500mL each)',
        'params': {}
    },
    {
        'step_type': 'note',
        'instructions': 'Label with preparation date, expiration date, and lot numbers',
        'params': {}
    },
]

# Create steps and parameters
for i, step_data in enumerate(steps_data, 1):
    # Create the step
    step = USPMediaRecipeStep.objects.create(
        recipe=recipe,
        step_number=i,
        step_type=step_data['step_type'],
        instructions=step_data.get('instructions', '')
    )

    print(f"  Step {i}: {step.get_step_type_display()}")

    # Create parameters
    for param_key, (param_type, param_value) in step_data.get('params', {}).items():
        # Determine typed values
        value_int = None
        value_float = None

        if param_type == 'integer':
            value_int = int(param_value)
        elif param_type == 'float':
            value_float = float(param_value)
        elif param_type == 'fk_component':
            value_int = int(param_value)

        param = USPMediaRecipeStepParameter.objects.create(
            step=step,
            parameter_key=param_key,
            parameter_type=param_type,
            value_text=param_value,
            value_int=value_int,
            value_float=value_float
        )
        print(f"    - {param_key}: {param_value}")

print("\n" + "=" * 80)
print("STEP 4: Verifying data...")
print("=" * 80)

# Verify
total_steps = USPMediaRecipeStep.objects.filter(recipe=recipe).count()
total_params = USPMediaRecipeStepParameter.objects.filter(step__recipe=recipe).count()

print(f"Recipe created: {recipe.recipe_id}")
print(f"Total steps: {total_steps}")
print(f"Total parameters: {total_params}")

print("\n" + "=" * 80)
print("SUCCESS! Test recipe created with all step types!")
print("=" * 80)
print(f"\nRecipe ID: {recipe.recipe_id}")
print(f"Recipe Name: {recipe.recipe_name}")
print(f"Base Volume: {recipe.base_volume}L")
print(f"Steps: {total_steps}")
print(f"Parameters: {total_params}")
print("\nYou can now test the media preparation flow in the web app!")
