import { useNavigate } from "react-router-dom";
import { ArrowRight, Users, BarChart3, ShoppingBag, Cpu, FlaskConical, Github } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useAuthStore } from "@/store/auth";
import Navbar from "@/components/Navbar";

const PRODUCTS = [
  {
    href: "/products/insidenaija",
    badge: "B2B",
    badgeColor: "text-naija-400 border-naija-700/50 bg-naija-900/30",
    accentColor: "border-naija-700/40 hover:border-naija-500/50",
    icon: Users,
    iconBg: "bg-naija-900/50 border-naija-700/30",
    iconColor: "text-naija-400",
    name: "InsideNaija",
    tagline: "Synthetic Nigerian consumer research panel",
    desc: "Run any product through 24 culturally-grounded Nigerian personas and get structured, actionable feedback in under 2 minutes.",
    cta: "Explore InsideNaija",
    stat: "48.5% win rate vs. Claude Sonnet",
  },
  {
    href: "/products/shopeasy",
    badge: "B2C",
    badgeColor: "text-amber-400 border-amber-700/50 bg-amber-900/20",
    accentColor: "border-amber-700/40 hover:border-amber-500/50",
    icon: ShoppingBag,
    iconBg: "bg-amber-900/30 border-amber-700/30",
    iconColor: "text-amber-400",
    name: "ShopEasy",
    tagline: "Persona-aware Nigerian storefront",
    desc: "AI-powered product recommendations tuned to Nigerian shopping behaviour, language register, and cultural context.",
    cta: "Explore ShopEasy",
    stat: "NDCG@10 0.572 — best of 5 models",
  },
];

const WHY = [
  {
    icon: Cpu,
    title: "Built for Nigeria, not adapted",
    body: "NaijaReviewer-8B was fine-tuned on Nigerian review data. Not a generic LLM with a Nigerian system prompt — a model that actually understands the culture.",
  },
  {
    icon: BarChart3,
    title: "Research-grade results",
    body: "Blind human evaluation shows statistical parity with frontier models at 4× smaller size. Real signal, not synthetic noise.",
  },
  {
    icon: Users,
    title: "24 personas, not one prompt",
    body: "Coverage across Yoruba, Hausa, Igbo, and Pidgin speakers — with distinct cognitive dimensions, aspect priorities, and register tiers per persona.",
  },
];

