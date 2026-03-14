'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { scansApi, websitesApi } from '@/lib/api';
import { useScanStore, useWebsiteStore, useUIStore } from '@/lib/store';
import type { Scan, Website } from '@/types';
import { FileSearch, Play, Eye, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react';

export default function ScansPage() {
  const router = useRouter();
  const { scans, setScans, addScan, setLoading } = useScanStore();
  const { websites } = useWebsiteStore();
  const [websiteFilter, setWebsiteFilter] = useState<string>('all');
  const { addNotification } = useUIStore();

  useEffect(() => {
    loadScans();
    // Poll for running scans
    const interval = setInterval(() => {
      const hasRunningScans = scans.some(s => s.status === 'running' || s.status === 'pending');
      if (hasRunningScans) {
        loadScans();
      }
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadScans = async () => {
    setLoading(true);
    try {
      const data = await scansApi.list(websiteFilter === 'all' ? undefined : websiteFilter);
      setScans(data);
    } catch (error) {
      addNotification({ message: 'Failed to load scans', type: 'error' });
    } finally {
      setLoading(false);
    }
  };

  const getWebsite = (websiteId: string) => {
    return websites.find(w => w.id === websiteId);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-600" />;
      case 'running':
      case 'pending':
        return <Clock className="w-5 h-5 text-blue-600 animate-spin" />;
      default:
        return <AlertCircle className="w-5 h-5 text-gray-600" />;
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-yellow-600';
    if (score >= 50) return 'text-orange-600';
    return 'text-red-600';
  };

  const filteredScans = websiteFilter === 'all'
    ? scans
    : scans.filter(s => s.website_id === websiteFilter);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Scans</h1>
          <p className="text-gray-600">View and manage accessibility scans</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-4">
        <label className="text-sm text-gray-600">Filter by website:</label>
        <select
          value={websiteFilter}
          onChange={(e) => setWebsiteFilter(e.target.value)}
          className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
        >
          <option value="all">All Websites</option>
          {websites.map(w => (
            <option key={w.id} value={w.id}>
              {w.name || new URL(w.url).hostname}
            </option>
          ))}
        </select>
      </div>

      {/* Scans list */}
      {filteredScans.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <FileSearch className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">No scans yet</h2>
          <p className="text-gray-600 mb-6">
            Run your first accessibility scan to see results here
          </p>
          <Link
            href="/dashboard/websites"
            className="inline-flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700"
          >
            <Play className="w-4 h-4" />
            Start Your First Scan
          </Link>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b border-gray-200">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Website
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Issues
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                    Date
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredScans.map((scan) => {
                  const website = getWebsite(scan.website_id);
                  return (
                    <tr key={scan.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <p className="font-medium text-gray-900">
                          {website?.name || website ? new URL(website.url).hostname : 'Unknown'}
                        </p>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          {getStatusIcon(scan.status)}
                          <span className="capitalize text-sm">{scan.status}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        {scan.score !== null && scan.status === 'completed' ? (
                          <span className={`font-bold ${getScoreColor(scan.score)}`}>
                            {scan.score}/100
                          </span>
                        ) : (
                          <span className="text-gray-400">—</span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex gap-3 text-sm">
                          <span className="text-red-600">{scan.critical_issues} critical</span>
                          <span className="text-orange-600">{scan.serious_issues} serious</span>
                          <span className="text-gray-600">{scan.moderate_issues} moderate</span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {scan.completed_at
                          ? new Date(scan.completed_at).toLocaleString()
                          : scan.started_at
                          ? new Date(scan.started_at).toLocaleString()
                          : new Date(scan.created_at).toLocaleString()}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center justify-end gap-2">
                          {scan.status === 'completed' && (
                            <Link
                              href={`/dashboard/scans/${scan.id}`}
                              className="inline-flex items-center gap-1 px-3 py-1.5 text-sm font-medium text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                            >
                              <Eye className="w-4 h-4" />
                              View
                            </Link>
                          )}
                          {scan.status === 'failed' && (
                            <span
                              className="text-sm text-red-600"
                              title={scan.error_message || 'Scan failed'}
                            >
                              {scan.error_message || 'Failed'}
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
