"use client";

import { MessageSquare } from "lucide-react";

export function ChatKitPlaceholder() {
  return (
    <div className="flex h-full w-full flex-col bg-white dark:bg-slate-900">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-slate-200 bg-emerald-600 px-4 py-3 dark:border-slate-700">
        <div className="flex items-center gap-2">
          <MessageSquare className="h-5 w-5 text-white" />
          <h3 className="font-semibold text-white">Asistente Tributario</h3>
        </div>
      </div>

      {/* Chat Content - Placeholder */}
      <div className="flex flex-1 items-center justify-center p-6">
        <div className="text-center">
          <div className="mb-4 flex justify-center">
            <div className="rounded-full bg-emerald-100 p-4 dark:bg-emerald-900/20">
              <MessageSquare className="h-8 w-8 text-emerald-600 dark:text-emerald-400" />
            </div>
          </div>
          <h4 className="mb-2 text-lg font-semibold text-slate-900 dark:text-white">
            ChatKit próximamente
          </h4>
          <p className="text-sm text-slate-600 dark:text-slate-400">
            El asistente de inteligencia artificial estará disponible
            próximamente para ayudarte con tus consultas tributarias.
          </p>
        </div>
      </div>

      {/* Input - Disabled */}
      <div className="border-t border-slate-200 p-4 dark:border-slate-700">
        <input
          type="text"
          placeholder="Escribe tu pregunta..."
          disabled
          className="w-full rounded-lg border border-slate-300 bg-slate-50 px-4 py-2 text-sm text-slate-400 dark:border-slate-600 dark:bg-slate-800"
        />
      </div>
    </div>
  );
}
