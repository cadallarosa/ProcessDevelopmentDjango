"""
Analysis Callbacks
Generate molecule cards from template data
"""

from dash import Input, Output, State, html
from dash.exceptions import PreventUpdate
import pandas as pd
from collections import defaultdict

from ..utils.data_fetchers import batch_fetch_samples
from ..utils.peak_detection import detect_main_peak, calculate_peak_areas
from ..utils.image_helper import get_molecule_image_url
from ..components.molecule_card import create_molecule_card, create_error_card


def register_analysis_callbacks(app):
    """Register analysis generation callbacks"""

    @app.callback(
        [Output('results-container', 'children'),
         Output('export-ppt-btn-container', 'style'),
         Output('analysis-results-store', 'data')],
        [Input('generate-from-template-btn', 'n_clicks'),
         Input('apply-settings-btn', 'n_clicks')],
        [State('template-data-store', 'data'),
         State('channel-settings-store', 'data'),
         State('peak-options-ps', 'value'),
         State('show-trend-store', 'data'),
         State('x-axis-range-store', 'data'),
         State('image-height-store', 'data'),
         State('plot-width-store', 'data')],
        prevent_initial_call=True
    )
    def generate_analysis(n_clicks_generate, n_clicks_settings, template_data, channels, peak_options,
                         show_trend, x_axis_range, image_height, plot_height):
        """
        Generate analysis from template data

        Args:
            n_clicks_generate: Generate button clicks
            n_clicks_settings: Apply settings button clicks
            template_data: List of dicts from uploaded template
            channels: Selected channels to plot
            peak_options: Peak display options (shading, percentages)
            show_trend: Whether to show stability trend plot
            x_axis_range: X-axis range [min, max]
            image_height: Molecule image height in pixels
            plot_height: Plot height in pixels

        Returns:
            Tuple of (molecule_cards, export_btn_style, analysis_data)
        """
        print("\n" + "="*80)
        print("GENERATE ANALYSIS CALLBACK")
        print("="*80)

        if not template_data:
            raise PreventUpdate

        try:
            # Convert to DataFrame for easier processing
            df = pd.DataFrame(template_data)
            print(f"✓ Template data: {len(df)} samples")
            print(f"✓ Channels: {channels}")
            print(f"✓ Peak options: {peak_options}")
            print(f"✓ Show trend: {show_trend}")
            print(f"✓ X-axis range: {x_axis_range}")
            print(f"✓ Image height: {image_height}")
            print(f"✓ Plot height: {plot_height}")

            # Group by Molecule ID
            molecules = df['Molecule ID'].unique()
            print(f"✓ Found {len(molecules)} molecules: {list(molecules)}")

            # Fetch all data in batch (optimize database queries)
            all_result_ids = df['Result ID'].tolist()
            batch_data = batch_fetch_samples(all_result_ids)

            # Process each molecule
            molecule_cards = []

            for idx, molecule_id in enumerate(molecules, 1):
                print(f"\n{'='*60}")
                print(f"MOLECULE {idx}/{len(molecules)}: {molecule_id}")
                print(f"{'='*60}")

                mol_df = df[df['Molecule ID'] == molecule_id].copy()
                print(f"Samples: {len(mol_df)}")

                try:
                    # Process this molecule
                    card = process_molecule(
                        molecule_id=molecule_id,
                        mol_df=mol_df,
                        batch_data=batch_data,
                        channels=channels or ['channel_1'],
                        show_shading='shading' in (peak_options or []),
                        show_trend=show_trend if show_trend is not None else False,
                        x_axis_range=x_axis_range or [4, 12],
                        image_height=image_height or 225,
                        plot_height=plot_height or 600
                    )
                    molecule_cards.append(card)

                except Exception as e:
                    print(f"✗ Error processing {molecule_id}: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    # Add error card
                    molecule_cards.append(create_error_card(molecule_id, str(e)))

            print(f"\n{'='*80}")
            print(f"✓ SUCCESS: Generated {len(molecule_cards)} molecule cards")
            print("="*80 + "\n")

            # Store analysis data for export
            analysis_data = {
                'template_data': template_data,
                'molecules': list(molecules),
                'channels': channels,
                'show_trend': show_trend
            }

            # Show export button
            export_btn_style = {'display': 'block'}

            return molecule_cards, export_btn_style, analysis_data

        except Exception as e:
            error_msg = f"Error generating analysis: {str(e)}"
            print(f"\n✗ {error_msg}")
            import traceback
            traceback.print_exc()
            print("="*80 + "\n")

            error_div = html.Div(
                error_msg,
                style={'color': '#dc2626', 'fontWeight': '600', 'padding': '20px',
                       'backgroundColor': '#fee2e2', 'borderRadius': '12px', 'marginTop': '20px'}
            )

            return error_div, {'display': 'none'}, None


def process_molecule(molecule_id, mol_df, batch_data, channels, show_shading, show_trend=True,
                     x_axis_range=None, image_height=225, plot_height=600):
    """
    Process one molecule and create its card

    Args:
        molecule_id: Molecule identifier
        mol_df: DataFrame with samples for this molecule
        batch_data: Batch-fetched database data
        channels: Channels to plot
        show_shading: Whether to show peak shading
        show_trend: Whether to show trend plot
        x_axis_range: X-axis range [min, max]
        image_height: Molecule image height in pixels
        plot_height: Plot height in pixels

    Returns:
        Molecule card component
    """
    print(f"\n→ Processing {molecule_id}")

    # Get molecule image
    image_url = get_molecule_image_url(molecule_id)
    print(f"  Image URL: {image_url}")

    # Group by condition (Matrix)
    conditions = mol_df['Matrix'].unique()
    print(f"  Conditions: {list(conditions)}")

    # Store reference RTs for auto mode (Day 0 reference for each condition)
    reference_rts = {}

    # Organize data by condition
    conditions_data = defaultdict(list)

    for condition in conditions:
        print(f"\n  → Condition: {condition}")
        cond_df = mol_df[mol_df['Matrix'] == condition].sort_values('Day')

        # First pass: Find Day 0 reference RT for auto mode
        day_0_samples = cond_df[cond_df['Day'] == 0]
        if not day_0_samples.empty:
            # Get first Day 0 sample for reference
            day_0_row = day_0_samples.iloc[0]
            result_id = day_0_row['Result ID']
            peak_rt_type = int(day_0_row.get('Peak RT Type', 0))
            user_peak_rt = day_0_row.get('Peak RT')

            # Get data for Day 0
            if result_id in batch_data and batch_data[result_id]['found']:
                peaks_df = batch_data[result_id]['peaks_df']

                # Detect main peak for Day 0
                if peak_rt_type == 0:
                    # Auto mode: Find highest peak (or closest to user RT if specified)
                    if pd.notna(user_peak_rt):
                        peak_info = detect_main_peak(peaks_df, mode=1, reference_rt=float(user_peak_rt))
                    else:
                        peak_info = detect_main_peak(peaks_df, mode=0, reference_rt=None)
                elif peak_rt_type == 1:
                    # Manual RT
                    peak_info = detect_main_peak(peaks_df, mode=1, reference_rt=float(user_peak_rt))
                else:
                    # Highest peak
                    peak_info = detect_main_peak(peaks_df, mode=2)

                if peak_info:
                    reference_rts[condition] = peak_info['main_peak_rt']
                    print(f"    Day 0 reference RT: {reference_rts[condition]:.3f}")

        # Second pass: Process all samples
        for _, row in cond_df.iterrows():
            result_id = row['Result ID']
            day = row['Day']
            peak_rt_type = int(row.get('Peak RT Type', 0))
            user_peak_rt = row.get('Peak RT')

            print(f"    Processing: Day {day}, Result ID {result_id}, Mode {peak_rt_type}")

            # Get batch data
            if result_id not in batch_data or not batch_data[result_id]['found']:
                print(f"      ✗ No data found")
                continue

            sample_info = batch_data[result_id]
            peaks_df = sample_info['peaks_df']
            ts_df = sample_info['timeseries_df']

            # Detect main peak based on mode
            if peak_rt_type == 0:
                # Auto mode
                if day == 0:
                    # Day 0: Already calculated above, use reference
                    if condition in reference_rts:
                        peak_info = detect_main_peak(peaks_df, mode=1, reference_rt=reference_rts[condition])
                    else:
                        if pd.notna(user_peak_rt):
                            peak_info = detect_main_peak(peaks_df, mode=1, reference_rt=float(user_peak_rt))
                        else:
                            peak_info = detect_main_peak(peaks_df, mode=0, reference_rt=None)
                else:
                    # Day 3+: Use Day 0 reference
                    ref_rt = reference_rts.get(condition)
                    if ref_rt:
                        peak_info = detect_main_peak(peaks_df, mode=0, reference_rt=ref_rt)
                    else:
                        print(f"      ⚠ No Day 0 reference, using highest peak")
                        peak_info = detect_main_peak(peaks_df, mode=2)

            elif peak_rt_type == 1:
                # Manual RT
                if pd.notna(user_peak_rt):
                    peak_info = detect_main_peak(peaks_df, mode=1, reference_rt=float(user_peak_rt))
                else:
                    print(f"      ⚠ Manual mode but no Peak RT, using highest peak")
                    peak_info = detect_main_peak(peaks_df, mode=2)

            else:
                # Highest peak (mode 2)
                peak_info = detect_main_peak(peaks_df, mode=2)

            # Calculate peak areas
            if peak_info:
                peak_areas = calculate_peak_areas(peaks_df, peak_info['main_peak_index'])

                if peak_areas:
                    conditions_data[condition].append({
                        'day': day,
                        'result_id': result_id,
                        'timeseries_df': ts_df,
                        'peak_areas': peak_areas
                    })
                    print(f"      ✓ Monomer: {peak_areas['monomer_pct']}%")
                else:
                    print(f"      ✗ Could not calculate peak areas")
            else:
                print(f"      ✗ Could not detect main peak")

    # Create molecule card
    print(f"\n  → Creating card for {molecule_id}")
    card = create_molecule_card(
        molecule_id=molecule_id,
        molecule_image_url=image_url,
        conditions_data=dict(conditions_data),
        channels=channels,
        show_shading=show_shading,
        show_trend=show_trend,
        x_axis_range=x_axis_range or [4, 12],
        image_height=image_height,
        plot_height=plot_height
    )

    print(f"  ✓ Card created successfully")
    return card
