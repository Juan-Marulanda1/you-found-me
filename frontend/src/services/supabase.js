import { createClient } from '@supabase/supabase-js';

const url = import.meta.env.VITE_SUPABASE_URL;
const publishableKey = import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY;

export const isImageStorageConfigured = Boolean(url && publishableKey);
export const supabase = isImageStorageConfigured ? createClient(url, publishableKey) : null;
