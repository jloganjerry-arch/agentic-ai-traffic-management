import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../client';
import { ENDPOINTS } from '../endpoints';

export function useSignalStatus() {
  return useQuery({
    queryKey: ['signalStatus'],
    queryFn: async () => {
      const res = await apiClient.get(ENDPOINTS.SIGNALS);
      return res.data;
    },
    staleTime: Infinity, // State updates are driven event-driven via /ws/signals + local 1s timer tick
    refetchOnWindowFocus: false,
  });
}
