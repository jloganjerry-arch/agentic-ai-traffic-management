import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../client';
import { ENDPOINTS } from '../endpoints';

export function useAgentStatus() {
  return useQuery({
    queryKey: ['agentStatus'],
    queryFn: async () => {
      const res = await apiClient.get(ENDPOINTS.AGENTS);
      return res.data;
    },
    refetchInterval: 1000,
  });
}
