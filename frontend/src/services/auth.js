import { supabase } from './supabase.js';

export async function getAccessToken() {
  if (!supabase) return null;
  const { data, error } = await supabase.auth.getSession();
  if (error) throw error;
  return data.session?.access_token || null;
}

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
