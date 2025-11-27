export function ThreeCs() {
  return (
    <section
      className="relative overflow-hidden bg-gradient-to-br from-slate-900 via-emerald-950 to-slate-900 py-32 transition-colors"
      aria-labelledby="three-cs-heading"
    >
      {/* Decorative background */}
      <div
        className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-emerald-900/20 via-transparent to-transparent"
        aria-hidden="true"
      />

      <div className="relative mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <header className="text-center mb-20">
          <h2
            id="three-cs-heading"
            className="text-5xl font-bold text-white sm:text-6xl mb-6"
          >
            Las 3C de Fizko
          </h2>
          <p className="text-2xl text-emerald-200">
            La esencia de nuestra plataforma
          </p>
        </header>

        <div className="grid gap-8 md:grid-cols-3 max-w-6xl mx-auto">
          {/* Conecta */}
          <div className="group relative">
            <div
              className="absolute inset-0 bg-gradient-to-br from-emerald-500/20 to-teal-500/20 rounded-3xl blur-xl group-hover:blur-2xl transition-all duration-300"
              aria-hidden="true"
            />
            <div className="relative flex flex-col items-center text-center h-full p-10 bg-white/5 backdrop-blur-sm rounded-3xl border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all duration-300">
              <div className="flex items-center justify-center w-20 h-20 mb-8 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-500 shadow-2xl flex-shrink-0 group-hover:scale-110 transition-transform duration-300">
                <svg
                  className="w-10 h-10 text-white"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2.5}
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                </svg>
              </div>
              <h3 className="text-4xl font-bold text-white mb-4">Conecta</h3>
              <p className="text-lg text-emerald-100 leading-relaxed">
                Tu información financiera con un click
              </p>
            </div>
          </div>

          {/* Controla */}
          <div className="group relative">
            <div
              className="absolute inset-0 bg-gradient-to-br from-teal-500/20 to-cyan-500/20 rounded-3xl blur-xl group-hover:blur-2xl transition-all duration-300"
              aria-hidden="true"
            />
            <div className="relative flex flex-col items-center text-center h-full p-10 bg-white/5 backdrop-blur-sm rounded-3xl border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all duration-300">
              <div className="flex items-center justify-center w-20 h-20 mb-8 rounded-2xl bg-gradient-to-br from-teal-500 to-cyan-500 shadow-2xl flex-shrink-0 group-hover:scale-110 transition-transform duration-300">
                <svg
                  className="w-10 h-10 text-white"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2.5}
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  />
                </svg>
              </div>
              <h3 className="text-4xl font-bold text-white mb-4">Controla</h3>
              <p className="text-lg text-emerald-100 leading-relaxed">
                Todos tus movimientos y crecimiento
              </p>
            </div>
          </div>

          {/* Cumple */}
          <div className="group relative">
            <div
              className="absolute inset-0 bg-gradient-to-br from-emerald-500/20 to-green-500/20 rounded-3xl blur-xl group-hover:blur-2xl transition-all duration-300"
              aria-hidden="true"
            />
            <div className="relative flex flex-col items-center text-center h-full p-10 bg-white/5 backdrop-blur-sm rounded-3xl border border-white/10 hover:bg-white/10 hover:border-white/20 transition-all duration-300">
              <div className="flex items-center justify-center w-20 h-20 mb-8 rounded-2xl bg-gradient-to-br from-emerald-500 to-green-500 shadow-2xl flex-shrink-0 group-hover:scale-110 transition-transform duration-300">
                <svg
                  className="w-10 h-10 text-white"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2.5}
                  aria-hidden="true"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
              </div>
              <h3 className="text-4xl font-bold text-white mb-4">Cumple</h3>
              <p className="text-lg text-blue-100 leading-relaxed">
                Todas tus obligaciones tributarias
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
