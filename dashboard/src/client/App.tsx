import { LoginPage } from "./pages/Login";
import { DashboardPage } from "./pages/Dashboard";
import { authClient } from "./auth-client";

export function App() {
  const { data: session, isPending } = authClient.useSession();

  if (isPending) {
    return (
      <div className="app-shell">
        <p className="muted">Chargement…</p>
      </div>
    );
  }

  if (!session) {
    return <LoginPage />;
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <h1>M.I.R.A</h1>
        <p className="topbar-sub muted">Console — robots, carte, vidéo, assistant</p>
        <button
          type="button"
          className="btn-link"
          onClick={() => void authClient.signOut()}
        >
          Déconnexion
        </button>
      </header>
      <main className="main main--dashboard">
        <DashboardPage />
      </main>
    </div>
  );
}
