import { create } from 'zustand';

export const useUIStore = create((set) => ({
  activeWorkspace: 'tactical', // 'tactical' | 'agents' | 'analytics' | 'hardware' | 'unified'
  isSidebarCollapsed: false,
  emergencyDrawerOpen: false,
  pipActive: false,
  liveTicker: 'All 5 autonomous AI agents active. TraCI dynamic green optimization nominal.',

  setActiveWorkspace: (workspace) => set({ activeWorkspace: workspace }),
  toggleSidebar: () => set((state) => ({ isSidebarCollapsed: !state.isSidebarCollapsed })),
  setSidebarCollapsed: (collapsed) => set({ isSidebarCollapsed: collapsed }),
  setEmergencyDrawerOpen: (open) => set({ emergencyDrawerOpen: open }),
  toggleEmergencyDrawer: () => set((state) => ({ emergencyDrawerOpen: !state.emergencyDrawerOpen })),
  setLiveTicker: (msg) => set({ liveTicker: msg }),
  setPipActive: (active) => set({ pipActive: active }),
  togglePip: () => set((state) => ({ pipActive: !state.pipActive })),
}));
