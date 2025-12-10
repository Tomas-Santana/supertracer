from nicegui import ui
from typing import List, Dict, Any
from urllib.parse import urlparse
from supertracer.ui.components.search_input import search_input
from supertracer.ui.components.filter_dropdown import filter_dropdown
from supertracer.ui.components.log_entry_card import log_entry_card
from supertracer.ui.components.dashboard.dashboard import Dashboard
from supertracer.metrics import MetricsService
from supertracer.broadcaster import LogBroadcaster
from supertracer.types.logs import Log

def format_log_entry(log: Log) -> Dict[str, Any]:
    endpoint = None
    if log.get('url'):
        parsed = urlparse(log.get('url'))
        endpoint = parsed.path or '/'
    
    return {
        'id': log.get('id'),
        'timestamp': log['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
        'type': log.get('log_level') or ('HTTP' if log.get('method') else None),
        'details': log['content'],
        'method': log.get('method'),
        'endpoint': endpoint,
        'status_code': log.get('status_code') or 200,
        'duration': f"{log.get('duration_ms')}ms"
    }

def render_logs_page(logs_data: List[Dict[str, Any]], metrics_service: MetricsService, broadcaster: LogBroadcaster):
    """Renders the logs page with filters and log entries.
    
    Args:
        logs_data: List of log dictionaries with keys: timestamp, type, details, 
                   method (optional), endpoint (optional), status_code (optional), duration (optional)
        metrics_service: Service to provide metrics data
        broadcaster: Service to subscribe to new logs
    """
    
    # Buffer for incoming logs
    new_logs_buffer: List[Log] = []

    def handle_new_log(log: Log):
        new_logs_buffer.append(log)

    # Subscribe to broadcaster
    broadcaster.subscribe(handle_new_log)
    
    # Unsubscribe when client disconnects
    ui.context.client.on_disconnect(lambda: broadcaster.unsubscribe(handle_new_log))

    with ui.column().classes('w-full min-h-screen bg-gray-900 p-6 gap-6'):
        # Dashboard Section
        with ui.column().classes('w-full max-w-7xl mx-auto gap-4'):
            Dashboard(metrics_service)

        # Filter section
        with ui.column().classes('w-full max-w-7xl mx-auto gap-4'):
            # Filter inputs row
            with ui.row().classes('w-full gap-4 flex-wrap md:flex-nowrap'):
                # Search message
                with ui.column().classes('flex-1 min-w-[250px] gap-2'):
                    ui.label('Search Message').classes('text-sm text-gray-400 font-medium')
                    search_input('e.g., User authenticated')
                
                # Filter by endpoint
                with ui.column().classes('flex-1 min-w-[250px] gap-2'):
                    ui.label('Filter by Endpoint').classes('text-sm text-gray-400 font-medium')
                    search_input('e.g., /api/users')
                    
                    # Filter by endpoint
                with ui.column().classes('flex-1 min-w-[250px] gap-2'):
                    ui.label('Filter by Response code').classes('text-sm text-gray-400 font-medium')
                    search_input('e.g., 200, 2X0, 4XX')
                
                # Filter by log level
                filter_dropdown(
                    'Filter by Log Level',
                    ['All Levels', 'INFO', 'HTTP', 'WARN', 'ERROR', 'DEBUG']
                )
                
            
        
        # Logs table section
        with ui.column().classes('w-full max-w-7xl mx-auto bg-gray-850 rounded-lg border border-gray-700 overflow-hidden gap-0'):
            # Table header
            with ui.row().classes('w-full border-b border-gray-700 px-4 py-3'):
                ui.label('TIMESTAMP').classes('text-gray-400 text-xs font-semibold uppercase min-w-[180px]')
                ui.label('TYPE').classes('text-gray-400 text-xs font-semibold uppercase min-w-[100px]')
                ui.label('DETAILS').classes('text-gray-400 text-xs font-semibold uppercase flex-1')
            
            # Log entries
            logs_container = ui.column().classes('w-full gap-0')
            with logs_container:
                if not logs_data:
                    ui.label('No logs available').classes('p-4 text-gray-500 text-sm')
                for log in logs_data:
                    log_entry_card(
                        timestamp=log.get('timestamp', ''),
                        log_type=log.get('type', 'INFO'),
                        details=log.get('details', ''),
                        log_id=log.get('id'),
                        method=log.get('method'),
                        endpoint=log.get('endpoint'),
                        status_code=log.get('status_code'),
                        duration=log.get('duration')
                    )

    def flush_logs():
        if not new_logs_buffer:
            return
        
        # Process buffer
        logs_to_add = list(new_logs_buffer)
        new_logs_buffer.clear()
        
        # Add new logs to the top
        with logs_container:
            for log in reversed(logs_to_add):
                formatted = format_log_entry(log)
                card = log_entry_card(
                    timestamp=formatted.get('timestamp', ''),
                    log_type=formatted.get('type', 'INFO'),
                    details=formatted.get('details', ''),
                    log_id=formatted.get('id'),
                    method=formatted.get('method'),
                    endpoint=formatted.get('endpoint'),
                    status_code=formatted.get('status_code'),
                    duration=formatted.get('duration')
                )
                card.move(target_index=0)
                
        if len(logs_container.default_slot.children) > 200:
            # This is a bit hacky in NiceGUI to remove from end, but for now let's just keep it simple
            # or we can clear and re-render if it gets too big, but that defeats the purpose.
            # Ideally we remove the last child.
            # logs_container.remove(logs_container.default_slot.children[-1])
            pass

    # Timer to flush logs every 500ms
    ui.timer(0.5, flush_logs)
