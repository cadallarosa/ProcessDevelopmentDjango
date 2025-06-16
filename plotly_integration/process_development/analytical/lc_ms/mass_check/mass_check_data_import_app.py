import base64
import os
import uuid
import numpy as np
from dash import dcc, html, Input, Output, State, dash_table
from django.db import IntegrityError
from django_plotly_dash import DjangoDash
from plotly_integration.models import MassCheckComponent, MassCheckResult
import pandas as pd
import base64
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

# Initialize the Dash app
app = DjangoDash('MassCheckDataImportApp')

# Define Layout
app.layout = html.Div(
    style={
        "fontFamily": "Arial, sans-serif",
        "backgroundColor": "#f4f7f6",
        "padding": "20px",
        "maxWidth": "1000px",
        "margin": "auto",
        "boxShadow": "0px 4px 10px rgba(0, 0, 0, 0.1)",
        "borderRadius": "8px"
    },
    children=[
        html.H1(
            "Mass Check Data Import",
            style={
                "textAlign": "center",
                "color": "#0047b3",
                "marginBottom": "20px"
            }
        ),

        # File Upload Section
        html.Div(
            style={"textAlign": "center", "marginBottom": "20px"},
            children=[
                dcc.Upload(
                    id='upload-data',

                    children=html.Button(
                        '📂 Upload Excel File',
                        style={
                            "backgroundColor": "#0047b3",
                            "color": "white",
                            "padding": "10px 20px",
                            "border": "none",
                            "borderRadius": "5px",
                            "cursor": "pointer",
                            "fontSize": "16px"
                        }
                    ),
                    multiple=True
                ),
                html.Div(id='file-name', style={"marginTop": "10px", "fontWeight": "bold", "color": "green"})
            ]
        ),

        # Preview Data Table
        html.H3("Preview Data", style={"color": "#0047b3", "marginTop": "20px"}),
        dash_table.DataTable(
            id='data-preview',
            columns=[],  # Populated dynamically
            data=[],
            page_size=15,
            style_table={"overflowX": "auto"},
            style_header={
                "backgroundColor": "#0047b3",
                "color": "white",
                "fontWeight": "bold"
            },
            style_cell={
                "padding": "10px",
                "textAlign": "center",
                "borderBottom": "1px solid #ccc"
            },
            style_data={"backgroundColor": "white", "color": "#333"}
        ),

        # Import Button (Initially Hidden)
        html.Div(
            style={"textAlign": "center", "marginTop": "20px"},
            children=[
                html.Button(
                    "⬇️ Import Data to Database",
                    id="save-button",
                    n_clicks=0,
                    style={
                        "display": "none",
                        "backgroundColor": "#28a745",
                        "color": "white",
                        "padding": "10px 20px",
                        "border": "none",
                        "borderRadius": "5px",
                        "cursor": "pointer",
                        "fontSize": "16px"
                    }
                )
            ]
        ),

        # Import Status
        html.Div(
            id='save-status',
            style={
                "textAlign": "center",
                "marginTop": "20px",
                "fontSize": "18px",
                "fontWeight": "bold"
            }
        )
    ]
)

def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    file_path = default_storage.save(f"uploads/{filename}", ContentFile(decoded))

    try:
        df = pd.read_csv(default_storage.path(file_path))
    except Exception as e:
        return f"❌ Error reading file: {e}", None

    relevant_columns = [
        'Protein name', 'Observed RT (min)', 'Response',
        'Expected mass (Da)', 'Observed mass (Da)',
        'Mass error (mDa)', 'Mass error (ppm)'
    ]

    df_cleaned = df[relevant_columns].copy()

    df_cleaned.rename(columns={
        'Protein name': 'protein_name',
        'Observed RT (min)': 'observed_rt_min',
        'Response': 'response',
        'Expected mass (Da)': 'expected_mass_da',
        'Observed mass (Da)': 'observed_mass_da',
        'Mass error (mDa)': 'mass_error_mda',
        'Mass error (ppm)': 'mass_error_ppm'
    }, inplace=True)

    numeric_columns = [
        'observed_rt_min', 'response', 'expected_mass_da',
        'observed_mass_da', 'mass_error_mda', 'mass_error_ppm'
    ]
    df_cleaned[numeric_columns] = df_cleaned[numeric_columns].apply(pd.to_numeric, errors='coerce')

    return "✅ File parsed successfully", df_cleaned


@app.callback(
    [Output('data-preview', 'columns'),
     Output('data-preview', 'data'),
     Output('file-name', 'children'),
     Output('save-button', 'style')],
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=True
)
def update_output(contents_list, filenames):
    if contents_list and filenames:
        preview_frames = []
        for contents, filename in zip(contents_list, filenames):
            status_msg, df_cleaned = parse_contents(contents, filename)
            if df_cleaned is not None:
                df_cleaned.insert(0, 'filename', filename)
                preview_frames.append(df_cleaned)

        if not preview_frames:
            return [], [], "❌ No valid data found.", {'display': 'none'}

        combined_df = pd.concat(preview_frames, ignore_index=True)
        columns = [{"name": i, "id": i} for i in combined_df.columns]
        data = combined_df.to_dict('records')

        return columns, data, f"✅ Files Ready: {', '.join(filenames)}", {'display': 'block'}

    return [], [], "No files uploaded.", {'display': 'none'}


@app.callback(
    Output('save-status', 'children'),
    Input('save-button', 'n_clicks'),
    State('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=True
)
def save_to_db(n_clicks, contents_list, filenames):
    if not contents_list or not filenames:
        return "No files to import."

    try:
        total_records = 0
        for contents, filename in zip(contents_list, filenames):
            status_msg, df = parse_contents(contents, filename)
            if df is None:
                continue

            df = df.replace({np.nan: None})
            result_id = uuid.uuid5(uuid.NAMESPACE_DNS, filename).hex
            result_name = os.path.splitext(filename)[0]

            # Create MassCheckResult
            MassCheckResult.objects.update_or_create(
                result_id=result_id,
                defaults={"result_name": result_name}
            )

            # Create MassCheckComponent entries
            new_records = [
                MassCheckComponent(
                    result_id=result_id,
                    protein_name=row['protein_name'],
                    expected_mass_da=row['expected_mass_da'],
                    observed_mass_da=row['observed_mass_da'],
                    mass_error_mda=row['mass_error_mda'],
                    mass_error_ppm=row['mass_error_ppm'],
                    observed_rt_min=row['observed_rt_min'],
                    response=row['response']
                ) for _, row in df.iterrows()
            ]

            MassCheckComponent.objects.bulk_create(new_records, ignore_conflicts=True)
            total_records += len(new_records)

        return f"✅ Successfully inserted {total_records} records."

    except Exception as e:
        return f"❌ Error importing data: {str(e)}"
