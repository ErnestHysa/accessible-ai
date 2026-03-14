'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { websitesApi } from '@/lib/api';
import { useWebsiteStore, useUIStore } from '@/lib/store';
import { useAuthStore } from '@/lib/store';
import { ArrowLeft, Globe, Check } from 'lucide-react';

export default function NewWebsitePage() {
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const { addWebsite } = useWebsiteStore();
  const { addNotification } = useUIStore();

  const [url, setUrl] = useState('');
  const [name, setName] = useState('');
  const [platform, setPlatform] = useState('generic');
  const [isLoading, setIsLoading] = useState(false);

  // Auto-detect platform from URL
  const handleUrlChange = (value: string) => {
    setUrl(value);
    if (!name) {
      try {
        const hostname = new URL(value).hostname;
        setName(hostname);
      } catch {
        // Invalid URL, ignore
      }
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Validate URL
    try {
      new URL(url);
    } catch {
      addNotification({ message: 'Please enter a valid URL', type: 'error' });
      return;
    }

    setIsLoading(true);

    try {
      const website = await websitesApi.create(url, name || undefined, platform);
      addWebsite(website);
      addNotification({ message: 'Website added successfully!', type: 'success' });
      router.push('/dashboard/websites');
    } catch (error: any) {
      addNotification({
        message: error.response?.data?.detail || 'Failed to add website',
        type: 'error',
      });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <Link
          href="/dashboard/websites"
          className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeft className="w-4 h-4" />
          Back to Websites
        </Link>
        <h1 className="text-2xl font-bold text-gray-900">Add Website</h1>
        <p className="text-gray-600">
          Add a website to monitor for accessibility compliance
        </p>
      </div>

      {/* Form */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* URL */}
          <div>
            <label htmlFor="url" className="block text-sm font-medium text-gray-700 mb-2">
              Website URL <span className="text-red-500">*</span>
            </label>
            <div className="relative">
              <Globe className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                id="url"
                type="url"
                value={url}
                onChange={(e) => handleUrlChange(e.target.value)}
                placeholder="https://example.com"
                required
                className="w-full pl-10 pr-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
              />
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Include the full URL with https:// or http://
            </p>
          </div>

          {/* Name */}
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
              Website Name
            </label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="My Website"
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            />
            <p className="text-xs text-gray-500 mt-1">
              Optional - defaults to domain name if not provided
            </p>
          </div>

          {/* Platform */}
          <div>
            <label htmlFor="platform" className="block text-sm font-medium text-gray-700 mb-2">
              Platform
            </label>
            <select
              id="platform"
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
              className="w-full px-4 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none"
            >
              <option value="generic">Generic Website</option>
              <option value="wordpress">WordPress</option>
              <option value="shopify">Shopify</option>
              <option value="webflow">Webflow</option>
              <option value="squarespace">Squarespace</option>
              <option value="wix">WIX</option>
            </select>
            <p className="text-xs text-gray-500 mt-1">
              Selecting a platform enables additional integrations
            </p>
          </div>

          {/* Info box */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-900">
              <strong>What happens next?</strong>
            </p>
            <ul className="text-sm text-blue-800 mt-2 space-y-1">
              <li className="flex items-start gap-2">
                <Check className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <span>We'll scan your website for WCAG 2.1 accessibility issues</span>
              </li>
              <li className="flex items-start gap-2">
                <Check className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <span>You'll receive a detailed report with prioritized issues</span>
              </li>
              <li className="flex items-start gap-2">
                <Check className="w-4 h-4 mt-0.5 flex-shrink-0" />
                <span>AI-powered fix suggestions help you resolve issues quickly</span>
              </li>
            </ul>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200">
            <Link
              href="/dashboard/websites"
              className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              Cancel
            </Link>
            <button
              type="submit"
              disabled={isLoading}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? 'Adding...' : 'Add Website'}
            </button>
          </div>
        </form>
      </div>

      {/* Usage info */}
      <div className="bg-gray-50 rounded-lg p-4 text-sm">
        <p className="text-gray-600">
          <strong>Usage:</strong> You have{' '}
          <span className="font-medium text-gray-900">
            {user?.subscription_tier === 'free' && '1 website'}
            {user?.subscription_tier === 'starter' && '3 websites'}
            {user?.subscription_tier === 'pro' && '10 websites'}
            {user?.subscription_tier === 'agency' && 'unlimited websites'}
          </span>{' '}
          on your {user?.subscription_tier} plan.
          {user?.subscription_tier === 'free' && (
            <Link href="/dashboard/settings/billing" className="text-blue-600 hover:underline ml-1">
              Upgrade
            </Link>
          )}
        </p>
      </div>
    </div>
  );
}
