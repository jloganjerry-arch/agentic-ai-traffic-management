import { useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../client';
import { ENDPOINTS } from '../endpoints';

export function useEmergencyControl() {
  const queryClient = useQueryClient();

  const triggerEmergencyCorridor = useMutation({
    mutationFn: async ({ active, direction, vehicle_type }) => {
      const res = await apiClient.post(ENDPOINTS.EMERGENCY_CORRIDOR, { active, direction, vehicle_type });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['aiDecision'] });
      queryClient.invalidateQueries({ queryKey: ['trafficOverview'] });
      queryClient.invalidateQueries({ queryKey: ['signalStatus'] });
    },
  });

  const toggleAdaptiveMode = useMutation({
    mutationFn: async ({ enabled }) => {
      const res = await apiClient.post(ENDPOINTS.ADAPTIVE_MODE, { enabled });
      return res.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['trafficOverview'] });
      queryClient.invalidateQueries({ queryKey: ['aiDecision'] });
    },
  });

  return {
    triggerEmergencyCorridor,
    toggleAdaptiveMode,
  };
}
