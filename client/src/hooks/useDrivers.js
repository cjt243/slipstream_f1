import { useEffect, useState } from "react";
import { api } from "../lib/api";

/** Fetch the current season's active drivers. */
export function useDrivers() {
  const [drivers, setDrivers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    api
      .get("/drivers", { auth: false })
      .then((data) => active && setDrivers(data?.drivers ?? []))
      .catch((err) => active && setError(err.message))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, []);

  return { drivers, loading, error };
}
