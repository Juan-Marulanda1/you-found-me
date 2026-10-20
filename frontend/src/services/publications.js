import { request } from './api.js';

const endpoints = {
  product: '/products',
  announcement: '/announcements',
};

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
export const createPublication = (kind, body, key) => request(endpoints[kind], {
  method: 'POST', body, headers: { 'X-Publication-Key': key },
});
export const verifyCreationKey = (key) => request('/publication-access/verify', {
  method: 'POST', headers: { 'X-Publication-Key': key },
});
export const getPublicationForManagement = (kind, id, adminPin) => request(
  `${endpoints[kind]}/${id}/manage`, { method: 'POST', body: { admin_pin: adminPin } },
);
export const updatePublication = (kind, id, body) => request(
  `${endpoints[kind]}/${id}`, { method: 'PATCH', body },
);
export const deletePublication = (kind, id, adminPin) => request(
  `${endpoints[kind]}/${id}`, { method: 'DELETE', body: { admin_pin: adminPin } },
);

export const listPublicationImages = (kind, id) => request(`${endpoints[kind]}/${id}/images`);
export const listPublicationImagesForManagement = (kind, id, adminPin) => request(
  `${endpoints[kind]}/${id}/images/manage`, { method: 'POST', body: { admin_pin: adminPin } },
);
export const createPublicationImageUpload = (kind, id, body) => request(
  `${endpoints[kind]}/${id}/images/upload-url`, { method: 'POST', body },
);
export const completePublicationImageUpload = (kind, id, imageId, adminPin) => request(
  `${endpoints[kind]}/${id}/images/${imageId}/complete`, { method: 'POST', body: { admin_pin: adminPin } },
);
export const deletePublicationImage = (kind, id, imageId, adminPin) => request(
  `${endpoints[kind]}/${id}/images/${imageId}`, { method: 'DELETE', body: { admin_pin: adminPin } },
);

export const listProductImages = (id) => listPublicationImages('product', id);
export const listProductImagesForManagement = (id, adminPin) => listPublicationImagesForManagement('product', id, adminPin);
export const createProductImageUpload = (id, body) => createPublicationImageUpload('product', id, body);
export const completeProductImageUpload = (id, imageId, adminPin) => completePublicationImageUpload('product', id, imageId, adminPin);
export const deleteProductImage = (id, imageId, adminPin) => deletePublicationImage('product', id, imageId, adminPin);

export function endpointFor(kind) {
  return endpoints[kind];
}
