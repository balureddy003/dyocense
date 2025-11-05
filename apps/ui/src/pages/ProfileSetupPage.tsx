import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Building2, Globe2, Layers, Target } from "lucide-react";
import { BusinessProfile, useAuth } from "../context/AuthContext";

const defaultProfile: BusinessProfile = {
  companyName: "",
  industry: "",
  teamSize: "",
  primaryGoal: "",
  timezone: "",
};

export const ProfileSetupPage = () => {
  const { profile, updateProfile, user, authenticated, ready } = useAuth();
  const navigate = useNavigate();

  const [form, setForm] = useState<BusinessProfile>(profile ?? defaultProfile);
  const [submitted, setSubmitted] = useState(false);

  useEffect(() => {
    if (!ready) return;
    if (!authenticated) {
      navigate("/login", { replace: true });
      return;
    }
    if (profile) {
      navigate("/home", { replace: true });
    }
  }, [authenticated, profile, ready, navigate]);

  useEffect(() => {
    if (profile) {
      setForm(profile);
    }
  }, [profile]);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setSubmitted(true);
    if (!form.companyName || !form.industry || !form.primaryGoal) {
      return;
    }
    await updateProfile(form);
    navigate("/home", { replace: true });
  };

  const handleChange = (field: keyof BusinessProfile) => (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    setForm((prev) => ({
      ...prev,
      [field]: event.target.value,
    }));
  };

  const errorMessage = (field: keyof BusinessProfile) => {
    if (!submitted) return "";
    if (!form[field]) {
      return "This field is required.";
    }
    return "";
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-blue-100 px-4">
      <div className="max-w-2xl w-full bg-white border border-gray-100 rounded-3xl shadow-xl p-10 space-y-8">
        <header className="space-y-2 text-center">
          <h1 className="text-2xl font-semibold text-gray-900">Welcome! Let's get to know your business</h1>
          <p className="text-sm text-gray-600">
            We'll customize your experience based on your industry and goals. You can change these details anytime in settings.
          </p>
        </header>
        <form className="space-y-6" onSubmit={handleSubmit}>
          <div className="grid gap-6 md:grid-cols-2">
            <label className="flex flex-col gap-2 text-sm text-gray-700">
              Your company or brand name
              <div className="relative">
                <Building2 size={16} className="absolute left-3 top-3 text-gray-400" />
                <input
                  className="w-full pl-9 pr-3 py-2 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10"
                  placeholder="e.g. Acme Supply Co."
                  value={form.companyName}
                  onChange={handleChange("companyName")}
                />
              </div>
              {errorMessage("companyName") && <span className="text-xs text-red-500">{errorMessage("companyName")}</span>}
            </label>
            <label className="flex flex-col gap-2 text-sm text-gray-700">
              What industry are you in?
              <div className="relative">
                <Layers size={16} className="absolute left-3 top-3 text-gray-400" />
                <select
                  className="w-full pl-9 pr-3 py-2 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10 appearance-none"
                  value={form.industry}
                  onChange={handleChange("industry")}
                >
                  <option value="">Choose your industry</option>
                  <option value="retail">Retail & eCommerce</option>
                  <option value="manufacturing">Manufacturing</option>
                  <option value="cpg">CPG & Food</option>
                  <option value="healthcare">Healthcare</option>
                  <option value="logistics">Logistics & 3PL</option>
                  <option value="other">Other</option>
                </select>
              </div>
              {errorMessage("industry") && <span className="text-xs text-red-500">{errorMessage("industry")}</span>}
            </label>
          </div>
          <label className="flex flex-col gap-2 text-sm text-gray-700">
            Which teams will use this? <span className="text-gray-500">(optional)</span>
            <input
              className="px-3 py-2 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10"
              placeholder="e.g. Sales, Inventory, Operations"
              value={form.teamSize ?? ""}
              onChange={handleChange("teamSize")}
            />
            <span className="text-xs text-gray-500">This helps us show relevant features for your team</span>
          </label>
          <label className="flex flex-col gap-2 text-sm text-gray-700">
            What's your main business challenge right now?
            <div className="relative">
              <Target size={16} className="absolute left-3 top-3 text-gray-400" />
              <textarea
                className="w-full pl-9 pr-3 py-2 min-h-[110px] rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10"
                placeholder="e.g. Reduce inventory costs, improve stock availability, better sales forecasting..."
                value={form.primaryGoal ?? ""}
                onChange={handleChange("primaryGoal")}
              />
            </div>
            {errorMessage("primaryGoal") && <span className="text-xs text-red-500">{errorMessage("primaryGoal")}</span>}
          </label>
          <label className="flex flex-col gap-2 text-sm text-gray-700">
            Your timezone <span className="text-gray-500">(optional)</span>
            <div className="relative">
              <Globe2 size={16} className="absolute left-3 top-3 text-gray-400" />
              <input
                className="w-full pl-9 pr-3 py-2 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10"
                placeholder="e.g. America/Chicago or America/New_York"
                value={form.timezone ?? ""}
                onChange={handleChange("timezone")}
              />
            </div>
            <span className="text-xs text-gray-500">We'll use this to show dates and times in your local time</span>
          </label>
          <div className="flex justify-between items-center pt-4 border-t border-gray-100">
            <div>
              <p className="font-medium text-gray-800">{user?.fullName}</p>
              <p className="text-xs text-gray-500">{user?.email}</p>
            </div>
            <button
              type="submit"
              className="px-6 py-3 rounded-full bg-primary text-white font-semibold shadow-lg hover:shadow-xl hover:bg-blue-700 transition"
            >
              Continue to Dashboard
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
