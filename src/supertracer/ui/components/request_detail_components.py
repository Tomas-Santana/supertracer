from nicegui import ui
from typing import Dict, Any, Optional
from supertracer.types.logs import Log
from supertracer.ui.components.badges import status_code_badge, http_method_badge
import json

def general_info_card(log: Log):
    with ui.card().classes('w-full p-6 rounded-xl border border-gray-700 bg-transparent text-white'):
        with ui.column().classes('gap-6 w-full'):
            # Header with Title and Badges
            with ui.row().classes('w-full justify-between items-center flex-wrap gap-4'):
                ui.label('General').classes('text-gray-400 text-xl mb-2')
                with ui.row().classes('gap-2 items-center'):
                    if log.get('status_code'):
                        status_code_badge(log.get('status_code') or 200)
                    
                    if log.get('method'):
                        http_method_badge(log.get('method') or 'GET')

            # Info Rows
            _metric_row('Log ID', str(log.get('id') or 'N/A'))
            _metric_row('Timestamp', str(log.get('timestamp').strftime('%Y-%m-%d %H:%M:%S') if log.get('timestamp') else 'N/A'))
            _metric_row('Path', log.get('path') or 'N/A')  if log.get('path') else 'N/A'
            
def performance_card(log: Log):
    with ui.card().classes('w-full p-6 rounded-xl border border-gray-700 bg-transparent text-white'):
        ui.label('Performance').classes('text-xl font-bold text-gray-400 mb-4')
        with ui.column().classes('space-y-3 w-full'):
            _metric_row('Latency', f"{log.get('duration_ms')}ms")
            _metric_row('Response Size', f"{log.get('response_size_bytes') or 0} bytes")
            # Processing Time is usually same as Latency in this context unless we track more granularly
            _metric_row('Processing Time', f"{log.get('duration_ms')}ms")

def client_info_card(log: Log):
    with ui.card().classes('w-full p-6 rounded-xl border border-gray-700 bg-transparent text-white'):
        ui.label('Client Info').classes('text-xl font-bold text-gray-400 mb-4')
        with ui.column().classes('space-y-3 w-full'):
            _metric_row('Client IP', log.get('client_ip') or 'N/A')
            _metric_row('User Agent', log.get('user_agent') or 'N/A')

def content_card(content: str):
    language = 'text'
    with ui.card().classes('w-full p-6 rounded-xl border border-gray-700 bg-transparent text-white'):
        ui.label('Content').classes('text-xl font-bold text-gray-400 mb-4')
        if content:
            try:
                parsed = json.loads(content.replace("'", '"'))
                content = json.dumps(parsed, indent=2)
                language = 'json'
            except json.JSONDecodeError:
                pass
            ui.code(content, language=language).classes('w-full rounded-lg bg-gray-900 p-4 text-sm overflow-x-auto text-pretty')
        else:
            ui.label('No content available').classes('text-sm text-gray-500 italic')

def _metric_row(label: str, value: str):
    with ui.row().classes('w-full justify-between items-baseline'):
        ui.label(label).classes('text-sm text-gray-400')
        ui.label(value).classes('text-base font-semibold text-white')

def headers_table(headers: Optional[Dict[str, Any]], empty_message: str = 'No headers'):
    if not headers:
        ui.label(empty_message).classes('text-sm text-gray-500 italic')
        return
        
    with ui.element('div').classes('max-h-60 overflow-y-auto rounded-lg border border-gray-700 w-full'):
        with ui.element('table').classes('w-full text-sm'):
            with ui.element('tbody').classes('divide-y divide-gray-700 font-mono'):
                for i, (key, value) in enumerate(headers.items()):
                    bg_class = 'bg-gray-800/50' if i % 2 != 0 else ''
                    with ui.element('tr').classes(f'divide-x divide-gray-700 {bg_class}'):
                        with ui.element('td').classes('w-1/3 px-3 py-2 font-medium text-gray-400'):
                            ui.label(key)
                        with ui.element('td').classes('px-3 py-2 text-gray-300 break-all'):
                            ui.label(str(value))

def json_viewer(data: Any):
    if not data:
        ui.label('No content').classes('text-sm text-gray-500 italic')
        return
    
    content = json.dumps(data, indent=2) if isinstance(data, (dict, list)) else str(data)
    ui.code(content, language='json').classes('w-full rounded-lg bg-gray-900 p-4 text-sm overflow-x-auto')

def request_info_section(log: Log):
    with ui.expansion('Request Info', icon='upload').classes('w-full rounded-xl border border-gray-700 bg-transparent text-white p-2') as exp:
        exp.value = True  # Default to opened
        with ui.column().classes('w-full gap-6 p-4'):
            with ui.column().classes('w-full'):
                ui.label('Request Headers').classes('mb-2 text-base font-semibold text-gray-300')
                headers_table(log.get('headers'))
            
            with ui.column().classes('w-full'):
                ui.label('Query Parameters').classes('mb-2 text-base font-semibold text-gray-300')
                headers_table(log.get('request_query'), empty_message='No query parameters')
            
            if log.get('request_body'):
                with ui.column().classes('w-full'):
                    ui.label('Request Body').classes('mb-2 text-base font-semibold text-gray-300')
                    json_viewer(log.get('request_body'))

def response_info_section(log: Log):
    is_error = (log.get('status_code') or 200) >= 400
    border_color = 'red-500/50' if is_error else 'gray-700'
    bg_color = 'red-900/20' if is_error else 'transparent'
    
    with ui.expansion('Response & Error Info', icon='download').classes(f'w-full rounded-xl border border-{border_color} bg-{bg_color} text-white p-2').props('default-opened'):
        with ui.column().classes('w-full gap-6 p-4'):
            with ui.column().classes('w-full'):
                ui.label('Response Headers').classes('mb-2 text-base font-semibold text-gray-300')
                headers_table(log.get('response_headers'))
                
                # response body if exists
            if log.get('response_body'):
                with ui.column().classes('w-full'):
                    ui.label('Response Body').classes('mb-2 text-base font-semibold text-gray-300')
                    json_viewer(log.get('response_body'))
        
            
            if is_error:
                with ui.column().classes('w-full space-y-4'):
                    ui.label('Error Info').classes('mb-2 text-base font-semibold')
                    
                    with ui.column():
                        ui.label('Error Message').classes('text-xs text-gray-400')
                        ui.label(str(log.get('error_message'))).classes('font-mono text-sm text-red-400')
                    
                    if log.get('stack_trace'):
                        with ui.column().classes('w-full'):
                            ui.label('Stack Trace').classes('mb-1 text-xs text-gray-400')
                            ui.code(log['stack_trace'] or "", language='text').classes('w-full max-h-96 overflow-y-auto rounded-lg bg-gray-900 p-4 font-mono text-sm text-red-400')
