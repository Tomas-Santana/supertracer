from nicegui import ui
from typing import Dict, List
from contextlib import contextmanager
from supertracer.types.metrics import MethodDistribution, StatusDistribution, TimelineData, PerformanceData

@contextmanager
def chart_card(title: str):
    with ui.card().classes('flex-1 min-w-[300px] bg-transparent rounded-lg border-gray-700 border p-4'):
        ui.label(title).classes('text-gray-400 text-lg mb-2')
        yield

def method_distribution_chart(data: MethodDistribution):
    """Pie chart for HTTP methods"""
    chart_data = [{'value': v, 'name': k} for k, v in data.items()]
    
    options = {
        'tooltip': {'trigger': 'item'},
        'legend': {'top': '5%', 'left': 'center', 'textStyle': {'color': '#ccc'}},
        'series': [
            {
                'name': 'HTTP Methods',
                'type': 'pie',
                'radius': ['40%', '70%'],
                'avoidLabelOverlap': False,
                'itemStyle': {
                    'borderRadius': 10,
                    'borderColor': '#1f2937',
                    'borderWidth': 2
                },
                'label': {'show': False, 'position': 'center'},
                'emphasis': {
                    'label': {'show': True, 'fontSize': 20, 'fontWeight': 'bold', 'color': '#fff'}
                },
                'labelLine': {'show': False},
                'data': chart_data
            }
        ],
        'backgroundColor': 'transparent',
    }
    return ui.echart(options).classes('h-64 w-full')

def status_distribution_chart(data: StatusDistribution):
    """Bar chart for Status Codes"""
    categories = list(data.keys())
    values = list(data.values())
    
    options = {
        'tooltip': {'trigger': 'axis', 'axisPointer': {'type': 'shadow'}},
        'grid': {'left': '3%', 'right': '4%', 'bottom': '3%', 'containLabel': True},
        'xAxis': [
            {
                'type': 'category',
                'data': categories,
                'axisTick': {'alignWithLabel': True},
                'axisLabel': {'color': '#ccc'}
            }
        ],
        'yAxis': [{'type': 'value', 'axisLabel': {'color': '#ccc'}, 'splitLine': {'lineStyle': {'color': '#374151'}}}],
        'series': [
            {
                'name': 'Count',
                'type': 'bar',
                'barWidth': '60%',
                'data': values,
                'itemStyle': {'color': '#60a5fa'}
            }
        ],
        'backgroundColor': 'transparent',
    }
    return ui.echart(options).classes('h-64 w-full')

def timeline_chart(data: TimelineData):
    """Line chart for Requests over time"""
    options = {
        'tooltip': {'trigger': 'axis'},
        'grid': {'left': '3%', 'right': '4%', 'bottom': '3%', 'containLabel': True},
        'xAxis': {
            'type': 'category',
            'boundaryGap': False,
            'data': data.get('times', []),
            'axisLabel': {'color': '#ccc'}
        },
        'yAxis': {
            'type': 'value',
            'axisLabel': {'color': '#ccc'},
            'splitLine': {'lineStyle': {'color': '#374151'}}
        },
        'series': [
            {
                'name': 'Requests',
                'type': 'line',
                'smooth': True,
                'areaStyle': {'opacity': 0.3, 'color': '#818cf8'},
                'itemStyle': {'color': '#6366f1'},
                'data': data.get('counts', [])
            }
        ],
        'backgroundColor': 'transparent',
    }
    return ui.echart(options).classes('h-64 w-full')

def performance_chart(data: PerformanceData):
    """Line chart for Latency over time"""
    options = {
        'tooltip': {'trigger': 'axis'},
        'grid': {'left': '3%', 'right': '4%', 'bottom': '3%', 'containLabel': True},
        'xAxis': {
            'type': 'category',
            'boundaryGap': False,
            'data': data.get('times', []),
            'axisLabel': {'color': '#ccc'}
        },
        'yAxis': {
            'type': 'value',
            'name': 'ms',
            'nameTextStyle': {'color': '#ccc'},
            'axisLabel': {'color': '#ccc'},
            'splitLine': {'lineStyle': {'color': '#374151'}}
        },
        'series': [
            {
                'name': 'Avg Latency',
                'type': 'line',
                'smooth': True,
                'itemStyle': {'color': '#34d399'},
                'data': data.get('latencies', [])
            }
        ],
        'backgroundColor': 'transparent',
    }
    return ui.echart(options).classes('h-64 w-full')