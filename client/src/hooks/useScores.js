import { useEffect, useState } from "react";
import { api } from "../lib/api";

/** A race's driver + constructor scores. Only fetches when `enabled`. */
export function useScores(raceId, enabled) {
  const [state, setState] = useState({ drivers: [], constructors: [], loading: enabled, error: null });

  useEffect(() => {
    if (!enabled) return;
    let active = true;
    setState((s) => ({ ...s, loading: true, error: null }));
    Promise.all([
      api.get(`/scores/${raceId}/drivers`, { auth: false }),
      api.get(`/scores/${raceId}/constructors`, { auth: false }),
    ])
      .then(([d, c]) => active && setState({ drivers: d.scores, constructors: c.scores, loading: false, error: null }))
      .catch((err) => active && setState({ drivers: [], constructors: [], loading: false, error: err.message }));
    return () => {
      active = false;
    };
  }, [raceId, enabled]);

  return state;
}
