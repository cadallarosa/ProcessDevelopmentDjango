from dash import html, dcc
from django_plotly_dash import DjangoDash

# Initialize the Dash app
app = DjangoDash(name='homepage',title="Homepage")

# Define the layout
app.layout = html.Div(
    children=[
        # Header section
        html.Div(
            children=[
                html.H1("Process Development", style={
                    'font-size': '36px',
                    'color': '#ffffff',
                    'margin-bottom': '20px',
                }),
                html.P("Select an option below to proceed.", style={
                    'font-size': '18px',
                    'color': '#eaeaea'
                }),
            ],
            style={
                'text-align': 'center',
                'padding': '30px 20px',
                'background-color': '#0056b3',
                'border-radius': '8px',
                'margin-bottom': '10px',
            }
        ),
#LIMS Management
        html.Div(
            children=[
                html.H2("LIMS", style={
                    'font-size': '28px',
                    'color': '#ffffff',
                    'text-align': 'center',
                    'margin-bottom': '20px'
                }),
                html.Div(
                    children=[
                        dcc.Link(
                            html.Button("Upstream Sample Management", style={
                                'width': '250px',
                                'height': '60px',
                                'font-size': '18px',
                                'color': '#ffffff',
                                'background-color': '#007bff',
                                'border': 'none',
                                'border-radius': '8px',
                                'cursor': 'pointer',
                                'box-shadow': '2px 2px 5px rgba(0, 0, 0, 0.2)'
                            }),
                            href="http://localhost:8000/plotly_integration/dash-app/app/UPSampleManagementApp/",
                            target="_blank"
                        ),
                        dcc.Link(
                            html.Button("CLD Sample Management", style={
                                'width': '250px',
                                'height': '60px',
                                'font-size': '18px',
                                'color': '#ffffff',
                                'background-color': '#28a745',
                                'border': 'none',
                                'border-radius': '8px',
                                'cursor': 'pointer',
                                'box-shadow': '2px 2px 5px rgba(0, 0, 0, 0.2)'
                            }),
                            href="http://localhost:8000/plotly_integration/dash-app/app/CLDDashboardApp3/",
                            target="_blank"
                        ),
                        dcc.Link(
                            html.Button("Downstream Experiment Management", style={
                                'width': '250px',
                                'height': '60px',
                                'font-size': '18px',
                                'color': '#ffffff',
                                'background-color': '#ffc107',
                                'border': 'none',
                                'border-radius': '8px',
                                'cursor': 'pointer',
                                'box-shadow': '2px 2px 5px rgba(0, 0, 0, 0.2)'
                            }),
                            href="http://localhost:8000/plotly_integration/dash-app/app/DnAssignmentApp/",
                            target="_blank"
                        ),
                        # dcc.Link(
                        #     html.Button("Titer Analysis", style={
                        #         'width': '250px',
                        #         'height': '60px',
                        #         'font-size': '18px',
                        #         'color': '#ffffff',
                        #         'background-color': '#008080',
                        #         'border': 'none',
                        #         'border-radius': '8px',
                        #         'cursor': 'pointer',
                        #         'box-shadow': '2px 2px 5px rgba(0, 0, 0, 0.2)'
                        #     }),
                        #     href="http://localhost:8000/plotly_integration/dash-app/app/TiterReportApp/",
                        #     target="_blank"
                        # ),
                        # dcc.Link(
                        #     html.Button("Column Analysis", style={
                        #         'width': '250px',
                        #         'height': '60px',
                        #         'font-size': '18px',
                        #         'color': '#ffffff',
                        #         'background-color': '#ff7f00',
                        #         'border': 'none',
                        #         'border-radius': '8px',
                        #         'cursor': 'pointer',
                        #         'box-shadow': '2px 2px 5px rgba(0, 0, 0, 0.2)'
                        #     }),
                        #     href="http://localhost:8000/plotly_integration/dash-app/app/ColumnUsageApp/",
                        #     target="_blank"
                        # ),
                    ],
                    style={
                        'display': 'flex',
                        'justify-content': 'center',
                        'gap': '20px',
                        'flex-wrap': 'wrap'
                    }
                )
            ],
            style={
                'text-align': 'center',
                'padding': '30px 20px',
                'background-color': '#343a40',
                'border-radius': '8px',
                'margin-top': '30px',
                'width': '100%'
            }
        ),

        # Empower Section
        html.Div(
            children=[
                html.H2("Empower", style={
                    'font-size': '28px',
                    'color': '#ffffff',
                    'text-align': 'center',
                    'margin-bottom': '20px'
                }),
                html.Div(
                    children=[
                        dcc.Link(
                            html.Button("Database Management", style={
                                'width': '250px',
                                'height': '60px',
                                'font-size': '18px',
                                'color': '#ffffff',
                                'background-color': '#007bff',
                                'border': 'none',
                                'border-radius': '8px',
                                'cursor': 'pointer',
                                'box-shadow': '2px 2px 5px rgba(0, 0, 0, 0.2)'
                            }),
                            href="http://localhost:8000/plotly_integration/dash-app/app/DatabaseManagerApp/",
                            target="_blank"
                        ),
                        dcc.Link(
                            html.Button("Create Report", style={
                                'width': '250px',
                                'height': '60px',
                                'font-size': '18px',
                                'color': '#ffffff',
                                'background-color': '#28a745',
                                'border': 'none',
                                'border-radius': '8px',
                                'cursor': 'pointer',
                                'box-shadow': '2px 2px 5px rgba(0, 0, 0, 0.2)'
                            }),
                            href="http://localhost:8000/plotly_integration/dash-app/app/ReportApp/",
                            target="_blank"
                        ),
                        dcc.Link(
                            html.Button("Sec Analysis", style={
                                'width': '250px',
                                'height': '60px',
                                'font-size': '18px',
                                'color': '#ffffff',
                                'background-color': '#ffc107',
                                'border': 'none',
                                'border-radius': '8px',
                                'cursor': 'pointer',
                                'box-shadow': '2px 2px 5px rgba(0, 0, 0, 0.2)'
                            }),
                            href="http://localhost:8000/plotly_integration/dash-app/app/SecReportApp/",
                            target="_blank"
                        ),
                        dcc.Link(
                            html.Button("Titer Analysis", style={
                                'width': '250px',
                                'height': '60px',
                                'font-size': '18px',
                                'color': '#ffffff',
                                'background-color': '#008080',
                                'border': 'none',
                                'border-radius': '8px',
                                'cursor': 'pointer',
                                'box-shadow': '2px 2px 5px rgba(0, 0, 0, 0.2)'
                            }),
                            href="http://localhost:8000/plotly_integration/dash-app/app/TiterReportApp/",
                            target="_blank"
                        ),
                        dcc.Link(
                            html.Button("Column Analysis", style={
                                'width': '250px',
                                'height': '60px',
                                'font-size': '18px',
                                'color': '#ffffff',
                                'background-color': '#ff7f00',
                                'border': 'none',
                                'border-radius': '8px',
                                'cursor': 'pointer',
                                'box-shadow': '2px 2px 5px rgba(0, 0, 0, 0.2)'
                            }),
                            href="http://localhost:8000/plotly_integration/dash-app/app/ColumnUsageApp/",
                            target="_blank"
                        ),
                    ],
                    style={
                        'display': 'flex',
                        'justify-content': 'center',
                        'gap': '20px',
                        'flex-wrap': 'wrap'
                    }
                )
            ],
            style={
                'text-align': 'center',
                'padding': '30px 20px',
                'background-color': '#343a40',
                'border-radius': '8px',
                'margin-top': '30px',
                'width': '100%'
            }
        ),
        # CE SDS Section
        html.Div(
            children=[
                html.H2("CE SDS", style={
                    'font-size': '28px',
                    'color': '#ffffff',
                    'text-align': 'center',
                    'margin-bottom': '20px'
                }),
                html.Div(
                    children=[
                        dcc.Link(
                            html.Button("CE SDS Data Import", style={
                                'width': '250px',
                                'height': '60px',
                                'font-size': '18px',
                                'color': '#ffffff',
                                'background-color': '#9966CC',
                                'border': 'none',
                                'border-radius': '8px',
                                'cursor': 'pointer',
                                'box-shadow': '2px 2px 5px rgba(0, 0, 0, 0.2)'
                            }),
                            href="http://localhost:8000/plotly_integration/dash-app/app/CeSdsImportManagerApp/",
                            target="_blank"
                        ),
                        dcc.Link(
                            html.Button("Create Report", style={
                                'width': '250px',
                                'height': '60px',
                                'font-size': '18px',
                                'color': '#ffffff',
                                'background-color': '#FFB6C1',
                                'border': 'none',
                                'border-radius': '8px',
                                'cursor': 'pointer',
                                'box-shadow': '2px 2px 5px rgba(0, 0, 0, 0.2)'
                            }),
                            href="http://localhost:8000/plotly_integration/dash-app/app/CreateCESDSReportApp/",
                            target="_blank"
                        ),
                        dcc.Link(
                            html.Button("CE SDS Analysis", style={
                                'width': '250px',
                                'height': '60px',
                                'font-size': '18px',
                                'color': '#ffffff',
                                'background-color': '#FFB6C1',
                                'border': 'none',
                                'border-radius': '8px',
                                'cursor': 'pointer',
                                'box-shadow': '2px 2px 5px rgba(0, 0, 0, 0.2)'
                            }),
                            href="http://localhost:8000/plotly_integration/dash-app/app/CESDSReportViewerApp/",
                            target="_blank"
                        ),
                    ],
                    style={
                        'display': 'flex',
                        'justify-content': 'center',
                        'gap': '20px',
                        'flex-wrap': 'wrap'
                    }
                )
            ],
            style={
                'text-align': 'center',
                'padding': '30px 20px',
                'background-color': '#3a3f44',
                'border-radius': '8px',
                'margin-top': '30px',
                'width': '100%'
            }
        ),
        # Nova Flex Section
        html.Div(
            children=[
                html.H2("cIEF", style={
                    'font-size': '28px',
                    'color': '#ffffff',
                    'text-align': 'center',
                    'margin-bottom': '20px'
                }),
                html.Div(
                    children=[
                        dcc.Link(
                            html.Button("cIEF Data Import", style={
                                'width': '250px',
                                'height': '60px',
                                'font-size': '18px',
                                'color': '#ffffff',
                                'background-color': '#007bff',
                                'border': 'none',
                                'border-radius': '8px',
                                'cursor': 'pointer',
                                'box-shadow': '2px 2px 5px rgba(0, 0, 0, 0.2)'
                            }),
                            href="http://localhost:8000/plotly_integration/dash-app/app/cIEFImportManagerApp/",
                            target="_blank"
                        ),
                        dcc.Link(
                            html.Button("Create cIEF Report", style={
                                'width': '250px',
                                'height': '60px',
                                'font-size': '18px',
                                'color': '#ffffff',
                                'background-color': '#28a745',
                                'border': 'none',
                                'border-radius': '8px',
                                'cursor': 'pointer',
                                'box-shadow': '2px 2px 5px rgba(0, 0, 0, 0.2)'
                            }),
                            href="http://localhost:8000/plotly_integration/dash-app/app/cIEFReportApp/",
                            target="_blank"
                        ),
                        dcc.Link(
                            html.Button("Analyze cIEF Report", style={
                                'width': '250px',
                                'height': '60px',
                                'font-size': '18px',
                                'color': '#ffffff',
                                'background-color': '#ffc107',
                                'border': 'none',
                                'border-radius': '8px',
                                'cursor': 'pointer',
                                'box-shadow': '2px 2px 5px rgba(0, 0, 0, 0.2)'
                            }),
                            href="http://localhost:8000/plotly_integration/dash-app/app/cIEFReportViewerApp/",
                            target="_blank"
                        ),

                    ],
                    style={
                        'display': 'flex',
                        'justify-content': 'center',
                        'gap': '20px',
                        'flex-wrap': 'wrap'
                    }
                )
            ],
            style={
                'text-align': 'center',
                'padding': '30px 20px',
                'background-color': '#343a40',
                'border-radius': '8px',
                'margin-top': '30px',
                'width': '100%'
            }
        ),
        # AKTA Section
        html.Div(
            children=[
                html.H2("AKTA", style={
                    'font-size': '28px',
                    'color': '#ffffff',
                    'text-align': 'center',
                    'margin-bottom': '20px'
                }),
                html.Div(
                    children=[
                        dcc.Link(
                            html.Button("Akta App", style={
                                'width': '250px',
                                'height': '60px',
                                'font-size': '18px',
                                'color': '#ffffff',
                                'background-color': '#9966CC',
                                'border': 'none',
                                'border-radius': '8px',
                                'cursor': 'pointer',
                                'box-shadow': '2px 2px 5px rgba(0, 0, 0, 0.2)'
                            }),
                            href="http://localhost:8000/plotly_integration/dash-app/app/AktaChromatogramApp/",
                            target="_blank"
                        ),
                        # dcc.Link(
                        #     html.Button("Akta Data Import", style={
                        #         'width': '250px',
                        #         'height': '60px',
                        #         'font-size': '18px',
                        #         'color': '#ffffff',
                        #         'background-color': '#FFB6C1',
                        #         'border': 'none',
                        #         'border-radius': '8px',
                        #         'cursor': 'pointer',
                        #         'box-shadow': '2px 2px 5px rgba(0, 0, 0, 0.2)'
                        #     }),
                        #     href="http://localhost:8000/plotly_integration/dash-app/app/ServerControlApp/",
                        #     target="_blank"
                        # ),
                        # dcc.Link(
                        #     html.Button("OPCUA Server Client", style={
                        #         'width': '250px',
                        #         'height': '60px',
                        #         'font-size': '18px',
                        #         'color': '#ffffff',
                        #         'background-color': '#FFB6C1',
                        #         'border': 'none',
                        #         'border-radius': '8px',
                        #         'cursor': 'pointer',
                        #         'box-shadow': '2px 2px 5px rgba(0, 0, 0, 0.2)'
                        #     }),
                        #     href="http://localhost:8000/plotly_integration/dash-app/app/OPCBrowserApp/",
                        #     target="_blank"
                        # ),
                    ],
                    style={
                        'display': 'flex',
                        'justify-content': 'center',
                        'gap': '20px',
                        'flex-wrap': 'wrap'
                    }
                )
            ],
            style={
                'text-align': 'center',
                'padding': '30px 20px',
                'background-color': '#3a3f44',
                'border-radius': '8px',
                'margin-top': '30px',
                'width': '100%'
            }
        ),

        # SartoFlow Smart Section
        html.Div(
            children=[
                html.H2("Ultrafiltration/Diafiltration", style={
                    'font-size': '28px',
                    'color': '#ffffff',
                    'text-align': 'center',
                    'margin-bottom': '20px'
                }),
                html.Div(
                    children=[
                        dcc.Link(
                            html.Button("Import UFDF Experiment", style={
                                'width': '250px',
                                'height': '60px',
                                'font-size': '18px',
                                'color': '#ffffff',
                                'background-color': '#008080',  # Teal
                                'border': 'none',
                                'border-radius': '8px',
                                'cursor': 'pointer',
                                'box-shadow': '2px 2px 5px rgba(0, 0, 0, 0.2)'
                            }),
                            href="http://localhost:8000/plotly_integration/dash-app/app/UFDFAnalysis/",
                            target="_blank"
                        ),

                        dcc.Link(
                            html.Button("Analyze Experiment", style={
                                'width': '250px',
                                'height': '60px',
                                'font-size': '18px',
                                'color': '#ffffff',
                                'background-color': '#800080',  # Purple
                                'border': 'none',
                                'border-radius': '8px',
                                'cursor': 'pointer',
                                'box-shadow': '2px 2px 5px rgba(0, 0, 0, 0.2)'
                            }),
                            href="http://localhost:8000/plotly_integration/dash-app/app/UFDFApp/",
                            target="_blank"
                        ),

                    ],
                    style={
                        'display': 'flex',
                        'justify-content': 'center',
                        'gap': '20px',
                        'flex-wrap': 'wrap'
                    }
                )
            ],
            style={
                'text-align': 'center',
                'padding': '30px 20px',
                'background-color': '#343a40',
                'border-radius': '8px',
                'margin-top': '30px',
                'width': '100%'
            }
        ),
        # Viral Filtration Section (NEW DIV)
        html.Div(
            children=[
                html.H2("Viral Filtration", style={
                    'font-size': '28px',
                    'color': '#ffffff',
                    'text-align': 'center',
                    'margin-bottom': '20px'
                }),
                html.Div(
                    children=[
                        dcc.Link(
                            html.Button("Import Experiment", style={
                                'width': '250px',
                                'height': '60px',
                                'font-size': '18px',
                                'color': '#ffffff',
                                'background-color': '#008080',  # Teal
                                'border': 'none',
                                'border-radius': '8px',
                                'cursor': 'pointer',
                                'box-shadow': '2px 2px 5px rgba(0, 0, 0, 0.2)'
                            }),
                            href="http://localhost:8000/plotly_integration/dash-app/app/ViralFiltrationExperimentImport/",
                            target="_blank"
                        ),
                        dcc.Link(
                            html.Button("Analyze Experiment", style={
                                'width': '250px',
                                'height': '60px',
                                'font-size': '18px',
                                'color': '#ffffff',
                                'background-color': '#B22222',  # Firebrick Red
                                'border': 'none',
                                'border-radius': '8px',
                                'cursor': 'pointer',
                                'box-shadow': '2px 2px 5px rgba(0, 0, 0, 0.2)'
                            }),
                            href="http://localhost:8000/plotly_integration/dash-app/app/ViralFiltrationApp/",
                            target="_blank"
                        ),
                    ],
                    style={
                        'display': 'flex',
                        'justify-content': 'center',
                        'gap': '20px',
                        'flex-wrap': 'wrap'
                    }
                )
            ],
            style={
                'text-align': 'center',
                'padding': '30px 20px',
                'background-color': '#343a40',  # 2c3e50
                'border-radius': '8px',
                'margin-top': '30px',
                'width': '100%'
            }
        ),
        # Nova Flex Section
        html.Div(
            children=[
                html.H2("Nova Flex", style={
                    'font-size': '28px',
                    'color': '#ffffff',
                    'text-align': 'center',
                    'margin-bottom': '20px'
                }),
                html.Div(
                    children=[
                        dcc.Link(
                            html.Button("Nova Flex 2 Data Import", style={
                                'width': '250px',
                                'height': '60px',
                                'font-size': '18px',
                                'color': '#ffffff',
                                'background-color': '#007bff',
                                'border': 'none',
                                'border-radius': '8px',
                                'cursor': 'pointer',
                                'box-shadow': '2px 2px 5px rgba(0, 0, 0, 0.2)'
                            }),
                            href="http://localhost:8000/plotly_integration/dash-app/app/NovaFlex2DataUploadApp/",
                            target="_blank"
                        ),
                        dcc.Link(
                            html.Button("Create Nova Flex 2 Report", style={
                                'width': '250px',
                                'height': '60px',
                                'font-size': '18px',
                                'color': '#ffffff',
                                'background-color': '#28a745',
                                'border': 'none',
                                'border-radius': '8px',
                                'cursor': 'pointer',
                                'box-shadow': '2px 2px 5px rgba(0, 0, 0, 0.2)'
                            }),
                            href="http://localhost:8000/plotly_integration/dash-app/app/NovaFlex2ReportApp/",
                            target="_blank"
                        ),
                        dcc.Link(
                            html.Button("Analyze Nova Report", style={
                                'width': '250px',
                                'height': '60px',
                                'font-size': '18px',
                                'color': '#ffffff',
                                'background-color': '#ffc107',
                                'border': 'none',
                                'border-radius': '8px',
                                'cursor': 'pointer',
                                'box-shadow': '2px 2px 5px rgba(0, 0, 0, 0.2)'
                            }),
                            href="http://localhost:8000/plotly_integration/dash-app/app/NovaDataReportApp/",
                            target="_blank"
                        ),

                    ],
                    style={
                        'display': 'flex',
                        'justify-content': 'center',
                        'gap': '20px',
                        'flex-wrap': 'wrap'
                    }
                )
            ],
            style={
                'text-align': 'center',
                'padding': '30px 20px',
                'background-color': '#343a40',
                'border-radius': '8px',
                'margin-top': '30px',
                'width': '100%'
            }
        ),
        # Nova Vi Cell Section
        html.Div(
            children=[
                html.H2("Vi Cell", style={
                    'font-size': '28px',
                    'color': '#ffffff',
                    'text-align': 'center',
                    'margin-bottom': '20px'
                }),
                html.Div(
                    children=[

                        dcc.Link(
                            html.Button("ViCell Data Import", style={
                                'width': '250px',
                                'height': '60px',
                                'font-size': '18px',
                                'color': '#ffffff',
                                'background-color': '#007bff',
                                'border': 'none',
                                'border-radius': '8px',
                                'cursor': 'pointer',
                                'box-shadow': '2px 2px 5px rgba(0, 0, 0, 0.2)'
                            }),
                            href="http://localhost:8000/plotly_integration/dash-app/app/ViCellDataUploadApp/",
                            target="_blank"
                        ),
                        dcc.Link(
                            html.Button("Create ViCell Report", style={
                                'width': '250px',
                                'height': '60px',
                                'font-size': '18px',
                                'color': '#ffffff',
                                'background-color': '#28a745',
                                'border': 'none',
                                'border-radius': '8px',
                                'cursor': 'pointer',
                                'box-shadow': '2px 2px 5px rgba(0, 0, 0, 0.2)'
                            }),
                            href="http://localhost:8000/plotly_integration/dash-app/app/CreateViCellReportApp/",
                            target="_blank"
                        ),
                        dcc.Link(
                            html.Button("Analyze ViCell Report", style={
                                'width': '250px',
                                'height': '60px',
                                'font-size': '18px',
                                'color': '#ffffff',
                                'background-color': '#ffc107',
                                'border': 'none',
                                'border-radius': '8px',
                                'cursor': 'pointer',
                                'box-shadow': '2px 2px 5px rgba(0, 0, 0, 0.2)'
                            }),
                            href="http://localhost:8000/plotly_integration/dash-app/app/ViCellReportApp/",
                            target="_blank"
                        ),

                    ],
                    style={
                        'display': 'flex',
                        'justify-content': 'center',
                        'gap': '20px',
                        'flex-wrap': 'wrap'
                    }
                )
            ],
            style={
                'text-align': 'center',
                'padding': '30px 20px',
                'background-color': '#343a40',
                'border-radius': '8px',
                'margin-top': '30px',
                'width': '100%'
            }
        ),
    ],
    style={
        'display': 'flex',
        'flex-direction': 'column',
        'align-items': 'center',
        'padding': '40px',
        'font-family': 'Arial, sans-serif',
        'background-color': '#f4f6f9',
        'min-height': '100vh'
    }
)
