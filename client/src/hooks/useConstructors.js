import { useEffect, useState } from "react";
import { api } from "../lib/api";

/** Fetch the current season's constructors. */
export function useConstructors() {
  const [constructors, setConstructors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    api
      .get("/constructors", { auth: false })
      .then((data) => active && setConstructors(data?.constructors ?? []))
      .catch((err) => active && setError(err.message))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, []);

  return { constructors, loading, error };
}
