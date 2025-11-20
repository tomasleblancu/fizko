import { Mail } from "lucide-react";

interface CTAProps {
  onContactSales: () => void;
}

export function CTA({ onContactSales }: CTAProps) {
  return (
    <section
      className="relative bg-white dark:bg-slate-900 py-20 transition-colors"
      aria-labelledby="cta-heading"
    >
      <div className="mx-auto max-w-4xl px-4 text-center sm:px-6 lg:px-8">
        <div className="rounded-3xl bg-gradient-to-br from-emerald-600 to-teal-600 p-12 shadow-xl">
          <h2
            id="cta-heading"
            className="text-3xl font-bold text-white sm:text-4xl"
          >
            Sé parte del futuro de la gestión tributaria
          </h2>
          <p className="mt-4 text-xl text-emerald-50">
            Únete al pre lanzamiento y obtén acceso exclusivo a Fizko.
          </p>
          <button
            onClick={onContactSales}
            className="mt-8 inline-flex items-center space-x-3 rounded-full bg-white px-8 py-4 text-lg font-semibold text-slate-900 shadow-lg transition-all hover:scale-105 hover:shadow-xl"
            aria-label="Acceder al pre lanzamiento"
          >
            <Mail className="h-6 w-6 text-emerald-600" />
            <span>Accede al Pre Lanzamiento</span>
          </button>
        </div>
      </div>
    </section>
  );
}
