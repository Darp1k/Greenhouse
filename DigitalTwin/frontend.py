import dash
from dash import html, dcc, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np
import json
import requests
import os
from dotenv import load_dotenv

load_dotenv()


# FastAPI Backend URL
API_BASE_URL = os.environ["API_BASE_URL"]

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

plant_buttons = [
    dbc.Button(
        f"Pea Plant {i}", 
        id={"type": "plant-selector", "index": i},
        color="success", 
        outline=True,
        className="w-100 mb-2"
    )
    for i in range(1, 41)
]

sidebar = html.Div(
    [
        html.H4("Greenhouse Digital Twin", className="display-6", style={"fontSize": "1.5rem"}),
        html.Hr(),
        html.P("Select a specimen from the tracking database.", className="text-muted"),
        html.Div(plant_buttons, style={"height": "75vh", "overflowY": "auto", "paddingRight": "10px"})
    ],
    style={"padding": "2rem", "backgroundColor": "#f8f9fa", "height": "100vh"}
)

# Hidden store to remember which plant is currently clicked
current_plant_store = dcc.Store(id="current-plant-store", data=None)

# Modal popup to show the drone images
captures_modal = dbc.Modal(
    [
        dbc.ModalHeader(dbc.ModalTitle(id="modal-title")),
        dbc.ModalBody(id="modal-body"), # Carousel goes here
        dbc.ModalFooter(dbc.Button("Close", id="close-modal-btn", className="ms-auto", n_clicks=0))
    ],
    id="modal",
    size="xl",
    is_open=False,
)

main_window = html.Div(
    [
        html.H2(id="plant-header", children="Select a plant to view its 3D model", className="mt-4 mb-4"),
        dbc.Card(
            dbc.CardBody(dcc.Graph(id="3d-model-viewer", style={"height": "65vh"}, figure=go.Figure())),
            className="shadow-sm mb-3"
        ),
        # Button to trigger the database query and open the modal (hidden by default)
        dbc.Button("View Drone Captures", id="open-modal-btn", color="primary", style={"display": "none"}),
        captures_modal,
        current_plant_store
    ],
    style={"padding": "2rem"}
)

app.layout = dbc.Container(
    [dbc.Row([dbc.Col(sidebar, width=3, className="p-0"), dbc.Col(main_window, width=9)])],
    fluid=True, className="p-0"
)

# Callbacks

@app.callback(
    [Output("plant-header", "children"),
     Output("3d-model-viewer", "figure"),
     Output({"type": "plant-selector", "index": dash.ALL}, "active"),
     Output("current-plant-store", "data"),
     Output("open-modal-btn", "style")],
    [Input({"type": "plant-selector", "index": dash.ALL}, "n_clicks")],
    prevent_initial_call=True
)
def update_3d_view(n_clicks_list):
    if not ctx.triggered:
        return dash.no_update

    button_id = json.loads(ctx.triggered[0]["prop_id"].split(".")[0])
    plant_index = button_id["index"]

    # Generate placeholder 3D geometry
    z = np.linspace(0, 15, 100)
    x = np.sin(z + plant_index) * np.exp(-0.05 * z)
    y = np.cos(z + plant_index) * np.exp(-0.05 * z)

    fig = go.Figure(data=[go.Scatter3d(
        x=x, y=y, z=z, mode='markers+lines',
        marker=dict(size=6, color=z, colorscale='Greens', opacity=0.9),
        line=dict(color='darkgreen', width=4)
    )])
    fig.update_layout(
        scene=dict(xaxis_showgrid=False, yaxis_showgrid=False, zaxis_title='Height (cm)', aspectmode='data'),
        margin=dict(l=0, r=0, b=0, t=0), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)'
    )

    active_states = [i == plant_index for i in range(1, 41)]
    header_text = f"Viewing: Pea Plant {plant_index}"
    
    # Make the "View Captures" button visible now that a plant is selected
    button_style = {"display": "block", "width": "100%"}

    return header_text, fig, active_states, plant_index, button_style

@app.callback(
    [Output("modal", "is_open"),
     Output("modal-title", "children"),
     Output("modal-body", "children")],
    [Input("open-modal-btn", "n_clicks"),
     Input("close-modal-btn", "n_clicks")],
    [State("modal", "is_open"),
     State("current-plant-store", "data")],
    prevent_initial_call=True
)
def toggle_modal_and_fetch_data(n_open, n_close, is_open, plant_index):
    # Determine if we are opening or closing the modal
    trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
    
    if trigger_id == "close-modal-btn":
        return False, dash.no_update, dash.no_update
        
    if trigger_id == "open-modal-btn" and plant_index is not None:
        # Request data from FastAPI Backend
        try:
            response = requests.get(f"{API_BASE_URL}/api/v1/captures/{plant_index}")
            data = response.json()
            captures = data.get("captures", [])
        except requests.exceptions.RequestException:
            captures = []

        if not captures:
            return True, f"Drone Captures for Plant {plant_index}", html.P("No images found for this plant yet.")

        # Format image data for the Dash Bootstrap Carousel
        carousel_items = []
        for i, cap in enumerate(captures):
            # Prepend the API Base URL so Dash can download the image from FastAPI's static mount
            image_url = f"{API_BASE_URL}{cap['file_path']}" 
            caption_text = f"Flight #{cap['flight_id']} | {cap['timestamp']}"
            
            carousel_items.append({
                "key": str(i),
                "src": image_url,
                "header": f"Capture {i+1}",
                "caption": caption_text
            })

        carousel = dbc.Carousel(items=carousel_items, controls=True, indicators=True, className="carousel-fade")
        return True, f"Drone Captures for Plant {plant_index}", carousel

    return is_open, dash.no_update, dash.no_update

if __name__ == "__main__":
    # Dash runs on port 8050 to avoid conflicting with FastAPI on port 8000
    app.run(debug=True, port=8050)
