"""
Import recipes from Excel template files
Run with: python import_excel_recipes.py
"""

import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject.settings')
django.setup()

import pandas as pd
from plotly_integration.models import (
    USPMediaRecipe, USPMediaRecipeStep,
    USPMediaComponentLibrary, USPMediaRecipeStepParameter
)

def get_or_create_component(name, component_type='other', catalog=None, vendor=None, units='g'):
    """Get or create a component in the library"""
    comp, created = USPMediaComponentLibrary.objects.get_or_create(
        component_name=name,
        defaults={
            'component_type': component_type,
            'catalog_number': catalog,
            'vendor': vendor,
            'typical_units': units,
            'active': True
        }
    )
    return comp

def create_step_with_params(recipe, step_number, step_type, instructions='', params=None):
    """Create a step and its parameters"""
    step = USPMediaRecipeStep.objects.create(
        recipe=recipe,
        step_number=step_number,
        step_type=step_type,
        instructions=instructions
    )

    if params:
        for param_key, (param_type, param_value) in params.items():
            value_int = None
            value_float = None

            if param_type == 'integer':
                value_int = int(float(param_value))
            elif param_type == 'float':
                value_float = float(param_value)
            elif param_type == 'fk_component':
                value_int = int(param_value)

            USPMediaRecipeStepParameter.objects.create(
                step=step,
                parameter_key=param_key,
                parameter_type=param_type,
                value_text=str(param_value),
                value_int=value_int,
                value_float=value_float
            )

    return step

def import_cho_maxfa():
    """Import CHO MaxFA recipe"""
    print("\nImporting CHO MaxFA recipe...")

    # Create recipe
    recipe = USPMediaRecipe.objects.create(
        recipe_id='RCP0002',
        recipe_name='CHO MaxFA',
        recipe_type='Feed A',
        version='1.0',
        base_volume=4.0,  # 4L base from template
        ph_target=6.7,
        osmolality_target=270,  # midpoint of 240-300
        storage_temp='4C',
        shelf_life_days=30,
        active=True
    )

    # Get/create components
    maxfa_powder = get_or_create_component('CHO MaxFA Dry Powder', 'base_powder', 'MB1201.206', 'Manufacturer', 'g')
    naoh_10n = get_or_create_component('10N NaOH', 'base', 'SS255-4', 'Vendor', 'mL')
    hcl_5n = get_or_create_component('5N HCl', 'acid', None, 'Vendor', 'mL')

    step_num = 1

    # Step 1: Initial water fill (80%)
    create_step_with_params(recipe, step_num, 'initial_water_fill',
                           'Add 80% of batch weight as MilliQ water (e.g., 3200g for 4L batch)')
    step_num += 1

    # Step 2: Add CHO MaxFA powder
    create_step_with_params(recipe, step_num, 'add_component',
                           'Add CHO MaxFA dry powder slowly while stirring',
                           params={
                               'component_id': ('fk_component', str(maxfa_powder.id)),
                               'amount_per_liter': ('float', '180'),  # 720g / 4L
                               'amount_unit': ('string', 'g')
                           })
    step_num += 1

    # Step 3: Add initial NaOH
    create_step_with_params(recipe, step_num, 'add_component',
                           'Add 10N NaOH for initial pH adjustment',
                           params={
                               'component_id': ('fk_component', str(naoh_10n.id)),
                               'amount_per_liter': ('float', '18'),  # 72mL / 4L
                               'amount_unit': ('string', 'mL')
                           })
    step_num += 1

    # Step 4: Measure pH
    create_step_with_params(recipe, step_num, 'measure_ph',
                           'Measure pH (target 6.6-6.8)',
                           params={'target_ph': ('string', '6.6-6.8')})
    step_num += 1

    # Step 5: Stir
    create_step_with_params(recipe, step_num, 'stir',
                           'Stir for 60 minutes',
                           params={'duration_minutes': ('integer', '60')})
    step_num += 1

    # Step 6: Adjust pH with NaOH or HCl
    create_step_with_params(recipe, step_num, 'adjust_ph',
                           'Adjust pH to 6.7-7.0 using 10N NaOH or 5N HCl as needed',
                           params={'target_ph': ('string', '6.7-7.0')})
    step_num += 1

    # Step 7: Final water fill
    create_step_with_params(recipe, step_num, 'final_water_fill',
                           'Add MilliQ water to target mass (1000g per L)')
    step_num += 1

    # Step 8: Measure pH
    create_step_with_params(recipe, step_num, 'measure_ph',
                           'Record final pH (target 6.6-6.8)',
                           params={'target_ph': ('string', '6.6-6.8')})
    step_num += 1

    # Step 9: Measure osmolality
    create_step_with_params(recipe, step_num, 'measure_osmolality',
                           'Measure osmolality (dilute 1:5 - 20 uL CHO MaxFA + 80 uL MilliQ)',
                           params={'target_osmolality': ('string', '240-300')})
    step_num += 1

    # Step 10: Filter sterilize
    create_step_with_params(recipe, step_num, 'filter_sterilize',
                           'Filter sterilize through 0.22 um filter')

    print(f"  Created recipe: {recipe.recipe_id} - {recipe.recipe_name}")
    print(f"  Total steps: {step_num}")
    return recipe

