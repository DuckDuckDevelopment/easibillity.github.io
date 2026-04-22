import React, { useState, useEffect } from 'react';

const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:5000";

const DISEASE_CODES = {
  "HD": "Heart Disease and Stroke", "CA": "Cancer", "DB": "Diabetes", "OB": "Obesity",
  "AD": "Alzheimer's Disease and Other Dementias", "AR": "Arthritis", "CK": "Chronic Kidney Disease",
  "EP": "Epilepsy", "TD": "Tooth Decay and Oral Disease", "CP": "Chronic Obstructive Pulmonary Disease (COPD)",
  "MH": "Depression and Other Mental Health Disorders", "HT": "Hypertension", "AS": "Asthma",
  "SC": "High-Cost Drugs / Specialty Treatments", "LV": "Liver Disease (including Cirrhosis and Hepatitis)",
  "MS": "Multiple Sclerosis and Autoimmune Disorders", "ID": "Serious Infectious Diseases",
  "BP": "Chronic Pain and Back Disorders", "OA": "Opioid Addiction and Substance Use Disorders",
  "RG": "Rare or Genetic Disorders"
};

const STATES = [
  "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", "IL", "IN", "IA",
  "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
  "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT",
  "VA", "WA", "WV", "WI", "WY", "DC"
];

// ─── Utility: detect which "page" this tab should render ─────────────────────
const isResultsTab = () => window.location.hash === '#results';

