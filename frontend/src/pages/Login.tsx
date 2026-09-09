import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth";

export function Login() {
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const [tenant, setTenant] = useState("farm");
  const [email, setEmail] = useState("admin@demofarm.ph");
  const [password, setPassword] = useState("supersecret123");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await signIn(tenant, email, password);
      navigate("/");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="login-wrap">
      <h1>PAEOS</h1>
      <p className="sub">Philippine Agriculture Enterprise Operating System</p>
      <form className="card" onSubmit={onSubmit}>
        <div>
          <label>Tenant</label>
          <input
            className="grow"
            value={tenant}
            onChange={(e) => setTenant(e.target.value)}
            style={{ width: "100%" }}
          />
        </div>
        <div>
          <label>Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={{ width: "100%" }}
          />
        </div>
        <div>
          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{ width: "100%" }}
          />
        </div>
        {error && <p className="err">{error}</p>}
        <button type="submit" disabled={busy} style={{ width: "100%" }}>
          {busy ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </div>
  );
}
