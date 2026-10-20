import { completePublicationImageUpload, createPublicationImageUpload } from './publications.js';
import { isImageStorageConfigured, supabase } from './supabase.js';

// Validación temprana para evitar cargas que la API rechazaría; el backend aplica los límites reales.
const ACCEPTED_TYPES = new Set(['image/jpeg', 'image/png', 'image/webp']);
const MAX_BYTES = 5 * 1024 * 1024;

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
