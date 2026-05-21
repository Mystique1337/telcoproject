// Embeddable B2B recommendations widget. Businesses drop this in an <iframe>:
//   <iframe src="HOST/?widget=1&business=biz_xxx" width="100%" height="520"></iframe>
// It serves recommendations from our engine, branded for the business.

import { useEffect, useState } from "react";
import { Loader2, Search, ShoppingBag } from "lucide-react";

interface WProduct { product_id: string; title: string; category?: string | null; price_naira?: number | null; }

function naira(n?: number | null) { return n ? "₦" + Number(n).toLocaleString() : " - "; }

function WThumb({ p }: { p: WProduct }) {
  const [url, setUrl] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let c = false;
    const q = `${p.title || ""} ${(p.category || "").replace(/-/g, " ")}`.trim().slice(0, 100);
    fetch(`/shop/image?q=${encodeURIComponent(q)}`).then((r) => r.json())
      .then((d) => { if (!c) setUrl(d.url || null); }).catch(() => {});
    return () => { c = true; };
  }, [p.product_id]);
  if (!url || failed) {
    return <div className="w-full aspect-square bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center"><ShoppingBag className="text-gray-400" /></div>;
  }
  return <img src={url} alt={p.title} onError={() => setFailed(true)} className="w-full aspect-square object-cover bg-gray-100" />;
}

export default function Widget() {
  const params = new URLSearchParams(window.location.search);
  const businessId = params.get("business") || "";
  const [name, setName] = useState("Store");
  const [color, setColor] = useState("#008751");
  const [query, setQuery] = useState("");
  const [products, setProducts] = useState<WProduct[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!businessId) { setLoading(false); return; }
    fetch(`/b2b/${businessId}`).then((r) => r.json()).then((d) => {
      setName(d.name || "Store");
      setColor(d.config?.brand_color || "#008751");
    }).catch(() => {});
    run("");
  }, [businessId]);

  async function run(q: string) {
    setLoading(true);
    try {
      const r = await fetch("/b2b/recommend", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ business_id: businessId, query: q, k: 8 }),
      });
      const d = await r.json();
      setProducts(d.products || []);
    } catch { /* ignore */ }
    setLoading(false);
  }

  if (!businessId) {
    return <div className="p-6 font-sans text-sm text-gray-500">Missing business id.</div>;
  }

  return (
    <div className="font-sans bg-white min-h-screen text-gray-800">
      <div className="px-4 py-3 flex items-center justify-between border-b" style={{ borderColor: "#eee" }}>
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded-md flex items-center justify-center text-white" style={{ background: color }}>
            <ShoppingBag size={14} />
          </div>
          <span className="font-semibold text-gray-900">{name}</span>
          <span className="text-[10px] text-gray-400">· recommended for you</span>
        </div>
      </div>

      <div className="p-3">
        <div className="flex items-center gap-2 border rounded-lg px-2 py-1.5 mb-3" style={{ borderColor: "#ddd" }}>
          <Search size={15} className="text-gray-400" />
          <input value={query} onChange={(e) => setQuery(e.target.value)}
                 onKeyDown={(e) => e.key === "Enter" && run(query)}
                 placeholder="What are you looking for?"
                 className="flex-1 text-sm outline-none bg-transparent" />
          <button onClick={() => run(query)} className="text-xs font-semibold text-white rounded-md px-3 py-1" style={{ background: color }}>Go</button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-10 text-gray-400"><Loader2 className="animate-spin" /></div>
        ) : (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {products.map((p) => (
              <div key={p.product_id} className="border rounded-lg overflow-hidden" style={{ borderColor: "#eee" }}>
                <WThumb p={p} />
                <div className="p-2">
                  <div className="text-xs text-gray-700 line-clamp-2 min-h-[2rem] leading-snug">{p.title}</div>
                  <div className="text-sm font-bold mt-1" style={{ color }}>{naira(p.price_naira)}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="px-4 py-2 text-center text-[10px] text-gray-400 border-t" style={{ borderColor: "#eee" }}>
        Powered by ShopEasy · InsideNaija
      </div>
    </div>
  );
}
