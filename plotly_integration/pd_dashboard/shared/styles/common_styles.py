# Enhanced common_styles.py with lighter colors and blue tables

# Color palette - Updated with lighter, less gray colors
COLORS = {
    'primary': '#007bff',
    'secondary': '#6c757d',
    'success': '#28a745',
    'danger': '#dc3545',
    'warning': '#ffc107',
    'info': '#17a2b8',
    'light': '#ffffff',  # Changed from gray to white
    'dark': '#343a40',
    'white': '#ffffff',
    # Modern additions with lighter theme
    'primary_gradient': 'linear-gradient(135deg, #4dabf7 0%, #339af0 100%)',  # Lighter blue
    'success_gradient': 'linear-gradient(135deg, #51cf66 0%, #40c057 100%)',  # Lighter green
    'info_gradient': 'linear-gradient(135deg, #74c0fc 0%, #339af0 100%)',     # Lighter blue
    'warning_gradient': 'linear-gradient(135deg, #ffd43b 0%, #fab005 100%)',  # Lighter yellow
    'card_shadow': '0 2px 4px rgba(0, 0, 0, 0.06)',     # Lighter shadow
    'card_shadow_hover': '0 4px 8px rgba(0, 0, 0, 0.1)',  # Lighter hover
    'table_blue': '#e3f2fd',     # Light blue for tables
    'table_blue_dark': '#1976d2' # Darker blue for headers
}

# Enhanced layout styles with lighter aesthetics
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "left": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background": "linear-gradient(180deg, #ffffff 0%, #f8fafc 100%)",  # Much lighter
    "borderRight": "1px solid #e2e8f0",  # Lighter border
    "overflowY": "auto",
    "boxShadow": "2px 0 8px rgba(0,0,0,0.05)",  # Much lighter shadow
    "zIndex": 1000
}

CONTENT_STYLE = {
    "marginLeft": "200px",  # 🎯 Changed from 250px to match new sidebar width
    "padding": "2rem",
    "backgroundColor": "#fafbfc",
    "minHeight": "100vh"
}

# Enhanced table styles with blue theme
TABLE_STYLE_CELL = {
    'textAlign': 'left',
    'padding': '12px 16px',
    'fontSize': '14px',
    'fontFamily': '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    'border': '1px solid #e3f2fd',  # Light blue border
    'backgroundColor': 'white',
    'transition': 'background-color 0.2s ease'
}

TABLE_STYLE_HEADER = {
    'backgroundColor': COLORS['table_blue_dark'],  # Blue header
    'color': 'white',
    'fontWeight': '600',
    'textAlign': 'center',
    'padding': '16px',
    'border': '1px solid #1976d2',
    'fontSize': '14px',
    'textTransform': 'uppercase',
    'letterSpacing': '0.5px'
}

TABLE_STYLE_DATA = {
    'backgroundColor': 'white',
    'color': '#2c3e50',  # Darker text for better contrast
    'border': '1px solid #e3f2fd',  # Light blue border
    'borderRadius': '0'
}

# Modern card styles with lighter shadows
CARD_STYLE = {
    'marginBottom': '1.5rem',
    'boxShadow': COLORS['card_shadow'],
    'border': 'none',
    'borderRadius': '12px',
    'transition': 'all 0.3s ease',
    'backgroundColor': 'white'
}

CARD_HOVER_STYLE = {
    'marginBottom': '1.5rem',
    'boxShadow': COLORS['card_shadow_hover'],
    'border': 'none',
    'borderRadius': '12px',
    'transition': 'all 0.3s ease',
    'backgroundColor': 'white',
    'cursor': 'pointer'
}

# Enhanced button styles
BUTTON_STYLE_PRIMARY = {
    'margin': '0.25rem',
    'fontSize': '0.875rem',
    'fontWeight': '500',
    'borderRadius': '8px',
    'padding': '0.5rem 1rem',
    'border': 'none',
    'boxShadow': '0 2px 4px rgba(0,123,255,0.15)',  # Lighter shadow
    'transition': 'all 0.2s ease'
}

