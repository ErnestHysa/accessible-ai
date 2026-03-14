'use client';

import { useEffect, useState } from 'react';
import { subscriptionApi } from '@/lib/api';
import { useAuthStore } from '@/lib/store';
import type { SubscriptionTierInfo, Subscription, Usage } from '@/types';
import { Check, ArrowRight } from 'lucide-react';
import Link from 'next/link';

export default function BillingPage() {
  const user = useAuthStore((state) => state.user);
  const [tiers, setTiers] = useState<SubscriptionTierInfo[]>([]);
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [usage, setUsage] = useState<Usage | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [tiersData, subData, usageData] = await Promise.all([
        subscriptionApi.getTiers(),
        subscriptionApi.getSubscription(),
        subscriptionApi.getUsage(),
      ]);
      setTiers(tiersData);
      setSubscription(subData);
      setUsage(usageData);
    } catch (error) {
      console.error('Failed to load billing data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCheckout = async (tierId: string) => {
    try {
      const result = await subscriptionApi.checkout(tierId);
      window.location.href = result.checkout_url;
    } catch (error) {
      console.error('Checkout failed:', error);
    }
  };

  const handlePortal = async () => {
    try {
      const result = await subscriptionApi.portal();
      window.location.href = result.portal_url;
    } catch (error) {
      console.error('Portal failed:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  const currentTier = user?.subscription_tier || 'free';

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Billing & Plans</h1>
        <p className="text-gray-600">Manage your subscription and view usage</p>
      </div>

      {/* Current Plan */}
      {subscription && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Current Plan</p>
              <p className="text-2xl font-bold text-gray-900 capitalize">{subscription.tier}</p>
              <p className="text-sm text-gray-600 capitalize">{subscription.status}</p>
            </div>
            {(subscription.tier !== 'free' && subscription.status === 'active') && (
              <button
                onClick={handlePortal}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Manage Subscription
              </button>
            )}
          </div>
        </div>
      )}

      {/* Usage */}
      {usage && (
        <div className="bg-white rounded-xl border border-gray-200 p-6">
          <h2 className="font-semibold text-gray-900 mb-4">Usage This Month</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-gray-600">Websites</p>
              <p className="text-xl font-bold text-gray-900">
                {usage.current_month.websites} / {usage.limits.websites === -1 ? '∞' : usage.limits.websites}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Scans</p>
              <p className="text-xl font-bold text-gray-900">
                {usage.current_month.scans} / {usage.limits.scans_per_month === -1 ? '∞' : usage.limits.scans_per_month}
              </p>
            </div>
          </div>
          <p className="text-xs text-gray-500 mt-4">
            Resets on {new Date(usage.reset_date).toLocaleDateString()}
          </p>
        </div>
      )}

      {/* Plans */}
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-4">Choose Your Plan</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {tiers.map((tier) => {
            const isCurrent = tier.id === currentTier;
            return (
              <div
                key={tier.id}
                className={`bg-white rounded-xl border-2 p-6 ${
                  isCurrent ? 'border-blue-500' : 'border-gray-200'
                }`}
              >
                <h3 className="font-semibold text-lg text-gray-900">{tier.name}</h3>
                <p className="text-3xl font-bold text-gray-900 mt-2">
                  ${tier.price}
                  <span className="text-base font-normal text-gray-600">/mo</span>
                </p>
                <ul className="mt-4 space-y-2 text-sm">
                  {tier.features.map((feature, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <Check className="w-4 h-4 text-green-600 flex-shrink-0 mt-0.5" />
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
                {isCurrent ? (
                  <button
                    disabled
                    className="w-full mt-6 py-2 border-2 border-blue-500 text-blue-600 rounded-lg font-medium"
                  >
                    Current Plan
                  </button>
                ) : (
                  <button
                    onClick={() => handleCheckout(tier.id)}
                    className="w-full mt-6 py-2 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 flex items-center justify-center gap-2"
                  >
                    Upgrade <ArrowRight className="w-4 h-4" />
                  </button>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
