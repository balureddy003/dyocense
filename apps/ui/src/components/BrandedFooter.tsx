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
              AI-powered decision intelligence for small businesses. Make smarter decisions faster.
            </p>
          </div>

          {/* Product Column */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Product</h3>
            <ul className="space-y-2">
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

          {/* Support Column */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Support</h3>
            <ul className="space-y-2">
              <li>
                <a href="mailto:support@dyocense.com" className="text-sm text-gray-600 hover:text-blue-600 transition flex items-center gap-2">
                  <Mail size={14} />
                  Email Support
                </a>
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
            </ul>
          </div>

          {/* Legal Column */}
          <div>
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Legal</h3>
            <ul className="space-y-2">
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
