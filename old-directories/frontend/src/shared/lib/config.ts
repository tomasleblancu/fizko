import { StartScreenPrompt } from "@openai/chatkit";

// Backend URL base - puede ser sobrescrito con VITE_BACKEND_URL
const BACKEND_URL = import.meta.env.VITE_BACKEND_URL ??
  (import.meta.env.PROD ? "https://fizko-ai.up.railway.app" : "");

export const CHATKIT_API_URL = BACKEND_URL ? `${BACKEND_URL}/chatkit` : "/chatkit";

export const CHATKIT_API_DOMAIN_KEY =
  import.meta.env.VITE_CHATKIT_API_DOMAIN_KEY ?? "domain_pk_localhost_dev";

// En producción, usar la URL completa del backend en Railway
// En desarrollo, usar proxy local
export const API_BASE_URL = BACKEND_URL ? `${BACKEND_URL}/api` : "/api";

export const THEME_STORAGE_KEY = "fizko-theme";

export const GREETING = "Fizko";

export const STARTER_PROMPTS: StartScreenPrompt[] = [
  {
    label: "Quiero agregar un gasto",
    prompt: "Quiero registrar un gasto manual",
    icon: "notebook-pencil",
  },
  {
    label: "Dame un resumen de ventas",
    prompt: "Muéstrame un resumen de las ventas del mes",
    icon: "notebook",
  },
  {
    label: "Agrega un nuevo colaborador",
    prompt: "Quiero agregar un nuevo colaborador a la nómina",
    icon: "user",
  },
  {
    label: "Quiero darte feedback",
    prompt: "Quiero reportar un problema o darte feedback sobre la plataforma",
    icon: "circle-question",
  },
];

export const PLACEHOLDER_INPUT = "Escribe un mensaje...";
