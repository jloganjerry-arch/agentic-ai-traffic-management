import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../client';
import { ENDPOINTS } from '../endpoints';

export function useApproachData() {
  return useQuery({
    queryKey: ['approachData'],
    queryFn: async () => {
      const res = await apiClient.get(ENDPOINTS.APPROACH);
      return res.data;
    },
    refetchInterval: 3000,
  });
}
