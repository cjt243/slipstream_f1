import { useEffect, useState } from "react";
import { api } from "../lib/api";

/** One race weekend: lineups, winner, qualifying ({ data, loading, error }). */
export function useWeekend(raceId) {
  const [state, setState] = useState({ data: null, loading: true, error: null });

  useEffect(() => {
    if (!raceId) return;
    let active = true;
    setState({ data: null, loading: true, error: null });
    api
      .get(`/weekend/${raceId}`)
      .then((data) => active && setState({ data, loading: false, error: null }))
      .catch((err) => active && setState({ data: null, loading: false, error: err.message }));
    return () => {
      active = false;
    };
  }, [raceId]);

  return state;
}
