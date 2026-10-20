import { completePublicationImageUpload, createPublicationImageUpload } from './publications.js';
const ACCEPTED_TYPES = new Set(['image/jpeg', 'image/png', 'image/webp']);
const MAX_BYTES = 5 * 1024 * 1024;

export async function uploadPublicationImage(kind, publicationId, file, adminPin, altText = '') {
  const { isImageStorageConfigured, supabase } = await import('./supabase.js');
  if (!isImageStorageConfigured) {
    throw new Error('Falta configurar el acceso público de Supabase para imágenes.');
  }
  if (!ACCEPTED_TYPES.has(file.type)) {
    throw new Error('Usa una imagen JPG, PNG o WebP.');
  }
  if (file.size > MAX_BYTES) {
    throw new Error('Cada imagen puede pesar hasta 5 MB.');
  }

  const upload = await createPublicationImageUpload(kind, publicationId, {
    admin_pin: adminPin,
    content_type: file.type,
    size_bytes: file.size,
    alt_text: altText || file.name.replace(/\.[^.]+$/, ''),
  });
  const { error } = await supabase.storage
    .from(upload.bucket)
    .uploadToSignedUrl(upload.path, upload.token, file, {
      contentType: file.type,
      upsert: false,
    });

  if (error) throw new Error('Supabase no pudo subir la imagen. Inténtalo de nuevo.');
  return completePublicationImageUpload(kind, publicationId, upload.id, adminPin);
}

export const uploadProductImage = (productId, file, adminPin, altText = '') => (
  uploadPublicationImage('product', productId, file, adminPin, altText)
);
