import { supabase } from './supabase.js';

// Funciones de Supabase Auth. La API vuelve a validar cada token en el servidor.

// Token de la sesión actual o null si no hay sesión o Supabase no está configurado.
export async function getAccessToken() {
  if (!supabase) return null;
  const { data, error } = await supabase.auth.getSession();
  if (error) throw error;
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
  if (error) throw error;
}

export async function signOut() {
  if (!supabase) return;
  const { error } = await supabase.auth.signOut();
  if (error) throw error;
}
