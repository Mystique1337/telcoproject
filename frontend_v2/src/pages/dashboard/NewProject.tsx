import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowLeft, Loader2, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import DashboardLayout from "@/components/DashboardLayout";
import { createProject } from "@/lib/apiClient";

const CATEGORIES = [
  "FMCG",
  "Fashion & Beauty",
  "Fintech",
  "Media & Entertainment",
  "Agriculture",
  "Health & Wellness",
  "Technology",
  "Other",
];

export default function NewProject() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("FMCG");
  const [imageUrl, setImageUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim() || !description.trim()) {
      setError("Product name and description are required.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const res = await createProject({
        name: name.trim(),
        description: description.trim(),
        category,
        image_url: imageUrl.trim() || undefined,
      });
      navigate(`/runs/${res.run_id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong. Try again.");
      setLoading(false);
    }
  }

  return (
    <DashboardLayout>
      <div className="max-w-2xl mx-auto px-6 py-10 space-y-8">
        {/* Back */}
        <button
          onClick={() => navigate("/dashboard")}
          className="flex items-center gap-1.5 text-sm text-ink-400 hover:text-ink-100 transition-colors"
        >
          <ArrowLeft size={16} />
          Back to dashboard
        </button>

        {/* Header */}
        <div className="space-y-1">
          <h1 className="text-2xl font-bold">New research project</h1>
          <p className="text-sm text-ink-400">
            Describe your product and we'll run it through 24 Nigerian consumer personas.
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="bg-ink-900 border border-ink-800 rounded-xl p-6 space-y-5">
            {/* Product name */}
            <div className="space-y-2">
              <Label htmlFor="name" className="text-ink-200">
                Product name <span className="text-red-400">*</span>
              </Label>
              <Input
                id="name"
                placeholder="e.g. Indomie Chicken Suya Flavour"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="bg-ink-950 border-ink-700 text-ink-50 placeholder:text-ink-600 focus-visible:ring-naija-600"
                disabled={loading}
              />
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="description" className="text-ink-200">
                Product description <span className="text-red-400">*</span>
              </Label>
              <textarea
                id="description"
                rows={4}
                placeholder="Describe the product — what it is, who it's for, what problem it solves, key features, price point…"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                disabled={loading}
                className="w-full rounded-md border border-ink-700 bg-ink-950 px-3 py-2 text-sm text-ink-50 placeholder:text-ink-600 focus:outline-none focus:ring-2 focus:ring-naija-600 focus:border-transparent disabled:opacity-50 resize-none"
              />
              <p className="text-xs text-ink-600">
                More detail = richer feedback from personas. Include price, variants, packaging if relevant.
              </p>
            </div>

            {/* Category */}
            <div className="space-y-2">
              <Label htmlFor="category" className="text-ink-200">
                Product category
              </Label>
              <select
                id="category"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                disabled={loading}
                className="w-full rounded-md border border-ink-700 bg-ink-950 px-3 py-2 text-sm text-ink-50 focus:outline-none focus:ring-2 focus:ring-naija-600 focus:border-transparent disabled:opacity-50"
              >
                {CATEGORIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>

            {/* Image URL (optional) */}
            <div className="space-y-2">
              <Label htmlFor="image" className="text-ink-200">
                Product image URL{" "}
                <span className="text-ink-600 font-normal">(optional)</span>
              </Label>
              <Input
                id="image"
                placeholder="https://…"
                value={imageUrl}
                onChange={(e) => setImageUrl(e.target.value)}
                className="bg-ink-950 border-ink-700 text-ink-50 placeholder:text-ink-600 focus-visible:ring-naija-600"
                disabled={loading}
              />
            </div>
          </div>

          {/* Info box */}
          <div className="flex items-start gap-3 bg-naija-900/20 border border-naija-700/30 rounded-xl px-4 py-3">
            <Zap size={16} className="text-naija-400 mt-0.5 shrink-0" />
            <p className="text-xs text-ink-400 leading-relaxed">
              Your product will be evaluated by 24 culturally-grounded Nigerian personas across regions, languages,
              and demographic segments. Results arrive in under 2 minutes.
            </p>
          </div>

          {error && (
            <p className="text-sm text-red-400 bg-red-900/20 border border-red-700/30 rounded-lg px-4 py-3">
              {error}
            </p>
          )}

          <Button
            type="submit"
            disabled={loading}
            className="w-full bg-naija-600 hover:bg-naija-700 text-white h-12 text-base"
          >
            {loading ? (
              <>
                <Loader2 size={18} className="mr-2 animate-spin" />
                Launching panel…
              </>
            ) : (
              "Run panel →"
            )}
          </Button>
        </form>
      </div>
    </DashboardLayout>
  );
}
