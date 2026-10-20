// Referencias locales de compatibilidad para publicaciones antiguas; solo guardan
// campos públicos de vista previa, nunca PIN ni tokens.
const STORAGE_KEY = 'you-found-me.publications.v1';
const PREVIEW_FIELDS = [
  'title', 'description', 'category', 'city', 'business_name', 'contact_name',
  'created_at', 'status', 'price', 'currency', 'quantity',
];

function sanitizePreview(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return null;

  const preview = {};
  for (const field of PREVIEW_FIELDS) {
    const fieldValue = value[field];
    if (typeof fieldValue === 'string' || typeof fieldValue === 'number') {
      preview[field] = fieldValue;
    }
  }

  if (Object.hasOwn(value, 'cover_image')) {
    const cover = value.cover_image;
    if (cover === null) preview.cover_image = null;
    else if (cover && typeof cover.url === 'string') {
      try {
        const url = new URL(cover.url);
        if (['http:', 'https:'].includes(url.protocol)) {
          preview.cover_image = {
            url: url.toString(),
            alt_text: typeof cover.alt_text === 'string' ? cover.alt_text : null,
          };
        }
      } catch {
        // Omite vistas previas locales con URL malformada.
      }
    }
  }

  return preview;
}

// Lee y sanea las referencias; un valor corrupto en localStorage devuelve una lista vacía.
export function getPublicationRefs() {
  try {
    const value = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    if (!Array.isArray(value)) return [];
    return value
      .filter((item) => item && ['product', 'announcement'].includes(item.kind) && typeof item.id === 'string')
      .map((item) => ({
        kind: item.kind,
        id: item.id,
        preview: sanitizePreview(item.preview),
      }));
  } catch {
    return [];
  }
}

// Guarda o actualiza la referencia al inicio de la lista, conservando la vista previa previa.
export function rememberPublication(kind, id, publication) {
  const current = getPublicationRefs();
  const existing = current.find((item) => item.kind === kind && item.id === id);
  const preview = sanitizePreview(publication);
  const refs = current.filter((item) => item.kind !== kind || item.id !== id);
  refs.unshift({
    kind,
    id,
    preview: preview ? { ...existing?.preview, ...preview } : existing?.preview || null,
  });
  localStorage.setItem(STORAGE_KEY, JSON.stringify(refs));
}

export function forgetPublication(kind, id) {
  const refs = getPublicationRefs().filter((item) => item.kind !== kind || item.id !== id);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(refs));
}
