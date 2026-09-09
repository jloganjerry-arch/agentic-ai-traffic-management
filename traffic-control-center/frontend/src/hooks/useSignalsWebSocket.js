import { useState, useEffect, useRef } from 'react';
import { wsSignals } from '../api/websocket';

export function useSignalsWebSocket(initialSignals = []) {
  const [signals, setSignals] = useState(initialSignals);
  const lastSimTimeRef = useRef(-1);
  const lastPhaseIdRef = useRef(-1);

  useEffect(() => {
    if (initialSignals.length > 0 && signals.length === 0) {
      setSignals(initialSignals);
    }
  }, [initialSignals]);

  // Sync state on WebSocket events from /ws/signals
  useEffect(() => {
    const unsubscribe = wsSignals.subscribe((data) => {
      if (
        data.event === 'signal_state_sync' ||
        data.event === 'signal_phase_change' ||
        data.event === 'SIGNAL_UPDATE'
      ) {
        // Monotonically increasing sequence check to reject stale/out-of-order WS updates
        const incomingSimTime = data.simulation_time ?? (data.signals && data.signals[0]?.simulation_time);
        const incomingPhaseId = data.phase_id ?? (data.signals && data.signals[0]?.phase_id);

        if (
          incomingSimTime !== undefined &&
          incomingPhaseId !== undefined &&
          incomingSimTime < lastSimTimeRef.current &&
          incomingPhaseId === lastPhaseIdRef.current
        ) {
          console.warn(`[WS /ws/signals] Rejected stale frame (sim_time: ${incomingSimTime} < ${lastSimTimeRef.current})`);
          return;
        }

        if (incomingSimTime !== undefined) {
          lastSimTimeRef.current = incomingSimTime;
        }
        if (incomingPhaseId !== undefined) {
          lastPhaseIdRef.current = incomingPhaseId;
        }

        if (Array.isArray(data.signals)) {
          // STEP 9: Log SIGNAL_UPDATE details for verification
          data.signals.forEach((sig) => {
            console.log(
              `[SIGNAL_UPDATE] signal_id=${sig.signal_id} phase_id=${sig.phase_id ?? incomingPhaseId} ` +
              `remaining_time=${sig.remaining_time ?? sig.timer_remaining} simulation_time=${sig.simulation_time ?? incomingSimTime} ` +
              `decision_id=${sig.decision_id ?? data.decision_id}`
            );
          });

          // STEP 5 & 6 & 7: Update signal state using signal_id + phase_id as key.
          // Maintain active phase countdown without resetting timer on mid-phase telemetry updates.
          setSignals((prevSignals) => {
            const prevMap = new Map((prevSignals || []).map((s) => [s.signal_id, s]));

            return data.signals.map((newSig) => {
              const prevSig = prevMap.get(newSig.signal_id);
              const pId = newSig.phase_id ?? incomingPhaseId;

              // Authoritative remaining time sent directly by backend Signal Controller
              const authRemaining = newSig.remaining_time !== undefined
                ? newSig.remaining_time
                : (newSig.timer_remaining !== undefined ? newSig.timer_remaining : 0);

              const isSamePhase =
                prevSig &&
                (prevSig.phase_id === pId || (pId !== undefined && prevSig.phase_id === undefined)) &&
                prevSig.state === newSig.state;

              if (isSamePhase) {
                return {
                  ...newSig,
                  phase_id: pId,
                  timer_remaining: authRemaining,
                  adaptive_action: newSig.adaptive_action || prevSig.adaptive_action || "NOMINAL",
                  adaptive_reason: newSig.adaptive_reason || prevSig.adaptive_reason || "",
                  adaptive_status: data.adaptive_status || newSig.adaptive_status,
                };
              } else {
                // NEW PHASE: Phase transition occurred! Initialize new phase timer
                console.log(
                  `[PHASE TRANSITION] ${newSig.signal_id} (${newSig.direction}): ` +
                  `${prevSig?.state || 'INIT'} -> ${newSig.state} (phase ${pId}) | remaining: ${authRemaining}s`
                );
                return {
                  ...newSig,
                  phase_id: pId,
                  timer_remaining: authRemaining,
                  adaptive_action: newSig.adaptive_action || "NOMINAL",
                  adaptive_reason: newSig.adaptive_reason || "Phase Transition",
                  adaptive_status: data.adaptive_status || newSig.adaptive_status,
                };
              }
            });
          });
        }
      }
    });

    return () => unsubscribe();
  }, []);

  // Local 1-second interval tick for smooth countdown timer rendering ONLY
  // Must NOT trigger phase transitions or alter signal states independently
  useEffect(() => {
    const interval = setInterval(() => {
      setSignals((prevSignals) =>
        prevSignals.map((sig) => ({
          ...sig,
          timer_remaining: Math.max(0, (sig.timer_remaining || 0) - 1),
        }))
      );
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return signals;
}
