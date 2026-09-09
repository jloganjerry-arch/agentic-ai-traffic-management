import React from 'react';
import { createPortal } from 'react-dom';
import { X, Car, Gauge, Navigation, Compass, Clock, MapPin } from 'lucide-react';

/**
 * VehicleDetailModal - Slide-over / Popup inspector modal for selected SUMO vehicle telemetry.
 */
export function VehicleDetailModal({ vehicle, onClose }) {
  if (!vehicle) return null;

  const {
    id = 'veh_unknown',
    speed_kmh = 0,
    waiting_time_s = 0,
    vehicle_type = 'sedan',
    direction = 'North',
    lane_id = 'lane_1',
    status = 'Moving',
    x = 0,
    y = 0,
    angle = 0
  } = vehicle;

  return createPortal(
    <div 
      className="fixed inset-0 z-[9999] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn"
      onClick={onClose}
    >
      <div 
        className="bg-slate-900 border border-cyan-500/30 rounded-2xl p-5 w-full max-w-md shadow-2xl space-y-4 font-mono text-slate-200 relative my-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-slate-800 pb-3">
          <div className="flex items-center space-x-2.5">
            <div className="p-2 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400">
              <Car className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                <span>{id}</span>
                <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                  status === 'Queued' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30'
                }`}>
                  {status}
                </span>
              </h3>
              <p className="text-[11px] text-slate-400">Live SUMO TraCI Telemetry Entity</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-slate-800 text-slate-400 hover:text-white transition"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Telemetry Metrics Grid */}
        <div className="grid grid-cols-2 gap-3 text-xs">
          {/* Speed */}
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80">
            <span className="text-slate-400 text-[11px] flex items-center space-x-1.5 mb-1">
              <Gauge className="w-3.5 h-3.5 text-cyan-400" />
              <span>Current Speed</span>
            </span>
            <strong className="text-lg font-bold text-white">{speed_kmh} <span className="text-xs text-slate-400 font-normal">km/h</span></strong>
          </div>

          {/* Direction & Approach */}
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80">
            <span className="text-slate-400 text-[11px] flex items-center space-x-1.5 mb-1">
              <Navigation className="w-3.5 h-3.5 text-emerald-400" />
              <span>Approach</span>
            </span>
            <strong className="text-sm font-bold text-emerald-400">{direction}</strong>
          </div>

          {/* Lane ID */}
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80">
            <span className="text-slate-400 text-[11px] flex items-center space-x-1.5 mb-1">
              <MapPin className="w-3.5 h-3.5 text-purple-400" />
              <span>Lane Segment</span>
            </span>
            <span className="text-xs font-semibold text-slate-200">{lane_id}</span>
          </div>

          {/* Waiting Time */}
          <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80">
            <span className="text-slate-400 text-[11px] flex items-center space-x-1.5 mb-1">
              <Clock className="w-3.5 h-3.5 text-amber-400" />
              <span>Wait Time</span>
            </span>
            <strong className="text-sm font-bold text-amber-300">{waiting_time_s} <span className="text-xs text-slate-400 font-normal">s</span></strong>
          </div>
        </div>

        {/* Spatial Coordinates & Heading */}
        <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80 space-y-2 text-xs">
          <div className="flex justify-between items-center text-slate-400 text-[11px]">
            <span className="flex items-center space-x-1">
              <Compass className="w-3.5 h-3.5 text-cyan-400" />
              <span>Heading Angle:</span>
            </span>
            <strong className="text-slate-200">{angle}°</strong>
          </div>
          <div className="flex justify-between items-center text-slate-400 text-[11px]">
            <span>Planned Maneuver:</span>
            <strong className="text-cyan-300 font-semibold">{vehicle.maneuver_label || vehicle.maneuver || 'Straight'}</strong>
          </div>
          <div className="flex justify-between items-center text-slate-400 text-[11px]">
            <span>Target Destination:</span>
            <span className="text-emerald-400 font-bold">{vehicle.destination || 'Exit Corridor'}</span>
          </div>
          <div className="flex justify-between items-center text-slate-400 text-[11px]">
            <span>Turn Signal Blinker:</span>
            <span className={vehicle.turn_signal && vehicle.turn_signal !== 'none' ? 'text-amber-400 font-bold uppercase' : 'text-slate-500'}>
              {vehicle.turn_signal && vehicle.turn_signal !== 'none' ? `${vehicle.turn_signal} (Active)` : 'Inactive'}
            </span>
          </div>
          <div className="flex justify-between items-center text-slate-400 text-[11px]">
            <span>SUMO Coordinates (X, Y):</span>
            <strong className="text-slate-200 font-mono">({typeof x === 'number' ? x.toFixed(1) : x}, {typeof y === 'number' ? y.toFixed(1) : y})</strong>
          </div>
          <div className="flex justify-between items-center text-slate-400 text-[11px]">
            <span>Vehicle Type Category:</span>
            <span className="text-cyan-300 capitalize font-bold">{vehicle_type}</span>
          </div>
        </div>

        {/* Footer Close Button */}
        <div className="pt-1">
          <button
            onClick={onClose}
            className="w-full py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold transition"
          >
            Close Telemetry Inspector
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
