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
          <h1 className="text-2xl font-semibold text-gray-900">Tell us about your organization</h1>
          <p className="text-sm text-gray-600">
            We tailor data foundations and AI playbooks based on your operating model. You can update these details
            anytime from settings.
          </p>
        </header>
        <form className="space-y-6" onSubmit={handleSubmit}>
          <div className="grid gap-6 md:grid-cols-2">
            <label className="flex flex-col gap-2 text-sm text-gray-700">
              Company or brand
              <div className="relative">
                <Building2 size={16} className="absolute left-3 top-3 text-gray-400" />
                <input
                  className="w-full pl-9 pr-3 py-2 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10"
                  placeholder="Acme Supply Co."
                  value={form.companyName}
                  onChange={handleChange("companyName")}
                />
              </div>
              {errorMessage("companyName") && <span className="text-xs text-red-500">{errorMessage("companyName")}</span>}
            </label>
            <label className="flex flex-col gap-2 text-sm text-gray-700">
              Industry
              <div className="relative">
                <Layers size={16} className="absolute left-3 top-3 text-gray-400" />
                <select
                  className="w-full pl-9 pr-3 py-2 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10 appearance-none"
                  value={form.industry}
                  onChange={handleChange("industry")}
                >
                  <option value="">Select industry</option>
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
            Teams using Dyocense
            <input
              className="px-3 py-2 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10"
              placeholder="Supply Planning, Merchandising, Finance Ops"
              value={form.teamSize ?? ""}
              onChange={handleChange("teamSize")}
            />
          </label>
          <label className="flex flex-col gap-2 text-sm text-gray-700">
            Primary business goal
            <div className="relative">
              <Target size={16} className="absolute left-3 top-3 text-gray-400" />
              <textarea
                className="w-full pl-9 pr-3 py-2 min-h-[110px] rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10"
                placeholder="Where do you want Dyocense copilots to focus first?"
                value={form.primaryGoal ?? ""}
                onChange={handleChange("primaryGoal")}
              />
            </div>
            {errorMessage("primaryGoal") && <span className="text-xs text-red-500">{errorMessage("primaryGoal")}</span>}
          </label>
          <label className="flex flex-col gap-2 text-sm text-gray-700">
            Preferred timezone
            <div className="relative">
              <Globe2 size={16} className="absolute left-3 top-3 text-gray-400" />
              <input
                className="w-full pl-9 pr-3 py-2 rounded-lg border border-gray-200 focus:border-primary focus:ring-2 focus:ring-primary/10"
                placeholder="e.g. America/Chicago"
                value={form.timezone ?? ""}
                onChange={handleChange("timezone")}
              />
            </div>
          </label>
          <div className="flex justify-between items-center text-sm text-gray-600">
            <div>
              <p className="font-medium text-gray-800">{user?.fullName}</p>
              <p className="text-xs text-gray-500">{user?.email}</p>
            </div>
            <button
              type="submit"
              className="px-5 py-2.5 rounded-full bg-primary text-white font-semibold shadow-lg hover:shadow-xl transition"
            >
              Save & continue
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
