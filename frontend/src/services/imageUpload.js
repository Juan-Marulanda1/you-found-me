import { completePublicationImageUpload, createPublicationImageUpload } from './publications.js';
import { isImageStorageConfigured, supabase } from './supabase.js';

// Validación temprana para evitar cargas que la API rechazaría; el backend aplica
// los límites reales (PRODUCT_IMAGE_MAX_BYTES y *_IMAGE_MAX_COUNT). Si cambian
// allí, actualiza estos valores.
const ACCEPTED_TYPES = new Set(['image/jpeg', 'image/png', 'image/webp']);
const MAX_BYTES = 5 * 1024 * 1024;
const MAX_IMAGES = { product: 8, announcement: 1 };

// Valor para el atributo accept de los campos de archivo.
export const ACCEPTED_IMAGE_TYPES = [...ACCEPTED_TYPES].join(',');

export function maxImagesFor(kind) {
  return MAX_IMAGES[kind] || 1;
}

// Flujo en tres pasos: la API registra la imagen y firma la carga, el navegador
// sube el archivo a Supabase Storage y la API confirma que el objeto coincide.
export async function uploadPublicationImage(kind, publicationId, file, adminPin, altText = '') {
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
    ...(adminPin ? { admin_pin: adminPin } : {}),
    content_type: file.type,
    size_bytes: file.size,
    alt_text: altText || file.name.replace(/\.[^.]+$/, ''),
  });
  // El navegador sube directamente a Storage; la API solo autoriza y confirma la carga.
  const { error } = await supabase.storage
    .from(upload.bucket)
    .uploadToSignedUrl(upload.path, upload.token, file, {
      contentType: file.type,
      upsert: false,
    });

  if (error) throw new Error('Supabase no pudo subir la imagen. Inténtalo de nuevo.');
  return completePublicationImageUpload(kind, publicationId, upload.id, adminPin);
}
