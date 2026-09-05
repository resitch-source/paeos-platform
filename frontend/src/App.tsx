import { useEffect, useState } from "react";
import { apiFetch } from "./api/client";
import { t, type Locale } from "./i18n";

interface Meta {
  product: string;
  component: string;
  version: string;
  active_phase: string;
  domain_phases_started: string[];
}

// The foundation shell renders platform status only — no domain screens exist.
export default function App() {
  const [locale] = useState<Locale>("en");
  const [meta, setMeta] = useState<Meta | null>(null);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    apiFetch<Meta>("/api/v1/meta")
      .then(setMeta)
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "error"));
  }, []);

  return (
    <main style={{ fontFamily: "system-ui", maxWidth: 720, margin: "48px auto" }}>
      <h1>{t("app.title", locale)}</h1>
      <p style={{ color: "#555" }}>{t("app.subtitle", locale)}</p>
      <p>{t("status.foundation", locale)}</p>

      <section
        style={{
          marginTop: 24,
          padding: 16,
          border: "1px solid #ddd",
          borderRadius: 8,
        }}
      >
        <h2 style={{ fontSize: 16 }}>Platform status</h2>
        {error && <p style={{ color: "crimson" }}>API unreachable: {error}</p>}
        {meta ? (
          <ul>
            <li>Component: {meta.component}</li>
            <li>Version: {meta.version}</li>
            <li>Active phase: {meta.active_phase}</li>
            <li>
              Domain phases started:{" "}
              {meta.domain_phases_started.length === 0
                ? "none"
                : meta.domain_phases_started.join(", ")}
            </li>
          </ul>
        ) : (
          !error && <p>Loading…</p>
        )}
      </section>
    </main>
  );
}
