'use client'

import { useEffect, useState } from 'react'
import { User, Mail, Save, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { getAuthHeaders } from '@/lib/auth-utils'
import { mockUser } from '@/lib/mock-data'

export default function ProfilePage() {
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [profile, setProfile] = useState({
    name: mockUser.name,
    email: mockUser.email,
  })

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        setIsLoading(true)
        const profileResponse = await fetch('/api/user/profile', {
          method: 'GET',
          headers: getAuthHeaders(),
        })

        if (profileResponse.ok) {
          const profileData = await profileResponse.json()
          setProfile({
            name: profileData.name || mockUser.name,
            email: profileData.email || mockUser.email,
          })
        }
      } catch (error) {
        console.error('Failed to fetch user profile:', error)
      } finally {
        setIsLoading(false)
      }
    }

    fetchProfile()
  }, [])

  const handleSaveProfile = async () => {
    setIsSaving(true)
    try {
      const response = await fetch('/api/user/profile', {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify(profile),
      })

      if (response.ok) {
        setSaved(true)
        setTimeout(() => setSaved(false), 2000)
      }
    } catch (error) {
      console.error('Failed to save profile:', error)
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="p-6 lg:p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold">Profile</h1>
        <p className="mt-2 text-muted-foreground">Manage your account details</p>
      </div>

      <div className="max-w-2xl">
        <section className="rounded-xl border border-border bg-card p-6">
          <h2 className="mb-6 flex items-center gap-2 text-lg font-semibold">
            <User className="h-5 w-5" />
            Account
          </h2>

          <div className="flex items-start gap-6">
            <Avatar className="h-20 w-20">
              <AvatarFallback className="bg-primary text-primary-foreground text-xl">
                {profile.name
                  .split(' ')
                  .filter(Boolean)
                  .map((n) => n[0])
                  .join('')
                  .slice(0, 2)
                  .toUpperCase()}
              </AvatarFallback>
            </Avatar>

            <div className="flex-1 space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Full name</Label>
                <Input
                  id="name"
                  value={profile.name}
                  onChange={(e) => setProfile({ ...profile, name: e.target.value })}
                  disabled={isLoading}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">Email address</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    id="email"
                    type="email"
                    className="pl-10"
                    value={profile.email}
                    onChange={(e) => setProfile({ ...profile, email: e.target.value })}
                    disabled={isLoading}
                  />
                </div>
              </div>
            </div>
          </div>

          <div className="mt-6 flex gap-2 border-t border-border pt-6">
            <Button onClick={handleSaveProfile} disabled={isSaving || isLoading}>
              {saved ? (
                <>
                  <Check className="mr-2 h-4 w-4" />
                  Saved
                </>
              ) : (
                <>
                  <Save className="mr-2 h-4 w-4" />
                  Save profile
                </>
              )}
            </Button>
          </div>
        </section>
      </div>
    </div>
  )
}
