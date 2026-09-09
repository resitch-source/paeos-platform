import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";

export function Layout() {
  const { session, signOut } = useAuth();
  const navigate = useNavigate();

  const onSignOut = () => {
    signOut();
    navigate("/login");
  };

  return (
    <>
      <header className="app-header">
        <span className="brand">PAEOS</span>
        <nav>
          <NavLink to="/" end>
            Dashboard
          </NavLink>
          <NavLink to="/inventory">Inventory</NavLink>
          <NavLink to="/sales">Sales Orders</NavLink>
        </nav>
        <span className="who">
          {session ? `${session.email} · ${session.tenantSlug}` : ""}
        </span>
        <button className="secondary" onClick={onSignOut}>
          Sign out
        </button>
      </header>
      <Outlet />
    </>
  );
}
