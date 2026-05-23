import { useState, useRef } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowRight, Users, Globe, BarChart3, Zap,
  TrendingUp, DollarSign, Clock, ShieldCheck, Package, Share2, Check,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import Navbar from "@/components/Navbar";
import InsideNaija from "@/InsideNaija";

const STATS = [
  { value: "48.5%", label: "Win rate vs Claude Sonnet", sub: "blind human evaluation" },
  { value: "24", label: "Nigerian personas", sub: "across regions, languages, demographics" },
  { value: "<2 min", label: "Time to results", sub: "vs. weeks for traditional research" },
  { value: "4×", label: "Smaller than frontier models", sub: "same quality, fraction of cost" },
];


const BUSINESS_VALUE = [
  {
    icon: DollarSign,
    title: "1/100th the cost of focus groups",
    body: "A traditional Nigerian consumer focus group costs ₦500k–₦2M and takes 3–6 weeks to recruit. InsideNaija delivers richer, structured feedback in minutes.",
  },
  {
    icon: Clock,
    title: "Move at the speed of product",
    body: "Test a new SKU, pricing variant, or campaign message before committing budget. Iterate in hours, not months.",
  },
  {
    icon: Globe,
    title: "Culturally grounded, not Westernised",
    body: "Generic LLMs carry implicit Western bias. NaijaReviewer-8B was fine-tuned on Nigerian review data — it knows what 'okay nah' actually means.",
  },
  {
    icon: ShieldCheck,
    title: "Reduce failed launches",
    body: "Products that miss Nigerian cultural context fail publicly and expensively. Catch positioning issues before they reach market.",
  },
];

const USE_CASES = [
  { sector: "FMCG", example: "Test a new Indomie variant across Hausa, Yoruba, and Igbo personas before national rollout." },
  { sector: "Fashion & Beauty", example: "Validate shade range positioning for a new cosmetics line across skin tone and demographic segments." },
  { sector: "Fintech", example: "Check if your onboarding copy lands in Pidgin vs. Standard English for different user tiers." },
  { sector: "Media & Entertainment", example: "Pressure-test a campaign tagline for cultural resonance before spending on media." },
  { sector: "Agencies", example: "Run rapid consumer validation for your clients without fielding a panel or survey." },
  { sector: "Market Research", example: "Augment traditional fieldwork with synthetic pre-screening to focus qual spend on what matters." },
];

