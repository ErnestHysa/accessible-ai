import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-xl">A</span>
            </div>
            <span className="font-bold text-xl">AccessibleAI</span>
          </div>
          <nav className="flex items-center gap-6">
            <a href="#features" className="text-sm font-medium hover:text-blue-600 transition">
              Features
            </a>
            <a href="#pricing" className="text-sm font-medium hover:text-blue-600 transition">
              Pricing
            </a>
            <Link
              href="/login"
              className="text-sm font-medium hover:text-blue-600 transition"
            >
              Sign In
            </Link>
            <Link
              href="/signup"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition"
            >
              Get Started Free
            </Link>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="py-20 bg-gradient-to-b from-blue-50 to-white">
        <div className="container mx-auto px-4 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium mb-6">
            <span>🎯</span>
            <span>WCAG 2.1 Compliance Made Easy</span>
          </div>
          <h1 className="text-5xl font-bold mb-6 text-balance">
            Make Your Website Accessible,
            <br />
            <span className="text-blue-600">Avoid Lawsuits</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            98% of websites fail ADA compliance. Get automated accessibility scans,
            AI-powered fixes, and protect your business from legal risks.
          </p>
          <div className="flex items-center justify-center gap-4">
            <Link
              href="/signup"
              className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition"
            >
              Start Free Scan
            </Link>
            <a
              href="#features"
              className="px-6 py-3 border border-gray-300 rounded-lg font-medium hover:bg-gray-50 transition"
            >
              Learn More
            </a>
          </div>
          <p className="text-sm text-gray-500 mt-4">No credit card required • 1 website free</p>
        </div>
      </section>

      {/* Stats */}
      <section className="py-12 border-b">
        <div className="container mx-auto px-4">
          <div className="grid grid-cols-4 gap-8 text-center">
            <div>
              <div className="text-3xl font-bold text-blue-600">98%</div>
              <div className="text-sm text-gray-600">of websites fail WCAG</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-blue-600">$50K+</div>
              <div className="text-sm text-gray-600">average ADA lawsuit cost</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-blue-600">200+</div>
              <div className="text-sm text-gray-600">WCAG 2.1 rules checked</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-blue-600">AI</div>
              <div className="text-sm text-gray-600">powered fix suggestions</div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section id="features" className="py-20">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">
            Everything You Need for Accessibility Compliance
          </h2>
          <div className="grid grid-cols-3 gap-8">
            <div className="p-6 rounded-xl border bg-white">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                🔍
              </div>
              <h3 className="font-semibold text-lg mb-2">Automated Scanning</h3>
              <p className="text-gray-600">
                Comprehensive WCAG 2.1 compliance checks with detailed reports.
                Scan your entire site in minutes.
              </p>
            </div>
            <div className="p-6 rounded-xl border bg-white">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                🤖
              </div>
              <h3 className="font-semibold text-lg mb-2">AI-Powered Fixes</h3>
              <p className="text-gray-600">
                Get specific code fixes generated by AI. No more guessing what
                needs to change.
              </p>
            </div>
            <div className="p-6 rounded-xl border bg-white">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                🔧
              </div>
              <h3 className="font-semibold text-lg mb-2">WordPress Plugin</h3>
              <p className="text-gray-600">
                One-click fixes for WordPress sites. No coding required for
                common issues.
              </p>
            </div>
            <div className="p-6 rounded-xl border bg-white">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                📊
              </div>
              <h3 className="font-semibold text-lg mb-2">Detailed Reports</h3>
              <p className="text-gray-600">
                Export accessibility reports for stakeholders, auditors, or
                legal documentation.
              </p>
            </div>
            <div className="p-6 rounded-xl border bg-white">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                ⚡
              </div>
              <h3 className="font-semibold text-lg mb-2">Real-Time Monitoring</h3>
              <p className="text-gray-600">
                Continuous monitoring with alerts when new accessibility issues
                are introduced.
              </p>
            </div>
            <div className="p-6 rounded-xl border bg-white">
              <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                💰
              </div>
              <h3 className="font-semibold text-lg mb-2">Affordable Pricing</h3>
              <p className="text-gray-600">
                Enterprise-level features at small business prices. Start free,
                scale as you grow.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing */}
      <section id="pricing" className="py-20 bg-gray-50">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-4">Simple, Transparent Pricing</h2>
          <p className="text-gray-600 text-center mb-12">Choose the plan that fits your needs</p>

          <div className="grid grid-cols-4 gap-6 max-w-6xl mx-auto">
            {/* Free */}
            <div className="p-6 rounded-xl border bg-white">
              <h3 className="font-semibold text-lg mb-2">Free</h3>
              <div className="text-3xl font-bold mb-4">$0</div>
              <ul className="space-y-2 text-sm mb-6">
                <li>✓ 1 website</li>
                <li>✓ 5 scans per month</li>
                <li>✓ Basic reports</li>
                <li>✓ Community support</li>
              </ul>
              <Link
                href="/signup"
                className="block w-full py-2 text-center border border-blue-600 text-blue-600 rounded-lg font-medium hover:bg-blue-50 transition"
              >
                Get Started
              </Link>
            </div>

            {/* Starter */}
            <div className="p-6 rounded-xl border-2 border-blue-600 bg-white relative">
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-blue-600 text-white text-xs font-medium rounded-full">
                Popular
              </div>
              <h3 className="font-semibold text-lg mb-2">Starter</h3>
              <div className="text-3xl font-bold mb-4">$49<span className="text-sm font-normal">/mo</span></div>
              <ul className="space-y-2 text-sm mb-6">
                <li>✓ 3 websites</li>
                <li>✓ Unlimited scans</li>
                <li>✓ WordPress plugin</li>
                <li>✓ AI fix suggestions</li>
                <li>✓ Email support</li>
              </ul>
              <Link
                href="/signup?tier=starter"
                className="block w-full py-2 text-center bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition"
              >
                Start Trial
              </Link>
            </div>

            {/* Pro */}
            <div className="p-6 rounded-xl border bg-white">
              <h3 className="font-semibold text-lg mb-2">Pro</h3>
              <div className="text-3xl font-bold mb-4">$99<span className="text-sm font-normal">/mo</span></div>
              <ul className="space-y-2 text-sm mb-6">
                <li>✓ 10 websites</li>
                <li>✓ Unlimited scans</li>
                <li>✓ All CMS integrations</li>
                <li>✓ Priority support</li>
                <li>✓ API access</li>
              </ul>
              <Link
                href="/signup?tier=pro"
                className="block w-full py-2 text-center border border-blue-600 text-blue-600 rounded-lg font-medium hover:bg-blue-50 transition"
              >
                Start Trial
              </Link>
            </div>

            {/* Agency */}
            <div className="p-6 rounded-xl border bg-white">
              <h3 className="font-semibold text-lg mb-2">Agency</h3>
              <div className="text-3xl font-bold mb-4">$249<span className="text-sm font-normal">/mo</span></div>
              <ul className="space-y-2 text-sm mb-6">
                <li>✓ Unlimited websites</li>
                <li>✓ White-label reports</li>
                <li>✓ Custom integrations</li>
                <li>✓ Dedicated support</li>
                <li>✓ SLA guarantee</li>
              </ul>
              <Link
                href="/signup?tier=agency"
                className="block w-full py-2 text-center border border-blue-600 text-blue-600 rounded-lg font-medium hover:bg-blue-50 transition"
              >
                Contact Sales
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 border-t bg-gray-50">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-xl">A</span>
              </div>
              <span className="font-bold">AccessibleAI</span>
            </div>
            <div className="text-sm text-gray-600">
              © 2026 AccessibleAI. Making the web accessible for everyone.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
