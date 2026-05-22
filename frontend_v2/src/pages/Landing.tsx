import { useNavigate } from "react-router-dom";
import { Users, BarChart3, Globe, Zap, ArrowRight, Star } from "lucide-react";
import { Button } from "@/components/ui/button";

const FEATURES = [
  {
    icon: Users,
    title: "24 Nigerian Personas",
    desc: "A synthetic panel covering all regions, languages, and demographics — Yoruba, Hausa, Igbo, and beyond.",
  },
  {
    icon: Globe,
    title: "4 Language Registers",
    desc: "From Standard English to Nigerian Pidgin and code-mixed responses. Real voices, not generic AI.",
  },
  {
    icon: BarChart3,
    title: "Instant Insights",
    desc: "Sentiment breakdown, top themes, and aspect priorities — delivered in under 2 minutes.",
  },
  {
    icon: Zap,
    title: "Export Ready",
    desc: "Download your panel results as PDF or CSV. Share with your team or present to stakeholders.",
  },
];

const TESTIMONIAL_STARS = [1, 2, 3, 4, 5];

export default function Landing() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-ink-950 text-ink-50">
      {/* Nav */}
      <nav className="border-b border-ink-800 px-6 py-4 flex items-center justify-between max-w-6xl mx-auto">
        <div className="flex items-center gap-2">
          <span className="w-7 h-7 rounded-md bg-naija-600 flex items-center justify-center text-white text-xs font-bold">IN</span>
          <span className="font-bold text-lg text-ink-50">InsideNaija</span>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="ghost" className="text-ink-300 hover:text-ink-50"
            onClick={() => navigate("/login")}>
            Sign in
          </Button>
          <Button className="bg-naija-600 hover:bg-naija-700 text-white"
            onClick={() => navigate("/signup")}>
            Get started
          </Button>
        </div>
      </nav>

      {/* Hero */}
      <section className="max-w-4xl mx-auto px-6 py-24 text-center space-y-8">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-naija-700/50 bg-naija-900/30 text-naija-400 text-sm">
          <span className="w-2 h-2 rounded-full bg-naija-500 animate-pulse" />
          Powered by NaijaReviewer-8B
        </div>
        <h1 className="text-5xl sm:text-6xl font-bold leading-tight text-ink-50">
          Know what Nigeria<br />
          <span className="text-naija-500">really thinks</span>
        </h1>
        <p className="text-xl text-ink-300 max-w-2xl mx-auto leading-relaxed">
          Run your product through a synthetic panel of 24 Nigerian personas —
          and get culturally-grounded feedback in minutes, not months.
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-2">
          <Button size="lg" className="bg-naija-600 hover:bg-naija-700 text-white px-8 h-12 text-base"
            onClick={() => navigate("/signup")}>
            Run your first panel free
            <ArrowRight size={18} className="ml-2" />
          </Button>
          <Button size="lg" variant="outline"
            className="border-ink-700 text-ink-200 hover:border-naija-600 h-12 text-base"
            onClick={() => navigate("/login")}>
            Sign in
          </Button>
        </div>
        <p className="text-sm text-ink-500">No credit card required · Results in under 2 minutes</p>
      </section>

      {/* Features */}
      <section className="max-w-5xl mx-auto px-6 py-16">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {FEATURES.map(({ icon: Icon, title, desc }) => (
            <div key={title} className="bg-ink-900 border border-ink-800 rounded-xl p-6 space-y-3 hover:border-naija-700/50 transition-colors">
              <div className="w-10 h-10 rounded-lg bg-naija-900/50 border border-naija-700/30 flex items-center justify-center">
                <Icon size={20} className="text-naija-400" />
              </div>
              <h3 className="font-semibold text-ink-100">{title}</h3>
              <p className="text-sm text-ink-400 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Social proof */}
      <section className="max-w-3xl mx-auto px-6 py-16 text-center space-y-6">
        <div className="flex justify-center gap-1">
          {TESTIMONIAL_STARS.map((n) => (
            <Star key={n} size={18} className="fill-amber-400 text-amber-400" />
          ))}
        </div>
        <blockquote className="text-xl text-ink-200 italic leading-relaxed">
          "NaijaReviewer-8B achieves statistical parity with Claude Sonnet in blind
          review quality evaluation — at a fraction of the cost."
        </blockquote>
        <p className="text-sm text-ink-500">Human evaluation study · 2025</p>
      </section>

      {/* CTA banner */}
      <section className="max-w-6xl mx-auto px-6 pb-24">
        <div className="bg-naija-900/30 border border-naija-700/40 rounded-2xl p-12 text-center space-y-6">
          <h2 className="text-3xl font-bold text-ink-50">
            Ready to hear from Nigeria?
          </h2>
          <p className="text-ink-300 max-w-xl mx-auto">
            Create your first project, run the panel, and get results before your next meeting.
          </p>
          <Button size="lg" className="bg-naija-600 hover:bg-naija-700 text-white px-10 h-12 text-base"
            onClick={() => navigate("/signup")}>
            Start for free
            <ArrowRight size={18} className="ml-2" />
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-ink-800 px-6 py-6 text-center text-sm text-ink-500">
        InsideNaija · Powered by NaijaReviewer-8B ·{" "}
        <button onClick={() => navigate("/login")} className="hover:text-ink-300">Sign in</button>
      </footer>
    </div>
  );
}
