import Image from "next/image";
import Link from "next/link";

export function Navbar() {
  const handleGetStarted = () => {
    window.location.href = "/auth/login";
  };

  return (
    <nav className="relative">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between py-6">
          {/* Logo a la izquierda */}
          <div className="flex items-center gap-2">
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
          </div>

          {/* Links de navegación y botón Entrar */}
          <div className="flex items-center gap-6">
            <Link
              href="/como-funciona"
              className="text-sm font-medium text-slate-700 hover:text-emerald-600 dark:text-slate-300 dark:hover:text-emerald-400 transition-colors hidden sm:inline-block"
            >
              Cómo Funciona
            </Link>
            <button
              onClick={handleGetStarted}
              className="inline-flex items-center rounded-full bg-gradient-to-r from-emerald-600 to-teal-600 px-6 py-2 text-sm font-semibold text-white shadow-sm transition-all hover:shadow-md hover:scale-105"
              aria-label="Entrar a Fizko"
            >
              <span>Entrar</span>
            </button>
          </div>
        </div>
      </div>
    </nav>
  );
}
