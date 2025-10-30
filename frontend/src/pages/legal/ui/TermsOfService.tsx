import { ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import { LandingFooter } from "@/shared/ui/branding/LandingFooter";

export default function TermsOfService() {
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
            Términos y Condiciones
          </h1>
          <p className="mt-4 text-lg text-gray-600 dark:text-gray-300">
            Última actualización: Enero 2025
          </p>
        </header>

        {/* Content */}
        <article className="prose prose-lg dark:prose-invert max-w-none">
          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <p className="text-gray-700 dark:text-gray-300">
              Los presentes Términos y Condiciones (en adelante, el "Acuerdo") regulan el acceso y
              uso de la plataforma digital Fizko y todos sus servicios asociados (en adelante, los
              "Servicios"), proporcionados por Fizko a través de su aplicación web y móvil.
            </p>
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              Al acceder y utilizar los Servicios de Fizko, usted (en adelante, el "Usuario")
              acepta estar sujeto a los términos y condiciones establecidos en este Acuerdo. Si no
              está de acuerdo con estos términos, le solicitamos no utilizar nuestros Servicios.
            </p>
          </section>

          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              1. Quiénes somos
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              Fizko es una plataforma tecnológica que facilita la gestión tributaria y contable
              para empresas y profesionales en Chile. Nuestra plataforma se conecta de forma segura
              con el Servicio de Impuestos Internos (SII) para proporcionar información en tiempo
              real sobre documentos tributarios, ingresos, gastos y obligaciones fiscales.
            </p>
          </section>

          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              2. En qué consisten los Servicios
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              Los Servicios de Fizko incluyen, de manera no limitativa:
            </p>
            <ul className="mt-4 list-disc space-y-2 pl-6 text-gray-700 dark:text-gray-300">
              <li>
                Conexión segura y automática con el SII para obtener información tributaria en
                tiempo real
              </li>
              <li>
                Visualización y organización de documentos tributarios electrónicos (facturas,
                boletas, notas de crédito, etc.)
              </li>
              <li>
                Dashboard con resúmenes de ingresos, gastos y situación tributaria actualizada
              </li>
              <li>
                Asistente virtual impulsado por inteligencia artificial para consultas fiscales y
                contables (Notebook)
              </li>
              <li>Proyecciones de impuestos mensuales basadas en la actividad del negocio</li>
              <li>Notificaciones sobre vencimientos y obligaciones tributarias importantes</li>
              <li>Gestión y seguimiento de declaraciones mensuales (Formulario 29)</li>
              <li>
                Herramientas para facilitar el pago de impuestos directamente desde la plataforma
              </li>
            </ul>
          </section>

          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              3. Condiciones de uso
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              Para utilizar los Servicios de Fizko, el Usuario debe:
            </p>
            <ul className="mt-4 list-disc space-y-2 pl-6 text-gray-700 dark:text-gray-300">
              <li>Ser mayor de 18 años</li>
              <li>
                Tener una cuenta de Google válida para autenticarse en la plataforma (inicio de
                sesión mediante Google)
              </li>
              <li>
                Proporcionar credenciales válidas del SII para permitir la conexión segura con el
                portal tributario
              </li>
              <li>
                Mantener la confidencialidad de sus credenciales de acceso y ser responsable de
                todas las actividades realizadas bajo su cuenta
              </li>
              <li>
                Utilizar los Servicios únicamente para fines lícitos y de conformidad con la
                legislación chilena vigente
              </li>
              <li>
                Proporcionar información veraz, completa y actualizada durante el registro y uso de
                la plataforma
              </li>
            </ul>
          </section>

          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              4. Prohibiciones
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              El Usuario se compromete a NO realizar las siguientes acciones:
            </p>
            <ul className="mt-4 list-disc space-y-2 pl-6 text-gray-700 dark:text-gray-300">
              <li>
                Utilizar los Servicios para actividades ilegales, fraudulentas o que violen
                derechos de terceros
              </li>
              <li>
                Intentar acceder sin autorización a sistemas, datos o cuentas de otros usuarios
              </li>
              <li>
                Realizar ingeniería inversa, descompilar o intentar extraer el código fuente de la
                plataforma
              </li>
              <li>
                Interferir con el funcionamiento normal de los Servicios mediante virus, malware o
                cualquier código malicioso
              </li>
              <li>
                Compartir, vender, sublicenciar o transferir sus credenciales de acceso a terceros
              </li>
              <li>
                Utilizar automatizaciones, bots o scripts no autorizados para interactuar con la
                plataforma
              </li>
              <li>
                Extraer masivamente datos de la plataforma mediante técnicas de web scraping o
                similares
              </li>
              <li>
                Realizar cualquier acción que pueda sobrecargar, dañar o afectar negativamente la
                infraestructura de Fizko
              </li>
            </ul>
          </section>

          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              5. Licencia de uso
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              Fizko otorga al Usuario una licencia personal, no exclusiva, no transferible y
              revocable para acceder y utilizar los Servicios, sujeta a los términos de este
              Acuerdo. Esta licencia no incluye el derecho a:
            </p>
            <ul className="mt-4 list-disc space-y-2 pl-6 text-gray-700 dark:text-gray-300">
              <li>Redistribuir, vender, alquilar o sublicenciar los Servicios</li>
              <li>Modificar, adaptar o crear obras derivadas de la plataforma</li>
              <li>
                Utilizar los Servicios para desarrollar productos o servicios competidores
              </li>
            </ul>
          </section>

          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              6. Propiedad intelectual
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              Todos los derechos de propiedad intelectual sobre los Servicios, incluyendo pero no
              limitado a software, diseños, logotipos, marcas comerciales, textos, gráficos,
              interfaces de usuario y código fuente, son propiedad exclusiva de Fizko o de sus
              licenciantes.
            </p>
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              El Usuario conserva la propiedad de los datos que proporciona a través de la
              plataforma. Sin embargo, al utilizar los Servicios, el Usuario otorga a Fizko una
              licencia limitada para procesar, almacenar y utilizar dichos datos exclusivamente con
              el fin de proporcionar y mejorar los Servicios.
            </p>
          </section>

          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              7. Protección de datos y privacidad
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              La protección de los datos personales del Usuario es una prioridad para Fizko.
              Implementamos medidas de seguridad técnicas y organizativas apropiadas para proteger
              la información contra accesos no autorizados, pérdida o alteración.
            </p>
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              Las credenciales de acceso al SII se almacenan utilizando tecnología de cifrado
              avanzado de extremo a extremo. Fizko cumple con todas las normativas de protección de
              datos vigentes en Chile, incluyendo la Ley N° 19.628 sobre Protección de la Vida
              Privada y sus modificaciones.
            </p>
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              Para más información sobre cómo procesamos y protegemos sus datos personales, por
              favor consulte nuestra{' '}
              <Link to="/privacidad" className="text-blue-600 hover:underline dark:text-blue-400">
                Política de Privacidad
              </Link>
              .
            </p>
          </section>

          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              8. Disponibilidad de los Servicios
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              Fizko se esfuerza por mantener los Servicios disponibles de manera continua. Sin
              embargo, no garantizamos que los Servicios estarán libres de interrupciones, errores
              o que funcionarán sin demoras.
            </p>
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              Fizko se reserva el derecho de suspender temporal o permanentemente los Servicios,
              total o parcialmente, para realizar mantenimiento, actualizaciones o por cualquier
              otra razón técnica o de negocio. Haremos esfuerzos razonables para notificar a los
              Usuarios con anticipación sobre interrupciones programadas.
            </p>
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              La disponibilidad de los Servicios también puede depender de sistemas externos como
              el portal del SII, sobre los cuales Fizko no tiene control.
            </p>
          </section>

          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              9. Planes, precios y pagos
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              Fizko ofrece diferentes planes de servicio que se detallan en la plataforma. Los
              precios y características de cada plan están sujetos a cambios, los cuales serán
              notificados a los Usuarios con al menos 30 días de anticipación.
            </p>
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              Los pagos se procesan de manera segura a través de procesadores de pago de terceros.
              El Usuario es responsable de proporcionar información de pago válida y mantenerla
              actualizada.
            </p>
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              Los servicios se facturarán de acuerdo al plan seleccionado. En caso de mora en el
              pago, Fizko se reserva el derecho de suspender el acceso a los Servicios hasta que se
              regularice el pago pendiente.
            </p>
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              Todos los precios se expresan en pesos chilenos (CLP) e incluyen IVA cuando
              corresponda.
            </p>
          </section>

          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              10. Duración y terminación
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              Este Acuerdo entra en vigor cuando el Usuario accede por primera vez a los Servicios
              y permanece vigente mientras el Usuario continúe utilizando la plataforma.
            </p>
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              El Usuario puede cancelar su cuenta y terminar este Acuerdo en cualquier momento
              desde la configuración de su cuenta o contactando a nuestro equipo de soporte. La
              terminación será efectiva al final del período de facturación actual.
            </p>
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              Fizko se reserva el derecho de suspender o cancelar el acceso del Usuario a los
              Servicios si:
            </p>
            <ul className="mt-4 list-disc space-y-2 pl-6 text-gray-700 dark:text-gray-300">
              <li>El Usuario incumple cualquiera de los términos de este Acuerdo</li>
              <li>Se detecta actividad fraudulenta o uso indebido de los Servicios</li>
              <li>Existen pagos pendientes después de un período razonable de gracia</li>
              <li>
                Se requiere cumplir con obligaciones legales o decisiones de autoridades competentes
              </li>
            </ul>
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              En caso de terminación, el Usuario conservará acceso de solo lectura a sus datos por
              un período de 30 días, después del cual Fizko podrá eliminar permanentemente toda la
              información del Usuario de sus sistemas.
            </p>
          </section>

          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              11. Responsabilidad
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              Fizko proporciona los Servicios "tal como están" y "según disponibilidad". No
              garantizamos que los Servicios cumplirán con todos los requisitos específicos del
              Usuario ni que serán ininterrumpidos, seguros o libres de errores.
            </p>
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              Fizko no se responsabiliza por:
            </p>
            <ul className="mt-4 list-disc space-y-2 pl-6 text-gray-700 dark:text-gray-300">
              <li>
                Decisiones tomadas por el Usuario basadas en la información proporcionada por la
                plataforma
              </li>
              <li>
                Errores en las declaraciones de impuestos o incumplimiento de obligaciones
                tributarias por parte del Usuario
              </li>
              <li>
                Pérdidas o daños resultantes de interrupciones en el servicio del SII u otros
                sistemas externos
              </li>
              <li>
                Daños indirectos, incidentales, especiales o consecuentes derivados del uso o
                imposibilidad de uso de los Servicios
              </li>
              <li>
                Pérdida de datos resultante de acciones del Usuario, fallas técnicas o terminación
                del servicio
              </li>
            </ul>
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              En la medida permitida por la ley, la responsabilidad total de Fizko bajo este
              Acuerdo no excederá el monto pagado por el Usuario en los 12 meses anteriores al
              evento que dio origen a la reclamación.
            </p>
            <p className="mt-4 font-semibold text-gray-900 dark:text-white">
              IMPORTANTE: Fizko es una herramienta de apoyo para la gestión tributaria. El Usuario
              es el único responsable de cumplir con todas sus obligaciones fiscales y contables
              ante el SII y otras autoridades competentes. Recomendamos consultar con un
              profesional contable o tributario para decisiones importantes.
            </p>
          </section>

          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              12. Confidencialidad
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              Toda la información tributaria, financiera y comercial del Usuario se considera
              confidencial. Fizko se compromete a no divulgar, compartir o utilizar dicha
              información para fines distintos a los establecidos en este Acuerdo, excepto cuando:
            </p>
            <ul className="mt-4 list-disc space-y-2 pl-6 text-gray-700 dark:text-gray-300">
              <li>Sea requerido por ley o por orden de autoridad competente</li>
              <li>El Usuario otorgue su consentimiento expreso</li>
              <li>
                Sea necesario para proporcionar los Servicios (por ejemplo, procesadores de pago,
                servicios de hosting)
              </li>
            </ul>
          </section>

          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              13. Notificaciones y alertas
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              Fizko enviará notificaciones importantes al Usuario a través de:
            </p>
            <ul className="mt-4 list-disc space-y-2 pl-6 text-gray-700 dark:text-gray-300">
              <li>Correo electrónico asociado a la cuenta de Google del Usuario</li>
              <li>Notificaciones dentro de la aplicación web y móvil</li>
              <li>WhatsApp (si el Usuario ha proporcionado y autorizado este canal)</li>
            </ul>
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              El Usuario es responsable de mantener actualizados sus canales de contacto y de
              revisar regularmente las notificaciones de Fizko.
            </p>
          </section>

          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              14. Soporte y ayuda
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              Fizko ofrece soporte técnico a través de los siguientes canales:
            </p>
            <ul className="mt-4 list-disc space-y-2 pl-6 text-gray-700 dark:text-gray-300">
              <li>
                Asistente virtual (Notebook) disponible 24/7 dentro de la plataforma para consultas
                sobre funcionalidades y dudas fiscales generales
              </li>
              <li>Correo electrónico de soporte para consultas técnicas y administrativas</li>
              <li>
                Base de conocimientos y tutoriales disponibles en la plataforma (cuando esté
                disponible)
              </li>
            </ul>
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              Los tiempos de respuesta pueden variar según el plan de servicio contratado y la
              complejidad de la consulta.
            </p>
          </section>

          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              15. Generalidades
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              <strong>Acuerdo completo:</strong> Este Acuerdo, junto con la Política de Privacidad,
              constituye el acuerdo completo entre el Usuario y Fizko respecto al uso de los
              Servicios.
            </p>
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              <strong>Divisibilidad:</strong> Si alguna disposición de este Acuerdo se considera
              inválida o inaplicable, las demás disposiciones permanecerán en pleno vigor y efecto.
            </p>
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              <strong>Renuncia:</strong> La falta de ejercicio de cualquier derecho bajo este
              Acuerdo no constituye una renuncia a dicho derecho.
            </p>
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              <strong>Cesión:</strong> El Usuario no puede ceder o transferir sus derechos u
              obligaciones bajo este Acuerdo sin el consentimiento previo y por escrito de Fizko.
            </p>
          </section>

          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              16. Ley aplicable y solución de controversias
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              Este Acuerdo se rige por las leyes de la República de Chile. Cualquier controversia
              derivada de este Acuerdo será sometida a la jurisdicción de los tribunales ordinarios
              de justicia de Santiago, Chile, renunciando las partes a cualquier otro fuero que
              pudiera corresponderles.
            </p>
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              Antes de iniciar cualquier acción legal, las partes se comprometen a intentar
              resolver la controversia de buena fe mediante negociación directa.
            </p>
          </section>

          <section className="mb-8 rounded-2xl bg-white p-8 shadow-sm dark:bg-gray-800">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">
              17. Modificaciones al Acuerdo
            </h2>
            <p className="text-gray-700 dark:text-gray-300">
              Fizko se reserva el derecho de modificar estos Términos y Condiciones en cualquier
              momento. Las modificaciones serán notificadas a los Usuarios con al menos 15 días de
              anticipación a través de correo electrónico y un aviso destacado en la plataforma.
            </p>
            <p className="mt-4 text-gray-700 dark:text-gray-300">
              El uso continuado de los Servicios después de la fecha de entrada en vigor de las
              modificaciones constituye la aceptación de los nuevos términos. Si el Usuario no está
              de acuerdo con las modificaciones, podrá cancelar su cuenta antes de que entren en
              vigor.
            </p>
          </section>

          <section className="rounded-2xl bg-blue-50 p-8 dark:bg-blue-900/20">
            <h2 className="mb-4 text-2xl font-bold text-gray-900 dark:text-white">Contacto</h2>
            <p className="text-gray-700 dark:text-gray-300">
              Para cualquier consulta sobre estos Términos y Condiciones, puede contactarnos a
              través de:
            </p>
            <ul className="mt-4 space-y-2 text-gray-700 dark:text-gray-300">
              <li>
                <strong>Correo electrónico:</strong> soporte@fizko.com
              </li>
              <li>
                <strong>Plataforma:</strong> A través del asistente virtual (Notebook) en la
                aplicación
              </li>
            </ul>
          </section>
        </article>
      </div>

      {/* Footer */}
      <LandingFooter />
    </main>
  );
}
