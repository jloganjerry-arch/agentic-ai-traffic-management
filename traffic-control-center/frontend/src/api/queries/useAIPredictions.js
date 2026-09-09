import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../client';
import { ENDPOINTS } from '../endpoints';

export function useAIPredictions() {
  return useQuery({
    queryKey: ['aiPredictions'],
    queryFn: async () => {
      const res = await apiClient.get(ENDPOINTS.PREDICTIONS);
      return res.data;
    },
    refetchInterval: 3000,
  });
}
