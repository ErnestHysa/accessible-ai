/** Shared type definitions for the frontend. */

export type SubscriptionTier = 'free' | 'starter' | 'pro' | 'agency';

export interface User {
  id: string;
  email: string;
  name?: string;
  subscription_tier: SubscriptionTier;
  is_active: boolean;
  email_verified: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export type Platform = 'generic' | 'wordpress' | 'shopify' | 'webflow' | 'squarespace' | 'wix';

export interface Website {
  id: string;
  user_id: string;
  url: string;
  name?: string;
  platform: Platform;
  api_key?: string;
  is_active: boolean;
  last_scan_at?: string;
  latest_score?: number;
  created_at: string;
}

export type ScanStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

export type Severity = 'critical' | 'serious' | 'moderate' | 'minor';

export interface Scan {
  id: string;
  website_id: string;
  status: ScanStatus;
  score?: number;
  total_issues: number;
  critical_issues: number;
  serious_issues: number;
  moderate_issues: number;
  minor_issues: number;
  started_at?: string;
  completed_at?: string;
  report_url?: string;
  error_message?: string;
  created_at: string;
}

export interface Issue {
  id: string;
  scan_id: string;
  type: string;
  severity: Severity;
  selector?: string;
  description: string;
  impact?: string;
  fix_suggestion?: string;
  fix_code?: string;
  is_fixed: boolean;
  page_url?: string;
  element_html?: string;
  created_at: string;
}

export interface SubscriptionTierInfo {
  id: string;
  name: string;
  price: number;
  interval: string;
  websites_limit: number;
  scans_limit: number;
  features: string[];
}

export interface Subscription {
  id: string;
  tier: string;
  status: string;
  current_period_start?: string;
  current_period_end?: string;
  cancel_at_period_end: boolean;
  trial_end?: string;
}

export interface Usage {
  current_month: {
    websites: number;
    scans: number;
  };
  limits: {
    websites: number;
    scans_per_month: number;
  };
  remaining: {
    websites: number;
    scans: number;
  };
  reset_date: string;
}
