from nicegui import ui
from typing import Dict, Any, Optional
from supertracer.types.logs import Log
import json

def general_info_card(log: Log):
    with ui.card().classes('w-full p-6 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900/50'):
        with ui.column().classes('gap-6 w-full'):
            # Header with Title and Badges
            with ui.row().classes('w-full justify-between items-center flex-wrap gap-4'):
                ui.label('General').classes('text-xl font-bold text-gray-900 dark:text-white')
                with ui.row().classes('gap-2'):
                    status_code = log.get('status_code')
                    method = log.get('method')
                    
                    status_color = 'green' if status_code and status_code < 400 else 'red'
                    ui.label(str(status_code)).classes(f'px-2.5 py-1 text-sm font-semibold rounded-md bg-{status_color}-500/10 text-{status_color}-500')
                    
                    method_color = 'blue' # Default
                    if method == 'GET': method_color = 'blue'
                    elif method == 'POST': method_color = 'green'
                    elif method == 'PUT': method_color = 'orange'
                    elif method == 'DELETE': method_color = 'red'
                    
                    ui.label(str(method)).classes(f'px-2.5 py-1 text-sm font-semibold rounded-md bg-{method_color}-500/10 text-{method_color}-500')

            # Grid for details
            with ui.grid(columns=4).classes('w-full gap-x-6 gap-y-4 sm:grid-cols-2 lg:grid-cols-4'):
                with ui.column():
                    ui.label('Request ID').classes('text-xs text-gray-500 dark:text-gray-400')
                    ui.label(str(log.get('id'))).classes('font-mono text-sm')
                
                with ui.column():
                    ui.label('Timestamp').classes('text-xs text-gray-500 dark:text-gray-400')
                    ui.label(str(log.get('timestamp'))).classes('font-mono text-sm')
                
                with ui.column().classes('col-span-1 sm:col-span-2'):
                    ui.label('Full Path').classes('text-xs text-gray-500 dark:text-gray-400')
                    ui.label(str(log.get('url'))).classes('font-mono text-sm truncate w-full')

def performance_card(log: Log):
    with ui.card().classes('w-full p-6 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900/50'):
        ui.label('Performance').classes('text-xl font-bold text-gray-900 dark:text-white mb-4')
        with ui.column().classes('space-y-3 w-full'):
            _metric_row('Latency', f"{log.get('duration_ms')}ms")
            _metric_row('Response Size', f"{log.get('response_size_bytes') or 0} bytes")
            # Processing Time is usually same as Latency in this context unless we track more granularly
            _metric_row('Processing Time', f"{log.get('duration_ms')}ms")

def client_info_card(log: Log):
    with ui.card().classes('w-full p-6 rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900/50'):
        ui.label('Client Info').classes('text-xl font-bold text-gray-900 dark:text-white mb-4')
        with ui.column().classes('space-y-3 w-full'):
            with ui.column():
                ui.label('IP Address').classes('text-xs text-gray-500 dark:text-gray-400')
                ui.label(str(log.get('client_ip'))).classes('font-mono text-sm')
            with ui.column():
                ui.label('User Agent').classes('text-xs text-gray-500 dark:text-gray-400')
                ui.label(str(log.get('user_agent'))).classes('text-sm break-all')

def _metric_row(label: str, value: str):
    with ui.row().classes('w-full justify-between items-baseline'):
        ui.label(label).classes('text-sm text-gray-600 dark:text-gray-400')
        ui.label(value).classes('text-base font-semibold text-gray-900 dark:text-white')

def headers_table(headers: Optional[Dict[str, Any]]):
    if not headers:
        ui.label('No headers').classes('text-sm text-gray-500 italic')
        return
        
    with ui.element('div').classes('max-h-60 overflow-y-auto rounded-lg border border-gray-200 dark:border-gray-700 w-full'):
        with ui.element('table').classes('w-full text-sm'):
            with ui.element('tbody').classes('divide-y divide-gray-200 dark:divide-gray-700 font-mono'):
                for i, (key, value) in enumerate(headers.items()):
                    bg_class = 'bg-gray-50 dark:bg-gray-800/50' if i % 2 != 0 else ''
                    with ui.element('tr').classes(f'divide-x divide-gray-200 dark:divide-gray-700 {bg_class}'):
                        with ui.element('td').classes('w-1/3 px-3 py-2 font-medium text-gray-500 dark:text-gray-400'):
                            ui.label(key)
                        with ui.element('td').classes('px-3 py-2 text-gray-700 dark:text-gray-300 break-all'):
                            ui.label(str(value))

def json_viewer(data: Any):
    if not data:
        ui.label('No content').classes('text-sm text-gray-500 italic')
        return
    
    content = json.dumps(data, indent=2) if isinstance(data, (dict, list)) else str(data)
    ui.code(content, language='json').classes('w-full rounded-lg bg-gray-900 p-4 text-sm overflow-x-auto')

def request_info_section(log: Log):
    with ui.expansion('Request Info', icon='upload').classes('w-full rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900/50 p-2').props('default-opened'):
        with ui.column().classes('w-full gap-6 p-4'):
            with ui.column().classes('w-full'):
                ui.label('Request Headers').classes('mb-2 text-base font-semibold text-gray-700 dark:text-gray-300')
                headers_table(log.get('headers'))
            
            with ui.column().classes('w-full'):
                ui.label('Query Parameters').classes('mb-2 text-base font-semibold text-gray-700 dark:text-gray-300')
                headers_table(log.get('request_query'))
            
            with ui.column().classes('w-full'):
                ui.label('Request Body').classes('mb-2 text-base font-semibold text-gray-700 dark:text-gray-300')
                json_viewer(log.get('request_body'))

def response_info_section(log: Log):
    is_error = log.get('status_code', 200) >= 400 # type: ignore
    border_color = 'red-500/30 dark:border-red-500/50' if is_error else 'gray-200 dark:border-gray-800'
    bg_color = 'red-50/20 dark:bg-red-900/20' if is_error else 'white dark:bg-gray-900/50'
    
    with ui.expansion('Response & Error Info', icon='download').classes(f'w-full rounded-xl border border-{border_color} bg-{bg_color} p-2').props('default-opened'):
        with ui.column().classes('w-full gap-6 p-4'):
            with ui.column().classes('w-full'):
                ui.label('Response Headers').classes('mb-2 text-base font-semibold text-gray-700 dark:text-gray-300')
                headers_table(log.get('response_headers'))
            
            with ui.column().classes('w-full'):
                ui.label('Response Body').classes('mb-2 text-base font-semibold text-gray-700 dark:text-gray-300')
                json_viewer(log.get('response_body'))
            
            if is_error:
                with ui.column().classes('w-full space-y-4'):
                    ui.label('Error Info').classes('mb-2 text-base font-semibold text-red-500 dark:text-red-400')
                    
                    with ui.column():
                        ui.label('Error Message').classes('text-xs text-gray-500 dark:text-gray-400')
                        ui.label(str(log.get('error_message'))).classes('font-mono text-sm text-red-500 dark:text-red-400')
                    
                    if log.get('stack_trace'):
                        with ui.column().classes('w-full'):
                            ui.label('Stack Trace').classes('mb-1 text-xs text-gray-500 dark:text-gray-400')
                            ui.code(log['stack_trace'] or "", language='text').classes('w-full max-h-96 overflow-y-auto rounded-lg bg-gray-900 p-4 font-mono text-sm text-red-400')
