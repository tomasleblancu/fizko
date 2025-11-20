/**
 * ChatKit API Endpoint - Proxy Mode
 *
 * Proxies all ChatKit operations directly to the FastAPI backend.
 * This allows us to use the backend's multi-agent system.
 *
 * The backend handles:
 * - Session creation (create_session)
 * - Thread management (create_thread, update_thread)
 * - Message streaming (create_message)
 * - Attachments
 */

import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8089';

/**
 * POST /api/chatkit
 * Proxy all ChatKit operations to backend
 */
export async function POST(req: NextRequest) {
  try {
    // Get the raw body
    const body = await req.text();

    // Parse to log operation
    let bodyObj: any = {};
    try {
      bodyObj = JSON.parse(body);
    } catch {
      // Ignore parse errors
    }

    console.log('[ChatKit Proxy] Operation:', bodyObj.op || 'unknown');

    // Extract query parameters from original request
    const url = new URL(req.url);
    const queryParams = url.searchParams;

    // Build backend URL with query params
    const backendUrl = new URL('/chatkit', BACKEND_URL);
    queryParams.forEach((value, key) => {
      backendUrl.searchParams.set(key, value);
    });

    // Forward headers (especially Authorization)
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    // Copy important headers
    const authHeader = req.headers.get('authorization');
    if (authHeader) {
      headers['Authorization'] = authHeader;
    }

    // Copy cookie header for session management
    const cookieHeader = req.headers.get('cookie');
    if (cookieHeader) {
      headers['Cookie'] = cookieHeader;
    }

    console.log('[ChatKit Proxy] Forwarding to:', backendUrl.toString());

    // Forward request to backend
    const response = await fetch(backendUrl.toString(), {
      method: 'POST',
      headers,
      body,
    });

    // Get response content type
    const contentType = response.headers.get('content-type') || '';

    // Handle streaming responses (text/event-stream)
    if (contentType.includes('text/event-stream')) {
      console.log('[ChatKit Proxy] Streaming response');

      return new Response(response.body, {
        headers: {
          'Content-Type': 'text/event-stream',
          'Cache-Control': 'no-cache',
          'Connection': 'keep-alive',
        },
      });
    }

    // Handle JSON responses
    const responseText = await response.text();

    console.log('[ChatKit Proxy] JSON response:', responseText.substring(0, 100));

    // Forward cookies from backend
    const responseHeaders: Record<string, string> = {
      'Content-Type': contentType,
    };

    const setCookieHeader = response.headers.get('set-cookie');
    if (setCookieHeader) {
      responseHeaders['Set-Cookie'] = setCookieHeader;
    }

    return new Response(responseText, {
      status: response.status,
      headers: responseHeaders,
    });
  } catch (error: any) {
    console.error('[ChatKit Proxy] Error:', error);
    return NextResponse.json(
      { error: error.message || 'Internal server error' },
      { status: 500 }
    );
  }
}

/**
 * GET /api/chatkit
 * Health check
 */
export async function GET() {
  return NextResponse.json({
    status: 'ok',
    service: 'chatkit-proxy',
    backend: BACKEND_URL,
    timestamp: new Date().toISOString(),
  });
}
