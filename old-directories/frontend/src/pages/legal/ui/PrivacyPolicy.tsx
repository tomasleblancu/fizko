import { ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import { LandingFooter } from "@/shared/ui/branding/LandingFooter";

export default function PrivacyPolicy() {
  return (
    <main className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900">
      <div className="mx-auto max-w-4xl px-4 py-16 sm:px-6 lg:px-8">
        {/* Back Button */}
        <Link
          to="/"
          className="mb-8 inline-flex items-center space-x-2 text-sm text-gray-600 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Volver al inicio</span>
        </Link>

        {/* Header */}
        <header className="mb-12">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white sm:text-5xl">
            Política de Privacidad
          </h1>
          <p className="mt-4 text-lg text-gray-600 dark:text-gray-300">
            Última actualización: Enero 2025
          </p>
        </header>

        {/* Content */}
        <article className="prose prose-lg dark:prose-invert max-w-none">
          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              1. Introducción
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              En Fizko, nos tomamos muy en serio la privacidad y la protección de los datos
              personales de nuestros usuarios. Esta Política de Privacidad describe cómo
              recopilamos, usamos, almacenamos y protegemos su información personal cuando utiliza
              nuestra plataforma de gestión tributaria.
            </p>
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              Esta política se aplica a todos los servicios ofrecidos por Fizko a través de su
              aplicación web y móvil, y cumple con las disposiciones de la Ley N° 19.628 sobre
              Protección de la Vida Privada y sus modificaciones, así como con todas las normativas
              vigentes en Chile sobre protección de datos personales.
            </p>
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              Al utilizar nuestros servicios, usted acepta las prácticas descritas en esta Política
              de Privacidad. Le recomendamos leer este documento detenidamente.
            </p>
          </section>

          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              2. Responsable del tratamiento de datos
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              El responsable del tratamiento de sus datos personales es:
            </p>
            <div className="mt-4 rounded-lg bg-blue-50 p-4 dark:bg-blue-900/20">
              <p className="font-semibold text-gray-900 dark:text-white">Fizko</p>
              <p className="mt-2 text-gray-700 dark:text-gray-300">
                <strong>Correo electrónico:</strong> privacidad@fizko.com
              </p>
              <p className="mt-1 text-gray-700 dark:text-gray-300">
                <strong>Correo electrónico de contacto general:</strong> soporte@fizko.com
              </p>
            </div>
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              Para ejercer sus derechos sobre sus datos personales o realizar consultas relacionadas
              con esta política, puede contactarnos a través de los medios indicados anteriormente.
            </p>
          </section>

          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              3. Datos personales que recopilamos
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              Recopilamos diferentes categorías de datos personales necesarios para proporcionar
              nuestros servicios:
            </p>

            <h3 className="mb-3 mt-6 text-xl font-semibold text-gray-900 dark:text-white">
              3.1 Datos de identificación y contacto
            </h3>
            <ul className="mt-2 list-disc space-y-2 pl-6 text-gray-700 dark:text-gray-300">
              <li>Nombre completo</li>
              <li>Correo electrónico (obtenido de su cuenta de Google)</li>
              <li>Número de teléfono (si se proporciona para notificaciones por WhatsApp)</li>
              <li>Foto de perfil (de su cuenta de Google)</li>
              <li>RUT (Rol Único Tributario)</li>
              <li>Razón social o nombre comercial de su empresa</li>
            </ul>

            <h3 className="mb-3 mt-6 text-xl font-semibold text-gray-900 dark:text-white">
              3.2 Credenciales y datos de acceso
            </h3>
            <ul className="mt-2 list-disc space-y-2 pl-6 text-gray-700 dark:text-gray-300">
              <li>
                Credenciales del SII (usuario y contraseña) - almacenadas con cifrado de extremo a
                extremo
              </li>
              <li>Token de autenticación de Google</li>
              <li>Dirección IP y datos de sesión</li>
              <li>Información del dispositivo y navegador utilizado</li>
            </ul>

            <h3 className="mb-3 mt-6 text-xl font-semibold text-gray-900 dark:text-white">
              3.3 Datos tributarios y financieros
            </h3>
            <ul className="mt-2 list-disc space-y-2 pl-6 text-gray-700 dark:text-gray-300">
              <li>
                Documentos tributarios electrónicos (facturas emitidas y recibidas, boletas, notas
                de crédito, notas de débito, guías de despacho)
              </li>
              <li>Información de ingresos y gastos de su negocio</li>
              <li>Declaraciones mensuales (Formulario 29) y sus movimientos</li>
              <li>Información de pagos de impuestos realizados</li>
              <li>Datos de cuentas bancarias (si se proporcionan para pagos)</li>
              <li>Historial de transacciones en la plataforma</li>
            </ul>

            <h3 className="mb-3 mt-6 text-xl font-semibold text-gray-900 dark:text-white">
              3.4 Datos de uso y comportamiento
            </h3>
            <ul className="mt-2 list-disc space-y-2 pl-6 text-gray-700 dark:text-gray-300">
              <li>Registro de actividades dentro de la plataforma</li>
              <li>Consultas realizadas al asistente virtual (Notebook)</li>
              <li>Preferencias de configuración y personalización</li>
              <li>Datos de navegación y páginas visitadas</li>
              <li>Tiempo de uso y frecuencia de acceso</li>
              <li>Interacciones con notificaciones y alertas</li>
            </ul>

            <h3 className="mb-3 mt-6 text-xl font-semibold text-gray-900 dark:text-white">
              3.5 Datos técnicos
            </h3>
            <ul className="mt-2 list-disc space-y-2 pl-6 text-gray-700 dark:text-gray-300">
              <li>Cookies y tecnologías similares</li>
              <li>Logs de sistema y registros de errores</li>
              <li>Información de diagnóstico y rendimiento</li>
              <li>Metadatos de archivos y documentos</li>
            </ul>
          </section>

          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              4. Cómo recopilamos sus datos
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              Recopilamos datos personales de las siguientes maneras:
            </p>

            <h3 className="mb-3 mt-6 text-xl font-semibold text-gray-900 dark:text-white">
              4.1 Datos proporcionados directamente por usted
            </h3>
            <ul className="mt-2 list-disc space-y-2 pl-6 text-gray-700 dark:text-gray-300">
              <li>Durante el proceso de registro e inicio de sesión con Google</li>
              <li>Al conectar su cuenta del SII con Fizko</li>
              <li>Al configurar su perfil y preferencias</li>
              <li>Al utilizar el asistente virtual y hacer consultas</li>
              <li>Al contactar a nuestro equipo de soporte</li>
              <li>Al realizar pagos o actualizar información de facturación</li>
            </ul>

            <h3 className="mb-3 mt-6 text-xl font-semibold text-gray-900 dark:text-white">
              4.2 Datos recopilados automáticamente
            </h3>
            <ul className="mt-2 list-disc space-y-2 pl-6 text-gray-700 dark:text-gray-300">
              <li>
                Información obtenida del SII mediante nuestra conexión segura (documentos
                tributarios, declaraciones, movimientos)
              </li>
              <li>Datos de uso y navegación a través de cookies y tecnologías similares</li>
              <li>Información técnica sobre su dispositivo y conexión</li>
              <li>Logs de acceso y actividad en la plataforma</li>
            </ul>

            <h3 className="mb-3 mt-6 text-xl font-semibold text-gray-900 dark:text-white">
              4.3 Datos de terceros
            </h3>
            <ul className="mt-2 list-disc space-y-2 pl-6 text-gray-700 dark:text-gray-300">
              <li>Información de perfil de su cuenta de Google (nombre, correo, foto)</li>
              <li>Datos públicos del SII relacionados con su actividad tributaria</li>
              <li>
                Información de procesadores de pago cuando realiza transacciones (con su
                consentimiento)
              </li>
            </ul>
          </section>

          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              5. Finalidad y base legal del tratamiento
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              Utilizamos sus datos personales para los siguientes propósitos y con las siguientes
              bases legales:
            </p>

            <h3 className="mb-3 mt-6 text-xl font-semibold text-gray-900 dark:text-white">
              5.1 Prestación de servicios (base legal: ejecución del contrato)
            </h3>
            <ul className="mt-2 list-disc space-y-2 pl-6 text-gray-700 dark:text-gray-300">
              <li>Crear y gestionar su cuenta de usuario</li>
              <li>Conectar de forma segura con el SII y obtener su información tributaria</li>
              <li>Procesar y organizar sus documentos tributarios</li>
              <li>Generar reportes, dashboards y proyecciones de impuestos</li>
              <li>Proporcionar el servicio de asistente virtual para consultas</li>
              <li>Enviar notificaciones sobre vencimientos y obligaciones importantes</li>
              <li>Facilitar el pago de impuestos desde la plataforma</li>
            </ul>

            <h3 className="mb-3 mt-6 text-xl font-semibold text-gray-900 dark:text-white">
              5.2 Mejora y desarrollo de servicios (base legal: interés legítimo)
            </h3>
            <ul className="mt-2 list-disc space-y-2 pl-6 text-gray-700 dark:text-gray-300">
              <li>Analizar el uso de la plataforma para mejorar la experiencia del usuario</li>
              <li>Desarrollar nuevas funcionalidades y servicios</li>
              <li>Entrenar y mejorar nuestros modelos de inteligencia artificial</li>
              <li>Realizar análisis estadísticos y de tendencias (datos anonimizados)</li>
              <li>Optimizar el rendimiento y la seguridad de la plataforma</li>
            </ul>

            <h3 className="mb-3 mt-6 text-xl font-semibold text-gray-900 dark:text-white">
              5.3 Seguridad y prevención de fraude (base legal: interés legítimo y obligación
              legal)
            </h3>
            <ul className="mt-2 list-disc space-y-2 pl-6 text-gray-700 dark:text-gray-300">
              <li>Detectar y prevenir actividades fraudulentas o no autorizadas</li>
              <li>Proteger la seguridad de la plataforma y de nuestros usuarios</li>
              <li>Verificar la identidad de los usuarios</li>
              <li>Cumplir con obligaciones legales y regulatorias</li>
              <li>Responder a solicitudes legales de autoridades competentes</li>
            </ul>

            <h3 className="mb-3 mt-6 text-xl font-semibold text-gray-900 dark:text-white">
              5.4 Comunicaciones y soporte (base legal: ejecución del contrato y consentimiento)
            </h3>
            <ul className="mt-2 list-disc space-y-2 pl-6 text-gray-700 dark:text-gray-300">
              <li>Responder a sus consultas y solicitudes de soporte</li>
              <li>Enviar notificaciones importantes sobre el servicio</li>
              <li>Informar sobre cambios en los términos o políticas</li>
              <li>
                Enviar comunicaciones promocionales (solo con su consentimiento explícito, que puede
                revocar en cualquier momento)
              </li>
            </ul>

            <h3 className="mb-3 mt-6 text-xl font-semibold text-gray-900 dark:text-white">
              5.5 Cumplimiento de obligaciones legales (base legal: obligación legal)
            </h3>
            <ul className="mt-2 list-disc space-y-2 pl-6 text-gray-700 dark:text-gray-300">
              <li>Cumplir con requisitos contables y fiscales</li>
              <li>Responder a requerimientos de autoridades competentes</li>
              <li>Conservar registros según lo exigido por la legislación chilena</li>
            </ul>
          </section>

          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              6. Con quién compartimos sus datos
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              Fizko no vende ni alquila sus datos personales a terceros. Compartimos su información
              únicamente en las siguientes circunstancias:
            </p>

            <h3 className="mb-3 mt-6 text-xl font-semibold text-gray-900 dark:text-white">
              6.1 Proveedores de servicios
            </h3>
            <p className="text-gray-700 dark:text-gray-300">
              Compartimos datos con proveedores de servicios que nos ayudan a operar nuestra
              plataforma, tales como:
            </p>
            <ul className="mt-2 list-disc space-y-2 pl-6 text-gray-700 dark:text-gray-300">
              <li>Proveedores de servicios de hosting y almacenamiento en la nube</li>
              <li>Servicios de autenticación (Google OAuth)</li>
              <li>Procesadores de pagos</li>
              <li>Proveedores de servicios de inteligencia artificial y procesamiento de datos</li>
              <li>Servicios de análisis y monitoreo</li>
              <li>Servicios de notificaciones y comunicaciones (email, WhatsApp)</li>
            </ul>
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              Todos estos proveedores están contractualmente obligados a proteger sus datos y solo
              pueden usarlos para los fines específicos que les hemos encomendado.
            </p>

            <h3 className="mb-3 mt-6 text-xl font-semibold text-gray-900 dark:text-white">
              6.2 Autoridades y cumplimiento legal
            </h3>
            <p className="text-gray-700 dark:text-gray-300">
              Podemos divulgar sus datos personales cuando:
            </p>
            <ul className="mt-2 list-disc space-y-2 pl-6 text-gray-700 dark:text-gray-300">
              <li>Sea requerido por ley, orden judicial o regulación gubernamental</li>
              <li>Sea necesario para proteger nuestros derechos legales</li>
              <li>Se requiera para prevenir fraude o actividades ilegales</li>
              <li>Sea necesario para proteger la seguridad de nuestros usuarios</li>
            </ul>

            <h3 className="mb-3 mt-6 text-xl font-semibold text-gray-900 dark:text-white">
              6.3 Transferencias empresariales
            </h3>
            <p className="text-gray-700 dark:text-gray-300">
              En caso de fusión, adquisición, venta de activos o reestructuración empresarial, sus
              datos personales podrían ser transferidos a la entidad sucesora, siempre bajo las
              mismas obligaciones de protección de datos.
            </p>

            <h3 className="mb-3 mt-6 text-xl font-semibold text-gray-900 dark:text-white">
              6.4 Con su consentimiento
            </h3>
            <p className="text-gray-700 dark:text-gray-300">
              En cualquier otro caso, compartiremos sus datos solo con su consentimiento explícito.
            </p>
          </section>

          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              7. Transferencias internacionales de datos
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              Algunos de nuestros proveedores de servicios pueden estar ubicados fuera de Chile,
              incluyendo en países de la Unión Europea y Estados Unidos. Cuando transferimos datos
              personales a otros países, nos aseguramos de que:
            </p>
            <ul className="mt-4 list-disc space-y-2 pl-6 text-gray-700 dark:text-gray-300">
              <li>
                Los proveedores cuenten con medidas de seguridad adecuadas conforme a estándares
                internacionales
              </li>
              <li>
                Se implementen cláusulas contractuales estándar u otros mecanismos de protección
                apropiados
              </li>
              <li>
                Los datos sean tratados con el mismo nivel de protección exigido por la legislación
                chilena
              </li>
            </ul>
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              Al utilizar nuestros servicios, usted consiente estas transferencias internacionales
              bajo las salvaguardas descritas.
            </p>
          </section>

          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              8. Plazo de conservación de datos
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              Conservamos sus datos personales durante el tiempo necesario para cumplir con las
              finalidades descritas en esta política, a menos que la ley requiera o permita un
              período de conservación más largo.
            </p>

            <h3 className="mb-3 mt-6 text-xl font-semibold text-gray-900 dark:text-white">
              Criterios de conservación:
            </h3>
            <ul className="mt-2 list-disc space-y-2 pl-6 text-gray-700 dark:text-gray-300">
              <li>
                <strong>Datos de cuenta activa:</strong> Mientras su cuenta esté activa y durante
                el período que utilice nuestros servicios
              </li>
              <li>
                <strong>Datos tributarios:</strong> Mínimo 6 años desde su generación, conforme a
                las obligaciones del Código Tributario chileno
              </li>
              <li>
                <strong>Datos de facturación:</strong> De acuerdo con los plazos legales de
                conservación de documentos contables (generalmente 6 años)
              </li>
              <li>
                <strong>Datos de comunicaciones:</strong> Durante el tiempo necesario para
                proporcionar soporte y resolver consultas
              </li>
              <li>
                <strong>Logs y datos técnicos:</strong> Típicamente entre 90 días y 2 años, según
                su propósito
              </li>
            </ul>

            <p className="mt-4 text-gray-700 dark:text-gray-300">
              Una vez que cancele su cuenta, conservaremos acceso de solo lectura a sus datos por 30
              días. Después de este período, sus datos serán eliminados o anonimizados, excepto
              aquellos que debamos conservar por obligaciones legales.
            </p>
          </section>

          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              9. Seguridad de sus datos
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              La seguridad de sus datos personales es una prioridad absoluta para Fizko.
              Implementamos múltiples capas de medidas de seguridad técnicas y organizativas:
            </p>

            <h3 className="mb-3 mt-6 text-xl font-semibold text-gray-900 dark:text-white">
              Medidas técnicas:
            </h3>
            <ul className="mt-2 list-disc space-y-2 pl-6 text-gray-700 dark:text-gray-300">
              <li>
                <strong>Cifrado de extremo a extremo:</strong> Sus credenciales del SII se almacenan
                con tecnología de cifrado avanzado
              </li>
              <li>
                <strong>Cifrado en tránsito:</strong> Todas las comunicaciones utilizan HTTPS/TLS
              </li>
              <li>
                <strong>Cifrado en reposo:</strong> Los datos almacenados están cifrados en nuestros
                servidores
              </li>
              <li>
                <strong>Autenticación segura:</strong> Utilizamos OAuth 2.0 con Google para
                autenticación
              </li>
              <li>
                <strong>Firewalls y sistemas de detección:</strong> Protección contra accesos no
                autorizados
              </li>
              <li>
                <strong>Monitoreo continuo:</strong> Detección y respuesta ante incidentes de
                seguridad 24/7
              </li>
              <li>
                <strong>Backups regulares:</strong> Copias de seguridad cifradas para recuperación
                ante desastres
              </li>
            </ul>

            <h3 className="mb-3 mt-6 text-xl font-semibold text-gray-900 dark:text-white">
              Medidas organizativas:
            </h3>
            <ul className="mt-2 list-disc space-y-2 pl-6 text-gray-700 dark:text-gray-300">
              <li>
                Acceso restringido a datos personales solo para personal autorizado y con necesidad
                de acceso
              </li>
              <li>
                Acuerdos de confidencialidad con todos los empleados y proveedores
              </li>
              <li>Capacitación regular en seguridad y protección de datos</li>
              <li>Auditorías de seguridad periódicas</li>
              <li>Procedimientos de respuesta ante incidentes</li>
              <li>Controles de acceso basados en roles y principio de mínimo privilegio</li>
            </ul>

            <p className="mt-4 text-gray-700 dark:text-gray-300">
              Sin embargo, ningún método de transmisión por internet o almacenamiento electrónico es
              100% seguro. Aunque nos esforzamos por proteger sus datos personales, no podemos
              garantizar su seguridad absoluta.
            </p>

            <div className="mt-4 rounded-lg bg-yellow-50 p-4 dark:bg-yellow-900/20">
              <p className="font-semibold text-gray-900 dark:text-white">
                Recomendaciones de seguridad para usuarios:
              </p>
              <ul className="mt-2 list-disc space-y-1 pl-6 text-gray-700 dark:text-gray-300">
                <li>Mantenga la confidencialidad de sus credenciales de acceso</li>
                <li>Utilice contraseñas fuertes y únicas</li>
                <li>No comparta su cuenta con terceros</li>
                <li>Cierre sesión al usar dispositivos compartidos</li>
                <li>Mantenga actualizado su navegador y sistema operativo</li>
                <li>Reporte inmediatamente cualquier actividad sospechosa</li>
              </ul>
            </div>
          </section>

          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              10. Sus derechos sobre sus datos personales
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              De acuerdo con la Ley N° 19.628 sobre Protección de la Vida Privada y normativas
              complementarias, usted tiene los siguientes derechos:
            </p>

            <h3 className="mb-3 mt-6 text-xl font-semibold text-gray-900 dark:text-white">
              10.1 Derecho de información
            </h3>
            <p className="text-gray-700 dark:text-gray-300">
              Tiene derecho a ser informado sobre qué datos personales tenemos sobre usted, cómo los
              usamos, con quién los compartimos y por cuánto tiempo los conservamos.
            </p>

            <h3 className="mb-3 mt-6 text-xl font-semibold text-gray-900 dark:text-white">
              10.2 Derecho de acceso
            </h3>
            <p className="text-gray-700 dark:text-gray-300">
              Puede solicitar una copia de sus datos personales que procesamos. Proporcionaremos
              esta información en un formato estructurado y de uso común.
            </p>

            <h3 className="mb-3 mt-6 text-xl font-semibold text-gray-900 dark:text-white">
              10.3 Derecho de rectificación (modificación)
            </h3>
            <p className="text-gray-700 dark:text-gray-300">
              Puede solicitar la corrección de datos personales inexactos o incompletos. Muchos de
              sus datos pueden ser actualizados directamente desde la configuración de su cuenta.
            </p>

            <h3 className="mb-3 mt-6 text-xl font-semibold text-gray-900 dark:text-white">
              10.4 Derecho de cancelación (eliminación)
            </h3>
            <p className="text-gray-700 dark:text-gray-300">
              Puede solicitar la eliminación de sus datos personales cuando ya no sean necesarios
              para los fines para los que fueron recopilados, o cuando retire su consentimiento,
              sujeto a nuestras obligaciones legales de conservación.
            </p>

            <h3 className="mb-3 mt-6 text-xl font-semibold text-gray-900 dark:text-white">
              10.5 Derecho de bloqueo
            </h3>
            <p className="text-gray-700 dark:text-gray-300">
              Puede solicitar el bloqueo temporal de sus datos para evitar su tratamiento mientras
              se verifica la exactitud de los mismos o la legitimidad del tratamiento.
            </p>

            <h3 className="mb-3 mt-6 text-xl font-semibold text-gray-900 dark:text-white">
              10.6 Derecho de oposición
            </h3>
            <p className="text-gray-700 dark:text-gray-300">
              Puede oponerse al tratamiento de sus datos personales en determinadas circunstancias,
              especialmente para fines de marketing directo.
            </p>

            <h3 className="mb-3 mt-6 text-xl font-semibold text-gray-900 dark:text-white">
              10.7 Derecho a retirar el consentimiento
            </h3>
            <p className="text-gray-700 dark:text-gray-300">
              Cuando el tratamiento se base en su consentimiento, puede retirarlo en cualquier
              momento. Esto no afectará la legalidad del tratamiento previo al retiro.
            </p>

            <h3 className="mb-3 mt-6 text-xl font-semibold text-gray-900 dark:text-white">
              10.8 Derecho de portabilidad
            </h3>
            <p className="text-gray-700 dark:text-gray-300">
              Puede solicitar recibir sus datos personales en un formato estructurado, de uso común
              y lectura mecánica, y transmitirlos a otro responsable cuando sea técnicamente posible.
            </p>

            <div className="mt-6 rounded-lg bg-blue-50 p-6 dark:bg-blue-900/20">
              <h4 className="mb-3 text-lg font-semibold text-gray-900 dark:text-white">
                Cómo ejercer sus derechos:
              </h4>
              <p className="text-gray-700 dark:text-gray-300">
                Para ejercer cualquiera de estos derechos, puede:
              </p>
              <ul className="mt-3 list-disc space-y-2 pl-6 text-gray-700 dark:text-gray-300">
                <li>
                  Enviar un correo electrónico a{' '}
                  <a
                    href="mailto:privacidad@fizko.com"
                    className="font-semibold text-blue-600 hover:underline dark:text-blue-400"
                  >
                    privacidad@fizko.com
                  </a>
                </li>
                <li>Acceder a la configuración de privacidad dentro de su cuenta</li>
                <li>Contactar a nuestro equipo de soporte</li>
              </ul>
              <p className="mt-3 text-gray-700 dark:text-gray-300">
                Responderemos a su solicitud dentro de un plazo razonable (generalmente dentro de 30
                días). Podemos solicitar información adicional para verificar su identidad antes de
                procesar su solicitud.
              </p>
            </div>
          </section>

          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              11. Cookies y tecnologías similares
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              Utilizamos cookies y tecnologías similares para mejorar su experiencia, analizar el
              uso de la plataforma y proporcionar funcionalidades personalizadas.
            </p>

            <h3 className="mb-3 mt-6 text-xl font-semibold text-gray-900 dark:text-white">
              Tipos de cookies que utilizamos:
            </h3>
            <ul className="mt-2 space-y-3 text-gray-700 dark:text-gray-300">
              <li>
                <strong>Cookies esenciales:</strong> Necesarias para el funcionamiento básico de la
                plataforma (autenticación, seguridad, preferencias de sesión). No pueden ser
                desactivadas.
              </li>
              <li>
                <strong>Cookies de rendimiento:</strong> Recopilan información sobre cómo los
                usuarios utilizan la plataforma para mejorar su funcionamiento.
              </li>
              <li>
                <strong>Cookies de funcionalidad:</strong> Permiten recordar sus preferencias y
                personalizaciones (idioma, tema, configuración).
              </li>
              <li>
                <strong>Cookies analíticas:</strong> Nos ayudan a entender cómo los usuarios
                interactúan con la plataforma mediante datos agregados y anonimizados.
              </li>
            </ul>

            <p className="mt-4 text-gray-700 dark:text-gray-300">
              Puede gestionar sus preferencias de cookies desde la configuración de su navegador. Sin
              embargo, deshabilitar ciertas cookies puede afectar la funcionalidad de la plataforma.
            </p>
          </section>

          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              12. Privacidad de menores
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              Nuestros servicios están dirigidos a personas mayores de 18 años. No recopilamos
              intencionalmente datos personales de menores de edad. Si descubrimos que hemos
              recopilado inadvertidamente información de un menor, tomaremos medidas para eliminar
              esos datos de nuestros sistemas lo antes posible.
            </p>
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              Si usted es padre, madre o tutor legal y cree que su hijo menor de edad nos ha
              proporcionado datos personales, por favor contáctenos inmediatamente.
            </p>
          </section>

          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              13. Toma de decisiones automatizadas
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              Utilizamos inteligencia artificial y algoritmos para proporcionar funcionalidades como:
            </p>
            <ul className="mt-4 list-disc space-y-2 pl-6 text-gray-700 dark:text-gray-300">
              <li>Organización y categorización automática de documentos tributarios</li>
              <li>Respuestas del asistente virtual (Notebook) a sus consultas</li>
              <li>Proyecciones de impuestos basadas en su actividad</li>
              <li>Detección de anomalías o posibles errores en sus documentos</li>
              <li>Recomendaciones personalizadas para optimización tributaria</li>
            </ul>
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              Estas herramientas están diseñadas para asistirle y proporcionarle información útil,
              pero <strong>no toman decisiones vinculantes</strong> sobre sus obligaciones
              tributarias. Usted siempre mantiene el control final y la responsabilidad sobre sus
              decisiones fiscales y contables.
            </p>
            <p className="mt-4 font-semibold text-gray-900 dark:text-white">
              Importante: Las sugerencias y proyecciones de Fizko son solo orientativas. Le
              recomendamos consultar con un profesional contable o tributario para decisiones
              importantes.
            </p>
          </section>

          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              14. Enlaces a sitios de terceros
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              Nuestra plataforma puede contener enlaces a sitios web de terceros, incluyendo el
              portal del SII y procesadores de pago. Esta Política de Privacidad no se aplica a
              esos sitios externos.
            </p>
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              No somos responsables de las prácticas de privacidad de sitios de terceros. Le
              recomendamos leer las políticas de privacidad de cada sitio que visite.
            </p>
          </section>

          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              15. Notificación de brechas de seguridad
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              En caso de que ocurra una brecha de seguridad que pueda afectar significativamente sus
              datos personales, le notificaremos sin demora injustificada a través del correo
              electrónico registrado en su cuenta y/o mediante un aviso destacado en la plataforma.
            </p>
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              También notificaremos a las autoridades competentes cuando sea requerido por la
              legislación vigente.
            </p>
          </section>

          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              16. Modificaciones a esta política
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              Nos reservamos el derecho de actualizar esta Política de Privacidad periódicamente
              para reflejar cambios en nuestras prácticas, tecnologías, requisitos legales u otros
              factores.
            </p>
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              Cuando realicemos cambios sustanciales, le notificaremos con al menos 15 días de
              anticipación mediante:
            </p>
            <ul className="mt-4 list-disc space-y-2 pl-6 text-gray-700 dark:text-gray-300">
              <li>Correo electrónico a la dirección registrada en su cuenta</li>
              <li>Un aviso destacado en la plataforma</li>
              <li>Una notificación dentro de la aplicación</li>
            </ul>
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              Le recomendamos revisar periódicamente esta política para mantenerse informado sobre
              cómo protegemos su información. La fecha de la última actualización se indica al
              inicio de este documento.
            </p>
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              El uso continuado de nuestros servicios después de la entrada en vigor de las
              modificaciones constituye su aceptación de la política actualizada. Si no está de
              acuerdo con los cambios, puede cancelar su cuenta antes de que entren en vigor.
            </p>
          </section>

          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              17. Ley aplicable y jurisdicción
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              Esta Política de Privacidad se rige por las leyes de la República de Chile,
              particularmente:
            </p>
            <ul className="mt-4 list-disc space-y-2 pl-6 text-gray-700 dark:text-gray-300">
              <li>Ley N° 19.628 sobre Protección de la Vida Privada</li>
              <li>Ley N° 19.496 sobre Protección de los Derechos de los Consumidores</li>
              <li>Ley N° 20.584 que regula los derechos y deberes que tienen las personas</li>
              <li>Código Civil y demás normativas aplicables</li>
            </ul>
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              Cualquier controversia relacionada con esta política será sometida a la jurisdicción
              de los tribunales ordinarios de justicia de Santiago, Chile.
            </p>
          </section>

          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              18. Reclamos ante autoridades
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              Si considera que el tratamiento de sus datos personales vulnera la legislación vigente
              o sus derechos de privacidad, puede presentar un reclamo ante:
            </p>
            <div className="mt-4 rounded-lg bg-gray-50 p-4 dark:bg-gray-700">
              <p className="font-semibold text-gray-900 dark:text-white">
                Consejo para la Transparencia
              </p>
              <p className="mt-2 text-gray-700 dark:text-gray-300">
                <strong>Sitio web:</strong>{' '}
                <a
                  href="https://www.consejotransparencia.cl"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline dark:text-blue-400"
                >
                  www.consejotransparencia.cl
                </a>
              </p>
              <p className="mt-1 text-gray-700 dark:text-gray-300">
                <strong>Teléfono:</strong> +56 2 2754 8200
              </p>
            </div>
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              Sin embargo, le animamos a contactarnos primero para que podamos intentar resolver su
              inquietud directamente.
            </p>
          </section>

          <section className="rounded-2xl bg-blue-50 p-8 dark:bg-blue-900/20">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              Información de contacto
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              Si tiene preguntas, inquietudes o solicitudes relacionadas con esta Política de
              Privacidad o el tratamiento de sus datos personales, puede contactarnos a través de:
            </p>
            <div className="mt-6 space-y-3 text-gray-700 dark:text-gray-300">
              <p>
                <strong>Para consultas sobre privacidad y datos personales:</strong>
                <br />
                <a
                  href="mailto:privacidad@fizko.com"
                  className="text-blue-600 hover:underline dark:text-blue-400"
                >
                  privacidad@fizko.com
                </a>
              </p>
              <p>
                <strong>Para soporte general:</strong>
                <br />
                <a
                  href="mailto:soporte@fizko.com"
                  className="text-blue-600 hover:underline dark:text-blue-400"
                >
                  soporte@fizko.com
                </a>
              </p>
              <p>
                <strong>A través de la plataforma:</strong>
                <br />
                Utilice el asistente virtual (Notebook) o la sección de contacto dentro de la
                aplicación
              </p>
            </div>
            <p className="mt-6 text-gray-700 dark:text-gray-300">
              Nos comprometemos a responder sus consultas de manera oportuna y a trabajar con usted
              para resolver cualquier inquietud sobre privacidad que pueda tener.
            </p>
          </section>

          <div className="mt-8 rounded-2xl border-2 border-blue-200 bg-blue-50 p-6 dark:border-blue-800 dark:bg-blue-900/20">
            <p className="text-center text-sm text-gray-700 dark:text-gray-300">
              <strong>Fecha de entrada en vigor:</strong> Enero 2025
              <br />
              <strong>Última actualización:</strong> Enero 2025
            </p>
          </div>
        </article>
      </div>

      {/* Footer */}
      <LandingFooter />
    </main>
  );
}
