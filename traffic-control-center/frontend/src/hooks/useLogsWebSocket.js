import { useState, useEffect } from 'react';
import { wsLogs } from '../api/websocket';

export function useLogsWebSocket(initialLogs = []) {
  const [logs, setLogs] = useState(initialLogs);

  useEffect(() => {
    if (initialLogs.length > 0 && logs.length === 0) {
      setLogs(initialLogs);
    }
  }, [initialLogs]);

  useEffect(() => {
    const unsubscribe = wsLogs.subscribe((data) => {
      if (data.event === 'pipeline_event' || data.event === 'log_event') {
        setLogs((prev) => [
          {
            timestamp: data.timestamp ? new Date(data.timestamp).toLocaleTimeString() : new Date().toLocaleTimeString(),
            level: data.level || 'INFO',
            source: data.source || 'Pipeline',
            message: data.message || JSON.stringify(data),
          },
          ...prev.slice(0, 49), // Keep latest 50 logs
        ]);
      }
    });

    return () => unsubscribe();
  }, []);

  return logs;
}
