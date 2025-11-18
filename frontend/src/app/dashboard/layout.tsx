'use client'

import { ProtectedRoute } from '@/components/protected-route'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/contexts/auth-context'
import { LogOut, LayoutDashboard, Activity, ClipboardCheck } from 'lucide-react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const { user, logout } = useAuth()
  const pathname = usePathname()

  const navigation = [
    {
      name: 'Overview',
      href: '/dashboard',
      icon: LayoutDashboard,
      current: pathname === '/dashboard',
    },
    {
      name: 'Review Queue',
      href: '/dashboard/review-queue',
      icon: ClipboardCheck,
      current: pathname === '/dashboard/review-queue',
    },
    {
      name: 'Activity',
      href: '/dashboard/activity',
      icon: Activity,
      current: pathname === '/dashboard/activity',
    },
  ]

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        {/* Top Navigation */}
        <nav className="bg-white border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex">
                <div className="flex-shrink-0 flex items-center">
                  <h1 className="text-xl font-bold">Email Agent</h1>
                </div>
                <div className="hidden sm:ml-8 sm:flex sm:space-x-4">
                  {navigation.map((item) => (
                    <Link
                      key={item.name}
                      href={item.href}
                      className={cn(
                        'inline-flex items-center px-3 py-2 text-sm font-medium rounded-md',
                        item.current
                          ? 'bg-gray-100 text-gray-900'
                          : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50'
                      )}
                    >
                      <item.icon className="mr-2 h-4 w-4" />
                      {item.name}
                    </Link>
                  ))}
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <div className="text-sm text-gray-700">
                  <span className="font-medium">{user?.name}</span>
                  <span className="text-gray-500 ml-2">({user?.email})</span>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={logout}
                  className="flex items-center"
                >
                  <LogOut className="mr-2 h-4 w-4" />
                  Logout
                </Button>
              </div>
            </div>
          </div>
        </nav>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {children}
        </main>
      </div>
    </ProtectedRoute>
  )
}
