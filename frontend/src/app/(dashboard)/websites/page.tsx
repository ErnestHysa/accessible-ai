'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { websitesApi } from '@/lib/api';
import { useWebsiteStore, useUIStore } from '@/lib/store';
import { useAuthStore } from '@/lib/store';
import type { Website } from '@/types';
import { Plus, Globe, Play, Trash2, Edit, CheckCircle, AlertTriangle } from 'lucide-react';

export default function WebsitesPage() {
  const router = useRouter();
  const user = useAuthStore((state) => state.user);
  const { websites, setWebsites, setLoading, removeWebsite } = useWebsiteStore();
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const { addNotification } = useUIStore();

  useEffect(() => {
    loadWebsites();
  }, []);

  const loadWebsites = async () => {
    setLoading(true);
    try {
      const data = await websitesApi.list();
      setWebsites(data);
    } catch (error) {
      addNotification({ message: 'Failed to load websites', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Are you sure you want to remove this website?')) return;

    setDeletingId(id);
    try {
      await websitesApi.delete(id);
      removeWebsite(id);
      addNotification({ message: 'Website removed successfully', type: 'success' });
    } catch (error) {
      addNotification({ message: 'Failed to remove website', type: 'error' });
    } finally {
      setDeletingId(null);
    }
  };

  const handleQuickScan = async (id: string) => {
    try {
      const result = await websitesApi.triggerScan(id, false);
      addNotification({
        message: `Scan started! Track progress in Scans tab.`,
        type: 'success',
      });
      router.push('/dashboard/scans');
    } catch (error: any) {
      addNotification({
        message: error.response?.data?.detail || 'Failed to start scan',
        type: 'error',
      });
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600 bg-green-50 border-green-200';
    if (score >= 70) return 'text-yellow-600 bg-yellow-50 border-yellow-200';
    if (score >= 50) return 'text-orange-600 bg-orange-50 border-orange-200';
    return 'text-red-600 bg-red-50 border-red-200';
  };

  const getPlatformLabel = (platform: string) => {
    const labels: Record<string, string> = {
      wordpress: 'WordPress',
      shopify: 'Shopify',
      webflow: 'Webflow',
      squarespace: 'Squarespace',
      wix: 'WIX',
      generic: 'Website',
    };
    return labels[platform] || platform;
  };

  // Check if user can add more websites
  const canAddWebsite = () => {
    const limits: Record<string, number> = {
      free: 1,
      starter: 3,
      pro: 10,
      agency: -1,
    };
    const limit = limits[user?.subscription_tier || 'free'];
    return limit === -1 || websites.length < limit;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Websites</h1>
          <p className="text-gray-600">Manage your monitored websites</p>
        </div>
        <Link
          href="/dashboard/websites/new"
          className={`inline-flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
            canAddWebsite()
              ? 'bg-blue-600 text-white hover:bg-blue-700'
              : 'bg-gray-100 text-gray-400 cursor-not-allowed'
          }`}
          onClick={(e) => {
            if (!canAddWebsite()) {
              e.preventDefault();
              addNotification({
                message: `Upgrade your plan to add more websites`,
                type: 'error',
              });
            }
          }}
        >
          <Plus className="w-4 h-4" />
          Add Website
        </Link>
      </div>

      {/* Upgrade prompt if at limit */}
      {!canAddWebsite() && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 flex items-center gap-4">
          <AlertTriangle className="w-5 h-5 text-blue-600" />
          <div className="flex-1">
            <p className="font-medium text-blue-900">Website limit reached</p>
            <p className="text-sm text-blue-700">
              Upgrade to add more websites to your account.
            </p>
          </div>
          <Link
            href="/dashboard/settings/billing"
            className="px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700"
          >
            Upgrade
          </Link>
        </div>
      )}

      {/* Websites list */}
      {websites.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <Globe className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">No websites yet</h2>
          <p className="text-gray-600 mb-6">
            Add your first website to start monitoring accessibility compliance
          </p>
          <Link
            href="/dashboard/websites/new"
            className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700"
          >
            <Plus className="w-4 h-4" />
            Add Your First Website
          </Link>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Website
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Platform
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Last Scan
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {websites.map((website) => (
                  <tr key={website.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                          <Globe className="w-5 h-5 text-gray-600" />
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">
                            {website.name || new URL(website.url).hostname}
                          </p>
                          <p className="text-sm text-gray-500">{website.url}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full capitalize">
                        {getPlatformLabel(website.platform)}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      {website.latest_score !== null ? (
                        <div className="flex items-center gap-2">
                          <div
                            className={`w-2 h-2 rounded-full ${
                              website.latest_score >= 90
                                ? 'bg-green-500'
                                : website.latest_score >= 70
                                ? 'bg-yellow-500'
                                : 'bg-red-500'
                            }`}
                          />
                          <span className={`font-semibold ${getScoreColor(website.latest_score).split(' ')[0]}`}>
                            {website.latest_score}/100
                          </span>
                        </div>
                      ) : (
                        <span className="text-sm text-gray-500">Not scanned</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {website.last_scan_at
                        ? new Date(website.last_scan_at).toLocaleDateString()
                        : 'Never'}
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleQuickScan(website.id)}
                          className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                          title="Start scan"
                        >
                          <Play className="w-4 h-4" />
                        </button>
                        <Link
                          href={`/dashboard/websites/${website.id}`}
                          className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                          title="View details"
                        >
                          <CheckCircle className="w-4 h-4" />
                        </Link>
                        <button
                          onClick={() => handleDelete(website.id)}
                          disabled={deletingId === website.id}
                          className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
                          title="Remove website"
                        >
                          {deletingId === website.id ? (
                            <div className="w-4 h-4 border-2 border-red-600 border-t-transparent rounded-full animate-spin" />
                          ) : (
                            <Trash2 className="w-4 h-4" />
                          )}
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
