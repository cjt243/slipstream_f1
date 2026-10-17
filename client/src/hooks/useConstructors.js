import { useEffect, useState } from "react";
import { api } from "../lib/api";
import { MOCK_CONSTRUCTORS } from "../lib/mockData";

/** Fetch current-season constructors, falling back to mock data. */
export function useConstructors() {
  const [constructors, setConstructors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [usingMock, setUsingMock] = useState(false);

  useEffect(() => {
    let active = true;
    api
      .get("/constructors", { auth: false })
      .then((data) => active && setConstructors(data?.constructors ?? []))
      .catch(() => {
        if (!active) return;
        setConstructors(MOCK_CONSTRUCTORS);
        setUsingMock(true);
      })
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, []);

  return { constructors, loading, usingMock };
}
