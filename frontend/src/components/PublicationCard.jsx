import { Link } from 'react-router-dom';
import { formatDate, formatPrice, kindLabel } from '../utils/format.js';

const statusLabels = {
  ACTIVE: 'Activa',
  PAUSED: 'Pausada',
  SOLD: 'Vendida',
  CLOSED: 'Cerrada',
};

export default function PublicationCard({
  kind,
  item,
  to,
  actionLabel,
  onRemove,
}) {
  const isProduct = kind === 'product';
  const href = to || `/${isProduct ? 'productos' : 'avisos'}/${item.id}`;
  const image = item.cover_image?.url;

  return (
    <div className="publication-card-frame">
      <Link
        to={href}
        className="publication-card"
        aria-label={`${item.title || kindLabel(kind)}. ${actionLabel || 'Ver publicación'}`}
      >
        <div className={`card-image ${image ? '' : 'card-image-placeholder'}`}>
          {image ? (
            <img src={image} alt={item.cover_image?.alt_text || item.title || ''} loading="lazy" />
          ) : (
            <span className="placeholder-symbol" aria-hidden="true">
              {isProduct ? '✳' : '⌂'}
            </span>
          )}
          <span className="card-kind">{kindLabel(kind)}</span>
        </div>
        <div className="card-body">
          <div className="card-meta">
            <span>{item.category || kindLabel(kind)}</span>
            {item.city && <span>{item.city}</span>}
          </div>
          {actionLabel && item.status && (
            <span className="card-status">Estado: {statusLabels[item.status] || item.status}</span>
          )}
          <span className="card-title">{item.title || 'Publicación guardada'}</span>
          {isProduct && item.price != null && (
            <p className="card-price">{formatPrice(item.price, item.currency)}</p>
          )}
          {!isProduct && item.business_name && (
            <p className="card-business">{item.business_name}</p>
          )}
          <p className="card-description">
            {item.description || 'Ingresa el PIN para cargar la vista previa y editar esta publicación.'}
          </p>
          {(item.contact_name || item.created_at) && (
            <div className="card-footer">
              {item.contact_name ? <span>Por {item.contact_name}</span> : <span />}
              {item.created_at && <time dateTime={item.created_at}>{formatDate(item.created_at)}</time>}
            </div>
          )}
          {actionLabel && <span className="card-action">{actionLabel} <span aria-hidden="true">→</span></span>}
        </div>
      </Link>
      {onRemove && (
        <button
          type="button"
          className="card-remove-reference"
          onClick={onRemove}
          aria-label="Quitar de Tus publicaciones"
          title="Quitar de esta lista"
        >
          ×
        </button>
      )}
    </div>
  );
}
