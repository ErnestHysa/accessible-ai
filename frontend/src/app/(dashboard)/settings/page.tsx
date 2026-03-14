'use client';

import { useEffect, useState } from 'react';
import { useAuthStore, useUIStore } from '@/lib/store';
import { authApi } from '@/lib/api';
import { User, Mail, CreditCard, Bell, Shield } from 'lucide-react';

export default function SettingsPage() {
  const user = useAuthStore((state) => state.user);
  const setUser = useAuthStore((state) => state.setUser);
  const { addNotification, theme, setTheme } = useUIStore();
  const [name, setName] = useState(user?.name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [isLoading, setIsLoading] = useState(false);

  const handleSaveProfile = async () => {
    setIsLoading(true);
    try {
      const updated = await authApi.getMe();
      setUser(updated);
      addNotification({ message: 'Profile updated successfully', type: 'success' });
    } catch (error) {
      addNotification({ message: 'Failed to update profile', type: 'error' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600">Manage your account settings</p>
      </div>

      {/* Profile Section */}
      <div className="bg-white rounded-xl border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="font-semibold text-gray-900 flex items-center gap-2">
            <User className="w-5 h-5" />
            Profile
          </h2>
        </div>
        <div className="p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input
                type="email"
                value={email}
                readOnly
                className="w-full px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-500"
              />
            </div>
          </div>
          <div className="flex justify-end">
            <button
              onClick={handleSaveProfile}
              disabled={isLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50"
            >
              {isLoading ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>
      </div>

      {/* Subscription */}
      <div className="bg-white rounded-xl border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="font-semibold text-gray-900 flex items-center gap-2">
            <CreditCard className="w-5 h-5" />
            Subscription
          </h2>
        </div>
        <div className="p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Current Plan</p>
              <p className="text-2xl font-bold text-gray-900 capitalize">{user?.subscription_tier}</p>
            </div>
            <a
              href="/dashboard/settings/billing"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700"
            >
              Manage Subscription
            </a>
          </div>
        </div>
      </div>

      {/* Notifications */}
      <div className="bg-white rounded-xl border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="font-semibold text-gray-900 flex items-center gap-2">
            <Bell className="w-5 h-5" />
            Notifications
          </h2>
        </div>
        <div className="p-6 space-y-4">
          <label className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900">Email notifications</p>
              <p className="text-sm text-gray-600">Receive updates about your scans</p>
            </div>
            <input type="checkbox" className="w-5 h-5 text-blue-600 rounded" defaultChecked />
          </label>
          <label className="flex items-center justify-between">
            <div>
              <p className="font-medium text-gray-900">Scan completion alerts</p>
              <p className="text-sm text-gray-600">Get notified when scans complete</p>
            </div>
            <input type="checkbox" className="w-5 h-5 text-blue-600 rounded" defaultChecked />
          </label>
        </div>
      </div>

      {/* Appearance */}
      <div className="bg-white rounded-xl border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="font-semibold text-gray-900">Appearance</h2>
        </div>
        <div className="p-6">
          <div className="flex gap-4">
            <button
              onClick={() => setTheme('light')}
              className={`flex-1 p-4 border-2 rounded-lg transition-colors ${
                theme === 'light' ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
              }`}
            >
              <div className="w-full h-16 bg-white border border-gray-200 rounded mb-2" />
              <span className="text-sm font-medium">Light</span>
            </button>
            <button
              onClick={() => setTheme('dark')}
              className={`flex-1 p-4 border-2 rounded-lg transition-colors ${
                theme === 'dark' ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
              }`}
            >
              <div className="w-full h-16 bg-gray-900 rounded mb-2" />
              <span className="text-sm font-medium">Dark</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
