"""Genealogy flowchart component for PD Samples."""
import plotly.graph_objects as go
from dash import dcc, html
import dash_bootstrap_components as dbc


# Color scheme for different node types
NODE_COLORS = {
    "PD": "#9b59b6",  # Purple
    "DN": "#3498db",  # Blue
    "SM": "#e67e22",  # Orange
    "UP": "#2ecc71",  # Green
    "FB": "#16a085",  # Teal
    "USP": "#27ae60",  # Dark green
    "Analytical": "#f39c12",  # Yellow/Gold
    "Other": "#95a5a6"  # Gray
}


def create_genealogy_flowchart(genealogy_data: dict):
    """
    Create an interactive flowchart from genealogy data.

    Args:
        genealogy_data: Dictionary with 'nodes' and 'edges' lists

    Returns:
        Dash component containing the flowchart
    """
    nodes = genealogy_data.get("nodes", [])
    edges = genealogy_data.get("edges", [])

    if not nodes:
        return dbc.Alert(
            "No genealogy data available for this sample.",
            color="info",
            className="mt-3"
        )

    # Create node position layout using a hierarchical approach
    node_positions = _calculate_hierarchical_layout(nodes, edges)

    # Prepare edge traces
    edge_traces = []
    for edge in edges:
        source_pos = node_positions.get(edge["source"])
        target_pos = node_positions.get(edge["target"])

        if source_pos and target_pos:
            # Draw edge line
            edge_trace = go.Scatter(
                x=[source_pos[0], target_pos[0], None],
                y=[source_pos[1], target_pos[1], None],
                mode="lines",
                line=dict(width=2, color="#7f8c8d"),
                hoverinfo="none",
                showlegend=False
            )
            edge_traces.append(edge_trace)

            # Add edge label
            mid_x = (source_pos[0] + target_pos[0]) / 2
            mid_y = (source_pos[1] + target_pos[1]) / 2
            edge_label_trace = go.Scatter(
                x=[mid_x],
                y=[mid_y],
                mode="text",
                text=[edge["label"]],
                textposition="middle center",
                textfont=dict(size=9, color="#7f8c8d"),
                hoverinfo="none",
                showlegend=False
            )
            edge_traces.append(edge_label_trace)

    # Prepare node trace
    node_x = []
    node_y = []
    node_colors = []
    node_text = []
    node_hover = []

    for node in nodes:
        pos = node_positions.get(node["id"])
        if pos:
            node_x.append(pos[0])
            node_y.append(pos[1])
            node_colors.append(NODE_COLORS.get(node["type"], NODE_COLORS["Other"]))
            node_text.append(node["label"])

            # Build hover text
            hover_lines = [f"<b>{node['label']}</b>", f"Type: {node['type']}", ""]
            for key, value in node.get("data", {}).items():
                if value and value != "N/A":
                    hover_lines.append(f"{key}: {value}")
            node_hover.append("<br>".join(hover_lines))

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        marker=dict(
            size=25,
            color=node_colors,
            line=dict(width=2, color="white"),
            opacity=0.9
        ),
        text=node_text,
        textposition="middle center",
        textfont=dict(size=9, color="white", family="Arial Black"),
        hovertext=node_hover,
        hoverinfo="text",
        hoverlabel=dict(bgcolor="white", font_size=12),
        showlegend=False
    )

    # Create figure
    fig = go.Figure(data=edge_traces + [node_trace])

    fig.update_layout(
        title=dict(
            text="Sample Genealogy (Left to Right)",
            x=0.5,
            xanchor="center",
            font=dict(size=14, color="#2c3e50")
        ),
        showlegend=False,
        hovermode="closest",
        margin=dict(b=20, l=20, r=20, t=50),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor="rgba(248, 249, 250, 1)",
        paper_bgcolor="white",
        height=400
    )

    # Create legend manually
    legend_items = []
    for node_type, color in NODE_COLORS.items():
        # Check if this type exists in the current data
        if any(n["type"] == node_type for n in nodes):
            legend_items.append(
                html.Span([
                    html.Span(
                        style={
                            "display": "inline-block",
                            "width": "15px",
                            "height": "15px",
                            "backgroundColor": color,
                            "borderRadius": "50%",
                            "marginRight": "8px",
                            "border": "2px solid white"
                        }
                    ),
                    html.Span(node_type, style={"fontSize": "12px", "marginRight": "20px"})
                ], style={"marginRight": "15px", "display": "inline-block"})
            )

    return html.Div([
        html.Div(
            legend_items,
            style={
                "textAlign": "center",
                "marginBottom": "10px",
                "padding": "10px",
                "backgroundColor": "#ecf0f1",
                "borderRadius": "5px"
            }
        ),
        dcc.Graph(
            figure=fig,
            config={"displayModeBar": False}
        )
    ])


def _calculate_hierarchical_layout(nodes: list, edges: dict) -> dict:
    """
    Calculate hierarchical layout positions for nodes (LEFT TO RIGHT).

    Args:
        nodes: List of node dictionaries
        edges: List of edge dictionaries

    Returns:
        Dictionary mapping node IDs to (x, y) positions
    """
    # Build adjacency for finding levels
    children_map = {}
    parents_map = {}

    for edge in edges:
        source = edge["source"]
        target = edge["target"]
        if source not in children_map:
            children_map[source] = []
        children_map[source].append(target)

        if target not in parents_map:
            parents_map[target] = []
        parents_map[target].append(source)

    # Find root nodes (nodes with no parents)
    node_ids = [n["id"] for n in nodes]
    roots = [nid for nid in node_ids if nid not in parents_map]

    if not roots:
        # If there are no clear roots (circular?), just pick the first node
        roots = [node_ids[0]] if node_ids else []

    # Assign levels using BFS
    levels = {}
    queue = [(root, 0) for root in roots]
    visited = set()

    while queue:
        node_id, level = queue.pop(0)
        if node_id in visited:
            continue
        visited.add(node_id)
        levels[node_id] = level

        for child in children_map.get(node_id, []):
            if child not in visited:
                queue.append((child, level + 1))

    # Add any unvisited nodes (shouldn't happen but just in case)
    for nid in node_ids:
        if nid not in levels:
            levels[nid] = 0

    # Group nodes by level
    level_groups = {}
    for node_id, level in levels.items():
        if level not in level_groups:
            level_groups[level] = []
        level_groups[level].append(node_id)

    # Calculate positions (LEFT TO RIGHT orientation with compact spacing)
    positions = {}
    x_spacing = 120  # Horizontal spacing between levels (left to right)
    y_spacing = 60   # Vertical spacing between nodes in same level (compact)

    for level, node_ids_at_level in level_groups.items():
        num_nodes = len(node_ids_at_level)

        # X position increases with level (left to right)
        x = level * x_spacing

        for idx, node_id in enumerate(node_ids_at_level):
            # Center nodes vertically
            y = (idx - (num_nodes - 1) / 2) * y_spacing
            positions[node_id] = (x, y)

    return positions
