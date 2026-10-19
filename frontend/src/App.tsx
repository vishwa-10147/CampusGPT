// ==============================================================================
// CampusGPT Frontend — Main App Component
// ==============================================================================
import React, { Suspense, lazy } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './features/auth/AuthContext'
import { MainLayout } from './components/layout'
import { Spinner } from './components/ui'

// Lazy load pages for code splitting
const Login = lazy(() => import('./pages/Login').then(m => ({ default: m.Login })))
const Register = lazy(() => import('./pages/Register').then(m => ({ default: m.Register })))
const Chat = lazy(() => import('./pages/Chat').then(m => ({ default: m.Chat })))
const History = lazy(() => import('./pages/History').then(m => ({ default: m.History })))
const Documents = lazy(() => import('./pages/Documents').then(m => ({ default: m.Documents })))
const Settings = lazy(() => import('./pages/Settings').then(m => ({ default: m.Settings })))
const Admin = lazy(() => import('./pages/Admin').then(m => ({ default: m.Admin })))

// Loading fallback
const PageLoader = () => (
  <div className="min-h-screen flex items-center justify-center">
    <Spinner size="lg" />
  </div>
)

// Protected route wrapper
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return <PageLoader />
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

// Public route wrapper (redirect if authenticated)
const PublicRoute = ({ children }: { children: React.ReactNode }) => {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return <PageLoader />
  }

  if (isAuthenticated) {
    return <Navigate to="/chat" replace />
  }

  return <>{children}</>
}

// Admin route wrapper
const AdminRoute = ({ children }: { children: React.ReactNode }) => {
  const { user, isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return <PageLoader />
  }

  if (!isAuthenticated || !user?.is_admin) {
    return <Navigate to="/chat" replace />
  }

  return <>{children}</>
}

const App = () => {
  return (
    <Suspense fallback={<PageLoader />}>
      <Routes>
        {/* Public routes */}
        <Route
          path="/login"
          element={
            <PublicRoute>
              <Login />
            </PublicRoute>
          }
        />
        <Route
          path="/register"
          element={
            <PublicRoute>
              <Register />
            </PublicRoute>
          }
        />

        {/* Protected routes with layout */}
        <Route
          element={
            <ProtectedRoute>
              <MainLayout>
                <Routes>
                  <Route path="/chat" element={<Chat />} />
                  <Route path="/chat/:conversationId" element={<Chat />} />
                  <Route path="/history" element={<History />} />
                  <Route path="/documents" element={<Documents />} />
                  <Route path="/settings" element={<Settings />} />
                  <Route
                    path="/admin"
                    element={
                      <AdminRoute>
                        <Admin />
                      </AdminRoute>
                    }
                  />
                  <Route path="/admin/*" element={
                    <AdminRoute>
                      <Admin />
                    </AdminRoute>
                  } />
                  <Route path="/" element={<Navigate to="/chat" replace />} />
                </Routes>
              </MainLayout>
            </ProtectedRoute>
          }
        />

        {/* Catch all */}
        <Route path="*" element={<Navigate to="/chat" replace />} />
      </Routes>
    </Suspense>
  )
}

export default App