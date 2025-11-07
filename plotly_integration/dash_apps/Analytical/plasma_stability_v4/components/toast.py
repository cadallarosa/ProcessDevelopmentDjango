"""
Toast Notification Component
Auto-dismissing notifications for user feedback
"""

import dash_bootstrap_components as dbc
from dash import html


def create_toast(message, toast_type="success", header="Success", is_open=True):
    """
    Create a toast notification that auto-dismisses after 5 seconds.

    Args:
        message: The message text to display
        toast_type: Type of toast - 'success', 'error', 'info', 'warning'
        header: Header text for the toast
        is_open: Whether the toast is initially visible

    Returns:
        dbc.Toast component
    """
    # Define colors and icons for different toast types
    toast_config = {
        'success': {
            'icon': 'fas fa-check-circle',
            'icon_color': '#10b981',
            'header_bg': '#d1fae5',
            'header_color': '#065f46'
        },
        'error': {
            'icon': 'fas fa-exclamation-circle',
            'icon_color': '#dc2626',
            'header_bg': '#fee2e2',
            'header_color': '#991b1b'
        },
        'info': {
            'icon': 'fas fa-info-circle',
            'icon_color': '#2563eb',
            'header_bg': '#dbeafe',
            'header_color': '#1e40af'
        },
        'warning': {
            'icon': 'fas fa-exclamation-triangle',
            'icon_color': '#f59e0b',
            'header_bg': '#fef3c7',
            'header_color': '#92400e'
        }
    }

    config = toast_config.get(toast_type, toast_config['info'])

    toast = dbc.Toast(
        [
            html.Div([
                html.I(className=config['icon'], style={
                    'color': config['icon_color'],
                    'marginRight': '8px',
                    'fontSize': '16px'
                }),
                html.Span(message, style={'fontSize': '14px'})
            ])
        ],
        id='toast-notification',
        header=html.Div([
            html.I(className=config['icon'], style={
                'color': config['icon_color'],
                'marginRight': '8px'
            }),
            html.Span(header, style={'fontWeight': '600'})
        ]),
        is_open=is_open,
        dismissable=True,
        duration=5000,  # Auto-dismiss after 5 seconds
        icon="success" if toast_type == "success" else toast_type,
        style={
            'position': 'fixed',
            'top': '20px',
            'right': '20px',
            'minWidth': '350px',
            'zIndex': '9999',
            'boxShadow': '0 4px 12px rgba(0,0,0,0.15)',
            'borderRadius': '8px'
        },
        header_style={
            'backgroundColor': config['header_bg'],
            'color': config['header_color'],
            'fontWeight': '600',
            'padding': '12px 16px'
        },
        body_style={
            'padding': '12px 16px',
            'fontSize': '14px',
            'color': '#374151'
        }
    )

    return toast


def create_toast_container():
    """
    Create a container div for toast notifications.

    Returns:
        html.Div with id='toast-container'
    """
    return html.Div(
        id='toast-container',
        style={
            'position': 'fixed',
            'top': '20px',
            'right': '20px',
            'zIndex': '9999'
        }
    )