BUTTON_STYLE_SECONDARY = {
    'margin': '0.25rem',
    'fontSize': '0.875rem',
    'fontWeight': '500',
    'borderRadius': '8px',
    'padding': '0.5rem 1rem',
    'border': '1px solid #e2e8f0',  # Lighter border
    'backgroundColor': 'white',
    'color': '#4a5568',  # Lighter gray text
    'transition': 'all 0.2s ease'
}

# Navigation icons with symbols
ICONS = {
    'dashboard': 'fa-tachometer-alt',
    'samples': 'fa-vial',
    'sample_sets': 'fa-layer-group',
    'add': 'fa-plus',
    'analytics': 'fa-chart-bar',
    'sec': 'fa-microscope',
    'reports': 'fa-chart-line',
    'settings': 'fa-cogs',
    'view': 'fa-eye',
    'create': 'fa-plus-circle',
    'edit': 'fa-edit',
    'delete': 'fa-trash',
    'download': 'fa-download',
    'upload': 'fa-upload',
    'refresh': 'fa-sync-alt',
    'live': 'fa-broadcast-tower',
    'health': 'fa-heartbeat',
    'trend_up': 'fa-arrow-trend-up',
    'trend_down': 'fa-arrow-trend-down'
}

# Status colors with lighter theme
STATUS_COLORS = {
    'REQUESTED': 'warning',
    'DATA_AVAILABLE': 'info',
    'REPORT_CREATED': 'success',
    'COMPLETED': 'success',
    'ERROR': 'danger',
    'PENDING': 'secondary',
    'IN_PROGRESS': 'primary',
    'HEALTHY': 'success',
    'WARNING': 'warning',
    'CRITICAL': 'danger'
}

STATUS_ICONS = {
    'REQUESTED': 'fa-clock',
    'DATA_AVAILABLE': 'fa-database',
    'REPORT_CREATED': 'fa-file-alt',
    'COMPLETED': 'fa-check-circle',
    'ERROR': 'fa-exclamation-triangle',
    'PENDING': 'fa-hourglass-half',
    'IN_PROGRESS': 'fa-spinner fa-spin',
    'HEALTHY': 'fa-check-circle',
    'WARNING': 'fa-exclamation-triangle',
    'CRITICAL': 'fa-times-circle'
}

# CSS classes for enhanced styling with lighter theme
CSS_CLASSES = """
/* Modern card hover effects */
.card-hover {
    transition: all 0.3s ease;
}

.card-hover:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.08) !important;
}

/* Enhanced table styling with blue theme */
.dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner table {
    border-collapse: separate;
    border-spacing: 0;
    border-radius: 8px;
    overflow: hidden;
}

.dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner th {
    background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%);
    position: sticky;
    top: 0;
    z-index: 10;
}

.dash-table-container .dash-spreadsheet-container .dash-spreadsheet-inner td:hover {
    background-color: #e3f2fd !important;
}

/* Modern sidebar styling with lighter theme */
.nav-link {
    border-radius: 8px;
    transition: all 0.2s ease;
    margin-bottom: 4px;
    color: #4a5568 !important;
}

.nav-link:hover {
    background-color: rgba(66, 165, 245, 0.08);
    transform: translateX(2px);
    color: #1976d2 !important;
}

.nav-link.active {
    background: linear-gradient(135deg, #42a5f5 0%, #1976d2 100%);
    color: white !important;
    box-shadow: 0 2px 4px rgba(25, 118, 210, 0.2);
}

/* Statistics card enhancements with lighter theme */
.stat-card {
    background: white;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.06);
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
    border: 1px solid #f0f4f8;
}

.stat-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: linear-gradient(90deg, #42a5f5, #66bb6a, #ffca28, #ef5350);
}

.stat-card:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.08);
}

/* Activity feed styling with lighter theme */
.activity-item {
    padding: 0.75rem;
    border-left: 3px solid #42a5f5;
    background: #fafbfc;
    margin-bottom: 0.5rem;
    border-radius: 0 8px 8px 0;
    transition: all 0.2s ease;
}

.activity-item:hover {
    background: #f0f4f8;
    border-left-color: #66bb6a;
}
"""

# Loading spinner style with lighter theme
LOADING_STYLE = {
    'textAlign': 'center',
    'padding': '3rem',
    'color': '#64748b'  # Lighter gray
}

