import { useEffect } from 'react';
import { wsManager } from '../api/websocket';

export function useWebSocketChannel(onMessage) {
  useEffect(() => {
    wsManager.connect();
    const unsubscribe = wsManager.subscribe(onMessage);
    return () => {
      unsubscribe();
    };
  }, [onMessage]);
}
