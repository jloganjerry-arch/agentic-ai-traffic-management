import { create } from 'zustand';

export const useConnectionStore = create((set) => ({
  sumoStatus: 'ONLINE',
  fastApiStatus: 'ONLINE',
  mqttStatus: 'CONNECTED',
  esp32Status: 'ACTIVE',
  trendTimeRange: '15m',
  
  setSumoStatus: (status) => set({ sumoStatus: status }),
  setFastApiStatus: (status) => set({ fastApiStatus: status }),
  setMqttStatus: (status) => set({ mqttStatus: status }),
  setEsp32Status: (status) => set({ esp32Status: status }),
  setTrendTimeRange: (range) => set({ trendTimeRange: range }),
  
  updateHealthFromHeartbeat: (data) => set({
    fastApiStatus: data.status || 'ONLINE',
    sumoStatus: data.source === 'sumo_simulation' ? 'ONLINE' : 'STANDBY',
    mqttStatus: 'CONNECTED',
    esp32Status: 'ACTIVE'
  })
}));
