import { TrendingUp, MessageCircle, CalendarCheck, Mail } from 'lucide-react';
import { useState, useEffect, useRef } from 'react';
import { TypeAnimation } from 'react-type-animation';
import { useAuth } from "@/app/providers/AuthContext";
import { LandingFooter } from "@/shared/ui/branding/LandingFooter";
import { ContactSalesDialog } from "./ContactSalesDialog";

export default function Landing() {
  const { signInWithGoogle } = useAuth();
  const [secretClickCount, setSecretClickCount] = useState(0);
  const [showSecretLogin, setShowSecretLogin] = useState(false);
  const [isContactDialogOpen, setIsContactDialogOpen] = useState(false);
  const [showSecondPart, setShowSecondPart] = useState(false);

  const handleContactSales = () => {
    setIsContactDialogOpen(true);
  };

  const handleSecretClick = () => {
    setSecretClickCount(prev => prev + 1);
    if (secretClickCount >= 4) {
      setShowSecretLogin(true);
    }
  };

  const handleGetStarted = async () => {
    await signInWithGoogle();
    setShowSecretLogin(false);
    setSecretClickCount(0);
  };


  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      {/* Hero Section */}
      {/* Sticky Logo - Only Fizko text */}
      <div className="sticky top-0 z-40 backdrop-blur-md">
        <div className="mx-auto max-w-7xl px-4 py-4">
          <div
            className="flex justify-center items-center gap-2"
            onClick={handleSecretClick}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => e.key === 'Enter' && handleSecretClick()}
          >
            <img
              src="/encabezado_fizko.png"
              alt="Fizko - Plataforma de Gestión Tributaria Inteligente"
              className="h-12 w-auto cursor-pointer sm:h-14"
            />
          </div>
        </div>
      </div>

      <section className="relative overflow-hidden bg-white dark:bg-gray-900" aria-label="Hero">
        {/* Decorative waves */}
        <div className="absolute inset-x-0 top-0 h-64 bg-gradient-to-b from-blue-100/50 to-transparent dark:from-blue-900/20" aria-hidden="true" />

        <div className="relative mx-auto max-w-7xl px-4 py-16 sm:px-6 sm:py-24 lg:px-8">
          <header className="text-center">

            {/* Main Headline - Accounting Entry Style */}
            <div className="mx-auto max-w-5xl min-h-[180px] sm:min-h-[220px]">
              {/* Accounting Entry Container */}
              <div className="flex items-center justify-center gap-2 sm:gap-4">
                {/* Left Parenthesis */}
                <img
                  src="/parentesis_izq.png"
                  alt=""
                  className="h-32 sm:h-40 w-auto flex-shrink-0"
                  aria-hidden="true"
                />

                {/* Accounting Entry Content - Two Lines */}
                <div className="flex flex-col justify-between w-full max-w-2xl" style={{ minHeight: '100px' }}>
                  {/* First Line - Left Aligned - Always at top */}
                  <div className="text-left">
                    <div className="text-xl sm:text-4xl font-bold text-gray-900 dark:text-white whitespace-nowrap">
                      <TypeAnimation
                        sequence={[
                          'Tus números claros.',
                          1000,
                          'Tus números claros.',
                          () => setShowSecondPart(true),
                        ]}
                        wrapper="span"
                        speed={50}
                        cursor={false}
                        repeat={0}
                      />
                    </div>
                  </div>

                  {/* Second Line - Right Aligned - Fixed position at bottom */}
                  <div className="text-right">
                    {showSecondPart && (
                      <div className="text-xl sm:text-4xl font-bold whitespace-nowrap">
                        <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                          <TypeAnimation
                            sequence={[
                              'Tus impuestos controlados.',
                              1000,
                            ]}
                            wrapper="span"
                            speed={50}
                            cursor={true}
                            repeat={0}
                          />
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Right Parenthesis */}
                <img
                  src="/parentesis_der.png"
                  alt=""
                  className="h-32 sm:h-40 w-auto flex-shrink-0"
                  aria-hidden="true"
                />
              </div>
            </div>

            {/* Subtitle */}
            <p className="mx-auto mt-8 max-w-2xl text-xl leading-relaxed text-gray-600 dark:text-gray-300">
              Conexión directa al SII, actualización en tiempo real y proyecciones para pagar a tiempo tus obligaciones.
            </p>

            {/* CTA Button */}
            <div className="mt-10 flex flex-col items-center gap-4">
              <button
                onClick={handleContactSales}
                className="group inline-flex items-center space-x-3 rounded-full bg-gradient-to-r from-blue-600 to-purple-600 px-8 py-4 text-lg font-semibold text-white shadow-xl transition-all hover:shadow-2xl hover:scale-105"
                aria-label="Acceder al pre lanzamiento de Fizko"
              >
                <Mail className="h-6 w-6" />
                <span>Accede al Pre Lanzamiento</span>
              </button>

              {/* Login secreto - aparece al hacer 5 clicks en el logo */}
              {showSecretLogin && (
                <button
                  onClick={handleGetStarted}
                  className="inline-flex items-center space-x-2 rounded-lg bg-white border border-gray-200 px-4 py-2 text-sm font-medium text-gray-700 shadow-sm transition-all hover:shadow-md hover:border-gray-300"
                  aria-label="Iniciar sesión con Google"
                >
                  <svg className="h-5 w-5" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                    <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                    <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                    <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                    <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                  </svg>
                  <span>Login con Google</span>
                </button>
              )}
            </div>

            <p className="mt-4 text-sm text-gray-500 dark:text-gray-400">
              Únete a los primeros usuarios y obtén acceso anticipado
            </p>
          </header>

          {/* Video Preview */}
          <figure className="mt-16 flex justify-center">
            {/* Desktop Video */}
            <video
              className="hidden sm:block w-full max-w-6xl"
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

            {/* Mobile Video */}
            <video
              className="block sm:hidden w-full max-w-sm mx-auto"
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
          </figure>
        </div>
      </section>

      {/* Las 3C de Fizko Section - BEFORE Features */}
      <section className="relative overflow-hidden bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 py-24" aria-labelledby="three-cs-heading">
        {/* Decorative background elements */}
        <div className="absolute inset-0 opacity-20" aria-hidden="true">
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500 rounded-full blur-3xl" />
          <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500 rounded-full blur-3xl" />
        </div>

        <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <header className="text-center mb-16">
            <h2 id="three-cs-heading" className="text-4xl font-bold text-white sm:text-5xl mb-4">
              Las 3C de Fizko
            </h2>
            <p className="text-xl text-blue-200">
              La esencia de nuestra plataforma
            </p>
          </header>

          <div className="grid gap-8 lg:grid-cols-3 lg:items-stretch">
            {/* Conecta */}
            <div className="relative group h-full">
              <div className="absolute inset-0 bg-gradient-to-r from-blue-600 to-cyan-600 rounded-3xl blur opacity-25 group-hover:opacity-40 transition duration-300" aria-hidden="true" />
              <div className="relative flex flex-col items-start h-full p-8 bg-white/10 backdrop-blur-sm rounded-3xl border border-white/20 hover:bg-white/15 transition-all duration-300">
                <div className="flex items-center justify-center w-14 h-14 mb-6 rounded-2xl bg-gradient-to-br from-blue-400 to-cyan-400 shadow-lg flex-shrink-0">
                  <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5} aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <h3 className="text-3xl font-bold text-white mb-3">Conecta</h3>
                <p className="text-lg text-blue-100 leading-relaxed">
                  tu información financiera con un click
                </p>
              </div>
            </div>

            {/* Controla */}
            <div className="relative group h-full">
              <div className="absolute inset-0 bg-gradient-to-r from-purple-600 to-pink-600 rounded-3xl blur opacity-25 group-hover:opacity-40 transition duration-300" aria-hidden="true" />
              <div className="relative flex flex-col items-start h-full p-8 bg-white/10 backdrop-blur-sm rounded-3xl border border-white/20 hover:bg-white/15 transition-all duration-300">
                <div className="flex items-center justify-center w-14 h-14 mb-6 rounded-2xl bg-gradient-to-br from-purple-400 to-pink-400 shadow-lg flex-shrink-0">
                  <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5} aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <h3 className="text-3xl font-bold text-white mb-3">Controla</h3>
                <p className="text-lg text-blue-100 leading-relaxed">
                  todos tus movimientos y crecimiento
                </p>
              </div>
            </div>

            {/* Cumple */}
            <div className="relative group h-full">
              <div className="absolute inset-0 bg-gradient-to-r from-green-600 to-emerald-600 rounded-3xl blur opacity-25 group-hover:opacity-40 transition duration-300" aria-hidden="true" />
              <div className="relative flex flex-col items-start h-full p-8 bg-white/10 backdrop-blur-sm rounded-3xl border border-white/20 hover:bg-white/15 transition-all duration-300">
                <div className="flex items-center justify-center w-14 h-14 mb-6 rounded-2xl bg-gradient-to-br from-green-400 to-emerald-400 shadow-lg flex-shrink-0">
                  <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5} aria-hidden="true">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-3xl font-bold text-white mb-3">Cumple</h3>
                <p className="text-lg text-blue-100 leading-relaxed">
                  todas tus obligaciones tributarias
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section - Connected to 3Cs */}
      <section className="relative bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 py-24" aria-labelledby="features-heading">
        {/* Connection line from 3Cs */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-1 h-12 bg-gradient-to-b from-emerald-500/50 to-transparent" aria-hidden="true" />

        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <header className="text-center mb-16">
            <h2 id="features-heading" className="text-3xl font-bold text-white sm:text-4xl mb-4">
              Qué incluye Fizko
            </h2>
            <p className="text-xl text-slate-300">
              Para cumplir con las 3C, te entregamos estas herramientas
            </p>
          </header>

          <div className="grid gap-8 md:grid-cols-3">
            {/* Feature 1 - Connects to "Conecta" */}
            <div className="relative group">
              {/* Connection indicator */}
              <div className="absolute -top-8 left-1/2 -translate-x-1/2 flex flex-col items-center" aria-hidden="true">
                <div className="w-1 h-6 bg-gradient-to-b from-blue-400/50 to-blue-400" />
                <div className="w-3 h-3 rounded-full bg-blue-400 ring-4 ring-blue-400/20" />
              </div>

              <div className="relative flex flex-col items-center bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl p-8 h-full border-2 border-blue-500/30 group-hover:border-blue-500/60 transition-all duration-300 shadow-xl">
                <div className="flex h-16 w-16 items-center justify-center rounded-xl bg-gradient-to-br from-blue-500 to-cyan-500 shadow-lg mb-6 group-hover:scale-110 transition-transform duration-300">
                  <TrendingUp className="h-8 w-8 text-white" />
                </div>
                <h3 className="text-xl font-bold text-white mb-3 text-center">
                  Información en tiempo real
                </h3>
                <p className="text-slate-300 text-center leading-relaxed text-sm">
                  Nos conectamos al SII y te actualizamos de todo lo que está pasando con tu negocio.
                </p>
              </div>
            </div>

            {/* Feature 2 - Connects to "Controla" */}
            <div className="relative group">
              {/* Connection indicator */}
              <div className="absolute -top-8 left-1/2 -translate-x-1/2 flex flex-col items-center" aria-hidden="true">
                <div className="w-1 h-6 bg-gradient-to-b from-purple-400/50 to-purple-400" />
                <div className="w-3 h-3 rounded-full bg-purple-400 ring-4 ring-purple-400/20" />
              </div>

              <div className="relative flex flex-col items-center bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl p-8 h-full border-2 border-purple-500/30 group-hover:border-purple-500/60 transition-all duration-300 shadow-xl">
                <div className="flex h-16 w-16 items-center justify-center rounded-xl bg-gradient-to-br from-purple-500 to-pink-500 shadow-lg mb-6 group-hover:scale-110 transition-transform duration-300">
                  <MessageCircle className="h-8 w-8 text-white" />
                </div>
                <h3 className="text-xl font-bold text-white mb-3 text-center">
                  Asistente disponible 24/7
                </h3>
                <p className="text-slate-300 text-center leading-relaxed text-sm">
                  Chat que resuelve todas las dudas que tengas, las 24 horas del día.
                </p>
              </div>
            </div>

            {/* Feature 3 - Connects to "Cumple" */}
            <div className="relative group">
              {/* Connection indicator */}
              <div className="absolute -top-8 left-1/2 -translate-x-1/2 flex flex-col items-center" aria-hidden="true">
                <div className="w-1 h-6 bg-gradient-to-b from-green-400/50 to-green-400" />
                <div className="w-3 h-3 rounded-full bg-green-400 ring-4 ring-green-400/20" />
              </div>

              <div className="relative flex flex-col items-center bg-gradient-to-br from-slate-800 to-slate-900 rounded-2xl p-8 h-full border-2 border-green-500/30 group-hover:border-green-500/60 transition-all duration-300 shadow-xl">
                <div className="flex h-16 w-16 items-center justify-center rounded-xl bg-gradient-to-br from-green-500 to-emerald-500 shadow-lg mb-6 group-hover:scale-110 transition-transform duration-300">
                  <CalendarCheck className="h-8 w-8 text-white" />
                </div>
                <h3 className="text-xl font-bold text-white mb-3 text-center">
                  Cumplimiento tributario
                </h3>
                <p className="text-slate-300 text-center leading-relaxed text-sm">
                  Nos encargamos de generar tus declaraciones y cumplir con las fechas que establece el SII.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-gradient-to-r from-blue-600 to-purple-600 py-16" aria-labelledby="cta-heading">
        <div className="mx-auto max-w-4xl px-4 text-center sm:px-6 lg:px-8">
          <h2 id="cta-heading" className="text-3xl font-bold text-white sm:text-4xl">
            Sé parte del futuro de la gestión tributaria
          </h2>
          <p className="mt-4 text-xl text-blue-100">
            Únete al pre lanzamiento y obtén acceso exclusivo a Fizko.
          </p>
          <button
            onClick={handleContactSales}
            className="mt-8 inline-flex items-center space-x-3 rounded-full bg-white px-8 py-4 text-lg font-semibold text-gray-700 shadow-xl transition-all hover:scale-105 hover:shadow-2xl"
            aria-label="Acceder al pre lanzamiento"
          >
            <Mail className="h-6 w-6 text-blue-600" />
            <span>Accede al Pre Lanzamiento</span>
          </button>
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