def import_cho_maxfb():
    """Import CHO MaxFB recipe"""
    print("\nImporting CHO MaxFB recipe...")

    # Create recipe
    recipe = USPMediaRecipe.objects.create(
        recipe_id='RCP0003',
        recipe_name='CHO MaxFB',
        recipe_type='Feed B',
        version='1.0',
        base_volume=0.5,  # 0.5L base from template
        ph_target=11.25,  # midpoint of 11.0-11.5
        osmolality_target=210,  # midpoint of 180-240
        storage_temp='4C',
        shelf_life_days=30,
        active=True
    )

    # Get/create components
    maxfb_powder = get_or_create_component('CHO MaxFB Dry Powder', 'base_powder', 'MB1202.202', 'Manufacturer', 'g')
    naoh_10n = get_or_create_component('10N NaOH', 'base', 'SS255-4', 'Vendor', 'mL')
    hcl_5n = get_or_create_component('5N HCl', 'acid', None, 'Vendor', 'mL')

    step_num = 1

    # Step 1: Initial water fill (70%)
    create_step_with_params(recipe, step_num, 'add_water',
                           'Add 70% of batch weight as MilliQ water (e.g., 350g for 0.5L batch)',
                           params={'target_volume': ('float', '350')})  # mL for 0.5L
    step_num += 1

    # Step 2: Add CHO MaxFB powder
    create_step_with_params(recipe, step_num, 'add_component',
                           'Add CHO MaxFB dry powder slowly while stirring',
                           params={
                               'component_id': ('fk_component', str(maxfb_powder.id)),
                               'amount_per_liter': ('float', '94.5'),  # 47.25g / 0.5L
                               'amount_unit': ('string', 'g')
                           })
    step_num += 1

    # Step 3: Add 10M NaOH
    create_step_with_params(recipe, step_num, 'add_component',
                           'Add 10N NaOH',
                           params={
                               'component_id': ('fk_component', str(naoh_10n.id)),
                               'amount_per_liter': ('float', '80'),  # 40mL / 0.5L
                               'amount_unit': ('string', 'mL')
                           })
    step_num += 1

    # Step 4: Adjust pH with NaOH or HCl
    create_step_with_params(recipe, step_num, 'adjust_ph',
                           'Adjust pH to 11.0-11.5 using 10N NaOH or 5N HCl as needed',
                           params={'target_ph': ('string', '11.0-11.5')})
    step_num += 1

    # Step 5: Measure pH
    create_step_with_params(recipe, step_num, 'measure_ph',
                           'Measure pH (target 11.0-11.5)',
                           params={'target_ph': ('string', '11.0-11.5')})
    step_num += 1

    # Step 6: Stir
    create_step_with_params(recipe, step_num, 'stir',
                           'Stir for 60 minutes',
                           params={'duration_minutes': ('integer', '60')})
    step_num += 1

    # Step 7: Final water fill
    create_step_with_params(recipe, step_num, 'final_water_fill',
                           'Add MilliQ water to target mass (1000g per L)')
    step_num += 1

    # Step 8: Measure osmolality
    create_step_with_params(recipe, step_num, 'measure_osmolality',
                           'Measure osmolality (dilute 1:5 - 20 uL CHO MaxFB + 80 uL MilliQ)',
                           params={'target_osmolality': ('string', '180-240')})
    step_num += 1

    # Step 9: Filter sterilize
    create_step_with_params(recipe, step_num, 'filter_sterilize',
                           'Filter sterilize through 0.22 um filter')

    print(f"  Created recipe: {recipe.recipe_id} - {recipe.recipe_name}")
    print(f"  Total steps: {step_num}")
    return recipe

