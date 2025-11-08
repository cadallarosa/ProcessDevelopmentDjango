"""
Chart components for Project Management Dashboard
"""
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime, timedelta
from ..config import (
    PHASE_COLORS, PRIORITY_COLORS, STATUS_COLORS,
    RECOMMENDATION_COLORS, GANTT_CHART_HEIGHT
)


def create_gantt_chart(projects_data: List[Dict[str, Any]]) -> go.Figure:
    """
    Create an interactive Gantt chart showing project timelines.
    Uses px.timeline for better date handling (same approach as molecule_dashboard).

    Args:
        projects_data: List of project dictionaries

    Returns:
        Plotly Figure with Gantt chart
    """
    if not projects_data:
        # Return empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="No project data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="gray")
        )
        fig.update_layout(height=GANTT_CHART_HEIGHT)
        return fig

    # Prepare data for Gantt chart
    gantt_data = []

    for project in projects_data:
        molecule_id = project['molecule_id']
        priority = project['priority_set']
        status = project['status']

        # Parse dates - handle None/null values
        creation_date = pd.to_datetime(project.get('creation_date'), errors='coerce')
        cloning_date = pd.to_datetime(project.get('cloning_finish_date'), errors='coerce')
        purification_date = pd.to_datetime(project.get('purification_finish_date'), errors='coerce')

        # Skip if no creation date
        if pd.isna(creation_date):
            continue

        # Phase 1: Creation to Cloning (or estimated)
        if not pd.isna(cloning_date):
            gantt_data.append({
                'Task': molecule_id,
                'Start': creation_date,
                'Finish': cloning_date,
                'Phase': 'Cloning',
                'Priority': priority,
                'Status': status,
            })
        else:
            # Estimate cloning (30 days from creation)
            estimated_cloning = creation_date + pd.Timedelta(days=30)
            gantt_data.append({
                'Task': molecule_id,
                'Start': creation_date,
                'Finish': estimated_cloning,
                'Phase': 'Cloning (Est.)',
                'Priority': priority,
                'Status': status,
            })
            cloning_date = estimated_cloning

        # Phase 2: Cloning to Purification (or estimated)
        if not pd.isna(purification_date):
            gantt_data.append({
                'Task': molecule_id,
                'Start': cloning_date,
                'Finish': purification_date,
                'Phase': 'Purification',
                'Priority': priority,
                'Status': status,
            })
        else:
            # Estimate purification (30 days from cloning)
            estimated_purification = cloning_date + pd.Timedelta(days=30)
            gantt_data.append({
                'Task': molecule_id,
                'Start': cloning_date,
                'Finish': estimated_purification,
                'Phase': 'Purification (Est.)',
                'Priority': priority,
                'Status': status,
            })

    if not gantt_data:
        fig = go.Figure()
        fig.add_annotation(
            text="No timeline data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="gray")
        )
        fig.update_layout(height=GANTT_CHART_HEIGHT)
        return fig

    df_gantt = pd.DataFrame(gantt_data)

    # Use px.timeline for better date handling (same as molecule_dashboard)
    color_map = {
        'Cloning': PHASE_COLORS.get('Cloning', '#4ECDC4'),
        'Cloning (Est.)': PHASE_COLORS.get('Cloning', '#4ECDC4'),
        'Purification': PHASE_COLORS.get('Purification', '#45B7D1'),
        'Purification (Est.)': PHASE_COLORS.get('Purification', '#45B7D1'),
    }

    fig = px.timeline(
        df_gantt,
        x_start='Start',
        x_end='Finish',
        y='Task',
        color='Phase',
        color_discrete_map=color_map,
        title='Project Timeline (Gantt Chart)',
        hover_data=['Status', 'Priority']
    )

    # Make estimated phases semi-transparent
    for trace in fig.data:
        if '(Est.)' in trace.name:
            trace.marker.opacity = 0.4
        else:
            trace.marker.opacity = 0.8

    # Update layout
    fig.update_layout(
        title={
            'text': 'Project Timeline (Gantt Chart)',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20, 'color': '#2c3e50'}
        },
        xaxis_title='Date',
        yaxis_title='Project',
        height=GANTT_CHART_HEIGHT,
        hovermode='closest',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(size=11),
        xaxis=dict(
            showgrid=True,
            gridcolor='#ecf0f1',
            type='date'
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor='#ecf0f1',
            autorange='reversed',  # Most recent at top
            categoryorder='total ascending'
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=150, r=50, t=100, b=50),
        bargap=0.15
    )

    # Add molecule images with priority-colored borders
    for project in projects_data:
        molecule_id = project['molecule_id']
        priority = project['priority_set']

        # Get the latest phase for this molecule from gantt_data
        molecule_phases = [d for d in gantt_data if d['Task'] == molecule_id]
        if not molecule_phases:
            continue

        # Use the last (most recent) phase
        latest_phase = molecule_phases[-1]

        # Calculate midpoint of the phase
        start = latest_phase['Start']
        finish = latest_phase['Finish']
        midpoint = start + (finish - start) / 2

        # Determine border color based on priority
        border_color = PRIORITY_COLORS.get(priority, '#95a5a6')

        # Get image URL
        image_url = f"http://fs2.systimmune.net/imgs/{molecule_id}.png"

        # Add invisible scatter marker for positioning
        fig.add_scatter(
            x=[midpoint],
            y=[molecule_id],
            mode='markers',
            marker=dict(
                size=55,
                symbol='square',
                color='white',
                opacity=0.01,  # Nearly invisible
                line=dict(width=4, color=border_color)
            ),
            showlegend=False,
            hoverinfo='skip',
            customdata=[[{
                'molecule_id': molecule_id,
                'priority': priority,
                'status': project.get('status'),
                'image_url': image_url
            }]]
        )

        # Add actual molecule image
        fig.add_layout_image(
            dict(
                source=image_url,
                xref="x",
                yref="y",
                x=midpoint,
                y=molecule_id,
                sizex=timedelta(days=5).total_seconds() * 1000,  # 5 days width
                sizey=0.6,  # Height relative to row
                xanchor="center",
                yanchor="middle",
                sizing="contain",
                opacity=0.95,
                layer="above"
            )
        )

    return fig


