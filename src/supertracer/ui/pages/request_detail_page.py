from nicegui import ui
from supertracer.connectors.base import BaseConnector
from supertracer.auth_service import AuthService
from supertracer.ui.components.header import page_header
from supertracer.ui.components.request_detail_components import (
    content_card, general_info_card, performance_card, client_info_card,
    request_info_section, response_info_section
)

def render_request_detail_page(log_id: int, connector: BaseConnector, auth_service: AuthService):
    log = connector.fetch_log(log_id)
    
    if not log:
        with ui.column().classes('w-full min-h-screen bg-gray-900 p-6 items-center justify-center'):
            ui.label(f'Log with ID {log_id} not found').classes('text-xl text-red-500')
            ui.button('Go Back', on_click=lambda: ui.navigate.to('/supertracer/logs')).props('outline color=white')
        return

    with ui.column().classes('w-full min-h-screen bg-gray-900 p-6 gap-6'):
        # Header
        page_header('Request Details', auth_service, back_path='/supertracer/logs')
        
        # Main Content
        with ui.column().classes('w-full max-w-7xl mx-auto gap-6'):
            # General Info
            
            # Grid for Performance and Client Info
            with ui.grid(columns=3).classes('w-full gap-6 lg:grid-cols-3'):
                with ui.column().classes('lg:col-span-1 gap-6 w-full'):
                    general_info_card(log)
                    performance_card(log) if log.get('method') else None
                    client_info_card(log) if log.get('method') else None
                
                with ui.column().classes('lg:col-span-2 gap-6 w-full'):
                    if log.get('method'):
                        request_info_section(log) 
                        response_info_section(log) 
                        
                    else:
                        content_card(log.get('content') or '')
