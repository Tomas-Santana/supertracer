from nicegui import ui
from typing import List, Optional


def filter_dropdown(label: str, options: List[str], default: Optional[str] = None) -> ui.column:
    """Reusable filter dropdown component."""
    with ui.column().classes('flex-1 gap-2') as container:
        ui.label(label).classes('text-sm text-gray-400 font-medium')
        ui.select(
            options=options, 
            value=default or options[0]
        ).classes(
            'w-full'
        ).props('outlined dense dark')
    
    return container
