// ==============================================================================
// CampusGPT Frontend — Settings Page
// ==============================================================================
import { useState } from 'react'
import { useAuth } from '../features/auth/AuthContext'
import { MainLayout } from '../components/layout'
import { Card, Button, Input, Badge } from '../components/ui'
import { User, Bell, Shield, Palette } from 'lucide-react'

export const Settings = () => {
  const { user, logout } = useAuth()
  const [activeTab, setActiveTab] = useState<'profile' | 'security' | 'preferences' | 'danger'>('profile')

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'security', label: 'Security', icon: Shield },
    { id: 'preferences', label: 'Preferences', icon: Palette },
    { id: 'danger', label: 'Danger Zone', icon: Bell },
  ]

  return (
    <MainLayout>
      <div className="max-w-3xl mx-auto space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-2xl font-bold text-neutral-900">Settings</h1>
          <p className="text-neutral-600 mt-1">Manage your account settings</p>
        </div>

        {/* Tabs */}
        <div className="border-b border-neutral-200">
          <nav className="flex gap-1" role="tablist" aria-label="Settings tabs">
            {tabs.map((tab) => {
              const Icon = tab.icon
              const isActive = activeTab === tab.id
              return (
                <button
                  key={tab.id}
                  role="tab"
                  aria-selected={isActive}
                  aria-controls={`${tab.id}-panel`}
                  id={`${tab.id}-tab`}
                  onClick={() => setActiveTab(tab.id as typeof activeTab)}
                  className={`
                    flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors
                    ${isActive
                      ? 'border-primary-600 text-primary-600'
                      : 'border-transparent text-neutral-500 hover:text-neutral-700 hover:border-neutral-300'
                    }
                  `}
                >
                  <Icon className="h-4 w-4" />
                  {tab.label}
                </button>
              )
            })}
          </nav>
        </div>

        {/* Tab Panels */}
        <div className="space-y-6">
          {/* Profile Tab */}
          <div role="tabpanel" id="profile-panel" aria-labelledby="profile-tab" hidden={activeTab !== 'profile'}>
            <Card>
              <div className="p-6">
                <h2 className="text-lg font-semibold text-neutral-900 mb-6">Profile Information</h2>
                <form className="space-y-4">
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    <Input
                      label="Full Name"
                      value={user?.full_name || ''}
                      disabled
                    />
                    <Input
                      label="Email"
                      type="email"
                      value={user?.email || ''}
                      disabled
                    />
                  </div>
                  <div>
                    <Label htmlFor="bio">Bio</Label>
                    <textarea
                      id="bio"
                      className="input min-h-[100px] resize-y"
                      placeholder="Tell us about yourself..."
                      defaultValue={''}
                    />
                  </div>
                  <div className="flex justify-end">
                    <Button variant="primary" disabled>Save Changes</Button>
                  </div>
                </form>
              </div>
            </Card>
          </div>

          {/* Security Tab */}
          <div role="tabpanel" id="security-panel" aria-labelledby="security-tab" hidden={activeTab !== 'security'}>
            <Card>
              <div className="p-6 space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-neutral-900 mb-4">Change Password</h3>
                  <form className="space-y-4">
                    <Input label="Current Password" type="password" placeholder="••••••••" />
                    <Input label="New Password" type="password" placeholder="••••••••" />
                    <Input label="Confirm New Password" type="password" placeholder="••••••••" />
                    <Button variant="primary">Update Password</Button>
                  </form>
                </div>

                <div className="border-t border-neutral-200 pt-6">
                  <h3 className="text-lg font-semibold text-neutral-900 mb-4">Active Sessions</h3>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 bg-neutral-50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <div className="h-10 w-10 rounded-full bg-primary-100 flex items-center justify-center">
                          <Monitor className="h-5 w-5 text-primary-600" />
                        </div>
                        <div>
                          <p className="font-medium text-neutral-900">Current Session</p>
                          <p className="text-sm text-neutral-500">Chrome on Windows • Active now</p>
                        </div>
                      </div>
                      <Badge variant="success">Current</Badge>
                    </div>
                    <p className="text-sm text-neutral-500">Only one active session (current)</p>
                  </div>
                </div>
              </div>
            </Card>
          </div>

          {/* Preferences Tab */}
          <div role="tabpanel" id="preferences-panel" aria-labelledby="preferences-tab" hidden={activeTab !== 'preferences'}>
            <Card>
              <div className="p-6 space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-neutral-900 mb-4">Appearance</h3>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-neutral-900">Theme</p>
                        <p className="text-sm text-neutral-500">Choose your preferred color scheme</p>
                      </div>
                      <div className="flex gap-2">
                        <Button variant="secondary" size="sm">Light</Button>
                        <Button variant="secondary" size="sm">Dark</Button>
                        <Button variant="primary" size="sm">System</Button>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="border-t border-neutral-200 pt-6">
                  <h3 className="text-lg font-semibold text-neutral-900 mb-4">Notifications</h3>
                  <div className="space-y-4">
                    <label className="flex items-center justify-between cursor-pointer">
                      <div>
                        <p className="font-medium text-neutral-900">Email notifications</p>
                        <p className="text-sm text-neutral-500">Receive updates via email</p>
                      </div>
                      <input type="checkbox" className="h-5 w-5 rounded border-neutral-300 text-primary-600 focus:ring-primary-500" defaultChecked />
                    </label>
                    <label className="flex items-center justify-between cursor-pointer">
                      <div>
                        <p className="font-medium text-neutral-900">Push notifications</p>
                        <p className="text-sm text-neutral-500">Browser notifications for new messages</p>
                      </div>
                      <input type="checkbox" className="h-5 w-5 rounded border-neutral-300 text-primary-600 focus:ring-primary-500" />
                    </label>
                  </div>
                </div>
              </div>
            </Card>
          </div>

          {/* Danger Zone Tab */}
          <div role="tabpanel" id="danger-panel" aria-labelledby="danger-tab" hidden={activeTab !== 'danger'}>
            <Card className="border-red-200">
              <div className="p-6 space-y-6">
                <div>
                  <h3 className="text-lg font-semibold text-red-900 mb-2 flex items-center gap-2">
                    <AlertTriangle className="h-5 w-5" />
                    Danger Zone
                  </h3>
                  <p className="text-red-700">Irreversible actions. Proceed with caution.</p>
                </div>

                <div className="border-t border-red-200 pt-6 space-y-4">
                  <div className="flex items-center justify-between p-4 bg-red-50 rounded-lg">
                    <div>
                      <p className="font-medium text-red-900">Delete Account</p>
                      <p className="text-sm text-red-700">Permanently delete your account and all data</p>
                    </div>
                    <Button variant="danger" onClick={() => alert('Account deletion not implemented yet')}>
                      Delete Account
                    </Button>
                  </div>

                  <div className="flex items-center justify-between p-4 bg-red-50 rounded-lg">
                    <div>
                      <p className="font-medium text-red-900">Sign Out Everywhere</p>
                      <p className="text-sm text-red-700">Revoke all active sessions</p>
                    </div>
                    <Button variant="danger" onClick={() => logout()}>
                      Sign Out
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </div>
    </MainLayout>
  )
}

// Missing imports
import { Label } from '../components/ui'
import { Monitor, AlertTriangle } from 'lucide-react'