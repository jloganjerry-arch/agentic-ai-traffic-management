import React from 'react';
import { OverviewCard } from './OverviewCard';
import { useTrafficOverview } from '../../api/queries/useTrafficOverview';
import { Car, Gauge, Layers, ShieldCheck, Activity, BarChart3, Radio, Bot } from 'lucide-react';

export function OverviewGrid() {
  const { data: overview } = useTrafficOverview();
  const confidence = overview?.confidence || 'exact';

  const metrics = [
    { label: 'Vehicle Volume', value: overview?.total_vehicle_count ?? 0, unit: 'veh', icon: Car, confidence },
    { label: 'Avg Speed', value: overview?.avg_speed_kmh ?? 0, unit: 'km/h', icon: Gauge, confidence },
    { label: 'Queue Length', value: overview?.total_queue_length_m ?? 0, unit: 'm', icon: Layers, confidence },
    { label: 'Traffic Density', value: overview?.avg_density_veh_km ?? 0, unit: 'v/km', icon: Activity, confidence },
    { label: 'Throughput', value: overview?.throughput_vph ?? 0, unit: 'v/h', icon: BarChart3, confidence },
    { label: 'Level of Service', value: overview?.level_of_service ?? 'A', unit: '', icon: ShieldCheck, statusColor: 'text-emerald-400', confidence },
    { label: 'Active Signals', value: overview?.active_signals ?? 4, unit: 'heads', icon: Radio, confidence },
    { label: 'AI Control Mode', value: overview?.ai_control_mode ?? 'Supervisory', unit: '', icon: Bot, statusColor: 'text-indigo-400', confidence },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {metrics.map((m, idx) => (
        <OverviewCard key={idx} {...m} />
      ))}
    </div>
  );
}
