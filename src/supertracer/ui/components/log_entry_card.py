from nicegui import ui
from typing import Optional
from supertracer.ui.components.badges import log_type_badge, http_method_badge, status_code_badge


def log_entry_card(
    timestamp: str,
    log_type: str,
    details: str,
    method: Optional[str] = None,
    endpoint: Optional[str] = None,
    status_code: Optional[int] = None,
    duration: Optional[str] = None
) -> ui.card:
    """Reusable log entry card component."""
    with ui.card().classes(
        'w-full bg-transparent shadow-none hover:bg-gray-800 border-b border-gray-700 transition-colors duration-200 rounded-none'
    ) as card:
        with ui.row().classes('w-full items-start gap-4'):
            # Timestamp column
            ui.label(timestamp).classes('text-gray-500 text-sm font-mono min-w-[180px]')
            
            # Type badge column
            with ui.column().classes('min-w-[100px]'):
                log_type_badge(log_type)
            
            # Details column
            with ui.column().classes('flex-1 gap-2'):
                if method and endpoint:
                    # HTTP request style
                    with ui.row().classes('items-center gap-2 flex-wrap'):
                        http_method_badge(method)
                        ui.label(endpoint).classes('text-gray-300 font-mono text-sm')
                        if status_code:
                            status_code_badge(status_code)
                        if duration:
                            ui.label(duration).classes('text-gray-500 text-sm')
                else:
                    # Regular log style
                    ui.label(details).classes('text-gray-300 text-sm')
    
    return card
