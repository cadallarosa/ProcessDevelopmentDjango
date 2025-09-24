"""
CLD Clonality Report Analyzer App
Advanced image analysis tool for clonality reports with PDF viewing and automated cell counting
"""

import dash
from dash import dcc, html, Input, Output, State, no_update
from dash.exceptions import PreventUpdate
from django_plotly_dash import DjangoDash
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import base64
import io
import cv2
import numpy as np
from PIL import Image
import pandas as pd
from datetime import datetime
import os

# Try to import additional libraries, with fallbacks for missing dependencies
try:
    from sklearn.cluster import DBSCAN
    from scipy import ndimage
    from skimage import feature, segmentation, measure, filters, morphology
    ADVANCED_CV_AVAILABLE = True
except ImportError:
    print("Advanced computer vision libraries not available. Basic analysis only.")
    ADVANCED_CV_AVAILABLE = False

try:
    import fitz  # PyMuPDF for PDF handling
    PDF_SUPPORT = True
except ImportError:
    print("PyMuPDF not available. PDF features disabled.")
    PDF_SUPPORT = False

# Initialize the Django Dash app
app = DjangoDash("ClonalityReportAnalyzer", external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
], suppress_callback_exceptions=True)

# PDF file path
PDF_PATH = r"C:\Users\cdallarosa\DataAlchemy\djangoProject\plotly_integration\cld\clonality_report\Clonality Report_05_06_2025_top8.pdf"

def encode_pdf_as_base64(pdf_path):
    """Encode PDF file as base64 for embedding in HTML"""
    try:
        with open(pdf_path, "rb") as pdf_file:
            encoded = base64.b64encode(pdf_file.read()).decode()
        return encoded
    except Exception as e:
        print(f"Error encoding PDF: {e}")
        return None

def extract_images_from_pdf(pdf_path):
    """Extract images from PDF pages"""
    images = []

    if not PDF_SUPPORT:
        print("PDF extraction not available. PyMuPDF not installed.")
        return []

    try:
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            image_list = page.get_images()

            for img_index, img in enumerate(image_list):
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)

                if pix.n - pix.alpha < 4:  # GRAY or RGB
                    img_data = pix.tobytes("png")
                    img_b64 = base64.b64encode(img_data).decode()

                    images.append({
                        'page': page_num + 1,
                        'image_index': img_index,
                        'data': img_b64,
                        'width': pix.width,
                        'height': pix.height
                    })
                pix = None
        doc.close()
    except Exception as e:
        print(f"Error extracting images: {e}")

    return images

def load_test_image():
    """Load a test cell image for demonstration when PDF is not available"""
    # Create a simple test image with circles representing cells
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    img.fill(128)  # Gray background

    # Add some circular "cells"
    centers = [(50, 50), (150, 60), (80, 120), (160, 140)]

    for i, (x, y) in enumerate(centers):
        cv2.circle(img, (x, y), 15, (80, 80, 80), -1)  # Filled circle
        cv2.circle(img, (x, y), 15, (60, 60, 60), 2)   # Border

    # Convert to PIL and encode
    img_pil = Image.fromarray(img)
    buffer = io.BytesIO()
    img_pil.save(buffer, format='PNG')
    img_b64 = base64.b64encode(buffer.getvalue()).decode()

    return [{
        'page': 1,
        'image_index': 0,
        'data': img_b64,
        'width': 200,
        'height': 200,
        'is_test': True
    }]

