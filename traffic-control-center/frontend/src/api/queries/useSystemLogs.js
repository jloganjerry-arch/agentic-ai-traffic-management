import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../client';
import { ENDPOINTS } from '../endpoints';

export function useSystemLogs() {
  return useQuery({
    queryKey: ['systemLogs'],
    queryFn: async () => {
      const res = await apiClient.get(ENDPOINTS.LOGS);
      return res.data;
    },
    refetchInterval: 3000,
  });
}