def create_priority_matrix(projects_data: List[Dict[str, Any]]) -> go.Figure:
    """
    Create a priority matrix showing projects by completion vs priority.

    Args:
        projects_data: List of project dictionaries

    Returns:
        Plotly Figure with scatter plot matrix
    """
    if not projects_data:
        fig = go.Figure()
        fig.add_annotation(
            text="No project data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="gray")
        )
        return fig

    df = pd.DataFrame(projects_data)

    # Handle NaN lead_time values - use default size of 20 for projects without lead time
    df['lead_time_display'] = df['lead_time'].fillna(20)

    # Create scatter plot
    fig = px.scatter(
        df,
        x='weighted_score',
        y='priority_set',
        color='recommendation',
        size='lead_time_display',
        hover_data=['molecule_id', 'status', 'completion_score'],
        text='molecule_id',
        color_discrete_map=RECOMMENDATION_COLORS,
        title='Priority Matrix: Performance vs Priority',
    )

    # Update traces
    fig.update_traces(
        textposition='top center',
        textfont=dict(size=9),
        marker=dict(
            line=dict(width=2, color='white'),
            sizemode='diameter',
            sizemin=10
        )
    )

    # Add quadrant lines
    fig.add_hline(y=1.5, line_dash="dash", line_color="gray", opacity=0.5)
    fig.add_vline(x=50, line_dash="dash", line_color="gray", opacity=0.5)

    # Add quadrant annotations
    annotations = [
        dict(x=75, y=1, text="High Priority<br>High Performance<br><b>PUSH FORWARD</b>",
             showarrow=False, font=dict(size=12, color='green'), bgcolor='rgba(200,255,200,0.3)'),
        dict(x=25, y=1, text="High Priority<br>Low Performance<br><b>REVIEW</b>",
             showarrow=False, font=dict(size=12, color='orange'), bgcolor='rgba(255,240,200,0.3)'),
        dict(x=75, y=2.5, text="Low Priority<br>High Performance<br><b>MONITOR</b>",
             showarrow=False, font=dict(size=12, color='blue'), bgcolor='rgba(200,240,255,0.3)'),
        dict(x=25, y=2.5, text="Low Priority<br>Low Performance<br><b>CANCEL?</b>",
             showarrow=False, font=dict(size=12, color='red'), bgcolor='rgba(255,200,200,0.3)'),
    ]

    fig.update_layout(
        annotations=annotations,
        xaxis_title='Weighted Score',
        yaxis_title='Priority Set (1=High, 3=Low)',
        yaxis=dict(autorange='reversed'),
        height=700,
        plot_bgcolor='white',
        paper_bgcolor='white',
        hovermode='closest',
        legend=dict(
            title='Recommendation',
            orientation="v",
            yanchor="top",
            y=1,
            xanchor="left",
            x=1.02
        )
    )

    return fig


