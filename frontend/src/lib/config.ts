import { StartScreenPrompt } from "@openai/chatkit";

// Backend URL base - puede ser sobrescrito con VITE_BACKEND_URL
// IMPORTANT: Always force HTTPS in production to avoid mixed content errors
let BACKEND_URL = import.meta.env.VITE_BACKEND_URL ??
  (import.meta.env.PROD ? "https://fizko-ai.up.railway.app" : "");

// Force HTTPS in production if http:// is accidentally configured
if (import.meta.env.PROD && BACKEND_URL.startsWith("http://")) {
  BACKEND_URL = BACKEND_URL.replace("http://", "https://");
  console.warn("⚠️ Backend URL was http:// in production. Auto-corrected to https://");
}

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
    label: "¿Qué puedes hacer?",
    prompt: "¿Qué puedes hacer por mi empresa?",
    icon: "circle-question",
  },
  {
    label: "Muéstrame el resumen tributario del mes",
    prompt: "Muéstrame un resumen de los impuestos y obligaciones tributarias del mes actual",
    icon: "notebook",
  },
  {
    label: "Calcula el IVA a pagar",
    prompt: "Calcula el IVA que debo pagar este mes basado en las ventas y compras",
    icon: "chart",
  },
  {
    label: "Revisa mi planilla de sueldos",
    prompt: "Revisa la planilla de sueldos del último mes y muéstrame un resumen",
    icon: "user",
  },
];

export const PLACEHOLDER_INPUT = "Escribe un mensaje...";
