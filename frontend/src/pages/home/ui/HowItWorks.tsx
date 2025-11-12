import { ArrowRight, Shield, Zap, CheckCircle2, TrendingUp, FileText, Calendar, MessageCircle, Users, Building2 } from 'lucide-react';
import { LandingFooter } from "@/shared/ui/branding/LandingFooter";
import { useEffect } from 'react';

export default function HowItWorks() {
  useEffect(() => {
    // Add HowTo Schema.org structured data
    const script = document.createElement('script');
    script.type = 'application/ld+json';
    script.text = JSON.stringify({
      "@context": "https://schema.org",
      "@type": "HowTo",
      "name": "Cómo funciona Fizko - Plataforma de Gestión Tributaria",
      "description": "Guía completa sobre cómo Fizko automatiza la gestión tributaria de tu empresa conectándose con el SII",
      "image": "https://fizko.cl/og-image.png",
      "totalTime": "PT5M",
      "estimatedCost": {
        "@type": "MonetaryAmount",
        "currency": "CLP",
        "value": "0"
      },
      "step": [
        {
          "@type": "HowToStep",
          "name": "Conecta tu empresa con el SII",
          "text": "Ingresa tus credenciales del SII de forma segura. Fizko se conecta automáticamente y extrae toda tu información tributaria.",
          "image": "https://fizko.cl/og-image.png"
        },
        {
          "@type": "HowToStep",
          "name": "Visualiza tus datos en tiempo real",
          "text": "Accede a un dashboard intuitivo con todos tus ingresos, gastos, IVA y obligaciones tributarias actualizadas automáticamente.",
          "image": "https://fizko.cl/og-image.png"
        },
        {
          "@type": "HowToStep",
          "name": "Cumple con tus obligaciones",
          "text": "Fizko genera automáticamente tus declaraciones (F29, F22) y te notifica de fechas importantes para que nunca te atrases.",
          "image": "https://fizko.cl/og-image.png"
        }
      ],
      "tool": [
        {
          "@type": "HowToTool",
          "name": "Asistente IA 24/7"
        },
        {
          "@type": "HowToTool",
          "name": "Conexión segura con SII"
        },
        {
          "@type": "HowToTool",
          "name": "Dashboard en tiempo real"
        }
      ]
    });
    document.head.appendChild(script);

    return () => {
      document.head.removeChild(script);
    };
  }, []);

  return (
    <main className="min-h-screen bg-white dark:bg-slate-900">
      {/* Navigation Bar */}
      <nav className="border-b border-slate-200 dark:border-slate-800">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between py-6">
            <a href="/" className="flex items-center gap-2">
              <img src="/encabezado.png" alt="Fizko Icon" className="h-8 w-auto sm:h-10" />
              <img src="/encabezado_fizko.svg" alt="Fizko" className="h-10 w-auto sm:h-12" />
            </a>
            <a
              href="/login"
              className="inline-flex items-center rounded-full bg-gradient-to-r from-emerald-600 to-teal-600 px-6 py-2 text-sm font-semibold text-white shadow-sm transition-all hover:shadow-md hover:scale-105"
            >
              Entrar
            </a>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-br from-emerald-50 via-white to-teal-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
        <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 sm:py-24 lg:px-8">
          <div className="text-center">
            <h1 className="text-4xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-5xl md:text-6xl">
              ¿Cómo funciona{" "}
              <span className="bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent">
                Fizko
              </span>
              ?
            </h1>
            <p className="mx-auto mt-6 max-w-2xl text-xl text-slate-600 dark:text-slate-300">
              Tu asistente inteligente para la gestión tributaria en Chile. Conecta, controla y cumple con tus obligaciones del SII de forma automática.
            </p>
          </div>
        </div>
      </section>

      {/* What is Fizko Section */}
      <section className="py-16 sm:py-24">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-slate-900 dark:text-white sm:text-4xl">
              ¿Qué es Fizko?
            </h2>
          </div>

          <div className="prose prose-lg dark:prose-invert max-w-none">
            <p className="text-lg text-slate-600 dark:text-slate-300 leading-relaxed">
              <strong>Fizko es una plataforma de gestión tributaria inteligente</strong> diseñada específicamente para empresas chilenas que quieren simplificar su relación con el Servicio de Impuestos Internos (SII).
            </p>

            <p className="text-lg text-slate-600 dark:text-slate-300 leading-relaxed mt-4">
              Nos conectamos de forma segura con tu cuenta del SII para extraer automáticamente toda tu información tributaria: facturas de compra y venta, DTEs, boletas electrónicas, y datos del Formulario 29. Con esta información, generamos un <strong>dashboard en tiempo real</strong> donde puedes ver el estado de tu negocio en cualquier momento.
            </p>

            <p className="text-lg text-slate-600 dark:text-slate-300 leading-relaxed mt-4">
              Además, nuestro <strong>asistente de inteligencia artificial está disponible 24/7</strong> para resolver cualquier duda tributaria que tengas, desde cómo llenar el F29 hasta consultas sobre régimen tributario, retenciones, y más.
            </p>
          </div>
        </div>
      </section>

      {/* How it Works Steps */}
      <section className="bg-slate-50 dark:bg-slate-800/50 py-16 sm:py-24">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900 dark:text-white sm:text-4xl">
              Cómo funciona en 3 simples pasos
            </h2>
            <p className="mt-4 text-xl text-slate-600 dark:text-slate-300">
              De la conexión al cumplimiento tributario en minutos
            </p>
          </div>

          <div className="space-y-12">
            {/* Step 1 */}
            <div className="relative flex flex-col md:flex-row items-start gap-8">
              <div className="flex-shrink-0">
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-500 text-2xl font-bold text-white shadow-lg">
                  1
                </div>
              </div>
              <div className="flex-1">
                <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-3">
                  <Zap className="h-7 w-7 text-emerald-600" />
                  Conecta tu empresa con el SII
                </h3>
                <p className="text-lg text-slate-600 dark:text-slate-300 leading-relaxed mb-4">
                  Ingresa tus credenciales del SII (RUT y clave) de forma segura en Fizko. Usamos encriptación de nivel bancario (AES-256) para proteger tus datos. Una vez conectado, Fizko extrae automáticamente:
                </p>
                <ul className="space-y-2 text-slate-600 dark:text-slate-300">
                  <li className="flex items-start gap-3">
                    <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-1" />
                    <span><strong>Documentos Tributarios Electrónicos (DTEs):</strong> Todas tus facturas de compra y venta</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-1" />
                    <span><strong>Boletas Electrónicas:</strong> Ventas al consumidor final</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-1" />
                    <span><strong>Formulario 29:</strong> Historial de declaraciones de IVA</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-1" />
                    <span><strong>Información del contribuyente:</strong> Datos de tu empresa y régimen tributario</span>
                  </li>
                </ul>
              </div>
            </div>

            <div className="flex justify-center">
              <ArrowRight className="h-8 w-8 text-slate-400" />
            </div>

            {/* Step 2 */}
            <div className="relative flex flex-col md:flex-row items-start gap-8">
              <div className="flex-shrink-0">
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-teal-500 to-cyan-500 text-2xl font-bold text-white shadow-lg">
                  2
                </div>
              </div>
              <div className="flex-1">
                <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-3">
                  <TrendingUp className="h-7 w-7 text-teal-600" />
                  Visualiza tus datos en tiempo real
                </h3>
                <p className="text-lg text-slate-600 dark:text-slate-300 leading-relaxed mb-4">
                  Una vez conectado, accedes a un dashboard intuitivo que organiza toda tu información tributaria de forma clara y actualizada. En tu panel de control puedes ver:
                </p>
                <ul className="space-y-2 text-slate-600 dark:text-slate-300">
                  <li className="flex items-start gap-3">
                    <CheckCircle2 className="h-5 w-5 text-teal-600 flex-shrink-0 mt-1" />
                    <span><strong>Resumen financiero:</strong> Ingresos, gastos y utilidades del mes</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <CheckCircle2 className="h-5 w-5 text-teal-600 flex-shrink-0 mt-1" />
                    <span><strong>IVA por pagar:</strong> Cálculo automático de débito y crédito fiscal</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <CheckCircle2 className="h-5 w-5 text-teal-600 flex-shrink-0 mt-1" />
                    <span><strong>Documentos organizados:</strong> Todas tus facturas y boletas en un solo lugar</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <CheckCircle2 className="h-5 w-5 text-teal-600 flex-shrink-0 mt-1" />
                    <span><strong>Calendario tributario:</strong> Fechas importantes de vencimiento del SII</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <CheckCircle2 className="h-5 w-5 text-teal-600 flex-shrink-0 mt-1" />
                    <span><strong>Análisis de tendencias:</strong> Gráficos de evolución mensual</span>
                  </li>
                </ul>
              </div>
            </div>

            <div className="flex justify-center">
              <ArrowRight className="h-8 w-8 text-slate-400" />
            </div>

            {/* Step 3 */}
            <div className="relative flex flex-col md:flex-row items-start gap-8">
              <div className="flex-shrink-0">
                <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-500 to-green-500 text-2xl font-bold text-white shadow-lg">
                  3
                </div>
              </div>
              <div className="flex-1">
                <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-3">
                  <Calendar className="h-7 w-7 text-emerald-600" />
                  Cumple con tus obligaciones tributarias
                </h3>
                <p className="text-lg text-slate-600 dark:text-slate-300 leading-relaxed mb-4">
                  Fizko no solo organiza tu información, sino que te ayuda a cumplir con el SII de forma proactiva:
                </p>
                <ul className="space-y-2 text-slate-600 dark:text-slate-300">
                  <li className="flex items-start gap-3">
                    <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-1" />
                    <span><strong>Generación automática del F29:</strong> Pre-llenado con tus datos reales del SII</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-1" />
                    <span><strong>Recordatorios inteligentes:</strong> Notificaciones antes de cada fecha de vencimiento</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-1" />
                    <span><strong>Alertas de inconsistencias:</strong> Te avisamos si detectamos errores o problemas</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-1" />
                    <span><strong>Soporte del asistente IA:</strong> Resuelve dudas sobre declaraciones 24/7</span>
                  </li>
                  <li className="flex items-start gap-3">
                    <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-1" />
                    <span><strong>Integración con WhatsApp:</strong> Recibe notificaciones directamente en tu teléfono</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Key Features Section */}
      <section className="py-16 sm:py-24">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900 dark:text-white sm:text-4xl">
              Características principales de Fizko
            </h2>
            <p className="mt-4 text-xl text-slate-600 dark:text-slate-300">
              Todo lo que necesitas para gestionar tus impuestos en una sola plataforma
            </p>
          </div>

          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
            {/* Feature 1 */}
            <div className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-8 shadow-sm hover:shadow-md transition-shadow">
              <div className="mb-4">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500">
                  <Shield className="h-6 w-6 text-white" />
                </div>
              </div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-3">
                Seguridad de nivel bancario
              </h3>
              <p className="text-slate-600 dark:text-slate-300">
                Encriptación AES-256 para proteger tus credenciales. Nunca almacenamos contraseñas en texto plano y cumplimos con estándares internacionales de seguridad.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-8 shadow-sm hover:shadow-md transition-shadow">
              <div className="mb-4">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-teal-500 to-cyan-500">
                  <MessageCircle className="h-6 w-6 text-white" />
                </div>
              </div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-3">
                Asistente IA 24/7
              </h3>
              <p className="text-slate-600 dark:text-slate-300">
                Chat inteligente que responde todas tus dudas tributarias en tiempo real. Desde cómo llenar formularios hasta consultas sobre régimen tributario y retenciones.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-8 shadow-sm hover:shadow-md transition-shadow">
              <div className="mb-4">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-emerald-500 to-green-500">
                  <FileText className="h-6 w-6 text-white" />
                </div>
              </div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-3">
                Gestión completa de DTEs
              </h3>
              <p className="text-slate-600 dark:text-slate-300">
                Todas tus facturas de compra y venta organizadas automáticamente. Filtra, busca y exporta documentos en segundos.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-8 shadow-sm hover:shadow-md transition-shadow">
              <div className="mb-4">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-500">
                  <TrendingUp className="h-6 w-6 text-white" />
                </div>
              </div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-3">
                Dashboard en tiempo real
              </h3>
              <p className="text-slate-600 dark:text-slate-300">
                Visualiza ingresos, gastos, IVA y utilidades actualizados automáticamente desde el SII. Gráficos y reportes intuitivos para tomar mejores decisiones.
              </p>
            </div>

            {/* Feature 5 */}
            <div className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-8 shadow-sm hover:shadow-md transition-shadow">
              <div className="mb-4">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-purple-500 to-pink-500">
                  <Calendar className="h-6 w-6 text-white" />
                </div>
              </div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-3">
                Calendario tributario
              </h3>
              <p className="text-slate-600 dark:text-slate-300">
                Recordatorios automáticos de fechas de vencimiento del F29, F22 y otras obligaciones. Nunca más te atrases con el SII.
              </p>
            </div>

            {/* Feature 6 */}
            <div className="rounded-2xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 p-8 shadow-sm hover:shadow-md transition-shadow">
              <div className="mb-4">
                <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-br from-green-500 to-emerald-500">
                  <Users className="h-6 w-6 text-white" />
                </div>
              </div>
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-3">
                Multi-empresa
              </h3>
              <p className="text-slate-600 dark:text-slate-300">
                ¿Tienes más de una empresa? Cambia entre empresas con un click y gestiona todas desde una sola plataforma.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Who is it for Section */}
      <section className="bg-slate-50 dark:bg-slate-800/50 py-16 sm:py-24">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl font-bold text-slate-900 dark:text-white sm:text-4xl">
              ¿Para quién es Fizko?
            </h2>
            <p className="mt-4 text-xl text-slate-600 dark:text-slate-300">
              Diseñado para emprendedores y empresas que quieren simplificar su gestión tributaria
            </p>
          </div>

          <div className="grid gap-8 md:grid-cols-3">
            {/* Emprendedores */}
            <div className="rounded-2xl bg-white dark:bg-slate-800 p-8 shadow-sm">
              <div className="mb-6">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-500">
                  <Users className="h-8 w-8 text-white" />
                </div>
              </div>
              <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">
                Emprendedores
              </h3>
              <p className="text-slate-600 dark:text-slate-300 mb-4">
                Si estás comenzando tu negocio y quieres entender tus impuestos sin complicarte, Fizko es para ti.
              </p>
              <ul className="space-y-2 text-slate-600 dark:text-slate-300">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                  <span>Interface simple e intuitiva</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                  <span>Asistente IA para resolver dudas básicas</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                  <span>Automatización del F29</span>
                </li>
              </ul>
            </div>

            {/* PYMEs */}
            <div className="rounded-2xl bg-white dark:bg-slate-800 p-8 shadow-sm border-2 border-emerald-500">
              <div className="mb-6">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-teal-500 to-cyan-500">
                  <Building2 className="h-8 w-8 text-white" />
                </div>
                <span className="inline-block mt-2 text-sm font-semibold text-emerald-600 dark:text-emerald-400">
                  Más Popular
                </span>
              </div>
              <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">
                PYMEs
              </h3>
              <p className="text-slate-600 dark:text-slate-300 mb-4">
                Si tienes un negocio establecido con múltiples facturas al mes, Fizko te ahorra tiempo y reduce errores.
              </p>
              <ul className="space-y-2 text-slate-600 dark:text-slate-300">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-5 w-5 text-teal-600 flex-shrink-0 mt-0.5" />
                  <span>Gestión de cientos de DTEs</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-5 w-5 text-teal-600 flex-shrink-0 mt-0.5" />
                  <span>Dashboard financiero completo</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-5 w-5 text-teal-600 flex-shrink-0 mt-0.5" />
                  <span>Multi-empresa incluido</span>
                </li>
              </ul>
            </div>

            {/* Contadores */}
            <div className="rounded-2xl bg-white dark:bg-slate-800 p-8 shadow-sm">
              <div className="mb-6">
                <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-emerald-500 to-green-500">
                  <FileText className="h-8 w-8 text-white" />
                </div>
              </div>
              <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-4">
                Contadores
              </h3>
              <p className="text-slate-600 dark:text-slate-300 mb-4">
                Si eres contador y manejas múltiples clientes, Fizko complementa tu trabajo con automatización.
              </p>
              <ul className="space-y-2 text-slate-600 dark:text-slate-300">
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                  <span>Acceso a múltiples empresas</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                  <span>Exportación de reportes</span>
                </li>
                <li className="flex items-start gap-2">
                  <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                  <span>Vista consolidada de clientes</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Security Section */}
      <section className="py-16 sm:py-24">
        <div className="mx-auto max-w-4xl px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-slate-900 dark:text-white sm:text-4xl">
              Tu seguridad es nuestra prioridad
            </h2>
            <p className="mt-4 text-xl text-slate-600 dark:text-slate-300">
              Protegemos tu información con los más altos estándares de seguridad
            </p>
          </div>

          <div className="prose prose-lg dark:prose-invert max-w-none">
            <div className="bg-white dark:bg-slate-800 rounded-2xl p-8 shadow-sm border border-slate-200 dark:border-slate-700">
              <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-4 flex items-center gap-3">
                <Shield className="h-6 w-6 text-emerald-600" />
                ¿Cómo protegemos tus credenciales del SII?
              </h3>
              <ul className="space-y-3 text-slate-600 dark:text-slate-300">
                <li className="flex items-start gap-3">
                  <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-1" />
                  <span><strong>Encriptación AES-256:</strong> El mismo nivel de seguridad que usan los bancos para proteger transacciones financieras</span>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-1" />
                  <span><strong>Nunca almacenamos contraseñas en texto plano:</strong> Usamos hash criptográfico para que nadie pueda ver tu contraseña, ni siquiera nuestro equipo</span>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-1" />
                  <span><strong>Conexión HTTPS:</strong> Toda la comunicación entre tu navegador y nuestros servidores está cifrada</span>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-1" />
                  <span><strong>Auditorías de seguridad regulares:</strong> Revisamos constantemente nuestros sistemas para detectar y prevenir vulnerabilidades</span>
                </li>
                <li className="flex items-start gap-3">
                  <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-1" />
                  <span><strong>Solo lectura:</strong> Fizko únicamente lee información del SII, nunca modifica ni envía declaraciones sin tu autorización explícita</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-gradient-to-br from-slate-900 via-emerald-950 to-slate-900 py-16 sm:py-24">
        <div className="mx-auto max-w-4xl px-4 text-center sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-white sm:text-4xl">
            ¿Listo para simplificar tu gestión tributaria?
          </h2>
          <p className="mt-4 text-xl text-emerald-100">
            Únete a empresas que ya usan Fizko para automatizar sus impuestos
          </p>
          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
            <a
              href="mailto:contacto@fizko.cl?subject=Solicitud%20de%20Demo%20Fizko"
              className="inline-flex items-center rounded-full bg-white px-8 py-4 text-lg font-semibold text-slate-900 shadow-lg transition-all hover:scale-105 hover:shadow-xl"
            >
              Solicitar Demo
            </a>
            <a
              href="/"
              className="inline-flex items-center rounded-full border-2 border-white/30 bg-white/10 px-8 py-4 text-lg font-semibold text-white transition-all hover:bg-white/20"
            >
              Volver al Inicio
            </a>
          </div>
        </div>
      </section>

      {/* Footer */}
      <LandingFooter />
    </main>
  );
}
