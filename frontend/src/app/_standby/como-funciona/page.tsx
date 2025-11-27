import {
  ArrowRight,
  Shield,
  CheckCircle2,
  Sparkles,
  Brain,
  Clock,
} from "lucide-react";
import { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { LandingFooter } from "@/shared/ui/branding/LandingFooter";

export const metadata: Metadata = {
  title: "Cómo Funciona Fizko - Plataforma de Gestión Tributaria",
  description:
    "Guía completa sobre cómo Fizko automatiza la gestión tributaria de tu empresa conectándose con el SII",
};

export default function HowItWorks() {
  return (
    <main className="min-h-screen bg-white dark:bg-slate-900">
      {/* Navigation Bar */}
      <nav className="fixed w-full top-0 z-50 bg-white/80 dark:bg-slate-900/80 backdrop-blur-md border-b border-slate-200 dark:border-slate-800">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-6">
            {/* Logo a la izquierda */}
            <Link href="/" className="flex items-center gap-2">
              <Image
                src="/encabezado.png"
                alt="Fizko Icon"
                width={40}
                height={40}
                className="h-8 w-auto sm:h-10"
              />
              <Image
                src="/encabezado_fizko.svg"
                alt="Fizko"
                width={120}
                height={48}
                className="h-10 w-auto sm:h-12"
              />
            </Link>

            {/* Links de navegación y botón Entrar */}
            <div className="flex items-center gap-6">
              <Link
                href="/como-funciona"
                className="text-sm font-medium text-slate-700 hover:text-emerald-600 dark:text-slate-300 dark:hover:text-emerald-400 transition-colors hidden sm:inline-block"
              >
                Cómo Funciona
              </Link>
              <Link
                href="/login"
                className="inline-flex items-center rounded-full bg-gradient-to-r from-emerald-600 to-teal-600 px-6 py-2 text-sm font-semibold text-white shadow-sm transition-all hover:shadow-md hover:scale-105"
                aria-label="Entrar a Fizko"
              >
                <span>Entrar</span>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-16 sm:pt-40 sm:pb-24 lg:pt-48 lg:pb-32">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-slate-900 dark:text-white leading-tight mb-6">
            Te explicamos cómo funciona
          </h1>
          <p className="text-xl sm:text-2xl text-slate-600 dark:text-slate-300 leading-relaxed max-w-2xl mx-auto">
            Es más simple de lo que crees. Te conectas, revisas y listo.
          </p>
        </div>
      </section>

      {/* Main Content */}
      <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8 space-y-32 pb-32">
        {/* Section 1: Connect */}
        <section>
          <div className="flex items-start gap-4 mb-6">
            <div className="flex-shrink-0 w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center text-2xl font-bold text-white">
              1
            </div>
            <div>
              <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 dark:text-white mb-4">
                Te conectas al SII
              </h2>
              <p className="text-xl text-slate-600 dark:text-slate-300 leading-relaxed mb-8">
                Solo necesitas tu RUT y contraseña.{" "}
                <strong>Igual que cuando entras a tu cuenta del SII</strong>,
                pero nosotros lo hacemos automático por ti.
              </p>

              <div className="bg-slate-50 dark:bg-slate-800/50 rounded-3xl p-8 mb-6">
                <p className="text-slate-700 dark:text-slate-300 text-lg leading-relaxed">
                  No te preocupes por la seguridad. Usamos el mismo nivel de
                  encriptación que los bancos (AES-256) y <strong>nunca</strong>{" "}
                  guardamos tu contraseña en texto plano.
                </p>
              </div>

              <div className="space-y-3">
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="w-6 h-6 text-emerald-600 flex-shrink-0 mt-1" />
                  <p className="text-slate-600 dark:text-slate-300 text-lg">
                    Traemos <strong>todas tus facturas</strong> de compra y
                    venta
                  </p>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="w-6 h-6 text-emerald-600 flex-shrink-0 mt-1" />
                  <p className="text-slate-600 dark:text-slate-300 text-lg">
                    Actualizamos tu <strong>IVA automáticamente</strong>
                  </p>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="w-6 h-6 text-emerald-600 flex-shrink-0 mt-1" />
                  <p className="text-slate-600 dark:text-slate-300 text-lg">
                    Revisamos el estado de tu <strong>F29</strong>
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Section 2: Dashboard */}
        <section>
          <div className="flex items-start gap-4 mb-6">
            <div className="flex-shrink-0 w-12 h-12 rounded-2xl bg-gradient-to-br from-teal-500 to-cyan-500 flex items-center justify-center text-2xl font-bold text-white">
              2
            </div>
            <div>
              <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 dark:text-white mb-4">
                Revisas todo en un solo lugar
              </h2>
              <p className="text-xl text-slate-600 dark:text-slate-300 leading-relaxed mb-8">
                Olvídate de entrar al SII cada vez que necesitas algo. Nosotros
                te mostramos <strong>todo lo importante</strong> en un dashboard
                simple.
              </p>

              <div className="grid gap-4 sm:grid-cols-2 mb-8">
                <div className="bg-emerald-50 dark:bg-emerald-900/20 rounded-2xl p-6 border-2 border-emerald-200 dark:border-emerald-800">
                  <h3 className="font-bold text-slate-900 dark:text-white mb-2 text-lg">
                    Cuánto llevas vendido
                  </h3>
                  <p className="text-slate-600 dark:text-slate-300">
                    Ingresos del mes actualizados al día
                  </p>
                </div>
                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-2xl p-6 border-2 border-blue-200 dark:border-blue-800">
                  <h3 className="font-bold text-slate-900 dark:text-white mb-2 text-lg">
                    Cuánto has gastado
                  </h3>
                  <p className="text-slate-600 dark:text-slate-300">
                    Todas tus compras organizadas
                  </p>
                </div>
                <div className="bg-purple-50 dark:bg-purple-900/20 rounded-2xl p-6 border-2 border-purple-200 dark:border-purple-800">
                  <h3 className="font-bold text-slate-900 dark:text-white mb-2 text-lg">
                    Cuánto IVA debes
                  </h3>
                  <p className="text-slate-600 dark:text-slate-300">
                    Cálculo automático y preciso
                  </p>
                </div>
                <div className="bg-orange-50 dark:bg-orange-900/20 rounded-2xl p-6 border-2 border-orange-200 dark:border-orange-800">
                  <h3 className="font-bold text-slate-900 dark:text-white mb-2 text-lg">
                    Cuándo vencen tus fechas
                  </h3>
                  <p className="text-slate-600 dark:text-slate-300">
                    Calendario con todas las fechas del SII
                  </p>
                </div>
              </div>

              <p className="text-lg text-slate-600 dark:text-slate-300 leading-relaxed">
                Y si tienes más de una empresa, cambias entre ellas con un
                click.
              </p>
            </div>
          </div>
        </section>

        {/* Section 3: AI Assistant */}
        <section>
          <div className="flex items-start gap-4 mb-6">
            <div className="flex-shrink-0 w-12 h-12 rounded-2xl bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-2xl font-bold text-white">
              3
            </div>
            <div>
              <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 dark:text-white mb-4">
                Le preguntas cualquier duda
              </h2>
              <p className="text-xl text-slate-600 dark:text-slate-300 leading-relaxed mb-8">
                Tenemos un <strong>asistente con inteligencia artificial</strong>{" "}
                que sabe de impuestos. Le preguntas lo que sea y te responde al
                tiro.
              </p>

              <div className="bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-3xl p-8 mb-6 border-2 border-purple-200 dark:border-purple-800">
                <div className="flex items-start gap-4">
                  <Brain className="w-8 h-8 text-purple-600 flex-shrink-0" />
                  <div className="space-y-4">
                    <p className="text-slate-700 dark:text-slate-300 text-lg italic">
                      "¿Cuánto IVA tengo que pagar este mes?"
                    </p>
                    <p className="text-slate-700 dark:text-slate-300 text-lg italic">
                      "¿Qué pasa si me atraso con el F29?"
                    </p>
                    <p className="text-slate-700 dark:text-slate-300 text-lg italic">
                      "¿Puedo descontar esto como gasto?"
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex items-start gap-3 mb-4">
                <Clock className="w-6 h-6 text-emerald-600 flex-shrink-0 mt-1" />
                <p className="text-lg text-slate-600 dark:text-slate-300">
                  Disponible <strong>24/7</strong>, incluso fines de semana y
                  feriados
                </p>
              </div>
              <div className="flex items-start gap-3">
                <Sparkles className="w-6 h-6 text-emerald-600 flex-shrink-0 mt-1" />
                <p className="text-lg text-slate-600 dark:text-slate-300">
                  Te responde en <strong>segundos</strong>, no horas ni días
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Section 4: Compliance */}
        <section>
          <div className="flex items-start gap-4 mb-6">
            <div className="flex-shrink-0 w-12 h-12 rounded-2xl bg-gradient-to-br from-emerald-500 to-green-500 flex items-center justify-center text-2xl font-bold text-white">
              4
            </div>
            <div>
              <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 dark:text-white mb-4">
                Nunca más te atrasas
              </h2>
              <p className="text-xl text-slate-600 dark:text-slate-300 leading-relaxed mb-8">
                Te mandamos recordatorios <strong>antes</strong> de cada fecha
                importante. Por WhatsApp, email o donde prefieras.
              </p>

              <div className="space-y-3 mb-8">
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="w-6 h-6 text-emerald-600 flex-shrink-0 mt-1" />
                  <p className="text-slate-600 dark:text-slate-300 text-lg">
                    Te avisamos <strong>7 días antes</strong> del vencimiento
                    del F29
                  </p>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="w-6 h-6 text-emerald-600 flex-shrink-0 mt-1" />
                  <p className="text-slate-600 dark:text-slate-300 text-lg">
                    Pre-llenamos el formulario con <strong>tus datos reales</strong>
                  </p>
                </div>
                <div className="flex items-start gap-3">
                  <CheckCircle2 className="w-6 h-6 text-emerald-600 flex-shrink-0 mt-1" />
                  <p className="text-slate-600 dark:text-slate-300 text-lg">
                    Te alertamos si hay algo <strong>raro</strong> en tu
                    declaración
                  </p>
                </div>
              </div>

              <div className="bg-slate-50 dark:bg-slate-800/50 rounded-3xl p-8">
                <p className="text-slate-700 dark:text-slate-300 text-lg leading-relaxed">
                  En resumen:{" "}
                  <strong>te sacas el cacho de estar pendiente</strong> del SII.
                  Nosotros nos preocupamos por ti.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Security Section */}
        <section className="border-t border-slate-200 dark:border-slate-800 pt-16">
          <div className="text-center mb-12">
            <Shield className="w-16 h-16 text-emerald-600 mx-auto mb-6" />
            <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 dark:text-white mb-4">
              ¿Qué tan seguro es?
            </h2>
            <p className="text-xl text-slate-600 dark:text-slate-300 max-w-2xl mx-auto leading-relaxed">
              Muy seguro. Usamos lo mismo que usan los bancos.
            </p>
          </div>

          <div className="grid gap-6 sm:grid-cols-2">
            <div className="bg-slate-50 dark:bg-slate-800/50 rounded-2xl p-8">
              <h3 className="font-bold text-slate-900 dark:text-white mb-3 text-xl">
                Encriptación AES-256
              </h3>
              <p className="text-slate-600 dark:text-slate-300 leading-relaxed">
                El mismo nivel que usan los bancos para proteger tus
                transacciones. Nadie puede ver tus datos, ni siquiera nosotros.
              </p>
            </div>
            <div className="bg-slate-50 dark:bg-slate-800/50 rounded-2xl p-8">
              <h3 className="font-bold text-slate-900 dark:text-white mb-3 text-xl">
                Solo lectura
              </h3>
              <p className="text-slate-600 dark:text-slate-300 leading-relaxed">
                Solo <strong>leemos</strong> información del SII. No modificamos
                ni enviamos nada sin que tú lo apruebes primero.
              </p>
            </div>
            <div className="bg-slate-50 dark:bg-slate-800/50 rounded-2xl p-8">
              <h3 className="font-bold text-slate-900 dark:text-white mb-3 text-xl">
                Nunca guardamos contraseñas
              </h3>
              <p className="text-slate-600 dark:text-slate-300 leading-relaxed">
                Usamos hash criptográfico. Ni siquiera nuestro equipo técnico
                puede ver tu contraseña.
              </p>
            </div>
            <div className="bg-slate-50 dark:bg-slate-800/50 rounded-2xl p-8">
              <h3 className="font-bold text-slate-900 dark:text-white mb-3 text-xl">
                Conexión HTTPS
              </h3>
              <p className="text-slate-600 dark:text-slate-300 leading-relaxed">
                Todo lo que viaja entre tu navegador y nuestros servidores está
                cifrado de punta a punta.
              </p>
            </div>
          </div>
        </section>

        {/* Who is it for */}
        <section>
          <div className="text-center mb-12">
            <h2 className="text-3xl sm:text-4xl font-bold text-slate-900 dark:text-white mb-4">
              ¿Para quién es Fizko?
            </h2>
            <p className="text-xl text-slate-600 dark:text-slate-300 max-w-2xl mx-auto leading-relaxed">
              Para cualquiera que tenga que declarar impuestos en Chile
            </p>
          </div>

          <div className="space-y-8">
            <div className="bg-gradient-to-r from-emerald-50 to-teal-50 dark:from-emerald-900/20 dark:to-teal-900/20 rounded-3xl p-8 border-2 border-emerald-200 dark:border-emerald-800">
              <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-3">
                Si estás empezando
              </h3>
              <p className="text-lg text-slate-700 dark:text-slate-300 leading-relaxed">
                Fizko te ayuda a <strong>entender tus impuestos</strong> sin
                necesidad de contratar a un contador. Nuestro asistente te
                explica todo en palabras simples.
              </p>
            </div>

            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-3xl p-8 border-2 border-blue-200 dark:border-blue-800">
              <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-3">
                Si ya tienes una PYME
              </h3>
              <p className="text-lg text-slate-700 dark:text-slate-300 leading-relaxed">
                Fizko te <strong>ahorra horas</strong> de trabajo manual. En vez
                de revisar facturas una por una, lo ves todo organizado
                automáticamente.
              </p>
            </div>

            <div className="bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20 rounded-3xl p-8 border-2 border-purple-200 dark:border-purple-800">
              <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-3">
                Si eres contador
              </h3>
              <p className="text-lg text-slate-700 dark:text-slate-300 leading-relaxed">
                Fizko <strong>complementa tu trabajo</strong>. Tus clientes
                tienen acceso a su info en tiempo real y tú puedes revisar todo
                desde un solo lugar.
              </p>
            </div>
          </div>
        </section>
      </div>

      {/* CTA Section */}
      <section className="bg-gradient-to-br from-slate-900 via-emerald-950 to-slate-900 py-24">
        <div className="mx-auto max-w-3xl px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-4xl sm:text-5xl font-bold text-white mb-6">
            ¿Te tinca probarlo?
          </h2>
          <p className="text-xl text-emerald-100 mb-10 leading-relaxed">
            Estamos en pre lanzamiento. Los primeros usuarios entran con
            condiciones especiales.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <a
              href="mailto:contacto@fizko.cl?subject=Quiero%20probar%20Fizko"
              className="inline-flex items-center justify-center rounded-full bg-white px-8 py-4 text-lg font-semibold text-slate-900 shadow-lg hover:scale-105 transition-transform"
            >
              Solicitar Demo
            </a>
            <a
              href="https://wa.me/56975389973"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center rounded-full border-2 border-white/30 bg-white/10 px-8 py-4 text-lg font-semibold text-white hover:bg-white/20 transition-all"
            >
              Háblanos por WhatsApp
            </a>
          </div>
        </div>
      </section>

      {/* Footer */}
      <LandingFooter />

      {/* Schema.org Structured Data */}
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{
          __html: JSON.stringify({
            "@context": "https://schema.org",
            "@type": "HowTo",
            name: "Cómo funciona Fizko - Plataforma de Gestión Tributaria",
            description:
              "Guía completa sobre cómo Fizko automatiza la gestión tributaria de tu empresa conectándose con el SII",
            image: "https://fizko.cl/og-image.png",
            totalTime: "PT5M",
            estimatedCost: {
              "@type": "MonetaryAmount",
              currency: "CLP",
              value: "0",
            },
            step: [
              {
                "@type": "HowToStep",
                name: "Conecta tu empresa con el SII",
                text: "Ingresa tus credenciales del SII de forma segura. Fizko se conecta automáticamente y extrae toda tu información tributaria.",
                image: "https://fizko.cl/og-image.png",
              },
              {
                "@type": "HowToStep",
                name: "Visualiza tus datos en tiempo real",
                text: "Accede a un dashboard intuitivo con todos tus ingresos, gastos, IVA y obligaciones tributarias actualizadas automáticamente.",
                image: "https://fizko.cl/og-image.png",
              },
              {
                "@type": "HowToStep",
                name: "Cumple con tus obligaciones",
                text: "Fizko genera automáticamente tus declaraciones (F29, F22) y te notifica de fechas importantes para que nunca te atrases.",
                image: "https://fizko.cl/og-image.png",
              },
            ],
          }),
        }}
      />
    </main>
  );
}
