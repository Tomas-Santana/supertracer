import sqlite3
import time
import json
import os
from typing import Callable
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

class SuperTracer:
    def __init__(self, app: FastAPI, db_path: str = "requests.db"):
        self.app = app
        self.db_path = db_path
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
        @self.app.get("/logs", response_class=HTMLResponse)
        def get_logs():
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id, method, url, timestamp, headers FROM requests ORDER BY id DESC LIMIT 100")
            rows = cursor.fetchall()
            conn.close()

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
