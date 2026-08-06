import React from 'react';
import { ApproachCard } from './ApproachCard';
import { SectionCard } from '../layout/SectionCard';
import { useApproachData } from '../../api/queries/useApproachData';
import { Compass } from 'lucide-react';

export function ApproachGrid() {
  const { data: responseData } = useApproachData();
  const approaches = responseData?.approaches || (Array.isArray(responseData) ? responseData : []);

  return (
    <SectionCard title="Approach Telemetry (N / S / E / W)" icon={Compass}>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {approaches.map((app, idx) => (
          <ApproachCard key={idx} {...app} />
        ))}
      </div>
    </SectionCard>
  );
}
