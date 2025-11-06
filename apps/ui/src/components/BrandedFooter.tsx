import { Link } from "react-router-dom";
import { Mail, MessageCircle, FileText, Shield } from "lucide-react";

export const BrandedFooter = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-gray-50 border-t border-gray-200 mt-auto">
      <div className="max-w-7xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Brand Column */}
          <div className="space-y-3">
            <div className="flex items-center gap-2">
              <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-gradient-to-br from-blue-600 to-blue-700 text-white font-bold text-sm">
                D
              </div>
              <span className="text-lg font-bold text-gray-900">Dyocense</span>
            </div>
            <p className="text-sm text-gray-600 leading-relaxed">
              AI-powered business decisions for small businesses. Save 20-30% on costs. Boost profits by up to 20%. Get started free.
            </p>
            <div className="flex gap-3 pt-2">
              <a href="https://twitter.com/dyocense" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-blue-600 transition">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M23 3a10.9 10.9 0 01-3.14 1.53 4.48 4.48 0 00-7.86 3v1A10.66 10.66 0 013 4s-4 9 5 13a11.64 11.64 0 01-7 2c9 5 20 0 20-11.5a4.5 4.5 0 00-.08-.83A7.72 7.72 0 0023 3z"/></svg>
              </a>
              <a href="https://linkedin.com/company/dyocense" target="_blank" rel="noopener noreferrer" className="text-gray-400 hover:text-blue-600 transition">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M16 8a6 6 0 016 6v7h-4v-7a2 2 0 00-2-2 2 2 0 00-2 2v7h-4v-7a6 6 0 016-6zM2 9h4v12H2z"/><circle cx="4" cy="4" r="2"/></svg>
              </a>
            </div>
          </div>

          {/* Product Column */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Product</h3>
            <ul className="space-y-2">
              <li>
                <Link to="/marketplace" className="text-sm text-gray-600 hover:text-blue-600 transition">
                  Marketplace
                </Link>
              </li>
              <li>
                <Link to="/buy?plan=free" className="text-sm text-gray-600 hover:text-blue-600 transition">
                  Start Free
                </Link>
              </li>
              <li>
                <Link to="/buy?plan=trial" className="text-sm text-gray-600 hover:text-blue-600 transition">
                  Free Trial
                </Link>
              </li>
              <li>
                <Link to="/pricing" className="text-sm text-gray-600 hover:text-blue-600 transition">
                  Pricing
                </Link>
              </li>
              <li>
                <Link to="/features" className="text-sm text-gray-600 hover:text-blue-600 transition">
                  Features
                </Link>
              </li>
            </ul>
          </div>

          {/* Resources Column */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Resources</h3>
            <ul className="space-y-2">
              <li>
                <Link to="/blog" className="text-sm text-gray-600 hover:text-blue-600 transition">
                  Blog & Updates
                </Link>
              </li>
              <li>
                <Link to="/docs" className="text-sm text-gray-600 hover:text-blue-600 transition flex items-center gap-2">
                  <FileText size={14} />
                  Documentation
                </Link>
              </li>
              <li>
                <Link to="/help" className="text-sm text-gray-600 hover:text-blue-600 transition flex items-center gap-2">
                  <MessageCircle size={14} />
                  Help Center
                </Link>
              </li>
              <li>
                <a href="mailto:support@dyocense.com" className="text-sm text-gray-600 hover:text-blue-600 transition flex items-center gap-2">
                  <Mail size={14} />
                  Email Support
                </a>
              </li>
            </ul>
          </div>

          {/* Legal Column */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Company</h3>
            <ul className="space-y-2">
              <li>
                <Link to="/about" className="text-sm text-gray-600 hover:text-blue-600 transition">
                  About Us
                </Link>
              </li>
              <li>
                <Link to="/privacy" className="text-sm text-gray-600 hover:text-blue-600 transition flex items-center gap-2">
                  <Shield size={14} />
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link to="/terms" className="text-sm text-gray-600 hover:text-blue-600 transition">
                  Terms of Service
                </Link>
              </li>
              <li>
                <Link to="/security" className="text-sm text-gray-600 hover:text-blue-600 transition">
                  Security
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-6 border-t border-gray-200 flex flex-col sm:flex-row items-center justify-between gap-4">
          <p className="text-xs text-gray-500">
            © {currentYear} Dyocense. All rights reserved.
          </p>
          <div className="flex items-center gap-4">
            <span className="text-xs text-gray-500">Made for small businesses 🚀</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
