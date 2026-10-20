import { supabase } from './supabase.js';

// Funciones de Supabase Auth. La API vuelve a validar cada token en el servidor.

const INACTIVE_ACCOUNT = 'Esta cuenta aún no está activa. Solicita una invitación desde «Crear cuenta».';

// Supabase responde en inglés; se traducen sus códigos de error documentados
// (https://supabase.com/docs/guides/auth/debugging/error-codes).
const AUTH_ERROR_MESSAGES = {
  otp_disabled: INACTIVE_ACCOUNT,
  signup_disabled: INACTIVE_ACCOUNT,
  user_not_found: INACTIVE_ACCOUNT,
  email_not_confirmed: 'Confirma tu correo electrónico antes de iniciar sesión.',
  email_address_invalid: 'Revisa que el correo electrónico sea válido.',
  validation_failed: 'Revisa que el correo electrónico sea válido.',
  over_email_send_rate_limit: 'Enviamos demasiados correos. Espera unos minutos antes de pedir otro enlace.',
  over_request_rate_limit: 'Hiciste demasiadas solicitudes. Espera unos minutos e inténtalo de nuevo.',
  session_expired: 'Tu sesión expiró. Inicia sesión de nuevo.',
  session_not_found: 'Tu sesión ya no es válida. Inicia sesión de nuevo.',
  refresh_token_not_found: 'Tu sesión ya no es válida. Inicia sesión de nuevo.',
};

// Convierte un error de Supabase en un Error con mensaje en español.
// Conserva `code` para que la interfaz pueda distinguir casos sin leer el texto.
function authError(error) {
  const message = AUTH_ERROR_MESSAGES[error?.code]
    || (error?.status === 0 || error?.name === 'AuthRetryableFetchError'
      ? 'No pudimos conectar con el servicio de cuentas. Revisa tu conexión e inténtalo de nuevo.'
      : 'No pudimos completar la operación con tu cuenta. Inténtalo de nuevo.');
  const translated = new Error(message);
  translated.code = error?.code || 'auth_error';
  return translated;
}

// Token de la sesión actual o null si no hay sesión o Supabase no está configurado.
export async function getAccessToken() {
  if (!supabase) return null;
  const { data, error } = await supabase.auth.getSession();
  if (error) throw authError(error);
  return data.session?.access_token || null;
}

// Envía un enlace de acceso; el enlace regresa a /cuenta con la sesión iniciada.
export async function requestMagicLink(email) {
  if (!supabase) throw new Error('Falta configurar Supabase Auth en el frontend.');
  const { error } = await supabase.auth.signInWithOtp({
    email: email.trim().toLowerCase(),
    options: {
      // Las cuentas nuevas solo nacen por invitación desde la API.
      shouldCreateUser: false,
      emailRedirectTo: `${window.location.origin}/cuenta`,
    },
  });
  if (error) throw authError(error);
}

export async function signOut() {
  if (!supabase) return;
  const { error } = await supabase.auth.signOut();
  if (error) throw authError(error);
}
