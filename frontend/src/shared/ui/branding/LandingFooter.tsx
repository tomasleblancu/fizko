import { Link } from 'react-router-dom';

export function LandingFooter() {
  return (
    <footer className="bg-white py-12 dark:bg-gray-900">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex flex-col items-center justify-between space-y-4 sm:flex-row sm:space-y-0">
          <div className="flex items-center">
            <img
              src="/encabezado.png"
              alt="Fizko - Plataforma de Gestión Tributaria"
              className="h-8 w-auto"
            />
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400">
            © 2025 Fizko. Todos los derechos reservados.
          </p>
          <nav className="flex space-x-6 text-sm text-gray-600 dark:text-gray-400" aria-label="Footer">
            <Link to="/terminos" className="hover:text-blue-600 dark:hover:text-blue-400">
              Términos de Servicio
            </Link>
            <Link to="/privacidad" className="hover:text-blue-600 dark:hover:text-blue-400">
              Política de Privacidad
            </Link>
            <a href="/contacto" className="hover:text-blue-600 dark:hover:text-blue-400">
              Contacto
            </a>
          </nav>
        </div>
      </div>
    </footer>
  );
}
