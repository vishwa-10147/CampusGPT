// ==============================================================================
// CampusGPT Frontend — Layout Components
// ==============================================================================
import React, { useState } from 'react'
import { Link, NavLink, useLocation } from 'react-router-dom'
import { cn } from '../ui'
import { Button, Avatar, Separator } from '../ui'
import { useAuth } from '../../features/auth/AuthContext'
import {
  LayoutDashboard,
  MessageSquare,
  FileText,
  Settings,
  LogOut,
  Menu,
  X,
  BookOpen,
  Bot,
} from 'lucide-react'

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

export const Sidebar = ({ isOpen, onClose }: SidebarProps) => {
  const location = useLocation()
  const { user, logout } = useAuth()

  const navItems = [
    { path: '/chat', label: 'New Chat', icon: MessageSquare },
    { path: '/history', label: 'History', icon: BookOpen },
    { path: '/documents', label: 'Documents', icon: FileText },
    { path: '/settings', label: 'Settings', icon: Settings },
  ]

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed lg:static inset-y-0 left-0 z-50 w-72 bg-white border-r border-neutral-200 transform transition-transform duration-200 ease-out flex flex-col',
          isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
        role="navigation"
        aria-label="Main navigation"
      >
        {/* Header */}
        <div className="flex items-center justify-between h-16 px-4 border-b border-neutral-200">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-primary-600 flex items-center justify-center">
              <Bot className="h-5 w-5 text-white" />
            </div>
            <span className="font-semibold text-lg text-neutral-900">CampusGPT</span>
          </div>
          <button
            className="lg:hidden p-2 rounded-lg text-neutral-500 hover:bg-neutral-100"
            onClick={onClose}
            aria-label="Close sidebar"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 py-4 space-y-1 overflow-y-auto" role="nav">
          {navItems.map((item) => {
            const Icon = item.icon
            const isActive = location.pathname === item.path || location.pathname.startsWith(item.path + '/')
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={onClose}
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900'
                )}
                aria-current={isActive ? 'page' : undefined}
              >
                <Icon className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
                {item.label}
              </NavLink>
            )
          })}

          {/* Admin section */}
          {user?.is_admin && (
            <>
              <Separator className="my-4" />
              <NavLink
                to="/admin"
                onClick={onClose}
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                  location.pathname.startsWith('/admin')
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900'
                )}
              >
                <LayoutDashboard className="h-5 w-5 flex-shrink-0" aria-hidden="true" />
                Admin
              </NavLink>
            </>
          )}
        </nav>

        {/* User section */}
        <div className="p-4 border-t border-neutral-200">
          <div className="flex items-center gap-3 mb-3">
            <Avatar name={user?.full_name} size="md" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-neutral-900 truncate">{user?.full_name}</p>
              <p className="text-xs text-neutral-500 truncate">{user?.email}</p>
            </div>
          </div>
          <Button variant="ghost" size="sm" className="w-full justify-start" onClick={() => logout()}>
            <LogOut className="h-4 w-4" aria-hidden="true" />
            Sign Out
          </Button>
        </div>
      </aside>
    </>
  )
}

// Header
interface HeaderProps {
  onMenuClick: () => void
}

export const Header = ({ onMenuClick }: HeaderProps) => {
  return (
    <header className="sticky top-0 z-30 h-16 bg-white/95 backdrop-blur-sm border-b border-neutral-200 lg:hidden">
      <div className="h-full px-4 flex items-center justify-between">
        <button
          onClick={onMenuClick}
          className="p-2 rounded-lg text-neutral-500 hover:bg-neutral-100"
          aria-label="Open menu"
        >
          <Menu className="h-6 w-6" />
        </button>
        <div className="flex items-center gap-2">
          <div className="h-7 w-7 rounded-lg bg-primary-600 flex items-center justify-center">
            <Bot className="h-4 w-4 text-white" />
          </div>
          <span className="font-semibold text-base text-neutral-900">CampusGPT</span>
        </div>
        <div className="w-10" />
      </div>
    </header>
  )
}

// Main Layout
interface MainLayoutProps {
  children: React.ReactNode
}

export const MainLayout = ({ children }: MainLayoutProps) => {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="min-h-screen bg-neutral-50 flex">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
      <Header onMenuClick={() => setSidebarOpen(true)} />
      <main className="flex-1 lg:ml-72 min-w-0">
        <div className="lg:hidden h-16" aria-hidden="true" />
        <div className="p-4 lg:p-6">
          {children}
        </div>
      </main>
    </div>
  )
}
// Centered card page used by sign-in, sign-up and email confirmation
export const AuthPageShell = ({ children }: { children: React.ReactNode }) => (
  <div className="min-h-screen flex items-center justify-center bg-neutral-50 px-4 py-12">
    <div className="w-full">
      <div className="flex justify-center mb-8">
        <Link to="/" className="flex items-center gap-2" aria-label="CampusGPT Home">
          <div className="h-10 w-10 rounded-xl bg-primary-600 flex items-center justify-center">
            <Bot className="h-6 w-6 text-white" />
          </div>
          <span className="text-xl font-bold text-neutral-900">CampusGPT</span>
        </Link>
      </div>
      {children}
    </div>
  </div>
)
