from nicegui import ui
from supertracer.connectors.base import BaseConnector
from supertracer.ui.components.request_detail_components import (
    general_info_card, performance_card, client_info_card,
    request_info_section, response_info_section
)

def render_request_detail_page(log_id: int, connector: BaseConnector):
    log = connector.fetch_log(log_id)
    
    if not log:
        with ui.column().classes('w-full min-h-screen bg-gray-900 p-6 items-center justify-center'):
            ui.label(f'Log with ID {log_id} not found').classes('text-xl text-red-500')
            ui.button('Go Back', on_click=lambda: ui.navigate.to('/logs')).props('outline color=white')
        return

    with ui.column().classes('w-full min-h-screen bg-gray-900 p-6 gap-6'):
        # Header
        with ui.row().classes('w-full items-center justify-between border-b border-gray-700 pb-4'):
            with ui.row().classes('items-center gap-4'):
                ui.button(icon='arrow_back', on_click=lambda: ui.navigate.to('/logs')).props('flat round color=white')
                ui.label('Request Details').classes('text-2xl font-bold text-white')
        
        # Main Content
        with ui.column().classes('w-full max-w-7xl mx-auto gap-6'):
            # General Info
            general_info_card(log)
            
            # Grid for Performance and Client Info
            with ui.grid(columns=3).classes('w-full gap-6 lg:grid-cols-3'):
                with ui.column().classes('lg:col-span-1 gap-6 w-full'):
                    performance_card(log)
                    client_info_card(log)
                
                with ui.column().classes('lg:col-span-2 gap-6 w-full'):
                    request_info_section(log)
                    response_info_section(log)
