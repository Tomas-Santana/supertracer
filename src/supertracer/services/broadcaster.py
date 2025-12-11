from typing import Callable, List
from supertracer.types.logs import Log

class LogBroadcaster:
    """
    A simple broadcaster to notify subscribers of new log entries.
    """
    def __init__(self):
        self._subscribers: List[Callable[[Log], None]] = []

    def subscribe(self, callback: Callable[[Log], None]):
        self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[Log], None]):
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def broadcast(self, log: Log):
        for callback in self._subscribers:
            try:
                callback(log)
            except Exception as e:
                print(f"Error broadcasting log: {e}")
