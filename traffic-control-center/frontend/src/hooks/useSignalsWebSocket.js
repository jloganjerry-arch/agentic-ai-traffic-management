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

              // Compute authoritative remaining time from phase_end_time & simulation_time if available
              let calcRemaining = newSig.remaining_time ?? newSig.timer_remaining ?? 0;
              if (
                newSig.phase_end_time !== undefined &&
                newSig.simulation_time !== undefined &&
                newSig.phase_end_time > 0
              ) {
                calcRemaining = Math.max(0, Math.round(newSig.phase_end_time - newSig.simulation_time));
              }

              const isSamePhase =
                prevSig &&
                (prevSig.phase_id === pId || (pId !== undefined && prevSig.phase_id === undefined)) &&
                prevSig.state === newSig.state;

              if (isSamePhase) {
                // SAME PHASE: Smoothly preserve local countdown unless drift > 2s
                const activeLocalTimer = prevSig.timer_remaining ?? calcRemaining;
                const finalTimer = Math.abs(activeLocalTimer - calcRemaining) <= 2 ? activeLocalTimer : calcRemaining;

                return {
                  ...newSig,
                  phase_id: pId,
                  timer_remaining: finalTimer,
                };
              } else {
                // NEW PHASE: Phase transition occurred! Initialize new phase timer
                console.log(
                  `[PHASE TRANSITION] ${newSig.signal_id} (${newSig.direction}): ` +
                  `${prevSig?.state || 'INIT'} -> ${newSig.state} (phase ${pId}) | remaining: ${calcRemaining}s`
                );
                return {
                  ...newSig,
                  phase_id: pId,
                  timer_remaining: calcRemaining,
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
