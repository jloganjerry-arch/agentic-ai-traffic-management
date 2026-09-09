export class WebSocketManager {
  constructor(endpoint = '/ws/live') {
    this.endpoint = endpoint;
    this.socket = null;
    this.listeners = new Set();
    this.reconnectTimer = null;
    this.isConnecting = false;
  }

  getWsUrl() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host || '127.0.0.1:3000';
    return `${protocol}//${host}${this.endpoint}`;
  }

  connect() {
    if (this.socket && (this.socket.readyState === WebSocket.OPEN || this.socket.readyState === WebSocket.CONNECTING)) {
      return;
    }

    this.isConnecting = true;
    const url = this.getWsUrl();

    try {
      this.socket = new WebSocket(url);

      this.socket.onopen = () => {
        this.isConnecting = false;
      };

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          this.listeners.forEach((callback) => callback(data));
        } catch (err) {
          console.error(`[WS ${this.endpoint}] Failed to parse JSON frame:`, err);
        }
      };

      this.socket.onclose = () => {
        this.isConnecting = false;
        this.scheduleReconnect();
      };

      this.socket.onerror = (err) => {
        console.warn(`[WS ${this.endpoint}] Socket error:`, err);
      };
    } catch (e) {
      this.isConnecting = false;
      this.scheduleReconnect();
    }
  }

  scheduleReconnect() {
    if (!this.reconnectTimer) {
      this.reconnectTimer = setTimeout(() => {
        this.reconnectTimer = null;
        this.connect();
      }, 3000);
    }
  }

  subscribe(callback) {
    this.listeners.add(callback);
    if (!this.socket || this.socket.readyState === WebSocket.CLOSED) {
      this.connect();
    }
    return () => {
      this.listeners.delete(callback);
    };
  }

  disconnect() {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }
}

export const wsSignals = new WebSocketManager('/ws/signals');
export const wsLogs = new WebSocketManager('/ws/logs');
export const wsHeartbeat = new WebSocketManager('/ws/heartbeat');
export const wsManager = new WebSocketManager('/ws/live');