def count_cells_in_image(image_data):
    """
    Advanced cell counting using multiple computer vision techniques
    """
    try:
        # Decode base64 image
        img_bytes = base64.b64decode(image_data)
        img = Image.open(io.BytesIO(img_bytes))
        img_array = np.array(img)

        # Convert to grayscale
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array

        # Multiple detection methods
        cell_counts = {}

        # Method 1: Circular Hough Transform (good for round cells)
        try:
            circles = cv2.HoughCircles(
                gray,
                cv2.HOUGH_GRADIENT,
                dp=1,
                minDist=int(gray.shape[0]/10),
                param1=50,
                param2=30,
                minRadius=int(gray.shape[0]/50),
                maxRadius=int(gray.shape[0]/8)
            )

            hough_count = 0 if circles is None else len(circles[0])
            cell_counts['hough_circles'] = hough_count
        except:
            cell_counts['hough_circles'] = 0

        # Method 2: Blob detection
        try:
            # Setup SimpleBlobDetector parameters
            params = cv2.SimpleBlobDetector_Params()
            params.filterByArea = True
            params.minArea = 50
            params.maxArea = 5000
            params.filterByCircularity = True
            params.minCircularity = 0.3
            params.filterByConvexity = True
            params.minConvexity = 0.5

            detector = cv2.SimpleBlobDetector_create(params)
            keypoints = detector.detect(gray)
            cell_counts['blob_detection'] = len(keypoints)
        except:
            cell_counts['blob_detection'] = 0

        # Method 3: Contour-based detection
        try:
            # Apply Gaussian blur and threshold
            blurred = cv2.GaussianBlur(gray, (11, 11), 0)
            _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Find contours
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Filter contours by area and circularity
            valid_contours = []
            for contour in contours:
                area = cv2.contourArea(contour)
                if 50 < area < 5000:  # Filter by area
                    perimeter = cv2.arcLength(contour, True)
                    if perimeter > 0:
                        circularity = 4 * np.pi * area / (perimeter ** 2)
                        if circularity > 0.3:  # Filter by circularity
                            valid_contours.append(contour)

            cell_counts['contour_detection'] = len(valid_contours)
        except:
            cell_counts['contour_detection'] = 0

        # Method 4: Watershed segmentation
        try:
            # Distance transform
            dist_transform = cv2.distanceTransform(thresh, cv2.DIST_L2, 5)
            _, sure_fg = cv2.threshold(dist_transform, 0.4*dist_transform.max(), 255, 0)

            # Find seed points
            sure_fg = np.uint8(sure_fg)
            markers = cv2.connectedComponents(sure_fg)[1]

            # Apply watershed
            markers = cv2.watershed(cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR), markers)

            # Count regions (subtract background)
            watershed_count = len(np.unique(markers)) - 2  # -1 for background, -1 for boundary
            watershed_count = max(0, watershed_count)
            cell_counts['watershed'] = watershed_count
        except:
            cell_counts['watershed'] = 0

        # Calculate consensus count (weighted average)
        weights = {
            'hough_circles': 0.3,
            'blob_detection': 0.3,
            'contour_detection': 0.2,
            'watershed': 0.2
        }

        weighted_sum = sum(count * weights[method] for method, count in cell_counts.items())
        consensus_count = round(weighted_sum)

        # Additional confidence scoring
        counts_list = list(cell_counts.values())
        std_dev = np.std(counts_list) if len(counts_list) > 1 else 0
        confidence = max(0, 100 - (std_dev * 10))  # Higher std dev = lower confidence

        return {
            'consensus_count': consensus_count,
            'confidence': round(confidence, 1),
            'method_counts': cell_counts,
            'image_stats': {
                'width': gray.shape[1],
                'height': gray.shape[0],
                'mean_intensity': np.mean(gray),
                'std_intensity': np.std(gray)
            }
        }

    except Exception as e:
        print(f"Error in cell counting: {e}")
        return {
            'consensus_count': 0,
            'confidence': 0,
            'method_counts': {},
            'image_stats': {},
            'error': str(e)
        }

