import { useCallback, useEffect, useState } from "react";
import { api } from "../lib/api";

/** The signed-in user's team (GET /contracts) plus sign/release actions that
 * refresh it. Actions throw ApiError so callers can show the message. */
export function useTeam() {
  const [team, setTeam] = useState(null);
  const [error, setError] = useState(null);

  const refresh = useCallback(
    () =>
      api
        .get("/contracts")
        .then((data) => {
          setTeam(data);
          setError(null);
        })
        .catch((err) => setError(err.message)),
    []
  );

  useEffect(() => {
    refresh();
  }, [refresh]);

  const sign = useCallback(
    async (elementType, elementId, length) => {
      await api.post("/contracts", { element_type: elementType, element_id: elementId, contract_length: length });
      await refresh();
    },
    [refresh]
  );

  const release = useCallback(
    async (contractId) => {
      const result = await api.del(`/contracts/${contractId}`);
      await refresh();
      return result;
    },
    [refresh]
  );

  // Pick (driverId) or clear (null) the current race's star driver.
  const setStar = useCallback(
    async (driverId) => {
      if (driverId == null) await api.del("/contracts/star");
      else await api.put("/contracts/star", { driver_id: driverId });
      await refresh();
    },
    [refresh]
  );

  return { team, loading: team === null && !error, error, sign, release, setStar, refresh };
}
