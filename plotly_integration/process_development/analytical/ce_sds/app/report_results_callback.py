from datetime import datetime

from .app import app
from dash import Input, Output, State

from plotly_integration.models import CESDSReport, LimsSampleAnalysis, LimsCeSdsResult


@app.callback(
    [Output("status-message", "children", allow_duplicate=True),
     Output("status-message", "style", allow_duplicate=True),
     Output("button-success-trigger", "data"),
     Output("button-reset-interval", "disabled")],
    [Input("report-results-btn", "n_clicks")],
    [State("reduced-table", "data"),
     State("nonreduced-table", "data"),
     State("selected-report", "data"),
     State("button-success-trigger", "data"),
     State("standard-regression-params", "data")],  # ADD: Get regression parameters
    prevent_initial_call=True
)
def save_to_lims(n_clicks, reduced_data, nonreduced_data, selected_report, current_trigger, regression_params):
    print('=' * 50)
    print('SAVE TO LIMS CALLBACK TRIGGERED')
    print(f'n_clicks: {n_clicks}')
    print(f'selected_report: {selected_report}')
    print(f'reduced_data length: {len(reduced_data) if reduced_data else 0}')
    print(f'nonreduced_data length: {len(nonreduced_data) if nonreduced_data else 0}')
    print(f'regression_params: {regression_params}')
    print('=' * 50)

    if (not reduced_data and not nonreduced_data) or not selected_report:
        print('No data or report name - returning early')
        return "⚠️ No data to link!", {
            "display": "block",
            "backgroundColor": "#f8d7da",
            "color": "#721c24",
            "border": "1px solid #f5c6cb",
            "padding": "10px 20px",
            "margin": "10px 20px",
            "borderRadius": "5px"
        }, current_trigger, True

    try:
        # Get report info
        print(f'Looking for report with name: {selected_report}')
        report = CESDSReport.objects.filter(id=selected_report).first()
        if report:
            project_id = report.project_id
            print(f'Found report - project_id: {project_id}')
        else:
            project_id = "Unknown"
            print('Report not found - using Unknown project_id')

        saved_count = 0
        errors = []
        skipped_controls = []

        # Dictionary to combine reduced and non-reduced data by sample ID
        combined_samples = {}

        # Process reduced samples WITH MW DATA
        if reduced_data:
            print(f'\nProcessing {len(reduced_data)} reduced samples...')
            for idx, row in enumerate(reduced_data):
                print(f'\nReduced Row {idx}: {row}')
                sample_name = row.get("Sample Name", "")
                print(f'Sample name: "{sample_name}"')

                # Skip control samples
                if any(control in sample_name.upper() for control in ['BLK', 'IGG', 'STD', 'BLANK', 'CONTROL']):
                    print(f'Skipping control sample: {sample_name}')
                    skipped_controls.append(sample_name)
                    continue

                # Remove R prefix if present
                clean_sample_name = sample_name
                if sample_name.startswith('R '):
                    clean_sample_name = sample_name[2:].strip()
                elif sample_name.startswith('R'):
                    clean_sample_name = sample_name[1:].strip()
                print(f'Clean sample name: "{clean_sample_name}"')

                try:
                    # Get percentage values
                    lmw = row.get("LMW (%)", 0)
                    hmw = row.get("HMW (%)", 0)
                    light_chain = row.get("Light Chain (%)", 0)
                    heavy_chain = row.get("Heavy Chain (%)", 0)

                    # NEW: Get MW values
                    lmw_mw = row.get("LMW MW (kDa)", None)
                    lc_mw = row.get("Light Chain MW (kDa)", None)
                    hc_mw = row.get("Heavy Chain MW (kDa)", None)
                    hmw_mw = row.get("HMW MW (kDa)", None)

                    print(f'Raw values - LMW: {lmw}, HMW: {hmw}, LC: {light_chain}, HC: {heavy_chain}')
                    print(f'MW values - LMW MW: {lmw_mw}, LC MW: {lc_mw}, HC MW: {hc_mw}, HMW MW: {hmw_mw}')

                    # Convert to float, handling None and empty strings
                    lmw = float(lmw) if lmw not in [None, '', 'None'] else 0
                    hmw = float(hmw) if hmw not in [None, '', 'None'] else 0
                    light_chain = float(light_chain) if light_chain not in [None, '', 'None'] else 0
                    heavy_chain = float(heavy_chain) if heavy_chain not in [None, '', 'None'] else 0

                    # Convert MW values
                    lmw_mw = float(lmw_mw) if lmw_mw not in [None, '', 'None'] else None
                    lc_mw = float(lc_mw) if lc_mw not in [None, '', 'None'] else None
                    hc_mw = float(hc_mw) if hc_mw not in [None, '', 'None'] else None
                    hmw_mw = float(hmw_mw) if hmw_mw not in [None, '', 'None'] else None

                    # Initialize sample entry if not exists
                    if clean_sample_name not in combined_samples:
                        combined_samples[clean_sample_name] = {
                            'original_names': [],
                            'methods': {},
                            'purity': None
                        }

                    # UPDATED: Add reduced method data WITH MW
                    combined_samples[clean_sample_name]['original_names'].append(sample_name)
                    combined_samples[clean_sample_name]['methods']['reduced'] = {
                        "peaks": {
                            "LMW": {
                                "value": lmw,
                                "unit": "%",
                                "molecular_weight": lmw_mw
                            },
                            "Light Chain": {
                                "value": light_chain,
                                "unit": "%",
                                "molecular_weight": lc_mw
                            },
                            "Heavy Chain": {
                                "value": heavy_chain,
                                "unit": "%",
                                "molecular_weight": hc_mw
                            },
                            "HMW": {
                                "value": hmw,
                                "unit": "%",
                                "molecular_weight": hmw_mw
                            }
                        },
                        "total_peaks": 4
                    }

                    # Calculate purity for reduced (main chain components)
                    purity = 100 - lmw - hmw
                    combined_samples[clean_sample_name]['purity'] = purity
                    print(f'Calculated purity: {purity}')

                except Exception as e:
                    print(f'ERROR processing reduced sample {sample_name}: {str(e)}')
                    import traceback
                    traceback.print_exc()
                    errors.append(f"{sample_name} (reduced): {str(e)}")

        # Process non-reduced samples WITH MW DATA
        if nonreduced_data:
            print(f'\nProcessing {len(nonreduced_data)} non-reduced samples...')
            for idx, row in enumerate(nonreduced_data):
                print(f'\nNon-reduced Row {idx}: {row}')
                sample_name = row.get("Sample Name", "")
                print(f'Sample name: "{sample_name}"')

                # Skip control samples
                if any(control in sample_name.upper() for control in ['BLK', 'IGG', 'STD', 'BLANK', 'CONTROL']):
                    print(f'Skipping control sample: {sample_name}')
                    skipped_controls.append(sample_name)
                    continue

                # Remove NR prefix if present
                clean_sample_name = sample_name
                if sample_name.startswith('NR '):
                    clean_sample_name = sample_name[3:].strip()
                elif sample_name.startswith('NR'):
                    clean_sample_name = sample_name[2:].strip()
                print(f'Clean sample name: "{clean_sample_name}"')

                try:
                    # Get percentage values
                    lmw = row.get("LMW (%)", 0)
                    hmw = row.get("HMW (%)", 0)
                    light_chain = row.get("Light Chain (%)", 0)
                    intact = row.get("Intact (%)", 0)

                    # NEW: Get MW values
                    lmw_mw = row.get("LMW MW (kDa)", None)
                    lc_mw = row.get("Light Chain MW (kDa)", None)
                    intact_mw = row.get("Intact MW (kDa)", None)  # KEY VALUE for display
                    hmw_mw = row.get("HMW MW (kDa)", None)

                    print(f'Raw values - LMW: {lmw}, HMW: {hmw}, LC: {light_chain}, Intact: {intact}')
                    print(f'MW values - LMW MW: {lmw_mw}, LC MW: {lc_mw}, Intact MW: {intact_mw}, HMW MW: {hmw_mw}')

                    # Convert percentage values to float
                    lmw = float(lmw) if lmw not in [None, '', 'None'] else 0
                    hmw = float(hmw) if hmw not in [None, '', 'None'] else 0
                    light_chain = float(light_chain) if light_chain not in [None, '', 'None'] else 0
                    intact = float(intact) if intact not in [None, '', 'None'] else 0

                    # Convert MW values
                    lmw_mw = float(lmw_mw) if lmw_mw not in [None, '', 'None'] else None
                    lc_mw = float(lc_mw) if lc_mw not in [None, '', 'None'] else None
                    intact_mw = float(intact_mw) if intact_mw not in [None, '', 'None'] else None
                    hmw_mw = float(hmw_mw) if hmw_mw not in [None, '', 'None'] else None

                    # Initialize sample entry if not exists
                    if clean_sample_name not in combined_samples:
                        combined_samples[clean_sample_name] = {
                            'original_names': [],
                            'methods': {},
                            'purity': None
                        }

                    # UPDATED: Add non-reduced method data WITH MW
                    combined_samples[clean_sample_name]['original_names'].append(sample_name)
                    combined_samples[clean_sample_name]['methods']['non_reduced'] = {
                        "peaks": {
                            "LMW": {
                                "value": lmw,
                                "unit": "%",
                                "molecular_weight": lmw_mw
                            },
                            "Light Chain": {
                                "value": light_chain,
                                "unit": "%",
                                "molecular_weight": lc_mw
                            },
                            "Intact": {
                                "value": intact,
                                "unit": "%",
                                "molecular_weight": intact_mw  # KEY: Intact MW for display
                            },
                            "HMW": {
                                "value": hmw,
                                "unit": "%",
                                "molecular_weight": hmw_mw
                            }
                        },
                        "total_peaks": 4
                    }

                    # Calculate purity for non-reduced if not already set
                    if combined_samples[clean_sample_name]['purity'] is None:
                        purity = 100 - lmw - hmw
                        combined_samples[clean_sample_name]['purity'] = purity
                        print(f'Calculated purity: {purity}')

                except Exception as e:
                    print(f'ERROR processing non-reduced sample {sample_name}: {str(e)}')
                    import traceback
                    traceback.print_exc()
                    errors.append(f"{sample_name} (non-reduced): {str(e)}")

        # Now save the combined data to LIMS
        print(f'\n=== SAVING COMBINED DATA ===')
        print(f'Total unique samples to save: {len(combined_samples)}')

        for clean_sample_name, sample_data in combined_samples.items():
            try:
                print(f'\nProcessing combined sample: {clean_sample_name}')
                print(f'Original names: {sample_data["original_names"]}')
                print(f'Methods available: {list(sample_data["methods"].keys())}')

                # UPDATED: Create comprehensive band pattern with MW data and regression info
                band_pattern = {
                    "methods": sample_data['methods'],
                    "original_names": sample_data['original_names'],
                    "analysis_date": datetime.now().isoformat(),
                    "instrument": "CE-SDS",
                    "total_methods": len(sample_data['methods']),
                    "regression_parameters": regression_params if regression_params else None
                    # NEW: Add regression params
                }

                print(f'Combined band pattern: {band_pattern}')

                # Create or update LIMS records
                print(f'Creating/updating LimsSampleAnalysis for sample_id: {clean_sample_name}')
                lims_sample, created = LimsSampleAnalysis.objects.update_or_create(
                    sample_id=clean_sample_name,
                    defaults={
                        'sample_type': 2,  # FB samples
                        'project_id': project_id,
                        'analyst': report.user_id if report else 'Unknown',
                        'sample_date': datetime.now().date(),
                        'description': f'CE-SDS analysis from report {selected_report}'
                    }
                )
                print(f'LimsSampleAnalysis {"created" if created else "updated"}: {lims_sample.sample_id}')

                # Determine notes based on available methods
                method_list = list(sample_data['methods'].keys())
                if len(method_list) == 2:
                    notes = 'CE-SDS analysis (both reduced and non-reduced)'
                elif 'reduced' in method_list:
                    notes = 'CE-SDS analysis (reduced only)'
                else:
                    notes = 'CE-SDS analysis (non-reduced only)'

                print(f'Creating/updating LimsCeSdsResult...')

                # Get or create the CESDSReport (assuming it should exist)
                try:
                    cesds_report = CESDSReport.objects.get(id=selected_report)
                    print(f'Found CESDSReport: {cesds_report.report_name}')
                except CESDSReport.DoesNotExist:
                    print(f'CESDSReport with ID {selected_report} not found')
                    cesds_report = None

                cesds_result, created = LimsCeSdsResult.objects.update_or_create(
                    sample_id=lims_sample,
                    defaults={
                        'purity': sample_data['purity'],
                        'band_pattern': band_pattern,
                        'notes': notes,
                        'status': 'completed',
                        'report': cesds_report  # Use the CESDSReport object, not the ID
                    }
                )
                print(f'LimsCeSdsResult {"created" if created else "updated"}')

                # Update the OneToOne relationship in LimsSampleAnalysis
                lims_sample.ce_sds_result = cesds_result
                lims_sample.save()
                print(f'Updated LimsSampleAnalysis with ce_sds_result relationship')

                saved_count += 1
                print(f'Successfully saved combined sample {clean_sample_name}')

            except Exception as e:
                print(f'ERROR processing combined sample {clean_sample_name}: {str(e)}')
                import traceback
                traceback.print_exc()
                errors.append(f"{clean_sample_name}: {str(e)}")

        # ... rest of the function remains the same (summary, status messages, etc.)
        print(f'\n=== SUMMARY ===')
        print(f'Total saved: {saved_count}')
        print(f'Skipped controls: {len(skipped_controls)} - {skipped_controls}')
        print(f'Errors: {len(errors)} - {errors}')

        # Prepare status message
        message_parts = []
        if saved_count > 0:
            message_parts.append(f"✅ Linked {saved_count} CE-SDS results to LIMS")
        if skipped_controls:
            message_parts.append(f"⚠️ Skipped {len(skipped_controls)} control samples: {', '.join(skipped_controls)}")
        if errors:
            error_msg = f"❌ Errors: {'; '.join(errors[:3])}"
            if len(errors) > 3:
                error_msg += f" and {len(errors) - 3} more..."
            message_parts.append(error_msg)

        message = " | ".join(message_parts) if message_parts else "No samples processed"

        # Determine style based on results
        if errors and not saved_count:
            style = {
                "display": "block",
                "backgroundColor": "#f8d7da",
                "color": "#721c24",
                "border": "1px solid #f5c6cb",
                "padding": "10px 20px",
                "margin": "10px 20px",
                "borderRadius": "5px"
            }
        elif errors or skipped_controls:
            style = {
                "display": "block",
                "backgroundColor": "#fff3cd",
                "color": "#856404",
                "border": "1px solid #ffeeba",
                "padding": "10px 20px",
                "margin": "10px 20px",
                "borderRadius": "5px"
            }
        else:
            style = {
                "display": "block",
                "backgroundColor": "#d4edda",
                "color": "#155724",
                "border": "1px solid #c3e6cb",
                "padding": "10px 20px",
                "margin": "10px 20px",
                "borderRadius": "5px"
            }

        return message, style, current_trigger + 1, False

    except Exception as e:
        print(f'MAIN EXCEPTION: {str(e)}')
        import traceback
        traceback.print_exc()
        return f"❌ Error linking to LIMS: {str(e)}", {
            "display": "block",
            "backgroundColor": "#f8d7da",
            "color": "#721c24",
            "border": "1px solid #f5c6cb",
            "padding": "10px 20px",
            "margin": "10px 20px",
            "borderRadius": "5px"
        }, current_trigger, True
