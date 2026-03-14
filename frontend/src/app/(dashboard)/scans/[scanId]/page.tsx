'use client';

import { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import Link from 'next/link';
import { scansApi, websitesApi } from '@/lib/api';
import { useUIStore } from '@/lib/store';
import type { Scan, Issue, Website } from '@/types';
import {
  ArrowLeft,
  Download,
  AlertTriangle,
  AlertCircle,
  Info,
  CheckCircle,
  Copy,
  ExternalLink,
} from 'lucide-react';

export default function ScanDetailPage() {
  const router = useRouter();
  const params = useParams();
  const scanId = params.scanId as string;
  const { addNotification } = useUIStore();

  const [scan, setScan] = useState<Scan | null>(null);
  const [issues, setIssues] = useState<Issue[]>([]);
  const [website, setWebsite] = useState<Website | null>(null);
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [fixedFilter, setFixedFilter] = useState<string>('all');
  const [selectedIssue, setSelectedIssue] = useState<Issue | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadScanData();
  }, [scanId]);

  const loadScanData = async () => {
    setIsLoading(true);
    try {
      const [scanData, issuesData] = await Promise.all([
        scansApi.get(scanId),
        scansApi.getIssues(scanId),
      ]);

      setScan(scanData);
      setIssues(issuesData);

      // Load website info
      const websiteData = await websitesApi.get(scanData.website_id);
      setWebsite(websiteData);
    } catch (error) {
      addNotification({ message: 'Failed to load scan details', type: 'error' });
      router.push('/dashboard/scans');
    } finally {
      setIsLoading(false);
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <AlertTriangle className="w-5 h-5 text-red-600" />;
      case 'serious':
        return <AlertCircle className="w-5 h-5 text-orange-600" />;
      case 'moderate':
        return <Info className="w-5 h-5 text-yellow-600" />;
      case 'minor':
        return <CheckCircle className="w-5 h-5 text-blue-600" />;
      default:
        return <Info className="w-5 h-5 text-gray-600" />;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'border-red-200 bg-red-50';
      case 'serious':
        return 'border-orange-200 bg-orange-50';
      case 'moderate':
        return 'border-yellow-200 bg-yellow-50';
      case 'minor':
        return 'border-blue-200 bg-blue-50';
      default:
        return 'border-gray-200 bg-gray-50';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-yellow-600';
    if (score >= 50) return 'text-orange-600';
    return 'text-red-600';
  };

  const filteredIssues = issues.filter(issue => {
    if (severityFilter !== 'all' && issue.severity !== severityFilter) return false;
    if (fixedFilter === 'fixed' && !issue.is_fixed) return false;
    if (fixedFilter === 'unfixed' && issue.is_fixed) return false;
    return true;
  });

  const handleApplyFix = async (issueId: string) => {
    try {
      const result = await scansApi.applyFix(issueId, false);
      if (result.fix_code) {
        setSelectedIssue(prev => prev?.id === issueId ? { ...prev, fix_code: result.fix_code! } : prev);
      }
      addNotification({ message: result.message, type: result.success ? 'success' : 'error' });
    } catch (error) {
      addNotification({ message: 'Failed to get fix', type: 'error' });
    }
  };

  const copyFixCode = (code: string) => {
    navigator.clipboard.writeText(code);
    addNotification({ message: 'Code copied to clipboard', type: 'success' });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!scan || !website) {
    return <div>Scan not found</div>;
  }

  const issueStats = {
    total: issues.length,
    critical: issues.filter(i => i.severity === 'critical').length,
    serious: issues.filter(i => i.severity === 'serious').length,
    moderate: issues.filter(i => i.severity === 'moderate').length,
    minor: issues.filter(i => i.severity === 'minor').length,
    fixed: issues.filter(i => i.is_fixed).length,
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            href="/dashboard/scans"
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Scan Results</h1>
            <p className="text-gray-600">{website.name || new URL(website.url).hostname}</p>
          </div>
        </div>
        <button
          onClick={() => {
            const report = JSON.stringify({ scan, issues }, null, 2);
            const blob = new Blob([report], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `scan-${scanId}.json`;
            a.click();
          }}
          className="inline-flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
        >
          <Download className="w-4 h-4" />
          Export Report
        </button>
      </div>

      {/* Score Card */}
      {scan.status === 'completed' && scan.score !== null && (
        <div className={`bg-gradient-to-r ${scan.score >= 70 ? 'from-green-50 to-emerald-50 border-green-200' : 'from-orange-50 to-amber-50 border-orange-200'} rounded-xl border p-6`}>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600 mb-1">Accessibility Score</p>
              <p className="text-4xl font-bold text-gray-900">{scan.score}/100</p>
              <p className="text-sm text-gray-600 mt-1">
                {scan.score >= 90 ? 'Excellent!' : scan.score >= 70 ? 'Good progress!' : 'Needs improvement'}
              </p>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-600 mb-2">Issues by Severity</div>
              <div className="space-y-1">
                <div className="flex items-center gap-2 text-sm">
                  <div className="w-3 h-3 bg-red-500 rounded-full" />
                  <span>{issueStats.critical} Critical</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <div className="w-3 h-3 bg-orange-500 rounded-full" />
                  <span>{issueStats.serious} Serious</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <div className="w-3 h-3 bg-yellow-500 rounded-full" />
                  <span>{issueStats.moderate} Moderate</span>
                </div>
                <div className="flex items-center gap-2 text-sm">
                  <div className="w-3 h-3 bg-blue-500 rounded-full" />
                  <span>{issueStats.minor} Minor</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center gap-4 flex-wrap">
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600">Severity:</label>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
          >
            <option value="all">All</option>
            <option value="critical">Critical</option>
            <option value="serious">Serious</option>
            <option value="moderate">Moderate</option>
            <option value="minor">Minor</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm text-gray-600">Status:</label>
          <select
            value={fixedFilter}
            onChange={(e) => setFixedFilter(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 outline-none"
          >
            <option value="all">All</option>
            <option value="unfixed">Unfixed</option>
            <option value="fixed">Fixed</option>
          </select>
        </div>
        <div className="ml-auto text-sm text-gray-600">
          Showing {filteredIssues.length} of {issueStats.total} issues
        </div>
      </div>

      {/* Issues List */}
      {filteredIssues.length === 0 ? (
        <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
          <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">No issues found</h2>
          <p className="text-gray-600">
            {severityFilter !== 'all' || fixedFilter !== 'all'
              ? 'Try adjusting your filters'
              : 'Great job! No accessibility issues were detected.'}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredIssues.map((issue) => (
            <div
              key={issue.id}
              className={`border rounded-lg ${getSeverityColor(issue.severity)} ${
                selectedIssue?.id === issue.id ? 'ring-2 ring-blue-500' : ''
              }`}
            >
              <div className="p-4">
                <div className="flex items-start gap-4">
                  <div className="flex-shrink-0 mt-1">{getSeverityIcon(issue.severity)}</div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold text-gray-900">{issue.type}</h3>
                      <span className={`px-2 py-0.5 text-xs font-medium rounded-full capitalize ${
                        issue.severity === 'critical' ? 'bg-red-100 text-red-700' :
                        issue.severity === 'serious' ? 'bg-orange-100 text-orange-700' :
                        issue.severity === 'moderate' ? 'bg-yellow-100 text-yellow-700' :
                        'bg-blue-100 text-blue-700'
                      }`}>
                        {issue.severity}
                      </span>
                      {issue.is_fixed && (
                        <span className="px-2 py-0.5 text-xs font-medium rounded-full bg-green-100 text-green-700">
                          Fixed
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-700 mb-2">{issue.description}</p>
                    {issue.selector && (
                      <p className="text-xs text-gray-500 font-mono mb-2">
                        Selector: <code className="bg-white px-1.5 py-0.5 rounded">{issue.selector}</code>
                      </p>
                    )}
                    {issue.page_url && (
                      <a
                        href={issue.page_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-blue-600 hover:underline flex items-center gap-1"
                      >
                        View on page <ExternalLink className="w-3 h-3" />
                      </a>
                    )}
                  </div>

                  <button
                    onClick={() => setSelectedIssue(issue)}
                    className="px-3 py-1.5 text-sm font-medium text-blue-600 hover:bg-blue-100 rounded-lg transition-colors"
                  >
                    {issue.fix_code || selectedIssue?.id === issue.id ? 'Hide Fix' : 'View Fix'}
                  </button>
                </div>

                {selectedIssue?.id === issue.id && (
                  <div className="mt-4 pt-4 border-t border-gray-200">
                    {!issue.fix_code ? (
                      <button
                        onClick={() => handleApplyFix(issue.id)}
                        className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700"
                      >
                        Generate AI Fix
                      </button>
                    ) : (
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-medium text-gray-900">Suggested Fix</h4>
                          <button
                            onClick={() => copyFixCode(issue.fix_code!)}
                            className="inline-flex items-center gap-1 px-2 py-1 text-xs text-gray-600 hover:bg-gray-200 rounded transition-colors"
                          >
                            <Copy className="w-3 h-3" />
                            Copy
                          </button>
                        </div>
                        <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm">
                          <code>{issue.fix_code}</code>
                        </pre>
                        {issue.fix_suggestion && (
                          <p className="text-sm text-gray-600 mt-2">{issue.fix_suggestion}</p>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
