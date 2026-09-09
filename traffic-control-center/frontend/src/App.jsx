import React from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { workspaceTransitionVariants } from './theme/motion';
import { DashboardShell } from './components/layout/DashboardShell';
import { OverviewGrid } from './components/overview/OverviewGrid';
import { SumoSimulationPanel } from './components/simulation/SumoSimulationPanel';
import { ScenarioInjectorPanel } from './components/simulation/ScenarioInjectorPanel';
import { ApproachGrid } from './components/approach/ApproachGrid';
import { SignalGrid } from './components/signals/SignalGrid';
import { AgentPipelineFlow } from './components/agents/AgentPipelineFlow';
import { EmergencyCorridorPanel } from './components/emergency/EmergencyCorridorPanel';
import { AIPredictionPanel } from './components/prediction/AIPredictionPanel';
import { TrendChart } from './components/charts/TrendChart';
import { DatasetTable } from './components/dataset/DatasetTable';
import { HardwareGrid } from './components/hardware/HardwareGrid';
import { SystemLogPanel } from './components/logs/SystemLogPanel';
import { AIDecisionPanel } from './components/decision/AIDecisionPanel';
import { useUIStore } from './store/uiStore';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function DashboardContent() {
  const { activeWorkspace } = useUIStore();

  const isVisible = (workspaces) => workspaces.includes(activeWorkspace);

  return (
    <motion.div
      key={activeWorkspace}
      variants={workspaceTransitionVariants}
      initial="initial"
      animate="animate"
      className="space-y-6"
    >
      {/* Section 1: Overview Cards (8 primary metrics) */}
      <div className={isVisible(['tactical', 'analytics', 'unified']) ? 'block' : 'hidden'}>
        <OverviewGrid />
      </div>

      {/* Section 2: Multi-Agent Pipeline Status Flow */}
      <div className={isVisible(['agents', 'unified']) ? 'block' : 'hidden'}>
        <AgentPipelineFlow />
      </div>

      {/* 12-Column Responsive Layout Grid */}
      <div className="grid grid-cols-12 gap-6">
        {/* Scenario Injector Panel */}
        <div
          className={`${
            isVisible(['tactical', 'unified']) ? 'block' : 'hidden'
          } col-span-12 ${activeWorkspace === 'tactical' ? 'xl:col-span-6' : ''}`}
        >
          <ScenarioInjectorPanel />
        </div>

        {/* Emergency Vehicle Green Corridor Control Panel */}
        <div
          className={`${
            isVisible(['tactical', 'unified']) ? 'block' : 'hidden'
          } col-span-12 xl:col-span-6`}
        >
          <EmergencyCorridorPanel />
        </div>

        {/* Section 3: SUMO Simulation Control Panel (Full Width Canvas) */}
        <div
          className={`${
            isVisible(['tactical', 'unified']) ? 'block' : 'hidden'
          } col-span-12`}
        >
          <SumoSimulationPanel />
        </div>

        {/* Section 5: Signal Heads & Live Dynamic Countdown Timers */}
        <div
          className={`${
            isVisible(['tactical', 'unified']) ? 'block' : 'hidden'
          } col-span-12 xl:col-span-6`}
        >
          <SignalGrid />
        </div>

        {/* Section 4: Approach Analytics Breakdown */}
        <div
          className={`${
            isVisible(['tactical', 'analytics', 'unified']) ? 'block' : 'hidden'
          } col-span-12 ${
            activeWorkspace === 'tactical'
              ? 'xl:col-span-6'
              : activeWorkspace === 'analytics'
              ? 'col-span-12'
              : 'lg:col-span-6'
          }`}
        >
          <ApproachGrid />
        </div>

        {/* Executive AI Supervisor Decision */}
        <div
          className={`${
            isVisible(['agents', 'unified']) ? 'block' : 'hidden'
          } col-span-12 xl:col-span-6`}
        >
          <AIDecisionPanel />
        </div>

        {/* AI Congestion Prediction Panel (+15m, +30m, +60m) */}
        <div
          className={`${
            isVisible(['analytics', 'unified']) ? 'block' : 'hidden'
          } col-span-12`}
        >
          <AIPredictionPanel />
        </div>

        {/* Section 6: Historical Time-Series Trends */}
        <div
          className={`${
            isVisible(['analytics', 'unified']) ? 'block' : 'hidden'
          } col-span-12`}
        >
          <TrendChart />
        </div>

        {/* Section 7: Live TraCI Dataset Preview */}
        <div
          className={`${
            isVisible(['hardware', 'unified']) ? 'block' : 'hidden'
          } col-span-12 xl:col-span-6`}
        >
          <DatasetTable />
        </div>

        {/* Section 8: Hardware Microcontrollers (ESP32) */}
        <div
          className={`${
            isVisible(['hardware', 'unified']) ? 'block' : 'hidden'
          } col-span-12 xl:col-span-6`}
        >
          <HardwareGrid />
        </div>

        {/* Section 9: Real-time Event Log Console */}
        <div
          className={`${
            isVisible(['agents', 'hardware', 'unified']) ? 'block' : 'hidden'
          } col-span-12`}
        >
          <SystemLogPanel />
        </div>
      </div>
    </motion.div>
  );
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <DashboardShell>
        <DashboardContent />
      </DashboardShell>
    </QueryClientProvider>
  );
}
