import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { ArrowRight, ShoppingBag, Brain, Languages, TrendingUp, Repeat, Star, Search, Sparkles, ShoppingCart } from "lucide-react";
import { Button } from "@/components/ui/button";
import Navbar from "@/components/Navbar";
import ShopEasy from "@/ShopEasy";

const STATS = [
  { value: "NDCG 0.572", label: "Recommendation relevance", sub: "best of 5 models evaluated" },
  { value: "5", label: "Languages supported", sub: "English, Pidgin, Yoruba, Hausa, Igbo" },
  { value: "4", label: "Cognitive dimensions", sub: "per persona — hedonic, communal, aspect, intensity" },
  { value: "Real-time", label: "Persona adaptation", sub: "learns from every interaction" },
];


const BUSINESS_VALUE = [
  {
    title: "Higher conversion through cultural fit",
    body: "A recommendation engine trained on Western behaviour patterns will recommend the wrong products to Nigerian shoppers. ShopEasy's persona model is built for how Nigerians actually shop — communal gifting, occasion-driven purchases, price sensitivity by category.",
  },
  {
    title: "Reduce returns and dissatisfaction",
    body: "Wrong recommendations drive returns and erode trust. By matching on cultural fit — not just collaborative filtering — ShopEasy surfaces products that genuinely resonate.",
  },
  {
    title: "Language is a conversion lever",
    body: "Shoppers who interact in Pidgin or Yoruba are more engaged. Native language support isn't a feature — it's a conversion driver that Western platforms consistently underinvest in.",
  },
  {
    title: "Embeddable for any retailer",
    body: "ShopEasy ships with a B2B widget — drop one script tag into any Nigerian e-commerce platform and get persona-aware recommendations instantly. No replatforming required.",
  },
];

const IMPLICATIONS = [
  {
    number: "01",
    heading: "The recommendation gap is real",
    body: "Amazon, Jumia, Konga — all use recommendation engines trained on global or Western data. For Nigerian shoppers, that means generic results that miss cultural context. ShopEasy is the first recommendation layer built specifically for Nigerian consumer behaviour.",
  },
  {
    number: "02",
    heading: "Language unlocks trust",
    body: "Code-switching between English and Pidgin is not informal — it is how Nigerians signal authenticity. A storefront that speaks Pidgin back to a Pidgin-speaking shopper doesn't just feel better. It converts better.",
  },
  {
    number: "03",
    heading: "The opportunity is structural",
    body: "Nigerian e-commerce is growing at 15%+ annually. The retailers who build cultural intelligence into their stack now will have a compounding advantage over those who bolt it on later.",
  },
];

