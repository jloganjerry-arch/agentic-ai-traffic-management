import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../client';
import { ENDPOINTS } from '../endpoints';
import { useConnectionStore } from '../../store/connectionStore';

export function useTrends() {
  const trendTimeRange = useConnectionStore((state) => state.trendTimeRange);

  return useQuery({
    queryKey: ['trends', trendTimeRange],
    queryFn: async () => {
      const res = await apiClient.get(ENDPOINTS.TRENDS, {
        params: { window: trendTimeRange }
      });
      return res.data;
    },
    refetchInterval: 1000,
  });
}
