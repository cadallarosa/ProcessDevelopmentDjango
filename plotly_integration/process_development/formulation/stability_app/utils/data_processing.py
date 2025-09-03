"""
Data processing utilities for formulation stability analysis
"""

import pandas as pd
import numpy as np
from scipy import stats
from scipy.optimize import curve_fit
from django.db.models import Q
import logging

from plotly_integration.models import (
    FormulationStudy, FormulationCondition, FormulationSample, 
    FormulationSecResult, FormulationStabilityMetric
)

logger = logging.getLogger(__name__)

def get_formulation_data(formulation_ids, storage_conditions=None):
    """
    Retrieve formulation stability data for analysis
    
    Args:
        formulation_ids: List of FormulationCondition IDs
        storage_conditions: List of storage conditions to filter by
        
    Returns:
        dict: Processed data organized by formulation and storage condition
    """
    try:
        data = {}
        
        for formulation_id in formulation_ids:
            formulation = FormulationCondition.objects.get(id=formulation_id)
            formulation_data = {
                'formulation_info': {
                    'id': formulation.id,
                    'number': formulation.formulation_number,
                    'study': formulation.study.study_id,
                    'buffer_type': formulation.buffer_type,
                    'ph': formulation.ph,
                    'composition': get_formulation_composition(formulation)
                },
                'storage_conditions': {}
            }
            
            # Get samples for this formulation
            samples_query = FormulationSample.objects.filter(formulation=formulation)
            if storage_conditions:
                samples_query = samples_query.filter(storage_condition__in=storage_conditions)
            
            samples = samples_query.order_by('storage_condition', 'time_point_months')
            
            # Organize data by storage condition
            for sample in samples:
                condition = sample.storage_condition
                if condition not in formulation_data['storage_conditions']:
                    formulation_data['storage_conditions'][condition] = {
                        'samples': [],
                        'sec_results': [],
                        'time_points': [],
                        'hmw_values': [],
                        'main_values': [],
                        'lmw_values': [],
                        'tm_values': [],
                        'scattering_onset_values': []
                    }
                
                # Get SEC results for this sample
                sec_results = FormulationSecResult.objects.filter(sample=sample)
                
                for sec_result in sec_results:
                    formulation_data['storage_conditions'][condition]['samples'].append(sample)
                    formulation_data['storage_conditions'][condition]['sec_results'].append(sec_result)
                    formulation_data['storage_conditions'][condition]['time_points'].append(sample.time_point_months)
                    formulation_data['storage_conditions'][condition]['hmw_values'].append(sec_result.hmw_percent)
                    formulation_data['storage_conditions'][condition]['main_values'].append(sec_result.main_percent)
                    formulation_data['storage_conditions'][condition]['lmw_values'].append(sec_result.lmw_percent)
                    
                    if sec_result.tm_celsius:
                        formulation_data['storage_conditions'][condition]['tm_values'].append(sec_result.tm_celsius)
                    if sec_result.scattering_onset:
                        formulation_data['storage_conditions'][condition]['scattering_onset_values'].append(sec_result.scattering_onset)
            
            data[formulation_id] = formulation_data
            
        return data
        
    except Exception as e:
        logger.error(f"Error retrieving formulation data: {e}")
        return {}

def get_formulation_composition(formulation):
    """
    Get a formatted string of formulation composition
    
    Args:
        formulation: FormulationCondition object
        
    Returns:
        str: Formatted composition string
    """
    composition_parts = []
    
    if formulation.buffer_type and formulation.buffer_concentration:
        composition_parts.append(f"{formulation.buffer_concentration}mM {formulation.buffer_type}")
    
    if formulation.arginine_hcl:
        composition_parts.append(f"{formulation.arginine_hcl}mg/mL Arg·HCl")
    
    if formulation.sucrose:
        composition_parts.append(f"{formulation.sucrose}mg/mL Sucrose")
    
    if formulation.sorbitol:
        composition_parts.append(f"{formulation.sorbitol}mg/mL Sorbitol")
    
    if formulation.trehalose:
        composition_parts.append(f"{formulation.trehalose}mg/mL Trehalose")
    
    if formulation.glycine:
        composition_parts.append(f"{formulation.glycine}mg/mL Glycine")
    
    if formulation.polysorbate_80:
        composition_parts.append(f"{formulation.polysorbate_80}mg/mL PS80")
    
    return ", ".join(composition_parts) if composition_parts else "No excipients"

def calculate_degradation_rates(time_points, values, parameter_name):
    """
    Calculate degradation rates using linear regression
    
    Args:
        time_points: List of time points (months)
        values: List of parameter values
        parameter_name: Name of the parameter being analyzed
        
    Returns:
        dict: Statistical analysis results
    """
    try:
        if len(time_points) < 2 or len(values) < 2:
            return None
        
        # Convert to numpy arrays
        x = np.array(time_points)
        y = np.array(values)
        
        # Remove any NaN values
        valid_indices = ~(np.isnan(x) | np.isnan(y))
        x = x[valid_indices]
        y = y[valid_indices]
        
        if len(x) < 2:
            return None
        
        # Perform linear regression
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        # Calculate additional statistics
        r_squared = r_value ** 2
        
        # Calculate half-life for degradation (when applicable)
        half_life = None
        if parameter_name in ['main_percent', 'Main'] and slope != 0:
            # For main peak, calculate time to reach 50% of initial value
            initial_value = y[0] if len(y) > 0 else 100
            half_life = (initial_value * 0.5 - intercept) / slope if slope < 0 else None
        
        return {
            'slope': slope,
            'intercept': intercept,
            'r_squared': r_squared,
            'p_value': p_value,
            'std_error': std_err,
            'half_life_months': half_life,
            'n_points': len(x)
        }
        
    except Exception as e:
        logger.error(f"Error calculating degradation rates for {parameter_name}: {e}")
        return None

