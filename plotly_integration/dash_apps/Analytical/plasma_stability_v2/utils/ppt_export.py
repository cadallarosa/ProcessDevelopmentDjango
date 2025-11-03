"""
PowerPoint Export
Generate PowerPoint presentation from molecule analysis data
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
import io
import pandas as pd
from typing import Dict, List
from datetime import datetime
import requests
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

from .data_fetchers import batch_fetch_samples
from .peak_detection import detect_main_peak, calculate_peak_areas
from .image_helper import get_molecule_image_url




def create_chromatogram_matplotlib(condition_name, sample_data, channels, x_axis_range=None,
                                   width_inches=4.0, height_inches=6.9):
    """
    Create chromatogram plot directly with matplotlib for PowerPoint export

    Args:
        condition_name: Name of condition (e.g., "Plasma", "Buffer")
        sample_data: List of dicts with {day, timeseries_df, peak_areas}
        channels: List of channel names to plot
        x_axis_range: X-axis range [min, max] in minutes
        width_inches: Plot width in inches
        height_inches: Plot height in inches

    Returns:
        BytesIO stream with PNG image
    """
    if x_axis_range is None:
        x_axis_range = [4, 12]

    # Create figure with exact dimensions
    plt_fig, ax = plt.subplots(figsize=(width_inches, height_inches), dpi=150)

    # Color palette (matches Plotly)
    colors = ['#3b82f6', '#f97316', '#10b981', '#ec4899', '#8b5cf6', '#f59e0b']

    # Plot each sample
    for idx, sample in enumerate(sample_data):
        ts_data = sample['timeseries_df']
        day = sample['day']
        color = colors[idx % len(colors)]

        for channel in channels:
            if channel in ts_data.columns:
                day_label = f'D{day}'
                ax.plot(ts_data['time'], ts_data[channel],
                       label=day_label, color=color, linewidth=1)

    # Title
    ax.set_title(f"{condition_name} - Stability", fontsize=14, fontweight='bold',
                color='#374151', pad=10)

    # Axis labels
    ax.set_xlabel("Time (Minutes)", fontsize=11, color='#374151')
    ax.set_ylabel("UV280 (AU)", fontsize=11, color='#374151')

    # Set x-axis range
    ax.set_xlim(x_axis_range)

    # Legend
    legend = ax.legend(loc='upper right', framealpha=0.9,
                      edgecolor='#e5e7eb', fancybox=False,
                      fontsize=10, frameon=True)
    legend.get_frame().set_linewidth(1)

    # Grid
    ax.grid(True, alpha=0.3, color='#f3f4f6', linewidth=1)
    ax.set_axisbelow(True)

    # Background colors
    ax.set_facecolor('white')
    plt_fig.patch.set_facecolor('white')

    # Spine styling - only show left and bottom
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#d1d5db')
    ax.spines['left'].set_linewidth(1)
    ax.spines['bottom'].set_color('#d1d5db')
    ax.spines['bottom'].set_linewidth(1)

    # Tick styling
    ax.tick_params(axis='both', which='major', labelsize=9, colors='#6b7280',
                  direction='out', length=4, width=1)

    # Save to bytes
    img_stream = io.BytesIO()
    plt_fig.savefig(img_stream, format='png', dpi=150, bbox_inches='tight',
                   facecolor='white', edgecolor='none', pad_inches=0.1)
    plt.close(plt_fig)
    img_stream.seek(0)

    return img_stream


def create_trend_matplotlib(molecule_id, conditions_data, width_inches=5.0, height_inches=2.0):
    """
    Create stability trend plot directly with matplotlib for PowerPoint export

    Args:
        molecule_id: Molecule identifier for title
        conditions_data: Dict mapping condition name to list of sample data
        width_inches: Plot width in inches
        height_inches: Plot height in inches

    Returns:
        BytesIO stream with PNG image
    """
    # Create figure with exact dimensions
    plt_fig, ax = plt.subplots(figsize=(width_inches, height_inches), dpi=150)

    # Color palette
    colors = ['#ec4899', '#10b981', '#3b82f6', '#f59e0b', '#8b5cf6']

    # Plot each condition
    for idx, (condition, samples) in enumerate(sorted(conditions_data.items())):
        if not samples:
            continue

        days = [s['day'] for s in samples]
        monomer_pcts = [s.get('peak_areas', {}).get('monomer_pct', 0) for s in samples]

        color = colors[idx % len(colors)]
        ax.plot(days, monomer_pcts, label=condition, color=color,
               linewidth=3, marker='o', markersize=10)

    # Title
    ax.set_title(f"{molecule_id} - Stability Trend", fontsize=14, fontweight='bold',
                color='#374151', pad=10)

    # Axis labels
    ax.set_xlabel("Day", fontsize=11, color='#374151')
    ax.set_ylabel("Monomer (%)", fontsize=11, color='#374151')

    # Y-axis range
    ax.set_ylim([0, 100])

    # Legend
    legend = ax.legend(loc='upper right', framealpha=0.9,
                      edgecolor='#e5e7eb', fancybox=False,
                      fontsize=10, frameon=True)
    legend.get_frame().set_linewidth(1)

    # Grid
    ax.grid(True, alpha=0.3, color='#f3f4f6', linewidth=1)
    ax.set_axisbelow(True)

    # Background colors
    ax.set_facecolor('white')
    plt_fig.patch.set_facecolor('white')

    # Spine styling
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#d1d5db')
    ax.spines['left'].set_linewidth(1)
    ax.spines['bottom'].set_color('#d1d5db')
    ax.spines['bottom'].set_linewidth(1)

    # Tick styling
    ax.tick_params(axis='both', which='major', labelsize=9, colors='#6b7280',
                  direction='out', length=4, width=1)

    # Save to bytes
    img_stream = io.BytesIO()
    plt_fig.savefig(img_stream, format='png', dpi=150, bbox_inches='tight',
                   facecolor='white', edgecolor='none', pad_inches=0.1)
    plt.close(plt_fig)
    img_stream.seek(0)

    return img_stream


def create_powerpoint(template_data: List[Dict], analysis_data: Dict) -> bytes:
    """
    Create PowerPoint presentation from analysis data

    Args:
        template_data: List of sample dictionaries from Excel template
        analysis_data: Analysis settings and metadata

    Returns:
        bytes: PowerPoint file content
    """
    print("\n" + "="*80)
    print("CREATING POWERPOINT PRESENTATION")
    print("="*80)

    # Create presentation (16:9 widescreen)
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # Process data
    df = pd.DataFrame(template_data)
    molecules = df['Molecule ID'].unique()
    all_result_ids = df['Result ID'].tolist()

    print(f"Molecules to export: {list(molecules)}")

    # Batch fetch all data
    batch_data = batch_fetch_samples(all_result_ids)

    # Create a slide for each molecule
    for molecule_id in molecules:
        print(f"\n  → Creating slide for {molecule_id}")
        mol_df = df[df['Molecule ID'] == molecule_id].copy()

        try:
            create_molecule_slide(
                prs=prs,
                molecule_id=molecule_id,
                mol_df=mol_df,
                batch_data=batch_data,
                analysis_data=analysis_data,
                x_axis_range=analysis_data.get('x_axis_range', [4, 12])
            )
            print(f"    ✓ Slide created for {molecule_id}")
        except Exception as e:
            print(f"    ✗ Error creating slide for {molecule_id}: {e}")
            import traceback
            traceback.print_exc()

    # Save to bytes
    ppt_bytes = io.BytesIO()
    prs.save(ppt_bytes)
    ppt_bytes.seek(0)

    print(f"\n✓ PowerPoint created successfully with {len(molecules)} slides")
    print("="*80 + "\n")

    return ppt_bytes.getvalue()


def create_molecule_slide(prs, molecule_id, mol_df, batch_data, analysis_data, x_axis_range=None):
    """
    Create one slide for a molecule
    Layout matches web app: Left 30% (image, trend, table), Right 70% (2 plots side by side)

    Args:
        prs: Presentation object
        molecule_id: Molecule identifier
        mol_df: DataFrame with samples for this molecule
        batch_data: Batch-fetched database data
        analysis_data: Analysis settings
        x_axis_range: X-axis range [min, max]
    """
    if x_axis_range is None:
        x_axis_range = [4, 12]
    # Add blank slide
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # Blank layout

    # Calculate layout dimensions
    left_x = 0.2
    left_width = 4.75

    # Title (centered over image column, black font)
    title_box = slide.shapes.add_textbox(
        Inches(left_x), Inches(0.1),
        Inches(left_width), Inches(0.4)
    )
    title_frame = title_box.text_frame
    title_frame.text = molecule_id
    title_para = title_frame.paragraphs[0]
    title_para.font.size = Pt(28)
    title_para.font.bold = True
    title_para.font.color.rgb = RGBColor(0, 0, 0)  # Black
    title_para.alignment = PP_ALIGN.CENTER

    # Get analysis settings
    peak_mode = analysis_data.get('peak_mode', 'auto')
    channels = analysis_data.get('channels', ['channel_1'])

    # Process molecule data by condition
    conditions_data = {}
    conditions = sorted(mol_df['Matrix'].unique())

    # Store reference RTs for auto mode (Day 0 reference for each condition)
    reference_rts = {}

    for condition in conditions:
        cond_df = mol_df[mol_df['Matrix'] == condition].sort_values('Day')

        # First pass: Find Day 0 reference RT for auto mode
        day_0_samples = cond_df[cond_df['Day'] == 0]
        if not day_0_samples.empty:
            day_0_row = day_0_samples.iloc[0]
            result_id = day_0_row['Result ID']
            peak_rt_type = int(day_0_row.get('Peak RT Type', 0))
            user_peak_rt = day_0_row.get('Peak RT')

            # Get data for Day 0
            if result_id in batch_data and batch_data[result_id]['found']:
                peaks_df = batch_data[result_id]['peaks_df']

                # Detect main peak for Day 0
                if peak_rt_type == 0:
                    # Auto mode
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

        # Second pass: Process all samples
        samples = []
        for _, row in cond_df.iterrows():
            result_id = row['Result ID']
            day = row['Day']
            peak_rt_type = int(row.get('Peak RT Type', 0))
            user_peak_rt = row.get('Peak RT')

            # Get data from batch
            if result_id not in batch_data or not batch_data[result_id].get('found'):
                continue

            ts_data = batch_data[result_id].get('timeseries_df')
            peaks_df = batch_data[result_id].get('peaks_df')

            if ts_data is None or ts_data.empty:
                continue

            # Detect main peak based on mode (same logic as web app)
            if peak_rt_type == 0:
                # Auto mode
                if day == 0:
                    # Day 0: Use reference
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
                        peak_info = detect_main_peak(peaks_df, mode=2)

            elif peak_rt_type == 1:
                # Manual RT
                if pd.notna(user_peak_rt):
                    peak_info = detect_main_peak(peaks_df, mode=1, reference_rt=float(user_peak_rt))
                else:
                    peak_info = detect_main_peak(peaks_df, mode=2)

            else:
                # Highest peak (mode 2)
                peak_info = detect_main_peak(peaks_df, mode=2)

            # Calculate peak areas
            peak_areas = None
            if peak_info:
                peak_areas = calculate_peak_areas(peaks_df, peak_info['main_peak_index'])

            if peak_areas:
                samples.append({
                    'day': day,
                    'timeseries_df': ts_data,
                    'peak_areas': peak_areas
                })

        if samples:
            conditions_data[condition] = sorted(samples, key=lambda x: x['day'])

    # Calculate positions based on plot alignment
    plot_y = 0.3  # Plots centered vertically on 7.5" slide
    plot_height = 6.9
    plot_bottom = plot_y + plot_height  # = 7.2"

    # Table positioned so bottom aligns with plot bottom
    table_height = 1.5
    table_y = plot_bottom - table_height  # = 5.7"

    # Image centered vertically between title bottom (0.5") and table top
    title_bottom = 0.5
    image_height = 2.75  # Changed from 2.5"
    table_header_height = 0.3
    table_top = table_y - table_header_height
    image_y = (title_bottom + table_top) / 2 - (image_height / 2)

    # Image centered horizontally in left column (left_x to left_x + left_width)
    # Will be calculated after image is loaded to get actual width

    # Download and add molecule image (aspect ratio locked, centered in left column)
    try:
        image_url = get_molecule_image_url(molecule_id)
        if image_url.startswith('http'):
            response = requests.get(image_url, timeout=10)
            if response.status_code == 200:
                img_stream = io.BytesIO(response.content)
                # Add picture with locked aspect ratio (only height specified)
                pic = slide.shapes.add_picture(
                    img_stream,
                    Inches(0), Inches(0),  # Temp position
                    height=Inches(image_height)
                )
                # Center horizontally in left column
                pic.left = Inches(left_x + (left_width - pic.width / 914400) / 2)  # 914400 EMUs per inch
                pic.top = Inches(image_y)
    except Exception as e:
        print(f"    Warning: Could not add image for {molecule_id}: {e}")

    # Add trend plot below image
    show_trend = analysis_data.get('show_trend', False)
    trend_y = image_y + image_height + 0.2
    trend_width = 5.0
    trend_height = 2.0

    if show_trend and conditions_data:
        try:
            # Create trend plot directly with matplotlib
            trend_stream = create_trend_matplotlib(molecule_id, conditions_data,
                                                   width_inches=trend_width, height_inches=trend_height)

            if trend_stream:
                slide.shapes.add_picture(
                    trend_stream,
                    Inches(left_x), Inches(trend_y),
                    width=Inches(trend_width),
                    height=Inches(trend_height)
                )
                print(f"    ✓ Added trend plot (matplotlib)")
        except Exception as e:
            print(f"    Warning: Could not add trend plot: {e}")

    # RIGHT SIDE: Two chromatogram plots side by side (centered vertically)
    right_x_start = left_x + left_width + 0.2
    plot_width = 4.0

    for idx, condition in enumerate(sorted(conditions)):
        samples = conditions_data.get(condition, [])
        if not samples:
            continue

        # Position: side by side (idx 0 = left, idx 1 = right plot shifted 0.5" left)
        x_pos = right_x_start + (idx * (plot_width - 0.3))

        # Create chromatogram plot directly with matplotlib
        try:
            img_stream = create_chromatogram_matplotlib(
                condition_name=condition,
                sample_data=samples,
                channels=channels,
                x_axis_range=x_axis_range,
                width_inches=plot_width,
                height_inches=plot_height
            )

            if img_stream:
                slide.shapes.add_picture(
                    img_stream,
                    Inches(x_pos), Inches(plot_y),
                    width=Inches(plot_width),
                    height=Inches(plot_height)
                )
                print(f"    ✓ Added plot for {condition} (matplotlib)")
        except Exception as e:
            print(f"    ✗ Error creating plot for {condition}: {e}")
            # Add placeholder text if plot creation fails
            plot_box = slide.shapes.add_textbox(
                Inches(x_pos), Inches(plot_y),
                Inches(plot_width), Inches(plot_height)
            )
            plot_frame = plot_box.text_frame
            plot_frame.text = f"[{condition} Chromatogram Plot]\n\nError: {str(e)}"
            plot_frame.paragraphs[0].alignment = PP_ALIGN.CENTER

    # Add results table (bottom aligned with plot bottom at 7.2")
    table_data = create_results_table_data(conditions_data)
    if table_data:
        # Add table section header above table
        table_header_y = table_y - 0.3
        table_header = slide.shapes.add_textbox(
            Inches(left_x), Inches(table_header_y),
            Inches(left_width), Inches(0.3)
        )
        table_header_frame = table_header.text_frame
        table_header_frame.text = "Monomer % by SEC"
        para = table_header_frame.paragraphs[0]
        para.font.size = Pt(16)  # Changed from 14pt
        para.font.bold = True
        para.font.color.rgb = RGBColor(55, 65, 81)  # #374151

        add_results_table(slide, table_data, left_x, table_y, left_width)


def create_results_table_data(conditions_data):
    """Create data for results table"""
    table_data = []

    for condition, samples in sorted(conditions_data.items()):
        row = {'Condition': condition}
        for sample in samples:
            day = sample['day']
            peak_areas = sample.get('peak_areas')
            if peak_areas:
                monomer_pct = peak_areas.get('monomer_pct', 0)
                row[f'D{day}'] = f"{monomer_pct:.1f}%"
            else:
                row[f'D{day}'] = "N/A"
        table_data.append(row)

    return table_data


def add_results_table(slide, table_data, x_position=0.2, y_position=5.1, width=4.75):
    """Add results table to slide with PowerPoint's Medium Style 1"""
    if not table_data:
        return

    # Get all day columns
    all_days = set()
    for row in table_data:
        all_days.update([k for k in row.keys() if k.startswith('D')])
    all_days = sorted(all_days, key=lambda x: int(x[1:]))

    rows = len(table_data) + 1  # +1 for header
    cols = len(all_days) + 1  # +1 for condition column

    # Create table
    table_shape = slide.shapes.add_table(
        rows, cols,
        Inches(x_position), Inches(y_position),
        Inches(width), Inches(1.5)
    )
    table = table_shape.table

    # Apply PowerPoint's built-in Medium Style 1
    # Access the XML element to set the style
    graphic_frame = table_shape._element
    tbl = graphic_frame.graphic.graphicData.tbl

    # Find the tableStyleId element and set its text to Medium Style 1
    ns = {'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
    style_elem = tbl.tblPr.find('.//a:tableStyleId', ns)
    if style_elem is not None:
        style_elem.text = "{793D81CF-94F2-401A-BA57-92F5A7B2D0C5}"  # Medium Style 1

    # Enable first row formatting
    table.first_row = True

    # Header row text
    table.cell(0, 0).text = "Matrix"
    for col_idx, day in enumerate(all_days):
        table.cell(0, col_idx + 1).text = day

    # Set header row font size to 16pt
    for col_idx in range(cols):
        cell = table.cell(0, col_idx)
        cell.text_frame.paragraphs[0].font.size = Pt(16)

    # Data rows
    for row_idx, row_data in enumerate(table_data):
        # First column (Condition)
        cell = table.cell(row_idx + 1, 0)
        cell.text = row_data['Condition']
        cell.text_frame.paragraphs[0].font.size = Pt(14)

        # Data columns
        for col_idx, day in enumerate(all_days):
            value = row_data.get(day, "N/A")
            cell = table.cell(row_idx + 1, col_idx + 1)
            cell.text = value
            # Center align the data
            cell.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
            cell.text_frame.paragraphs[0].font.size = Pt(14)

def export_molecule_data_to_ppt(
    molecule_id: str,
    conditions_data: Dict,
    image_url: str
) -> dict:
    """
    Export single molecule data (for future enhancement)

    Args:
        molecule_id: Molecule identifier
        conditions_data: Conditions and sample data
        image_url: URL to molecule image

    Returns:
        dict: Export data for PowerPoint generation
    """
    return {
        'molecule_id': molecule_id,
        'image_url': image_url,
        'conditions': list(conditions_data.keys()),
        'sample_count': sum(len(samples) for samples in conditions_data.values())
    }
