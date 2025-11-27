from nicegui import ui


def log_type_badge(log_type: str) -> ui.row:
    """Reusable log type badge component with color coding."""
    color_map = {
        'INFO': 'bg-blue-700',
        'HTTP': 'bg-blue-600',
        'WARN': 'bg-orange-600',
        'ERROR': 'bg-red-700',
        'DEBUG': 'bg-gray-700'
    }
    
    icon_map = {
        'INFO': 'info',
        'HTTP': 'http',
        'WARN': 'warning',
        'ERROR': 'error',
        'DEBUG': 'bug_report'
    }
    
    bg_color = color_map.get(log_type, 'bg-gray-600')
    icon = icon_map.get(log_type, 'circle')
    
    with ui.row().classes(f'{bg_color} rounded px-3 py-1 items-center justify-center gap-1 text-white font-semibold text-xs w-20') as badge:
        ui.icon(icon).classes('text-sm')
        ui.label(log_type).classes('text-xs')
    
    return badge


def http_method_badge(method: str) -> ui.label:
    """Reusable HTTP method badge component."""
    color_map = {
        'GET': 'text-blue-400',
        'POST': 'text-green-400',
        'PUT': 'text-purple-400',
        'DELETE': 'text-red-400',
        'PATCH': 'text-yellow-400'
    }
    
    text_color = color_map.get(method, 'text-gray-400')
    
    return ui.label(method).classes(f'{text_color} font-bold text-sm')


def status_code_badge(status_code: int) -> ui.label:
    """Reusable status code badge component with color coding."""
    if 200 <= status_code < 300:
        color = 'text-green-500 bg-green-950'
    elif 400 <= status_code < 500:
        color = 'text-yellow-500 bg-yellow-950'
    elif 500 <= status_code < 600:
        color = 'text-red-500 bg-red-950'
    else:
        color = 'text-gray-500 bg-gray-950'
    
    status_text = {
        200: '200 OK',
        404: '404 Not Found',
        500: '500 Server Error'
    }.get(status_code, f'{status_code}')
    
    return ui.label(status_text).classes(
        f'{color} px-4 py-1 rounded-full text-xs font-semibold'
    )