def calculate_stability_score(formulation_data, reference_condition='25C'):
    """
    Calculate an overall stability score for a formulation
    
    Args:
        formulation_data: Data for a single formulation
        reference_condition: Reference storage condition for scoring
        
    Returns:
        dict: Stability scoring results
    """
    try:
        scores = {}
        
        for condition, data in formulation_data['storage_conditions'].items():
            if not data['time_points'] or not data['main_values']:
                continue
            
            # Calculate degradation rate for main peak
            main_stats = calculate_degradation_rates(
                data['time_points'], 
                data['main_values'], 
                'main_percent'
            )
            
            # Calculate degradation rate for HMW
            hmw_stats = calculate_degradation_rates(
                data['time_points'], 
                data['hmw_values'], 
                'hmw_percent'
            )
            
            # Base score calculation
            base_score = 100
            
            # Penalize based on main peak loss rate (more negative slope = lower score)
            if main_stats and main_stats['slope'] < 0:
                main_penalty = abs(main_stats['slope']) * 10  # 10 points per %/month loss
                base_score -= min(main_penalty, 50)  # Cap penalty at 50 points
            
            # Penalize based on HMW increase rate
            if hmw_stats and hmw_stats['slope'] > 0:
                hmw_penalty = hmw_stats['slope'] * 15  # 15 points per %/month increase
                base_score -= min(hmw_penalty, 40)  # Cap penalty at 40 points
            
            # Bonus for good fit (high R²)
            if main_stats and main_stats['r_squared'] > 0.8:
                base_score += 5  # Bonus for predictable behavior
            
            # Additional penalties for accelerated conditions
            if condition == '40C':
                base_score *= 0.9  # 10% penalty for harsh condition performance
            elif condition == 'FT':
                base_score *= 0.95  # 5% penalty for freeze/thaw stress
            
            scores[condition] = {
                'stability_score': max(0, min(100, base_score)),
                'main_degradation_rate': main_stats['slope'] if main_stats else None,
                'hmw_increase_rate': hmw_stats['slope'] if hmw_stats else None,
                'main_r_squared': main_stats['r_squared'] if main_stats else None,
                'estimated_shelf_life_months': main_stats['half_life_months'] if main_stats else None
            }
        
        return scores
        
    except Exception as e:
        logger.error(f"Error calculating stability score: {e}")
        return {}

def create_comparison_dataframe(formulation_data_dict):
    """
    Create a comparison DataFrame for multiple formulations
    
    Args:
        formulation_data_dict: Dictionary of formulation data
        
    Returns:
        pd.DataFrame: Comparison dataframe
    """
    try:
        comparison_rows = []
        
        for formulation_id, formulation_data in formulation_data_dict.items():
            formulation_info = formulation_data['formulation_info']
            stability_scores = calculate_stability_score(formulation_data)
            
            for condition, scores in stability_scores.items():
                row = {
                    'Formulation_ID': formulation_id,
                    'Formulation_Number': formulation_info['number'],
                    'Study': formulation_info['study'],
                    'Buffer_Type': formulation_info['buffer_type'],
                    'pH': formulation_info['ph'],
                    'Composition': formulation_info['composition'],
                    'Storage_Condition': condition,
                    'Stability_Score': scores['stability_score'],
                    'Main_Degradation_Rate_per_month': scores['main_degradation_rate'],
                    'HMW_Increase_Rate_per_month': scores['hmw_increase_rate'],
                    'Main_R_Squared': scores['main_r_squared'],
                    'Estimated_Shelf_Life_months': scores['estimated_shelf_life_months']
                }
                comparison_rows.append(row)
        
        return pd.DataFrame(comparison_rows)
        
    except Exception as e:
        logger.error(f"Error creating comparison dataframe: {e}")
        return pd.DataFrame()

def export_stability_data_to_excel(formulation_data_dict, filename):
    """
    Export stability data to Excel format
    
    Args:
        formulation_data_dict: Dictionary of formulation data
        filename: Output filename
    """
    try:
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            # Summary sheet
            summary_df = create_comparison_dataframe(formulation_data_dict)
            summary_df.to_excel(writer, sheet_name='Stability_Summary', index=False)
            
            # Individual formulation sheets
            for formulation_id, formulation_data in formulation_data_dict.items():
                formulation_info = formulation_data['formulation_info']
                sheet_name = f"Form_{formulation_info['number']}"[:31]  # Excel sheet name limit
                
                # Create detailed data for this formulation
                detailed_rows = []
                
                for condition, data in formulation_data['storage_conditions'].items():
                    for i, sample in enumerate(data['samples']):
                        if i < len(data['sec_results']):
                            sec_result = data['sec_results'][i]
                            row = {
                                'Sample_ID': sample.sample_id,
                                'Storage_Condition': condition,
                                'Time_Point_months': sample.time_point_months,
                                'HMW_percent': sec_result.hmw_percent,
                                'Main_percent': sec_result.main_percent,
                                'LMW_percent': sec_result.lmw_percent,
                                'Tm_celsius': sec_result.tm_celsius,
                                'Scattering_Onset': sec_result.scattering_onset,
                                'Concentration_mg_mL': sample.concentration,
                                'pH_measured': sample.ph_measured,
                                'Appearance': sample.appearance
                            }
                            detailed_rows.append(row)
                
                if detailed_rows:
                    detailed_df = pd.DataFrame(detailed_rows)
                    detailed_df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        logger.info(f"Successfully exported stability data to {filename}")
        
    except Exception as e:
        logger.error(f"Error exporting stability data to Excel: {e}")
        raise