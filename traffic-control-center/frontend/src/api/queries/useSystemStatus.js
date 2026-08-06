import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../client';

export function useSystemStatus() {
  return useQuery({
    queryKey: ['systemStatus'],
    queryFn: async () => {
      const res = await apiClient.get('/');
      return res.data;
    },
    refetchInterval: 10000,
  });
}
