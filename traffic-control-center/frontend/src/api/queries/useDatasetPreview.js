import { useQuery } from '@tanstack/react-query';
import { apiClient } from '../client';
import { ENDPOINTS } from '../endpoints';

export function useDatasetPreview() {
  return useQuery({
    queryKey: ['datasetPreview'],
    queryFn: async () => {
      const res = await apiClient.get(ENDPOINTS.DATASET_PREVIEW);
      return res.data;
    },
    refetchInterval: 1000,
  });
}