# Toast notification styles
TOAST_STYLE = {
    'position': 'fixed',
    'top': '20px',
    'right': '20px',
    'zIndex': 9999,
    'minWidth': '300px',
    'borderRadius': '8px',
    'boxShadow': '0 4px 12px rgba(0,0,0,0.08)'  # Lighter shadow
}

# Modern input styles with lighter theme
INPUT_STYLE = {
    'borderRadius': '8px',
    'border': '1px solid #e2e8f0',
    'padding': '0.75rem',
    'fontSize': '14px',
    'transition': 'border-color 0.2s ease, box-shadow 0.2s ease',
    'backgroundColor': 'white'
}

# Dropdown styles
DROPDOWN_STYLE = {
    'borderRadius': '8px',
    'border': '1px solid #e2e8f0',
    'fontSize': '14px',
    'backgroundColor': 'white'
}

# Badge styles for modern look with blue theme
BADGE_STYLE = {
    'borderRadius': '6px',
    'padding': '0.25rem 0.5rem',
    'fontSize': '0.75rem',
    'fontWeight': '500',
    'textTransform': 'uppercase',
    'letterSpacing': '0.5px'
}

# Utility functions remain the same but with updated colors
def get_status_style(status):
    """Get styling for status indicators"""
    color = STATUS_COLORS.get(status, 'secondary')
    icon = STATUS_ICONS.get(status, 'fa-question')

    return {
        'color': color,
        'icon': icon,
        'badge_color': color
    }

def get_trend_indicator(current, previous):
    """Get trend indicator with styling"""
    if current > previous:
        return {
            'icon': 'fa-arrow-up',
            'color': 'success',
            'text': f'↗ +{((current - previous) / previous * 100):.1f}%'
        }
    elif current < previous:
        return {
            'icon': 'fa-arrow-down',
            'color': 'danger',
            'text': f'↘ -{((previous - current) / previous * 100):.1f}%'
        }
    else:
        return {
            'icon': 'fa-minus',
            'color': 'muted',
            'text': '→ 0%'
        }

def create_gradient_style(color1, color2, direction='135deg'):
    """Create gradient background style"""
    return {
        'background': f'linear-gradient({direction}, {color1} 0%, {color2} 100%)'
    }

def create_shadow_style(elevation='medium'):
    """Create box shadow based on elevation - lighter shadows"""
    shadows = {
        'low': '0 1px 3px rgba(0,0,0,0.06)',
        'medium': '0 2px 4px rgba(0,0,0,0.06)',
        'high': '0 4px 8px rgba(0,0,0,0.08)',
        'highest': '0 8px 16px rgba(0,0,0,0.1)'
    }

    return {'boxShadow': shadows.get(elevation, shadows['medium'])}


# =============================================================================
# SIDEBAR CONFIGURATION - Easy to adjust all sidebar styling from here
# =============================================================================

SIDEBAR_CONFIG = {
    # Sidebar dimensions
    'width': '220px',  # 🎯 Slightly wider for better text fit
    'padding': '1rem',

    # Text sizes
    'title_font_size': '18px',  # Dashboard title
    'main_item_font_size': '16px',  # Main section titles (CLD, USP, etc.)
    'dropdown_item_font_size': '15px',  # Dropdown items (Create Samples, etc.)
    'user_font_size': '14px',  # User text at bottom

    # Icon sizes
    'main_icon_size': '16px',  # Main section icons
    'dropdown_icon_size': '14px',  # Dropdown item icons
    'chevron_size': '12px',  # Chevron arrows

    # Spacing and layout
    'dropdown_offset': '20px',  # 🎯 Left offset for dropdown items (not 50px - too much)
    'main_item_padding': '12px 16px',  # Padding for main items
    'dropdown_item_padding': '10px 12px',  # Padding for dropdown items
    'item_margin': '3px',  # Margin between items
    'section_margin': '25px',  # Margin for logo/brand area

    # Colors
    'background_color': '#2c3e50',
    'border_color': '#34495e',
    'text_color': '#ecf0f1',
    'text_muted': '#bdc3c7',
    'accent_color': '#3498db',

    # Hover effects
    'hover_main': 'rgba(52, 152, 219, 0.1)',
    'hover_dropdown': 'rgba(52, 152, 219, 0.2)',
}

