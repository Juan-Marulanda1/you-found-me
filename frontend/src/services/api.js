import { getAccessToken } from './auth.js';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1').replace(/\/$/, '');
const MESSAGE_TRANSLATIONS = {
  'Sign in with a verified account to continue.': 'Inicia sesión con una cuenta verificada para continuar.',
  'Confirm your email before managing publications.': 'Confirma tu correo antes de administrar publicaciones.',
  'This account was not invited to publish.': 'Esta cuenta todavía no tiene permiso para publicar. Solicita una invitación.',
  'Account authentication is not configured.': 'Falta configurar la autenticación de cuentas en el backend.',
  'Account authentication is temporarily unavailable.': 'La autenticación no está disponible por ahora. Inténtalo de nuevo.',
  'Account invitations are not configured.': 'Falta configurar las invitaciones de cuenta en el backend.',
  'Account invitations are temporarily unavailable.': 'No pudimos enviar la invitación por ahora. Inténtalo de nuevo.',
  'Too many account invitations. Try again later.': 'Se enviaron demasiadas invitaciones. Inténtalo más tarde.',
  'An account already exists for this email. Request a sign-in link.': 'Ya existe una cuenta con este correo. Usa Iniciar sesión para recibir un enlace.',
  'This email address cannot be invited.': 'No pudimos invitar este correo. Revisa la dirección e inténtalo de nuevo.',
  'Invalid publication access key.': 'La clave de publicación no es correcta.',
  'Publication creation is not configured.': 'La clave de publicación aún no está configurada en el servidor.',
  'Invalid management PIN.': 'El PIN de administración no es correcto.',
  'Too many invalid PIN attempts. Try again later.': 'Hubo demasiados intentos. Espera 15 minutos antes de probar de nuevo.',
  'Product not found': 'No encontramos este producto.',
  'Announcement not found': 'No encontramos este aviso.',
  'Product image not found.': 'No encontramos esta imagen.',
  'Announcement image not found.': 'No encontramos la imagen de este aviso.',
  'This product has reached its image limit.': 'Este producto ya alcanzó el máximo de imágenes.',
  'This announcement has reached its image limit.': 'Este aviso ya tiene una imagen. Elimina la actual antes de subir otra.',
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
    const accessToken = await getAccessToken();
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
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
