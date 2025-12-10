from nicegui import ui
from typing import Optional
from supertracer.services.auth import AuthService

def page_header(title: str, auth_service: Optional[AuthService] = None, back_path: Optional[str] = None):
    with ui.row().classes('w-full items-center justify-between border-b border-gray-700 pb-4 sticky top-0 bg-gray-900 z-20'):
        with ui.row().classes('items-center gap-4'):
            if back_path:
                ui.button(icon='arrow_back', on_click=lambda: ui.navigate.to(back_path.removeprefix('/supertracer'))).props('flat round color=white')
            ui.label(title).classes('text-2xl font-bold text-white')
        
        if auth_service and auth_service.enabled:
            ui.button('Logout', icon='logout', on_click=auth_service.logout).props('flat color=white')
