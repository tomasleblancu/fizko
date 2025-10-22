/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_CHATKIT_API_DOMAIN_KEY: string;
  readonly VITE_CHATKIT_API_URL?: string;
  readonly VITE_API_BASE_URL?: string;
  readonly VITE_SUPABASE_URL: string;
  readonly VITE_SUPABASE_ANON_KEY: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
