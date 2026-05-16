import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const skipCache = body.skipCache === true  // Support forcing fresh digest
    
    console.log('[API Route] Digest request received:', { skipCache, domain: body.domain, days: body.days })

    // Add timestamp to force bypassing backend cache
    const timestamp = Date.now()
    const url = `${BACKEND_URL}/digest/generate?skip_cache=${skipCache}&t=${timestamp}`
    console.log('[API Route] Calling backend URL:', url)

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-cache, no-store, must-revalidate',
        'Pragma': 'no-cache',
      },
      body: JSON.stringify({
        domain: body.domain,
        days: body.days,
        keywords: body.keywords,
        skip_cache: skipCache,
      }),
    })

    if (!response.ok) {
      const errorText = await response.text()
      console.error('Backend error:', errorText)
      let detail = 'Failed to generate digest'
      try {
        const parsed = JSON.parse(errorText)
        detail = parsed?.detail || parsed?.error || detail
      } catch {
        if (errorText) {
          detail = errorText
        }
      }
      return NextResponse.json(
        { error: detail },
        { status: response.status }
      )
    }

    const data = await response.json()
    console.log('[API Route] Response cached flag:', data.cached)
    return NextResponse.json(data)
  } catch (error) {
    console.error('API route error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
