import Link from "next/link";
import Image from "next/image";

export function LandingFooter() {
  return (
    <footer className="bg-white py-12 dark:bg-gray-900">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col items-center justify-between space-y-4 sm:flex-row sm:space-y-0">
          <div className="flex items-center gap-2">
            <Image
              src="/encabezado.png"
              alt="Fizko Icon"
              width={32}
              height={32}
              className="h-8 w-auto"
            />
            <Image
              src="/encabezado_fizko.svg"
              alt="Fizko - Plataforma de Gestión Tributaria"
              width={120}
              height={40}
              className="h-10 w-auto"
            />
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            © 2025 Fizko. Todos los derechos reservados.
          </p>
          <nav
            className="flex space-x-6 text-sm text-gray-600 dark:text-gray-400"
            aria-label="Footer"
          >
            <Link
              href="/terminos"
              className="hover:text-blue-600 dark:hover:text-blue-400"
            >
              Términos de Servicio
            </Link>
            <Link
              href="/privacidad"
              className="hover:text-blue-600 dark:hover:text-blue-400"
            >
              Política de Privacidad
            </Link>
            <Link
              href="/contacto"
              className="hover:text-blue-600 dark:hover:text-blue-400"
            >
              Contacto
            </Link>
          </nav>
        </div>
      </div>
    </footer>
  );
}
