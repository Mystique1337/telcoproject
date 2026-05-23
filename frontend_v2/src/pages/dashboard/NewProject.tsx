import { useState, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import * as XLSX from "xlsx";
import {
  ArrowLeft, Loader2, Zap, Upload, Download,
  FileSpreadsheet, CheckCircle2, X, AlertCircle,
  ChevronDown,
} from "lucide-react";
import RichTextEditor from "@/components/RichTextEditor";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import DashboardLayout from "@/components/DashboardLayout";
import { createProject, createProjectsBulk, type BulkProjectItem, type BulkProjectResult } from "@/lib/apiClient";

// ── Constants ─────────────────────────────────────────────────────────────────

const CATEGORIES = ["FMCG","Fashion & Beauty","Fintech","Media & Entertainment","Agriculture","Health & Wellness","Technology","Other"];

const TEMPLATE_HEADERS = ["name","description","category","image_url"];
const TEMPLATE_EXAMPLE  = ["Indomie Chicken Suya Flavour","A new limited-edition noodle flavour combining the bold heat of Suya spice with the convenience of Indomie. Targeting young professionals aged 18–35 in Lagos and Abuja. ₦250 per pack.","FMCG",""];

const REQUIRED_FIELDS: Array<keyof BulkProjectItem> = ["name","description"];
const OPTIONAL_FIELDS: Array<keyof BulkProjectItem> = ["category","image_url"];
const ALL_FIELDS = [...REQUIRED_FIELDS, ...OPTIONAL_FIELDS];

const FIELD_LABELS: Record<string, string> = {
  name: "Product name",
  description: "Product description",
  category: "Category",
  image_url: "Image URL",
};

// ── Types ─────────────────────────────────────────────────────────────────────

type ParsedRow = Record<string, string>;
type ColMapping = Record<string, string>; // field → column header

// ── Template download ─────────────────────────────────────────────────────────

function downloadTemplate(format: "csv" | "xlsx") {
  const data = [TEMPLATE_HEADERS, TEMPLATE_EXAMPLE];
  const ws = XLSX.utils.aoa_to_sheet(data);

  // Column widths
  ws["!cols"] = [{ wch: 32 }, { wch: 80 }, { wch: 24 }, { wch: 40 }];

  if (format === "xlsx") {
    const wb = XLSX.utils.book_new();
    XLSX.utils.book_append_sheet(wb, ws, "Projects");
    XLSX.writeFile(wb, "naija-persona-import-template.xlsx");
  } else {
    const csv = XLSX.utils.sheet_to_csv(ws);
    const blob = new Blob([csv], { type: "text/csv" });
    const a = Object.assign(document.createElement("a"), {
      href: URL.createObjectURL(blob),
      download: "naija-persona-import-template.csv",
    });
    a.click();
  }
}

// ── Auto-map columns ──────────────────────────────────────────────────────────

function autoMap(headers: string[]): ColMapping {
  const lower = headers.map((h) => h.toLowerCase().trim());
  const mapping: ColMapping = {};
  for (const field of ALL_FIELDS) {
    const aliases: Record<string, string[]> = {
      name:        ["name","product name","product_name","title","product title"],
      description: ["description","desc","product description","details","about"],
      category:    ["category","cat","type","product category","product type"],
      image_url:   ["image_url","image url","image","img","photo","photo url"],
    };
    for (const alias of (aliases[field] ?? [field])) {
      const idx = lower.indexOf(alias);
      if (idx !== -1) { mapping[field] = headers[idx]; break; }
    }
  }
  return mapping;
}

function isFullyMapped(mapping: ColMapping): boolean {
  return REQUIRED_FIELDS.every((f) => !!mapping[f]);
}

// ── Single project form ───────────────────────────────────────────────────────

function SingleProjectForm() {
  const navigate = useNavigate();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [category, setCategory] = useState("FMCG");
  const [imageUrl, setImageUrl] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const descText = description.replace(/<[^>]+>/g, "").trim();
    if (!name.trim() || !descText) { setError("Product name and description are required."); return; }
    setError(""); setLoading(true);
    try {
      const res = await createProject({ name: name.trim(), description: description.trim(), category, image_url: imageUrl.trim() || undefined });
      navigate(`/runs/${res.run_id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
      setLoading(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="bg-ink-900 border border-ink-800 rounded-xl p-6 space-y-5">
        <div className="space-y-2">
          <Label htmlFor="name" className="text-ink-200">Product name <span className="text-red-400">*</span></Label>
          <Input id="name" placeholder="e.g. Indomie Chicken Suya Flavour" value={name} onChange={(e) => setName(e.target.value)}
            className="bg-ink-950 border-ink-700 text-ink-50 placeholder:text-ink-600 focus-visible:ring-naija-600" disabled={loading} />
        </div>
        <div className="space-y-2">
          <Label className="text-ink-200">
            Description <span className="text-red-400">*</span>
            <span className="ml-2 text-xs text-ink-600 font-normal">supports bold, italic, lists</span>
          </Label>
          <RichTextEditor
            value={description}
            onChange={setDescription}
            placeholder="Describe the product — what it is, who it's for, price point, key variants…"
            disabled={loading}
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="category" className="text-ink-200">Category</Label>
            <select id="category" value={category} onChange={(e) => setCategory(e.target.value)} disabled={loading}
              className="w-full rounded-md border border-ink-700 bg-ink-950 px-3 py-2 text-sm text-ink-50 focus:outline-none focus:ring-2 focus:ring-naija-600">
              {CATEGORIES.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div className="space-y-2">
            <Label htmlFor="image" className="text-ink-200">Image URL <span className="text-ink-600 font-normal">(optional)</span></Label>
            <Input id="image" placeholder="https://…" value={imageUrl} onChange={(e) => setImageUrl(e.target.value)}
              className="bg-ink-950 border-ink-700 text-ink-50 placeholder:text-ink-600 focus-visible:ring-naija-600" disabled={loading} />
          </div>
        </div>
      </div>

      <div className="flex items-start gap-3 bg-naija-900/20 border border-naija-700/30 rounded-xl px-4 py-3">
        <Zap size={15} className="text-naija-400 mt-0.5 shrink-0" />
        <p className="text-xs text-ink-400 leading-relaxed">
          Your product runs through 24 culturally-grounded Nigerian personas. Results in under 2 minutes.
        </p>
      </div>

      {error && <p className="text-sm text-red-400 bg-red-900/20 border border-red-700/30 rounded-lg px-4 py-3">{error}</p>}

      <Button type="submit" disabled={loading} className="w-full bg-naija-600 hover:bg-naija-700 text-white h-12 text-base">
        {loading ? <><Loader2 size={18} className="mr-2 animate-spin" />Launching panel…</> : "Run panel →"}
      </Button>
    </form>
  );
}

// ── Bulk import ───────────────────────────────────────────────────────────────

interface ParsedData {
  headers: string[];
  rows: ParsedRow[];
  fileName: string;
}

function ColumnMapperRow({ field, headers, value, onChange, required }: {
  field: string; headers: string[]; value: string; onChange: (v: string) => void; required: boolean;
}) {
  return (
    <div className="flex items-center gap-4">
      <div className="w-44 shrink-0">
        <span className="text-sm text-ink-200">{FIELD_LABELS[field]}</span>
        {required && <span className="text-red-400 ml-1">*</span>}
      </div>
      <div className="relative flex-1">
        <select value={value} onChange={(e) => onChange(e.target.value)}
          className="w-full appearance-none rounded-lg border border-ink-700 bg-ink-950 px-3 py-2 pr-8 text-sm text-ink-50 focus:outline-none focus:ring-2 focus:ring-naija-600">
          <option value="">— skip —</option>
          {headers.map((h) => <option key={h} value={h}>{h}</option>)}
        </select>
        <ChevronDown size={13} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-ink-500 pointer-events-none" />
      </div>
      {value
        ? <span className="text-xs text-naija-400 w-24 shrink-0">→ "{value}"</span>
        : <span className="text-xs text-ink-700 w-24 shrink-0">{required ? "required" : "optional"}</span>}
    </div>
  );
}

function BulkImport() {
  const navigate = useNavigate();
  const fileRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [parsed, setParsed] = useState<ParsedData | null>(null);
  const [mapping, setMapping] = useState<ColMapping>({});
  const [needsMapping, setNeedsMapping] = useState(false);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [submitting, setSubmitting] = useState(false);
  const [results, setResults] = useState<BulkProjectResult[]>([]);
  const [parseError, setParseError] = useState("");
  const [submitError, setSubmitError] = useState("");

  function parseFile(file: File) {
    setParseError(""); setSubmitError(""); setResults([]);
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = new Uint8Array(e.target!.result as ArrayBuffer);
        const wb = XLSX.read(data, { type: "array" });
        const ws = wb.Sheets[wb.SheetNames[0]];
        const raw: string[][] = XLSX.utils.sheet_to_json(ws, { header: 1, defval: "" });
        if (raw.length < 2) { setParseError("File must have a header row and at least one data row."); return; }
        const headers = raw[0].map(String);
        const dataRows: ParsedRow[] = raw.slice(1)
          .filter((r) => r.some((c) => String(c).trim()))
          .map((r) => Object.fromEntries(headers.map((h, i) => [h, String(r[i] ?? "")])));
        const auto = autoMap(headers);
        setParsed({ headers, rows: dataRows, fileName: file.name });
        setMapping(auto);
        setNeedsMapping(!isFullyMapped(auto));
        setSelected(new Set(dataRows.map((_, i) => i)));
      } catch {
        setParseError("Could not read file. Make sure it's a valid CSV or Excel file.");
      }
    };
    reader.readAsArrayBuffer(file);
  }

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setDragging(false);
    const file = e.dataTransfer.files[0];
    if (file) parseFile(file);
  }, []);

  function applyMapping(): BulkProjectItem[] {
    return (parsed?.rows ?? [])
      .filter((_, i) => selected.has(i))
      .map((row) => ({
        name:        (row[mapping.name]        ?? "").trim(),
        description: (row[mapping.description] ?? "").trim(),
        category:    (row[mapping.category]    ?? "FMCG").trim() || "FMCG",
        image_url:   mapping.image_url ? (row[mapping.image_url] ?? "").trim() || undefined : undefined,
      }))
      .filter((item) => item.name && item.description);
  }

  async function handleSubmit() {
    const items = applyMapping();
    if (!items.length) return;
    setSubmitting(true); setSubmitError("");
    try {
      const res = await createProjectsBulk(items);
      setResults(res);
    } catch (err: unknown) {
      setSubmitError(err instanceof Error ? err.message : "Submission failed. Try again.");
    } finally {
      setSubmitting(false);
    }
  }

  const toggleRow = (i: number) => setSelected((prev) => {
    const next = new Set(prev);
    next.has(i) ? next.delete(i) : next.add(i);
    return next;
  });

  const allChecked = parsed ? selected.size === parsed.rows.length : false;
  const toggleAll = () => setSelected(allChecked ? new Set() : new Set((parsed?.rows ?? []).map((_, i) => i)));
  const selectedItems = applyMapping();
  const readyToSubmit = selectedItems.length > 0 && (!needsMapping || isFullyMapped(mapping));

  return (
    <div className="space-y-4">

      {/* ── Step 1: Download template (always visible) ─────────────────────── */}
      <div className="bg-ink-900 border border-ink-800 rounded-xl p-5 space-y-3">
        <div className="flex items-start gap-3">
          <FileSpreadsheet size={18} className="text-naija-400 mt-0.5 shrink-0" />
          <div>
            <p className="text-sm font-semibold text-ink-100">Step 1 — Download the template</p>
            <p className="text-xs text-ink-500 mt-0.5">
              Required columns: <code className="text-naija-400">name</code>, <code className="text-naija-400">description</code>.
              Optional: <code className="text-ink-400">category</code>, <code className="text-ink-400">image_url</code>.
            </p>
          </div>
        </div>
        <div className="flex gap-2 pl-7">
          <button onClick={() => downloadTemplate("xlsx")}
            className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-naija-900/40 border border-naija-700/40 text-naija-300 hover:bg-naija-900/60 transition-colors">
            <Download size={12} /> Download XLSX
          </button>
          <button onClick={() => downloadTemplate("csv")}
            className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg bg-ink-800 border border-ink-700 text-ink-300 hover:bg-ink-700 transition-colors">
            <Download size={12} /> Download CSV
          </button>
        </div>
      </div>

      {/* ── Step 2: Upload zone (always visible) ───────────────────────────── */}
      <div className="bg-ink-900 border border-ink-800 rounded-xl p-5 space-y-3">
        <p className="text-sm font-semibold text-ink-100 flex items-center gap-2">
          <Upload size={16} className="text-naija-400" />
          Step 2 — {parsed ? "File loaded" : "Upload your file"}
        </p>

        {/* When a file is loaded: compact strip + re-upload button */}
        {parsed && (
          <div className="flex items-center gap-3 bg-ink-950 border border-ink-800 rounded-xl px-4 py-3">
            <CheckCircle2 size={16} className="text-naija-400 shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-ink-100 truncate">{parsed.fileName}</p>
              <p className="text-xs text-ink-500">{parsed.rows.length} row{parsed.rows.length !== 1 ? "s" : ""} detected</p>
            </div>
            <button
              onClick={() => { fileRef.current!.value = ""; fileRef.current?.click(); }}
              className="shrink-0 flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg border border-ink-700 text-ink-300 hover:border-naija-600 hover:text-naija-300 transition-colors"
            >
              <Upload size={11} /> Replace file
            </button>
          </div>
        )}

        {/* Drop zone — always shown; compact when file loaded */}
        <div
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
          onClick={() => fileRef.current?.click()}
          className={`border-2 border-dashed rounded-xl text-center cursor-pointer transition-all ${
            parsed ? "py-4" : "py-10"
          } ${dragging ? "border-naija-500 bg-naija-900/20" : "border-ink-700/60 hover:border-naija-700/60 hover:bg-ink-800/20"}`}
        >
          <Upload size={parsed ? 16 : 26} className="mx-auto text-ink-600 mb-2" />
          <p className="text-xs text-ink-500">{parsed ? "Drop a new file here to replace" : "Drop CSV or XLSX here, or click to browse"}</p>
          {!parsed && <p className="text-xs text-ink-700 mt-1">.csv · .xlsx · .xls</p>}
          <input ref={fileRef} type="file" accept=".csv,.xlsx,.xls" className="hidden"
            onChange={(e) => { const f = e.target.files?.[0]; if (f) parseFile(f); e.target.value = ""; }} />
        </div>

        {parseError && (
          <p className="flex items-center gap-2 text-sm text-red-400 bg-red-900/20 border border-red-700/30 rounded-lg px-4 py-3">
            <AlertCircle size={14} className="shrink-0" /> {parseError}
          </p>
        )}
      </div>

      {/* ── Step 3: Column mapping (only when needed) ──────────────────────── */}
      {parsed && needsMapping && (
        <div className="bg-ink-900 border border-amber-700/30 rounded-xl p-5 space-y-4">
          <div className="flex items-start gap-2">
            <AlertCircle size={15} className="text-amber-400 mt-0.5 shrink-0" />
            <div>
              <p className="text-sm font-semibold text-ink-100">Step 3 — Map your columns</p>
              <p className="text-xs text-ink-500 mt-0.5">
                We couldn't auto-detect all required fields. Tell us which column is which.
              </p>
            </div>
          </div>
          <div className="space-y-3">
            {ALL_FIELDS.map((field) => (
              <ColumnMapperRow
                key={field} field={field}
                headers={parsed.headers}
                value={mapping[field] ?? ""}
                onChange={(v) => setMapping((m) => ({ ...m, [field]: v }))}
                required={REQUIRED_FIELDS.includes(field as keyof BulkProjectItem)}
              />
            ))}
          </div>
          {!isFullyMapped(mapping) && (
            <p className="text-xs text-amber-400 flex items-center gap-1.5">
              <AlertCircle size={11} /> Map <strong>Product name</strong> and <strong>Description</strong> to continue.
            </p>
          )}
        </div>
      )}

      {/* ── Step 3/4: Row preview + selection ─────────────────────────────── */}
      {parsed && (!needsMapping || isFullyMapped(mapping)) && results.length === 0 && (
        <div className="bg-ink-900 border border-ink-800 rounded-xl overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-5 py-3.5 border-b border-ink-800">
            <div>
              <p className="text-sm font-semibold text-ink-100">
                {needsMapping ? "Step 4" : "Step 3"} — Select rows to import
              </p>
              <p className="text-xs text-ink-500 mt-0.5">
                {parsed.rows.length} row{parsed.rows.length !== 1 ? "s" : ""} ·{" "}
                <span className="text-naija-400">{selected.size} selected</span>
              </p>
            </div>
          </div>

          {/* Column labels */}
          <div className="grid grid-cols-[36px_1fr_2fr_1fr] gap-3 px-4 py-2.5 bg-ink-950/40 border-b border-ink-800 text-xs font-medium text-ink-500 uppercase tracking-wider">
            <div className="flex items-center">
              <input type="checkbox" checked={allChecked} onChange={toggleAll}
                className="w-4 h-4 rounded border-ink-600 bg-ink-800 accent-naija-600 cursor-pointer" />
            </div>
            <span>Product name</span>
            <span>Description</span>
            <span>Category</span>
          </div>

          {/* Rows */}
          <div className="divide-y divide-ink-800/60 max-h-72 overflow-y-auto">
            {parsed.rows.map((row, i) => {
              const name = (row[mapping.name] ?? "").trim();
              const desc = (row[mapping.description] ?? "").trim();
              const cat  = (row[mapping.category]    ?? "").trim();
              const valid = !!name && !!desc;
              return (
                <div key={i} onClick={() => valid && toggleRow(i)}
                  className={`grid grid-cols-[36px_1fr_2fr_1fr] gap-3 px-4 py-3 items-start transition-colors ${
                    valid ? "cursor-pointer hover:bg-ink-800/30" : "opacity-40"
                  } ${selected.has(i) ? "bg-naija-900/10" : ""}`}>
                  <div className="flex items-center pt-0.5">
                    <input type="checkbox" checked={selected.has(i)} readOnly disabled={!valid}
                      className="w-4 h-4 rounded border-ink-600 bg-ink-800 accent-naija-600 cursor-pointer" />
                  </div>
                  <p className="text-sm text-ink-100 font-medium truncate">{name || <span className="text-red-400 italic">missing</span>}</p>
                  <p className="text-xs text-ink-500 line-clamp-2 leading-relaxed">{desc || <span className="text-red-400 italic">missing</span>}</p>
                  <span className="text-xs px-2 py-0.5 rounded-md bg-ink-800 text-ink-400 w-fit">{cat || "—"}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Submit error */}
      {submitError && (
        <p className="flex items-center gap-2 text-sm text-red-400 bg-red-900/20 border border-red-700/30 rounded-lg px-4 py-3">
          <AlertCircle size={14} className="shrink-0" /> {submitError}
        </p>
      )}

      {/* ── Submit button ─────────────────────────────────────────────────── */}
      {parsed && readyToSubmit && results.length === 0 && (
        <Button disabled={submitting} onClick={handleSubmit}
          className="w-full bg-naija-600 hover:bg-naija-700 text-white h-12 text-base">
          {submitting
            ? <><Loader2 size={18} className="mr-2 animate-spin" />Launching {selectedItems.length} panel{selectedItems.length !== 1 ? "s" : ""}…</>
            : `Run ${selectedItems.length} panel${selectedItems.length !== 1 ? "s" : ""} →`}
        </Button>
      )}

      {/* ── Done: launched list ───────────────────────────────────────────── */}
      {results.length > 0 && (
        <div className="space-y-3">
          <div className="bg-naija-900/20 border border-naija-700/30 rounded-xl px-5 py-4 flex items-center gap-3">
            <CheckCircle2 size={20} className="text-naija-400 shrink-0" />
            <div>
              <p className="text-sm font-semibold text-ink-50">{results.length} panel{results.length !== 1 ? "s" : ""} launched</p>
              <p className="text-xs text-ink-500">Results stream in as each persona completes.</p>
            </div>
          </div>
          <div className="bg-ink-900 border border-ink-800 rounded-xl divide-y divide-ink-800">
            {results.map((r) => (
              <div key={r.run_id} onClick={() => navigate(`/runs/${r.run_id}`)}
                className="flex items-center justify-between px-5 py-3.5 hover:bg-ink-800/30 cursor-pointer transition-colors group">
                <div className="flex items-center gap-3">
                  <Loader2 size={13} className="text-naija-400 animate-spin shrink-0" />
                  <span className="text-sm font-medium text-ink-100 group-hover:text-naija-300 transition-colors truncate">{r.name}</span>
                </div>
                <span className="text-xs text-ink-500 shrink-0">View live →</span>
              </div>
            ))}
          </div>
          <Button variant="outline" className="w-full border-ink-700 text-ink-300" onClick={() => navigate("/dashboard")}>
            Back to dashboard
          </Button>
        </div>
      )}
    </div>
  );
}

// ── Page ──────────────────────────────────────────────────────────────────────

export default function NewProject() {
  const navigate = useNavigate();
  const [tab, setTab] = useState<"single" | "bulk">("single");

  return (
    <DashboardLayout>
      <div className="max-w-2xl mx-auto px-6 py-10 space-y-8">
        {/* Back */}
        <button onClick={() => navigate("/dashboard")}
          className="flex items-center gap-1.5 text-sm text-ink-400 hover:text-ink-100 transition-colors">
          <ArrowLeft size={16} /> Back to dashboard
        </button>

        {/* Header */}
        <div className="space-y-1">
          <h1 className="text-2xl font-bold">New research project</h1>
          <p className="text-sm text-ink-400">Run any product through 24 Nigerian consumer personas.</p>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-ink-900 border border-ink-800 rounded-xl p-1">
          {(["single","bulk"] as const).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`flex-1 py-2 text-sm font-medium rounded-lg transition-all ${
                tab === t ? "bg-naija-600 text-white shadow" : "text-ink-400 hover:text-ink-100"
              }`}
            >
              {t === "single" ? "Single project" : "Import bulk"}
            </button>
          ))}
        </div>

        {/* Content */}
        {tab === "single" ? <SingleProjectForm /> : <BulkImport />}
      </div>
    </DashboardLayout>
  );
}
