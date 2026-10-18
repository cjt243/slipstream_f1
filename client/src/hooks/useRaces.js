import { useEffect, useState } from "react";
import { api } from "../lib/api";

/** Season calendar: { races, nextRaceId, loading, error }. */
export function useRaces() {
  const [state, setState] = useState({ races: [], nextRaceId: null, loading: true, error: null });

  useEffect(() => {
    let active = true;
    api
      .get("/races", { auth: false })
      .then((data) =>
        active && setState({ races: data.races, nextRaceId: data.next_race, loading: false, error: null })
      )
      .catch((err) => active && setState((s) => ({ ...s, loading: false, error: err.message })));
    return () => {
      active = false;
    };
  }, []);

  return state;
}

/** One race's detail: { race, loading, error }. */
export function useRace(id) {
  const [state, setState] = useState({ race: null, loading: true, error: null });

  useEffect(() => {
    let active = true;
    setState({ race: null, loading: true, error: null });
    api
      .get(`/races/${id}`, { auth: false })
      .then((race) => active && setState({ race, loading: false, error: null }))
      .catch((err) => active && setState({ race: null, loading: false, error: err.message }));
    return () => {
      active = false;
    };
  }, [id]);

  return state;
}
