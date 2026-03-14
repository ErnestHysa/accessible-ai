/**
 * Analytics and monitoring integration for AccessibleAI.
 *
 * Supports:
 * - Google Analytics 4 (GA4)
 * - Plausible Analytics (privacy-friendly)
 * - PostHog (product analytics)
 * - Sentry (error tracking)
 */

interface AnalyticsEvent {
  name: string;
  properties?: Record<string, string | number | boolean>;
}

interface UserProperties {
  userId?: string;
  email?: string;
  subscriptionTier?: string;
  signupDate?: string;
}

// Configuration from environment
const GA4_ID = process.env.NEXT_PUBLIC_GA_ID;
const PLAUSIBLE_DOMAIN = process.env.NEXT_PUBLIC_PLAUSIBLE_DOMAIN;
const POSTHOG_KEY = process.env.NEXT_PUBLIC_POSTHOG_KEY;
const POSTHOG_HOST = process.env.NEXT_PUBLIC_POSTHOG_HOST;
const SENTRY_DSN = process.env.NEXT_PUBLIC_SENTRY_DSN;

// Initialize Sentry
if (typeof window !== 'undefined' && SENTRY_DSN) {
  import('@sentry/nextjs').then(({ init }) => {
    init({
      dsn: SENTRY_DSN,
      environment: process.env.NODE_ENV,
      tracesSampleRate: 0.1,
      replaysSessionSampleRate: 0.1,
      replaysOnErrorSampleRate: 1.0,
    });
  });
}

// Initialize PostHog
if (typeof window !== 'undefined' && POSTHOG_KEY) {
  import('posthog-js').then((posthog) => {
    posthog.default.init(POSTHOG_KEY, {
      api_host: POSTHOG_HOST || 'https://app.posthog.com',
      capture_pageview: false,
      persistence: 'localStorage',
    });
  });
}

class Analytics {
  /**
   * Track a page view
   */
  pageView(url: string, title?: string): void {
    // Google Analytics 4
    if (typeof window !== 'undefined' && (window as any).gtag && GA4_ID) {
      (window as any).gtag('event', 'page_view', {
        page_location: url,
        page_title: title,
      });
    }

    // Plausible
    if (PLAUSIBLE_DOMAIN && typeof document !== 'undefined') {
      // Plausible uses script-based auto-tracking
      // This is a fallback for manual event tracking
      this.track('pageview', { path: url });
    }

    // PostHog
    if (typeof window !== 'undefined' && (window as any).posthog) {
      (window as any).posthog.capture('$pageview', {
        $current_url: url,
      });
    }
  }

  /**
   * Track a custom event
   */
  track(event: string, properties?: Record<string, string | number | boolean>): void {
    const eventData: AnalyticsEvent = {
      name: event,
      properties: {
        ...properties,
        timestamp: new Date().toISOString(),
      },
    };

    // Google Analytics 4
    if (typeof window !== 'undefined' && (window as any).gtag && GA4_ID) {
      (window as any).gtag('event', event, properties);
    }

    // Plausible
    if (PLAUSIBLE_DOMAIN) {
      // Plausible event API
      fetch('https://plausible.io/api/event', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: event,
          url: window.location.href,
          domain: PLAUSIBLE_DOMAIN,
          props: properties,
        }),
      }).catch((err) => console.warn('Plausible tracking failed:', err));
    }

    // PostHog
    if (typeof window !== 'undefined' && (window as any).posthog) {
      (window as any).posthog.capture(event, properties);
    }
  }

  /**
   * Identify a user with properties
   */
  identify(userId: string, properties?: UserProperties): void {
    // Google Analytics 4
    if (typeof window !== 'undefined' && (window as any).gtag && GA4_ID) {
      (window as any).gtag('config', GA4_ID, {
        user_id: userId,
        ...properties,
      });
    }

    // PostHog
    if (typeof window !== 'undefined' && (window as any).posthog) {
      (window as any).posthog.identify(userId, properties);
    }
  }

  /**
   * Set user properties for current user
   */
  setUserProperties(properties: UserProperties): void {
    // Google Analytics 4
    if (typeof window !== 'undefined' && (window as any).gtag && GA4_ID) {
      (window as any).gtag('set', 'user_properties', properties);
    }

    // PostHog
    if (typeof window !== 'undefined' && (window as any).posthog) {
      (window as any).posthog.people.set(properties);
    }
  }

  /**
   * Track error
   */
  trackError(error: Error, context?: Record<string, any>): void {
    this.track('error', {
      error_message: error.message,
      error_stack: error.stack,
      ...context,
    });

    // Sentry will automatically capture unhandled errors
    // For manual error reporting:
    if (typeof window !== 'undefined' && (window as any).Sentry) {
      (window as any).Sentry.captureException(error, {
        extra: context,
      });
    }
  }

  /**
   * Track scan started
   */
  trackScanStarted(websiteId: string, websiteUrl: string): void {
    this.track('scan_started', {
      website_id: websiteId,
      website_url: websiteUrl,
    });
  }

  /**
   * Track scan completed
   */
  trackScanCompleted(scanId: string, score: number, issuesFound: number): void {
    this.track('scan_completed', {
      scan_id: scanId,
      score,
      issues_found: issuesFound,
      score_range: this.getScoreRange(score),
    });
  }

  /**
   * Track fix generated
   */
  trackFixGenerated(issueId: string, severity: string): void {
    this.track('fix_generated', {
      issue_id: issueId,
      severity,
    });
  }

  /**
   * Track fix applied
   */
  trackFixApplied(issueId: string, severity: string): void {
    this.track('fix_applied', {
      issue_id: issueId,
      severity,
    });
  }

  /**
   * Track subscription upgrade
   */
  trackSubscriptionUpgrade(tier: string, amount: number): void {
    this.track('subscription_upgraded', {
      tier,
      amount,
      currency: 'USD',
    });
  }

  /**
   * Track website added
   */
  trackWebsiteAdded(platform: string): void {
    this.track('website_added', {
      platform,
    });
  }

  /**
   * Get score range for analytics grouping
   */
  private getScoreRange(score: number): string {
    if (score >= 90) return 'excellent';
    if (score >= 70) return 'good';
    if (score >= 50) return 'fair';
    return 'poor';
  }
}

// Export singleton instance
export const analytics = new Analytics();

// Type definitions for window objects
declare global {
  interface Window {
    gtag?: (...args: any[]) => void;
    posthog?: any;
    plausible?: any;
    Sentry?: any;
  }
}

export default analytics;