def create_status_distribution_chart(projects_data: List[Dict[str, Any]]) -> go.Figure:
    """
    Create a pie chart showing status distribution.

    Args:
        projects_data: List of project dictionaries

    Returns:
        Plotly Figure with pie chart
    """
    if not projects_data:
        fig = go.Figure()
        fig.add_annotation(
            text="No project data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="gray")
        )
        return fig

    df = pd.DataFrame(projects_data)
    status_counts = df['status'].value_counts()

    fig = go.Figure(data=[go.Pie(
        labels=status_counts.index,
        values=status_counts.values,
        marker=dict(
            colors=[STATUS_COLORS.get(s, '#95A5A6') for s in status_counts.index],
            line=dict(color='white', width=2)
        ),
        textinfo='label+percent+value',
        textfont=dict(size=14),
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
    )])

    fig.update_layout(
        title={
            'text': 'Project Status Distribution',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18}
        },
        height=400,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5
        )
    )

    return fig


def create_recommendation_distribution_chart(projects_data: List[Dict[str, Any]]) -> go.Figure:
    """
    Create a bar chart showing recommendation distribution.

    Args:
        projects_data: List of project dictionaries

    Returns:
        Plotly Figure with bar chart
    """
    if not projects_data:
        fig = go.Figure()
        fig.add_annotation(
            text="No project data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="gray")
        )
        return fig

    df = pd.DataFrame(projects_data)
    rec_counts = df['recommendation'].value_counts()

    colors = [RECOMMENDATION_COLORS.get(r, '#95A5A6') for r in rec_counts.index]

    fig = go.Figure(data=[go.Bar(
        x=rec_counts.index,
        y=rec_counts.values,
        marker=dict(
            color=colors,
            line=dict(color='white', width=2)
        ),
        text=rec_counts.values,
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Count: %{y}<extra></extra>'
    )])

    fig.update_layout(
        title={
            'text': 'System Recommendations',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18}
        },
        xaxis_title='Recommendation',
        yaxis_title='Number of Projects',
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='#ecf0f1')
    )

    return fig


def create_score_histogram(projects_data: List[Dict[str, Any]]) -> go.Figure:
    """
    Create a histogram of project scores.

    Args:
        projects_data: List of project dictionaries

    Returns:
        Plotly Figure with histogram
    """
    if not projects_data:
        fig = go.Figure()
        fig.add_annotation(
            text="No project data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="gray")
        )
        return fig

    df = pd.DataFrame(projects_data)

    fig = go.Figure(data=[go.Histogram(
        x=df['weighted_score'],
        nbinsx=20,
        marker=dict(
            color='#3498db',
            line=dict(color='white', width=1)
        ),
        hovertemplate='Score Range: %{x}<br>Count: %{y}<extra></extra>'
    )])

    # Add threshold lines
    fig.add_vline(x=75, line_dash="dash", line_color="green",
                  annotation_text="Push Forward (75+)", annotation_position="top right")
    fig.add_vline(x=50, line_dash="dash", line_color="blue",
                  annotation_text="Monitor (50+)", annotation_position="top right")
    fig.add_vline(x=30, line_dash="dash", line_color="orange",
                  annotation_text="Review (30+)", annotation_position="top right")

    fig.update_layout(
        title={
            'text': 'Score Distribution',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18}
        },
        xaxis_title='Weighted Score',
        yaxis_title='Number of Projects',
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white',
        xaxis=dict(showgrid=True, gridcolor='#ecf0f1'),
        yaxis=dict(showgrid=True, gridcolor='#ecf0f1')
    )

    return fig


def create_lead_time_chart(projects_data: List[Dict[str, Any]]) -> go.Figure:
    """
    Create a box plot showing lead time distribution by priority.

    Args:
        projects_data: List of project dictionaries

    Returns:
        Plotly Figure with box plot
    """
    if not projects_data:
        fig = go.Figure()
        fig.add_annotation(
            text="No project data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="gray")
        )
        return fig

    df = pd.DataFrame(projects_data)
    df = df[df['lead_time'].notna()]  # Remove null lead times

    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No lead time data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20, color="gray")
        )
        return fig

    fig = go.Figure()

    for priority in sorted(df['priority_set'].unique()):
        priority_data = df[df['priority_set'] == priority]

        fig.add_trace(go.Box(
            y=priority_data['lead_time'],
            name=f'Priority {priority}',
            marker=dict(color=PRIORITY_COLORS.get(priority, '#95A5A6')),
            boxmean='sd',
            hovertemplate='<b>Priority %{x}</b><br>Lead Time: %{y} days<extra></extra>'
        ))

    fig.update_layout(
        title={
            'text': 'Lead Time Distribution by Priority',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18}
        },
        xaxis_title='Priority Set',
        yaxis_title='Lead Time (days)',
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white',
        yaxis=dict(showgrid=True, gridcolor='#ecf0f1')
    )

    return fig
