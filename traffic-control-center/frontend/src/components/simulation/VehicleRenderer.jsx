import React, { memo } from 'react';

/**
 * VehicleRenderer - Smart City SVG Vector Vehicle Renderer.
 * High-definition, properly scaled vehicle models designed for realistic road proportions:
 * - Ambulance 🚑 (White/Red livery, Red Cross roof badge, rapid Dual Red/Blue strobes, rear chevrons)
 * - Fire Truck 🚒 (Fire Engine Red heavy apparatus, roof ladder, dual Red/Amber strobes, chrome bullbar)
 * - Police Cruiser 🚓 (Black & White interceptor, aero Red/Blue strobe lightbar, front pushbar)
 * - City Bus 🚌 (Extended transit chassis, panoramic windows, destination marquee)
 * - Van / SUV 🚐 (Utility fleet vehicle, tinted windshield)
 * - Sedan 🚗 (Aerodynamic passenger car, LED headlights, taillights, blinkers)
 */
export const VehicleRenderer = memo(function VehicleRenderer({
  vehicle,
  isSelected = false,
  isHovered = false,
  onHover,
  onLeave,
  onClick
}) {
  if (!vehicle) return null;

  const {
    id = 'veh_0',
    x = 0,
    y = 0,
    angle = 0,
    speed_kmh = 0,
    vehicle_type = 'sedan',
    direction = 'North',
    status = 'Moving',
    turn_signal = 'none',
    is_emergency = false
  } = vehicle;

  const type = (vehicle_type || '').toLowerCase();
  const isAmbulance = type === 'ambulance' || (is_emergency && type.includes('amb'));
  const isFireTruck = type === 'fire' || type === 'fire_truck' || (is_emergency && type.includes('fire'));
  const isPolice = type === 'police' || (is_emergency && type.includes('pol'));
  const isGenericEmergency = type === 'emergency' && !isAmbulance && !isFireTruck && !isPolice;
  const isBus = type === 'bus';
  const isVan = type === 'van';
  const isStopped = status === 'Queued' || speed_kmh < 2;

  // Visual color theme per vehicle class
  const getVehicleTheme = () => {
    if (isAmbulance) return { body: '#F8FAFC', stroke: '#EF4444', glow: 'rgba(239, 68, 68, 0.95)', roof: '#FFFFFF' };
    if (isFireTruck) return { body: '#DC2626', stroke: '#FCA5A5', glow: 'rgba(239, 68, 68, 0.95)', roof: '#991B1B' };
    if (isPolice) return { body: '#0F172A', stroke: '#38BDF8', glow: 'rgba(56, 189, 248, 0.95)', roof: '#F8FAFC' };
    if (isGenericEmergency) return { body: '#EF4444', stroke: '#FCA5A5', glow: 'rgba(239, 68, 68, 0.95)', roof: '#991B1B' };
    if (isBus) return { body: '#D97706', stroke: '#FCD34D', glow: 'rgba(217, 119, 6, 0.7)', roof: '#78350F' };
    if (isVan) return { body: '#6366F1', stroke: '#A5B4FC', glow: 'rgba(99, 102, 241, 0.7)', roof: '#4338CA' };

    // Sedan colors tailored by approach for easy tracking
    const dir = (direction || '').toLowerCase();
    if (dir.includes('north') || dir.includes('south')) {
      return { body: '#0284C7', stroke: '#38BDF8', glow: 'rgba(56, 189, 248, 0.8)', roof: '#0369A1' };
    }
    return { body: '#0D9488', stroke: '#5EEAD4', glow: 'rgba(45, 212, 191, 0.8)', roof: '#115E59' };
  };

  const theme = getVehicleTheme();

  return (
    <g
      transform={`translate(${x}, ${y}) rotate(${angle})`}
      className="cursor-pointer select-none"
      onMouseEnter={() => onHover && onHover(vehicle)}
      onMouseLeave={() => onLeave && onLeave()}
      onClick={(e) => {
        e.stopPropagation();
        onClick && onClick(vehicle);
      }}
    >
      {/* 1. Forward Headlight Road Illumination Beam (when moving) */}
      {!isStopped && (
        <path
          d={isBus ? "M -3.8,-11 L -9,-28 L 9,-28 L 3.8,-11 Z" : "M -2.8,-7.5 L -7,-20 L 7,-20 L 2.8,-7.5 Z"}
          fill="url(#headlightBeamGrad)"
          opacity="0.28"
          className="pointer-events-none"
        />
      )}

      {/* 2. Soft Ground Shadow */}
      <ellipse
        cx="0"
        cy="0.5"
        rx={isFireTruck ? "5.2" : (isBus ? "4.8" : (isVan || isAmbulance ? "4.4" : "3.8"))}
        ry={isFireTruck ? "12" : (isBus ? "11" : (isVan || isAmbulance ? "9" : "7.8"))}
        fill="rgba(0, 0, 0, 0.55)"
        className="blur-[0.8px]"
      />

      {/* 3. Selection / Hover Glow Aura */}
      {(isSelected || isHovered) && (
        <rect
          x={isFireTruck ? "-6.5" : (isBus ? "-6" : "-5.5")}
          y={isFireTruck ? "-13.5" : (isBus ? "-12.5" : "-9.5")}
          width={isFireTruck ? "13" : (isBus ? "12" : "11")}
          height={isFireTruck ? "27" : (isBus ? "25" : "19")}
          rx="3"
          fill="none"
          stroke={isSelected ? "#22D3EE" : "#38BDF8"}
          strokeWidth="1.2"
          className="animate-pulse"
          style={{ filter: `drop-shadow(0 0 6px ${theme.glow})` }}
        />
      )}

      {/* ==================================================================== */}
      {/* 4. PROPORTIONAL VEHICLE BODY GEOMETRIES */}
      {/* ==================================================================== */}

      {/* A. AMBULANCE 🚑 (Width: 8px, Length: 17px) */}
      {isAmbulance && (
        <g>
          {/* Main Ambulance Body */}
          <rect x="-4" y="-8.5" width="8" height="17" rx="1.8" fill="#F8FAFC" stroke="#E2E8F0" strokeWidth="0.6" />
          
          {/* Red Emergency Side Stripes */}
          <rect x="-4" y="-2" width="8" height="1.8" fill="#DC2626" />
          
          {/* Cab Windshield */}
          <path d="M -3.2,-7.5 L 3.2,-7.5 L 2.8,-5 L -2.8,-5 Z" fill="#0F172A" opacity="0.9" />
          
          {/* Rear Medical Compartment */}
          <rect x="-3.4" y="-4.2" width="6.8" height="12" rx="0.8" fill="#FFFFFF" stroke="#CBD5E1" strokeWidth="0.3" />
          
          {/* Red Medical Cross Badge on Roof */}
          <g transform="translate(0, 0.8)">
            <rect x="-0.6" y="-1.8" width="1.2" height="3.6" fill="#EF4444" rx="0.2" />
            <rect x="-1.8" y="-0.6" width="3.6" height="1.2" fill="#EF4444" rx="0.2" />
          </g>

          {/* Rear Reflective Hazard Chevron Bar */}
          <rect x="-3.5" y="7.6" width="7" height="0.8" fill="#F59E0B" />
          <line x1="-2.2" y1="7.6" x2="-1.4" y2="8.4" stroke="#DC2626" strokeWidth="0.6" />
          <line x1="0" y1="7.6" x2="0.8" y2="8.4" stroke="#DC2626" strokeWidth="0.6" />
          <line x1="1.6" y1="7.6" x2="2.4" y2="8.4" stroke="#DC2626" strokeWidth="0.6" />

          {/* Dual Emergency Strobes: Red (Left) and Blue (Right) */}
          <circle cx="-2.4" cy="-3.8" r="1.3" fill="#EF4444" className="animate-ping" style={{ animationDuration: '0.35s' }} />
          <circle cx="-2.4" cy="-3.8" r="0.9" fill="#EF4444" style={{ filter: 'drop-shadow(0 0 3px #EF4444)' }} />
          <circle cx="2.4" cy="-3.8" r="1.3" fill="#3B82F6" className="animate-ping" style={{ animationDuration: '0.35s' }} />
          <circle cx="2.4" cy="-3.8" r="0.9" fill="#38BDF8" style={{ filter: 'drop-shadow(0 0 3px #38BDF8)' }} />

          {/* Front Headlights & Taillights */}
          <circle cx="-3" cy="-8.2" r="0.6" fill="#FEF08A" />
          <circle cx="3" cy="-8.2" r="0.6" fill="#FEF08A" />
          <line x1="-3.2" y1="8.3" x2="-1.6" y2="8.3" stroke="#EF4444" strokeWidth="0.8" />
          <line x1="1.6" y1="8.3" x2="3.2" y2="8.3" stroke="#EF4444" strokeWidth="0.8" />
        </g>
      )}

      {/* B. FIRE TRUCK 🚒 (Width: 9.2px, Length: 23px) */}
      {isFireTruck && (
        <g>
          {/* Heavy Chassis */}
          <rect x="-4.6" y="-11.5" width="9.2" height="23" rx="2" fill="#DC2626" stroke="#991B1B" strokeWidth="0.7" />
          
          {/* Front Chrome Bumper Bullbar */}
          <rect x="-4.2" y="-12.3" width="8.4" height="1.4" rx="0.4" fill="#E2E8F0" stroke="#94A3B8" strokeWidth="0.3" />
          
          {/* Cab Windshield & Roof */}
          <rect x="-3.8" y="-10.5" width="7.6" height="3.8" rx="0.8" fill="#0F172A" opacity="0.9" />
          <rect x="-3" y="-9.2" width="6" height="2.2" fill="#991B1B" opacity="0.7" />

          {/* Side Utility Compartments */}
          <rect x="-4.2" y="-4.5" width="1.2" height="14" fill="#CBD5E1" stroke="#64748B" strokeWidth="0.2" />
          <rect x="3" y="-4.5" width="1.2" height="14" fill="#CBD5E1" stroke="#64748B" strokeWidth="0.2" />

          {/* Roof Extension Rescue Ladder */}
          <rect x="-1.6" y="-5.5" width="3.2" height="15" rx="0.4" fill="#F1F5F9" stroke="#64748B" strokeWidth="0.4" opacity="0.9" />
          {[...Array(5)].map((_, i) => (
            <line key={i} x1="-1.4" y1={-4 + i * 2.8} x2="1.4" y2={-4 + i * 2.8} stroke="#334155" strokeWidth="0.5" />
          ))}

          {/* High-Power Emergency Strobes (Dual Red & Amber) */}
          <circle cx="-3" cy="-6.5" r="1.4" fill="#EF4444" className="animate-ping" style={{ animationDuration: '0.3s' }} />
          <circle cx="-3" cy="-6.5" r="1.0" fill="#EF4444" style={{ filter: 'drop-shadow(0 0 4px #EF4444)' }} />
          <circle cx="3" cy="-6.5" r="1.4" fill="#F59E0B" className="animate-ping" style={{ animationDuration: '0.3s' }} />
          <circle cx="3" cy="-6.5" r="1.0" fill="#F59E0B" style={{ filter: 'drop-shadow(0 0 4px #F59E0B)' }} />

          {/* Headlights & Taillights */}
          <circle cx="-3.4" cy="-11.4" r="0.7" fill="#FEF08A" />
          <circle cx="3.4" cy="-11.4" r="0.7" fill="#FEF08A" />
          <line x1="-3.8" y1="11.2" x2="-1.6" y2="11.2" stroke="#EF4444" strokeWidth="1" />
          <line x1="1.6" y1="11.2" x2="3.8" y2="11.2" stroke="#EF4444" strokeWidth="1" />
        </g>
      )}

      {/* C. POLICE CRUISER 🚓 (Width: 7.2px, Length: 15.5px) */}
      {isPolice && (
        <g>
          {/* Interceptor Body Shell */}
          <path
            d="M -3.4,-7.5 C -3.4,-8.2 -2,-8.5 0,-8.5 C 2,-8.5 3.4,-8.2 3.4,-7.5 L 3.6,6 C 3.6,7 2.4,7.5 0,7.5 C -2.4,7.5 -3.6,7 -3.6,6 Z"
            fill="#0F172A"
            stroke="#334155"
            strokeWidth="0.6"
          />

          {/* Front Bumper Pushbar */}
          <rect x="-2.4" y="-9" width="4.8" height="1" rx="0.3" fill="#E2E8F0" />

          {/* White Doors & Roof */}
          <rect x="-3.4" y="-2.5" width="6.8" height="5.5" fill="#F8FAFC" />

          {/* Front Windshield & Rear Window */}
          <path d="M -2.6,-4.2 L 2.6,-4.2 L 2,-1.5 L -2,-1.5 Z" fill="#020617" opacity="0.9" />
          <path d="M -2.2,2.8 L 2.2,2.8 L 1.8,4.5 L -1.8,4.5 Z" fill="#020617" opacity="0.9" />

          {/* Police Low-Profile Aero LED Lightbar on Roof */}
          <rect x="-2.4" y="-0.4" width="4.8" height="1.5" rx="0.4" fill="#1E293B" stroke="#475569" strokeWidth="0.3" />
          <circle cx="-1.4" cy="0.35" r="1.1" fill="#EF4444" className="animate-ping" style={{ animationDuration: '0.28s' }} />
          <circle cx="-1.4" cy="0.35" r="0.8" fill="#EF4444" style={{ filter: 'drop-shadow(0 0 3px #EF4444)' }} />
          <circle cx="1.4" cy="0.35" r="1.1" fill="#3B82F6" className="animate-ping" style={{ animationDuration: '0.28s' }} />
          <circle cx="1.4" cy="0.35" r="0.8" fill="#38BDF8" style={{ filter: 'drop-shadow(0 0 3px #38BDF8)' }} />

          {/* Headlights & Taillights */}
          <ellipse cx="-2.6" cy="-7.8" rx="0.6" ry="0.4" fill="#FEF08A" style={{ filter: 'drop-shadow(0 0 1.5px #FEF08A)' }} />
          <ellipse cx="2.6" cy="-7.8" rx="0.6" ry="0.4" fill="#FEF08A" style={{ filter: 'drop-shadow(0 0 1.5px #FEF08A)' }} />
          <line x1="-2.8" y1="7.2" x2="-1.2" y2="7.2" stroke="#EF4444" strokeWidth="0.8" />
          <line x1="1.2" y1="7.2" x2="2.8" y2="7.2" stroke="#EF4444" strokeWidth="0.8" />
        </g>
      )}

      {/* D. CITY BUS 🚌 (Width: 8.4px, Length: 21px) */}
      {isBus && (
        <g>
          <rect x="-4.2" y="-10.5" width="8.4" height="21" rx="2" fill={theme.body} stroke={theme.stroke} strokeWidth="0.6" />
          <rect x="-3.5" y="-9.5" width="7" height="3" rx="0.8" fill="#0F172A" opacity="0.9" />
          <line x1="-3.6" y1="-4.5" x2="-3.6" y2="6" stroke="#0F172A" strokeWidth="0.9" />
          <line x1="3.6" y1="-4.5" x2="3.6" y2="6" stroke="#0F172A" strokeWidth="0.9" />
          <rect x="-2.4" y="-2" width="4.8" height="6.5" rx="0.8" fill={theme.roof} opacity="0.6" />
          <circle cx="-3" cy="-10" r="0.6" fill="#FEF08A" />
          <circle cx="3" cy="-10" r="0.6" fill="#FEF08A" />
          <line x1="-3.4" y1="10.2" x2="-1.6" y2="10.2" stroke="#EF4444" strokeWidth="0.9" />
          <line x1="1.6" y1="10.2" x2="3.4" y2="10.2" stroke="#EF4444" strokeWidth="0.9" />
        </g>
      )}

      {/* E. VAN / UTILITY FLEET 🚐 (Width: 7.2px, Length: 16px) */}
      {isVan && (
        <g>
          <rect x="-3.6" y="-8" width="7.2" height="16" rx="1.8" fill={theme.body} stroke={theme.stroke} strokeWidth="0.6" />
          <rect x="-3" y="-6.8" width="6" height="2.8" rx="0.8" fill="#0F172A" opacity="0.9" />
          <rect x="-2.8" y="-2.5" width="5.6" height="8.5" rx="0.8" fill={theme.roof} opacity="0.5" />
          <circle cx="-2.6" cy="-7.6" r="0.6" fill="#FEF08A" />
          <circle cx="2.6" cy="-7.6" r="0.6" fill="#FEF08A" />
          <line x1="-3" y1="7.6" x2="-1.2" y2="7.6" stroke="#EF4444" strokeWidth="0.8" />
          <line x1="1.2" y1="7.6" x2="3" y2="7.6" stroke="#EF4444" strokeWidth="0.8" />
        </g>
      )}

      {/* F. STANDARD SEDAN / PASSENGER CAR 🚗 (Width: 6.8px, Length: 14.8px) */}
      {!isAmbulance && !isFireTruck && !isPolice && !isBus && !isVan && (
        <g>
          {/* Passenger Car Shell */}
          <path
            d="M -3.2,-7 C -3.2,-7.5 -2,-8 0,-8 C 2,-8 3.2,-7.5 3.2,-7 L 3.4,5 C 3.4,6.2 2.2,6.8 0,6.8 C -2.2,6.8 -3.4,6.2 -3.4,5 Z"
            fill={theme.body}
            stroke={theme.stroke}
            strokeWidth="0.6"
          />

          {/* Windshields & Roof Profile */}
          <path d="M -2.4,-3.5 L 2.4,-3.5 L 1.8,-0.5 L -1.8,-0.5 Z" fill="#0F172A" opacity="0.88" />
          <path d="M -2,3.2 L 2,3.2 L 1.8,4.8 L -1.8,4.8 Z" fill="#0F172A" opacity="0.88" />
          <path d="M -1.8,-0.5 L 1.8,-0.5 L 2,3.2 L -2,3.2 Z" fill="rgba(255, 255, 255, 0.2)" />

          {/* Headlights (Front Beams) */}
          <ellipse cx="-2.5" cy="-7.2" rx="0.6" ry="0.4" fill="#FEF08A" style={{ filter: 'drop-shadow(0 0 1.2px #FEF08A)' }} />
          <ellipse cx="2.5" cy="-7.2" rx="0.6" ry="0.4" fill="#FEF08A" style={{ filter: 'drop-shadow(0 0 1.2px #FEF08A)' }} />

          {/* Taillights / Brake Lights (Bright Red when stopped) */}
          <line
            x1="-2.8"
            y1="6.4"
            x2="-1.2"
            y2="6.4"
            stroke="#EF4444"
            strokeWidth={isStopped ? "1.3" : "0.8"}
            style={isStopped ? { filter: 'drop-shadow(0 0 2px #EF4444)' } : undefined}
          />
          <line
            x1="1.2"
            y1="6.4"
            x2="2.8"
            y2="6.4"
            stroke="#EF4444"
            strokeWidth={isStopped ? "1.3" : "0.8"}
            style={isStopped ? { filter: 'drop-shadow(0 0 2px #EF4444)' } : undefined}
          />

          {/* Generic Emergency Siren */}
          {isGenericEmergency && (
            <circle cx="0" cy="1" r="1.4" fill="#3B82F6" className="animate-ping" />
          )}
        </g>
      )}

      {/* ==================================================================== */}
      {/* 5. DYNAMIC TURN BLINKER LIGHTS */}
      {/* ==================================================================== */}
      {turn_signal === 'left' && (
        <g>
          <circle cx={isBus ? "-4.2" : "-3.2"} cy={isBus ? "-10" : "-7"} r="1" fill="#F59E0B" className="animate-ping" style={{ animationDuration: '0.5s' }} />
          <circle cx={isBus ? "-4.2" : "-3.2"} cy={isBus ? "-10" : "-7"} r="0.7" fill="#F59E0B" />
          <circle cx={isBus ? "-4.2" : "-3.2"} cy={isBus ? "10" : "6"} r="0.9" fill="#F59E0B" className="animate-ping" style={{ animationDuration: '0.5s' }} />
          <circle cx={isBus ? "-4.2" : "-3.2"} cy={isBus ? "10" : "6"} r="0.6" fill="#F59E0B" />
        </g>
      )}

      {turn_signal === 'right' && (
        <g>
          <circle cx={isBus ? "4.2" : "3.2"} cy={isBus ? "-10" : "-7"} r="1" fill="#F59E0B" className="animate-ping" style={{ animationDuration: '0.5s' }} />
          <circle cx={isBus ? "4.2" : "3.2"} cy={isBus ? "-10" : "-7"} r="0.7" fill="#F59E0B" />
          <circle cx={isBus ? "4.2" : "3.2"} cy={isBus ? "10" : "6"} r="0.9" fill="#F59E0B" className="animate-ping" style={{ animationDuration: '0.5s' }} />
          <circle cx={isBus ? "4.2" : "3.2"} cy={isBus ? "10" : "6"} r="0.6" fill="#F59E0B" />
        </g>
      )}
    </g>
  );
});
