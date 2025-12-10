from nicegui import ui
from typing import List
from supertracer.types.metrics import EndpointCount, EndpointLatency, MetricRecord

def top_endpoints_table(data: List[EndpointCount]):
    with ui.card().classes('w-full bg-transparent p-0 border border-gray-700 rounded-lg'):
        ui.label('Top Endpoints').classes('text-gray-400 text-xs font-bold uppercase p-3 border-b border-gray-700')
        with ui.column().classes('w-full gap-0'):
            if not data:
                ui.label('No data').classes('p-3 text-gray-500 text-sm')
            for item in data:
                with ui.row().classes('w-full justify-between p-2 border-b border-gray-700/50 hover:bg-gray-700/50'):
                    ui.label(item['path']).classes('text-gray-300 text-sm truncate flex-1')
                    ui.label(str(item['count'])).classes('text-blue-400 text-sm font-mono')

def slow_endpoints_table(data: List[EndpointLatency]):
    with ui.card().classes('w-full bg-transparent p-0 border border-gray-700 rounded-lg'):
        ui.label('Slowest Endpoints (Avg)').classes('text-gray-400 text-xs font-bold uppercase p-3 border-b border-gray-700')
        with ui.column().classes('w-full gap-0'):
            if not data:
                ui.label('No data').classes('p-3 text-gray-500 text-sm')
            for item in data:
                with ui.row().classes('w-full justify-between p-2 border-b border-gray-700/50 hover:bg-gray-700/50'):
                    ui.label(item['path']).classes('text-gray-300 text-sm truncate flex-1')
                    ui.label(f"{item['avg_latency']}ms").classes('text-orange-400 text-sm font-mono')

def recent_errors_list(data: List[MetricRecord]):
    with ui.card().classes('w-full bg-transparent p-0 border border-gray-700 rounded-lg'):
        ui.label('Last 5 Errors').classes('text-gray-400 text-xs font-bold uppercase p-3 border-b border-gray-700')
        with ui.column().classes('w-full gap-0'):
            if not data:
                ui.label('No errors').classes('p-3 text-gray-500 text-sm')
            for item in data:
                with ui.row().classes('w-full items-center gap-2 p-2 border-b border-gray-700/50 hover:bg-gray-700/50 cursor-pointer').on('click', lambda log_id=item['id']: ui.navigate.to(f'/logs/{log_id}')):
                    # click to navigate to log detail
                    
                    ui.label(str(item['status_code'])).classes('text-red-500 font-bold text-xs min-w-[30px]')
                    with ui.column().classes('flex-1 gap-0 overflow-hidden'):
                        ui.label(f"{item['method']} {item['path']}").classes('text-gray-300 text-xs font-mono truncate w-full')
                        ui.label(item['timestamp'].strftime('%H:%M:%S')).classes('text-gray-500 text-[10px]')
