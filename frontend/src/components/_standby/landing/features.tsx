import { TrendingUp, MessageCircle, CalendarCheck } from "lucide-react";

export function Features() {
  return (
    <section
      className="relative bg-white dark:bg-slate-900 py-20 transition-colors"
      aria-labelledby="features-heading"
    >
      <div className="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
        <header className="text-center mb-12">
          <h2
            id="features-heading"
            className="text-3xl font-bold text-slate-900 dark:text-white mb-3"
          >
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
                Nos conectamos al SII y te actualizamos de todo lo que está
                pasando con tu negocio.
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
                Chat que resuelve todas las dudas que tengas, las 24 horas del
                día.
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
                Nos encargamos de generar tus declaraciones y cumplir con las
                fechas que establece el SII.
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
