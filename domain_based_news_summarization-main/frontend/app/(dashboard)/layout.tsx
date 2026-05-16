'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { 
  Zap, LayoutDashboard, Bookmark, User,
  ChevronLeft, ChevronRight, LogOut, Menu, X
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { cn } from '@/lib/utils'
import { getAuthHeaders } from '@/lib/auth-utils'

interface UserProfile {
  name: string
  email: string
}

const navItems = [
  { href: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { href: '/saved', icon: Bookmark, label: 'Saved Trends' },
  { href: '/profile', icon: User, label: 'Profile' },
]

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const pathname = usePathname()
  const router = useRouter()
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [isMobileOpen, setIsMobileOpen] = useState(false)
  const [userProfile, setUserProfile] = useState<UserProfile>({
    name: 'User',
    email: 'user@example.com',
  })
  const [isLoadingUser, setIsLoadingUser] = useState(true)

  // Fetch user profile on mount
  useEffect(() => {
    const token = typeof window !== 'undefined' ? localStorage.getItem('authToken') : null
    if (!token) {
      router.replace('/login')
      return
    }

    const fetchData = async () => {
      setIsLoadingUser(true)
      try {
        // Fetch user profile
        const profileResponse = await fetch('/api/user/profile', {
          headers: getAuthHeaders(),
        })
        if (profileResponse.status === 401) {
          localStorage.removeItem('authToken')
          localStorage.removeItem('user_id')
          router.replace('/login')
          return
        }
        if (profileResponse.ok) {
          const profileData = await profileResponse.json()
          setUserProfile({
            name: profileData.name || 'User',
            email: profileData.email || 'user@example.com',
          })
        }
      } catch (error) {
        console.error('Failed to fetch data:', error)
      } finally {
        setIsLoadingUser(false)
      }
    }

    fetchData()
  }, [router])

  const handleLogout = () => {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('authToken')
      localStorage.removeItem('user_id')
    }
    router.push('/login')
  }

  return (
    <div className="flex min-h-screen bg-background">
      {/* Mobile menu overlay */}
      {isMobileOpen && (
        <div 
          className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm lg:hidden"
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed left-0 top-0 z-50 flex h-full flex-col border-r border-sidebar-border bg-sidebar transition-all duration-300 lg:relative",
          isCollapsed ? "w-16" : "w-64",
          isMobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        {/* Logo */}
        <div className={cn(
          "flex h-16 items-center border-b border-sidebar-border px-4",
          isCollapsed ? "justify-center" : "gap-2"
        )}>
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-sidebar-primary">
            <Zap className="h-4 w-4 text-sidebar-primary-foreground" />
          </div>
          {!isCollapsed && (
            <span className="text-lg font-semibold text-sidebar-foreground">{"What's New?"}</span>
          )}
          
          {/* Mobile close button */}
          <Button
            variant="ghost"
            size="icon"
            className="ml-auto lg:hidden"
            onClick={() => setIsMobileOpen(false)}
          >
            <X className="h-4 w-4" />
          </Button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 p-2">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = pathname === item.href
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors",
                  isActive
                    ? "bg-sidebar-accent text-sidebar-accent-foreground"
                    : "text-sidebar-foreground/70 hover:bg-sidebar-accent/50 hover:text-sidebar-foreground",
                  isCollapsed && "justify-center px-0"
                )}
              >
                <Icon className="h-4 w-4 shrink-0" />
                {!isCollapsed && <span>{item.label}</span>}
              </Link>
            )
          })}
        </nav>

        {/* User section */}
        <div className="border-t border-sidebar-border p-2">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                className={cn(
                  "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors hover:bg-sidebar-accent/50",
                  isCollapsed && "justify-center px-0"
                )}
              >
                <Avatar className="h-8 w-8">
                  <AvatarFallback className="bg-sidebar-primary text-sidebar-primary-foreground text-xs">
                    {userProfile.name.split(' ').map(n => n[0]).join('')}
                  </AvatarFallback>
                </Avatar>
                {!isCollapsed && (
                  <div className="flex-1 text-left">
                    <p className="font-medium text-sidebar-foreground">{userProfile.name}</p>
                    <p className="text-xs text-sidebar-foreground/50">{userProfile.email}</p>
                  </div>
                )}
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuItem asChild>
                <Link href="/profile" className="flex items-center gap-2">
                  <User className="h-4 w-4" />
                  <span>Profile</span>
                </Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleLogout}>
                <span className="flex items-center gap-2 text-destructive">
                  <LogOut className="h-4 w-4" />
                  <span>Log out</span>
                </span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>

        {/* Collapse toggle */}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="absolute -right-3 top-20 hidden h-6 w-6 items-center justify-center rounded-full border border-sidebar-border bg-sidebar text-sidebar-foreground shadow-sm transition-colors hover:bg-sidebar-accent lg:flex"
        >
          {isCollapsed ? (
            <ChevronRight className="h-3 w-3" />
          ) : (
            <ChevronLeft className="h-3 w-3" />
          )}
        </button>
      </aside>

      {/* Main content */}
      <div className="flex flex-1 flex-col">
        {/* Mobile header */}
        <header className="flex h-16 items-center justify-between gap-4 border-b border-border px-4 lg:hidden">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsMobileOpen(true)}
            >
              <Menu className="h-5 w-5" />
            </Button>
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
                <Zap className="h-4 w-4 text-primary-foreground" />
              </div>
              <span className="text-lg font-semibold">{"What's New?"}</span>
            </div>
          </div>
        </header>

        {/* Desktop header */}
        <header className="hidden h-16 items-center justify-end border-b border-border px-6 lg:flex gap-4">
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto">
          {children}
        </main>
      </div>
    </div>
  )
}