def create_annotated_image(image_data, cell_analysis):
    """Create an annotated version of the image showing detected cells"""
    try:
        # Decode image
        img_bytes = base64.b64decode(image_data)
        img = Image.open(io.BytesIO(img_bytes))
        img_array = np.array(img)

        # Convert to BGR for OpenCV
        if len(img_array.shape) == 3:
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
            img_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

        # Detect circles using Hough transform
        circles = cv2.HoughCircles(
            gray,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=int(gray.shape[0]/10),
            param1=50,
            param2=30,
            minRadius=int(gray.shape[0]/50),
            maxRadius=int(gray.shape[0]/8)
        )

        # Draw circles
        if circles is not None:
            circles = np.round(circles[0, :]).astype("int")
            for i, (x, y, r) in enumerate(circles):
                cv2.circle(img_bgr, (x, y), r, (0, 255, 0), 2)
                cv2.circle(img_bgr, (x, y), 2, (0, 0, 255), 3)
                cv2.putText(img_bgr, f'{i+1}', (x-10, y-r-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 0), 2)

        # Convert back to RGB and encode
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)

        buffer = io.BytesIO()
        img_pil.save(buffer, format='PNG')
        encoded_img = base64.b64encode(buffer.getvalue()).decode()

        return encoded_img

    except Exception as e:
        print(f"Error creating annotated image: {e}")
        return image_data

# App layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Clonality Report Analyzer", className="text-center mb-4"),
            html.Hr(),
        ], width=12)
    ]),

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H4("PDF Report Upload & Options")),
                dbc.CardBody([
                    # Upload component
                    dcc.Upload(
                        id='upload-pdf',
                        children=html.Div([
                            'Drag and Drop or ',
                            html.A('Select PDF File')
                        ]),
                        style={
                            'width': '100%',
                            'height': '60px',
                            'lineHeight': '60px',
                            'borderWidth': '2px',
                            'borderStyle': 'dashed',
                            'borderRadius': '5px',
                            'textAlign': 'center',
                            'margin': '10px 0',
                            'backgroundColor': '#f8f9fa'
                        },
                        multiple=False
                    ),
                    html.Div(id="upload-status", className="mb-3"),

                    # Debug div to show upload state
                    html.Div(id="upload-debug", style={"fontSize": "12px", "color": "#666"}),

                    dbc.ButtonGroup([
                        dbc.Button(
                            "📄 View in Modal",
                            id="open-pdf-modal",
                            color="primary",
                            className="me-2",
                            n_clicks=0
                        ),
                        dbc.Button(
                            "🔗 Open PDF File",
                            id="open-pdf-external",
                            color="info",
                            className="me-2",
                            n_clicks=0
                        ),
                        dbc.Button(
                            "👁️ Toggle Embedded View",
                            id="toggle-embedded",
                            color="secondary",
                            n_clicks=0
                        )
                    ], className="mb-3"),
                    html.Div(id="pdf-info", className="mb-2"),
                    html.Div(id="pdf-link", className="mb-2")
                ])
            ])
        ], width=6),

        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H4("Report Approval")),
                dbc.CardBody([
                    dbc.Checklist(
                        options=[{"label": "✅ Approve Report", "value": "approved"}],
                        value=[],
                        id="approval-checkbox",
                        style={"fontSize": "18px"}
                    ),
                    html.Div(id="approval-status", className="mt-3"),
                    dbc.Button(
                        "💾 Save Approval Status",
                        id="save-approval",
                        color="success",
                        className="mt-3"
                    )
                ])
            ])
        ], width=6)
    ], className="mb-4"),

    # Simple PDF viewer section (always visible)
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H4("PDF Viewer")),
                dbc.CardBody([
                    html.Iframe(
                        id="simple-pdf-iframe",
                        style={"width": "100%", "height": "500px", "border": "1px solid #ddd"}
                    )
                ])
            ])
        ], width=12)
    ], className="mb-4"),

    # Embedded PDF viewer section (collapsible)
    dbc.Row([
        dbc.Col([
            dbc.Collapse([
                dbc.Card([
                    dbc.CardHeader(html.H4("Alternative PDF Viewer")),
                    dbc.CardBody([
                        html.Iframe(
                            id="embedded-pdf-iframe",
                            style={"width": "100%", "height": "600px", "border": "1px solid #ddd"}
                        )
                    ])
                ])
            ], id="embedded-pdf-collapse", is_open=False)
        ], width=12)
    ], className="mb-4", style={"display": "none"}),  # Hide the collapsible one for now

    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader([
                    html.H4("Cell Analysis Dashboard"),
                    dbc.Button("🔍 Analyze All Images", id="analyze-btn", color="info", className="float-end")
                ]),
                dbc.CardBody([
                    html.Div(id="analysis-results"),
                    dcc.Loading(
                        id="loading-analysis",
                        children=[html.Div(id="loading-output")],
                        type="default"
                    )
                ])
            ])
        ], width=12)
    ], className="mb-4"),

    # Modal for PDF viewing
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Clonality Report - Full View")),
        dbc.ModalBody([
            html.Iframe(
                id="pdf-iframe",
                style={"width": "100%", "height": "80vh", "border": "none"}
            )
        ], style={"padding": "0"}),
        dbc.ModalFooter([
            dbc.Button("Close", id="close-pdf-modal", color="secondary")
        ])
    ], id="pdf-modal", size="xl", is_open=False),

    # Store components
    dcc.Store(id="images-store"),
    dcc.Store(id="analysis-store"),
    dcc.Store(id="approval-store"),
    dcc.Store(id="uploaded-pdf-store")  # Store for uploaded PDF

], fluid=True)

