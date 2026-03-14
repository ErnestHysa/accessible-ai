/**
 * TypeScript type definitions for AccessibleAI.
 */

// User types
export interface User {
  id: string;
  email: string;
  name?: string;
  subscription_tier: 'free' | 'starter' | 'pro' | 'agency';
  created_at: string;
  updated_at?: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  user: User;
}

// Website types
export interface Website {
  id: string;
  user_id: string;
  url: string;
  name?: string;
  platform: 'generic' | 'wordpress' | 'shopify' | 'webflow' | 'squarespace' | 'wix';
  api_key?: string;
  is_active: boolean;
  last_scan_at?: string;
  latest_score?: number;
  created_at: string;
  updated_at?: string;
}

export interface WebsiteCreate {
  url: string;
  name?: string;
  platform?: string;
}

export interface WebsiteUpdate {
  name?: string;
  platform?: string;
  is_active?: boolean;
}

// Scan types
export interface Scan {
  id: string;
  website_id: string;
  user_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  score?: number;
  total_issues?: number;
  critical_issues?: number;
  serious_issues?: number;
  moderate_issues?: number;
  minor_issues?: number;
  full_scan: boolean;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  error_message?: string;
}

export interface Issue {
  id: string;
  scan_id: string;
  website_id: string;
  type: string;
  selector?: string;
  description: string;
  severity: 'critical' | 'serious' | 'moderate' | 'minor';
  impact?: string;
  element_html?: string;
  fix_generated: boolean;
  fix_applied: boolean;
  fix_code?: string;
  created_at: string;
}

export interface IssueFix {
  issue_id: string;
  fix_code: string;
  applied: boolean;
}

// Subscription types
export interface Subscription {
  id: string;
  user_id: string;
  tier: 'free' | 'starter' | 'pro' | 'agency';
  status: 'active' | 'cancelled' | 'past_due' | 'incomplete';
  current_period_start?: string;
  current_period_end?: string;
  cancel_at_period_end?: boolean;
  stripe_subscription_id?: string;
  created_at: string;
  updated_at?: string;
}

export interface SubscriptionTierInfo {
  tier: string;
  name: string;
  price: number;
  currency: string;
  max_websites: number;
  max_scans_per_month: number | null;
  features: string[];
}

export interface CheckoutResponse {
  checkout_url: string;
  session_id: string;
}

export interface PortalResponse {
  portal_url: string;
}

// Usage types
export interface Usage {
  scans_used: number;
  scans_limit: number;
  websites_used: number;
  websites_limit: number;
  current_period_start: string;
  current_period_end: string;
}

export interface UsageRecord {
  id: string;
  user_id: string;
  website_id: string;
  scan_id?: string;
  usage_type: 'scan' | 'api_call' | 'export';
  quantity: number;
  created_at: string;
}

// API Response types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pages: number;
  limit: number;
}

export interface ApiError {
  detail: string;
  code?: string;
  fields?: Record<string, string[]>;
}

// Form types
export interface LoginForm {
  email: string;
  password: string;
}

export interface SignupForm {
  email: string;
  password: string;
  name?: string;
}

export interface WebsiteForm {
  url: string;
  name?: string;
  platform?: string;
}

export interface ScanTriggerForm {
  full_scan?: boolean;
  max_pages?: number;
}

// Component prop types
export interface TableColumn<T> {
  key: string;
  title: string;
  sortable?: boolean;
  render?: (value: any, row: T) => React.ReactNode;
}

export interface NotificationProps {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info' | 'warning';
  duration?: number;
}

// Chart data types
export interface ScoreHistoryPoint {
  date: string;
  score: number;
  issues: number;
}

export interface IssueBySeverity {
  critical: number;
  serious: number;
  moderate: number;
  minor: number;
}

// Filter types
export interface ScanFilters {
  website_id?: string;
  status?: string;
  severity?: string;
  date_from?: string;
  date_to?: string;
}

export interface IssueFilters {
  severity?: string;
  is_fixed?: boolean;
  type?: string;
}

// WordPress plugin specific types
export interface WordPressConfig {
  api_key: string;
  site_id: string;
  site_name: string;
  site_url: string;
  auto_scan: 'disabled' | 'daily' | 'weekly' | 'monthly';
  email_notifications: boolean;
  widget_enabled: boolean;
}

export interface ScanResult {
  id: string;
  score: number;
  total_issues: number;
  critical_issues: number;
  serious_issues: number;
  moderate_issues: number;
  minor_issues: number;
  status: string;
  created_at: string;
}

export default null;