# Updated content style to match sidebar width
CONTENT_STYLE = {
    "marginLeft": SIDEBAR_CONFIG['width'],  # 🎯 Use sidebar width
    "padding": "2rem",
    "backgroundColor": "#fafbfc",
    "minHeight": "100vh"
}


# =============================================================================
# SIDEBAR STYLE BUILDER FUNCTIONS
# =============================================================================

def get_sidebar_main_style():
    """Get the main sidebar container style"""
    return {
        'position': 'fixed',
        'top': 0,
        'left': 0,
        'bottom': 0,
        'width': SIDEBAR_CONFIG['width'],
        'padding': SIDEBAR_CONFIG['padding'],
        'backgroundColor': SIDEBAR_CONFIG['background_color'],
        'borderRight': f"1px solid {SIDEBAR_CONFIG['border_color']}",
        'overflowY': 'auto',
        'overflowX': 'hidden',
        'zIndex': 1000,
        'boxSizing': 'border-box'
    }


def get_sidebar_title_style():
    """Get the dashboard title style"""
    return {
        'fontSize': SIDEBAR_CONFIG['title_font_size'],
        'fontWeight': 'bold',
        'color': SIDEBAR_CONFIG['accent_color']
    }


def get_main_item_icon_style(color):
    """Get style for main item icons"""
    return {
        'fontSize': SIDEBAR_CONFIG['main_icon_size'],
        'color': color,
        'marginRight': '10px',
        'width': '20px'
    }


def get_main_item_text_style():
    """Get style for main item text"""
    return {
        'color': SIDEBAR_CONFIG['text_color'],
        'fontSize': SIDEBAR_CONFIG['main_item_font_size']
    }


def get_main_item_button_style():
    """Get style for main item buttons"""
    return {
        'backgroundColor': 'transparent',
        'border': 'none',
        'padding': SIDEBAR_CONFIG['main_item_padding'],
        'textDecoration': 'none'
    }


def get_dropdown_container_style():
    """Get style for dropdown container"""
    return {
        'padding': f"0 0 10px {SIDEBAR_CONFIG['dropdown_offset']}"  # 🎯 Left offset here
    }


def get_dropdown_item_style():
    """Get style for individual dropdown items"""
    return {
        'display': 'flex',  # 🎯 Use flex for better alignment
        'alignItems': 'center',
        'padding': SIDEBAR_CONFIG['dropdown_item_padding'],
        'color': SIDEBAR_CONFIG['text_muted'],
        'textDecoration': 'none',
        'fontSize': SIDEBAR_CONFIG['dropdown_item_font_size'],
        'borderRadius': '4px',
        'margin': f"{SIDEBAR_CONFIG['item_margin']} 0",
        'transition': 'all 0.2s ease'
    }


def get_dropdown_icon_style():
    """Get style for dropdown item icons"""
    return {
        'width': '16px',
        'marginRight': '8px',
        'fontSize': SIDEBAR_CONFIG['dropdown_icon_size'],
        'color': SIDEBAR_CONFIG['text_muted'],
        'flexShrink': 0  # 🎯 Prevent icon from shrinking
    }


def get_chevron_style():
    """Get style for chevron arrows"""
    return {
        'fontSize': SIDEBAR_CONFIG['chevron_size'],
        'color': SIDEBAR_CONFIG['text_muted'],
        'marginLeft': 'auto'
    }


def get_logo_area_style():
    """Get style for logo/brand area"""
    return {
        'display': 'flex',
        'alignItems': 'center',
        'marginBottom': SIDEBAR_CONFIG['section_margin'],
        'padding': '10px'
    }


def get_user_area_style():
    """Get style for user area at bottom"""
    return {
        'display': 'flex',
        'alignItems': 'center',
        'padding': '10px 16px'
    }


def get_user_text_style():
    """Get style for user text"""
    return {
        'color': SIDEBAR_CONFIG['text_muted'],
        'fontSize': SIDEBAR_CONFIG['user_font_size']
    }


# CSS for hover effects
SIDEBAR_HOVER_CSS = f"""
.sidebar-main-item:hover {{
    background-color: {SIDEBAR_CONFIG['hover_main']} !important;
}}

.sidebar-sub-item:hover {{
    background-color: {SIDEBAR_CONFIG['hover_dropdown']} !important;
    color: #ffffff !important;
}}
"""