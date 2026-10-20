import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import PublicationCard from '../components/PublicationCard.jsx';
import { Busy, Notice } from '../components/Feedback.jsx';
import { listPublications } from '../services/publications.js';

const emptyPage = { items: [], page: 1, pages: 0, total: 0 };

export default function CatalogPage() {
  const [kind, setKind] = useState('product');
  const [form, setForm] = useState({ search: '', city: '', category: '' });
  const [filters, setFilters] = useState({});
  const [page, setPage] = useState(1);
  const [result, setResult] = useState(emptyPage);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError('');
    listPublications(kind, { ...filters, page, page_size: 12 })
      .then((data) => { if (active) setResult(data); })
      .catch((requestError) => { if (active) setError(requestError.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [kind, filters, page]);

  function submitSearch(event) {
    event.preventDefault();
    const nextFilters = Object.fromEntries(
      Object.entries(form).filter(([, value]) => value.trim().length >= 2),
    );
    setPage(1);
    setFilters(nextFilters);
  }

  return (
    <>
      <section className="hero">
        <div className="hero-copy">
          <span className="eyebrow"><span className="eyebrow-dot" /> Hecho cerca, encontrado aquí</span>
          <h1>Lo que buscas<br /><em>está más cerca.</em></h1>
          <p>Encuentra productos, negocios y buenas ideas de personas de tu comunidad.</p>
        </div>
        <div className="hero-sticker" aria-hidden="true"><span>✨</span><small>Descubre<br />lo local</small></div>
        <div className="hero-orbit orbit-one" aria-hidden="true" />
        <div className="hero-orbit orbit-two" aria-hidden="true" />
      </section>

      <section className="catalog-section">
        <div className="section-heading">
          <div>
            <span className="eyebrow">El mercado de tu barrio</span>
            <h2>Explora lo que hay</h2>
          </div>
          <span className="result-count">{result.total} {result.total === 1 ? 'publicación' : 'publicaciones'}</span>
        </div>

        <div className="catalog-controls">
          <div className="catalog-tabs" role="tablist" aria-label="Tipo de publicación">
            <button type="button" className={kind === 'product' ? 'tab active' : 'tab'} onClick={() => { setKind('product'); setPage(1); }} role="tab" aria-selected={kind === 'product'}>Productos <span>↗</span></button>
            <button type="button" className={kind === 'announcement' ? 'tab active' : 'tab'} onClick={() => { setKind('announcement'); setPage(1); }} role="tab" aria-selected={kind === 'announcement'}>Avisos <span>↗</span></button>
          </div>
          <form className="search-form" onSubmit={submitSearch}>
            <label className="sr-only" htmlFor="catalog-search">Buscar publicaciones</label>
            <span className="search-icon" aria-hidden="true">⌕</span>
            <input id="catalog-search" className="search-input" placeholder="¿Qué estás buscando?" value={form.search} onChange={(event) => setForm({ ...form, search: event.target.value })} />
            <input aria-label="Ciudad" className="search-city" placeholder="Ciudad" value={form.city} onChange={(event) => setForm({ ...form, city: event.target.value })} />
            <input aria-label="Categoría" className="search-category" placeholder="Categoría" value={form.category} onChange={(event) => setForm({ ...form, category: event.target.value })} />
            <button className="button button-dark search-submit" type="submit">Buscar <span aria-hidden="true">→</span></button>
          </form>
        </div>

        <Notice tone="error">{error}</Notice>
        {loading ? <Busy>Buscando en tu comunidad…</Busy> : result.items.length ? (
          <div className="card-grid">
            {result.items.map((item) => <PublicationCard key={item.id} kind={kind} item={item} />)}
          </div>
        ) : !error ? (
          <div className="empty-state catalog-empty">
            <span className="empty-illustration" aria-hidden="true">✳</span>
            <h3>Aún no hay publicaciones por aquí</h3>
            <p>Prueba con otra búsqueda o vuelve pronto: lo bueno siempre aparece.</p>
          </div>
        ) : null}

        {!loading && result.pages > 1 && (
          <nav className="pagination" aria-label="Paginación">
            <button className="button button-outline" type="button" disabled={page <= 1} onClick={() => setPage(page - 1)}>← Anterior</button>
            <span>Página {result.page} de {result.pages}</span>
            <button className="button button-outline" type="button" disabled={page >= result.pages} onClick={() => setPage(page + 1)}>Siguiente →</button>
          </nav>
        )}
      </section>

      <section className="community-callout">
        <div className="callout-art" aria-hidden="true"><span>✦</span><span>⌂</span><span>✳</span></div>
        <div><span className="eyebrow">Tu comunidad tiene mucho que ofrecer</span><h2>¿Tienes algo bueno<br />para compartir?</h2></div>
        <p>Publica un producto o dale visibilidad a tu negocio y conecta con personas cerca de ti.</p>
        <Link to="/publicar" className="button button-primary">Quiero publicar <span aria-hidden="true">↗</span></Link>
      </section>
    </>
  );
}
