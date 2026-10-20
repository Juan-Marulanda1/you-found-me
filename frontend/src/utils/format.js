export function formatPrice(price, currency = 'COP') {
  return new Intl.NumberFormat('es-CO', {
    style: 'currency', currency, maximumFractionDigits: 0,
  }).format(Number(price));
}

export function formatDate(date) {
  return new Intl.DateTimeFormat('es-CO', { day: 'numeric', month: 'short', year: 'numeric' }).format(new Date(date));
}

export function kindLabel(kind) {
  return kind === 'product' ? 'Producto' : 'Aviso';
}

export function truncateId(id) {
  return `${id.slice(0, 8)}…${id.slice(-4)}`;
}
