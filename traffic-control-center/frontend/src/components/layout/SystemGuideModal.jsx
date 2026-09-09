import React, { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { 
  BookOpen, 
  X, 
  Zap, 
  ShieldCheck, 
  ArrowRightLeft, 
  Activity, 
  Siren, 
  Sparkles, 
  Cpu, 
  CheckCircle2, 
  AlertTriangle, 
  FileText,
  BarChart3,
  ShieldAlert
} from 'lucide-react';

export function SystemGuideModal({ isOpen, onClose }) {
  const [activeTab, setActiveTab] = useState('agents');

  // Close on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };
    if (isOpen) {
      window.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'auto';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const tabs = [
    { id: 'agents', label: '1. 5-Agent Architecture', icon: Activity },
    { id: 'adaptive', label: '2. Adaptive Timing & GLIDE', icon: Sparkles },
    { id: 'modes', label: '3. Phasing & Yellow Clearance', icon: ArrowRightLeft },
    { id: 'emergency', label: '4. Emergency Preemption', icon: Siren },
    { id: 'scenarios', label: '5. Scenarios & Hardware MQTT', icon: Cpu },
  ];

  return createPortal(
    <div 
      className="fixed inset-0 z-[9999] bg-black/80 backdrop-blur-md flex items-center justify-center p-3 sm:p-6 overflow-y-auto animate-fadeIn"
      onClick={onClose}
    >
      <div 
        className="relative w-full max-w-4xl max-h-[88vh] my-auto flex flex-col bg-[#0B1224] border border-cyan-500/40 rounded-2xl shadow-[0_0_60px_rgba(6,182,212,0.35)] overflow-hidden font-sans"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Modal Top Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-[#0F172A] shrink-0">
          <div className="flex items-center space-x-3.5">
            <div className="p-2.5 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-400 shadow-[0_0_12px_rgba(6,182,212,0.2)]">
              <BookOpen className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-base sm:text-lg font-bold text-white tracking-wide">
                  Agentic AI Traffic Management — Master System Guide
                </h2>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-cyan-950 border border-cyan-700 text-cyan-300 font-bold whitespace-nowrap">
                  PROJECT SPEC v4.2
                </span>
              </div>
              <p className="text-xs text-slate-400 mt-0.5">
                Operating manual for AI Adaptive Timing, GLIDE extensions, 4-way intersection sequencing, and safety gates.
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            type="button"
            className="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800/80 border border-slate-800 hover:border-slate-700 transition cursor-pointer shrink-0 ml-2"
            title="Close Guide (Esc)"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tab Navigation Bar */}
        <div className="flex overflow-x-auto border-b border-slate-800/80 bg-slate-950/80 px-4 py-2.5 gap-2 scrollbar-thin shrink-0">
          {tabs.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              type="button"
              onClick={() => setActiveTab(id)}
              className={`flex items-center space-x-2 px-3.5 py-2 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${
                activeTab === id
                  ? 'bg-cyan-500/20 text-cyan-200 border border-cyan-500/50 shadow-[0_0_14px_rgba(6,182,212,0.25)] font-bold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900 border border-transparent'
              }`}
            >
              <Icon className="w-4 h-4 shrink-0" />
              <span>{label}</span>
            </button>
          ))}
        </div>

        {/* Modal Scrollable Content Body with Clean Spacing & Alignment */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6 text-slate-300 text-xs leading-relaxed scrollbar-thin scroll-pt-4">
          
          {/* TAB 1: 5-AGENT MASTER ARCHITECTURE */}
          {activeTab === 'agents' && (
            <div className="space-y-4 animate-fadeIn">
              <div className="bg-slate-900/90 border border-slate-800/90 rounded-2xl p-4.5 space-y-2">
                <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                  <Activity className="w-4 h-4 text-cyan-400" />
                  <span>The 5-Agent Autonomous Pipeline (Evaluated Every 3 Seconds)</span>
                </h3>
                <p className="text-slate-300 leading-normal text-[12px]">
                  The system runs a strict pipeline of specialized micro-agents where each stage has a distinct cognitive role. Decisions flow sequentially from raw telemetry to physical hardware actuation without bypassing safety constraints.
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Agent 1 */}
                <div className="bg-slate-900/70 border border-slate-800/90 rounded-2xl p-4 space-y-2.5 hover:border-cyan-500/40 transition-all">
                  <div className="flex items-center justify-between gap-2 flex-wrap pb-2 border-b border-white/5">
                    <span className="font-bold text-cyan-300 text-sm flex items-center space-x-2">
                      <Activity className="w-4 h-4 text-cyan-400 shrink-0" />
                      <span>1. Traffic Monitoring Agent</span>
                    </span>
                    <span className="text-[10px] font-mono bg-cyan-950/80 text-cyan-300 px-2 py-0.5 rounded-md border border-cyan-800 font-bold whitespace-nowrap">
                      Stage: Ingestion
                    </span>
                  </div>
                  <p className="text-slate-300 text-[12px] leading-relaxed">
                    Extracts TraCI induction loop telemetry: approach volume, vehicle queue length in meters, speed distribution, and emergency vehicle detection.
                  </p>
                </div>

                {/* Agent 2 */}
                <div className="bg-slate-900/70 border border-slate-800/90 rounded-2xl p-4 space-y-2.5 hover:border-emerald-500/40 transition-all">
                  <div className="flex items-center justify-between gap-2 flex-wrap pb-2 border-b border-white/5">
                    <span className="font-bold text-emerald-300 text-sm flex items-center space-x-2">
                      <BarChart3 className="w-4 h-4 text-emerald-400 shrink-0" />
                      <span>2. Traffic Analysis Agent</span>
                    </span>
                    <span className="text-[10px] font-mono bg-emerald-950/80 text-emerald-300 px-2 py-0.5 rounded-md border border-emerald-800 font-bold whitespace-nowrap">
                      Stage: Analytics
                    </span>
                  </div>
                  <p className="text-slate-300 text-[12px] leading-relaxed">
                    Calculates density per corridor (veh/km), determines Level of Service (LOS A–F), and pinpoints congested bottleneck directions.
                  </p>
                </div>

                {/* Agent 3 */}
                <div className="bg-slate-900/70 border border-slate-800/90 rounded-2xl p-4 space-y-2.5 hover:border-amber-500/40 transition-all">
                  <div className="flex items-center justify-between gap-2 flex-wrap pb-2 border-b border-white/5">
                    <span className="font-bold text-amber-300 text-sm flex items-center space-x-2">
                      <Sparkles className="w-4 h-4 text-amber-400 shrink-0" />
                      <span>3. Signal Optimization Agent</span>
                    </span>
                    <span className="text-[10px] font-mono bg-amber-950/80 text-amber-300 px-2 py-0.5 rounded-md border border-amber-800 font-bold whitespace-nowrap">
                      Stage: Optimization
                    </span>
                  </div>
                  <p className="text-slate-300 text-[12px] leading-relaxed">
                    Computes adaptive green times (15s–75s) using multi-factor demand scoring: 35% Density + 30% Queue + 20% Wait + 15% Volume with congested priority boosts.
                  </p>
                </div>

                {/* Agent 4 */}
                <div className="bg-slate-900/70 border border-slate-800/90 rounded-2xl p-4 space-y-2.5 hover:border-purple-500/40 transition-all">
                  <div className="flex items-center justify-between gap-2 flex-wrap pb-2 border-b border-white/5">
                    <span className="font-bold text-purple-300 text-sm flex items-center space-x-2">
                      <ShieldCheck className="w-4 h-4 text-purple-400 shrink-0" />
                      <span>4. Supervisor Agent</span>
                    </span>
                    <span className="text-[10px] font-mono bg-purple-950/80 text-purple-300 px-2 py-0.5 rounded-md border border-purple-800 font-bold whitespace-nowrap">
                      Stage: Policy & Fairness
                    </span>
                  </div>
                  <p className="text-slate-300 text-[12px] leading-relaxed">
                    Enforces regulatory bounds: Min Green (10s), Max Green (90s), and starvation prevention override (opposing red wait &lt; 90s).
                  </p>
                </div>

                {/* Agent 5 */}
                <div className="bg-gradient-to-r from-rose-950/30 to-slate-900/80 border border-rose-500/30 rounded-2xl p-4 space-y-2.5 md:col-span-2 hover:border-rose-500/60 transition-all">
                  <div className="flex items-center justify-between gap-2 flex-wrap pb-2 border-b border-white/5">
                    <span className="font-bold text-rose-300 text-sm flex items-center space-x-2">
                      <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
                      <span>5. Traffic Safety Agent</span>
                    </span>
                    <span className="text-[10px] font-mono bg-rose-950/90 text-rose-200 px-2 py-0.5 rounded-md border border-rose-800 font-bold whitespace-nowrap">
                      Stage: Physical Safety Gate
                    </span>
                  </div>
                  <p className="text-slate-300 text-[12px] leading-relaxed">
                    The ultimate safety gate. Verifies mutual exclusion (no conflicting greens), enforces mandatory 3.0s Yellow + 2.0s All-Red clearance intervals, and confirms dilemma-zone vehicle stopping distances.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* TAB 2: ADAPTIVE TIMING & GLIDE */}
          {activeTab === 'adaptive' && (
            <div className="space-y-4 animate-fadeIn">
              <div className="bg-slate-900/90 border border-slate-800/90 rounded-2xl p-4.5 space-y-2">
                <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                  <Sparkles className="w-4 h-4 text-amber-400" />
                  <span>AI Adaptive Signal Timing & GLIDE Dynamic Extension Engine</span>
                </h3>
                <p className="text-slate-300 text-[12px] leading-relaxed">
                  Adaptive Timing actively scales green light duration based on live vehicle demand, while GLIDE (Green Light Intelligent Dynamic Extension) prevents cut-offs by dynamically extending green times when vehicle platoons are detected.
                </p>
              </div>

              <div className="space-y-3.5">
                <div className="border border-slate-800 rounded-2xl p-4 bg-slate-900/60 space-y-2.5">
                  <h4 className="font-bold text-cyan-300 text-xs">How Adaptive Timing Works</h4>
                  <ul className="list-disc list-inside space-y-1.5 text-slate-300 text-[12px] leading-relaxed">
                    <li><strong className="text-white">Multi-Factor Scoring:</strong> Each approach is continuously scored based on Density (35%), Queue Length (30%), Estimated Waiting Time (20%), and Vehicle Count (15%).</li>
                    <li><strong className="text-white">Congestion Priority Boost:</strong> When queue length exceeds 25m or density exceeds 35 veh/km, the approach receives a +0.25 priority boost (+15s green allocation).</li>
                    <li><strong className="text-white">Toggle Between Adaptive vs Fixed:</strong> Click the <code className="bg-slate-950 px-2 py-0.5 rounded border border-slate-800 text-cyan-300">Adaptive GLIDE: [● ENABLED / ○ FIXED]</code> button in the Signal Grid to switch instantly between AI Dynamic Adaptive timing and Fixed 30s schedules.</li>
                  </ul>
                </div>

                <div className="border border-slate-800 rounded-2xl p-4 bg-slate-900/60 space-y-2.5">
                  <h4 className="font-bold text-emerald-300 text-xs">GLIDE Dynamic Extension Parameters</h4>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 text-[12px]">
                    <div className="bg-slate-950/90 p-3.5 rounded-xl border border-slate-800">
                      <strong className="text-emerald-400 block mb-1 font-mono">Platoon Extension Step (+2s to +8s)</strong>
                      <span className="text-slate-300">When an approaching convoy or platoon of 2+ vehicles is detected near the end of green time (&lt;= 4s remaining), GLIDE injects dynamic green seconds to let the platoon clear without braking.</span>
                    </div>
                    <div className="bg-slate-950/90 p-3.5 rounded-xl border border-slate-800">
                      <strong className="text-cyan-400 block mb-1 font-mono">Gap-Out Clearance Threshold (1.8s to 3.5s)</strong>
                      <span className="text-slate-300">If headway between trailing vehicles exceeds this gap-out threshold, the controller yields green early to serve waiting cross traffic, maximizing intersection efficiency.</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* TAB 3: PHASING & YELLOW CLEARANCE */}
          {activeTab === 'modes' && (
            <div className="space-y-4 animate-fadeIn">
              <div className="bg-slate-900/90 border border-slate-800/90 rounded-2xl p-4.5 space-y-2">
                <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                  <ArrowRightLeft className="w-4 h-4 text-cyan-400" />
                  <span>Signal Phasing Modes & The 3-Second Yellow Clearance Sequence</span>
                </h3>
                <p className="text-slate-300 text-[12px] leading-relaxed">
                  The system supports two distinct sequencing modes, both governed by mandatory yellow clearance intervals.
                </p>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="border border-cyan-500/30 rounded-2xl p-4.5 bg-slate-900/60 space-y-2.5">
                  <div className="flex items-center justify-between pb-2 border-b border-white/5">
                    <span className="font-bold text-cyan-400 text-xs">Paired Corridors (2-Phase)</span>
                    <span className="text-[10px] font-mono bg-cyan-950 text-cyan-300 px-2 py-0.5 rounded border border-cyan-800 font-bold">[N+S ⇄ E+W]</span>
                  </div>
                  <p className="text-[12px] text-slate-300 leading-relaxed">
                    Dual-ring synchronized green waves. North and South flow simultaneously, followed by East and West. Ideal for heavy straight-line arterial corridors.
                  </p>
                  <div className="bg-slate-950 p-2.5 rounded-xl font-mono text-[11px] text-cyan-300 border border-slate-800">
                    NS GREEN (35s) ➔ NS YELLOW (3s) ➔ ALL RED ➔ EW GREEN (25s) ➔ EW YELLOW (3s)
                  </div>
                </div>

                <div className="border border-emerald-500/30 rounded-2xl p-4.5 bg-slate-900/60 space-y-2.5">
                  <div className="flex items-center justify-between pb-2 border-b border-white/5">
                    <span className="font-bold text-emerald-400 text-xs">One-by-One (4-Phase Isolated)</span>
                    <span className="text-[10px] font-mono bg-emerald-950 text-emerald-300 px-2 py-0.5 rounded border border-emerald-800 font-bold">[N ➔ E ➔ S ➔ W]</span>
                  </div>
                  <p className="text-[12px] text-slate-300 leading-relaxed">
                    Isolated single-approach green sequencing. The active green road can safely turn left, go straight, or turn right while all other 3 approaches hold solid RED.
                  </p>
                  <div className="bg-slate-950 p-2.5 rounded-xl font-mono text-[11px] text-emerald-300 border border-slate-800">
                    N GREEN (35s) ➔ N YELLOW (3s) ➔ E GREEN (25s) ➔ E YELLOW (3s) ➔ ...
                  </div>
                </div>
              </div>

              <div className="border border-amber-500/40 rounded-2xl p-4.5 bg-amber-950/15 space-y-2.5">
                <h4 className="font-bold text-amber-300 text-xs flex items-center space-x-2 pb-1 border-b border-amber-500/20">
                  <AlertTriangle className="w-4 h-4 text-amber-400" />
                  <span>Authoritative 3-Second Yellow & Dilemma-Zone Clearance</span>
                </h4>
                <p className="text-[12px] text-slate-300 leading-relaxed">
                  The dashboard never jumps directly from Green to Red. An explicit 3-second amber clearance frame is broadcast over WebSockets and rendered with amber glow (<code className="text-amber-400 font-mono">#F59E0B</code>) and physical amber LED illumination on the Signal Grid and 4-way Intersection Visualizer.
                </p>
                <p className="text-[12px] text-slate-300 leading-relaxed">
                  <strong className="text-white">Dilemma-Zone Kinematics:</strong> Vehicles within 35px of the stop line continue forward to clear the junction safely; trailing vehicles decelerate smoothly to a full stop before the stop bar.
                </p>
              </div>
            </div>
          )}

          {/* TAB 4: EMERGENCY GREEN PREEMPTION */}
          {activeTab === 'emergency' && (
            <div className="space-y-4 animate-fadeIn">
              <div className="bg-slate-900/90 border border-slate-800/90 rounded-2xl p-4.5 space-y-2">
                <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                  <Siren className="w-4 h-4 text-rose-400" />
                  <span>Emergency Vehicle Green Corridor Preemption</span>
                </h3>
                <p className="text-slate-300 text-[12px] leading-relaxed">
                  Instant priority override granting zero-delay green waves to critical first-responder vehicles.
                </p>
              </div>

              <div className="space-y-3.5">
                <div className="border border-slate-800 rounded-2xl p-4 bg-slate-900/60 space-y-3">
                  <h4 className="font-bold text-rose-300 text-xs">Supported Emergency Vehicle Classes</h4>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5 text-center text-[12px]">
                    <div className="bg-rose-950/40 border border-rose-800/60 p-3.5 rounded-xl">
                      <strong className="text-rose-300 block mb-1 text-sm">🚑 Ambulance</strong>
                      <span className="text-slate-400">High-speed medical priority corridor.</span>
                    </div>
                    <div className="bg-rose-950/40 border border-rose-800/60 p-3.5 rounded-xl">
                      <strong className="text-rose-300 block mb-1 text-sm">🚒 Fire Truck</strong>
                      <span className="text-slate-400">Heavy vehicle emergency wave.</span>
                    </div>
                    <div className="bg-rose-950/40 border border-rose-800/60 p-3.5 rounded-xl">
                      <strong className="text-rose-300 block mb-1 text-sm">🚓 Police Cruiser</strong>
                      <span className="text-slate-400">Tactical rapid response preemption.</span>
                    </div>
                  </div>
                </div>

                <div className="border border-slate-800 rounded-2xl p-4 bg-slate-900/60 space-y-2.5 text-[12px]">
                  <h4 className="font-bold text-white text-xs">How to Operate Emergency Preemption:</h4>
                  <ol className="list-decimal list-inside space-y-1.5 text-slate-300 leading-relaxed">
                    <li>Navigate to the <strong className="text-cyan-300">Emergency Vehicle Green Corridor</strong> panel or use the <strong className="text-rose-400">Emergency HUD</strong> at the top of the Command Rail.</li>
                    <li>Select the emergency vehicle type (Ambulance, Fire Truck, or Police).</li>
                    <li>Choose the target corridor direction (North-South or East-West).</li>
                    <li>Click <strong className="text-rose-400">ACTIVATE GREEN CORRIDOR</strong>. The visualizer will render illuminated neon-green runway arrows along the priority road and red laser stop bars holding cross traffic.</li>
                    <li>Click <strong className="text-emerald-400">RESUME AI ADAPTIVE MODE</strong> to restore autonomous multi-agent balancing once the vehicle has passed.</li>
                  </ol>
                </div>
              </div>
            </div>
          )}

          {/* TAB 5: SCENARIOS & HARDWARE MQTT */}
          {activeTab === 'scenarios' && (
            <div className="space-y-4 animate-fadeIn">
              <div className="bg-slate-900/90 border border-slate-800/90 rounded-2xl p-4.5 space-y-2">
                <h3 className="text-sm font-bold text-white flex items-center space-x-2">
                  <Cpu className="w-4 h-4 text-indigo-400" />
                  <span>Stress-Testing Scenarios & Hardware Microcontroller Actuation</span>
                </h3>
                <p className="text-slate-300 text-[12px] leading-relaxed">
                  Simulate extreme conditions and verify end-to-end hardware execution across MQTT brokers and ESP32 nodes.
                </p>
              </div>

              <div className="space-y-3.5">
                <div className="border border-slate-800 rounded-2xl p-4 bg-slate-900/60 space-y-3">
                  <h4 className="font-bold text-cyan-300 text-xs">Real-Time Scenario Injector</h4>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-[12px]">
                    <div className="bg-slate-950/90 p-3 rounded-xl border border-slate-800">
                      <strong className="text-amber-400 block mb-1">⚡ Rush Hour Surge</strong>
                      <span className="text-slate-300">Surges incoming vehicle flow by +80% to test whether the Optimization Agent dynamically widens green allocations.</span>
                    </div>
                    <div className="bg-slate-950/90 p-3 rounded-xl border border-slate-800">
                      <strong className="text-rose-400 block mb-1">⚠️ Accident Blockage</strong>
                      <span className="text-slate-300">Stalls a vehicle in Lane 1 with warning flashers, forcing traffic to merge left into Lane 2.</span>
                    </div>
                    <div className="bg-slate-950/90 p-3 rounded-xl border border-slate-800">
                      <strong className="text-blue-400 block mb-1">🌧️ Weather Hazard</strong>
                      <span className="text-slate-300">Renders dynamic rain streaks, reduces road surface friction, and decreases safe vehicle speeds by 40%.</span>
                    </div>
                  </div>
                </div>

                <div className="border border-slate-800 rounded-2xl p-4 bg-slate-900/60 space-y-2.5">
                  <h4 className="font-bold text-indigo-300 text-xs">Hardware MQTT Actuation Architecture</h4>
                  <p className="text-[12px] text-slate-300 leading-relaxed">
                    The backend publishes authorized phase decisions and second-by-second signal states to an active Mosquitto MQTT broker on port 1883:
                  </p>
                  <div className="bg-slate-950/90 p-3.5 rounded-xl font-mono text-[11px] space-y-1.5 text-slate-300 border border-slate-800">
                    <div><strong className="text-cyan-400">traffic/signal:</strong> Authoritative live phase command (e.g. NS_GREEN, NS_YELLOW, ALL_RED)</div>
                    <div><strong className="text-emerald-400">traffic/signals/control:</strong> Multi-approach JSON state matrix and durations</div>
                    <div><strong className="text-amber-400">traffic/signals/status/{'{id}'}:</strong> Per-head telemetry for SIG-N1, SIG-S1, SIG-E1, SIG-W1</div>
                    <div><strong className="text-indigo-400">traffic/esp32/ack:</strong> Microcontroller ACK response verifying physical hardware latching</div>
                  </div>
                </div>
              </div>
            </div>
          )}

        </div>

        {/* Modal Bottom Footer with Clean Responsive Alignment */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 px-6 py-4 border-t border-slate-800 bg-[#0F172A] text-xs shrink-0">
          <div className="flex items-center space-x-2 text-slate-400 overflow-hidden w-full sm:w-auto">
            <FileText className="w-4 h-4 text-cyan-400 shrink-0" />
            <span className="truncate">Master PDF Guide: <code className="text-cyan-300 font-mono bg-slate-950 px-2 py-0.5 rounded border border-slate-800 text-[11px]">AGENTIC_AI_TRAFFIC_MANAGEMENT_MASTER_GUIDE.pdf</code></span>
          </div>
          <button
            onClick={onClose}
            type="button"
            className="w-full sm:w-auto px-6 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-slate-950 font-bold text-xs tracking-wider transition-all shadow-[0_0_15px_rgba(6,182,212,0.35)] cursor-pointer shrink-0"
          >
            Close Guide
          </button>
        </div>
      </div>
    </div>,
    document.body
  );
}
