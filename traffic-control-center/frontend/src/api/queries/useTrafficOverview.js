import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../client';
import { ENDPOINTS } from '../endpoints';

export function useTrafficOverview() {
  return useQuery({
    queryKey: ['trafficOverview'],
    queryFn: async () => {
      const res = await apiClient.get(ENDPOINTS.OVERVIEW);
      return res.data;
    },
    refetchInterval: 1000,
  });
}
