import { TrendingUp, MessageCircle, CalendarCheck, Mail, ChevronDown } from 'lucide-react';
import { useState } from 'react';
import { LandingFooter } from "@/shared/ui/branding/LandingFooter";
import { ContactSalesDialog } from "./ContactSalesDialog";

export default function Landing() {
  const [isContactDialogOpen, setIsContactDialogOpen] = useState(false);
  const [openFaqIndex, setOpenFaqIndex] = useState<number | null>(null);

  const handleContactSales = () => {
    setIsContactDialogOpen(true);
  };

  const handleGetStarted = () => {
    window.location.href = '/login';
  };

  const toggleFaq = (index: number) => {
    setOpenFaqIndex(openFaqIndex === index ? null : index);
  };

  const faqs = [
    {
      question: "¿Cómo se conecta Fizko con el SII?",
      answer: "Fizko se conecta de forma segura con el SII usando tus credenciales. Toda la información viaja encriptada y nunca almacenamos tus contraseñas. La conexión nos permite mantener tu información actualizada en tiempo real."
    },
    {
      question: "¿Qué impuestos puedo declarar con Fizko?",
      answer: "Actualmente Fizko te ayuda con el Formulario 29 (IVA mensual), Impuesto a la Renta Anual (F22), documentos tributarios electrónicos (DTEs), y próximamente soportaremos otros formularios. Nuestro asistente también puede responder consultas sobre cualquier tema tributario."
    },
    {
      question: "¿Cuánto cuesta Fizko?",
      answer: "Estamos en fase de pre lanzamiento. Los primeros usuarios que se unan tendrán acceso exclusivo con condiciones especiales. Contáctanos para conocer más detalles y ser parte de nuestros early adopters."
    },
    {
      question: "¿Es seguro compartir mis credenciales del SII?",
      answer: "Sí, es completamente seguro. Usamos encriptación de nivel bancario (AES-256) para proteger tus credenciales. Además, nunca almacenamos tu contraseña en texto plano y todos nuestros sistemas cumplen con estándares internacionales de seguridad."
    },
    {
      question: "¿Qué pasa si tengo dudas o necesito ayuda?",
      answer: "Nuestro asistente inteligente está disponible 24/7 para resolver todas tus dudas tributarias. Para dudas complejas, tenemos un equipo experto de contadores disponibles en horario normal. Además, durante el pre lanzamiento tendrás soporte directo de nuestro equipo vía WhatsApp."
    },
    {
      question: "¿Puedo usar Fizko si tengo contador?",
      answer: "¡Por supuesto! Fizko complementa el trabajo de tu contador. Tu contador puede tener acceso a la plataforma para revisar información en tiempo real, y tú mantienes el control y visibilidad de todo lo que pasa con tu negocio."
    }
  ];

  return (
    <main className="min-h-screen bg-gradient-to-br from-emerald-50 via-white to-teal-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      {/* Navigation Bar */}
      <nav className="relative">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-6">
            {/* Logo a la izquierda */}
            <div className="flex items-center gap-2">
              <img
                src="/encabezado.png"
                alt="Fizko Icon"
                className="h-8 w-auto sm:h-10"
              />
              <img
                src="/encabezado_fizko.svg"
                alt="Fizko"
                className="h-10 w-auto sm:h-12"
              />
            </div>

            {/* Botón Entrar a la derecha */}
            <button
              onClick={handleGetStarted}
              className="inline-flex items-center rounded-full bg-gradient-to-r from-emerald-600 to-teal-600 px-6 py-2 text-sm font-semibold text-white shadow-sm transition-all hover:shadow-md hover:scale-105"
              aria-label="Entrar a Fizko"
            >
              <span>Entrar</span>
            </button>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden" aria-label="Hero">
        {/* Decorative background */}
        <div className="absolute inset-0 bg-gradient-to-b from-emerald-50/50 via-transparent to-transparent dark:from-emerald-950/30" aria-hidden="true" />

        <div className="relative mx-auto max-w-7xl px-4 py-16 sm:px-6 sm:py-24 lg:px-8">
          <header className="text-center">
            {/* Main Headline */}
            <div className="mx-auto max-w-4xl">
              <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-bold text-slate-900 dark:text-white mb-8 leading-tight">
                <span className="block transition-all duration-300 hover:scale-105 cursor-default inline-block">
                  Tus números claros.
                </span>
                <span className="block bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent transition-all duration-300 hover:scale-105 cursor-default inline-block">
                  Tus impuestos bajo control.
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
                onClick={handleContactSales}
                className="group inline-flex items-center space-x-3 rounded-full bg-gradient-to-r from-emerald-600 to-teal-600 px-10 py-5 text-xl font-semibold text-white shadow-xl transition-all hover:shadow-2xl hover:scale-105"
                aria-label="Solicitar una demo de Fizko"
              >
                <Mail className="h-6 w-6" />
                <span>Solicitar Demo</span>
              </button>

              <button
                onClick={() => window.open('https://wa.me/56975389973', '_blank')}
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
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" style={{ animationDelay: '1s' }}></span>
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
              <div className="absolute -inset-8 bg-gradient-to-r from-emerald-400 to-teal-400 rounded-3xl blur-3xl opacity-10" aria-hidden="true" />

              {/* Pure white container with padding */}
              <div className="relative bg-white dark:bg-slate-800 rounded-3xl p-8 sm:p-12 shadow-2xl">
                {/* Desktop Video */}
                <div className="hidden sm:block relative overflow-hidden">
                  <video
                    className="w-full"
                    autoPlay
                    muted
                    loop
                    playsInline
                    preload="auto"
                    aria-label="Video demostrativo de la plataforma Fizko mostrando cambio de empresa, agregar trabajador y chat en acción"
                  >
                    <source src="/video_tutorial_fizko.mp4" type="video/mp4" />
                    Tu navegador no soporta la reproducción de video. Por favor actualiza tu navegador.
                  </video>
                </div>

                {/* Mobile Video */}
                <div className="block sm:hidden relative overflow-hidden max-w-sm mx-auto">
                  <video
                    className="w-full"
                    autoPlay
                    muted
                    loop
                    playsInline
                    preload="auto"
                    aria-label="Video demostrativo de la plataforma Fizko mostrando cambio de empresa, agregar trabajador y chat en acción"
                  >
                    <source src="/video_tutorial_fizko_phone.mp4" type="video/mp4" />
                    Tu navegador no soporta la reproducción de video. Por favor actualiza tu navegador.
                  </video>
                </div>
              </div>
            </div>
          </figure>
        </div>
      </section>

      {/* Las 3C de Fizko Section - Hero Style */}
      <section className="relative overflow-hidden bg-gradient-to-br from-slate-900 via-emerald-950 to-slate-900 py-32 transition-colors" aria-labelledby="three-cs-heading">
        {/* Decorative background */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-emerald-900/20 via-transparent to-transparent" aria-hidden="true" />

        <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <header className="text-center mb-20">
            <h2 id="three-cs-heading" className="text-5xl font-bold text-white sm:text-6xl mb-6">
              Las 3C de Fizko
            </h2>
            <p className="text-2xl text-emerald-200">
              La esencia de nuestra plataforma
            </p>
          </header>

          <div className="grid gap-8 md:grid-cols-3 max-w-6xl mx-auto">
            {/* Conecta */}
            <div className="group relative">
              <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/20 to-teal-500/20 rounded-3xl blur-xl group-hover:blur-2xl transition-all duration-300" aria-hidden="true" />
              <div className="relative flex flex-col items-center text-center h-full p-10 bg-white/5 backdrop-blur-sm rounded-3xl border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all duration-300">
                <div className="flex items-center justify-center w-20 h-20 mb-8 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-500 shadow-2xl flex-shrink-0 group-hover:scale-110 transition-transform duration-300">
                  <svg className="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5} aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <h3 className="text-4xl font-bold text-white mb-4">Conecta</h3>
                <p className="text-lg text-emerald-100 leading-relaxed">
                  Tu información financiera con un click
                </p>
              </div>
            </div>

            {/* Controla */}
            <div className="group relative">
              <div className="absolute inset-0 bg-gradient-to-br from-teal-500/20 to-cyan-500/20 rounded-3xl blur-xl group-hover:blur-2xl transition-all duration-300" aria-hidden="true" />
              <div className="relative flex flex-col items-center text-center h-full p-10 bg-white/5 backdrop-blur-sm rounded-3xl border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all duration-300">
                <div className="flex items-center justify-center w-20 h-20 mb-8 rounded-2xl bg-gradient-to-br from-teal-500 to-cyan-500 shadow-2xl flex-shrink-0 group-hover:scale-110 transition-transform duration-300">
                  <svg className="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5} aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <h3 className="text-4xl font-bold text-white mb-4">Controla</h3>
                <p className="text-lg text-emerald-100 leading-relaxed">
                  Todos tus movimientos y crecimiento
                </p>
              </div>
            </div>

            {/* Cumple */}
            <div className="group relative">
              <div className="absolute inset-0 bg-gradient-to-br from-emerald-500/20 to-green-500/20 rounded-3xl blur-xl group-hover:blur-2xl transition-all duration-300" aria-hidden="true" />
              <div className="relative flex flex-col items-center text-center h-full p-10 bg-white/5 backdrop-blur-sm rounded-3xl border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all duration-300">
                <div className="flex items-center justify-center w-20 h-20 mb-8 rounded-2xl bg-gradient-to-br from-emerald-500 to-green-500 shadow-2xl flex-shrink-0 group-hover:scale-110 transition-transform duration-300">
                  <svg className="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5} aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-4xl font-bold text-white mb-4">Cumple</h3>
                <p className="text-lg text-blue-100 leading-relaxed">
                  Todas tus obligaciones tributarias
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section - Compact Design */}
      <section className="relative bg-white dark:bg-slate-900 py-20 transition-colors" aria-labelledby="features-heading">
        <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
          <header className="text-center mb-12">
            <h2 id="features-heading" className="text-3xl font-bold text-slate-900 dark:text-white mb-3">
              Qué incluye Fizko
            </h2>
            <p className="text-lg text-slate-600 dark:text-slate-400">
              Para cumplir con las 3C, te entregamos estas herramientas
            </p>
          </header>

          <div className="space-y-4">
            {/* Feature 1 - Información en tiempo real */}
            <div className="group flex items-start gap-6 p-6 bg-slate-50 dark:bg-slate-800/50 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-all duration-300">
              <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-gradient-to-br from-emerald-500 to-teal-500 shadow-sm flex-shrink-0">
                <TrendingUp className="h-6 w-6 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-1">
                  Información en tiempo real
                </h3>
                <p className="text-slate-600 dark:text-slate-300 text-sm leading-relaxed">
                  Nos conectamos al SII y te actualizamos de todo lo que está pasando con tu negocio.
                </p>
              </div>
            </div>

            {/* Feature 2 - Asistente 24/7 */}
            <div className="group flex items-start gap-6 p-6 bg-slate-50 dark:bg-slate-800/50 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-all duration-300">
              <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-gradient-to-br from-teal-500 to-cyan-500 shadow-sm flex-shrink-0">
                <MessageCircle className="h-6 w-6 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-1">
                  Asistente disponible 24/7
                </h3>
                <p className="text-slate-600 dark:text-slate-300 text-sm leading-relaxed">
                  Chat que resuelve todas las dudas que tengas, las 24 horas del día.
                </p>
              </div>
            </div>

            {/* Feature 3 - Cumplimiento tributario */}
            <div className="group flex items-start gap-6 p-6 bg-slate-50 dark:bg-slate-800/50 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-all duration-300">
              <div className="flex items-center justify-center w-12 h-12 rounded-lg bg-gradient-to-br from-emerald-500 to-green-500 shadow-sm flex-shrink-0">
                <CalendarCheck className="h-6 w-6 text-white" />
              </div>
              <div className="flex-1">
                <h3 className="text-lg font-bold text-slate-900 dark:text-white mb-1">
                  Cumplimiento tributario
                </h3>
                <p className="text-slate-600 dark:text-slate-300 text-sm leading-relaxed">
                  Nos encargamos de generar tus declaraciones y cumplir con las fechas que establece el SII.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="relative bg-gradient-to-b from-slate-50 to-white dark:from-slate-800 dark:to-slate-900 py-20 transition-colors" aria-labelledby="faq-heading">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
          <header className="text-center mb-12">
            <h2 id="faq-heading" className="text-3xl font-bold text-slate-900 dark:text-white mb-3">
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
                      openFaqIndex === index ? 'rotate-180' : ''
                    }`}
                    aria-hidden="true"
                  />
                </button>
                <div
                  id={`faq-answer-${index}`}
                  className={`overflow-hidden transition-all duration-300 ${
                    openFaqIndex === index ? 'max-h-96' : 'max-h-0'
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

      {/* CTA Section */}
      <section className="relative bg-white dark:bg-slate-900 py-20 transition-colors" aria-labelledby="cta-heading">
        <div className="mx-auto max-w-4xl px-4 text-center sm:px-6 lg:px-8">
          <div className="rounded-3xl bg-gradient-to-br from-emerald-600 to-teal-600 p-12 shadow-xl">
            <h2 id="cta-heading" className="text-3xl font-bold text-white sm:text-4xl">
              Sé parte del futuro de la gestión tributaria
            </h2>
            <p className="mt-4 text-xl text-emerald-50">
              Únete al pre lanzamiento y obtén acceso exclusivo a Fizko.
            </p>
            <button
              onClick={handleContactSales}
              className="mt-8 inline-flex items-center space-x-3 rounded-full bg-white px-8 py-4 text-lg font-semibold text-slate-900 shadow-lg transition-all hover:scale-105 hover:shadow-xl"
              aria-label="Acceder al pre lanzamiento"
            >
              <Mail className="h-6 w-6 text-emerald-600" />
              <span>Accede al Pre Lanzamiento</span>
            </button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <LandingFooter />

      {/* Contact Sales Dialog */}
      <ContactSalesDialog
        isOpen={isContactDialogOpen}
        onClose={() => setIsContactDialogOpen(false)}
      />
    </main>
  );
}
