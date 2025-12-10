from nicegui import ui
from supertracer.connectors.base import BaseConnector
from supertracer.ui.components.request_detail_components import (
    general_info_card, performance_card, client_info_card,
    request_info_section, response_info_section
)

def render_request_detail_page(log_id: int, connector: BaseConnector):
    log = connector.fetch_log(log_id)
    
    if not log:
        ui.label(f'Log with ID {log_id} not found').classes('text-xl text-red-500')
        return

    # Header
    with ui.header().classes('sticky top-0 z-10 flex items-center justify-between whitespace-nowrap border-b border-solid border-gray-200/80 dark:border-gray-800/80 bg-background-light/80 dark:bg-background-dark/80 px-4 py-3 backdrop-blur-sm sm:px-6 lg:px-8'):
        with ui.row().classes('items-center gap-4'):
            ui.button(icon='arrow_back', on_click=lambda: ui.navigate.to('/supertracer/logs')).props('flat round color=gray')
            ui.element('div').classes('h-6 w-px bg-gray-200 dark:bg-gray-800')
            ui.label('Detalle de Petición/Respuesta Avanzado').classes('text-lg font-bold leading-tight tracking-[-0.015em] text-gray-900 dark:text-white')

    # Main Content
    with ui.column().classes('w-full max-w-7xl mx-auto p-4 sm:p-6 lg:p-8 gap-8'):
        # General Info
        general_info_card(log)
        
        # Grid for Performance and Client Info
        with ui.grid(columns=3).classes('w-full gap-8 lg:grid-cols-3'):
            with ui.column().classes('lg:col-span-1 gap-8 w-full'):
                performance_card(log)
                client_info_card(log)
            
            with ui.column().classes('lg:col-span-2 gap-8 w-full'):
                request_info_section(log)
                response_info_section(log)
