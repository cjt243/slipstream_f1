import { useEffect, useState } from "react";
import { api } from "../lib/api";

/** Season standings (+ races with fantasy points), or one race's standings
 * when `raceId` is set. */
export function useLeaderboard(raceId) {
  const [state, setState] = useState({ data: null, loading: true, error: null });

  useEffect(() => {
    let active = true;
    setState((s) => ({ ...s, loading: true, error: null }));
    api
      .get(raceId ? `/leaderboard/${raceId}` : "/leaderboard")
      .then((data) => active && setState({ data, loading: false, error: null }))
      .catch((err) => active && setState({ data: null, loading: false, error: err.message }));
    return () => {
      active = false;
    };
  }, [raceId]);

  return state;
}
