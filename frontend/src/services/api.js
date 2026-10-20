import { getAccessToken } from './auth.js';

// URL base de FastAPI, incluido el prefijo /api/v1.
const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1').replace(/\/$/, '');

// La API ya responde en español. Estas etiquetas solo reemplazan los nombres
// técnicos de los campos (p. ej. admin_pin) en los errores de validación.
const FIELD_LABELS = {
  title: 'Título',
  description: 'Descripción',
  category: 'Categoría',
  price: 'Precio',
  currency: 'Moneda',
  quantity: 'Unidades disponibles',
  business_name: 'Nombre del negocio',
  website_url: 'Sitio web',
  contact_name: 'Nombre de contacto',
  contact_phone: 'Teléfono',
  contact_email: 'Correo electrónico',
  email: 'Correo electrónico',
  city: 'Ciudad',
  address: 'Dirección',
  status: 'Estado',
  admin_pin: 'PIN de administración',
  new_admin_pin: 'Nuevo PIN',
  content_type: 'Tipo de imagen',
  size_bytes: 'Tamaño de la imagen',
  alt_text: 'Texto alternativo',
  search: 'Búsqueda',
  min_price: 'Precio mínimo',
  max_price: 'Precio máximo',
};

// Error de la API. `code` es el identificador estable del problema (RFC 9457)
// y es lo que el código debe comparar; `message` es solo para mostrar.
// status 0 indica que no hubo respuesta del servidor.
export class ApiError extends Error {
  constructor(message, { status = 0, code = 'network_error', errors = [] } = {}) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.errors = errors;
  }
}

// Construye el texto visible a partir de un Problem Details. En validaciones
// muestra cada campo con su etiqueta; en los demás casos usa `detail`.
function problemMessage(problem) {
  if (Array.isArray(problem.errors) && problem.errors.length) {
    return problem.errors
      .map(({ field, message }) => (field ? `${FIELD_LABELS[field] || field}: ${message}` : message))
      .join(' ');
  }
  return problem.detail || problem.title || 'No pudimos completar la solicitud.';
}

// Cliente HTTP único: adjunta la sesión, serializa JSON y devuelve solo `data`.
// Los errores llegan como application/problem+json y se convierten en ApiError.
export async function request(path, { body, headers = {}, ...options } = {}) {
  // Centraliza el token para que las páginas no tengan que gestionar encabezados de sesión.
  // Se obtiene fuera del try para no confundir un fallo de sesión con uno de red.
  const accessToken = await getAccessToken();
  let response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers: {
        Accept: 'application/json, application/problem+json',
        ...(body === undefined ? {} : { 'Content-Type': 'application/json' }),
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        ...headers,
      },
      ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    });
  } catch {
    throw new ApiError('No pudimos conectar con el servidor. Revisa tu conexión e inténtalo de nuevo.');
  }

  let payload;
  try {
    payload = await response.json();
  } catch {
    throw new ApiError('El servidor respondió con un formato inesperado.', {
      status: response.status,
      code: 'invalid_response',
    });
  }

  if (!response.ok) {
    throw new ApiError(problemMessage(payload), {
      status: response.status,
      code: payload.code || 'http_error',
      errors: payload.errors || [],
    });
  }

  return payload.data;
}
