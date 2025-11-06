import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { BookOpen, Users, Sparkles, Calendar, Clock, ArrowLeft, Search } from "lucide-react";
import { BrandedHeader } from "../components/BrandedHeader";
import { BrandedFooter } from "../components/BrandedFooter";

type BlogPost = {
  id: string;
  type: "Customer Story" | "Feature Update" | "Guide" | "Best Practice";
  title: string;
  excerpt: string;
  content?: string;
  date: string;
  readTime: string;
  author: string;
  authorRole: string;
  image: "customer-story" | "product-update" | "guide";
  tag: string;
  featured?: boolean;
};

const BLOG_POSTS: BlogPost[] = [
  {
    id: "urban-threads-success",
    type: "Customer Story",
    title: "How Urban Threads Reduced Overstock by 35% in 30 Days",
    excerpt: "Sarah Chen shares how Dyocense transformed her boutique's inventory management and saved thousands in holding costs.",
    content: `When Sarah Chen opened Urban Threads boutique in downtown Seattle, she knew fashion retail would be challenging. What she didn't expect was how much money she'd lose to overstock and markdowns.

"I was ordering based on gut feeling and last year's sales," Sarah explains. "Some items would sell out immediately, while others would sit on shelves for months. The carrying costs were killing my margins."

After implementing Dyocense's smart inventory recommendations, the results were dramatic:

• 35% reduction in overstock within 30 days
• 50% fewer stockouts of popular items
• $18,000 saved in holding costs in the first quarter
• 22% improvement in inventory turnover

"Dyocense doesn't just tell me what to order—it shows me why. I can see the predictions, understand the seasonal patterns, and trust the recommendations because they're backed by proven math, not just AI guesses."

The system integrates with Urban Threads' POS system, analyzing historical sales data, seasonal trends, and even local events to predict demand accurately.

"Now I spend my time on what I love—curating great fashion—instead of stressing about inventory. That's priceless."`,
    date: "November 1, 2025",
    readTime: "5 min read",
    author: "Sarah Chen",
    authorRole: "Owner, Urban Threads Boutique",
    image: "customer-story",
    tag: "Success Story",
    featured: true,
  },
  {
    id: "multi-location-update",
    type: "Feature Update",
    title: "New: Multi-Location Support & Advanced Forecasting",
    excerpt: "Manage multiple stores from one dashboard with our latest release. Plus, improved demand forecasting with weather data integration.",
    content: `We're excited to announce our biggest product update yet! Dyocense now supports multi-location management, making it easier than ever for growing businesses to optimize across all their locations.

**What's New:**

**Multi-Location Dashboard**
• Manage inventory, staffing, and operations across unlimited locations
• Compare performance metrics side-by-side
• Transfer inventory between locations with optimization recommendations
• Location-specific demand forecasting

**Advanced Forecasting Engine**
• Weather data integration for weather-sensitive businesses
• Local events and holidays automatically factored in
• Improved accuracy for seasonal patterns (10-15% better predictions)
• Support for new product launches with limited historical data

**Bulk Operations**
• Apply decisions across multiple locations simultaneously
• Batch import/export for faster data management
• Template-based planning for consistent operations

**Enhanced Reporting**
• New executive dashboard with key metrics across all locations
• Customizable alerts for inventory levels, staffing issues, and more
• Export to Excel, PDF, or integrate with your BI tools

These features are available now for Professional and Enterprise customers. Free tier users can try multi-location support with up to 2 locations.`,
    date: "October 28, 2025",
    readTime: "3 min read",
    author: "Product Team",
    authorRole: "Dyocense",
    image: "product-update",
    tag: "Product News",
    featured: true,
  },
  {
    id: "riverside-cafe-success",
    type: "Customer Story",
    title: "Riverside Cafe Cuts Labor Costs by 22% with Smart Scheduling",
    excerpt: "Learn how Marcus Johnson optimized his cafe's staffing and improved employee satisfaction at the same time.",
    content: `Marcus Johnson runs Riverside Cafe, a popular breakfast and lunch spot in Portland. With fluctuating customer traffic throughout the day and week, scheduling was his biggest headache.

"I was either overstaffed during slow periods or scrambling to find coverage during rushes," Marcus recalls. "Overtime was eating into profits, and my team was frustrated with inconsistent schedules."

After implementing Dyocense's workforce optimization:

• 22% reduction in labor costs
• 40% decrease in overtime expenses  
• 85% improvement in schedule consistency
• Higher employee satisfaction scores

"The AI learned our traffic patterns—morning rush, lunch peak, slow afternoons. It factors in employee availability, skills, and even preferences. Now everyone gets their schedules two weeks in advance, and we're always properly staffed."

The system also helped during unexpected situations:

"When a major road closure diverted traffic away from us for a week, Dyocense adjusted staffing recommendations immediately. We didn't waste money on unnecessary labor during that slow period."

Marcus's favorite feature? "The what-if scenarios. I can test different staffing levels and see the impact on costs and service quality before making changes. It's like having a business consultant available 24/7."`,
    date: "October 20, 2025",
    readTime: "6 min read",
    author: "Marcus Johnson",
    authorRole: "Manager, Riverside Cafe",
    image: "customer-story",
    tag: "Success Story",
    featured: false,
  },
  {
    id: "ai-decision-support-guide",
    type: "Guide",
    title: "5 Signs Your Business Needs AI Decision Support",
    excerpt: "Are you still making critical business decisions based on gut feeling? Here's how to know when it's time for an upgrade.",
    content: `Small business owners wear many hats, but when it comes to critical decisions about inventory, staffing, and operations, gut feeling isn't enough. Here are five signs it's time to upgrade to AI-powered decision support:

**1. You're Constantly Putting Out Fires**
If you're always reacting to stockouts, overstaffing, or emergency situations, you need better forecasting. AI can predict these issues before they happen.

**2. You Can't Explain Why You Made a Decision**
"It felt right" isn't a business strategy. If you can't articulate why you ordered specific quantities or scheduled certain shifts, you need data-driven insights.

**3. You're Losing Money on Avoidable Mistakes**
Overstock markdowns, wasted labor hours, missed opportunities—these add up fast. AI optimization typically saves 15-30% on operational costs.

**4. You Spend Hours in Spreadsheets**
If you're manually analyzing data, creating schedules, or forecasting demand, you're wasting valuable time. AI can do this in seconds, not hours.

**5. Your Business is Growing and Complexity is Increasing**
What worked when you had one location or 5 employees falls apart at scale. AI scales with you, handling complexity that humans simply can't manage efficiently.

**Ready to Upgrade?**
Modern AI decision support tools like Dyocense are affordable, easy to use, and designed specifically for small businesses. No data scientists required—just smart technology that helps you make better decisions every day.`,
    date: "October 15, 2025",
    readTime: "4 min read",
    author: "Dyocense Team",
    authorRole: "Product Education",
    image: "guide",
    tag: "Best Practices",
    featured: false,
  },
  {
    id: "techfix-repairs-story",
    type: "Customer Story",
    title: "TechFix Repairs Boosts Profit Margins by 18% with Dynamic Pricing",
    excerpt: "Priya Patel explains how Dyocense helped optimize pricing strategy and parts inventory for her electronics repair business.",
    content: `Priya Patel's electronics repair business, TechFix Repairs, was profitable but Priya knew she was leaving money on the table.

"Pricing was based on competitors and gut feeling. Parts inventory was a mess—too much of some things, not enough of others. I needed a smarter approach."

After implementing Dyocense:

• 18% increase in profit margins
• 45% reduction in parts stockouts
• 30% improvement in parts inventory turnover
• Better pricing strategy that customers actually preferred

"The pricing optimization surprised me. Dyocense showed me where I was underpricing premium repairs and overpricing common fixes. The recommendations balanced profitability with customer retention perfectly."

The parts inventory optimization was equally transformative:

"Now I know exactly which iPhone screens, battery models, and components to stock. The system predicts what repairs are coming based on device lifecycles and local trends. We rarely run out of critical parts anymore."

Priya's advice to other service business owners?

"Don't guess. The data is there—you just need the right tools to make sense of it. Dyocense paid for itself in the first month."`,
    date: "October 10, 2025",
    readTime: "5 min read",
    author: "Priya Patel",
    authorRole: "CEO, TechFix Repairs",
    image: "customer-story",
    tag: "Success Story",
    featured: false,
  },
  {
    id: "api-integrations-update",
    type: "Feature Update",
    title: "New Connections: Shopify, Square, and QuickBooks",
    excerpt: "Connect your existing tools seamlessly. We've added easy connections to the most popular small business platforms.",
    content: `Great news for our users! We've just launched easy connections with three of the most popular small business platforms: Shopify, Square, and QuickBooks.

**Shopify Integration**
• Automatic inventory sync across online and physical stores
• Sales data flows directly into Dyocense for smart predictions
• Push recommended reorder quantities back to Shopify
• Multi-location support for Shopify stores

**Square Integration**
• Real-time POS data for accurate predictions
• Employee schedule sync with Square Shifts
• Payment data for cash flow planning
• Customer traffic patterns for staffing decisions

**QuickBooks Integration**
• Expense data for cost-aware recommendations
• Vendor management and payment terms
• Financial reporting with operational metrics
• Budget limits automatically respected

**How to Get Started**
All integrations are available in your Dyocense dashboard under Settings > Integrations. Setup takes less than 5 minutes with our step-by-step guides.

**Coming Soon**
We're also working on integrations for Clover, Toast, and Xero. Let us know what platforms you'd like to see next!

These integrations are available on all paid plans. Free tier users can try one integration for free.`,
    date: "September 28, 2025",
    readTime: "3 min read",
    author: "Engineering Team",
    authorRole: "Dyocense",
    image: "product-update",
    tag: "Product News",
    featured: false,
  },
];