// ─── Form Page ────────────────────────────────────────────────────────────────
const FormPage = () => {
  const [selectedCode, setSelectedCode] = useState(null);
  const [income, setIncome] = useState('');
  const [hhSize, setHhSize] = useState(1);
  const [state, setState] = useState('TX');
  const [fplPct, setFplPct] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!income || income <= 0) { setFplPct(null); return; }
    const fpl48 = [15960, 21640, 27320, 33000, 38680, 44360, 50040, 55720];
    const fplAK = [19950, 27050, 34150, 41250, 48350, 55450, 62550, 69650];
    const fplHI = [18360, 24890, 31420, 37950, 44480, 51010, 57540, 64070];
    const table = state === "AK" ? fplAK : state === "HI" ? fplHI : fpl48;
    const base = table[Math.min(hhSize - 1, 7)];
    setFplPct(((income / base) * 100).toFixed(1));
  }, [income, hhSize, state]);

  const handleHunt = async () => {
    if (!selectedCode) return setError("Please select a disease code first.");
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_URL}/api/hunt`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          code: selectedCode,
          income: parseFloat(income) || 0,
          hhSize: parseInt(hhSize),
          state: state
        }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Search failed");

      // 1. Persist results so the new tab can read them
      sessionStorage.setItem('grantResults', JSON.stringify({
        grants: data.grants,
        disease: data.disease,
        fpl_percentage: data.fpl_percentage,
        meta: { code: selectedCode, state, hhSize, fplPct }
      }));

      // 2. Open a brand-new browser tab pointed at the results hash
      window.open(window.location.pathname + '#results', '_blank');

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0d0f0e] text-[#e8ede9] font-sans selection:bg-[#b8f06a] selection:text-black">
      {/* Header */}
      <header className="border-b border-[#2a2f2b] px-12 py-8 flex items-baseline gap-4">
        <h1 className="text-[#b8f06a] text-3xl font-serif font-black tracking-tight">Easibillity</h1>
        <span className="font-mono text-[10px] text-[#6b756c] uppercase tracking-[0.2em]">Financial Assistance Finder · 2026</span>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-12">
        {/* Hero */}
        <div className="mb-12">
          <h2 className="text-4xl font-serif font-bold leading-tight mb-4">
            Find <em className="text-[#b8f06a] italic not-italic">financial aid</em><br />for your condition.
          </h2>
          <p className="text-[#6b756c] text-sm max-w-lg leading-relaxed">
            Select a disease code and provide household details to search live nonprofit and foundation grant databases.
          </p>
        </div>

        {/* Disease Selection Grid */}
        <label className="block font-mono text-[10px] uppercase text-[#6b756c] mb-3 tracking-widest">Select Disease Code</label>
        <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-5 gap-2 mb-10">
          {Object.entries(DISEASE_CODES).map(([code, name]) => (
            <button
              key={code}
              onClick={() => setSelectedCode(code)}
              className={`text-left p-3 border rounded-md transition-all group ${
                selectedCode === code
                  ? 'border-[#b8f06a] bg-[#b8f06a]/5'
                  : 'border-[#2a2f2b] bg-[#141714] hover:border-[#b8f06a]/40'
              }`}
            >
              <span className={`block font-mono text-lg font-bold mb-1 ${selectedCode === code ? 'text-[#b8f06a]' : 'text-[#6b756c] group-hover:text-[#b8f06a]'}`}>
                {code}
              </span>
              <span className="text-[10px] leading-tight text-[#6b756c] block uppercase">{name.split(' ')[0]}...</span>
            </button>
          ))}
        </div>

        {/* Input Section */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="flex flex-col gap-2">
            <label className="font-mono text-[10px] uppercase text-[#6b756c]">Annual Income ($)</label>
            <input
              type="number"
              placeholder="e.g. 45000"
              className="bg-[#141714] border border-[#2a2f2b] rounded-lg p-3 outline-none focus:border-[#b8f06a] transition-colors text-[#e8ede9]"
              value={income}
              onChange={(e) => setIncome(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-2">
            <label className="font-mono text-[10px] uppercase text-[#6b756c]">Household Size</label>
            <input
              type="number"
              min="1" max="8"
              className="bg-[#141714] border border-[#2a2f2b] rounded-lg p-3 outline-none focus:border-[#b8f06a] transition-colors text-[#e8ede9]"
              value={hhSize}
              onChange={(e) => setHhSize(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-2">
            <label className="font-mono text-[10px] uppercase text-[#6b756c]">State</label>
            <select
              className="bg-[#141714] border border-[#2a2f2b] rounded-lg p-3 outline-none focus:border-[#b8f06a] appearance-none cursor-pointer text-[#e8ede9]"
              value={state}
              onChange={(e) => setState(e.target.value)}
            >
              {STATES.map(s => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
        </div>

        {/* FPL Badge */}
        <div className={`inline-flex items-center gap-3 px-4 py-2 rounded-full border mb-10 font-mono text-xs transition-colors ${
          !fplPct ? 'border-[#2a2f2b] text-[#6b756c]' : 'border-[#b8f06a]/30 bg-[#b8f06a]/5 text-[#b8f06a]'
        }`}>
          <span>FPL %</span>
          <span className="text-sm font-bold">{fplPct ? `${fplPct}%` : '—'}</span>
          <span className="text-[10px] opacity-60">of federal poverty level</span>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:gap-4 mb-4">
          <button
            onClick={handleHunt}
            disabled={loading}
            className="w-full md:w-auto flex items-center justify-center gap-3 bg-[#b8f06a] text-black px-10 py-4 rounded-xl font-bold hover:translate-y-[-2px] hover:shadow-[0_8px_30px_rgb(184,240,106,0.2)] active:translate-y-0 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <>
                <div className="w-4 h-4 border-2 border-black/20 border-t-black rounded-full animate-spin" />
                Searching Live Databases...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                  <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
                </svg>
                Hunt for Grants
              </>
            )}
          </button>
          <a
            href="./dashboard.html"
            target="_blank"
            rel="noreferrer"
            className="w-full md:w-auto inline-flex items-center justify-center gap-2 border border-[#2a2f2b] text-[#e8ede9] px-10 py-4 rounded-xl font-bold hover:bg-[#141714] hover:border-[#b8f06a] transition-all"
          >
            View Hospital Dashboard
          </a>
        </div>

        {error && (
          <div className="mt-8 p-4 bg-red-500/10 border border-red-500/30 text-red-500 rounded-lg text-sm font-mono">
            Error: {error}
          </div>
        )}
      </main>

      <footer className="max-w-4xl mx-auto px-6 py-12 text-center text-[#6b756c] text-[10px] leading-relaxed border-t border-[#2a2f2b]">
        Medical Disclaimer: This tool provides search results for educational purposes only. Always consult with a healthcare professional or social worker before applying for financial aid. Verify all program eligibility directly on the sponsoring organization's website.
      </footer>
    </div>
  );
};

// ─── Results Page ─────────────────────────────────────────────────────────────
const ResultsPage = () => {
  // Read results that FormPage saved to sessionStorage before opening this tab
  const [results] = useState(() => {
    const stored = sessionStorage.getItem('grantResults');
    return stored ? JSON.parse(stored) : null;
  });

  if (!results) {
    return (
      <div className="min-h-screen bg-[#0d0f0e] text-[#e8ede9] flex items-center justify-center font-sans">
        <p className="text-[#6b756c] font-mono text-sm">No results found. Please run a search first.</p>
      </div>
    );
  }

  const { grants, disease, meta } = results;

  return (
    <div className="min-h-screen bg-[#0d0f0e] text-[#e8ede9] font-sans selection:bg-[#b8f06a] selection:text-black">
      {/* Header */}
      <header className="border-b border-[#2a2f2b] px-12 py-8 flex items-baseline gap-4">
        <h1 className="text-[#b8f06a] text-3xl font-serif font-black tracking-tight">ClearPath</h1>
        <span className="font-mono text-[10px] text-[#6b756c] uppercase tracking-[0.2em]">Financial Assistance Finder · 2026</span>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-12">
        {/* Results header */}
        <div className="flex items-center justify-between mb-8">
          <h3 className="text-xl font-serif font-bold">Available Programs</h3>
          <div className="flex items-center gap-6 font-mono text-[10px] text-[#6b756c]">
            {meta?.fplPct && (
              <span>FPL <span className="text-[#b8f06a] font-bold">{meta.fplPct}%</span></span>
            )}
            <span>{disease}</span>
            <span>{grants.length} results found</span>
          </div>
        </div>

        {/* Grant cards — identical to original */}
        <div className="space-y-6">
          {grants.length === 0 ? (
            <p className="text-[#6b756c] text-sm py-16 text-center">No programs found. Try a different code.</p>
          ) : grants.map((grant, i) => (
            <div
              key={i}
              className="group relative p-6 border border-[#2a2f2b] bg-[#141714] rounded-2xl hover:border-[#b8f06a]/40 transition-all animate-in fade-in slide-in-from-bottom-4 duration-500"
              style={{ animationDelay: `${i * 100}ms` }}
            >
              <div className="absolute left-0 top-0 bottom-0 w-1 bg-[#b8f06a] opacity-0 group-hover:opacity-100 transition-opacity rounded-l-2xl" />
              <div className="font-mono text-[10px] text-[#6af0c8] uppercase tracking-widest mb-2">Verified Foundation</div>
              <h4 className="text-lg font-bold mb-2 group-hover:text-[#b8f06a] transition-colors">{grant.title}</h4>
              <p className="text-[#6b756c] text-sm leading-relaxed mb-6 line-clamp-3">
                {grant.description}
              </p>
              <div className="flex items-center gap-4">
                <span className="px-3 py-1 bg-[#b8f06a]/10 border border-[#b8f06a]/20 text-[#b8f06a] text-[10px] font-mono rounded-full uppercase">
                  {grant.type || "Nonprofit"}
                </span>
                <a
                  href={grant.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs font-bold text-[#e8ede9] underline decoration-[#b8f06a] underline-offset-4 hover:text-[#b8f06a] transition-colors"
                >
                  Visit Program Site ↗
                </a>
              </div>
            </div>
          ))}
        </div>
      </main>

      <footer className="max-w-4xl mx-auto px-6 py-12 text-center text-[#6b756c] text-[10px] leading-relaxed border-t border-[#2a2f2b]">
        Medical Disclaimer: This tool provides search results for educational purposes only. Always consult with a healthcare professional or social worker before applying for financial aid. Verify all program eligibility directly on the sponsoring organization's website.
      </footer>
    </div>
  );
};

// ─── Root: hash decides which page this tab renders ──────────────────────────
const App = () => {
  const [page, setPage] = useState(isResultsTab() ? 'results' : 'form');

  // Handle browser back/forward between hash states in the same tab
  useEffect(() => {
    const onHash = () => setPage(isResultsTab() ? 'results' : 'form');
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);

  return page === 'results' ? <ResultsPage /> : <FormPage />;
};

export default App;
