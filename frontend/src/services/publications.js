import { request } from './api.js';

// Único lugar que conoce las rutas de cada tipo de publicación; las páginas solo usan kind.
const endpoints = {
  product: '/products',
  announcement: '/announcements',
};

// Omite filtros vacíos: la API los rechazaría o los aplicaría como búsqueda.
export function listPublications(kind, filters = {}) {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries(filters)) {
    if (value !== undefined && value !== null && String(value).trim() !== '') {
      query.set(key, String(value).trim());
    }
  }
  const suffix = query.size ? `?${query.toString()}` : '';
  return request(`${endpoints[kind]}${suffix}`);
}

export const getPublication = (kind, id) => request(`${endpoints[kind]}/${id}`);
export const createPublication = (kind, body) => request(endpoints[kind], {
  method: 'POST', body,
});
// La clave de invitación viaja solo en este encabezado y no se persiste en el navegador.
export const requestAccountInvitation = (email, key) => request('/account-access/invite', {
  method: 'POST', body: { email }, headers: { 'X-Publication-Key': key },
});
export const getMyPublications = () => request('/account-access/me/publications');
export const claimLegacyPublication = (kind, publicationId, adminPin) => request(
  '/account-access/me/claim', {
    method: 'POST', body: { kind, publication_id: publicationId, admin_pin: adminPin },
  },
);
export const getPublicationForManagement = (kind, id, adminPin) => request(
  `${endpoints[kind]}/${id}/manage`, {
    method: 'POST', body: adminPin ? { admin_pin: adminPin } : {},
  },
);
export const updatePublication = (kind, id, body) => request(
  `${endpoints[kind]}/${id}`, { method: 'PATCH', body },
);
export const deletePublication = (kind, id, adminPin) => request(
  `${endpoints[kind]}/${id}`, {
    method: 'DELETE', body: adminPin ? { admin_pin: adminPin } : {},
  },
);

export const listPublicationImages = (kind, id) => request(`${endpoints[kind]}/${id}/images`);
export const listPublicationImagesForManagement = (kind, id, adminPin) => request(
  `${endpoints[kind]}/${id}/images/manage`, {
    method: 'POST', body: adminPin ? { admin_pin: adminPin } : {},
  },
);
export const createPublicationImageUpload = (kind, id, body) => request(
  `${endpoints[kind]}/${id}/images/upload-url`, { method: 'POST', body },
);
export const completePublicationImageUpload = (kind, id, imageId, adminPin) => request(
  `${endpoints[kind]}/${id}/images/${imageId}/complete`, {
    method: 'POST', body: adminPin ? { admin_pin: adminPin } : {},
  },
);
export const deletePublicationImage = (kind, id, imageId, adminPin) => request(
  `${endpoints[kind]}/${id}/images/${imageId}`, {
    method: 'DELETE', body: adminPin ? { admin_pin: adminPin } : {},
  },
);
