import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../client';
import { ENDPOINTS } from '../endpoints';

export function useHardwareStatus() {
  return useQuery({
    queryKey: ['hardwareStatus'],
    queryFn: async () => {
      const res = await apiClient.get(ENDPOINTS.HARDWARE);
      return res.data;
    },
    refetchInterval: 1000,
  });
}
