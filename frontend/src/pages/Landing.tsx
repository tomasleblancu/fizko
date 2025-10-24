import { ArrowRight, Zap, Shield, Clock, CheckCircle } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { DashboardPreview } from '../components/DashboardPreview';
import { DocumentsPreview } from '../components/DocumentsPreview';

export default function Landing() {
  const { signInWithGoogle } = useAuth();

  const handleGetStarted = async () => {
    await signInWithGoogle();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        {/* Decorative waves */}
        <div className="absolute inset-x-0 top-0 h-64 bg-gradient-to-b from-blue-100/50 to-transparent dark:from-blue-900/20" />

        <div className="relative mx-auto max-w-7xl px-4 py-16 sm:px-6 sm:py-24 lg:px-8">
          <div className="text-center">
            {/* Logo/Brand */}
            <div className="mb-8 flex justify-center">
              <img
                src="/encabezado.png"
                alt="Fizko"
                className="h-16 w-auto"
              />
            </div>

            {/* Main Headline */}
            <h2 className="mx-auto max-w-4xl text-4xl font-bold tracking-tight text-gray-900 dark:text-white sm:text-6xl">
              Tu negocio ya vive en el{' '}
              <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                futuro
              </span>
              .
            </h2>
            <h3 className="mx-auto mt-4 max-w-2xl text-4xl font-bold text-gray-900 dark:text-white sm:text-5xl">
              Ahora tus impuestos también.
            </h3>

            {/* Subtitle */}
            <p className="mx-auto mt-8 max-w-2xl text-xl leading-relaxed text-gray-600 dark:text-gray-300">
              Fizko se conecta con el SII,{' '}
              <span className="font-semibold text-gray-900 dark:text-white">organiza</span> ingresos
              y gastos en tiempo real,{' '}
              <span className="font-semibold text-gray-900 dark:text-white">responde</span> tus dudas
              24/7 y{' '}
              <span className="font-semibold text-gray-900 dark:text-white">proyecta</span> tus
              impuestos para pagarlos desde la app.
            </p>

            {/* CTA Button */}
            <div className="mt-10 flex justify-center">
              <button
                onClick={handleGetStarted}
                className="group inline-flex items-center space-x-3 rounded-full bg-white border-2 border-gray-200 px-8 py-4 text-lg font-semibold text-gray-700 shadow-xl transition-all hover:shadow-2xl hover:scale-105 hover:border-gray-300"
              >
                <svg className="h-6 w-6" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                </svg>
                <span>Comienza a usar Fizko</span>
              </button>
            </div>

            <p className="mt-4 text-sm text-gray-500 dark:text-gray-400">
              Inicia sesión con tu cuenta de Google
            </p>
          </div>

          {/* App Preview */}
          <div className="mt-16 flex justify-center">
            <div className="relative">
              <div className="absolute -inset-4 rounded-3xl bg-gradient-to-r from-blue-600/20 to-purple-600/20 blur-2xl" />
              <div className="relative">
                <DashboardPreview scheme="light" />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="relative bg-white py-24 dark:bg-gray-800">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white sm:text-4xl">
              Tres pasos simples
            </h2>
            <p className="mt-4 text-lg text-gray-600 dark:text-gray-300">
              Para tener el control total de tus impuestos
            </p>
          </div>

          <div className="mt-16 grid gap-8 md:grid-cols-3">
            {/* Step 1 */}
            <div className="relative">
              <div className="flex h-full flex-col items-center rounded-2xl border border-gray-200 bg-gradient-to-br from-blue-50 to-blue-100/50 p-8 text-center transition-all hover:shadow-xl dark:border-gray-700 dark:from-blue-900/20 dark:to-blue-800/10">
                <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-blue-600 to-blue-700 text-3xl font-bold text-white shadow-lg">
                  1
                </div>
                <h3 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">conectar</h3>
                <p className="mb-6 text-gray-600 dark:text-gray-300">
                  La app de Fizko se conecta al SII, y muestra los ingresos y gastos de tu negocio
                  día a día.
                </p>
                <div className="mt-auto">
                  <Shield className="h-8 w-8 text-blue-600 dark:text-blue-400" />
                  <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                    Protegemos tus claves con tecnología de cifrado avanzado, y cumplimos con todas
                    las normas de protección de datos vigentes en Chile.
                  </p>
                </div>
              </div>
            </div>

            {/* Step 2 */}
            <div className="relative">
              <div className="flex h-full flex-col items-center rounded-2xl border border-gray-200 bg-gradient-to-br from-purple-50 to-purple-100/50 p-8 text-center transition-all hover:shadow-xl dark:border-gray-700 dark:from-purple-900/20 dark:to-purple-800/10">
                <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-purple-600 to-purple-700 text-3xl font-bold text-white shadow-lg">
                  2
                </div>
                <h3 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">usar</h3>
                <p className="mb-6 text-gray-600 dark:text-gray-300">
                  Usa la app para seguir cada movimiento de tu negocio, recibir notificaciones, y
                  resolver tus preguntas con nuestro Notebook.
                </p>
                <div className="mt-auto">
                  <Clock className="h-8 w-8 text-purple-600 dark:text-purple-400" />
                  <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                    Disponible 24/7 para ayudarte con tus dudas fiscales y contables
                  </p>
                </div>
              </div>
            </div>

            {/* Step 3 */}
            <div className="relative">
              <div className="flex h-full flex-col items-center rounded-2xl border border-gray-200 bg-gradient-to-br from-green-50 to-green-100/50 p-8 text-center transition-all hover:shadow-xl dark:border-gray-700 dark:from-green-900/20 dark:to-green-800/10">
                <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-gradient-to-br from-green-600 to-green-700 text-3xl font-bold text-white shadow-lg">
                  3
                </div>
                <h3 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">declarar</h3>
                <p className="mb-6 text-gray-600 dark:text-gray-300">
                  Declara y paga tus impuestos directamente desde la app, o sigue de cerca cómo tu
                  equipo se encarga de ello.
                </p>
                <div className="mt-auto">
                  <Zap className="h-8 w-8 text-green-600 dark:text-green-400" />
                  <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                    Automatiza el proceso y ahorra tiempo en cada declaración
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Benefits Section */}
      <div className="bg-gradient-to-br from-gray-50 to-blue-50 py-24 dark:from-gray-900 dark:to-gray-800">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="grid gap-12 lg:grid-cols-2 lg:items-center">
            <div>
              <h2 className="text-3xl font-bold text-gray-900 dark:text-white sm:text-4xl">
                Control total de tu negocio en tiempo real
              </h2>
              <p className="mt-4 text-lg text-gray-600 dark:text-gray-300">
                Con Fizko tienes visibilidad completa de tu situación fiscal, proyecciones precisas
                y respuestas instantáneas a tus dudas.
              </p>
              <div className="mt-8 space-y-4">
                {[
                  'Sincronización automática con el SII',
                  'Dashboard en tiempo real con tus números',
                  'Asistente IA disponible 24/7',
                  'Proyecciones de impuestos mensuales',
                  'Gestión de F29 y documentos tributarios',
                  'Notificaciones de vencimientos importantes',
                ].map((benefit, index) => (
                  <div key={index} className="flex items-center space-x-3">
                    <CheckCircle className="h-6 w-6 flex-shrink-0 text-green-600 dark:text-green-400" />
                    <span className="text-gray-700 dark:text-gray-300">{benefit}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="relative">
              <div className="absolute -inset-4 rounded-3xl bg-gradient-to-r from-blue-600/20 to-purple-600/20 blur-2xl" />
              <div className="relative">
                <DocumentsPreview scheme="light" />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 py-16">
        <div className="mx-auto max-w-4xl px-4 text-center sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-white sm:text-4xl">
            ¿Listo para comenzar?
          </h2>
          <p className="mt-4 text-xl text-blue-100">
            Inicia sesión con tu cuenta de Google y empieza a usar Fizko.
          </p>
          <button
            onClick={handleGetStarted}
            className="mt-8 inline-flex items-center space-x-3 rounded-full bg-white px-8 py-4 text-lg font-semibold text-gray-700 shadow-xl transition-all hover:scale-105 hover:shadow-2xl"
          >
            <svg className="h-6 w-6" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
              <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
              <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
              <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
            </svg>
            <span>Comienza a usar Fizko</span>
          </button>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-white py-12 dark:bg-gray-900">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col items-center justify-between space-y-4 sm:flex-row sm:space-y-0">
            <div className="flex items-center">
              <img
                src="/encabezado.png"
                alt="Fizko"
                className="h-8 w-auto"
              />
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400">
              © 2025 Fizko. Todos los derechos reservados.
            </p>
            <div className="flex space-x-6 text-sm text-gray-600 dark:text-gray-400">
              <a href="#" className="hover:text-blue-600 dark:hover:text-blue-400">
                Términos
              </a>
              <a href="#" className="hover:text-blue-600 dark:hover:text-blue-400">
                Privacidad
              </a>
              <a href="#" className="hover:text-blue-600 dark:hover:text-blue-400">
                Contacto
              </a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
