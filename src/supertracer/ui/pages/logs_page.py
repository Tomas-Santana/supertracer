from nicegui import ui
from typing import List, Dict, Any
from supertracer.ui.components.search_input import search_input
from supertracer.ui.components.filter_dropdown import filter_dropdown
from supertracer.ui.components.log_entry_card import log_entry_card


def render_logs_page(logs_data: List[Dict[str, Any]]):
    """Renders the logs page with filters and log entries.
    
    Args:
        logs_data: List of log dictionaries with keys: timestamp, type, details, 
                   method (optional), endpoint (optional), status_code (optional), duration (optional)
    """
    
    with ui.column().classes('w-full min-h-screen bg-gray-900 p-6 gap-6'):
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
            with ui.column().classes('w-full gap-0'):
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