export const BlogPage = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("All");

  const categories = ["All", "Success Story", "Product News", "Best Practices", "Guides"];

  const filteredPosts = BLOG_POSTS.filter(post => {
    const matchesSearch = post.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         post.excerpt.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === "All" || post.tag === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const featuredPosts = BLOG_POSTS.filter(post => post.featured);
  const recentPosts = BLOG_POSTS.slice(0, 3);

  const getIcon = (image: string) => {
    switch (image) {
      case "customer-story":
        return Users;
      case "product-update":
        return Sparkles;
      default:
        return BookOpen;
    }
  };

  const getGradient = (image: string) => {
    switch (image) {
      case "customer-story":
        return "from-green-400 to-green-600";
      case "product-update":
        return "from-blue-400 to-blue-600";
      default:
        return "from-purple-400 to-purple-600";
    }
  };

  const getTagColor = (tag: string) => {
    switch (tag) {
      case "Success Story":
        return "bg-green-50 text-green-700";
      case "Product News":
        return "bg-blue-50 text-blue-700";
      default:
        return "bg-purple-50 text-purple-700";
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-white via-blue-50/40 to-blue-100/30">
      <BrandedHeader showNav={false} />

      <main className="flex-1 px-6 py-12">
        {/* Hero Section */}
        <section className="max-w-6xl mx-auto mb-16">
          <button
            onClick={() => navigate("/")}
            className="inline-flex items-center gap-2 text-sm text-gray-600 hover:text-primary transition mb-6"
          >
            <ArrowLeft size={16} />
            Back to Home
          </button>

          <div className="text-center mb-8">
            <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
              Blog & Updates
            </h1>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Customer success stories, product updates, and best practices for running a smarter business.
            </p>
          </div>

          {/* Search & Filter */}
          <div className="max-w-3xl mx-auto mb-8">
            <div className="relative mb-6">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="text"
                placeholder="Search articles..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-12 pr-4 py-3 rounded-full border-2 border-gray-200 focus:border-primary focus:outline-none transition"
              />
            </div>

            <div className="flex flex-wrap justify-center gap-2">
              {categories.map((category) => (
                <button
                  key={category}
                  onClick={() => setSelectedCategory(category)}
                  className={`px-4 py-2 rounded-full text-sm font-semibold transition ${
                    selectedCategory === category
                      ? "bg-primary text-white"
                      : "bg-white text-gray-700 hover:bg-gray-50 border border-gray-200"
                  }`}
                >
                  {category}
                </button>
              ))}
            </div>
          </div>
        </section>

        {/* Featured Posts */}
        {selectedCategory === "All" && !searchQuery && (
          <section className="max-w-6xl mx-auto mb-16">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Featured</h2>
            <div className="grid gap-6 md:grid-cols-2">
              {featuredPosts.map((post) => {
                const Icon = getIcon(post.image);
                return (
                  <article
                    key={post.id}
                    className="bg-white rounded-2xl border border-gray-200 overflow-hidden shadow-sm hover:shadow-lg transition group cursor-pointer"
                    onClick={() => navigate(`/blog/${post.id}`)}
                  >
                    <div className={`h-48 bg-gradient-to-br ${getGradient(post.image)} flex items-center justify-center`}>
                      <Icon size={64} className="text-white opacity-90" />
                    </div>
                    <div className="p-6">
                      <div className="flex items-center gap-2 mb-3">
                        <span className={`text-xs font-semibold px-3 py-1 rounded-full ${getTagColor(post.tag)}`}>
                          {post.tag}
                        </span>
                      </div>
                      <h3 className="text-xl font-bold text-gray-900 mb-3 group-hover:text-primary transition">
                        {post.title}
                      </h3>
                      <p className="text-sm text-gray-600 mb-4 leading-relaxed">
                        {post.excerpt}
                      </p>
                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <div className="flex items-center gap-4">
                          <span className="flex items-center gap-1">
                            <Calendar size={14} />
                            {post.date}
                          </span>
                          <span className="flex items-center gap-1">
                            <Clock size={14} />
                            {post.readTime}
                          </span>
                        </div>
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          </section>
        )}

        {/* All Posts Grid */}
        <section className="max-w-6xl mx-auto">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">
            {searchQuery ? "Search Results" : selectedCategory === "All" ? "All Posts" : selectedCategory}
          </h2>
          
          {filteredPosts.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500">No articles found matching your criteria.</p>
            </div>
          ) : (
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
              {filteredPosts.map((post) => {
                const Icon = getIcon(post.image);
                return (
                  <article
                    key={post.id}
                    className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm hover:shadow-md transition group cursor-pointer"
                    onClick={() => navigate(`/blog/${post.id}`)}
                  >
                    <div className={`h-40 bg-gradient-to-br ${getGradient(post.image)} flex items-center justify-center`}>
                      <Icon size={48} className="text-white opacity-90" />
                    </div>
                    <div className="p-5">
                      <div className="flex items-center gap-2 mb-3">
                        <span className={`text-xs font-semibold px-2 py-1 rounded-full ${getTagColor(post.tag)}`}>
                          {post.tag}
                        </span>
                      </div>
                      <h3 className="text-base font-semibold text-gray-900 mb-2 line-clamp-2 group-hover:text-primary transition">
                        {post.title}
                      </h3>
                      <p className="text-sm text-gray-600 mb-4 line-clamp-3 leading-relaxed">
                        {post.excerpt}
                      </p>
                      <div className="flex items-center justify-between text-xs text-gray-500">
                        <span>{post.date}</span>
                        <span>{post.readTime}</span>
                      </div>
                    </div>
                  </article>
                );
              })}
            </div>
          )}
        </section>

        {/* Newsletter Signup */}
        <section className="max-w-4xl mx-auto mt-16 mb-8">
          <div className="bg-gradient-to-br from-blue-600 to-blue-700 rounded-3xl p-8 md:p-12 text-center text-white">
            <h2 className="text-2xl md:text-3xl font-bold mb-4">
              Stay Updated
            </h2>
            <p className="text-blue-100 mb-6 max-w-2xl mx-auto">
              Get the latest customer stories, product updates, and business tips delivered to your inbox monthly.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto">
              <input
                type="email"
                placeholder="Your email address"
                className="flex-1 px-4 py-3 rounded-full text-gray-900 focus:outline-none focus:ring-2 focus:ring-white"
              />
              <button className="px-6 py-3 rounded-full bg-white text-primary font-semibold hover:shadow-lg transition">
                Subscribe
              </button>
            </div>
            <p className="text-xs text-blue-200 mt-4">
              No spam, ever. Unsubscribe anytime.
            </p>
          </div>
        </section>
      </main>

      <BrandedFooter />
    </div>
  );
};
