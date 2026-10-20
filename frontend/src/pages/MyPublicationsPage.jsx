import { useContext, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { AuthContext } from '../App.jsx';
import PublicationCard from '../components/PublicationCard.jsx';
import { Busy, Notice } from '../components/Feedback.jsx';
import { getMyPublications } from '../services/publications.js';
import { getPublicationRefs } from '../services/publicationRefs.js';
import { managementPath } from '../utils/routes.js';

// Convierte referencias guardadas en el navegador en tarjetas, omitiendo las que la API
// ya devolvió como propias o reclamables.
function localFallbacks(references, knownIds) {
  return references
    .filter((reference) => !knownIds.has(`${reference.kind}-${reference.id}`))
    .map((reference) => ({
      kind: reference.kind,
      id: reference.id,
      title: reference.preview?.title || 'Publicación anterior',
      category: reference.preview?.category || 'Sin categoría',
      description: reference.preview?.description || 'Abre esta publicación e ingresa su PIN para reclamarla.',
      city: reference.preview?.city || '',
      status: reference.preview?.status || 'ACTIVE',
      cover_image: reference.preview?.cover_image || null,
    }));
}

// Muestra tres grupos: publicaciones de la cuenta, antiguas con el mismo correo
// (reclamables con PIN) y referencias locales que no coinciden con el correo.
export default function MyPublicationsPage() {
  const { session } = useContext(AuthContext);
  const [publications, setPublications] = useState([]);
  const [claimable, setClaimable] = useState([]);
  const [localLegacy, setLocalLegacy] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    if (!session) {
      setPublications([]);
      setClaimable([]);
      setLocalLegacy([]);
      return () => { active = false; };
    }
    setLoading(true);
    setError('');
    getMyPublications().then((data) => {
      if (!active) return;
      setPublications([
        ...data.products.map((item) => ({ kind: 'product', item })),
        ...data.announcements.map((item) => ({ kind: 'announcement', item })),
      ]);
      setClaimable(data.claimable || []);
      const knownIds = new Set([
        ...data.products.map((item) => `product-${item.id}`),
        ...data.announcements.map((item) => `announcement-${item.id}`),
        ...(data.claimable || []).map((item) => `${item.kind}-${item.id}`),
      ]);
      setLocalLegacy(localFallbacks(getPublicationRefs(), knownIds));
    }).catch((requestError) => {
      if (active) setError(requestError.message);
    }).finally(() => {
      if (active) setLoading(false);
    });
    return () => { active = false; };
  }, [session]);

  return (
    <section className="content-page my-publications-page">
      <div className="page-heading">
        <span className="eyebrow">Tu espacio personal</span>
        <h1>Tus <em>publicaciones.</em></h1>
        <p>Inicia sesión para ver tus publicaciones en cualquier dispositivo. Las antiguas se pueden reclamar con su PIN.</p>
      </div>
      {!session && (
        <div className="empty-state my-empty">
          <span className="empty-illustration" aria-hidden="true">⌂</span>
          <h2>Inicia sesión para continuar</h2>
          <p>Las publicaciones nuevas aparecen aquí al entrar en tu cuenta.</p>
          <Link className="button button-primary" to="/cuenta">Entrar a mi cuenta <span aria-hidden="true">↗</span></Link>
        </div>
      )}
      {session && loading && <Busy>Cargando tus publicaciones…</Busy>}
      {session && <Notice tone="error">{error}</Notice>}
      {session && !loading && !error && publications.length > 0 && (
        <>
          <h2 className="my-publications-section-title">En tu cuenta</h2>
          <div className="card-grid my-publications-grid">
            {publications.map(({ kind, item }) => (
              <PublicationCard
                key={`${kind}-${item.id}`}
                kind={kind}
                item={item}
                to={managementPath(kind, item.id)}
                actionLabel="Administrar"
              />
            ))}
          </div>
        </>
      )}
      {session && !loading && !error && claimable.length > 0 && (
        <>
          <h2 className="my-publications-section-title">Publicaciones anteriores</h2>
          <p className="my-claim-hint">Encontramos publicaciones antiguas con el mismo correo. Abre una tarjeta e ingresa su PIN para vincularla a tu cuenta.</p>
          <div className="card-grid my-publications-grid">
            {claimable.map((item) => (
              <PublicationCard
                key={`claim-${item.kind}-${item.id}`}
                kind={item.kind}
                item={item}
                to={managementPath(item.kind, item.id)}
                actionLabel="Reclamar con PIN"
              />
            ))}
          </div>
        </>
      )}
      {session && !loading && !error && localLegacy.length > 0 && (
        <>
          <h2 className="my-publications-section-title">Guardadas en este navegador</h2>
          <p className="my-claim-hint">Estas referencias no coinciden con el correo de la cuenta. Reclama cada publicación con su PIN.</p>
          <div className="card-grid my-publications-grid">
            {localLegacy.map((item) => (
              <PublicationCard
                key={`local-${item.kind}-${item.id}`}
                kind={item.kind}
                item={item}
                to={managementPath(item.kind, item.id)}
                actionLabel="Abrir con PIN"
              />
            ))}
          </div>
        </>
      )}
      {session && !loading && !error && !publications.length && !claimable.length && !localLegacy.length && (
        <div className="empty-state my-empty">
          <span className="empty-illustration" aria-hidden="true">⌂</span>
          <h2>Aún no tienes publicaciones</h2>
          <p>Al publicar desde tu cuenta, podrás volver a encontrarlas aquí.</p>
          <Link className="button button-primary" to="/publicar">Crear una publicación <span aria-hidden="true">↗</span></Link>
        </div>
      )}
      <p className="privacy-note my-privacy">Las publicaciones se asocian a tu cuenta. El PIN de los avisos anteriores solo se usa una vez para reclamarlos.</p>
    </section>
  );
}
