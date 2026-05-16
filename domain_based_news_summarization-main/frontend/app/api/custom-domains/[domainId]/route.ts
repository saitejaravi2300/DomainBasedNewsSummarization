import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ domainId: string }> }
) {
  try {
    const { domainId } = await params
    const authToken = request.headers.get('authorization')

    const response = await fetch(`${BACKEND_URL}/user/custom-domains/${domainId}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        ...(authToken && { 'Authorization': authToken }),
      },
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: 'Failed to delete domain' },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error('Custom domain DELETE API route error:', error)
    return NextResponse.json(
      { error: 'Internal server error' },
      { status: 500 }
    )
  }
}
