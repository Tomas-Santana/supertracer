from nicegui import ui
from typing import List, Dict, Any
from supertracer.types.logs import Log
from supertracer.ui.components.log_entry_card import log_entry_card
from urllib.parse import urlparse

class LogsTable:
    def __init__(self):
        self.container = None
        self.list_container = None

    def build(self):
        with ui.column().classes('w-full max-w-7xl mx-auto bg-gray-900 rounded-lg border border-gray-700 overflow-hidden gap-0') as self.container:
            # Table header
            with ui.row().classes('w-full border-b border-gray-700 px-4 py-3 bg-gray-800/50'):
                ui.label('TIMESTAMP').classes('text-gray-400 text-xs font-semibold uppercase min-w-[180px]')
                ui.label('TYPE').classes('text-gray-400 text-xs font-semibold uppercase min-w-[100px]')
                ui.label('DETAILS').classes('text-gray-400 text-xs font-semibold uppercase flex-1')
            
            # List container
            self.list_container = ui.column().classes('w-full gap-0')

    def set_logs(self, logs: List[Log]):
        if self.list_container is None: return
        
        self.list_container.clear()
        with self.list_container:
            if not logs:
                with ui.row().classes('w-full justify-center p-8'):
                    ui.label('No logs found matching criteria').classes('text-gray-500 italic')
                return

            for log in logs:
                self._render_log_row(log)

    def prepend_logs(self, logs: List[Log]):
        if self.list_container is None: return
        
        with self.list_container:
            for log in reversed(logs):
                card = self._render_log_row(log)
                card.move(target_index=0)
        
        # Optional: Limit size to prevent DOM explosion
        # if len(self.list_container.default_slot.children) > 200:
        #     pass

    def _render_log_row(self, log: Log):
        formatted = self._format_log_entry(log)
        return log_entry_card(
            timestamp=formatted.get('timestamp', ''),
            log_type=formatted.get('type', 'INFO'),
            details=formatted.get('details', ''),
            log_id=formatted.get('id'),
            method=formatted.get('method'),
            endpoint=formatted.get('endpoint'),
            status_code=formatted.get('status_code'),
            duration=formatted.get('duration')
        )

    def _format_log_entry(self, log: Log) -> Dict[str, Any]:
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
