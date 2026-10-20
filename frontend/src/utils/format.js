// Formatos y etiquetas en español para mostrar datos de la API.

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

const STATUS_LABELS = {
  ACTIVE: 'Activa',
  PAUSED: 'Pausada',
  SOLD: 'Vendida',
  CLOSED: 'Cerrada',
};

// Estados válidos por tipo; deben coincidir con los enums del backend.
const STATUS_OPTIONS = {
  product: ['ACTIVE', 'SOLD', 'CLOSED'],
  announcement: ['ACTIVE', 'PAUSED', 'CLOSED'],
};

export function statusLabel(status) {
  return STATUS_LABELS[status] || status;
}

export function statusOptions(kind) {
  return STATUS_OPTIONS[kind] || [];
}
