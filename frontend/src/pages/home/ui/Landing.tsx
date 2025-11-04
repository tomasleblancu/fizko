import { TrendingUp, MessageCircle, CalendarCheck, Mail } from 'lucide-react';
import { useState } from 'react';
import { useAuth } from "@/app/providers/AuthContext";
import { DashboardPreview } from "@/features/dashboard/ui/DashboardPreview";
import { DocumentsPreview } from "@/shared/ui/DocumentsPreview";
import { LandingFooter } from "@/shared/ui/branding/LandingFooter";
import { ContactSalesDialog } from "./ContactSalesDialog";

export default function Landing() {
  const { signInWithGoogle } = useAuth();
  const [secretClickCount, setSecretClickCount] = useState(0);
  const [showSecretLogin, setShowSecretLogin] = useState(false);
  const [isContactDialogOpen, setIsContactDialogOpen] = useState(false);

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
      <section className="relative overflow-hidden" aria-label="Hero">
        {/* Decorative waves */}
        <div className="absolute inset-x-0 top-0 h-64 bg-gradient-to-b from-blue-100/50 to-transparent dark:from-blue-900/20" aria-hidden="true" />

        <div className="relative mx-auto max-w-7xl px-4 py-16 sm:px-6 sm:py-24 lg:px-8">
          <header className="text-center">
            {/* Logo/Brand - Click 5 veces para mostrar login */}
            <div
              className="mb-8 flex justify-center"
              onClick={handleSecretClick}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && handleSecretClick()}
            >
              <img
                src="/encabezado.png"
                alt="Fizko - Plataforma de Gestión Tributaria Inteligente"
                className="h-16 w-auto cursor-pointer"
              />
            </div>

            {/* Main Headline */}
            <h1 className="mx-auto max-w-4xl text-4xl font-bold tracking-tight text-gray-900 dark:text-white sm:text-6xl">
              Tus números, claros.{' '}
              <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Tus impuestos, bajo control.
              </span>
            </h1>

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

          {/* App Preview */}
          <figure className="mt-16 flex justify-center">
            <div className="relative">
              <div className="absolute -inset-4 rounded-3xl bg-gradient-to-r from-blue-600/20 to-purple-600/20 blur-2xl" aria-hidden="true" />
              <div className="relative">
                <DashboardPreview scheme="light" />
              </div>
            </div>
          </figure>
        </div>
      </section>

      {/* Features Section */}
      <section className="relative bg-white py-24 dark:bg-gray-800" aria-labelledby="features-heading">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <header className="text-center">
            <h2 id="features-heading" className="text-3xl font-bold text-gray-900 dark:text-white sm:text-4xl">
              Tres pasos simples
            </h2>
            <p className="mt-4 text-lg text-gray-600 dark:text-gray-300">
              Para tener el control total de tus impuestos
            </p>
          </header>

          <div className="mt-16 grid gap-8 md:grid-cols-3">
            {/* Step 1 */}
            <div className="relative">
              <div className="flex h-full flex-col items-center rounded-2xl border border-gray-200 bg-gradient-to-br from-blue-50 to-blue-100/50 p-8 text-center transition-all hover:shadow-xl dark:border-gray-700 dark:from-blue-900/20 dark:to-blue-800/10">
                <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-blue-600 to-blue-700 shadow-lg">
                  <TrendingUp className="h-8 w-8 text-white" />
                </div>
                <h3 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">Información en tiempo real</h3>
                <p className="text-gray-600 dark:text-gray-300">
                  Nos conectamos al SII y te actualizamos de todo lo que está pasando con tu negocio.
                </p>
              </div>
            </div>

            {/* Step 2 */}
            <div className="relative">
              <div className="flex h-full flex-col items-center rounded-2xl border border-gray-200 bg-gradient-to-br from-purple-50 to-purple-100/50 p-8 text-center transition-all hover:shadow-xl dark:border-gray-700 dark:from-purple-900/20 dark:to-purple-800/10">
                <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-purple-600 to-purple-700 shadow-lg">
                  <MessageCircle className="h-8 w-8 text-white" />
                </div>
                <h3 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">Asistente disponible 24/7</h3>
                <p className="text-gray-600 dark:text-gray-300">
                  Chat que resuelve todas las dudas que tengas, las 24 horas del día.
                </p>
              </div>
            </div>

            {/* Step 3 */}
            <div className="relative">
              <div className="flex h-full flex-col items-center rounded-2xl border border-gray-200 bg-gradient-to-br from-green-50 to-green-100/50 p-8 text-center transition-all hover:shadow-xl dark:border-gray-700 dark:from-green-900/20 dark:to-green-800/10">
                <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-green-600 to-green-700 shadow-lg">
                  <CalendarCheck className="h-8 w-8 text-white" />
                </div>
                <h3 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">Calendario tributario</h3>
                <p className="text-gray-600 dark:text-gray-300">
                  Nos encargamos de generar tus declaraciones y cumplir con las fechas que establece el SII.
                </p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Video Demo Section */}
      <section className="bg-gradient-to-br from-gray-50 to-blue-50 py-24 dark:from-gray-900 dark:to-gray-800" aria-labelledby="demo-heading">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <header className="text-center">
            <h2 id="demo-heading" className="text-3xl font-bold text-gray-900 dark:text-white sm:text-4xl">
              Mira cómo funciona
            </h2>
            <p className="mt-4 text-lg text-gray-600 dark:text-gray-300">
              Un vistazo rápido a la plataforma en acción
            </p>
          </header>

          <div className="mt-12 flex justify-center">
            <div className="relative w-full max-w-5xl">
              <div className="absolute -inset-4 rounded-3xl bg-gradient-to-r from-blue-600/20 to-purple-600/20 blur-2xl" aria-hidden="true" />
              <div className="relative overflow-hidden rounded-2xl bg-gray-900 shadow-2xl">
                {/* Video player - replace /demo-video.mp4 with your actual video path */}
                <video
                  className="w-full"
                  controls
                  poster="/video-poster.jpg"
                  aria-label="Video demostrativo de la plataforma Fizko mostrando cambio de empresa, agregar trabajador y chat en acción"
                >
                  <source src="/demo-video.mp4" type="video/mp4" />
                  <source src="/demo-video.webm" type="video/webm" />
                  Tu navegador no soporta la reproducción de video. Por favor actualiza tu navegador.
                </video>
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
