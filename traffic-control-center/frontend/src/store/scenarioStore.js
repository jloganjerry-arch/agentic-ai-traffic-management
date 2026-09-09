import { create } from 'zustand';

export const useScenarioStore = create((set) => ({
  activeScenario: 'normal',
  scenarioApproach: 'North',
  scenarioIntensity: 1.8,
  scenarioImpact: 'Nominal baseline traffic conditions active across all 4 corridors.',
  
  // Emergency Vehicle Dispatch state
  emergencyVehicleType: 'ambulance', // 'ambulance' | 'fire' | 'police'
  emergencyActive: false,
  emergencyRoute: 'North-South',
  
  // Signal Sequencing Mode state: 'one_by_one' (4-Phase Isolated) | 'paired_corridor' (2-Phase)
  signalMode: 'paired_corridor',

  setScenario: (scenario, approach = 'North', intensity = 1.8, impact = '') => 
    set((state) => ({ 
      activeScenario: scenario, 
      scenarioApproach: approach, 
      scenarioIntensity: intensity, 
      scenarioImpact: impact,
      emergencyActive: scenario === 'emergency_corridor' ? true : (scenario === 'normal' ? false : state.emergencyActive)
    })),
    
  setEmergencyDispatch: (vehicleType = 'ambulance', route = 'North-South', active = true) =>
    set({
      emergencyVehicleType: vehicleType,
      emergencyRoute: route,
      emergencyActive: active,
      activeScenario: active ? 'emergency_corridor' : 'normal',
      scenarioApproach: route.includes('East') || route.includes('West') ? 'East' : 'North',
      scenarioImpact: active 
        ? `Emergency ${vehicleType.toUpperCase()} dispatched on ${route} corridor. Green Wave preemption active; conflicting signals locked RED.`
        : 'Nominal baseline traffic conditions across junction.'
    }),

  setSignalMode: (mode) =>
    set({
      signalMode: mode === 'one_by_one' ? 'one_by_one' : 'paired_corridor'
    }),

  resetScenario: () => 
    set({ 
      activeScenario: 'normal', 
      scenarioApproach: 'North', 
      scenarioIntensity: 1.0, 
      scenarioImpact: 'Nominal baseline traffic conditions active across all 4 corridors.',
      emergencyActive: false,
      emergencyVehicleType: 'ambulance'
    })
}));
