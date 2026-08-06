import React from 'react';
import { SectionCard } from '../layout/SectionCard';
import { useDatasetPreview } from '../../api/queries/useDatasetPreview';
import { Database } from 'lucide-react';

export function DatasetTable() {
  const { data: dataset } = useDatasetPreview();
  const columns = dataset?.columns ?? ['timestamp', 'junction_id', 'vehicle_count', 'avg_speed', 'queue_length', 'signal_phase'];
  const rows = dataset?.rows ?? [];

  return (
    <SectionCard title="Dataset Telemetry Stream (dataset_v2.5)" icon={Database}>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-slate-900/80 text-slate-400 border-b border-slate-800">
            <tr>
              {columns.map((col, idx) => (
                <th key={idx} className="px-4 py-2.5 uppercase font-medium">{col}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {rows.map((row, rIdx) => (
              <tr key={rIdx} className="hover:bg-slate-800/30 transition">
                {row.map((cell, cIdx) => (
                  <td key={cIdx} className="px-4 py-2.5 text-slate-300">{cell}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </SectionCard>
  );
}
