import { useState } from 'react'
import { Plus, Trash2, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card } from '@/components/ui/card'
import { getAuthHeaders } from '@/lib/auth-utils'

interface CustomDomain {
  id: string
  name: string
  keywords: string
}

export function CustomDomainManager() {
  const [domains, setDomains] = useState<CustomDomain[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [newDomain, setNewDomain] = useState({
    domain_name: '',
    keywords: ''
  })

  const handleAddDomain = async () => {
    if (!newDomain.domain_name || !newDomain.keywords) {
      alert('Please fill in all fields')
      return
    }

    setIsLoading(true)
    try {
      const response = await fetch('/api/custom-domains', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(newDomain)
      })

      if (response.ok) {
        const data = await response.json()
        setDomains([...domains, data.domain])
        setNewDomain({ domain_name: '', keywords: '' })
      }
    } catch (error) {
      console.error('Failed to add domain:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeleteDomain = async (domainId: string) => {
    setDomains(domains.filter(d => d.id !== domainId))
  }

  return (
    <section className="rounded-xl border border-border bg-card p-6">
      <h2 className="mb-6 text-lg font-semibold">Custom Domains</h2>
      
      {/* Add New Domain */}
      <div className="mb-6 space-y-4 rounded-lg bg-muted/30 p-4">
        <div>
          <Label htmlFor="domain-name">Domain Name</Label>
          <Input
            id="domain-name"
            placeholder="e.g., Remote Work Trends"
            value={newDomain.domain_name}
            onChange={(e) => setNewDomain({ ...newDomain, domain_name: e.target.value })}
          />
        </div>
        <div>
          <Label htmlFor="keywords">Keywords (comma-separated)</Label>
          <Input
            id="keywords"
            placeholder="e.g., remote work, digital nomad, work from home"
            value={newDomain.keywords}
            onChange={(e) => setNewDomain({ ...newDomain, keywords: e.target.value })}
          />
        </div>
        <Button 
          onClick={handleAddDomain} 
          disabled={isLoading}
          className="w-full"
        >
          {isLoading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Adding...
            </>
          ) : (
            <>
              <Plus className="mr-2 h-4 w-4" />
              Add Custom Domain
            </>
          )}
        </Button>
      </div>

      {/* Existing Domains */}
      <div className="space-y-2">
        {domains.length === 0 ? (
          <p className="text-sm text-muted-foreground">No custom domains yet</p>
        ) : (
          domains.map(domain => (
            <Card key={domain.id} className="flex items-center justify-between p-4">
              <div>
                <p className="font-medium">{domain.name}</p>
                <p className="text-sm text-muted-foreground">{domain.keywords}</p>
              </div>
              <button
                onClick={() => handleDeleteDomain(domain.id)}
                className="rounded p-2 hover:bg-destructive/10"
              >
                <Trash2 className="h-4 w-4 text-muted-foreground" />
              </button>
            </Card>
          ))
        )}
      </div>
    </section>
  )
}
