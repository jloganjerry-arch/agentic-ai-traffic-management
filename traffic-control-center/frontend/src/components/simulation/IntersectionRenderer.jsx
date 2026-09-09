import React, { memo, useState, useCallback, useMemo, useEffect, useRef } from 'react';
import { VehicleRenderer } from './VehicleRenderer';
import { SignalRenderer } from './SignalRenderer';
import { useScenarioStore } from '../../store/scenarioStore';

/**
 * Computes exact (x, y) coordinates, heading angle, blinkers, and metadata
 * along realistic multi-directional paths (Straight, Right Turn 15px arc, Left Turn 60px Bezier curve).
 */
function computeVehicleTrajectory(direction, maneuver, d, isStopped, isLaneBlocked = false, isMerging = false) {
  const cleanDir = (direction || 'North').toLowerCase();
  
  let x = 200;
  let y = 200;
  let angle = 0;
  let turnSignal = 'none';
  let destination = 'Unknown';
  let maneuverLabel = 'Straight';

  // Lane offset adjustments (e.g. if merging around accident on lane 1)
  const laneOffset = isMerging ? 8 : 0;

  if (cleanDir.includes('north')) {
    // APPROACH: NORTH (Heading down into junction)
    if (maneuver === 'right') {
      destination = 'West';
      maneuverLabel = 'Right Turn ↱ (N → W)';
      turnSignal = 'right';
      if (d <= 170) {
        x = 185 + laneOffset;
        y = d;
        angle = 180;
      } else if (d <= 200) {
        const p = (d - 170) / 30;
        x = 170 + 15 * Math.cos((p * Math.PI) / 2);
        y = 170 + 15 * Math.sin((p * Math.PI) / 2);
        angle = 180 + p * 90;
      } else {
        y = 185;
        x = 170 - (d - 200);
        angle = 270;
        if (d > 240) turnSignal = 'none';
      }
    } else if (maneuver === 'left') {
      destination = 'East';
      maneuverLabel = 'Left Turn ↰ (N → E)';
      turnSignal = 'left';
      if (d <= 170) {
        x = 185 + laneOffset;
        y = d;
        angle = 180;
      } else if (d <= 230) {
        const p = (d - 170) / 60;
        x = 185 + 45 * (p * p);
        y = 170 + 45 * (2 * p - p * p);
        angle = 180 - p * 90;
      } else {
        y = 215;
        x = 230 + (d - 230);
        angle = 90;
        if (d > 270) turnSignal = 'none';
      }
    } else {
      // Straight
      destination = 'South';
      maneuverLabel = 'Straight ↓ (N → S)';
      x = 185 + laneOffset;
      y = d;
      angle = 180;
      turnSignal = 'none';
    }
  } else if (cleanDir.includes('south')) {
    // APPROACH: SOUTH (Heading up into junction)
    if (maneuver === 'right') {
      destination = 'East';
      maneuverLabel = 'Right Turn ↱ (S → E)';
      turnSignal = 'right';
      if (d <= 170) {
        x = 215 - laneOffset;
        y = 400 - d;
        angle = 0;
      } else if (d <= 200) {
        const p = (d - 170) / 30;
        x = 230 - 15 * Math.cos((p * Math.PI) / 2);
        y = 230 - 15 * Math.sin((p * Math.PI) / 2);
        angle = p * 90;
      } else {
        y = 215;
        x = 230 + (d - 200);
        angle = 90;
        if (d > 240) turnSignal = 'none';
      }
    } else if (maneuver === 'left') {
      destination = 'West';
      maneuverLabel = 'Left Turn ↰ (S → W)';
      turnSignal = 'left';
      if (d <= 170) {
        x = 215 - laneOffset;
        y = 400 - d;
        angle = 0;
      } else if (d <= 230) {
        const p = (d - 170) / 60;
        x = 215 - 45 * (p * p);
        y = 230 - 45 * (2 * p - p * p);
        angle = 360 - p * 90;
      } else {
        y = 185;
        x = 170 - (d - 230);
        angle = 270;
        if (d > 270) turnSignal = 'none';
      }
    } else {
      // Straight
      destination = 'North';
      maneuverLabel = 'Straight ↑ (S → N)';
      x = 215 - laneOffset;
      y = 400 - d;
      angle = 0;
      turnSignal = 'none';
    }
  } else if (cleanDir.includes('west')) {
    // APPROACH: WEST (Heading right into junction)
    if (maneuver === 'right') {
      destination = 'South';
      maneuverLabel = 'Right Turn ↱ (W → S)';
      turnSignal = 'right';
      if (d <= 170) {
        x = d;
        y = 215 - laneOffset;
        angle = 90;
      } else if (d <= 200) {
        const p = (d - 170) / 30;
        x = 170 + 15 * Math.sin((p * Math.PI) / 2);
        y = 230 - 15 * Math.cos((p * Math.PI) / 2);
        angle = 90 + p * 90;
      } else {
        x = 185;
        y = 230 + (d - 200);
        angle = 180;
        if (d > 240) turnSignal = 'none';
      }
    } else if (maneuver === 'left') {
      destination = 'North';
      maneuverLabel = 'Left Turn ↰ (W → N)';
      turnSignal = 'left';
      if (d <= 170) {
        x = d;
        y = 215 - laneOffset;
        angle = 90;
      } else if (d <= 230) {
        const p = (d - 170) / 60;
        x = 170 + 45 * (2 * p - p * p);
        y = 215 - 45 * (p * p);
        angle = 90 - p * 90;
      } else {
        x = 215;
        y = 170 - (d - 230);
        angle = 0;
        if (d > 270) turnSignal = 'none';
      }
    } else {
      // Straight
      destination = 'East';
      maneuverLabel = 'Straight → (W → E)';
      x = d;
      y = 215 - laneOffset;
      angle = 90;
      turnSignal = 'none';
    }
  } else {
    // APPROACH: EAST (Heading left into junction)
    if (maneuver === 'right') {
      destination = 'North';
      maneuverLabel = 'Right Turn ↱ (E → N)';
      turnSignal = 'right';
      if (d <= 170) {
        x = 400 - d;
        y = 185 + laneOffset;
        angle = 270;
      } else if (d <= 200) {
        const p = (d - 170) / 30;
        x = 230 - 15 * Math.sin((p * Math.PI) / 2);
        y = 170 + 15 * Math.cos((p * Math.PI) / 2);
        angle = (270 + p * 90) % 360;
      } else {
        x = 215;
        y = 170 - (d - 200);
        angle = 0;
        if (d > 240) turnSignal = 'none';
      }
    } else if (maneuver === 'left') {
      destination = 'South';
      maneuverLabel = 'Left Turn ↰ (E → S)';
      turnSignal = 'left';
      if (d <= 170) {
        x = 400 - d;
        y = 185 + laneOffset;
        angle = 270;
      } else if (d <= 230) {
        const p = (d - 170) / 60;
        x = 230 - 45 * (2 * p - p * p);
        y = 185 + 45 * (p * p);
        angle = 270 - p * 90;
      } else {
        x = 185;
        y = 230 + (d - 230);
        angle = 180;
        if (d > 270) turnSignal = 'none';
      }
    } else {
      // Straight
      destination = 'West';
      maneuverLabel = 'Straight ← (E → W)';
      x = 400 - d;
      y = 185 + laneOffset;
      angle = 270;
      turnSignal = 'none';
    }
  }

  return {
    x: Math.max(8, Math.min(392, x)),
    y: Math.max(8, Math.min(392, y)),
    angle: Math.round((angle + 360) % 360),
    turn_signal: turnSignal,
    status: isStopped ? 'Queued' : 'Moving',
    destination,
    maneuver,
    maneuver_label: maneuverLabel
  };
}

