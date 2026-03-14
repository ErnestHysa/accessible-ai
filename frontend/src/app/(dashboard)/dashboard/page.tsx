'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { websitesApi, subscriptionApi } from '@/lib/api';
import { useWebsiteStore, useUIStore } from '@/lib/store';
import type { Website, Usage } from '@/types';
import {
  Plus,
  Globe,
  Play,
  CheckCircle,
  AlertTriangle,
  TrendingUp,
} from 'lucide-react';

export default function DashboardPage() {
  const { websites, setWebsites, addWebsite, setLoading } = useWebsiteStore();
  const [usage, setUsage] = useState<Usage | null>(null);
  const [isLoadingUsage, setIsLoadingUsage] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    setLoading(true);
    setIsLoadingUsage(true);
    try {
      const [websitesData, usageData] = await Promise.all([
        websitesApi.list(),
        subscriptionApi.getUsage(),
      ]);
      setWebsites(websitesData);
      setUsage(usageData);
    } catch (error) {
      console.error('Failed to load dashboard:', error);
    } finally {
      setLoading(false);
      setIsLoadingUsage(false);
    }
  };

  const handleQuickScan = async (websiteId: string) => {
    try {
      await websitesApi.triggerScan(websiteId, false);
      // Navigate to scans page
      window.location.href = '/dashboard/scans';
    } catch (error) {
      console.error('Failed to start scan:', error);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-yellow-600';
    if (score >= 50) return 'text-orange-600';
    return 'text-red-600';
  };

  const getScoreBgColor = (score: number) => {
    if (score >= 90) return 'bg-green-50';
    if (score >= 70) return 'bg-yellow-50';
    if (score >= 50) return 'bg-orange-50';
    return 'bg-red-50';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">Monitor your website accessibility</p>
        </div>
        <Link
          href="/dashboard/websites/new"
          className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add Website
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Websites</p>
              <p className="text-2xl font-bold text-gray-900">{websites.length}</p>
            </div>
            <div className="w-12 h-12 bg-blue-50 rounded-lg flex items-center justify-center">
              <Globe className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Avg Score</p>
              <p className="text-2xl font-bold text-gray-900">
                {websites.length > 0
                  ? Math.round(
                      websites.reduce((sum, w) => sum + (w.latest_score || 0), 0) /
                        websites.filter((w) => w.latest_score).length || 0
                    )
                  : '-'}
              </p>
            </div>
            <div className="w-12 h-12 bg-green-50 rounded-lg flex items-center justify-center">
              <TrendingUp className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Scans This Month</p>
              <p className="text-2xl font-bold text-gray-900">
                {isLoadingUsage ? '...' : usage?.current_month.scans || 0}
              </p>
            </div>
            <div className="w-12 h-12 bg-purple-50 rounded-lg flex items-center justify-center">
              <CheckCircle className="w-6 h-6 text-purple-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Issues Found</p>
              <p className="text-2xl font-bold text-gray-900">
                {websites.reduce((sum, w) => {
                  if (w.latest_score && w.latest_score < 100) {
                    return sum + Math.floor((100 - w.latest_score) / 5);
                  }
                  return sum;
                }, 0)}
              </p>
            </div>
            <div className="w-12 h-12 bg-orange-50 rounded-lg flex items-center justify-center">
              <AlertTriangle className="w-6 h-6 text-orange-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Websites */}
      <div className="bg-white rounded-xl border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="font-semibold text-gray-900">Your Websites</h2>
        </div>

        {websites.length === 0 ? (
          <div className="p-12 text-center">
            <Globe className="w-12 h-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No websites yet</h3>
            <p className="text-gray-600 mb-4">
              Add your first website to start monitoring accessibility
            </p>
            <Link
              href="/dashboard/websites/new"
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
            >
              <Plus className="w-4 h-4" />
              Add Your First Website
            </Link>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {websites.map((website) => (
              <div key={website.id} className="p-6 flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                    <Globe className="w-5 h-5 text-gray-600" />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900">
                      {website.name || new URL(website.url).hostname}
                    </h3>
                    <p className="text-sm text-gray-600">{website.url}</p>
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  {website.latest_score !== null ? (
                    <div
                      className={`px-3 py-1 rounded-full ${getScoreBgColor(website.latest_score)}`}
                    >
                      <span className={`text-sm font-semibold ${getScoreColor(website.latest_score)}`}>
                        {website.latest_score}/100
                      </span>
                    </div>
                  ) : (
                    <span className="text-sm text-gray-500">Not scanned</span>
                  )}

                  <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-full capitalize">
                    {website.platform}
                  </span>

                  <button
                    onClick={() => handleQuickScan(website.id)}
                    className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                    title="Start scan"
                  >
                    <Play className="w-5 h-5" />
                  </button>

                  <Link
                    href={`/dashboard/websites/${website.id}`}
                    className="px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    View
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
