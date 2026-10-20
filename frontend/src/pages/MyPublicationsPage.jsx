import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import PublicationCard from '../components/PublicationCard.jsx';
import { Busy, Notice } from '../components/Feedback.jsx';
import { getPublication } from '../services/publications.js';
import { getPublicationRefs, forgetPublication } from '../services/publicationRefs.js';
import { kindLabel } from '../utils/format.js';

function savedPreview(reference) {
  const preview = reference.preview || {};
  return {
    ...preview,
    id: reference.id,
    title: preview.title || 'Publicación guardada',
    category: preview.category || kindLabel(reference.kind),
    description: preview.description || 'Ingresa el PIN para cargar la vista previa y editar esta publicación.',
  };
}

export default function MyPublicationsPage() {
  const [refs, setRefs] = useState(getPublicationRefs);
  const [publications, setPublications] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let active = true;
    if (!refs.length) {
      setPublications([]);
      setLoading(false);
      return () => { active = false; };
    }

    setLoading(true);
    Promise.all(refs.map(async (reference) => {
      try {
        const current = await getPublication(reference.kind, reference.id);
        return {
          ...reference,
          item: { ...reference.preview, ...current, id: reference.id },
        };
      } catch {
        return { ...reference, item: savedPreview(reference) };
      }
    })).then((items) => {
      if (active) setPublications(items);
    }).finally(() => {
      if (active) setLoading(false);
    });

    return () => { active = false; };
  }, [refs]);

  function removeReference(item) {
    forgetPublication(item.kind, item.id);
    setRefs(getPublicationRefs());
  }

  return (
    <section className="content-page my-publications-page">
      <div className="page-heading">
        <span className="eyebrow">Tu espacio personal</span>
        <h1>Tus <em>publicaciones.</em></h1>
        <p>Elige una tarjeta para editarla. El PIN se solicitará antes de abrir la administración.</p>
      </div>
      {loading && <Busy>Cargando tus publicaciones…</Busy>}
      {!loading && publications.length ? (
        <div className="card-grid my-publications-grid">
          {publications.map((reference) => (
            <PublicationCard
              key={`${reference.kind}-${reference.id}`}
              kind={reference.kind}
              item={reference.item}
              to={`/gestionar/${reference.kind}/${reference.id}`}
              actionLabel="Editar con tu PIN"
              onRemove={() => removeReference(reference)}
            />
          ))}
        </div>
      ) : !loading && (
        <div className="empty-state my-empty">
          <span className="empty-illustration" aria-hidden="true">⌂</span>
          <h2>Tu lista está vacía</h2>
          <p>Cuando publiques algo desde este navegador, lo encontrarás aquí.</p>
          <Link className="button button-primary" to="/publicar">Crear una publicación <span aria-hidden="true">↗</span></Link>
        </div>
      )}
      <p className="privacy-note my-privacy">La lista y sus vistas previas se guardan en este navegador. El PIN, el correo y la dirección privada nunca se guardan aquí.</p>
    </section>
  );
}
