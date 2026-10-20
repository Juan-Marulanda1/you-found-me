import { createClient } from '@supabase/supabase-js';

const url = import.meta.env.VITE_SUPABASE_URL;
const publishableKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY;

// Sin URL o clave publicable la app sigue funcionando como catálogo de solo lectura.
export const isSupabaseConfigured = Boolean(url && publishableKey);
export const isImageStorageConfigured = isSupabaseConfigured;
export const supabase = isSupabaseConfigured ? createClient(url, publishableKey) : null;
