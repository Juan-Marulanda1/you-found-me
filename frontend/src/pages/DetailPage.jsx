import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { Busy, Notice } from '../components/Feedback.jsx';
import { getPublication, listPublicationImages } from '../services/publications.js';
import { formatDate, formatPrice, kindLabel } from '../utils/format.js';

function safeExternalUrl(value) {
  if (!value) return '';
  try {
    const url = new URL(value);
    return ['http:', 'https:'].includes(url.protocol) ? url.toString() : '';
  } catch {
    return '';
  }
}

export default function DetailPage({ kind }) {
  const { id } = useParams();
  const [item, setItem] = useState(null);
  const [images, setImages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError('');
    const tasks = [getPublication(kind, id), listPublicationImages(kind, id).catch(() => [])];
    Promise.all(tasks)
      .then(([publication, publicationImages = []]) => {
        if (active) { setItem(publication); setImages(publicationImages); }
      })
      .catch((requestError) => { if (active) setError(requestError.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [id, kind]);

  if (loading) return <Busy>Abriendo publicación…</Busy>;
  if (error) return <section className="content-page"><Notice tone="error">{error}</Notice><Link className="text-link" to="/">← Volver a explorar</Link></section>;
  if (!item) return null;

  const gallery = images.length ? images : (item.cover_image ? [item.cover_image] : []);
  const websiteUrl = safeExternalUrl(item.website_url);
  return (
    <section className="detail-page">
      <Link className="back-link" to="/">← Volver a explorar</Link>
      <div className="detail-layout">
        <div className="detail-gallery">
          {gallery.length ? gallery.map((image) => (
            <figure className="detail-image" key={image.id}>
              <img src={image.url} alt={image.alt_text || item.title} />
            </figure>
          )) : <div className="detail-image detail-placeholder"><span aria-hidden="true">{kind === 'product' ? '✳' : '⌂'}</span><small>{kindLabel(kind)}</small></div>}
        </div>
        <article className="detail-copy">
          <div className="detail-meta"><span className="pill">{kindLabel(kind)}</span><span>{item.category}</span></div>
          <h1>{item.title}</h1>
          {kind === 'product' && <p className="detail-price">{formatPrice(item.price, item.currency)}</p>}
          {kind === 'product' && item.quantity !== null && <p className="stock-copy">{item.quantity > 0 ? `${item.quantity} disponibles` : 'Agotado'}</p>}
          {item.business_name && <p className="detail-business">{item.business_name}</p>}
          <p className="detail-description">{item.description}</p>
          <div className="detail-location"><span aria-hidden="true">⌖</span><div><strong>{item.city}</strong><small>Ubicación aproximada</small></div></div>
          <div className="seller-card">
            <span className="seller-avatar" aria-hidden="true">{item.contact_name.slice(0, 1).toUpperCase()}</span>
            <div className="seller-info"><small>Publicado por</small><strong>{item.contact_name}</strong></div>
            <time dateTime={item.created_at}>{formatDate(item.created_at)}</time>
          </div>
          <div className="contact-actions">
            {item.contact_phone ? <a className="button button-primary button-wide" href={`tel:${item.contact_phone}`}>Llamar al vendedor <span aria-hidden="true">↗</span></a> : <p className="private-contact">El teléfono no está visible porque quien publicó no autorizó compartirlo.</p>}
            {kind === 'announcement' && websiteUrl && <a className="button button-outline button-wide" href={websiteUrl} target="_blank" rel="noopener noreferrer">Visitar sitio web <span aria-hidden="true">↗</span></a>}
          </div>
          <p className="privacy-note">Por privacidad, el correo y la dirección exacta no se muestran públicamente.</p>
        </article>
      </div>
    </section>
  );
}