def import_cho_maxx():
    """Import CHO MaxX recipe"""
    print("\nImporting CHO MaxX recipe...")

    # Create recipe
    recipe = USPMediaRecipe.objects.create(
        recipe_id='RCP0004',
        recipe_name='CHO MaxX Medium',
        recipe_type='Growth Media',
        version='1.0',
        base_volume=6.0,  # 6L base from template
        ph_target=6.85,  # midpoint of 6.7-7.0
        osmolality_target=295,  # midpoint of 270-320
        storage_temp='4C',
        shelf_life_days=30,
        active=True
    )

    # Get/create components
    maxx_powder = get_or_create_component('CHO MaxX Dry Powder', 'base_powder', 'MB1113.201', 'Manufacturer', 'g')
    sodium_bicarb = get_or_create_component('Sodium Bicarbonate', 'buffer', 'S233-3', 'Vendor', 'g')
    naoh_10n = get_or_create_component('10N NaOH', 'base', 'ss256-500', 'Vendor', 'mL')
    hcl_5n = get_or_create_component('5N HCl', 'acid', '5618-03', 'Vendor', 'mL')

    step_num = 1

    # Step 1: Initial water fill (80%)
    create_step_with_params(recipe, step_num, 'initial_water_fill',
                           'Add 80% of batch weight as MilliQ water (e.g., 4800g for 6L batch)')
    step_num += 1

    # Step 2: Add CHO MaxX powder
    create_step_with_params(recipe, step_num, 'add_component',
                           'Add CHO MaxX dry powder slowly while stirring',
                           params={
                               'component_id': ('fk_component', str(maxx_powder.id)),
                               'amount_per_liter': ('float', '20.6'),  # 123.6g / 6L
                               'amount_unit': ('string', 'g')
                           })
    step_num += 1

    # Step 3: Add Sodium Bicarbonate
    create_step_with_params(recipe, step_num, 'add_component',
                           'Add sodium bicarbonate buffer',
                           params={
                               'component_id': ('fk_component', str(sodium_bicarb.id)),
                               'amount_per_liter': ('float', '1.8'),  # 10.8g / 6L
                               'amount_unit': ('string', 'g')
                           })
    step_num += 1

    # Step 4: Add 10N NaOH
    create_step_with_params(recipe, step_num, 'add_component',
                           'Add 10N NaOH for pH adjustment',
                           params={
                               'component_id': ('fk_component', str(naoh_10n.id)),
                               'amount_per_liter': ('float', '4.17'),  # 25mL / 6L
                               'amount_unit': ('string', 'mL')
                           })
    step_num += 1

    # Step 5: Measure pH
    create_step_with_params(recipe, step_num, 'measure_ph',
                           'Measure pH (target 9.0)',
                           params={'target_ph': ('string', '9.0')})
    step_num += 1

    # Step 6: Stir
    create_step_with_params(recipe, step_num, 'stir',
                           'Stir for 10-30 minutes',
                           params={'duration_minutes': ('integer', '20')})  # midpoint
    step_num += 1

    # Step 7: Adjust pH with HCl
    create_step_with_params(recipe, step_num, 'adjust_ph',
                           'Adjust pH to 6.7-7.0 using 5N HCl as needed',
                           params={'target_ph': ('string', '6.7-7.0')})
    step_num += 1

    # Step 8: Measure pH
    create_step_with_params(recipe, step_num, 'measure_ph',
                           'Record pH (target 6.7-7.0)',
                           params={'target_ph': ('string', '6.7-7.0')})
    step_num += 1

    # Step 9: Final water fill
    create_step_with_params(recipe, step_num, 'final_water_fill',
                           'Add MilliQ water to target mass (1000g per L)')
    step_num += 1

    # Step 10: Measure pH
    create_step_with_params(recipe, step_num, 'measure_ph',
                           'Record final NOVA pH (target 6.7-7.0)',
                           params={'target_ph': ('string', '6.7-7.0')})
    step_num += 1

    # Step 11: Measure osmolality
    create_step_with_params(recipe, step_num, 'measure_osmolality',
                           'Measure osmolality',
                           params={'target_osmolality': ('string', '270-320')})
    step_num += 1

    # Step 12: Filter sterilize
    create_step_with_params(recipe, step_num, 'filter_sterilize',
                           'Filter sterilize through 0.22 um filter')

    print(f"  Created recipe: {recipe.recipe_id} - {recipe.recipe_name}")
    print(f"  Total steps: {step_num}")
    return recipe

if __name__ == '__main__':
    print("=" * 80)
    print("Importing recipes from Excel templates")
    print("=" * 80)

    try:
        recipe1 = import_cho_maxfa()
        recipe2 = import_cho_maxfb()
        recipe3 = import_cho_maxx()

        print("\n" + "=" * 80)
        print("SUCCESS! All recipes imported")
        print("=" * 80)
        print(f"\nRecipes created:")
        print(f"  1. {recipe1.recipe_id} - {recipe1.recipe_name} (Feed A) - {recipe1.base_volume}L base")
        print(f"  2. {recipe2.recipe_id} - {recipe2.recipe_name} (Feed B) - {recipe2.base_volume}L base")
        print(f"  3. {recipe3.recipe_id} - {recipe3.recipe_name} (Growth Media) - {recipe3.base_volume}L base")

        # Print summary
        total_recipes = USPMediaRecipe.objects.filter(active=True).count()
        total_steps = USPMediaRecipeStep.objects.count()
        total_params = USPMediaRecipeStepParameter.objects.count()
        total_components = USPMediaComponentLibrary.objects.filter(active=True).count()

        print(f"\nDatabase summary:")
        print(f"  Total recipes: {total_recipes}")
        print(f"  Total steps: {total_steps}")
        print(f"  Total parameters: {total_params}")
        print(f"  Total components: {total_components}")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