/**
 * IntersectionRenderer - Smart City 4-Way Junction Visualizer with Dynamic Turning Trajectories,
 * Strict 4-Phase Isolated Movement, Realistic Queuing Physics, Scenario Injections,
 * Dedicated Emergency Vehicle Models (Ambulance, Fire, Police), and High-Tech Digital Road Surface layers.
 */
export const IntersectionRenderer = memo(function IntersectionRenderer({
  approaches = [],
  signals = [],
  telemetryVehicles = [],
  simTick = 0,
  onSelectVehicle,
  selectedVehicleId,
  activeScenario = 'normal',
  scenarioApproach = 'North'
}) {
  const [hoveredVehicle, setHoveredVehicle] = useState(null);
  const { emergencyVehicleType, emergencyActive, emergencyRoute, signalMode } = useScenarioStore();

  // Internal physical simulation state across ticks
  const simStateRef = useRef({
    vehicles: {},
    lastTick: 0,
    initialized: false
  });

  const getSignalState = useCallback((dir) => {
    const s = (signals || []).find((sig) => sig.direction?.toLowerCase() === dir.toLowerCase());
    if (s && s.state) return s.state.toUpperCase();
    return (dir === 'North' || dir === 'South') ? 'GREEN' : 'RED';
  }, [signals]);

  // Generate & animate persistent vehicle physics on each frame
  const displayVehicles = useMemo(() => {
    const state = simStateRef.current;
    const dirs = ['North', 'South', 'East', 'West'];

    // Determine target vehicle count per direction based on active scenario and telemetry
    const getTargetCount = (dir) => {
      const appData = (approaches || []).find(a => a.approach?.toLowerCase() === dir.toLowerCase());
      if (appData && typeof appData.vehicle_count === 'number' && appData.vehicle_count > 0) {
        return Math.min(appData.vehicle_count, 6);
      }
      const isTarget = scenarioApproach?.toLowerCase().includes(dir.toLowerCase());
      if (activeScenario === 'rush_hour' && isTarget) return 6;
      if (activeScenario === 'accident_blockage' && isTarget) return 5;
      return 4;
    };

    // Initialize vehicle registry if needed
    if (!state.initialized) {
      state.vehicles = {};
      dirs.forEach((dir) => {
        const cnt = getTargetCount(dir);
        state.vehicles[dir] = [];
        for (let i = 0; i < cnt; i++) {
          const maneuver = (i % 3 === 1) ? 'right' : ((i % 3 === 2) ? 'left' : 'straight');
          state.vehicles[dir].push({
            id: `veh_${dir.toLowerCase()}_${i + 1}`,
            dir,
            d: 18 + i * 44, // Clean 44px spacing between vehicle centers
            maneuver,
            vehicleType: (i === 0 && dir === 'North') ? 'sedan' : (i % 5 === 0 ? 'bus' : (i % 3 === 0 ? 'van' : 'sedan')),
            speed: 30 + (i % 3) * 3
          });
        }
      });
      state.initialized = true;
    }

    const renderedVehicles = [];

    dirs.forEach((dir) => {
      const sigState = getSignalState(dir);
      const isRed = sigState === 'RED';
      const isYellow = sigState === 'YELLOW';
      const isGreen = sigState === 'GREEN';

      // Check if this direction has an emergency vehicle active
      const isEmergencyCorridorDir = 
        (emergencyActive || activeScenario === 'emergency_corridor') &&
        ((emergencyRoute?.toLowerCase().includes(dir.toLowerCase())) || (scenarioApproach?.toLowerCase().includes(dir.toLowerCase())));

      let vehList = state.vehicles[dir] || [];
      const targetCnt = getTargetCount(dir);

      // Adjust list size smoothly to match target count
      while (vehList.length < targetCnt) {
        const idx = vehList.length;
        const lastCarD = vehList.length > 0 ? vehList[vehList.length - 1].d : 44;
        vehList.push({
          id: `veh_${dir.toLowerCase()}_${idx + 1}`,
          dir,
          d: Math.max(10, lastCarD - 44),
          maneuver: (idx % 3 === 1) ? 'right' : ((idx % 3 === 2) ? 'left' : 'straight'),
          vehicleType: idx % 4 === 0 ? 'van' : 'sedan',
          speed: 30
        });
      }
      if (vehList.length > targetCnt) {
        vehList = vehList.slice(0, targetCnt);
      }
      state.vehicles[dir] = vehList;

      // Speed modifier based on weather scenario
      const weatherFactor = activeScenario === 'weather_hazard' ? 0.65 : 1.0;
      const isAccidentApproach = activeScenario === 'accident_blockage' && scenarioApproach?.toLowerCase().includes(dir.toLowerCase());

      // Advance positions sequentially from front car to rear car with strict anti-collision bounds
      let prevDistance = 999;

      vehList.forEach((v, index) => {
        let currentD = v.d;
        let isStopped = false;
        let currentSpeed = v.speed * weatherFactor;

        // In Emergency Corridor mode, assign the lead vehicle to the selected emergency vehicle type
        let vType = v.vehicleType;
        if (isEmergencyCorridorDir && index === 0) {
          vType = emergencyVehicleType || 'ambulance';
          currentSpeed = 48; // Emergency speed
        }

        // Accident blockage setup: stalled vehicle at d = 110 on target approach
        const isBlocked = isAccidentApproach && currentD < 140 && currentD > 80;
        let isMerging = false;

        // Queuing physics before stop bar (164px)
        const stopLine = 164;
        const minStopGap = 34; // 34px minimum bumper-to-bumper center gap in queue (gives 20px clean asphalt gap)
        const dynamicFollowGap = Math.max(minStopGap, 44 + currentSpeed * 0.25); // Natural 44px+ gap when driving

        if (isRed) {
          // Approaching RED: If before stop line, stop at line or behind previous car
          if (currentD < stopLine) {
            const maxAllowed = Math.min(stopLine - 4, prevDistance - minStopGap);
            if (currentD >= maxAllowed - 1) {
              currentD = Math.max(10, maxAllowed);
              isStopped = true;
              currentSpeed = 0;
            } else {
              // Smooth progressive deceleration approaching queue
              const distanceToTarget = maxAllowed - currentD;
              const step = Math.min(currentSpeed * 0.045, Math.max(0.4, distanceToTarget * 0.12));
              currentD += step;
              if (currentD >= maxAllowed - 1) {
                currentD = maxAllowed;
                isStopped = true;
                currentSpeed = 0;
              }
            }
          } else {
            // Already inside or past junction: continue clearing the intersection!
            currentD += currentSpeed * 0.048;
          }
        } else if (isYellow) {
          // YELLOW CLEARANCE (Dilemma-Zone Handling):
          if (currentD < stopLine - 35) {
            const maxAllowed = Math.min(stopLine - 4, prevDistance - minStopGap);
            currentD += Math.min(currentSpeed * 0.038, Math.max(0, (maxAllowed - currentD) * 0.08));
            if (currentD >= maxAllowed - 1) {
              currentD = maxAllowed;
              isStopped = true;
              currentSpeed = 0;
            }
          } else {
            // Clearing junction:
            const maxAllowed = prevDistance - minStopGap;
            currentD += Math.min(currentSpeed * 0.048, Math.max(1.0, (maxAllowed - currentD) * 0.15));
          }
        } else {
          // GREEN:
          const maxAllowed = prevDistance - dynamicFollowGap;
          if (currentD < maxAllowed) {
            currentD += Math.min(currentSpeed * 0.048, Math.max(0.6, (maxAllowed - currentD) * 0.14));
          } else {
            currentD = Math.max(10, maxAllowed);
            if (currentD < stopLine && maxAllowed < stopLine) {
              isStopped = true;
              currentSpeed = 0;
            }
          }
        }

        // Handle accident merge
        if (isAccidentApproach && currentD >= 65 && currentD <= 150) {
          isMerging = true;
        }

        // Recycle car when it exits corridor (past 390px)
        if (currentD > 390) {
          currentD = 10;
          v.maneuver = (index % 3 === 1) ? 'right' : ((index % 3 === 2) ? 'left' : 'straight');
          v.vehicleType = (index % 5 === 0) ? 'bus' : (index % 3 === 0 ? 'van' : 'sedan');
        }

        v.d = currentD;
        prevDistance = currentD;

        // Compute 2D Vector trajectory
        const traj = computeVehicleTrajectory(dir, v.maneuver, currentD, isStopped, isBlocked, isMerging);

        renderedVehicles.push({
          id: v.id,
          x: traj.x,
          y: traj.y,
          angle: traj.angle,
          turn_signal: traj.turn_signal,
          speed_kmh: isStopped ? 0 : Math.round(currentSpeed),
          vehicle_type: vType,
          direction: dir,
          destination: traj.destination,
          maneuver: traj.maneuver,
          maneuver_label: traj.maneuver_label,
          status: traj.status,
          is_emergency: isEmergencyCorridorDir && index === 0,
          lane_id: `${dir.toLowerCase()}_lane_${traj.maneuver}`
        });
      });
    });

    // Sort rendered vehicles for clean SVG z-index layering (Emergency & selected vehicles rendered on top)
    const sortedVehicles = [...renderedVehicles].sort((a, b) => {
      if (a.id === selectedVehicleId || a.id === hoveredVehicle?.id) return 1;
      if (b.id === selectedVehicleId || b.id === hoveredVehicle?.id) return -1;
      if (a.is_emergency && !b.is_emergency) return 1;
      if (!a.is_emergency && b.is_emergency) return -1;
      return 0;
    });

    return sortedVehicles;
  }, [simTick, getSignalState, activeScenario, scenarioApproach, emergencyActive, emergencyRoute, emergencyVehicleType, approaches, selectedVehicleId, hoveredVehicle]);

  // Digital VMS Display Text for dynamic overhead gantries
  const getGantryMessage = (dir) => {
    const isTarget = scenarioApproach?.toLowerCase().includes(dir.toLowerCase());
    if (emergencyActive || activeScenario === 'emergency_corridor') {
      const isEmergency = emergencyRoute?.toLowerCase().includes(dir.toLowerCase()) || isTarget;
      return isEmergency 
        ? `🚨 EMERGENCY ${emergencyVehicleType?.toUpperCase()} PREEMPTION ACTIVE • SPEED 50 KM/H`
        : `🛑 HOLD - CROSS TRAFFIC EMERGENCY CORRIDOR LOCK`;
    }
    if (activeScenario === 'rush_hour' && isTarget) {
      return `⚡ RUSH HOUR SURGE (+80% DENSITY) • AI EXPANDING GREEN`;
    }
    if (activeScenario === 'accident_blockage' && isTarget) {
      return `⚠️ ACCIDENT AHEAD IN LANE 1 • MERGE LEFT • SPEED 15 KM/H`;
    }
    if (activeScenario === 'weather_hazard') {
      return `🌧️ WET SURFACE • SPEED REDUCED 40% • SAFE DISTANCE`;
    }
    return `● SMART CORRIDOR AI-SYNCED • SPEED LIMIT 45 KM/H`;
  };

  return (
    <div className="relative w-full h-full flex items-center justify-center select-none overflow-hidden rounded-xl bg-[#080D1A] border border-slate-800/80 shadow-2xl">
      {/* Dynamic Digital Grid Texture */}
      <div className="absolute inset-0 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:20px_20px] opacity-30"></div>

      {/* SVG Smart City Junction Canvas (400x400 ViewBox) */}
      <svg viewBox="0 0 400 400" className="w-full h-full max-w-[580px] max-h-[580px]">
        <defs>
          {/* Surface Gradients */}
          <linearGradient id="roadGradNS" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#0B1329" />
            <stop offset="50%" stopColor="#111B36" />
            <stop offset="100%" stopColor="#0B1329" />
          </linearGradient>
          <linearGradient id="roadGradEW" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#0B1329" />
            <stop offset="50%" stopColor="#111B36" />
            <stop offset="100%" stopColor="#0B1329" />
          </linearGradient>

          {/* Forward Headlight Beam Gradient */}
          <linearGradient id="headlightBeamGrad" x1="0" y1="1" x2="0" y2="0">
            <stop offset="0%" stopColor="rgba(254, 240, 138, 0.45)" />
            <stop offset="100%" stopColor="rgba(254, 240, 138, 0)" />
          </linearGradient>

          {/* Emergency Neon Green Wave Gradient */}
          <linearGradient id="emergencyWaveGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="rgba(16, 185, 129, 0.35)" />
            <stop offset="50%" stopColor="rgba(5, 150, 105, 0.15)" />
            <stop offset="100%" stopColor="rgba(16, 185, 129, 0.35)" />
          </linearGradient>

          {/* Rush Hour Surge Heatmap Gradient */}
          <linearGradient id="surgeHeatGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="rgba(245, 158, 11, 0.3)" />
            <stop offset="50%" stopColor="rgba(239, 68, 68, 0.2)" />
            <stop offset="100%" stopColor="rgba(245, 158, 11, 0.3)" />
          </linearGradient>

          {/* Central Radial Glow */}
          <radialGradient id="junctionHubGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(34, 211, 238, 0.18)" />
            <stop offset="100%" stopColor="rgba(34, 211, 238, 0)" />
          </radialGradient>
        </defs>

        {/* 1. Outer Ground Background */}
        <rect width="400" height="400" fill="#080D1A" />

        {/* 2. Central Hub Ambient Glow */}
        <circle cx="200" cy="200" r="140" fill="url(#junctionHubGlow)" />

        {/* 3. North-South Road Corridor (Width: 60px) */}
        <rect x="170" y="0" width="60" height="400" fill="url(#roadGradNS)" stroke="#1E293B" strokeWidth="1" />
        {/* East-West Road Corridor (Width: 60px) */}
        <rect x="0" y="170" width="400" height="60" fill="url(#roadGradEW)" stroke="#1E293B" strokeWidth="1" />

        {/* 4. Intersection Core Box */}
        <rect x="170" y="170" width="60" height="60" fill="#17223B" stroke="#334155" strokeWidth="1.5" />

        {/* 5. Center Yellow Dividing Lines (Dashed) */}
        <line x1="200" y1="0" x2="200" y2="170" stroke="#F59E0B" strokeWidth="1.5" strokeDasharray="6 4" opacity="0.75" />
        <line x1="200" y1="230" x2="200" y2="400" stroke="#F59E0B" strokeWidth="1.5" strokeDasharray="6 4" opacity="0.75" />
        <line x1="0" y1="200" x2="170" y2="200" stroke="#F59E0B" strokeWidth="1.5" strokeDasharray="6 4" opacity="0.75" />
        <line x1="230" y1="200" x2="400" y2="200" stroke="#F59E0B" strokeWidth="1.5" strokeDasharray="6 4" opacity="0.75" />

        {/* 6. Embedded Inductive Sensor Loops & GLIDE Detection in asphalt near stop lines */}
        <rect x="175" y="152" width="20" height="12" rx="1.5" fill={signalMode === 'one_by_one' ? 'rgba(16, 185, 129, 0.12)' : 'none'} stroke={signalMode === 'one_by_one' ? '#10B981' : '#22D3EE'} strokeWidth="1" strokeDasharray="2 2" opacity="0.85" className="animate-pulse" />
        <rect x="205" y="236" width="20" height="12" rx="1.5" fill={signalMode === 'one_by_one' ? 'rgba(16, 185, 129, 0.12)' : 'none'} stroke={signalMode === 'one_by_one' ? '#10B981' : '#22D3EE'} strokeWidth="1" strokeDasharray="2 2" opacity="0.85" className="animate-pulse" />
        <rect x="152" y="205" width="12" height="20" rx="1.5" fill={signalMode === 'one_by_one' ? 'rgba(16, 185, 129, 0.12)' : 'none'} stroke={signalMode === 'one_by_one' ? '#10B981' : '#22D3EE'} strokeWidth="1" strokeDasharray="2 2" opacity="0.85" className="animate-pulse" />
        <rect x="236" y="175" width="12" height="20" rx="1.5" fill={signalMode === 'one_by_one' ? 'rgba(16, 185, 129, 0.12)' : 'none'} stroke={signalMode === 'one_by_one' ? '#10B981' : '#22D3EE'} strokeWidth="1" strokeDasharray="2 2" opacity="0.85" className="animate-pulse" />

        {/* 7. Multi-Directional Pavement Lane Guide Arrows */}
        <g opacity="0.65">
          {/* North Southbound */}
          <path d="M 185,75 L 185,95 M 181,90 L 185,95 L 189,90" stroke="#64748B" strokeWidth="1.4" fill="none" strokeLinecap="round" />
          <path d="M 185,85 C 185,90 180,93 175,93 M 177,90 L 175,93 L 178,96" stroke="#64748B" strokeWidth="1.2" fill="none" strokeLinecap="round" />
          <path d="M 185,85 C 185,90 190,93 195,93 M 193,90 L 195,93 L 192,96" stroke="#64748B" strokeWidth="1.2" fill="none" strokeLinecap="round" />
          
          {/* South Northbound */}
          <path d="M 215,325 L 215,305 M 211,310 L 215,305 L 219,310" stroke="#64748B" strokeWidth="1.4" fill="none" strokeLinecap="round" />
          <path d="M 215,315 C 215,310 220,307 225,307 M 223,310 L 225,307 L 222,304" stroke="#64748B" strokeWidth="1.2" fill="none" strokeLinecap="round" />
          <path d="M 215,315 C 215,310 210,307 205,307 M 207,310 L 205,307 L 208,304" stroke="#64748B" strokeWidth="1.2" fill="none" strokeLinecap="round" />
          
          {/* West Eastbound */}
          <path d="M 75,215 L 95,215 M 90,211 L 95,215 L 90,219" stroke="#64748B" strokeWidth="1.4" fill="none" strokeLinecap="round" />
          <path d="M 85,215 C 90,215 93,220 93,225 M 90,223 L 93,225 L 96,222" stroke="#64748B" strokeWidth="1.2" fill="none" strokeLinecap="round" />
          <path d="M 85,215 C 90,215 93,210 93,205 M 90,207 L 93,205 L 96,208" stroke="#64748B" strokeWidth="1.2" fill="none" strokeLinecap="round" />
          
          {/* East Westbound */}
          <path d="M 325,185 L 305,185 M 310,181 L 305,185 L 310,189" stroke="#64748B" strokeWidth="1.4" fill="none" strokeLinecap="round" />
          <path d="M 315,185 C 310,185 307,180 307,175 M 310,177 L 307,175 L 304,178" stroke="#64748B" strokeWidth="1.2" fill="none" strokeLinecap="round" />
          <path d="M 315,185 C 310,185 307,190 307,195 M 310,193 L 307,195 L 304,192" stroke="#64748B" strokeWidth="1.2" fill="none" strokeLinecap="round" />
        </g>

        {/* 8. Zebra Crosswalks */}
        <line x1="172" y1="162" x2="228" y2="162" stroke="#64748B" strokeWidth="4" strokeDasharray="4 4" opacity="0.6" />
        <line x1="172" y1="238" x2="228" y2="238" stroke="#64748B" strokeWidth="4" strokeDasharray="4 4" opacity="0.6" />
        <line x1="162" y1="172" x2="162" y2="228" stroke="#64748B" strokeWidth="4" strokeDasharray="4 4" opacity="0.6" />
        <line x1="238" y1="172" x2="238" y2="228" stroke="#64748B" strokeWidth="4" strokeDasharray="4 4" opacity="0.6" />

        {/* 9. Solid White Stop Bars */}
        <line x1="170" y1="170" x2="200" y2="170" stroke="#F8FAFC" strokeWidth="3" opacity="0.9" />
        <line x1="200" y1="230" x2="230" y2="230" stroke="#F8FAFC" strokeWidth="3" opacity="0.9" />
        <line x1="170" y1="200" x2="170" y2="230" stroke="#F8FAFC" strokeWidth="3" opacity="0.9" />
        <line x1="230" y1="170" x2="230" y2="200" stroke="#F8FAFC" strokeWidth="3" opacity="0.9" />

        {/* ==================================================================== */}
        {/* 10. DYNAMIC DIGITAL ROAD SCENARIO ENHANCEMENT LAYERS */}
        {/* ==================================================================== */}

        {/* A. EMERGENCY GREEN WAVE CORRIDOR RUNWAY LIGHTS & RED LASER STOP BARS */}
        {(emergencyActive || activeScenario === 'emergency_corridor') && (
          <g className="pointer-events-none animate-fadeIn">
            {/* 1. Neon Green Runway Lighting along priority corridor */}
            {(emergencyRoute?.includes('East') || emergencyRoute?.includes('West') || scenarioApproach?.includes('East') || scenarioApproach?.includes('West')) ? (
              <>
                <rect x="0" y="170" width="400" height="60" fill="url(#emergencyWaveGrad)" stroke="#10B981" strokeWidth="1.8" strokeDasharray="8 4" className="animate-pulse" />
                {/* Fast Sweeping Directional Chevrons */}
                {[...Array(8)].map((_, i) => (
                  <path
                    key={i}
                    d={`M ${30 + i * 45},195 L ${40 + i * 45},200 L ${30 + i * 45},205`}
                    stroke="#34D399"
                    strokeWidth="2.2"
                    fill="none"
                    strokeLinecap="round"
                    className="animate-pulse"
                    style={{ animationDelay: `${i * 0.1}s` }}
                  />
                ))}
                {/* Red Laser Stop Bars on Cross Roads (North & South) */}
                <line x1="170" y1="170" x2="200" y2="170" stroke="#EF4444" strokeWidth="4" strokeDasharray="3 2" style={{ filter: 'drop-shadow(0 0 6px #EF4444)' }} />
                <line x1="200" y1="230" x2="230" y2="230" stroke="#EF4444" strokeWidth="4" strokeDasharray="3 2" style={{ filter: 'drop-shadow(0 0 6px #EF4444)' }} />
                <rect x="155" y="138" width="60" height="13" rx="2.5" fill="#450A0A" stroke="#EF4444" strokeWidth="0.8" />
                <text x="185" y="147.5" textAnchor="middle" fill="#FCA5A5" fontSize="6" className="font-mono font-bold">🛑 HOLD RED</text>
                <rect x="185" y="248" width="60" height="13" rx="2.5" fill="#450A0A" stroke="#EF4444" strokeWidth="0.8" />
                <text x="215" y="257.5" textAnchor="middle" fill="#FCA5A5" fontSize="6" className="font-mono font-bold">🛑 HOLD RED</text>
              </>
            ) : (
              <>
                <rect x="170" y="0" width="60" height="400" fill="url(#emergencyWaveGrad)" stroke="#10B981" strokeWidth="1.8" strokeDasharray="8 4" className="animate-pulse" />
                {/* Fast Sweeping Directional Chevrons */}
                {[...Array(8)].map((_, i) => (
                  <path
                    key={i}
                    d={`M 195,${30 + i * 45} L 200,${40 + i * 45} L 205,${30 + i * 45}`}
                    stroke="#34D399"
                    strokeWidth="2.2"
                    fill="none"
                    strokeLinecap="round"
                    className="animate-pulse"
                    style={{ animationDelay: `${i * 0.1}s` }}
                  />
                ))}
                {/* Red Laser Stop Bars on Cross Roads (East & West) */}
                <line x1="170" y1="200" x2="170" y2="230" stroke="#EF4444" strokeWidth="4" strokeDasharray="3 2" style={{ filter: 'drop-shadow(0 0 6px #EF4444)' }} />
                <line x1="230" y1="170" x2="230" y2="200" stroke="#EF4444" strokeWidth="4" strokeDasharray="3 2" style={{ filter: 'drop-shadow(0 0 6px #EF4444)' }} />
                <rect x="138" y="208" width="30" height="13" rx="2.5" fill="#450A0A" stroke="#EF4444" strokeWidth="0.8" />
                <text x="153" y="217.5" textAnchor="middle" fill="#FCA5A5" fontSize="5.5" className="font-mono font-bold">🛑 HOLD</text>
                <rect x="232" y="178" width="30" height="13" rx="2.5" fill="#450A0A" stroke="#EF4444" strokeWidth="0.8" />
                <text x="247" y="187.5" textAnchor="middle" fill="#FCA5A5" fontSize="5.5" className="font-mono font-bold">🛑 HOLD</text>
              </>
            )}
          </g>
        )}

        {/* B. RUSH HOUR CONGESTION HEATMAP & SURGE WAVES */}
        {activeScenario === 'rush_hour' && (
          <g className="pointer-events-none animate-fadeIn">
            {scenarioApproach?.toLowerCase().includes('east') || scenarioApproach?.toLowerCase().includes('west') ? (
              <rect x="0" y="170" width="400" height="60" fill="url(#surgeHeatGrad)" stroke="#F59E0B" strokeWidth="1.5" strokeDasharray="6 3" className="animate-pulse" />
            ) : (
              <rect x="170" y="0" width="60" height="400" fill="url(#surgeHeatGrad)" stroke="#F59E0B" strokeWidth="1.5" strokeDasharray="6 3" className="animate-pulse" />
            )}
          </g>
        )}

        {/* C. ACCIDENT / BLOCKAGE STALLED CAR & DIGITAL DIVERSION CHEVRONS */}
        {activeScenario === 'accident_blockage' && (() => {
          const clean = (scenarioApproach || 'North').toLowerCase();
          let ax = 185, ay = 110;
          if (clean.includes('south')) { ax = 215; ay = 290; }
          else if (clean.includes('east')) { ax = 290; ay = 185; }
          else if (clean.includes('west')) { ax = 110; ay = 215; }

          return (
            <g className="animate-fadeIn">
              {/* Pulsing Hazard Danger Zone */}
              <circle cx={ax} cy={ay} r="22" fill="rgba(239, 68, 68, 0.18)" stroke="#EF4444" strokeWidth="1.4" strokeDasharray="3 2" className="animate-pulse" />
              
              {/* Digital Asphalt Diversion Chevrons (Guides traffic to open lane) */}
              <path d={`M ${ax - 10},${ay - 22} L ${ax + 2},${ay - 14} M ${ax - 10},${ay - 16} L ${ax + 2},${ay - 8}`} stroke="#F59E0B" strokeWidth="1.8" fill="none" strokeLinecap="round" className="animate-pulse" />
              
              {/* Stalled Disabled Vehicle */}
              <rect x={ax - 5.5} y={ay - 10} width="11" height="20" rx="2.5" fill="#7F1D1D" stroke="#EF4444" strokeWidth="1" />
              <rect x={ax - 4.5} y={ay - 8} width="9" height="4" rx="1" fill="#18181B" />
              
              {/* 4-Corner Rapid Hazard Warning Blinkers */}
              <circle cx={ax - 4.5} cy={ay - 9} r="1.4" fill="#F59E0B" className="animate-ping" style={{ animationDuration: '0.4s' }} />
              <circle cx={ax + 4.5} cy={ay - 9} r="1.4" fill="#F59E0B" className="animate-ping" style={{ animationDuration: '0.4s' }} />
              <circle cx={ax - 4.5} cy={ay + 9} r="1.4" fill="#F59E0B" className="animate-ping" style={{ animationDuration: '0.4s' }} />
              <circle cx={ax + 4.5} cy={ay + 9} r="1.4" fill="#F59E0B" className="animate-ping" style={{ animationDuration: '0.4s' }} />
              
              {/* Reflective Safety Traffic Cones */}
              <polygon points={`${ax - 12},${ay - 16} ${ax - 9},${ay - 10} ${ax - 15},${ay - 10}`} fill="#F97316" stroke="#FFFFFF" strokeWidth="0.5" />
              <polygon points={`${ax + 12},${ay - 16} ${ax + 15},${ay - 10} ${ax + 9},${ay - 10}`} fill="#F97316" stroke="#FFFFFF" strokeWidth="0.5" />
              
              <rect x={ax - 30} y={ay + 14} width="60" height="12" rx="2.5" fill="rgba(15, 23, 42, 0.95)" stroke="#EF4444" strokeWidth="0.8" />
              <text x={ax} y={ay + 22.5} textAnchor="middle" fill="#FCA5A5" fontSize="6.5" className="font-mono font-bold">
                ⚠️ LANE BLOCKED
              </text>
            </g>
          );
        })()}

        {/* D. ADVERSE WEATHER RAIN PARTICLES & WET ROAD SHEEN */}
        {activeScenario === 'weather_hazard' && (
          <g opacity="0.55" className="pointer-events-none animate-fadeIn">
            {/* Animated falling rain streaks */}
            {[...Array(18)].map((_, idx) => (
              <line
                key={idx}
                x1={15 + ((idx * 23 + simTick * 5) % 370)}
                y1={10 + ((idx * 27 + simTick * 8) % 380)}
                x2={5 + ((idx * 23 + simTick * 5) % 370)}
                y2={28 + ((idx * 27 + simTick * 8) % 380)}
                stroke="#38BDF8"
                strokeWidth="1.4"
                strokeLinecap="round"
              />
            ))}
            {/* Road Surface Speed Reduction Badges */}
            <circle cx="185" cy="50" r="8" fill="#0369A1" stroke="#38BDF8" strokeWidth="0.8" />
            <text x="185" y="52.5" textAnchor="middle" fill="#FFFFFF" fontSize="5" className="font-mono font-bold">20</text>
            <circle cx="215" cy="350" r="8" fill="#0369A1" stroke="#38BDF8" strokeWidth="0.8" />
            <text x="215" y="352.5" textAnchor="middle" fill="#FFFFFF" fontSize="5" className="font-mono font-bold">20</text>
          </g>
        )}

        {/* ==================================================================== */}
        {/* 11. DYNAMIC OVERHEAD VMS GANTRY BANNERS ACROSS APPROACHES */}
        {/* ==================================================================== */}
        {/* North Gantry Banner */}
        <g transform="translate(110, 10)">
          <rect width="180" height="15" rx="3.5" fill="rgba(4, 7, 17, 0.95)" stroke="#334155" strokeWidth="0.8" style={{ filter: 'drop-shadow(0 2px 6px rgba(0,0,0,0.8))' }} />
          <text x="90" y="10.5" textAnchor="middle" fill="#38BDF8" fontSize="6.5" className="font-mono font-bold tracking-tight">
            {getGantryMessage('North')}
          </text>
        </g>

        {/* South Gantry Banner */}
        <g transform="translate(110, 375)">
          <rect width="180" height="15" rx="3.5" fill="rgba(4, 7, 17, 0.95)" stroke="#334155" strokeWidth="0.8" style={{ filter: 'drop-shadow(0 2px 6px rgba(0,0,0,0.8))' }} />
          <text x="90" y="10.5" textAnchor="middle" fill="#38BDF8" fontSize="6.5" className="font-mono font-bold tracking-tight">
            {getGantryMessage('South')}
          </text>
        </g>

        {/* 12. Traffic Signals Layer */}
        <SignalRenderer signals={signals} />

        {/* 13. Central Junction Hub Telemetry Marker */}
        <circle
          cx="200"
          cy="200"
          r="16"
          fill="#0B132B"
          stroke="#22D3EE"
          strokeWidth="1.5"
          strokeDasharray="4 2"
          className="animate-spin"
          style={{ animationDuration: '12s' }}
        />
        <text x="200" y="203.5" textAnchor="middle" fill="#22D3EE" fontSize="8" className="font-mono font-bold select-none">
          J1-HUB
        </text>

        {/* 14. Direction Orientation Badges */}
        <text x="200" y="36" textAnchor="middle" fill="#94A3B8" fontSize="9" className="font-mono font-semibold">NORTH</text>
        <text x="200" y="370" textAnchor="middle" fill="#94A3B8" fontSize="9" className="font-mono font-semibold">SOUTH</text>
        <text x="375" y="203.5" textAnchor="middle" fill="#94A3B8" fontSize="9" className="font-mono font-semibold">EAST</text>
        <text x="25" y="203.5" textAnchor="middle" fill="#94A3B8" fontSize="9" className="font-mono font-semibold">WEST</text>

        {/* 15. Active Vector SVG Vehicles Layer */}
        {displayVehicles.map((veh) => (
          <VehicleRenderer
            key={veh.id}
            vehicle={veh}
            isSelected={selectedVehicleId === veh.id}
            isHovered={hoveredVehicle?.id === veh.id}
            onHover={setHoveredVehicle}
            onLeave={() => setHoveredVehicle(null)}
            onClick={onSelectVehicle}
          />
        ))}
      </svg>

      {/* Hover Telemetry Tooltip */}
      {hoveredVehicle && (
        <div
          className="absolute z-20 pointer-events-none bg-slate-950/95 border border-cyan-500/50 p-2.5 rounded-lg shadow-2xl backdrop-blur-md text-xs font-mono text-slate-200 transition-opacity duration-150"
          style={{
            left: `${Math.max(8, Math.min(285, (hoveredVehicle.x / 400) * 100))}%`,
            top: `${Math.max(8, Math.min(285, (hoveredVehicle.y / 400) * 100 - 15))}%`
          }}
        >
          <div className="flex items-center justify-between border-b border-slate-800 pb-1 mb-1 space-x-3">
            <span className="text-cyan-400 font-bold">{hoveredVehicle.id}</span>
            <span className={`px-1.5 py-0.2 rounded text-[9px] uppercase font-bold ${
              hoveredVehicle.status === 'Queued' ? 'bg-amber-500/20 text-amber-300' : 'bg-emerald-500/20 text-emerald-300'
            }`}>
              {hoveredVehicle.status}
            </span>
          </div>
          <div className="space-y-0.5 text-[11px]">
            <div className="flex justify-between space-x-3"><span className="text-slate-400">Type:</span><strong className="text-slate-100 capitalize">{hoveredVehicle.vehicle_type}</strong></div>
            <div className="flex justify-between space-x-3"><span className="text-slate-400">Maneuver:</span><strong className="text-cyan-300">{hoveredVehicle.maneuver_label || hoveredVehicle.maneuver}</strong></div>
            <div className="flex justify-between space-x-3"><span className="text-slate-400">Route:</span><span className="text-slate-200">{hoveredVehicle.direction} → {hoveredVehicle.destination || 'Corridor'}</span></div>
            <div className="flex justify-between space-x-3"><span className="text-slate-400">Speed:</span><strong className="text-white">{hoveredVehicle.speed_kmh} km/h</strong></div>
            <div className="flex justify-between space-x-3"><span className="text-slate-400">Heading:</span><span className="text-slate-300">{hoveredVehicle.angle}°</span></div>
            {hoveredVehicle.turn_signal && hoveredVehicle.turn_signal !== 'none' && (
              <div className="flex justify-between space-x-3 text-amber-300"><span className="text-slate-400">Blinker:</span><span className="font-bold flex items-center space-x-1"><span>{hoveredVehicle.turn_signal.toUpperCase()}</span><span className="inline-block w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping"></span></span></div>
            )}
          </div>
        </div>
      )}
    </div>
  );
});
