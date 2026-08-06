import { useState, useEffect } from 'react';
import { wsSignals } from '../api/websocket';

export function useSignalsWebSocket(initialSignals = []) {
  const [signals, setSignals] = useState(initialSignals);

  useEffect(() => {
    if (initialSignals.length > 0 && signals.length === 0) {
      setSignals(initialSignals);
    }
  }, [initialSignals]);

  // Sync state on WebSocket events from /ws/signals
  useEffect(() => {
    const unsubscribe = wsSignals.subscribe((data) => {
      if (data.event === 'signal_state_sync' || data.event === 'signal_phase_change') {
        if (Array.isArray(data.signals)) {
          setSignals(data.signals);
        }
      }
    });

    return () => unsubscribe();
  }, []);

  // Local 1-second interval tick for smooth countdown timer rendering
  useEffect(() => {
    const interval = setInterval(() => {
      setSignals((prevSignals) =>
        prevSignals.map((sig) => ({
          ...sig,
          timer_remaining: Math.max(0, (sig.timer_remaining || 0) - 1),
        }))
      );
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return signals;
}
