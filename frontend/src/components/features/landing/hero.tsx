"use client";

import { Mail, MessageCircle } from "lucide-react";

interface HeroProps {
  onContactSales: () => void;
}

export function Hero({ onContactSales }: HeroProps) {
  const handleWhatsApp = () => {
    window.open("https://wa.me/56975389973", "_blank");
  };

  return (
    <section className="relative overflow-hidden" aria-label="Hero">
      {/* Decorative background */}
      <div
        className="absolute inset-0 bg-gradient-to-b from-emerald-50/50 via-transparent to-transparent dark:from-emerald-950/30"
        aria-hidden="true"
      />

      <div className="relative mx-auto max-w-7xl px-4 py-16 sm:px-6 sm:py-24 lg:px-8">
        <header className="text-center">
          {/* Main Headline */}
          <div className="mx-auto max-w-4xl">
            <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-bold text-slate-900 dark:text-white mb-8 leading-tight">
              <span className="block transition-all duration-300 hover:scale-105 cursor-default inline-block">
                Tus números claros
              </span>
              <span className="block bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent transition-all duration-300 hover:scale-105 cursor-default inline-block">
                Tus impuestos bajo control
              </span>
            </h1>
          </div>

          {/* Subtitle */}
          <p className="mx-auto mt-8 max-w-2xl text-xl sm:text-2xl leading-relaxed text-slate-600 dark:text-slate-300">
            Declaramos tus impuestos automáticamente.
            <span className="block mt-2 font-medium text-slate-700 dark:text-slate-200">
              Tú vuelves a enfocarte en crecer.
            </span>
          </p>

          {/* CTA Buttons */}
          <div className="mt-12 flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              onClick={onContactSales}
              className="group inline-flex items-center space-x-3 rounded-full bg-gradient-to-r from-emerald-600 to-teal-600 px-10 py-5 text-xl font-semibold text-white shadow-xl transition-all hover:shadow-2xl hover:scale-105"
              aria-label="Solicitar una demo de Fizko"
            >
              <Mail className="h-6 w-6" />
              <span>Solicitar Demo</span>
            </button>

            <button
              onClick={handleWhatsApp}
              className="inline-flex items-center space-x-3 rounded-full bg-white dark:bg-slate-800 border-2 border-slate-200 dark:border-slate-700 px-10 py-5 text-xl font-semibold text-slate-700 dark:text-slate-200 shadow-lg transition-all hover:shadow-xl hover:scale-105 hover:border-slate-300 dark:hover:border-slate-600"
              aria-label="Contactar por WhatsApp"
            >
              <MessageCircle className="h-6 w-6" />
              <span>Háblanos</span>
            </button>
          </div>

          {/* Trust Indicators with pulsing dots */}
          <div className="mt-10 flex flex-wrap items-center justify-center gap-6 text-sm text-slate-600 dark:text-slate-400">
            <div className="flex items-center gap-2">
              <div className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500"></span>
              </div>
              <span>Conexión segura con el SII</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="relative flex h-2 w-2">
                <span
                  className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"
                  style={{ animationDelay: "1s" }}
                ></span>
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500"></span>
              </div>
              <span>Acceso anticipado disponible</span>
            </div>
          </div>
        </header>

        {/* Video Preview - Pure White Container */}
        <figure className="mt-12 sm:mt-16">
          <div className="relative mx-auto max-w-6xl">
            {/* Decorative blur behind container */}
            <div
              className="absolute -inset-8 bg-gradient-to-r from-emerald-400 to-teal-400 rounded-3xl blur-3xl opacity-10"
              aria-hidden="true"
            />

            {/* Pure white container with padding */}
            <div className="relative bg-white dark:bg-slate-800 rounded-3xl p-8 sm:p-12 shadow-2xl">
              {/* Desktop Video */}
              <div className="hidden sm:block relative overflow-hidden rounded-lg">
                <video
                  className="w-full rounded-lg"
                  autoPlay
                  muted
                  loop
                  playsInline
                  preload="metadata"
                  aria-label="Video demostrativo de la plataforma Fizko mostrando cambio de empresa, agregar trabajador y chat en acción"
                  onError={(e) => {
                    console.error('Error loading desktop video:', e);
                  }}
                  onLoadedData={(e) => {
                    console.log('Desktop video loaded successfully');
                    const video = e.currentTarget;
                    video.play().catch(err => console.error('Error playing video:', err));
                  }}
                >
                  <source src="/video_tutorial_fizko.mp4" type="video/mp4" />
                  Tu navegador no soporta la reproducción de video. Por favor
                  actualiza tu navegador.
                </video>
              </div>

              {/* Mobile Video */}
              <div className="block sm:hidden relative overflow-hidden rounded-lg max-w-sm mx-auto">
                <video
                  className="w-full rounded-lg"
                  autoPlay
                  muted
                  loop
                  playsInline
                  preload="metadata"
                  aria-label="Video demostrativo de la plataforma Fizko mostrando cambio de empresa, agregar trabajador y chat en acción"
                  onError={(e) => {
                    console.error('Error loading mobile video:', e);
                  }}
                  onLoadedData={(e) => {
                    console.log('Mobile video loaded successfully');
                    const video = e.currentTarget;
                    video.play().catch(err => console.error('Error playing video:', err));
                  }}
                >
                  <source
                    src="/video_tutorial_fizko_phone.mp4"
                    type="video/mp4"
                  />
                  Tu navegador no soporta la reproducción de video. Por favor
                  actualiza tu navegador.
                </video>
              </div>
            </div>
          </div>
        </figure>
      </div>
    </section>
  );
}
