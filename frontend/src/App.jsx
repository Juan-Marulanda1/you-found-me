import { createContext, useContext, useEffect, useState } from 'react';
import { Link, Outlet, Route, Routes } from 'react-router-dom';
import AccountPage from './pages/AccountPage.jsx';
import CatalogPage from './pages/CatalogPage.jsx';
import DetailPage from './pages/DetailPage.jsx';
import ManagePage from './pages/ManagePage.jsx';
import MyPublicationsPage from './pages/MyPublicationsPage.jsx';
import PublishPage from './pages/PublishPage.jsx';
import { signOut } from './services/auth.js';
import { supabase } from './services/supabase.js';

// Comparte la sesión de Supabase con las páginas que publican o administran.
export const AuthContext = createContext({ session: null });

// Estructura común: cabecera con navegación según la sesión, contenido y pie.
function SiteLayout() {
  const { session } = useContext(AuthContext);
  return (
    <div className="app-shell">
      <header className="site-header">
        <Link to="/" className="brand" aria-label="You Found Me, inicio">
          <span className="brand-mark" aria-hidden="true">y</span>
          <span>you found me<span className="brand-period">.</span></span>
        </Link>
        <nav className="main-nav" aria-label="Navegación principal">
          <Link to="/">Explorar</Link>
          {session && <Link to="/mis-publicaciones">Tus publicaciones</Link>}
          <Link to="/publicar" className="nav-publish">Publicar <span aria-hidden="true">＋</span></Link>
          {session ? (
            <button className="nav-account-button" type="button" onClick={() => signOut()}>Salir</button>
          ) : <Link to="/cuenta">Entrar</Link>}
        </nav>
      </header>
      <main className="main-content"><Outlet /></main>
      <footer className="site-footer">
        <span className="footer-brand">you found me<span className="brand-period">.</span></span>
        <span>Productos y negocios de tu comunidad.</span>
      </footer>
    </div>
  );
}

export default function App() {
  const [session, setSession] = useState(null);

  useEffect(() => {
    if (!supabase) return undefined;
    // Mantiene la navegación sincronizada con la sesión restaurada y sus cambios.
    supabase.auth.getSession().then(({ data }) => setSession(data.session));
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, nextSession) => {
      setSession(nextSession);
    });
    return () => subscription.unsubscribe();
  }, []);

  return (
    <AuthContext.Provider value={{ session }}>
      {/* Si agregas una ruta, configura el hosting para servir index.html en ella. */}
      <Routes>
        <Route element={<SiteLayout />}>
          <Route index element={<CatalogPage />} />
          <Route path="/productos/:id" element={<DetailPage kind="product" />} />
          <Route path="/avisos/:id" element={<DetailPage kind="announcement" />} />
          <Route path="/cuenta" element={<AccountPage />} />
          <Route path="/publicar" element={<PublishPage />} />
          <Route path="/mis-publicaciones" element={<MyPublicationsPage />} />
          <Route path="/gestionar/:kind/:id" element={<ManagePage />} />
          <Route path="*" element={<section className="empty-state"><span className="eyebrow">404</span><h1>No encontramos esta página</h1><Link className="button button-primary" to="/">Volver al inicio</Link></section>} />
        </Route>
      </Routes>
    </AuthContext.Provider>
  );
}
