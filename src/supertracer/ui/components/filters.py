from nicegui import ui
from typing import Callable, List, Optional
from datetime import datetime
from supertracer.ui.components.search_input import search_input

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
        self.start_time = None
        self.end_time = None

def date_picker_input(label: str, bind_target: object, bind_property: str, on_change: Callable):
    with ui.date_input().props('outlined dense dark').classes('w-full').bind_value(bind_target, bind_property).on_value_change(on_change) as date:
        date.label = label
    return date
  
def time_picker_input(label: str, bind_target: object, bind_property: str, on_change: Callable):
    with ui.time_input().props('outlined dense dark').classes('w-full').bind_value(bind_target, bind_property).on_value_change(on_change) as time:
        time.label = label
    return time

def log_filters(state: FilterState, on_change: Callable):
    with ui.card().classes('w-full p-4 bg-gray-900 border border-gray-700 rounded-lg gap-4'):
        # Primary Filters
        with ui.row().classes('w-full gap-4 flex-wrap md:flex-nowrap items-center'):
            # Search
            with ui.column().classes('flex-[2] min-w-[200px] gap-1'):
                ui.label('Search Message').classes('text-xs text-gray-400 font-medium')
                search_input('e.g., User authenticated').bind_value(state, 'search_text').on('change', on_change).classes('w-full')
            
            # Log Level
            with ui.column().classes('flex-1 min-w-[150px] gap-1'):
                ui.label('Log Level').classes('text-xs text-gray-400 font-medium')
                ui.select(
                    options=['All Levels', 'INFO', 'HTTP', 'WARN', 'ERROR', 'DEBUG'], 
                    value='All Levels'
                ).classes('w-full').props('outlined dense dark').bind_value(state, 'log_level').on_value_change(on_change)

            # Status Code
            with ui.column().classes('flex-1 min-w-[150px] gap-1'):
                ui.label('Response Code').classes('text-xs text-gray-400 font-medium')
                search_input('e.g., 200, 2X0').bind_value(state, 'status_code').on('change', on_change).classes('w-full')

        # Advanced Filters (Expandable)
        with ui.expansion('Advanced Filters', icon='tune').classes('w-full text-gray-400 bg-gray-800/50 rounded-md'):
            with ui.column().classes('w-full gap-4 p-4'):
                # Row 1: Endpoint & Methods
                with ui.row().classes('w-full gap-4 flex-wrap md:flex-nowrap'):
                    with ui.column().classes('flex-[2] min-w-[200px] gap-1'):
                        ui.label('Endpoint').classes('text-xs text-gray-400 font-medium')
                        search_input('e.g., /api/users').bind_value(state, 'endpoint').on('change', on_change).classes('w-full')
                    
                    with ui.column().classes('flex-1 min-w-[200px] gap-1'):
                        ui.label('HTTP Methods').classes('text-xs text-gray-400 font-medium')
                        ui.select(
                            options=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'],
                            multiple=True
                        ).classes('w-full').props('outlined dense dark use-chips').bind_value(state, 'methods').on_value_change(on_change)

                # Row 2: Latency & Errors
                with ui.row().classes('w-full gap-4 flex-wrap md:flex-nowrap'):
                    with ui.column().classes('flex-1 min-w-[150px] gap-1'):
                        ui.label('Min Latency (ms)').classes('text-xs text-gray-400 font-medium')
                        ui.number().classes('w-full').props('outlined dense dark').bind_value(state, 'min_latency').on('change', on_change)

                    with ui.column().classes('flex-1 min-w-[150px] gap-1'):
                        ui.label('Max Latency (ms)').classes('text-xs text-gray-400 font-medium')
                        ui.number().classes('w-full').props('outlined dense dark').bind_value(state, 'max_latency').on('change', on_change)
                    
                    with ui.column().classes('flex-1 min-w-[150px] gap-1 justify-end pb-2'):
                        ui.checkbox('Has Error Only').classes('text-gray-400').bind_value(state, 'has_error').on('change', on_change)

                # Row 3: Dates
                with ui.row().classes('w-full gap-4 flex-wrap md:flex-nowrap'):
                    with ui.column().classes('flex-1 min-w-[200px] gap-1'):
                        ui.label('From').classes('text-xs text-gray-400 font-medium')
                        with ui.row().classes('w-full gap-2'):
                            with ui.column().classes('flex-[2]'):
                                date_picker_input('Date', state, 'start_date', on_change)
                            with ui.column().classes('flex-1'):
                                time_picker_input('Time', state, 'start_time', on_change)

                    with ui.column().classes('flex-1 min-w-[200px] gap-1'):
                        ui.label('To').classes('text-xs text-gray-400 font-medium')
                        with ui.row().classes('w-full gap-2'):
                            with ui.column().classes('flex-[2]'):
                                date_picker_input('Date', state, 'end_date', on_change)
                            with ui.column().classes('flex-1'):
                                time_picker_input('Time', state, 'end_time', on_change)