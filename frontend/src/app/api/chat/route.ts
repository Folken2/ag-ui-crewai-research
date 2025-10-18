import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Get backend URL from environment or use localhost for development
    let backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    // Remove trailing slash to prevent double slashes
    backendUrl = backendUrl.replace(/\/$/, '');
    
    // Get authorization header from the request
    const authHeader = request.headers.get('authorization');
    
    // Prepare headers for backend request
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    // Add authorization header if present
    if (authHeader) {
      headers['Authorization'] = authHeader;
    }
    
    // Forward the request to the backend
    const response = await fetch(`${backendUrl}/agent`, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`);
    }

    // Return the response as a stream
    const { readable, writable } = new TransformStream();
    
    response.body?.pipeTo(writable);
    
    return new NextResponse(readable, {
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });
  } catch (error) {
    console.error('Error proxying to backend:', error);
    return NextResponse.json(
      { error: 'Failed to connect to backend' },
      { status: 500 }
    );
  }
} 