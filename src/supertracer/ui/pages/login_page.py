from nicegui import ui
from supertracer.auth import AuthService

def render_login_page(auth_service: AuthService):
    def try_login():
        if auth_service.authenticate(username.value, password.value):
            auth_service.login(username.value)
            ui.navigate.to('/logs')
        else:
            ui.notify('Invalid username or password', color='negative')

    with ui.column().classes('w-full min-h-screen items-center justify-center bg-gray-900 p-4'):
        with ui.card().classes('w-full max-w-sm p-8 gap-6 bg-gray-800 border border-gray-700'):
            ui.label('SuperTracer Login').classes('text-2xl font-bold text-white w-full text-center')
            
            username = ui.input('Username').classes('w-full').props('dark outlined')
            password = ui.input('Password', password=True, password_toggle_button=True).classes('w-full').props('dark outlined').on('keydown.enter', try_login)
            
            ui.button('Log in', on_click=try_login).classes('w-full bg-blue-600 hover:bg-blue-700 text-white')
