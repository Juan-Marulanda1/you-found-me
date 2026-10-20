import { createContext, useMemo, useState } from 'react';
import { Link, Outlet, Route, Routes } from 'react-router-dom';
import CatalogPage from './pages/CatalogPage.jsx';
import DetailPage from './pages/DetailPage.jsx';
import ManagePage from './pages/ManagePage.jsx';
import MyPublicationsPage from './pages/MyPublicationsPage.jsx';
import PublishPage from './pages/PublishPage.jsx';

export const PublicationAccessContext = createContext(null);

function SiteLayout() {
  return (
    <div className="app-shell">
      <header className="site-header">
        <Link to="/" className="brand" aria-label="You Found Me, inicio">
          <span className="brand-mark" aria-hidden="true">y</span>
          <span>you found me<span className="brand-period">.</span></span>
        </Link>
        <nav className="main-nav" aria-label="Navegación principal">
          <Link to="/">Explorar</Link>
          <Link to="/mis-publicaciones">Tus publicaciones</Link>
          <Link to="/publicar" className="nav-publish">Publicar <span aria-hidden="true">＋</span></Link>
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
  const [creationKey, setCreationKey] = useState('');
  const access = useMemo(() => ({ creationKey, setCreationKey }), [creationKey]);

  return (
    <PublicationAccessContext.Provider value={access}>
      <Routes>
        <Route element={<SiteLayout />}>
          <Route index element={<CatalogPage />} />
          <Route path="/productos/:id" element={<DetailPage kind="product" />} />
          <Route path="/avisos/:id" element={<DetailPage kind="announcement" />} />
          <Route path="/publicar" element={<PublishPage />} />
          <Route path="/mis-publicaciones" element={<MyPublicationsPage />} />
          <Route path="/gestionar/:kind/:id" element={<ManagePage />} />
          <Route path="*" element={<section className="empty-state"><span className="eyebrow">404</span><h1>No encontramos esta página</h1><Link className="button button-primary" to="/">Volver al inicio</Link></section>} />
        </Route>
      </Routes>
    </PublicationAccessContext.Provider>
  );
}
