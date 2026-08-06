import React from 'react';
import { SectionCard } from '../layout/SectionCard';
import { HardwareStatusRow } from './HardwareStatusRow';
import { useHardwareStatus } from '../../api/queries/useHardwareStatus';
import { Cpu } from 'lucide-react';

export function HardwareGrid() {
  const { data: responseData } = useHardwareStatus();
  const nodes = responseData?.hardware_status || (Array.isArray(responseData) ? responseData : []);

  return (
    <SectionCard title="Microcontroller & ESP32 Node Network" icon={Cpu}>
      <div className="space-y-2">
        {nodes.map((node, idx) => (
          <HardwareStatusRow key={idx} {...node} />
        ))}
      </div>
    </SectionCard>
  );
}
