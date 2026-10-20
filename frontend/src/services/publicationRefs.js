const STORAGE_KEY = 'you-found-me.publications.v1';

export function getPublicationRefs() {
  try {
    const value = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
    if (!Array.isArray(value)) return [];
    return value.filter((item) => item && ['product', 'announcement'].includes(item.kind) && typeof item.id === 'string');
  } catch {
    return [];
  }
}

export function rememberPublication(kind, id) {
  const refs = getPublicationRefs().filter((item) => item.kind !== kind || item.id !== id);
  refs.unshift({ kind, id });
  localStorage.setItem(STORAGE_KEY, JSON.stringify(refs));
}

export function forgetPublication(kind, id) {
  const refs = getPublicationRefs().filter((item) => item.kind !== kind || item.id !== id);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(refs));
}
