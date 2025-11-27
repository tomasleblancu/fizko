/**
 * Chat Page
 *
 * Test page for ChatKit with Agents SDK integration.
 */

import { ChatKitPanel } from '@/components/chat/chatkit-panel';

export default function ChatPage() {
  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-5xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">Asistente Fizko</h1>
          <p className="text-gray-600 mt-2">
            Pregúntame sobre impuestos, facturas, F29 y más
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-sm h-[80vh] overflow-hidden">
          <ChatKitPanel companyId="demo-company-123" />
        </div>

        <div className="mt-4 text-sm text-gray-500 text-center">
          <p>Powered by OpenAI Agents SDK + ChatKit</p>
        </div>
      </div>
    </div>
  );
}
