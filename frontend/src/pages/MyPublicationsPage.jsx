import { useState } from 'react';
import { Link } from 'react-router-dom';
import { getPublicationRefs, forgetPublication } from '../services/publicationRefs.js';
import { kindLabel, truncateId } from '../utils/format.js';

export default function MyPublicationsPage() {
  const [refs, setRefs] = useState(getPublicationRefs);

  function removeReference(item) {
    forgetPublication(item.kind, item.id);
    setRefs(getPublicationRefs());
  }

  return (
    <section className="content-page my-publications-page">
      <div className="page-heading">
        <span className="eyebrow">Tu espacio personal</span>
        <h1>Tus <em>publicaciones.</em></h1>
        <p>Esta lista vive en este navegador. Ingresa el PIN que creaste para administrar cada publicación.</p>
      </div>
      {refs.length ? <div className="managed-list">
        {refs.map((item) => (
          <article className="managed-card" key={`${item.kind}-${item.id}`}>
            <div className="managed-card-heading"><span className="managed-kind">{kindLabel(item.kind)}</span><span className="managed-id">{truncateId(item.id)}</span><button type="button" className="icon-button" onClick={() => removeReference(item)} aria-label="Quitar de esta lista">×</button></div>
            <div className="manage-access-form"><p>El PIN se solicitará antes de abrir la administración.</p><Link className="button button-dark" to={`/gestionar/${item.kind}/${item.id}`}>Administrar →</Link></div>
          </article>
        ))}
      </div> : <div className="empty-state my-empty"><span className="empty-illustration" aria-hidden="true">⌂</span><h2>Tu lista está vacía</h2><p>Cuando publiques algo desde este navegador, lo encontrarás aquí.</p><Link className="button button-primary" to="/publicar">Crear una publicación <span aria-hidden="true">↗</span></Link></div>}
      <p className="privacy-note my-privacy">Solo guardamos el identificador en este navegador. El PIN nunca se guarda en la lista ni se envía en la dirección de la página.</p>
    </section>
  );
}
