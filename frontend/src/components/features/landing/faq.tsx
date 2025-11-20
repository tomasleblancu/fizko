"use client";

import { ChevronDown } from "lucide-react";
import { useState } from "react";

const faqs = [
  {
    question: "¿Cómo se conecta Fizko con el SII?",
    answer:
      "Fizko se conecta de forma segura con el SII usando tus credenciales. Toda la información viaja encriptada y nunca almacenamos tus contraseñas. La conexión nos permite mantener tu información actualizada en tiempo real.",
  },
  {
    question: "¿Qué impuestos puedo declarar con Fizko?",
    answer:
      "Actualmente Fizko te ayuda con el Formulario 29 (IVA mensual), Impuesto a la Renta Anual (F22), documentos tributarios electrónicos (DTEs), y próximamente soportaremos otros formularios. Nuestro asistente también puede responder consultas sobre cualquier tema tributario.",
  },
  {
    question: "¿Cuánto cuesta Fizko?",
    answer:
      "Estamos en fase de pre lanzamiento. Los primeros usuarios que se unan tendrán acceso exclusivo con condiciones especiales. Contáctanos para conocer más detalles y ser parte de nuestros early adopters.",
  },
  {
    question: "¿Es seguro compartir mis credenciales del SII?",
    answer:
      "Sí, es completamente seguro. Usamos encriptación de nivel bancario (AES-256) para proteger tus credenciales. Además, nunca almacenamos tu contraseña en texto plano y todos nuestros sistemas cumplen con estándares internacionales de seguridad.",
  },
  {
    question: "¿Qué pasa si tengo dudas o necesito ayuda?",
    answer:
      "Nuestro asistente inteligente está disponible 24/7 para resolver todas tus dudas tributarias. Para dudas complejas, tenemos un equipo experto de contadores disponibles en horario normal. Además, durante el pre lanzamiento tendrás soporte directo de nuestro equipo vía WhatsApp.",
  },
  {
    question: "¿Puedo usar Fizko si tengo contador?",
    answer:
      "¡Por supuesto! Fizko complementa el trabajo de tu contador. Tu contador puede tener acceso a la plataforma para revisar información en tiempo real, y tú mantienes el control y visibilidad de todo lo que pasa con tu negocio.",
  },
];

export function FAQ() {
  const [openFaqIndex, setOpenFaqIndex] = useState<number | null>(null);

  const toggleFaq = (index: number) => {
    setOpenFaqIndex(openFaqIndex === index ? null : index);
  };

  return (
    <section
      className="relative bg-gradient-to-b from-slate-50 to-white dark:from-slate-800 dark:to-slate-900 py-20 transition-colors"
      aria-labelledby="faq-heading"
    >
      <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
        <header className="text-center mb-12">
          <h2
            id="faq-heading"
            className="text-3xl font-bold text-slate-900 dark:text-white mb-3"
          >
            Preguntas Frecuentes
          </h2>
          <p className="text-lg text-slate-600 dark:text-slate-400">
            Todo lo que necesitas saber sobre Fizko
          </p>
        </header>

        <div className="space-y-4">
          {faqs.map((faq, index) => (
            <div
              key={index}
              className="bg-white dark:bg-slate-800 rounded-xl shadow-sm hover:shadow-md transition-all duration-300 overflow-hidden border border-slate-200 dark:border-slate-700"
            >
              <button
                onClick={() => toggleFaq(index)}
                className="w-full flex items-center justify-between p-6 text-left hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
                aria-expanded={openFaqIndex === index}
                aria-controls={`faq-answer-${index}`}
              >
                <span className="text-lg font-semibold text-slate-900 dark:text-white pr-4">
                  {faq.question}
                </span>
                <ChevronDown
                  className={`h-5 w-5 text-slate-500 dark:text-slate-400 flex-shrink-0 transition-transform duration-300 ${
                    openFaqIndex === index ? "rotate-180" : ""
                  }`}
                  aria-hidden="true"
                />
              </button>
              <div
                id={`faq-answer-${index}`}
                className={`overflow-hidden transition-all duration-300 ${
                  openFaqIndex === index ? "max-h-96" : "max-h-0"
                }`}
              >
                <div className="px-6 pb-6 text-slate-600 dark:text-slate-300 leading-relaxed">
                  {faq.answer}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
