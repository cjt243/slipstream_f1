import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { MOCK_DRIVERS } from "../lib/mockData";

/** Fetch current-season drivers, falling back to mock data when the backend
 * endpoint isn't available yet (issue 1B/2-series wire the real route). */
export function useDrivers() {
  const [drivers, setDrivers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [usingMock, setUsingMock] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    api
      .get("/drivers", { auth: false })
      .then((data) => active && setDrivers(data?.drivers ?? []))
      .catch((err) => {
        if (!active) return;
        // Mock data is a local-dev convenience only; production surfaces the error.
        if (import.meta.env.DEV) {
          setDrivers(MOCK_DRIVERS);
          setUsingMock(true);
        } else {
          setError(err.message);
        }
      })
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, []);

  return { drivers, loading, usingMock, error };
}
