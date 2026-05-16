import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const limit = searchParams.get('limit') || '10'
    const offset = searchParams.get('offset') || '0'
    const domain = searchParams.get('domain')

    const authToken = request.headers.get('authorization')

    try {
      const params = new URLSearchParams({
        limit,
        offset,
        ...(domain && { domain }),
      })
      
      const response = await fetch(`${BACKEND_URL}/digest/history?${params}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          ...(authToken && { 'Authorization': authToken }),
        },
      })

      if (response.ok) {
        const data = await response.json()
        return NextResponse.json(data)
      }
    } catch (backendError) {
      console.warn('Backend unavailable for digest history:', backendError)
    }

    const mockHistory = [
      {
        id: `digest-${Date.now()}-1`,
        domain: 'AI & ML',
        date: new Date(Date.now() - 86400000).toISOString().split('T')[0],
        trends: 6,
        articles: 43,
      },
      {
        id: `digest-${Date.now()}-2`,
        domain: 'Finance',
        date: new Date(Date.now() - 86400000 * 2).toISOString().split('T')[0],
        trends: 5,
        articles: 38,
      },
      {
        id: `digest-${Date.now()}-3`,
        domain: 'Healthcare',
        date: new Date(Date.now() - 86400000 * 3).toISOString().split('T')[0],
        trends: 4,
        articles: 31,
      },
    ]

    let result = mockHistory
    if (domain) {
      result = result.filter((h: any) => h.domain.toLowerCase() === domain.toLowerCase())
    }
    
    return NextResponse.json(result.slice(0, parseInt(limit)))
  } catch (error) {
    console.error('API route error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