# Callbacks
# Callback for file upload
@app.callback(
    Output("uploaded-pdf-store", "data"),
    Output("upload-status", "children"),
    [Input("upload-pdf", "contents")],
    [State("upload-pdf", "filename")]
)
def upload_pdf(contents, filename):
    print(f"Upload callback triggered. Filename: {filename}, Contents: {contents is not None}")

    if contents is not None:
        try:
            print(f"Processing uploaded file: {filename}")

            # Check if it's a PDF
            if not filename.lower().endswith('.pdf'):
                return None, dbc.Alert(f"❌ Please upload a PDF file. Got: {filename}", color="warning")

            # Parse the uploaded file
            if ',' in contents:
                content_type, content_string = contents.split(',', 1)
            else:
                content_string = contents

            print(f"Content type: {content_type if ',' in contents else 'raw'}")
            print(f"Content string length: {len(content_string)}")

            # Store the base64 PDF data
            stored_data = {
                'filename': filename,
                'data': content_string
            }

            success_msg = dbc.Alert([
                html.H6("✅ Upload Successful!", className="alert-heading"),
                html.P(f"File: {filename}"),
                html.Hr(),
                html.P(f"Size: {len(content_string) / 1024:.1f} KB", className="mb-0")
            ], color="success", dismissable=True)

            print(f"Successfully stored PDF: {filename}")
            return stored_data, success_msg

        except Exception as e:
            print(f"Error in upload_pdf: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, dbc.Alert(f"❌ Error uploading file: {str(e)}", color="danger", dismissable=True)

    print("No contents provided")
    return dash.no_update, dash.no_update

# Debug callback to show upload state
@app.callback(
    Output("upload-debug", "children"),
    [Input("uploaded-pdf-store", "data")]
)
def show_upload_debug(stored_data):
    if stored_data:
        return html.Pre(f"Stored PDF: {stored_data.get('filename', 'Unknown')}\nData length: {len(stored_data.get('data', ''))} chars")
    return "No PDF uploaded yet"

# Simple callback to display PDF immediately upon upload or on load
@app.callback(
    Output("simple-pdf-iframe", "src"),
    [Input("uploaded-pdf-store", "data"),
     Input("simple-pdf-iframe", "id")]  # Trigger on component mount
)
def display_simple_pdf(stored_data, _):
    # First try uploaded PDF
    if stored_data and stored_data.get('data'):
        print(f"Displaying uploaded PDF in simple iframe: {stored_data.get('filename')}")
        return f"data:application/pdf;base64,{stored_data['data']}"

    # Then try default PDF
    if os.path.exists(PDF_PATH):
        print(f"Displaying default PDF in simple iframe: {PDF_PATH}")
        pdf_base64 = encode_pdf_as_base64(PDF_PATH)
        if pdf_base64:
            return f"data:application/pdf;base64,{pdf_base64}"

    print("No PDF available to display")
    return ""

# Callback for PDF link display
@app.callback(
    Output("pdf-link", "children"),
    Output("pdf-info", "children"),
    [Input("uploaded-pdf-store", "data")]
)
def display_pdf_info(uploaded_pdf):
    if uploaded_pdf and uploaded_pdf.get('data'):
        # Display uploaded PDF info
        filename = uploaded_pdf.get('filename', 'Uploaded PDF')
        pdf_data = uploaded_pdf.get('data')
        file_size = len(base64.b64decode(pdf_data)) / (1024 * 1024)  # Convert to MB

        pdf_info = html.Div([
            html.P(f"📄 File: {filename}", style={"marginBottom": "5px"}),
            html.P(f"📏 Size: {file_size:.2f} MB", style={"marginBottom": "5px"}),
            html.P("📤 Uploaded file", style={"fontSize": "12px", "color": "#666"})
        ])
        return html.P(f"📁 {filename}"), pdf_info
    elif os.path.exists(PDF_PATH):
        # Display default PDF info
        file_size = os.path.getsize(PDF_PATH) / (1024 * 1024)  # Convert to MB
        pdf_link = html.A(
            f"📁 {os.path.basename(PDF_PATH)}",
            href=f"file:///{PDF_PATH.replace(os.sep, '/')}",
            target="_blank",
            style={"fontSize": "14px", "textDecoration": "none"}
        )
        pdf_info = html.Div([
            html.P(f"📄 File: {os.path.basename(PDF_PATH)}", style={"marginBottom": "5px"}),
            html.P(f"📏 Size: {file_size:.2f} MB", style={"marginBottom": "5px"}),
            html.P(f"📂 Path: {PDF_PATH}", style={"fontSize": "12px", "color": "#666"})
        ])
        return pdf_link, pdf_info
    else:
        return html.P("❌ No PDF loaded", style={"color": "red"}), html.P("Upload a PDF or ensure default path exists")

# Callback for toggling embedded PDF view
@app.callback(
    Output("embedded-pdf-collapse", "is_open"),
    Output("embedded-pdf-iframe", "src"),
    [Input("toggle-embedded", "n_clicks")],
    [State("embedded-pdf-collapse", "is_open"),
     State("uploaded-pdf-store", "data")]
)
def toggle_embedded_pdf(n_clicks, is_open, uploaded_pdf):
    if n_clicks and n_clicks > 0:
        if not is_open:
            # Load PDF when opening - prefer uploaded PDF
            if uploaded_pdf and uploaded_pdf.get('data'):
                pdf_src = f"data:application/pdf;base64,{uploaded_pdf['data']}"
                return True, pdf_src
            elif os.path.exists(PDF_PATH):
                pdf_base64 = encode_pdf_as_base64(PDF_PATH)
                if pdf_base64:
                    pdf_src = f"data:application/pdf;base64,{pdf_base64}"
                    return True, pdf_src
            return True, ""
        else:
            # Close the embedded view
            return False, ""
    return is_open, ""

# Callback for external PDF open button
@app.callback(
    Output("open-pdf-external", "children"),
    [Input("open-pdf-external", "n_clicks")]
)
def handle_external_open(n_clicks):
    if n_clicks and os.path.exists(PDF_PATH):
        try:
            import webbrowser
            webbrowser.open(f"file:///{PDF_PATH.replace(os.sep, '/')}")
        except Exception as e:
            print(f"Error opening PDF externally: {e}")
    return "🔗 Open PDF File"

@app.callback(
    Output("pdf-modal", "is_open"),
    Output("pdf-iframe", "src"),
    [Input("open-pdf-modal", "n_clicks"), Input("close-pdf-modal", "n_clicks")],
    [State("pdf-modal", "is_open"),
     State("uploaded-pdf-store", "data")]
)
def toggle_pdf_modal(open_clicks, close_clicks, is_open, uploaded_pdf):
    ctx = dash.callback_context
    if not ctx.triggered:
        return is_open, ""

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == "open-pdf-modal" and open_clicks and open_clicks > 0:
        # Opening modal - load PDF (prefer uploaded)
        if uploaded_pdf and uploaded_pdf.get('data'):
            print(f"Loading uploaded PDF: {uploaded_pdf.get('filename')}")
            pdf_src = f"data:application/pdf;base64,{uploaded_pdf['data']}"
            return True, pdf_src
        elif os.path.exists(PDF_PATH):
            print(f"Loading default PDF from: {PDF_PATH}")
            pdf_base64 = encode_pdf_as_base64(PDF_PATH)
            if pdf_base64:
                pdf_src = f"data:application/pdf;base64,{pdf_base64}"
                return True, pdf_src
        else:
            print("No PDF available to load")
        return True, ""  # Open modal even if PDF fails to load

    elif trigger_id == "close-pdf-modal" and close_clicks and close_clicks > 0:
        # Closing modal
        return False, ""

    return is_open, ""

@app.callback(
    Output("images-store", "data"),
    [Input("analyze-btn", "n_clicks")],
    [State("uploaded-pdf-store", "data")]
)
def extract_pdf_images(n_clicks, uploaded_pdf):
    if n_clicks and n_clicks > 0:
        if uploaded_pdf and uploaded_pdf.get('data') and PDF_SUPPORT:
            # Extract from uploaded PDF
            try:
                pdf_bytes = base64.b64decode(uploaded_pdf['data'])
                # Save temporarily to extract images
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                    tmp_file.write(pdf_bytes)
                    tmp_path = tmp_file.name

                images = extract_images_from_pdf(tmp_path)

                # Clean up temp file
                try:
                    os.unlink(tmp_path)
                except:
                    pass

                return images
            except Exception as e:
                print(f"Error extracting images from uploaded PDF: {e}")
                return load_test_image()
        elif os.path.exists(PDF_PATH) and PDF_SUPPORT:
            images = extract_images_from_pdf(PDF_PATH)
            return images
        else:
            # Use test image if PDF not available
            return load_test_image()
    return []

@app.callback(
    Output("analysis-results", "children"),
    Output("analysis-store", "data"),
    Output("loading-output", "children"),
    [Input("images-store", "data")]
)
def analyze_images(images_data):
    if not images_data:
        return html.Div("Click 'Analyze All Images' to start analysis."), {}, ""

    analysis_results = []
    analysis_data = {}

    for i, img_data in enumerate(images_data):
        try:
            # Perform cell analysis
            cell_analysis = count_cells_in_image(img_data['data'])

            # Create annotated image
            annotated_img = create_annotated_image(img_data['data'], cell_analysis)

            # Store analysis data
            analysis_data[f"image_{i}"] = cell_analysis

            # Create display card for each image
            card = dbc.Card([
                dbc.CardHeader([
                    html.H5(f"Image {i+1} (Page {img_data['page']})")
                ]),
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.H6("Original Image"),
                            html.Img(
                                src=f"data:image/png;base64,{img_data['data']}",
                                style={"width": "100%", "maxHeight": "200px", "objectFit": "contain"}
                            )
                        ], width=6),
                        dbc.Col([
                            html.H6("Analyzed Image"),
                            html.Img(
                                src=f"data:image/png;base64,{annotated_img}",
                                style={"width": "100%", "maxHeight": "200px", "objectFit": "contain"}
                            )
                        ], width=6)
                    ]),
                    html.Hr(),
                    dbc.Row([
                        dbc.Col([
                            html.H6("Analysis Results:"),
                            html.P([
                                html.Strong("Cell Count: "), f"{cell_analysis['consensus_count']} cells", html.Br(),
                                html.Strong("Confidence: "), f"{cell_analysis['confidence']}%", html.Br(),
                                html.Strong("Image Size: "), f"{img_data['width']} x {img_data['height']}"
                            ])
                        ], width=6),
                        dbc.Col([
                            html.H6("Detection Methods:"),
                            html.Ul([
                                html.Li(f"Hough Circles: {cell_analysis['method_counts'].get('hough_circles', 0)}"),
                                html.Li(f"Blob Detection: {cell_analysis['method_counts'].get('blob_detection', 0)}"),
                                html.Li(f"Contours: {cell_analysis['method_counts'].get('contour_detection', 0)}"),
                                html.Li(f"Watershed: {cell_analysis['method_counts'].get('watershed', 0)}")
                            ])
                        ], width=6)
                    ])
                ])
            ], className="mb-3")

            analysis_results.append(card)

        except Exception as e:
            error_card = dbc.Card([
                dbc.CardHeader(html.H5(f"Image {i+1} - Error")),
                dbc.CardBody([
                    dbc.Alert(f"Error analyzing image: {str(e)}", color="danger")
                ])
            ], className="mb-3")
            analysis_results.append(error_card)

    # Summary statistics
    if analysis_data:
        total_images = len(analysis_data)
        total_cells = sum(data['consensus_count'] for data in analysis_data.values())
        avg_confidence = np.mean([data['confidence'] for data in analysis_data.values()])

        summary_card = dbc.Card([
            dbc.CardHeader(html.H4("Analysis Summary")),
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.H3(str(total_images), className="text-primary"),
                        html.P("Images Analyzed")
                    ], width=3),
                    dbc.Col([
                        html.H3(str(total_cells), className="text-success"),
                        html.P("Total Cells Detected")
                    ], width=3),
                    dbc.Col([
                        html.H3(f"{avg_confidence:.1f}%", className="text-info"),
                        html.P("Average Confidence")
                    ], width=3),
                    dbc.Col([
                        html.H3(f"{total_cells/total_images:.1f}", className="text-warning"),
                        html.P("Cells per Image")
                    ], width=3)
                ])
            ])
        ], className="mb-4")

        analysis_results.insert(0, summary_card)

    return analysis_results, analysis_data, ""

@app.callback(
    Output("approval-status", "children"),
    Output("approval-store", "data"),
    [Input("approval-checkbox", "value"), Input("save-approval", "n_clicks")],
    [State("approval-store", "data")]
)
def handle_approval(approval_value, save_clicks, stored_approval):
    ctx = dash.callback_context
    if not ctx.triggered:
        return "", stored_approval or {}

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == "approval-checkbox":
        is_approved = "approved" in (approval_value or [])
        status_text = "✅ Report Approved" if is_approved else "⏳ Approval Pending"
        status_color = "success" if is_approved else "warning"

        return dbc.Alert(status_text, color=status_color), stored_approval or {}

    elif trigger_id == "save-approval" and save_clicks:
        is_approved = "approved" in (approval_value or [])
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        approval_data = {
            "approved": is_approved,
            "timestamp": timestamp,
            "report_file": PDF_PATH
        }

        # Here you could save to database or file
        success_msg = f"✅ Approval status saved at {timestamp}"
        return dbc.Alert(success_msg, color="success"), approval_data

    return "", stored_approval or {}

# Removed duplicate callback - pdf-info is already handled by display_pdf_info above

if __name__ == "__main__":
    app.run_server(debug=True, port=8051)