import { useEffect } from 'react';
import { wsHeartbeat } from '../api/websocket';
import { useConnectionStore } from '../store/connectionStore';

export function useHeartbeatWebSocket() {
  const updateHealth = useConnectionStore((state) => state.updateHealthFromHeartbeat);
  const setFastApiStatus = useConnectionStore((state) => state.setFastApiStatus);

  useEffect(() => {
    const unsubscribe = wsHeartbeat.subscribe((data) => {
      if (data.event === 'heartbeat') {
        updateHealth(data);
      }
    });

    return () => {
      unsubscribe();
    };
  }, [updateHealth, setFastApiStatus]);
}
