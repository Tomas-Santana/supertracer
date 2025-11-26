import sqlite3
import time
import json
import os
from typing import Callable
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from nicegui import ui


class SuperTracer:
    def __init__(self, app: FastAPI, db_path: str = "requests.db", use_nicegui: bool = True):
        self.app = app
        self.db_path = db_path
        self.use_nicegui = use_nicegui
        self._init_db()
        self._add_middleware()
        self._add_routes()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                method TEXT,
                url TEXT,
                headers TEXT,
                timestamp REAL
            )
        """)
        conn.commit()
        conn.close()

    def _add_middleware(self):
        @self.app.middleware("http")
        async def log_requests(request: Request, call_next: Callable):
            # Capture request details
            method = request.method
            url = str(request.url)
            # Convert headers to a serializable format
            headers = json.dumps(dict(request.headers))
            timestamp = time.time()

            # Save to DB (synchronously for simplicity in this example, 
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO requests (method, url, headers, timestamp) VALUES (?, ?, ?, ?)",
                    (method, url, headers, timestamp)
                )
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"SuperTracer Error: {e}")

            response = await call_next(request)
            return response

    def _add_routes(self):
        if self.use_nicegui:
            self._add_nicegui_logs()
        else:
            self._add_html_logs()

    def _fetch_logs(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, method, url, timestamp, headers FROM requests ORDER BY id DESC LIMIT 100")
        rows = cursor.fetchall()
        conn.close()
        return rows

    def _add_html_logs(self):
        @self.app.get("/logs", response_class=HTMLResponse)
        def get_logs():
            rows = self._fetch_logs()

            logs_html = ""
            for row in rows:
                # row: id, method, url, timestamp, headers
                ts_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(row[3]))
                logs_html += f"""
                <div class="log-entry">
                    <div class="log-header">
                        <span class="method {row[1].lower()}">{row[1]}</span>
                        <span class="url">{row[2]}</span>
                        <span class="time">{ts_str}</span>
                    </div>
                    <div class="log-details">
                        <details>
                            <summary>Headers</summary>
                            <pre>{row[4]}</pre>
                        </details>
                    </div>
                </div>
                """

            template_path = os.path.join(os.path.dirname(__file__), "templates", "logs.html")
            with open(template_path, "r", encoding="utf-8") as f:
                html_content = f.read()

            return html_content.replace("{{ logs_list }}", logs_html)

    def _add_nicegui_logs(self):

        method_filter = ui.toggle(['ALL', 'GET', 'POST', 'PUT', 'DELETE'], value='ALL')

        # basic CSS to mimic the existing HTML template styling
        ui.add_css("""
        .method-chip {
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 999px;
            color: white;
            min-width: 60px;
            text-align: center;
            font-size: 0.75rem;
        }
        .method-get { background-color: #61affe; }
        .method-post { background-color: #49cc90; }
        .method-put { background-color: #fca130; }
        .method-delete { background-color: #f93e3e; }
        """)

        @ui.page('/logs')
        def logs_page():
            # basic css styling
            ui.query('body').style('background-color: #f4f4f9;')
            with ui.column().classes('w-full max-w-5xl mx-auto py-6 gap-4'):
                with ui.row().classes('items-center justify-between w-full'):
                    ui.label('SuperTracer Logs').classes('text-2xl font-semibold text-gray-800')
                    ui.button('Refresh', on_click=lambda: ui.run_javascript('location.reload()').props('color=primary unelevated'))

            rows = self._fetch_logs()
            for row in rows:
                # row: id, method, url, timestamp, headers
                ts_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(row[3]))
                method = row[1]
                url = row[2]
                headers = row[4]

                if method_filter.value != 'ALL' and method != method_filter.value:
                    continue

                with ui.card().classes('w-full shadow-sm border border-gray-200'):
                    with ui.row().classes('items-center justify-between w-full'):
                        ui.label(method).classes(f'method-chip method-{method.lower()}')
                        ui.label(url).classes('font-mono text-sm break-all text-gray-800 flex-1 mx-4')
                        ui.label(ts_str).classes('text-gray-500 text-xs whitespace-nowrap')
                    with ui.expansion('Headers').classes('mt-2'):
                        ui.code(headers, language='json').classes('w-full text-xs')