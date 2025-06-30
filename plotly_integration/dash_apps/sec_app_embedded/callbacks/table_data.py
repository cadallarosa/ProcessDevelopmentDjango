import numpy as np
import pandas as pd

from plotly_integration.models import Report, SampleMetadata, PeakResults
from ..app import app
from dash import Input, Output, State, html
import dash


@app.callback(
    [Output('hmw-table', 'columns'),
     Output('hmw-table', 'data'),
     Output('hmw-table-store', 'data')],
    [
        Input('hmw-column-selector', 'value'),
        Input("selected-report", "data"),
        Input('main-peak-rt-input', 'value'),
        Input('low-mw-cutoff-input', 'value'),
        Input('regression-parameters', 'data')
    ],
    [State('selected-report', 'data')],
    prevent_initial_call=True
)
def update_hmw_table(selected_columns, report_name, main_peak_rt, low_mw_cutoff, regression_params, selected_report):
    from plotly_integration.models import LimsProjectInformation, TimeSeriesData,SystemInformation

    report_id = report_name or selected_report
    if not report_id:
        return [], [], []

    report = Report.objects.filter(report_id=report_id).first()
    if not report:
        return [], [], []

    selected_result_ids = sorted(
        [sample.strip() for sample in report.selected_result_ids.split(",") if sample.strip()],
        key=lambda x: int(x)
    )

    project = LimsProjectInformation.objects.filter(protein=report.project_id).first()
    expected_mw = project.molecular_weight / 1000 if project else None

    slope = regression_params.get("slope", 0)
    intercept = regression_params.get("intercept", 0)

    summary_data = []

    for result_id in selected_result_ids:
        sample = SampleMetadata.objects.filter(result_id=result_id).first()
        if not sample:
            continue
        injection_volume = sample.injection_volume
        system_name = sample.system_name
        system = SystemInformation.objects.filter(system_name=system_name).first()
        channel_name = system.channel_1
        # print(f'Channel Name:{channel_name}')

        peak_results = PeakResults.objects.filter(result_id=sample.result_id,channel_name=channel_name)
        if not peak_results.exists():
            continue

        df = pd.DataFrame.from_records(peak_results.values())
        if 'peak_retention_time' not in df.columns:
            continue

        df['peak_retention_time'] = pd.to_numeric(df['peak_retention_time'], errors='coerce')
        df = df.dropna(subset=['peak_retention_time'])
        df['area'] = df['area'].astype(float)
        df['peak_start_time'] = df['peak_start_time'].astype(float)
        df['peak_end_time'] = df['peak_end_time'].astype(float)
        df['height'] = df['height'].astype(float)

        try:
            closest_index = (df['peak_retention_time'] - main_peak_rt).abs().idxmin()
        except ValueError:
            continue

        main_peak_row = df.loc[closest_index]
        main_peak_area = round(main_peak_row['area'], 2)
        main_peak_start = main_peak_row['peak_start_time']
        main_peak_end = main_peak_row['peak_end_time']

        hmw_start = df[df['peak_retention_time'] < main_peak_start]['peak_start_time'].min()
        hmw_end = main_peak_start

        lmw_start = main_peak_end
        lmw_end = df[df['peak_retention_time'] > main_peak_end]['peak_end_time'].max()
        if lmw_end > low_mw_cutoff:
            lmw_end = low_mw_cutoff

        df_excluding_main_peak = df.drop(index=closest_index)

        hmw_area = round(
            df_excluding_main_peak[df_excluding_main_peak['peak_retention_time'] < main_peak_rt]['area'].sum(), 2
        )
        lmw_area = round(
            df_excluding_main_peak[
                (df_excluding_main_peak['peak_retention_time'] > main_peak_rt) &
                (df_excluding_main_peak['peak_retention_time'] <= low_mw_cutoff)
                ]['area'].sum(), 2
        )

        total_area = main_peak_area + hmw_area + lmw_area
        total_area_normalized = round(total_area / injection_volume, 2)
        hmw_percent = round((hmw_area / total_area) * 100, 2) if total_area > 0 else 0
        main_peak_percent = round((main_peak_area / total_area) * 100, 2) if total_area > 0 else 0
        lmw_percent = round((lmw_area / total_area) * 100, 2) if total_area > 0 else 0

        if total_area > 0:
            peak_area_cutoff = 1000
            if hmw_percent == 100:
                hmw_percent = f">{round(100 - ((peak_area_cutoff / total_area) * 100), 2)}"
            if main_peak_percent == 100:
                main_peak_percent = f">{round(100 - ((peak_area_cutoff / total_area) * 100), 2)}"
            if lmw_percent == 100:
                lmw_percent = f">{round(100 - ((peak_area_cutoff / total_area) * 100), 2)}"

        # ✅ MW calculation using max point in main peak region from time-series
        try:
            time_series = TimeSeriesData.objects.filter(result_id=sample.result_id).values("time", "channel_1")
            ts_df = pd.DataFrame(time_series)

            # Filter to main peak region
            region_df = ts_df[
                (ts_df['time'] >= main_peak_start) &
                (ts_df['time'] <= main_peak_end)
                ]

            max_row = region_df.loc[region_df['channel_1'].idxmax()]
            max_ret_time = max_row['time']
            log_mw = slope * float(max_ret_time) + intercept
            calc_mw = round(np.exp(log_mw) / 1000, 2)
            mw_deviation = (
                round(((calc_mw - expected_mw) / expected_mw) * 100, 2)
                if expected_mw else "N/A"
            )
        except Exception as e:
            print(f"MW calc failed for {sample.sample_name}: {e}")
            calc_mw = "Error"
            mw_deviation = "Error"

        summary_data.append({
            'Sample Name': sample.sample_name,
            'Main Peak Start': main_peak_start,
            'Main Peak End': main_peak_end,
            'HMW Start': hmw_start,
            'HMW End': hmw_end,
            'LMW Start': lmw_start,
            'LMW End': lmw_end,
            'HMW': hmw_percent,
            'Main Peak': main_peak_percent,
            'LMW': lmw_percent,
            'HMW Area': hmw_area,
            'Main Peak Area': main_peak_area,
            'LMW Area': lmw_area,
            'Total Area': total_area,
            'Injection Volume': injection_volume,
            'Total Area/uL': total_area_normalized,
            'Max Peak Height': round(df['height'].max(), 2),
            'Calculated MW': calc_mw,
            'MW Deviation': mw_deviation
        })

    desired_order = [
        'Sample Name', 'HMW', 'HMW Area', 'HMW Start', 'HMW End',
        'Main Peak', 'Main Peak Area', 'Main Peak Start', 'Main Peak End',
        'LMW', 'LMW Area', 'LMW Start', 'LMW End',
        'Total Area', 'Injection Volume', 'Total Area/uL', 'Max Peak Height',
        'Calculated MW', 'MW Deviation'
    ]

    selected_columns = selected_columns if selected_columns else []
    all_columns = list(set(['Sample Name', 'HMW', 'Main Peak', 'LMW'] + selected_columns))
    ordered_columns = [col for col in desired_order if col in all_columns]

    table_columns = [{"name": col, "id": col} for col in ordered_columns]
    filtered_data = [{col: row[col] for col in ordered_columns if col in row} for row in summary_data]

    return table_columns, filtered_data, summary_data
