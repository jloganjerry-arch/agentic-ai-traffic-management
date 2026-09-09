import React, { memo } from 'react';

/**
 * SignalRenderer - Visualizes 4 Smart Signal Controllers precisely at corner stop bars (North, South, East, West).
 * Features realistic 3-lamp LED housing (Red, Yellow, Green), high-intensity optical glow halos,
 * and adaptive timing status badges showing real-time environmental adaptations (Platoon extensions, Gap-Out, Rush Hour, Emergency).
 */
export const SignalRenderer = memo(function SignalRenderer({
  signals = []
}) {
  const getSignalForDirection = (dir) => {
    const s = signals.find((s) => s.direction?.toLowerCase() === dir.toLowerCase());
    if (s && s.state) return s;
    const isNS = dir.toLowerCase() === 'north' || dir.toLowerCase() === 'south';
    return {
      state: isNS ? 'GREEN' : 'RED',
      timer_remaining: 30,
      adaptive_action: 'NOMINAL',
      adaptive_reason: ''
    };
  };

  const signalConfigs = [
    { dir: 'North', label: 'NORTH', cx: 152, cy: 150, timerX: 126, timerY: 142 },
    { dir: 'South', label: 'SOUTH', cx: 248, cy: 250, timerX: 274, timerY: 258 },
    { dir: 'East',  label: 'EAST',  cx: 250, cy: 152, timerX: 274, timerY: 142 },
    { dir: 'West',  label: 'WEST',  cx: 150, cy: 248, timerX: 126, timerY: 258 },
  ];

  return (
    <g className="traffic-signals-layer select-none">
      {signalConfigs.map(({ dir, label, cx, cy, timerX, timerY }) => {
        const sig = getSignalForDirection(dir);
        const state = (sig.state || 'GREEN').toUpperCase();
        const isRed = state === 'RED';
        const isYellow = state === 'YELLOW';
        const isGreen = state === 'GREEN';

        const activeColor = isYellow ? '#F59E0B' : (isRed ? '#EF4444' : '#10B981');
        const remainingSeconds = sig.timer_remaining !== undefined ? sig.timer_remaining : (sig.remaining_time || 0);

        // Environmental adaptive status detection
        const adaptiveAction = sig.adaptive_action || 'NOMINAL';
        const isExtending = isGreen && (adaptiveAction.includes('EXTEND') || sig.is_extending);
        const isGapOut = adaptiveAction.includes('GAP-OUT') || sig.is_gap_out;
        const isEmergency = adaptiveAction.includes('EMERGENCY') || sig.is_emergency;

        // Dynamic badge label reflecting environmental adaptation
        let badgeText = `${remainingSeconds}s`;
        let badgeWidth = 34;
        let badgeStroke = activeColor;
        let badgeBg = isYellow ? 'rgba(245, 158, 11, 0.22)' : (isGreen ? 'rgba(16, 185, 129, 0.15)' : 'rgba(15, 23, 42, 0.95)');

        if (isEmergency) {
          badgeText = isGreen ? 'PRIORITY' : 'HOLD';
          badgeWidth = 44;
          badgeStroke = isGreen ? '#10B981' : '#EF4444';
        } else if (isGapOut) {
          badgeText = 'GAP-OUT';
          badgeWidth = 42;
          badgeStroke = '#F59E0B';
          badgeBg = 'rgba(245, 158, 11, 0.35)';
        } else if (isExtending) {
          badgeText = `${remainingSeconds}s ⚡`;
          badgeWidth = 40;
          badgeStroke = '#06B6D4';
          badgeBg = 'rgba(6, 182, 212, 0.25)';
        } else if (isYellow) {
          badgeText = `${remainingSeconds}s YEL`;
          badgeWidth = 40;
        }

        return (
          <g key={`sig-head-${dir}`} className="transition-all duration-300">
            {/* Signal Box Housing */}
            <rect
              x={cx - 10}
              y={cy - 10}
              width="20"
              height="20"
              rx="4"
              fill="#060A17"
              stroke={isExtending ? '#06B6D4' : (isYellow ? '#D97706' : '#334155')}
              strokeWidth={isExtending ? '1.8' : (isYellow ? '1.4' : '1.2')}
              style={{
                filter: isExtending
                  ? 'drop-shadow(0 0 8px rgba(6,182,212,0.6))'
                  : isYellow
                  ? 'drop-shadow(0 0 6px rgba(245,158,11,0.5))'
                  : 'drop-shadow(0 2px 5px rgba(0,0,0,0.9))'
              }}
            />

            {/* Glowing Active LED Indicator Circle */}
            <circle
              cx={cx}
              cy={cy}
              r="6.5"
              fill={activeColor}
              style={{ filter: `drop-shadow(0 0 ${isYellow ? '10px' : '8px'} ${activeColor})` }}
              className="transition-all duration-300"
            />

            {/* Specular Highlight dot on LED */}
            <circle cx={cx - 2} cy={cy - 2} r="2" fill="rgba(255,255,255,0.45)" />

            {/* Signal State / Countdown Badge */}
            <rect
              x={timerX - badgeWidth / 2}
              y={timerY - 7.5}
              width={badgeWidth}
              height="15"
              rx="3.5"
              fill={badgeBg}
              stroke={badgeStroke}
              strokeWidth={isExtending || isGapOut ? '1.5' : (isYellow ? '1.2' : '0.9')}
              className={isExtending ? 'animate-pulse' : ''}
              opacity="0.98"
            />
            <text
              x={timerX}
              y={timerY + 3.2}
              textAnchor="middle"
              fill={isExtending ? '#67E8F9' : (isYellow ? '#FDE68A' : (isGreen ? '#6EE7B7' : '#F8FAFC'))}
              fontSize={isEmergency || isGapOut ? '7.5' : '8.5'}
              className="font-mono font-bold select-none uppercase tracking-tight"
            >
              {badgeText}
            </text>

            {/* Micro Adaptive Indicator Pill when extending or gap-out */}
            {isExtending && (
              <g transform={`translate(${timerX - 16}, ${timerY - 15})`}>
                <rect width="32" height="7" rx="2" fill="#0E7490" stroke="#22D3EE" strokeWidth="0.5" />
                <text x="16" y="5.2" textAnchor="middle" fill="#CFFAFE" fontSize="4.8" className="font-mono font-bold">
                  +4s ADAPT
                </text>
              </g>
            )}
            {isGapOut && (
              <g transform={`translate(${timerX - 16}, ${timerY - 15})`}>
                <rect width="32" height="7" rx="2" fill="#78350F" stroke="#F59E0B" strokeWidth="0.5" />
                <text x="16" y="5.2" textAnchor="middle" fill="#FEF3C7" fontSize="4.8" className="font-mono font-bold">
                  CLEARED
                </text>
              </g>
            )}
          </g>
        );
      })}
    </g>
  );
});
