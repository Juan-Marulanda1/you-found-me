const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1').replace(/\/$/, '');
const MESSAGE_TRANSLATIONS = {
  'Invalid publication access key.': 'La clave de publicación no es correcta.',
  'Publication creation is not configured.': 'La clave de publicación aún no está configurada en el servidor.',
  'Invalid management PIN.': 'El PIN de administración no es correcto.',
  'Too many invalid PIN attempts. Try again later.': 'Hubo demasiados intentos. Espera 15 minutos antes de probar de nuevo.',
  'Product not found': 'No encontramos este producto.',
  'Announcement not found': 'No encontramos este aviso.',
  'Product image not found.': 'No encontramos esta imagen.',
  'This product has reached its image limit.': 'Este producto ya alcanzó el máximo de imágenes.',
  'The image has not been uploaded yet.': 'La imagen todavía no termina de subirse.',
  'The uploaded image does not match the requested file type or size.': 'La imagen no coincide con el tipo o tamaño permitido.',
  'Image storage is temporarily unavailable.': 'El almacenamiento de imágenes no está disponible por ahora.',
};

export class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
  }
}

export async function request(path, { body, headers = {}, ...options } = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
        ...headers,
      },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });
  } catch {
    throw new ApiError('No pudimos conectar con el servidor. Revisa que la API esté disponible.', 0);
  }

  let payload;
  try {
    payload = await response.json();
  } catch {
    throw new ApiError('El servidor respondió con un formato inesperado.', response.status);
  }

  if (!response.ok || payload.success === false) {
    const message = payload.message || 'No pudimos completar la solicitud.';
    throw new ApiError(MESSAGE_TRANSLATIONS[message] || message, response.status);
  }

  return payload.data;
}

export function publicationHeaders(key) {
  return { 'X-Publication-Key': key };
}

export function getApiBaseUrl() {
  return API_BASE_URL;
}
