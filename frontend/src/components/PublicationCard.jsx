import { Link } from 'react-router-dom';
import { formatDate, formatPrice } from '../utils/format.js';

export default function PublicationCard({ kind, item }) {
  const isProduct = kind === 'product';
  const href = `/${isProduct ? 'productos' : 'avisos'}/${item.id}`;
  const image = isProduct ? item.cover_image?.url : null;
  return (
    <article className="publication-card">
      <Link to={href} className={`card-image ${image ? '' : 'card-image-placeholder'}`} aria-label={`Ver ${item.title}`}>
        {image ? <img src={image} alt={item.cover_image?.alt_text || item.title} loading="lazy" /> : (
          <span className="placeholder-symbol" aria-hidden="true">{isProduct ? '✳' : '⌂'}</span>
        )}
        <span className="card-kind">{isProduct ? 'Producto' : 'Aviso'}</span>
      </Link>
      <div className="card-body">
        <div className="card-meta"><span>{item.category}</span><span>{item.city}</span></div>
        <Link to={href} className="card-title">{item.title}</Link>
        {isProduct && <p className="card-price">{formatPrice(item.price, item.currency)}</p>}
        {!isProduct && item.business_name && <p className="card-business">{item.business_name}</p>}
        <p className="card-description">{item.description}</p>
        <div className="card-footer">
          <span>Por {item.contact_name}</span><time dateTime={item.created_at}>{formatDate(item.created_at)}</time>
        </div>
      </div>
    </article>
  );
}
