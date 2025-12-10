from nicegui import ui
from supertracer.metrics import MetricsService
from supertracer.ui.components.dashboard.summary_cards import summary_card
from supertracer.ui.components.dashboard.charts import (
    method_distribution_chart, 
    status_distribution_chart, 
    timeline_chart, 
    performance_chart,
    chart_card
)
from supertracer.ui.components.dashboard.tables import (
    top_endpoints_table, 
    slow_endpoints_table, 
    recent_errors_list
)

class Dashboard:
    def __init__(self, metrics_service: MetricsService, refresh_interval: float = 1.0):
        self.metrics = metrics_service
        self.refresh_interval = refresh_interval
        self.build()
        
    def build(self):
        with ui.column().classes('w-full gap-6'):
            # 1. Summary Cards Row
            self.cards_container = ui.row().classes('w-full gap-4 flex-wrap md:flex-nowrap')
            with self.cards_container:
                self.lbl_requests = summary_card('Total Requests', '0', 'dns', '#6366f1') # Indigo
                self.lbl_rate = summary_card('Req / Min', '0', 'speed', '#34d399') # Emerald
                self.lbl_errors = summary_card('Errors', '0', 'warning', '#ef4444') # Red
                self.lbl_uptime = summary_card('Uptime', '00:00:00', 'schedule', '#f59e0b') # Amber

            # 2. Charts Row 1 (Distributions)
            with ui.row().classes('w-full gap-4 flex-wrap md:flex-nowrap'):
                with chart_card('Method Distribution'):
                    self.chart_method = method_distribution_chart({})
                
                with chart_card('Status Distribution'):
                    self.chart_status = status_distribution_chart({})

            # 3. Charts Row 2 (Timeline & Performance)
            with ui.row().classes('w-full gap-4 flex-wrap md:flex-nowrap'):
                with chart_card('Requests Timeline'):
                    self.chart_timeline = timeline_chart({})
                
                with chart_card('Latency Performance'):
                    self.chart_perf = performance_chart({})

            # 4. Tables Row
            with ui.row().classes('w-full gap-4 flex-wrap md:flex-nowrap'):
                with ui.column().classes('flex-1 min-w-[250px]'):
                    self.table_top = ui.element('div').classes('w-full')
                
                with ui.column().classes('flex-1 min-w-[250px]'):
                    self.table_slow = ui.element('div').classes('w-full')
                
                with ui.column().classes('flex-1 min-w-[250px]'):
                    self.list_errors = ui.element('div').classes('w-full')

            # Start auto-refresh timer
            self.timer = ui.timer(self.refresh_interval, self.refresh)

    def refresh(self):
        # Update Summary Cards
        stats = self.metrics.get_summary_stats()
        self.lbl_requests.text = str(stats['total_requests'])
        self.lbl_rate.text = str(stats['requests_per_min'])
        self.lbl_errors.text = str(stats['total_errors'])
        self.lbl_uptime.text = str(stats['uptime'])
        
        # Update Charts
        self.chart_method.options['series'][0]['data'] = [{'value': v, 'name': k} for k, v in self.metrics.get_method_distribution().items()]
        self.chart_method.update()

        status_data = self.metrics.get_status_distribution()
        self.chart_status.options['xAxis'][0]['data'] = list(status_data.keys())
        self.chart_status.options['series'][0]['data'] = list(status_data.values())
        self.chart_status.update()

        timeline_data = self.metrics.get_timeline_data()
        self.chart_timeline.options['xAxis']['data'] = timeline_data.get('times', [])
        self.chart_timeline.options['series'][0]['data'] = timeline_data.get('counts', [])
        # Errors per minute series
        if len(self.chart_timeline.options['series']) > 1:
            self.chart_timeline.options['series'][1]['data'] = timeline_data.get('error_counts', [])
        self.chart_timeline.update()

        perf_data = self.metrics.get_performance_data()
        self.chart_perf.options['xAxis']['data'] = perf_data.get('times', [])
        self.chart_perf.options['series'][0]['data'] = perf_data.get('latencies', [])
        self.chart_perf.update()

        # Update Tables (Re-render content)
        self.table_top.clear()
        with self.table_top:
            top_endpoints_table(self.metrics.get_top_endpoints())
            
        self.table_slow.clear()
        with self.table_slow:
            slow_endpoints_table(self.metrics.get_slow_endpoints())
            
        self.list_errors.clear()
        with self.list_errors:
            recent_errors_list(self.metrics.get_recent_errors())

    def update_cards(self, stats):
        pass
