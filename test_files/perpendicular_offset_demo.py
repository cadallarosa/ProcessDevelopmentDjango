"""
Perpendicular Offset Curve Demonstration
Creates an interactive plot showing a signal with a perpendicular offset line
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

def generate_sample_data():
    """Generate sample data with two Gaussian peaks"""
    x = np.linspace(0, 10, 200)
    
    # Create two Gaussian peaks
    peak1 = 5 * np.exp(-((x - 3) / 0.8) ** 2)  # Larger peak at x=3
    peak2 = 3 * np.exp(-((x - 7) / 0.6) ** 2)  # Smaller peak at x=7
    
    # Add baseline offset and small noise
    baseline = 0.2
    noise = 0.05 * np.random.normal(0, 1, len(x))
    y = peak1 + peak2 + baseline + noise
    
    return x, y

def calculate_derivatives(x, y):
    """Calculate numerical derivatives using finite differences"""
    dx = x[1] - x[0]  # Assuming uniform spacing
    dy_dx = np.zeros_like(y)
    
    # Forward difference for first point
    dy_dx[0] = (y[1] - y[0]) / dx
    
    # Central difference for middle points
    for i in range(1, len(y) - 1):
        dy_dx[i] = (y[i + 1] - y[i - 1]) / (2 * dx)
    
    # Backward difference for last point
    dy_dx[-1] = (y[-1] - y[-2]) / dx
    
    return dy_dx

def create_perpendicular_offset(x, y, offset_distance):
    """Create perpendicular offset curve maintaining constant perpendicular distance"""
    # Calculate derivatives (tangent slopes)
    dy_dx = calculate_derivatives(x, y)
    
    # Calculate normal vectors (perpendicular to tangent)
    # If tangent vector is (1, dy/dx), then normal vector is (-dy/dx, 1)
    # Normalize the normal vector
    normal_magnitude = np.sqrt(dy_dx**2 + 1)
    normal_x = -dy_dx / normal_magnitude
    normal_y = 1 / normal_magnitude
    
    # Create offset points by moving along normal vector
    offset_x = x + offset_distance * normal_x
    offset_y = y + offset_distance * normal_y
    
    return offset_x, offset_y, normal_x, normal_y

def create_perpendicular_indicators(x, y, offset_x, offset_y, num_indicators=8):
    """Create lines showing perpendicular distance at sample points"""
    # Select evenly spaced points for indicators
    indices = np.linspace(0, len(x) - 1, num_indicators, dtype=int)
    
    indicator_lines = []
    for i in indices:
        indicator_lines.append({
            'x': [x[i], offset_x[i]],
            'y': [y[i], offset_y[i]]
        })
    
    return indicator_lines

def create_interactive_plot():
    """Create interactive plot with slider for offset distance"""
    # Generate sample data
    x, y = generate_sample_data()
    
    # Create figure
    fig = go.Figure()
    
    # Add original signal
    fig.add_trace(go.Scatter(
        x=x, y=y,
        mode='lines',
        name='Original Signal',
        line=dict(color='blue', width=2),
        fill='tozeroy',
        fillcolor='rgba(173, 216, 230, 0.3)'  # Light blue fill
    ))
    
    # Initial offset distance
    initial_offset = 0.5
    offset_x, offset_y, normal_x, normal_y = create_perpendicular_offset(x, y, initial_offset)
    
    # Add offset line
    fig.add_trace(go.Scatter(
        x=offset_x, y=offset_y,
        mode='lines',
        name='Perpendicular Offset',
        line=dict(color='red', width=2, dash='dash')
    ))
    
    # Add perpendicular indicators
    indicators = create_perpendicular_indicators(x, y, offset_x, offset_y)
    for i, indicator in enumerate(indicators):
        fig.add_trace(go.Scatter(
            x=indicator['x'], y=indicator['y'],
            mode='lines',
            name='Perpendicular Distance' if i == 0 else '',
            line=dict(color='orange', width=1),
            showlegend=(i == 0)  # Only show in legend once
        ))
    
    # Create slider
    steps = []
    for offset_dist in np.arange(0, 1.6, 0.1):
        offset_x_step, offset_y_step, _, _ = create_perpendicular_offset(x, y, offset_dist)
        indicators_step = create_perpendicular_indicators(x, y, offset_x_step, offset_y_step)
        
        # Create step data
        step_data = []
        
        # Original signal (unchanged)
        step_data.append(go.Scatter(
            x=x, y=y,
            mode='lines',
            name='Original Signal',
            line=dict(color='blue', width=2),
            fill='tozeroy',
            fillcolor='rgba(173, 216, 230, 0.3)'
        ))
        
        # Updated offset line
        step_data.append(go.Scatter(
            x=offset_x_step, y=offset_y_step,
            mode='lines',
            name='Perpendicular Offset',
            line=dict(color='red', width=2, dash='dash')
        ))
        
        # Updated indicators
        for i, indicator in enumerate(indicators_step):
            step_data.append(go.Scatter(
                x=indicator['x'], y=indicator['y'],
                mode='lines',
                name='Perpendicular Distance' if i == 0 else '',
                line=dict(color='orange', width=1),
                showlegend=(i == 0)
            ))
        
        step = dict(
            method="restyle",
            args=[{"x": [trace.x for trace in step_data],
                   "y": [trace.y for trace in step_data]}],
            label=f"{offset_dist:.1f}"
        )
        steps.append(step)
    
    # Add slider
    sliders = [dict(
        active=5,  # Start at 0.5
        currentvalue={"prefix": "Perpendicular Distance: "},
        pad={"t": 50},
        steps=steps
    )]
    
    fig.update_layout(
        title="Signal with Perpendicular Offset Line",
        xaxis_title="Time / Position",
        yaxis_title="Signal Intensity",
        template="plotly_white",
        sliders=sliders,
        showlegend=True,
        width=800,
        height=600
    )
    
    return fig

def main():
    """Main function to create and display the plot"""
    print("Creating perpendicular offset demonstration...")
    
    # Create the interactive plot
    fig = create_interactive_plot()
    
    # Show the plot
    fig.show()
    
    # Save as HTML
    fig.write_html("perpendicular_offset_demo.html")
    print("Plot saved as 'perpendicular_offset_demo.html'")
    
    # Demonstrate the calculation
    print("\nDemonstrating perpendicular offset calculation:")
    x, y = generate_sample_data()
    offset_x, offset_y, normal_x, normal_y = create_perpendicular_offset(x, y, 0.5)
    
    print(f"Original signal has {len(x)} points")
    print(f"Offset curve has {len(offset_x)} points")
    print(f"Example: Point at x={x[50]:.2f}, y={y[50]:.2f}")
    print(f"         Offset to x={offset_x[50]:.2f}, y={offset_y[50]:.2f}")
    print(f"         Normal vector: ({normal_x[50]:.3f}, {normal_y[50]:.3f})")

if __name__ == "__main__":
    main()