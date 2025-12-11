from nicegui import ui
from typing import List, Dict, Any
from datetime import datetime
from supertracer.types.filters import LogFilters
from supertracer.ui.components.dashboard.dashboard import Dashboard
from supertracer.ui.components.filters import FilterState, log_filters
from supertracer.ui.components.logs_table import LogsTable
from supertracer.ui.components.header import page_header
from supertracer.services.metrics import MetricsService
from supertracer.services.broadcaster import LogBroadcaster
from supertracer.connectors.base import BaseConnector
from supertracer.services.auth import AuthService
from supertracer.types.logs import Log
from supertracer.ui.utils.logs_page import match_log_filters, format_log_entry




def render_logs_page(connector: BaseConnector, metrics_service: MetricsService, broadcaster: LogBroadcaster, auth_service: AuthService, page_size: int = 20):
    """Renders the logs page with filters and log entries."""
    
    new_logs_buffer: List[Log] = []

    def handle_new_log(log: Log):
        if match_log_filters(log, LogFilters(
            search_text=state.search_text,
            endpoint=state.endpoint,
            status_code=state.status_code,
            log_level=state.log_level,
            methods=state.methods,
            min_latency=int(state.min_latency) if state.min_latency else None,
            max_latency=int(state.max_latency) if state.max_latency else None,
            has_error=state.has_error,
            start_date=None,
            end_date=None
        )):
            new_logs_buffer.append(log)

    # Subscribe to broadcaster
    broadcaster.subscribe(handle_new_log)
    
    # Unsubscribe when client disconnects
    ui.context.client.on_disconnect(lambda: broadcaster.unsubscribe(handle_new_log))
    
    # State for filters
    state = FilterState()
    logs_table = LogsTable()
    
    # Pagination state
    pagination = {'limit': page_size}
    pagination_container = None
    last_log_timestamp: Dict[str, datetime | None] = {'value': None}

    def refresh_logs(e=None):
        # Parse dates if present
        start_dt = None
        end_dt = None
        
        if state.start_date:
            try:
                clean_start = state.start_date.replace('/', '-')
                if state.start_time:
                    start_dt = datetime.strptime(f"{clean_start} {state.start_time}", '%Y-%m-%d %H:%M')
                else:
                    start_dt = datetime.strptime(clean_start, '%Y-%m-%d')
            except ValueError:
                pass
                
        if state.end_date:
            try:
                clean_end = state.end_date.replace('/', '-')
                if state.end_time:
                    end_dt = datetime.strptime(f"{clean_end} {state.end_time}", '%Y-%m-%d %H:%M')
                else:
                    # Set end date to end of day if no time specified
                    end_dt = datetime.strptime(clean_end, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
            except ValueError:
                pass

        # Fetch logs with current filters
        filters = LogFilters(
            search_text=state.search_text,
            endpoint=state.endpoint,
            status_code=state.status_code,
            log_level=state.log_level,
            methods=state.methods,
            min_latency=int(state.min_latency) if state.min_latency else None,
            max_latency=int(state.max_latency) if state.max_latency else None,
            has_error=state.has_error,
            start_date=start_dt,
            end_date=end_dt,
            limit=pagination['limit']
        )
        
        logs_data: List[Log] = connector.fetch_logs(filters=filters)
        
        logs_table.set_logs(logs_data)
        
        if logs_data:
            last_log_timestamp['value'] = logs_data[-1]['timestamp']
        else:
            last_log_timestamp['value'] = None
            
        if pagination_container:
            pagination_container.clear()
            if len(logs_data) >= pagination['limit']:
                with pagination_container:
                    ui.button('Load More', on_click=load_more_logs).classes('w-full bg-gray-800 text-gray-400 hover:bg-gray-700')

    def load_more_logs():
        if not last_log_timestamp['value']:
            return
            
        if pagination_container:
            pagination_container.clear()

        # Parse dates (same as refresh_logs)
        start_dt = None
        # Use the last timestamp as the end date for pagination
        end_dt = last_log_timestamp['value']
        
        if state.start_date:
            try:
                clean_start = state.start_date.replace('/', '-')
                if state.start_time:
                    start_dt = datetime.strptime(f"{clean_start} {state.start_time}", '%Y-%m-%d %H:%M')
                else:
                    start_dt = datetime.strptime(clean_start, '%Y-%m-%d')
            except ValueError: pass

        filters = LogFilters(
            search_text=state.search_text,
            endpoint=state.endpoint,
            status_code=state.status_code,
            log_level=state.log_level,
            methods=state.methods,
            min_latency=int(state.min_latency) if state.min_latency else None,
            max_latency=int(state.max_latency) if state.max_latency else None,
            has_error=state.has_error,
            start_date=start_dt,
            end_date=end_dt,
            limit=pagination['limit']
        )

        logs_data: List[Log] = connector.fetch_logs(filters=filters)
        
        if logs_data:
            logs_table.append_logs(logs_data)
            last_log_timestamp['value'] = logs_data[-1]['timestamp']
            
            if pagination_container and len(logs_data) >= pagination['limit']:
                with pagination_container:
                    ui.button('Load More', on_click=load_more_logs).classes('w-full bg-gray-800 text-gray-400 hover:bg-gray-700')


    def flush_logs():
        if not new_logs_buffer:
            return
        
        # Process buffer
        logs_to_add = list(new_logs_buffer)
        new_logs_buffer.clear()
        
        # Add new logs to the top
        logs_table.prepend_logs(logs_to_add)

    with ui.column().classes('w-full min-h-screen bg-gray-900 p-6 gap-6'):
        # Header
        page_header('SuperTracer Logs', auth_service)

        # Dashboard Section
        with ui.column().classes('w-full max-w-7xl mx-auto gap-4'):
            Dashboard(metrics_service)

        # Filter section
        with ui.column().classes('w-full max-w-7xl mx-auto gap-4'):
            log_filters(state, refresh_logs)
        
        # Logs table section
        logs_table.build()
        
        pagination_container = ui.row().classes('w-full max-w-7xl mx-auto justify-center pb-6')
        
        # Initial load
        refresh_logs()

    # Timer to flush logs every 500ms
    ui.timer(0.5, flush_logs)
