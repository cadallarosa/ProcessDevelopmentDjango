# plotly_integration/pd_dashboard/shared/styles/collapsible_styles.py
# Enhanced styles for collapsible sidebar functionality

# Enhanced CSS for collapsible sidebar
COLLAPSIBLE_SIDEBAR_CSS = """
/* Base sidebar styling */
.sidebar-section-header {
    transition: all 0.2s ease;
    user-select: none;
}

.sidebar-section-header:hover {
    background-color: rgba(255,255,255,0.1) !important;
    transform: translateX(2px);
}

.sidebar-section-header:active {
    transform: translateX(1px);
    background-color: rgba(255,255,255,0.15) !important;
}

/* Collapse icon animation */
.collapse-icon-rotated {
    transform: rotate(-90deg) !important;
}

/* Sub-items container */
.sidebar-sub-items {
    transition: max-height 0.3s ease, padding 0.3s ease;
}

/* Individual sub-item styling */
.sidebar-sub-item {
    transition: all 0.2s ease;
    position: relative;
    overflow: hidden;
}

.sidebar-sub-item:hover {
    background-color: rgba(255,255,255,0.08) !important;
    transform: translateX(3px);
    border-left: 3px solid rgba(255,255,255,0.3);
}

.sidebar-sub-item:active {
    transform: translateX(2px);
    background-color: rgba(255,255,255,0.12) !important;
}

/* Active page highlighting */
.sidebar-sub-item.active {
    background-color: rgba(255,255,255,0.15) !important;
    border-left: 3px solid #007bff;
    font-weight: 600;
}

/* Main item (Dashboard, Settings) styling */
.sidebar-main-item:hover {
    background-color: rgba(255,255,255,0.1) !important;
    transform: translateX(2px);
}

.sidebar-main-item:active {
    transform: translateX(1px);
    background-color: rgba(255,255,255,0.15) !important;
}

.sidebar-main-item.active {
    background-color: rgba(255,255,255,0.15) !important;
    border-left: 3px solid #007bff;
    font-weight: 600;
}

/* Control buttons styling */
.sidebar-controls {
    padding: 10px 5px;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    margin-bottom: 10px;
}

.sidebar-control-btn {
    background-color: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.2);
    color: rgba(255,255,255,0.8);
    transition: all 0.2s ease;
}

.sidebar-control-btn:hover {
    background-color: rgba(255,255,255,0.1);
    border-color: rgba(255,255,255,0.3);
    color: white;
    transform: translateY(-1px);
}

.sidebar-control-btn:active {
    transform: translateY(0);
    background-color: rgba(255,255,255,0.15);
}

/* Help tooltip styling */
.sidebar-help-tooltip {
    background-color: rgba(0,0,0,0.9) !important;
    border: 1px solid rgba(255,255,255,0.2);
    color: white;
    font-size: 11px;
    max-width: 200px;
}

/* Responsive design for smaller screens */
@media (max-width: 768px) {
    .sidebar-section-header:hover,
    .sidebar-sub-item:hover,
    .sidebar-main-item:hover {
        transform: none;
    }

    .sidebar-control-btn:hover {
        transform: none;
    }
}

/* Smooth scrolling for sidebar */
#main-sidebar {
    scroll-behavior: smooth;
}

/* Focus styles for accessibility */
.sidebar-section-header:focus,
.sidebar-sub-item:focus,
.sidebar-main-item:focus {
    outline: 2px solid #007bff;
    outline-offset: 2px;
}

/* Loading state */
.sidebar-loading {
    opacity: 0.6;
    pointer-events: none;
    transition: opacity 0.3s ease;
}

/* Section dividers */
.sidebar-section-divider {
    height: 1px;
    background: linear-gradient(to right, transparent, rgba(255,255,255,0.2), transparent);
    margin: 15px 0;
}

/* Notification badges (for future use) */
.sidebar-notification-badge {
    position: absolute;
    top: -2px;
    right: -2px;
    background-color: #dc3545;
    color: white;
    border-radius: 50%;
    width: 16px;
    height: 16px;
    font-size: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
}

/* Tooltip custom styles */
.tooltip-inner {
    background-color: rgba(0,0,0,0.9);
    border: 1px solid rgba(255,255,255,0.2);
    font-size: 11px;
    max-width: 250px;
}

.tooltip.bs-tooltip-right .tooltip-arrow::before {
    border-right-color: rgba(0,0,0,0.9);
}

/* Keyboard shortcut indicators */
.keyboard-shortcut {
    position: absolute;
    top: 4px;
    right: 4px;
    background-color: rgba(255,255,255,0.1);
    color: rgba(255,255,255,0.6);
    padding: 1px 4px;
    border-radius: 3px;
    font-size: 9px;
    font-family: monospace;
}

/* Animation for section expand/collapse */
@keyframes expandSection {
    from { max-height: 0; opacity: 0; }
    to { max-height: 1000px; opacity: 1; }
}

@keyframes collapseSection {
    from { max-height: 1000px; opacity: 1; }
    to { max-height: 0; opacity: 0; }
}

.section-expanding {
    animation: expandSection 0.3s ease-out;
}

.section-collapsing {
    animation: collapseSection 0.3s ease-out;
}
"""


def get_enhanced_sidebar_styles():
    """Get enhanced styles for collapsible sidebar"""
    from .common_styles import SIDEBAR_HOVER_CSS

    return SIDEBAR_HOVER_CSS + COLLAPSIBLE_SIDEBAR_CSS


def create_sidebar_style_component():
    """Create a style component for the sidebar"""
    return html.Style(get_enhanced_sidebar_styles())


# Color scheme constants for consistency
SIDEBAR_COLORS = {
    'home': '#3498db',
    'cld': '#e74c3c',
    'usp': '#27ae60',
    'dsp': '#f39c12',
    'analytical': '#9b59b6',
    'data_import': '#1abc9c',
    'settings': '#7f8c8d'
}

INTERACTION_COLORS = {
    'hover_bg': 'rgba(255,255,255,0.1)',
    'active_bg': 'rgba(255,255,255,0.15)',
    'focus_outline': '#007bff',
    'border_accent': 'rgba(255,255,255,0.2)'
}


def get_section_color(section_id):
    """Get color for a specific section"""
    return SIDEBAR_COLORS.get(section_id, '#7f8c8d')


def get_interaction_style(state='default'):
    """Get interaction styles for different states"""
    styles = {
        'default': {},
        'hover': {'backgroundColor': INTERACTION_COLORS['hover_bg']},
        'active': {'backgroundColor': INTERACTION_COLORS['active_bg']},
        'focus': {'outline': f"2px solid {INTERACTION_COLORS['focus_outline']}"}
    }
    return styles.get(state, {})


# Utility function for dynamic styling
def create_dynamic_section_style(section_id, is_expanded=True, is_active=False):
    """Create dynamic styles for sections based on state"""
    base_color = get_section_color(section_id)

    style = {
        'transition': 'all 0.2s ease',
        'borderLeft': f'3px solid {base_color}' if is_active else 'none'
    }

    if is_expanded:
        style.update({
            'maxHeight': '1000px',
            'opacity': '1'
        })
    else:
        style.update({
            'maxHeight': '0px',
            'opacity': '0',
            'paddingTop': '0px',
            'paddingBottom': '0px'
        })

    return style