import React from 'react';
import { SectionCard } from '../layout/SectionCard';
import { useTrends } from '../../api/queries/useTrends';
import { useConnectionStore } from '../../store/connectionStore';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid } from 'recharts';
import { TrendingUp } from 'lucide-react';

export function TrendChart() {
  const { data: trends } = useTrends();
  const { trendTimeRange, setTrendTimeRange } = useConnectionStore();

  const volumeData = trends?.volume_over_time ?? [];

  return (
    <SectionCard
      title="Traffic Volume & Speed Trends"
      icon={TrendingUp}
      action={
        <div className="flex items-center space-x-2">
          <span className="text-[10px] font-mono text-slate-400 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
            Source: {trends?.source || 'sumo_simulation'} ({trends?.confidence || 'exact'})
          </span>
          <div className="flex items-center bg-slate-900 p-0.5 rounded-lg border border-slate-800 text-xs">
            {['15m', '1h', '24h'].map((range) => (
              <button
                key={range}
                onClick={() => setTrendTimeRange(range)}
                className={`px-2.5 py-0.5 rounded font-mono text-[11px] transition ${
                  trendTimeRange === range
                    ? 'bg-cyan-500/20 text-cyan-400 font-semibold border border-cyan-500/40'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {range}
              </button>
            ))}
          </div>
        </div>
      }
    >
      <div className="h-[220px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={volumeData}>
            <defs>
              <linearGradient id="cyanGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#22D3EE" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#22D3EE" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
            <XAxis dataKey="time" stroke="#64748b" fontSize={11} />
            <YAxis stroke="#64748b" fontSize={11} />
            <Tooltip
              contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
              itemStyle={{ color: '#22d3ee' }}
            />
            <Area type="monotone" dataKey="volume" stroke="#22D3EE" fill="url(#cyanGradient)" strokeWidth={2} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </SectionCard>
  );
}
