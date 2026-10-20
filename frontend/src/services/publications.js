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

export const listProductImages = (id) => request(`/products/${id}/images`);
export const listProductImagesForManagement = (id, adminPin) => request(
  `/products/${id}/images/manage`, { method: 'POST', body: { admin_pin: adminPin } },
);
export const createProductImageUpload = (id, body) => request(
  `/products/${id}/images/upload-url`, { method: 'POST', body },
);
export const completeProductImageUpload = (id, imageId, adminPin) => request(
  `/products/${id}/images/${imageId}/complete`, { method: 'POST', body: { admin_pin: adminPin } },
);
export const deleteProductImage = (id, imageId, adminPin) => request(
  `/products/${id}/images/${imageId}`, { method: 'DELETE', body: { admin_pin: adminPin } },
);

export function endpointFor(kind) {
  return endpoints[kind];
}
