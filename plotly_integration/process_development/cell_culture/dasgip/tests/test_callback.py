"""
Test just the callback registration - minimal test
"""
import dash
from dash import dcc, html, Input, Output, State, callback
import dash_bootstrap_components as dbc
from django_plotly_dash import DjangoDash

# Create minimal test app
app = DjangoDash(
    'test_callback_app', 
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)

app.layout = dbc.Container([
    html.H2("Callback Test"),
    dbc.Button("Test Button", id="test-button", color="primary"),
    html.Div(id="test-output"),
    dcc.Store(id="test-store", data="test-data")
])

@app.callback(
    Output('test-output', 'children'),
    Input('test-button', 'n_clicks'),
    State('test-store', 'data'),
    prevent_initial_call=True
)
def test_callback(n_clicks, store_data):
    print(f"CALLBACK TRIGGERED! Clicks: {n_clicks}, Store: {store_data}")
    return f"Button clicked {n_clicks} times! Store data: {store_data}"

print("Test app created successfully!")