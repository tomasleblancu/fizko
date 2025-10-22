import { StartScreenPrompt } from "@openai/chatkit";

export const CHATKIT_API_URL =
  import.meta.env.VITE_CHATKIT_API_URL ??
  (import.meta.env.PROD ? "https://fizko-ai.up.railway.app/chatkit" : "/chatkit");

export const CHATKIT_API_DOMAIN_KEY =
  import.meta.env.VITE_CHATKIT_API_DOMAIN_KEY ?? "domain_pk_localhost_dev";

// En producción, usar la URL completa del backend en Railway
// En desarrollo, usar proxy local
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ??
  (import.meta.env.PROD ? "https://fizko-ai.up.railway.app/api" : "/api");

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
