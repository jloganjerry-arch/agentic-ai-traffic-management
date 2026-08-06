import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../client';
import { ENDPOINTS } from '../endpoints';

export function useAIDecision() {
  return useQuery({
    queryKey: ['aiDecision'],
    queryFn: async () => {
      const res = await apiClient.get(ENDPOINTS.DECISION);
      return res.data;
    },
    refetchInterval: 1000,
  });
}
