import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    const response = await fetch(`${BACKEND_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: body.email,
        password: body.password,
      }),
    })

    if (!response.ok) {
      const error = await response.json()
      return NextResponse.json(
        { detail: error.detail || 'Login failed' },
        { status: response.status }
      )
    }

    const data = await response.json()
    
    // Set secure httpOnly cookie with JWT token
    const response_with_cookie = new NextResponse(
      JSON.stringify(data),
      { status: 200 }
    )
    
    // Also set a secure token in response body for client-side storage
    return response_with_cookie
  } catch (error) {
    console.error('Login API route error:', error)
    return NextResponse.json(
      { detail: 'Internal server error' },
      { status: 500 }
    )
  }
}
