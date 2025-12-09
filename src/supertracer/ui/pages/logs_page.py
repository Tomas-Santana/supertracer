from nicegui import ui
from typing import List, Dict, Any, Callable
from supertracer.ui.components.search_input import search_input
from supertracer.ui.components.log_entry_card import log_entry_card


def render_logs_page(fetch_logs_func: Callable):
    """Renders the logs page with filters and log entries.
    
    Args:
        fetch_logs_func: Function to fetch logs, accepts filter kwargs.
    """
    
    # State for filters
    class FilterState:
        def __init__(self):
            self.search_text = ''
            self.endpoint = ''
            self.status_code = ''
            self.log_level = 'All Levels'
            
    state = FilterState()
    
    def refresh_logs(e=None):
        logs_container.refresh()

    @ui.refreshable
    def logs_container():
        # Fetch logs with current filters
        logs_data = fetch_logs_func(
            search_text=state.search_text,
            endpoint=state.endpoint,
            status_code=state.status_code,
            log_level=state.log_level
        )
        
        # Log entries
        with ui.column().classes('w-full gap-0'):
            if not logs_data:
                with ui.row().classes('w-full justify-center p-4'):
                    ui.label('No logs found matching criteria').classes('text-gray-500')
            
            for log in logs_data:
                log_entry_card(
                    timestamp=log.get('timestamp', ''),
                    log_type=log.get('type', 'INFO'),
                    details=log.get('details', ''),
                    method=log.get('method'),
                    endpoint=log.get('endpoint'),
                    status_code=log.get('status_code'),
                    duration=log.get('duration')
                )

    with ui.column().classes('w-full min-h-screen bg-gray-900 p-6 gap-6'):
        # Filter section
        with ui.column().classes('w-full max-w-7xl mx-auto gap-4'):
            # Filter inputs row
            with ui.row().classes('w-full gap-4 flex-wrap md:flex-nowrap'):
                # Search message
                with ui.column().classes('flex-1 min-w-[250px] gap-2'):
                    ui.label('Search Message').classes('text-sm text-gray-400 font-medium')
                    search_input('e.g., User authenticated').bind_value(state, 'search_text').on('change', refresh_logs)
                
                # Filter by endpoint
                with ui.column().classes('flex-1 min-w-[250px] gap-2'):
                    ui.label('Filter by Endpoint').classes('text-sm text-gray-400 font-medium')
                    search_input('e.g., /api/users').bind_value(state, 'endpoint').on('change', refresh_logs)
                    
                # Filter by response code
                with ui.column().classes('flex-1 min-w-[250px] gap-2'):
                    ui.label('Filter by Response code').classes('text-sm text-gray-400 font-medium')
                    search_input('e.g., 200, 2X0, 4XX').bind_value(state, 'status_code').on('change', refresh_logs)
                
                # Filter by log level
                with ui.column().classes('flex-1 gap-2'):
                    ui.label('Filter by Log Level').classes('text-sm text-gray-400 font-medium')
                    ui.select(
                        options=['All Levels', 'INFO', 'HTTP', 'WARN', 'ERROR', 'DEBUG'], 
                        value='All Levels'
                    ).classes('w-full').props('outlined dense dark').bind_value(state, 'log_level').on_value_change(refresh_logs)
                
            
        
        # Logs table section
        with ui.column().classes('w-full max-w-7xl mx-auto bg-gray-850 rounded-lg border border-gray-700 overflow-hidden gap-0'):
            # Table header
            with ui.row().classes('w-full border-b border-gray-700 px-4 py-3'):
                ui.label('TIMESTAMP').classes('text-gray-400 text-xs font-semibold uppercase min-w-[180px]')
                ui.label('TYPE').classes('text-gray-400 text-xs font-semibold uppercase min-w-[100px]')
                ui.label('DETAILS').classes('text-gray-400 text-xs font-semibold uppercase flex-1')
            
            # Log entries
            logs_container()