export default function ShopEasyPage() {
  const navigate = useNavigate();
  const [showDemo, setShowDemo] = useState(false);

  return (
    <div className="min-h-screen bg-ink-950 text-ink-50">
      <Navbar />

      {/* Hero — ported from the ShopEasy demo Home component */}
      <section className="relative overflow-hidden">
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[800px] h-[800px] bg-amber-600/10 rounded-full blur-3xl pointer-events-none" />
        <div className="relative max-w-5xl mx-auto px-6 pt-20 pb-12 grid lg:grid-cols-2 gap-12 items-center">
          <div>
            <div className="inline-flex items-center gap-2 text-xs font-medium text-amber-300 bg-amber-900/30 border border-amber-700/40 rounded-full px-3 py-1 mb-6">
              <Sparkles size={13} /> Nigeria's AI shopping assistant
            </div>
            <h1 className="text-4xl md:text-5xl font-extrabold text-ink-50 leading-[1.1] tracking-tight">
              Shop smarter,{" "}
              <span className="text-amber-400">the Naija way.</span>
            </h1>
            <p className="mt-5 text-lg text-ink-300 leading-relaxed max-w-lg">
              Type it, snap it, say it, or just chat — in English, Pidgin, Yorùbá,
              Hausa or Igbo. ShopEasy understands what you mean and recommends what
              actually fits you.
            </p>
            <div className="mt-8 flex items-center gap-3 flex-wrap">
              <Button size="lg" className="bg-amber-600 hover:bg-amber-700 text-white px-6 h-12 text-base"
                onClick={() => navigate("/signup")}>
                Start shopping <ArrowRight size={16} className="ml-2" />
              </Button>
              <Button size="lg" variant="outline"
                className="border-ink-700 text-ink-200 hover:border-amber-600 h-12"
                onClick={() => setShowDemo((d) => !d)}>
                {showDemo ? "Hide demo" : "See it live"}
              </Button>
            </div>
            <div className="mt-8 flex items-center gap-6 text-xs text-ink-400 flex-wrap">
              <span className="inline-flex items-center gap-1.5"><ShoppingCart size={13} /> Pay on delivery</span>
              <span className="inline-flex items-center gap-1.5"><Sparkles size={13} /> Persona-aware AI</span>
              <span className="inline-flex items-center gap-1.5"><ShoppingBag size={13} /> 5 languages</span>
            </div>
          </div>
          {/* Photo placeholder — gradient box matching ShopEasy amber theme */}
          <div className="rounded-2xl min-h-[320px] border border-amber-800/40 bg-gradient-to-br from-amber-900/30 via-ink-900 to-ink-950 items-center justify-center hidden lg:flex">
            <div className="text-center space-y-2 px-8">
              <div className="text-5xl">🛒</div>
              <p className="text-sm text-ink-500">Search by text, photo or voice</p>
              <p className="text-xs text-ink-700">English · Pidgin · Yorùbá · Hausa · Igbo</p>
            </div>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="max-w-5xl mx-auto px-6 pb-16">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          {STATS.map((s) => (
            <div key={s.value} className="bg-ink-900 border border-ink-800 rounded-xl p-6 text-center space-y-1">
              <p className="text-2xl font-bold text-amber-400">{s.value}</p>
              <p className="text-sm font-medium text-ink-100">{s.label}</p>
              <p className="text-xs text-ink-500">{s.sub}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Live demo */}
      {showDemo && (
        <section className="max-w-6xl mx-auto px-6 pb-16">
          <div className="border border-amber-700/40 rounded-2xl overflow-hidden">
            <div className="bg-ink-900 border-b border-ink-800 px-6 py-3 flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-red-500/60" />
              <span className="w-3 h-3 rounded-full bg-amber-500/60" />
              <span className="w-3 h-3 rounded-full bg-green-500/60" />
              <span className="ml-3 text-xs text-ink-500">ShopEasy — live demo</span>
            </div>
            <ShopEasy />
          </div>
        </section>
      )}

      {/* How it works */}
      <section className="max-w-5xl mx-auto px-6 py-16">
        <div className="grid md:grid-cols-3 gap-6">
          {[
            { icon: Search,       t: "Search any way",    d: "Type, snap a photo, talk, or just chat — in your language." },
            { icon: Sparkles,     t: "We learn you",      d: "Tell us your area & taste once; recommendations get personal." },
            { icon: ShoppingCart, t: "Order in clicks",   d: "Real prices, clear picks, pay on delivery." },
          ].map(({ icon: Icon, t, d }) => (
            <div key={t} className="bg-ink-900/40 border border-ink-800 rounded-2xl p-6">
              <div className="w-10 h-10 rounded-xl bg-amber-600/20 border border-amber-700/40 text-amber-300 flex items-center justify-center mb-4">
                <Icon size={18} />
              </div>
              <h3 className="text-lg font-semibold text-ink-50">{t}</h3>
              <p className="text-sm text-ink-400 mt-2 leading-relaxed">{d}</p>
            </div>
          ))}
        </div>
        <div className="mt-10 text-center">
          <Button size="lg" className="bg-amber-600 hover:bg-amber-700 text-white px-8 h-12 text-base" onClick={() => navigate("/signup")}>
            Browse products <ArrowRight size={18} className="ml-2" />
          </Button>
        </div>
      </section>

      {/* Business value */}
      <section className="bg-ink-900/50 border-y border-ink-800 py-16">
        <div className="max-w-5xl mx-auto px-6 space-y-10">
          <div className="text-center space-y-3">
            <h2 className="text-3xl font-bold">Business value</h2>
            <p className="text-ink-400 max-w-xl mx-auto">
              Cultural fit is not a nice-to-have. It is the difference between a recommendation
              that converts and one that gets ignored.
            </p>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
            {BUSINESS_VALUE.map(({ title, body }) => (
              <div key={title} className="bg-ink-900 border border-ink-800 rounded-xl p-6 space-y-2 hover:border-amber-700/40 transition-colors">
                <div className="flex items-start gap-2">
                  <Star size={16} className="text-amber-400 mt-0.5 shrink-0" />
                  <h3 className="font-semibold text-ink-100">{title}</h3>
                </div>
                <p className="text-sm text-ink-400 leading-relaxed pl-6">{body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Implications */}
      <section className="max-w-5xl mx-auto px-6 py-16 space-y-8">
        <h2 className="text-3xl font-bold text-center">Why this matters</h2>
        <div className="space-y-4">
          {IMPLICATIONS.map(({ number, heading, body }) => (
            <div key={number} className="bg-ink-900 border border-ink-800 rounded-xl p-6 flex gap-6 hover:border-amber-700/30 transition-colors">
              <span className="text-3xl font-bold text-amber-700 shrink-0">{number}</span>
              <div className="space-y-2">
                <h3 className="font-semibold text-ink-100">{heading}</h3>
                <p className="text-sm text-ink-400 leading-relaxed">{body}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-4xl mx-auto px-6 py-16 text-center space-y-6">
        <h2 className="text-4xl font-bold">Start selling to Nigeria, not at it</h2>
        <p className="text-ink-400 text-lg max-w-xl mx-auto">
          Create an account and experience persona-aware shopping in your language.
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Button size="lg" className="bg-amber-600 hover:bg-amber-700 text-white px-10 h-12 text-base"
            onClick={() => navigate("/signup")}>
            Try ShopEasy free <ArrowRight size={18} className="ml-2" />
          </Button>
          <Button size="lg" variant="outline"
            className="border-ink-700 text-ink-200 hover:border-naija-600 h-12"
            onClick={() => navigate("/products/insidenaija")}>
            ← See InsideNaija
          </Button>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-ink-800">
        <div className="max-w-5xl mx-auto px-6 py-12 grid md:grid-cols-4 gap-8">
          <div className="md:col-span-2">
            <div className="flex items-center gap-2.5 mb-3">
              <div className="w-7 h-7 rounded-lg bg-amber-600 flex items-center justify-center">
                <ShoppingCart size={14} className="text-white" />
              </div>
              <span className="font-bold text-ink-50">ShopEasy</span>
            </div>
            <p className="text-sm text-ink-400 max-w-xs leading-relaxed">
              AI shopping for the Nigerian market. Search by text, photo, voice or chat in 5 languages.
            </p>
          </div>
          <div>
            <div className="text-xs font-semibold text-ink-300 uppercase tracking-wider mb-3">Products</div>
            <ul className="space-y-2 text-sm text-ink-400">
              <li><button onClick={() => navigate("/products/shopeasy")} className="hover:text-amber-300 transition-colors">ShopEasy — Store</button></li>
              <li><button onClick={() => navigate("/products/insidenaija")} className="hover:text-amber-300 transition-colors">InsideNaija — Panel</button></li>
              <li><button onClick={() => navigate("/signup")} className="hover:text-amber-300 transition-colors">Get started free</button></li>
            </ul>
          </div>
          <div>
            <div className="text-xs font-semibold text-ink-300 uppercase tracking-wider mb-3">Platform</div>
            <ul className="space-y-2 text-sm text-ink-400">
              <li>5 Nigerian languages</li>
              <li>Voice + photo search</li>
              <li>Persona-aware AI</li>
            </ul>
          </div>
        </div>
        <div className="border-t border-ink-800/70">
          <div className="max-w-5xl mx-auto px-6 py-5 text-xs text-ink-600 flex items-center justify-between flex-wrap gap-2">
            <span>© 2026 Naija Persona. ShopEasy — AI shopping built for Nigeria.</span>
            <span>Search by text, photo, voice or chat · 5 languages</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
