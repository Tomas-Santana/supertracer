from nicegui import ui
from typing import List, Dict, Any, Callable
from datetime import datetime
from supertracer.ui.components.search_input import search_input
from supertracer.ui.components.log_entry_card import log_entry_card
from supertracer.ui.components.dashboard.dashboard import Dashboard
from supertracer.metrics import MetricsService


def render_logs_page(fetch_logs_func: Callable, metrics_service: MetricsService):
    """Renders the logs page with filters and log entries.
    
    Args:
        fetch_logs_func: Function to fetch logs, accepts filter kwargs.
        metrics_service: Service to provide metrics data
    """
    
    # State for filters
    class FilterState:
        def __init__(self):
            self.search_text = ''
            self.endpoint = ''
            self.status_code = ''
            self.log_level = 'All Levels'
            self.methods = []
            self.min_latency = None
            self.max_latency = None
            self.has_error = False
            self.start_date = None
            self.end_date = None
            
    state = FilterState()
    
    def refresh_logs(e=None):
        logs_container.refresh()

    @ui.refreshable
    def logs_container():
        # Parse dates if present
        start_dt = None
        end_dt = None
        
        if state.start_date:
            try:
                # Handle potential slash format from ui.date
                clean_start = state.start_date.replace('/', '-')
                start_dt = datetime.strptime(clean_start, '%Y-%m-%d')
            except ValueError:
                pass
                
        if state.end_date:
            try:
                # Handle potential slash format from ui.date
                clean_end = state.end_date.replace('/', '-')
                # Set end date to end of day
                end_dt = datetime.strptime(clean_end, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            except ValueError:
                pass

        # Fetch logs with current filters
        logs_data = fetch_logs_func(
            search_text=state.search_text,
            endpoint=state.endpoint,
            status_code=state.status_code,
            log_level=state.log_level,
            methods=state.methods,
            min_latency=int(state.min_latency) if state.min_latency else None,
            max_latency=int(state.max_latency) if state.max_latency else None,
            has_error=state.has_error,
            start_date=start_dt,
            end_date=end_dt
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
        # Dashboard Section
        with ui.column().classes('w-full max-w-7xl mx-auto gap-4'):
            Dashboard(metrics_service)

        # Filter section
        with ui.column().classes('w-full max-w-7xl mx-auto gap-4'):
            # Filter inputs row
            with ui.row().classes('w-full gap-4 flex-wrap md:flex-nowrap'):
                # Search message
                with ui.column().classes('flex-1 min-w-[200px] gap-2'):
                    ui.label('Search Message').classes('text-sm text-gray-400 font-medium')
                    search_input('e.g., User authenticated').bind_value(state, 'search_text').on('change', refresh_logs)
                
                # Filter by endpoint
                with ui.column().classes('flex-1 min-w-[200px] gap-2'):
                    ui.label('Filter by Endpoint').classes('text-sm text-gray-400 font-medium')
                    search_input('e.g., /api/users').bind_value(state, 'endpoint').on('change', refresh_logs)
                    
                # Filter by response code
                with ui.column().classes('flex-1 min-w-[150px] gap-2'):
                    ui.label('Response code').classes('text-sm text-gray-400 font-medium')
                    search_input('e.g., 200, 2X0').bind_value(state, 'status_code').on('change', refresh_logs)
                
                # Filter by log level
                with ui.column().classes('flex-1 min-w-[150px] gap-2'):
                    ui.label('Log Level').classes('text-sm text-gray-400 font-medium')
                    ui.select(
                        options=['All Levels', 'INFO', 'HTTP', 'WARN', 'ERROR', 'DEBUG'], 
                        value='All Levels'
                    ).classes('w-full').props('outlined dense dark').bind_value(state, 'log_level').on_value_change(refresh_logs)

                # Filter by HTTP Method
                with ui.column().classes('flex-1 min-w-[150px] gap-2'):
                    ui.label('HTTP Method').classes('text-sm text-gray-400 font-medium')
                    ui.select(
                        options=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'],
                        multiple=True
                    ).classes('w-full').props('outlined dense dark use-chips').bind_value(state, 'methods').on_value_change(refresh_logs)

            # Latency filters row
            with ui.row().classes('w-full gap-4 flex-wrap md:flex-nowrap'):
                with ui.column().classes('flex-1 min-w-[200px] gap-2'):
                    ui.label('Min Latency (ms)').classes('text-sm text-gray-400 font-medium')
                    ui.number().classes('w-full').props('outlined dense dark').bind_value(state, 'min_latency').on('change', refresh_logs)

                with ui.column().classes('flex-1 min-w-[200px] gap-2'):
                    ui.label('Max Latency (ms)').classes('text-sm text-gray-400 font-medium')
                    ui.number().classes('w-full').props('outlined dense dark').bind_value(state, 'max_latency').on('change', refresh_logs)
                
                # Has Error toggle
                with ui.column().classes('flex-1 min-w-[150px] gap-2 justify-end pb-2'):
                    ui.checkbox('Has Error').classes('text-gray-400').bind_value(state, 'has_error').on('change', refresh_logs)
                
                # Spacer to align with top row if needed
                with ui.column().classes('flex-[1]'):
                    pass

            # Date filters row
            with ui.row().classes('w-full gap-4 flex-wrap md:flex-nowrap'):
                with ui.column().classes('flex-1 min-w-[200px] gap-2'):
                    ui.label('From Date').classes('text-sm text-gray-400 font-medium')
                    ui.input('YYYY-MM-DD').classes('w-full').props('outlined dense dark').bind_value(state, 'start_date').on('change', refresh_logs)

                with ui.column().classes('flex-1 min-w-[200px] gap-2'):
                    ui.label('To Date').classes('text-sm text-gray-400 font-medium')
                    ui.input('YYYY-MM-DD').classes('w-full').props('outlined dense dark').bind_value(state, 'end_date').on('change', refresh_logs)
                
                # Spacer to align with top row if needed
                with ui.column().classes('flex-[2]'):
                    pass
            
        
        # Logs table section
        with ui.column().classes('w-full max-w-7xl mx-auto bg-gray-850 rounded-lg border border-gray-700 overflow-hidden gap-0'):
            # Table header
            with ui.row().classes('w-full border-b border-gray-700 px-4 py-3'):
                ui.label('TIMESTAMP').classes('text-gray-400 text-xs font-semibold uppercase min-w-[180px]')
                ui.label('TYPE').classes('text-gray-400 text-xs font-semibold uppercase min-w-[100px]')
                ui.label('DETAILS').classes('text-gray-400 text-xs font-semibold uppercase flex-1')
            
            # Log entries
            logs_container()