export default function InsideNaijaPage() {
  const navigate = useNavigate();
  const [showDemo, setShowDemo] = useState(false);
  const demoRef = useRef<HTMLElement>(null);

  function toggleDemo() {
    const next = !showDemo;
    setShowDemo(next);
    if (next) {
      // Small delay so the DOM renders the section before scrolling
      setTimeout(() => {
        demoRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      }, 60);
    }
  }

  return (
    <div className="min-h-screen bg-ink-950 text-ink-50">
      <Navbar />

      {/* Live demo — sits above the hero, hidden until "See it live" is clicked */}
      {showDemo && (
        <section ref={demoRef} className="max-w-6xl mx-auto px-6 pt-6 pb-2">
          <div className="border border-naija-700/40 rounded-2xl overflow-hidden">
            <div className="bg-ink-900 border-b border-ink-800 px-6 py-3 flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-red-500/60" />
              <span className="w-3 h-3 rounded-full bg-amber-500/60" />
              <span className="w-3 h-3 rounded-full bg-naija-500/60" />
              <span className="ml-3 text-xs text-ink-500">InsideNaija — live demo</span>
              <button
                onClick={toggleDemo}
                className="ml-auto text-xs text-ink-500 hover:text-ink-200 transition-colors"
              >
                Hide ×
              </button>
            </div>
            <InsideNaija />
          </div>
        </section>
      )}

      {/* Hero */}
      <section className="max-w-5xl mx-auto px-6 pt-20 pb-16 text-center space-y-8">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-naija-700/50 bg-naija-900/30 text-naija-400 text-sm">
          <span className="w-2 h-2 rounded-full bg-naija-500 animate-pulse" />
          B2B · Consumer Research
        </div>

        <h1 className="text-5xl sm:text-6xl font-bold leading-tight">
          Know what Nigeria<br />
          <span className="text-naija-500">really thinks</span>
        </h1>

        <p className="text-xl text-ink-300 max-w-2xl mx-auto leading-relaxed">
          A synthetic panel of 24 Nigerian personas — built on a fine-tuned 8B model —
          gives you structured, culturally-grounded feedback on any product in under 2 minutes.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Button size="lg" className="bg-naija-600 hover:bg-naija-700 text-white px-8 h-12 text-base"
            onClick={() => navigate("/signup")}>
            Start for free <ArrowRight size={18} className="ml-2" />
          </Button>
          <Button size="lg" variant="outline"
            className="border-ink-700 text-ink-200 hover:border-naija-600 h-12 text-base"
            onClick={toggleDemo}>
            {showDemo ? "Hide demo" : "See it live"}
          </Button>
        </div>
      </section>

      {/* Stats */}
      <section className="max-w-5xl mx-auto px-6 pb-16">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {STATS.map((s) => (
            <div key={s.value} className="bg-ink-900 border border-ink-800 rounded-xl p-6 text-center space-y-1">
              <p className="text-3xl font-bold text-naija-400">{s.value}</p>
              <p className="text-sm font-medium text-ink-100">{s.label}</p>
              <p className="text-xs text-ink-500">{s.sub}</p>
            </div>
          ))}
        </div>
      </section>

      {/* From product to verdict */}
      <section className="max-w-5xl mx-auto px-6 py-16">
        <div className="text-center max-w-2xl mx-auto mb-12 space-y-3">
          <h2 className="text-3xl font-bold text-ink-50 tracking-tight">From product to verdict in 90 seconds</h2>
          <p className="text-ink-400">A traditional Nigerian panel study costs ₦5M and takes 6 weeks. InsideNaija simulates one instantly so you can kill bad ideas before they cost you.</p>
        </div>
        <div className="grid sm:grid-cols-2 md:grid-cols-4 gap-6">
          {[
            { n: 1, icon: Package,   t: "Describe your product", d: "Title, price, a line of detail. Takes 20 seconds." },
            { n: 2, icon: Users,     t: "The panel reacts",       d: "24 Nigerian personas across 6 zones rate it and write a real review in their own register." },
            { n: 3, icon: BarChart3, t: "Read the verdict",       d: "Predicted rating, buy-likelihood, who's warm/cold, and the recurring praise & concerns." },
            { n: 4, icon: Share2,    t: "Export & share",         d: "CSV export or shareable link. Ready for your deck, your client, or your team." },
          ].map(({ n, icon: Icon, t, d }) => (
            <div key={n} className="bg-ink-900/40 border border-ink-800 rounded-2xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <div className="w-10 h-10 rounded-xl bg-naija-600/20 border border-naija-700/40 text-naija-300 flex items-center justify-center">
                  <Icon size={20} />
                </div>
                <span className="text-xs text-ink-500 font-mono">STEP {n}</span>
              </div>
              <h3 className="text-lg font-semibold text-ink-50">{t}</h3>
              <p className="text-sm text-ink-400 mt-2 leading-relaxed">{d}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Validated by Nigerians */}
      <section className="relative overflow-hidden border-y border-ink-800/80">
        <div className="absolute inset-0 bg-gradient-to-r from-naija-600/[0.07] via-transparent to-amber-500/[0.06] pointer-events-none" />
        <div className="relative max-w-4xl mx-auto px-6 py-20 text-center">
          <div className="text-xs font-semibold tracking-widest text-naija-400 uppercase mb-5">Validated by Nigerians</div>
          <p className="text-2xl md:text-[2.1rem] leading-snug font-semibold text-ink-50 tracking-tight">
            Nigerian readers rate our <span className="text-naija-300">8B local model</span> as authentic
            as frontier AI — <span className="text-ink-300">a statistical tie at 48.5%</span> in blind A/B,
            while frontier LLM judges (carrying a Western prior) under-rate it.
          </p>
          <div className="mt-8 flex items-center justify-center gap-8 text-sm flex-wrap">
            <div><div className="text-3xl font-bold text-naija-300 tabular-nums">48.5%</div><div className="text-xs text-ink-400 mt-1">human win-rate vs Claude</div></div>
            <div className="w-px h-10 bg-ink-700" />
            <div><div className="text-3xl font-bold text-naija-300 tabular-nums">−15.5%</div><div className="text-xs text-ink-400 mt-1">rating-error vs frontier</div></div>
            <div className="w-px h-10 bg-ink-700" />
            <div><div className="text-3xl font-bold text-naija-300 tabular-nums">$0</div><div className="text-xs text-ink-400 mt-1">per call, runs local</div></div>
          </div>
        </div>
      </section>

      {/* Built for how Nigerians actually shop & speak */}
      <section className="max-w-5xl mx-auto px-6 py-16">
        <div className="grid lg:grid-cols-2 gap-8 items-center">
          {/* Styled placeholder — mirrors the photo box in the demo */}
          <div className="rounded-2xl min-h-[280px] border border-ink-800 bg-gradient-to-br from-naija-900/40 via-ink-900 to-amber-900/20 flex items-center justify-center">
            <div className="text-center space-y-2 px-8">
              <div className="text-5xl">🇳🇬</div>
              <p className="text-sm text-ink-500">24 personas · 6 zones · 4 languages</p>
            </div>
          </div>
          <div className="flex flex-col justify-center space-y-4">
            <h2 className="text-2xl md:text-3xl font-bold text-ink-50 tracking-tight">
              Built for how Nigerians actually shop &amp; speak
            </h2>
            <p className="text-ink-300 leading-relaxed">
              Vanilla AI flattens "e too much abeg" into bland English and reads "Alhamdulillah" as a
              complaint. InsideNaija is powered by{" "}
              <span className="text-naija-300">NaijaReviewer-8B</span>, fine-tuned on Nigerian reviews,
              so reactions land in the right register — Pidgin, Yorùbá, Hausa, Igbo — for every region,
              age and faith.
            </p>
            <ul className="space-y-2.5">
              {[
                "Calibrated to 6 geopolitical zones",
                "Predicts ratings within ±1.1★ on unseen products",
                "Hear every reaction in a Nigerian voice",
              ].map((x) => (
                <li key={x} className="flex items-center gap-2.5 text-sm text-ink-200">
                  <Check size={16} className="text-naija-400 shrink-0" /> {x}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </section>

      {/* Business value */}
      <section className="bg-ink-900/50 border-y border-ink-800 py-16">
        <div className="max-w-5xl mx-auto px-6 space-y-12">
          <div className="text-center space-y-3">
            <h2 className="text-3xl font-bold">Business value</h2>
            <p className="text-ink-400 max-w-xl mx-auto">
              The Nigerian market is the largest in Africa — and the most underserved
              by Western AI tools. That gap has a cost.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {BUSINESS_VALUE.map(({ icon: Icon, title, body }) => (
              <div key={title} className="bg-ink-900 border border-ink-800 rounded-xl p-6 space-y-3 hover:border-naija-700/50 transition-colors">
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

      {/* Implications */}
      <section className="max-w-5xl mx-auto px-6 py-16 space-y-8">
        <div className="text-center space-y-3">
          <h2 className="text-3xl font-bold">Why this matters now</h2>
        </div>
        <div className="bg-ink-900 border border-ink-800 rounded-2xl p-8 space-y-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 text-center">
            <div className="space-y-2">
              <p className="text-4xl font-bold text-naija-400">218M+</p>
              <p className="text-sm text-ink-300 font-medium">Nigerians</p>
              <p className="text-xs text-ink-500">Africa's largest consumer market</p>
            </div>
            <div className="space-y-2">
              <p className="text-4xl font-bold text-naija-400">500+</p>
              <p className="text-sm text-ink-300 font-medium">Languages & dialects</p>
              <p className="text-xs text-ink-500">No Western model adequately covers this</p>
            </div>
            <div className="space-y-2">
              <p className="text-4xl font-bold text-naija-400">$1T+</p>
              <p className="text-sm text-ink-300 font-medium">Projected GDP by 2030</p>
              <p className="text-xs text-ink-500">The market is growing fast</p>
            </div>
          </div>
          <div className="border-t border-ink-800 pt-6 space-y-3">
            <p className="text-ink-200 leading-relaxed">
              Most AI tools were trained predominantly on English-language Western data. When applied to
              Nigerian consumers, they miss register shifts, cultural reference points, and the
              Pidgin-code-mixed communication patterns that define how Nigerians actually talk about products.
            </p>
            <p className="text-ink-400 leading-relaxed text-sm">
              InsideNaija closes that gap — not by patching a generic model, but by building a
              culturally-specific research tool from the ground up. The implication for businesses
              is simple: better insight, faster, at a fraction of the cost of traditional methods.
            </p>
          </div>
        </div>
      </section>

      {/* Use cases */}
      <section className="bg-ink-900/50 border-y border-ink-800 py-16">
        <div className="max-w-5xl mx-auto px-6 space-y-10">
          <h2 className="text-3xl font-bold text-center">Use cases</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {USE_CASES.map(({ sector, example }) => (
              <div key={sector} className="bg-ink-900 border border-ink-800 rounded-xl p-5 space-y-2 hover:border-naija-700/40 transition-colors">
                <span className="text-xs font-bold text-naija-400 uppercase tracking-wider">{sector}</span>
                <p className="text-sm text-ink-300 leading-relaxed">{example}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-4xl mx-auto px-6 py-20 text-center space-y-6">
        <h2 className="text-4xl font-bold">Ready to run your first panel?</h2>
        <p className="text-ink-400 text-lg max-w-xl mx-auto">
          Create an account, describe your product, and get results before your next meeting.
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Button size="lg" className="bg-naija-600 hover:bg-naija-700 text-white px-10 h-12 text-base"
            onClick={() => navigate("/signup")}>
            Start for free <ArrowRight size={18} className="ml-2" />
          </Button>
          <Button size="lg" variant="outline"
            className="border-ink-700 text-ink-200 hover:border-naija-600 h-12"
            onClick={() => navigate("/products/shopeasy")}>
            See ShopEasy →
          </Button>
        </div>
        <p className="text-sm text-ink-600">No credit card · Results in under 2 minutes</p>
      </section>
    </div>
  );
}
