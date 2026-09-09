import { useEffect, useState } from "react";
import { apiFetch } from "../api/client";
import { useAuth } from "../auth";

interface Meta {
  product: string;
  version: string;
  active_phase: string;
  domain_phases_started: number[];
}

export function Dashboard() {
  const { session } = useAuth();
  const [meta, setMeta] = useState<Meta | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    apiFetch<Meta>("/api/v1/meta")
      .then(setMeta)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "error"));
  }, []);

  return (
    <main className="page">
      <h1>Dashboard</h1>
      <p className="sub">
        Signed in to tenant <span className="pill">{session?.tenantSlug}</span>
      </p>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>Platform</h2>
        {error && <p className="err">API unreachable: {error}</p>}
        {meta ? (
          <ul className="stack" style={{ margin: 0, paddingLeft: 18 }}>
            <li>Product: {meta.product}</li>
            <li>Version: {meta.version}</li>
            <li>Active phase: {meta.active_phase}</li>
            <li>Domain phases: {meta.domain_phases_started.join(", ")}</li>
          </ul>
        ) : (
          !error && <p>Loading…</p>
        )}
      </div>

      <div className="card">
        <h2 style={{ marginTop: 0 }}>Your access</h2>
        <p className="sub" style={{ margin: 0 }}>
          {session ? `${session.permissions.length} permissions granted` : ""}
        </p>
      </div>
    </main>
  );
}
