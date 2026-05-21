// B2B connect page - a business registers and gets an embeddable widget snippet.

import { useState } from "react";
import { ArrowRight, Check, Code2, Copy, Loader2, Store, Zap } from "lucide-react";

export default function B2B() {
  const [name, setName] = useState("");
  const [website, setWebsite] = useState("");
  const [color, setColor] = useState("#008751");
  const [category, setCategory] = useState("");
  const [loading, setLoading] = useState(false);
  const [bizId, setBizId] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const origin = window.location.origin;
  const embed = bizId
    ? `<iframe src="${origin}/?widget=1&business=${bizId}"\n        width="100%" height="520" style="border:0;border-radius:12px"></iframe>`
    : "";

  async function connect() {
    if (!name.trim() || loading) return;
    setLoading(true);
    try {
      const r = await fetch("/b2b/register", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: name.trim(), website: website.trim() || undefined,
          brand_color: color, default_category: category.trim() || undefined,
        }),
      }).then((x) => x.json());
      if (r?.business_id) setBizId(r.business_id);
    } catch { /* ignore */ }
    setLoading(false);
  }

  return (
    <div className="min-h-screen bg-ink-950 text-ink-100">
      <header className="border-b border-ink-800 bg-ink-950/80 backdrop-blur-md">
        <div className="max-w-5xl mx-auto px-6 py-3.5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-naija-500 to-naija-800 flex items-center justify-center"><Store size={16} className="text-white" /></div>
            <span className="font-bold text-ink-50">ShopEasy <span className="brand-text">for Business</span></span>
          </div>
          <nav className="flex items-center gap-4 text-xs">
            <a href="#shopeasy" className="text-ink-400 hover:text-ink-200">Consumer app ↗</a>
            <a href="#" className="text-ink-400 hover:text-ink-200">InsideNaija ↗</a>
          </nav>
        </div>
      </header>

      <section className="relative overflow-hidden mesh grain max-w-5xl mx-auto px-6 pt-16 pb-8 text-center rounded-3xl">
        <div className="inline-flex items-center gap-2 text-xs font-medium text-naija-300 bg-naija-900/40 border border-naija-700/40 rounded-full px-3 py-1 mb-5">
          <Zap size={13} /> B2B · embeddable recommendations
        </div>
        <h1 className="text-4xl md:text-5xl font-extrabold text-ink-50 tracking-tight max-w-2xl mx-auto leading-[1.05]">
          Add <span className="brand-text">Nigeria-smart</span> recommendations to your store in one snippet.
        </h1>
        <p className="text-ink-300 mt-4 max-w-xl mx-auto">
          Connect your business and drop one line of code. Your shoppers get
          persona-aware product recommendations powered by our Nigerian engine -           no ML team required.
        </p>
      </section>

      <section className="max-w-5xl mx-auto px-6 pb-20 grid lg:grid-cols-2 gap-8 items-start">
        {/* Connect form */}
        <div className="bg-ink-900/50 border border-ink-700 rounded-2xl p-6">
          <h2 className="font-semibold text-ink-50 mb-4 flex items-center gap-2"><Store size={16} /> Connect your business</h2>
          <label className="text-xs text-ink-400">Business name *</label>
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Bigi Stores"
                 className="w-full mt-1 mb-3 bg-ink-950 border border-ink-700 focus:border-naija-600 rounded-lg px-3 py-2 text-sm text-ink-100 outline-none" />
          <label className="text-xs text-ink-400">Website</label>
          <input value={website} onChange={(e) => setWebsite(e.target.value)} placeholder="https://…"
                 className="w-full mt-1 mb-3 bg-ink-950 border border-ink-700 focus:border-naija-600 rounded-lg px-3 py-2 text-sm text-ink-100 outline-none" />
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-xs text-ink-400">Brand colour</label>
              <input type="color" value={color} onChange={(e) => setColor(e.target.value)}
                     className="w-full mt-1 h-9 bg-ink-950 border border-ink-700 rounded-lg" />
            </div>
            <div>
              <label className="text-xs text-ink-400">Default category</label>
              <input value={category} onChange={(e) => setCategory(e.target.value)} placeholder="electronics"
                     className="w-full mt-1 bg-ink-950 border border-ink-700 focus:border-naija-600 rounded-lg px-3 py-2 text-sm text-ink-100 outline-none" />
            </div>
          </div>
          <button onClick={connect} disabled={loading || !name.trim()}
                  className="w-full mt-5 inline-flex items-center justify-center gap-2 bg-naija-600 hover:bg-naija-500 disabled:opacity-50 text-white font-semibold rounded-lg py-2.5 transition-colors">
            {loading ? <Loader2 size={16} className="animate-spin" /> : <>Connect & get snippet <ArrowRight size={15} /></>}
          </button>
        </div>

        {/* Snippet + preview */}
        <div>
          {bizId ? (
            <>
              <div className="bg-ink-900/50 border border-ink-700 rounded-2xl p-6">
                <h2 className="font-semibold text-ink-50 mb-1 flex items-center gap-2"><Code2 size={16} /> Your embed snippet</h2>
                <p className="text-xs text-ink-400 mb-3">Paste this where you want recommendations to appear.</p>
                <pre className="bg-ink-950 border border-ink-800 rounded-lg p-3 text-[11px] text-naija-200 overflow-x-auto whitespace-pre-wrap">{embed}</pre>
                <button onClick={() => { navigator.clipboard.writeText(embed); setCopied(true); setTimeout(() => setCopied(false), 1500); }}
                        className="mt-3 inline-flex items-center gap-1.5 text-xs bg-ink-800 hover:bg-ink-700 text-ink-200 rounded-lg px-3 py-1.5">
                  {copied ? <><Check size={13} className="text-naija-400" /> Copied</> : <><Copy size={13} /> Copy</>}
                </button>
              </div>
              <div className="mt-4">
                <div className="text-xs text-ink-400 mb-2">Live preview</div>
                <iframe src={`/?widget=1&business=${bizId}`} className="w-full rounded-xl border border-ink-700 bg-white" height={500} title="widget preview" />
              </div>
            </>
          ) : (
            <div className="bg-ink-900/30 border border-dashed border-ink-700 rounded-2xl p-10 text-center text-ink-500 text-sm">
              Connect your business to generate an embeddable widget + live preview.
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