export default function Landing() {
  const navigate = useNavigate();
  const session = useAuthStore((s) => s.session);

  return (
    <div className="min-h-screen bg-ink-950 text-ink-50 flex flex-col">
      <Navbar />

      {/* Hero */}
      <section className="max-w-5xl mx-auto px-6 pt-24 pb-16 text-center space-y-8">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-naija-700/50 bg-naija-900/20 text-naija-400 text-sm">
          <span className="w-2 h-2 rounded-full bg-naija-500 animate-pulse" />
          AI infrastructure for the Nigerian market
        </div>

        <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold leading-tight tracking-tight">
          AI that understands<br />
          <span className="text-naija-500">Nigerian context</span>
        </h1>

        <p className="text-xl text-ink-300 max-w-2xl mx-auto leading-relaxed">
          Two products. One mission — close the gap between generic Western AI
          and the richness of Nigerian consumer culture.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          {session ? (
            <Button size="lg" className="bg-naija-600 hover:bg-naija-700 text-white px-8 h-12 text-base"
              onClick={() => navigate("/dashboard")}>
              Go to Dashboard <ArrowRight size={18} className="ml-2" />
            </Button>
          ) : (
            <>
              <Button size="lg" className="bg-naija-600 hover:bg-naija-700 text-white px-8 h-12 text-base"
                onClick={() => navigate("/signup")}>
                Get started free <ArrowRight size={18} className="ml-2" />
              </Button>
              <Button size="lg" variant="outline"
                className="border-ink-700 text-ink-200 hover:border-naija-600 h-12 text-base"
                onClick={() => navigate("/login")}>
                Sign in
              </Button>
            </>
          )}
          <Button size="lg" variant="outline"
            className="border-purple-700/50 text-purple-300 hover:border-purple-500 hover:bg-purple-900/20 h-12 text-base"
            onClick={() => navigate("/lab")}>
            <FlaskConical size={16} className="mr-2" /> Labz
          </Button>
        </div>
      </section>

      {/* Products */}
      <section className="max-w-5xl mx-auto px-6 pb-20">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {PRODUCTS.map((p) => (
            <div
              key={p.name}
              className={`bg-ink-900 border ${p.accentColor} rounded-2xl p-8 space-y-5 cursor-pointer transition-all group`}
              onClick={() => navigate(p.href)}
            >
              <div className="flex items-start justify-between">
                <div className={`w-12 h-12 rounded-xl border ${p.iconBg} flex items-center justify-center`}>
                  <p.icon size={22} className={p.iconColor} />
                </div>
                <span className={`text-xs font-bold px-2.5 py-1 rounded-full border ${p.badgeColor}`}>
                  {p.badge}
                </span>
              </div>
              <div className="space-y-1">
                <h3 className="text-xl font-bold text-ink-50 group-hover:text-naija-300 transition-colors">
                  {p.name}
                </h3>
                <p className="text-sm font-medium text-ink-400">{p.tagline}</p>
              </div>
              <p className="text-sm text-ink-400 leading-relaxed">{p.desc}</p>
              <div className="flex items-center justify-between pt-2 border-t border-ink-800">
                <span className="text-xs text-ink-500">{p.stat}</span>
                <span className="text-sm text-naija-400 group-hover:text-naija-300 flex items-center gap-1 transition-colors">
                  {p.cta} <ArrowRight size={14} />
                </span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Why */}
      <section className="bg-ink-900/40 border-y border-ink-800 py-16">
        <div className="max-w-5xl mx-auto px-6 space-y-10">
          <h2 className="text-3xl font-bold text-center">Why Naija Persona</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
            {WHY.map(({ icon: Icon, title, body }) => (
              <div key={title} className="space-y-3">
                <div className="w-10 h-10 rounded-lg bg-naija-900/50 border border-naija-700/30 flex items-center justify-center">
                  <Icon size={20} className="text-naija-400" />
                </div>
                <h3 className="font-semibold text-ink-100">{title}</h3>
                <p className="text-sm text-ink-400 leading-relaxed">{body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Market numbers */}
      <section className="max-w-5xl mx-auto px-6 py-16 text-center space-y-10">
        <h2 className="text-3xl font-bold">The opportunity</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          {[
            { n: "218M+", label: "Nigerians", sub: "Africa's largest consumer market" },
            { n: "15%+", label: "E-commerce growth YoY", sub: "fastest growing digital market on the continent" },
            { n: "0", label: "Culturally-native AI tools", sub: "before Naija Persona" },
          ].map(({ n, label, sub }) => (
            <div key={n} className="bg-ink-900 border border-ink-800 rounded-xl p-8 space-y-2">
              <p className="text-4xl font-bold text-naija-400">{n}</p>
              <p className="text-sm font-semibold text-ink-200">{label}</p>
              <p className="text-xs text-ink-500">{sub}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-4xl mx-auto px-6 pb-24 text-center space-y-6">
        <div className="bg-naija-900/20 border border-naija-700/30 rounded-2xl p-12 space-y-5">
          <h2 className="text-3xl font-bold">Start building for Nigeria today</h2>
          <p className="text-ink-400 max-w-md mx-auto">
            Free to try. No credit card. Results in under 2 minutes.
          </p>
          <Button size="lg" className="bg-naija-600 hover:bg-naija-700 text-white px-10 h-12 text-base"
            onClick={() => navigate(session ? "/dashboard" : "/signup")}>
            {session ? "Go to Dashboard" : "Get started free"} <ArrowRight size={18} className="ml-2" />
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-ink-800 px-6 py-5 flex items-center justify-between text-sm text-ink-600">
        <span className="font-semibold text-ink-400">Naija Persona</span>
        <div className="flex gap-6">
          <button onClick={() => navigate("/products/insidenaija")} className="hover:text-ink-300">InsideNaija</button>
          <button onClick={() => navigate("/products/shopeasy")} className="hover:text-ink-300">ShopEasy</button>
          <button onClick={() => navigate("/login")} className="hover:text-ink-300">Sign in</button>
          <button onClick={() => navigate("/lab")} className="hover:text-purple-400 text-purple-500">Labz ⚗️</button>
          <a
            href="https://github.com/Mystique1337/telcoproject"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 hover:text-ink-300 transition-colors"
          >
            <Github size={15} /> GitHub
          </a>
        </div>
      </footer>
    </div>
  );
}
