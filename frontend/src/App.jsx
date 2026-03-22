import { useState, useEffect, useRef } from 'react'

// In dev (no VITE_API_URL): calls /api/analyze → Vite proxies to localhost:8000/analyze
// In prod (VITE_API_URL set): calls https://your-backend.railway.app/analyze
const API_URL = import.meta.env.VITE_API_URL ?? '/api'

// ─── Helpers ────────────────────────────────────────────────────────────────

function gradeColor(grade) {
  if (!grade) return '#6B7280'
  const g = grade.toUpperCase()
  if (g.startsWith('A')) return '#2DD4A0'
  if (g.startsWith('B')) return '#4B83EF'
  if (g.startsWith('C')) return '#F5B942'
  return '#F16060'
}

function gradeBg(grade) {
  if (!grade) return 'rgba(107,114,128,0.12)'
  const g = grade.toUpperCase()
  if (g.startsWith('A')) return 'rgba(45,212,160,0.12)'
  if (g.startsWith('B')) return 'rgba(75,131,239,0.12)'
  if (g.startsWith('C')) return 'rgba(245,185,66,0.12)'
  return 'rgba(241,96,96,0.12)'
}

// ─── GradeBadge ─────────────────────────────────────────────────────────────

function GradeBadge({ grade, size = 'sm' }) {
  const color = gradeColor(grade)
  const bg = gradeBg(grade)
  const padClass = size === 'lg'
    ? 'px-3 py-1.5 text-base font-bold tracking-wide'
    : 'px-2 py-0.5 text-xs font-bold tracking-wider'
  return (
    <span
      className={`inline-flex items-center rounded-md border ${padClass}`}
      style={{ color, borderColor: `${color}40`, backgroundColor: bg }}
    >
      {grade ?? '—'}
    </span>
  )
}

// ─── LandingForm ────────────────────────────────────────────────────────────

function LandingForm({ onSubmit, loading }) {
  const [form, setForm] = useState({ name: '', email: '', website_url: '' })
  const [errors, setErrors] = useState({})

  function validate() {
    const e = {}
    if (!form.name.trim()) e.name = 'Name is required'
    if (!form.email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) e.email = 'Valid email required'
    if (!form.website_url.trim()) e.website_url = 'Website URL is required'
    return e
  }

  function handleSubmit(e) {
    e.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) { setErrors(errs); return }
    setErrors({})
    onSubmit(form)
  }

  return (
    <div className="min-h-screen flex flex-col" style={{ background: '#060A14' }}>
      {/* Nav */}
      <nav className="flex items-center justify-between px-8 py-5 border-b" style={{ borderColor: '#1A2540' }}>
        <div className="flex items-center gap-2.5">
          <div className="w-7 h-7 rounded-lg flex items-center justify-center text-white font-bold text-sm" style={{ background: '#4B83EF' }}>P</div>
          <span className="text-white font-semibold text-sm tracking-wide">PersonalBranding.com</span>
        </div>
        <a href="https://personalbranding.com" target="_blank" rel="noreferrer"
          className="text-xs font-medium px-3.5 py-1.5 rounded-lg border transition-colors"
          style={{ color: '#8B9DBF', borderColor: '#1A2540' }}>
          Learn more →
        </a>
      </nav>

      {/* Hero */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 py-16">
        {/* Badge */}
        <div className="mb-6 inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border text-xs font-medium"
          style={{ borderColor: '#2A4E99', background: 'rgba(75,131,239,0.08)', color: '#6FA0FF' }}>
          <span className="w-1.5 h-1.5 rounded-full bg-accent-bright animate-pulse" style={{ background: '#4B83EF' }} />
          Free Competitive Analysis — 60 seconds
        </div>

        <h1 className="text-4xl sm:text-5xl font-bold text-center leading-tight mb-4 max-w-2xl"
          style={{ color: '#E2E8F5' }}>
          See how your firm stacks up<br />
          <span style={{ color: '#4B83EF' }}>against your competitors</span>
        </h1>

        <p className="text-center max-w-lg mb-10 leading-relaxed" style={{ color: '#8B9DBF' }}>
          Enter your website and we'll analyze your media visibility versus your
          top regional competitors — in under a minute.
        </p>

        {/* Form card */}
        <div className="w-full max-w-md rounded-2xl border p-8"
          style={{ background: '#0D1426', borderColor: '#1A2540' }}>
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Name */}
            <div>
              <label className="block text-xs font-semibold mb-1.5 uppercase tracking-wider" style={{ color: '#8B9DBF' }}>
                Your Name
              </label>
              <input
                type="text"
                placeholder="Jane Smith"
                value={form.name}
                onChange={e => setForm(f => ({ ...f, name: e.target.value }))}
                className="w-full rounded-lg px-4 py-2.5 text-sm outline-none transition-colors"
                style={{
                  background: '#111829',
                  border: `1px solid ${errors.name ? '#F16060' : '#1A2540'}`,
                  color: '#E2E8F5',
                }}
              />
              {errors.name && <p className="mt-1 text-xs" style={{ color: '#F16060' }}>{errors.name}</p>}
            </div>

            {/* Email */}
            <div>
              <label className="block text-xs font-semibold mb-1.5 uppercase tracking-wider" style={{ color: '#8B9DBF' }}>
                Work Email
              </label>
              <input
                type="email"
                placeholder="jane@smithlaw.com"
                value={form.email}
                onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
                className="w-full rounded-lg px-4 py-2.5 text-sm outline-none transition-colors"
                style={{
                  background: '#111829',
                  border: `1px solid ${errors.email ? '#F16060' : '#1A2540'}`,
                  color: '#E2E8F5',
                }}
              />
              {errors.email && <p className="mt-1 text-xs" style={{ color: '#F16060' }}>{errors.email}</p>}
            </div>

            {/* URL */}
            <div>
              <label className="block text-xs font-semibold mb-1.5 uppercase tracking-wider" style={{ color: '#8B9DBF' }}>
                Your Firm's Website
              </label>
              <input
                type="url"
                placeholder="https://yourfirm.com"
                value={form.website_url}
                onChange={e => setForm(f => ({ ...f, website_url: e.target.value }))}
                className="w-full rounded-lg px-4 py-2.5 text-sm outline-none transition-colors"
                style={{
                  background: '#111829',
                  border: `1px solid ${errors.website_url ? '#F16060' : '#1A2540'}`,
                  color: '#E2E8F5',
                }}
              />
              {errors.website_url && <p className="mt-1 text-xs" style={{ color: '#F16060' }}>{errors.website_url}</p>}
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 py-3 rounded-xl font-semibold text-sm text-white transition-all duration-200 disabled:opacity-60"
              style={{
                background: loading ? '#2A4E99' : 'linear-gradient(135deg, #3B73DF 0%, #4B83EF 100%)',
                boxShadow: loading ? 'none' : '0 0 24px rgba(75,131,239,0.25)',
              }}
            >
              {loading ? 'Analyzing…' : 'Analyze My Firm →'}
            </button>
          </form>

          <p className="mt-5 text-center text-xs" style={{ color: '#4A5878' }}>
            No credit card. No obligation. Results sent to your email.
          </p>
        </div>

        {/* Social proof */}
        <div className="mt-10 flex items-center gap-6 flex-wrap justify-center">
          {['100+ law firms analyzed', 'Free competitive report', 'Results in ~60 seconds'].map(item => (
            <div key={item} className="flex items-center gap-1.5 text-xs" style={{ color: '#4A5878' }}>
              <svg className="w-3.5 h-3.5" style={{ color: '#2DD4A0' }} fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" />
              </svg>
              {item}
            </div>
          ))}
        </div>
      </main>
    </div>
  )
}

// ─── LoadingState ────────────────────────────────────────────────────────────

const STEPS = [
  { label: 'Analyzing your website',         detail: 'Scraping content & metadata',        delay: 0  },
  { label: 'Identifying top competitors',    detail: 'Searching regional market',          delay: 12 },
  { label: 'Measuring media coverage',       detail: 'Counting news & PR mentions',        delay: 28 },
  { label: 'Building your report',           detail: 'Mapping insights to your market',    delay: 48 },
]

function LoadingState({ firmHint }) {
  const [elapsed, setElapsed] = useState(0)
  const startRef = useRef(Date.now())

  useEffect(() => {
    const id = setInterval(() => {
      setElapsed((Date.now() - startRef.current) / 1000)
    }, 300)
    return () => clearInterval(id)
  }, [])

  const activeStep = STEPS.reduce((acc, s, i) => elapsed >= s.delay ? i : acc, 0)
  const progressPct = Math.min((elapsed / 65) * 100, 96)

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4" style={{ background: '#060A14' }}>
      {/* Logo */}
      <div className="mb-12 flex items-center gap-2.5">
        <div className="w-8 h-8 rounded-xl flex items-center justify-center text-white font-bold" style={{ background: '#4B83EF' }}>P</div>
        <span className="font-semibold text-sm tracking-wide" style={{ color: '#8B9DBF' }}>PersonalBranding.com</span>
      </div>

      {/* Spinner */}
      <div className="relative mb-8">
        <div className="w-16 h-16 rounded-full border-4 animate-spin"
          style={{ borderColor: '#1A2540', borderTopColor: '#4B83EF' }} />
        <div className="absolute inset-0 flex items-center justify-center text-xl">🔍</div>
      </div>

      <h2 className="text-xl font-semibold mb-2 text-center" style={{ color: '#E2E8F5' }}>
        {firmHint ? `Analyzing ${firmHint}` : 'Analyzing your firm'}
      </h2>
      <p className="text-sm mb-8" style={{ color: '#4A5878' }}>
        This takes about 60 seconds — please keep this tab open.
      </p>

      {/* Progress bar */}
      <div className="w-full max-w-sm mb-8">
        <div className="h-1.5 rounded-full overflow-hidden" style={{ background: '#1A2540' }}>
          <div
            className="h-full rounded-full transition-all duration-500"
            style={{ width: `${progressPct}%`, background: 'linear-gradient(90deg, #3B73DF, #6FA0FF)' }}
          />
        </div>
        <p className="mt-2 text-right text-xs" style={{ color: '#4A5878' }}>{Math.round(progressPct)}%</p>
      </div>

      {/* Steps */}
      <div className="w-full max-w-sm space-y-3">
        {STEPS.map((step, i) => {
          const done = i < activeStep
          const active = i === activeStep
          return (
            <div key={i} className="flex items-start gap-3">
              {/* Icon */}
              <div className="mt-0.5 flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center"
                style={{
                  background: done ? 'rgba(45,212,160,0.15)' : active ? 'rgba(75,131,239,0.15)' : '#111829',
                  border: `1px solid ${done ? '#2DD4A0' : active ? '#4B83EF' : '#1A2540'}`,
                }}>
                {done
                  ? <svg className="w-3 h-3" fill="#2DD4A0" viewBox="0 0 20 20"><path fillRule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" /></svg>
                  : active
                    ? <div className="w-2 h-2 rounded-full animate-pulse" style={{ background: '#4B83EF' }} />
                    : <div className="w-1.5 h-1.5 rounded-full" style={{ background: '#1A2540' }} />
                }
              </div>
              {/* Text */}
              <div>
                <p className="text-sm font-medium leading-tight"
                  style={{ color: done ? '#2DD4A0' : active ? '#E2E8F5' : '#4A5878' }}>
                  {step.label}
                </p>
                {active && (
                  <p className="text-xs mt-0.5" style={{ color: '#4A5878' }}>{step.detail}</p>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ─── CoverageChart ───────────────────────────────────────────────────────────

function CoverageChart({ prospect, competitors }) {
  const [animated, setAnimated] = useState(false)
  useEffect(() => { const t = setTimeout(() => setAnimated(true), 100); return () => clearTimeout(t) }, [])

  const allFirms = [
    { ...prospect, isProspect: true },
    ...competitors,
  ]
  const maxCount = Math.max(...allFirms.map(f => f.news_mention_count ?? 0), 1)

  // Scale ticks
  const ticks = []
  const tickCount = 5
  for (let i = 0; i <= tickCount; i++) {
    ticks.push(Math.round((maxCount / tickCount) * i))
  }

  return (
    <div className="rounded-2xl border p-6 sm:p-8" style={{ background: '#0D1426', borderColor: '#1A2540' }}>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="font-semibold text-base" style={{ color: '#E2E8F5' }}>Media Coverage Comparison</h3>
          <p className="text-xs mt-0.5" style={{ color: '#4A5878' }}>News articles &amp; PR mentions — past 2–3 years</p>
        </div>
        <div className="flex items-center gap-3 text-xs" style={{ color: '#4A5878' }}>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 rounded" style={{ background: '#4B83EF', display: 'inline-block' }} />
            Your firm
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-3 h-0.5 rounded" style={{ background: '#2A3F6A', display: 'inline-block' }} />
            Competitors
          </span>
        </div>
      </div>

      {/* Chart rows */}
      <div className="space-y-2.5">
        {allFirms.map((firm, i) => {
          const count = firm.news_mention_count ?? 0
          const pct = Math.max((count / maxCount) * 100, count > 0 ? 2 : 0)
          const isProspect = firm.isProspect
          const color = isProspect ? '#4B83EF' : gradeColor(firm.media_grade)
          const barBg = isProspect
            ? 'linear-gradient(90deg, #3B73DF, #6FA0FF)'
            : `${color}55`

          return (
            <div
              key={i}
              className="group flex items-center gap-3 rounded-xl px-3 py-2.5 transition-colors"
              style={{
                background: isProspect ? 'rgba(75,131,239,0.06)' : 'transparent',
                border: `1px solid ${isProspect ? '#2A4E99' : 'transparent'}`,
              }}
            >
              {/* Firm name */}
              <div className="w-40 sm:w-52 flex-shrink-0">
                <div className="flex items-center gap-1.5">
                  {isProspect && (
                    <span className="text-xs font-bold" style={{ color: '#4B83EF' }}>★</span>
                  )}
                  <span
                    className="text-xs font-medium leading-tight truncate"
                    style={{ color: isProspect ? '#E2E8F5' : '#8B9DBF' }}
                    title={firm.firm_name}
                  >
                    {firm.firm_name}
                  </span>
                </div>
                {isProspect && (
                  <span className="text-xs ml-4" style={{ color: '#4A5878' }}>Your firm</span>
                )}
              </div>

              {/* Bar */}
              <div className="flex-1 h-6 rounded overflow-hidden" style={{ background: '#0A1020' }}>
                <div
                  className="h-full rounded"
                  style={{
                    width: animated ? `${pct}%` : '0%',
                    background: barBg,
                    transition: `width 1s cubic-bezier(0.4,0,0.2,1) ${i * 80}ms`,
                    minWidth: count > 0 ? '4px' : '0',
                    boxShadow: isProspect ? '0 0 12px rgba(75,131,239,0.4)' : 'none',
                  }}
                />
              </div>

              {/* Count + Grade */}
              <div className="flex items-center gap-2 flex-shrink-0">
                <span className="text-xs font-semibold w-6 text-right" style={{ color: isProspect ? '#E2E8F5' : '#8B9DBF' }}>
                  {count}
                </span>
                <GradeBadge grade={firm.media_grade} />
              </div>
            </div>
          )
        })}
      </div>

      {/* X-axis label */}
      <div className="mt-4 flex justify-between text-xs" style={{ color: '#2A3F6A' }}>
        <span>0</span>
        <span style={{ color: '#4A5878' }}>← News mentions →</span>
        <span>{maxCount}</span>
      </div>
    </div>
  )
}

// ─── StatCard ────────────────────────────────────────────────────────────────

function StatCard({ label, value, sub, accent }) {
  return (
    <div className="rounded-xl border p-4" style={{ background: '#0D1426', borderColor: '#1A2540' }}>
      <p className="text-xs font-semibold uppercase tracking-wider mb-2" style={{ color: '#4A5878' }}>{label}</p>
      <p className="text-2xl font-bold leading-none mb-1" style={{ color: accent ?? '#E2E8F5' }}>{value}</p>
      {sub && <p className="text-xs" style={{ color: '#4A5878' }}>{sub}</p>}
    </div>
  )
}

// ─── InsightBox ──────────────────────────────────────────────────────────────

function InsightBox({ title, text, accent }) {
  return (
    <div
      className="rounded-xl border-l-4 p-5"
      style={{
        borderColor: accent,
        background: `${accent}0D`,
        border: `1px solid ${accent}30`,
        borderLeftColor: accent,
        borderLeftWidth: 4,
      }}
    >
      <p className="text-xs font-bold uppercase tracking-widest mb-2" style={{ color: accent }}>{title}</p>
      <p className="text-sm leading-relaxed" style={{ color: '#C4D0E8' }}>{text}</p>
    </div>
  )
}

// ─── ResultsDashboard ────────────────────────────────────────────────────────

function ResultsDashboard({ data, onReset }) {
  const { prospect, competitors = [], analysis = {} } = data

  if (!prospect) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ background: '#060A14' }}>
        <div className="text-center">
          <p className="mb-4" style={{ color: '#F16060' }}>Unexpected response format.</p>
          <button onClick={onReset} className="text-sm underline" style={{ color: '#4B83EF' }}>Try again</button>
        </div>
      </div>
    )
  }

  const gradeColor_ = gradeColor(prospect.media_grade)
  const topCompetitorCount = analysis.top_competitor_mention_count ?? 0
  const prospectCount = prospect.news_mention_count ?? 0
  const ratio = analysis.prospect_to_top_competitor_ratio ?? (topCompetitorCount > prospectCount
    ? `${Math.round(topCompetitorCount / Math.max(prospectCount, 1))}x behind`
    : 'Leading')

  return (
    <div className="min-h-screen" style={{ background: '#060A14' }}>
      {/* Header */}
      <div className="border-b" style={{ borderColor: '#1A2540' }}>
        <div className="max-w-4xl mx-auto px-4 sm:px-6 py-5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg flex items-center justify-center text-white font-bold text-sm" style={{ background: '#4B83EF' }}>P</div>
            <span className="text-white font-semibold text-sm tracking-wide">PersonalBranding.com</span>
          </div>
          <button
            onClick={onReset}
            className="text-xs font-medium px-3.5 py-1.5 rounded-lg border transition-colors"
            style={{ color: '#8B9DBF', borderColor: '#1A2540' }}
          >
            ← New analysis
          </button>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10 space-y-6">

        {/* Firm hero */}
        <div
          className="rounded-2xl border p-6 sm:p-8 relative overflow-hidden"
          style={{ background: '#0D1426', borderColor: '#1A2540' }}
        >
          {/* Glow */}
          <div className="absolute -top-16 -right-16 w-64 h-64 rounded-full opacity-10 pointer-events-none"
            style={{ background: 'radial-gradient(circle, #4B83EF 0%, transparent 70%)' }} />

          <div className="relative flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-xs font-semibold uppercase tracking-widest" style={{ color: '#4A5878' }}>
                  Competitive Media Analysis
                </span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-bold leading-tight" style={{ color: '#E2E8F5' }}>
                {prospect.firm_name}
              </h1>
              <div className="flex flex-wrap items-center gap-2 mt-2">
                {prospect.city && (
                  <span className="text-sm" style={{ color: '#8B9DBF' }}>
                    📍 {prospect.city}{prospect.state ? `, ${prospect.state}` : ''}
                  </span>
                )}
                {prospect.practice_area && (
                  <span className="text-xs px-2.5 py-1 rounded-full border"
                    style={{ color: '#6FA0FF', borderColor: '#2A4E99', background: 'rgba(75,131,239,0.08)' }}>
                    {prospect.practice_area}
                  </span>
                )}
              </div>
            </div>
            <div className="flex items-center gap-3 flex-shrink-0">
              <div className="text-right">
                <p className="text-xs font-semibold uppercase tracking-wider mb-1" style={{ color: '#4A5878' }}>Your Grade</p>
                <GradeBadge grade={prospect.media_grade} size="lg" />
              </div>
            </div>
          </div>

          {/* Quick stats strip */}
          <div className="mt-6 pt-5 border-t grid grid-cols-3 sm:grid-cols-3 gap-4"
            style={{ borderColor: '#1A2540' }}>
            <div>
              <p className="text-xs" style={{ color: '#4A5878' }}>News mentions</p>
              <p className="text-xl font-bold mt-0.5" style={{ color: gradeColor_ }}>
                {prospectCount}
              </p>
            </div>
            <div>
              <p className="text-xs" style={{ color: '#4A5878' }}>PR releases</p>
              <p className="text-xl font-bold mt-0.5" style={{ color: '#E2E8F5' }}>
                {prospect.pr_wire_count ?? 0}
              </p>
            </div>
            <div>
              <p className="text-xs" style={{ color: '#4A5878' }}>Google rating</p>
              <p className="text-xl font-bold mt-0.5" style={{ color: '#E2E8F5' }}>
                {prospect.google_rating ? `${prospect.google_rating} ⭐` : '—'}
              </p>
            </div>
          </div>
        </div>

        {/* Main chart */}
        <CoverageChart prospect={prospect} competitors={competitors} />

        {/* Stats grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <StatCard
            label="Your coverage"
            value={prospectCount}
            sub="news mentions"
            accent={gradeColor_}
          />
          <StatCard
            label="Top competitor"
            value={topCompetitorCount}
            sub={analysis.top_competitor_name ?? 'competitor'}
          />
          <StatCard
            label="Visibility gap"
            value={ratio}
            sub="vs. top competitor"
            accent={topCompetitorCount > prospectCount ? '#F5B942' : '#2DD4A0'}
          />
          <StatCard
            label="Google reviews"
            value={prospect.google_review_count ?? '—'}
            sub={prospect.google_rating ? `${prospect.google_rating} avg rating` : 'reviews'}
          />
        </div>

        {/* Insight boxes */}
        {analysis.visibility_gap_summary && (
          <InsightBox
            title="Key Finding"
            text={analysis.visibility_gap_summary}
            accent="#4B83EF"
          />
        )}
        {analysis.prospect_strengths_summary && (
          <InsightBox
            title="Your Strengths"
            text={analysis.prospect_strengths_summary}
            accent="#2DD4A0"
          />
        )}

        {/* Competitor breakdown */}
        {competitors.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold mb-3" style={{ color: '#8B9DBF' }}>
              TOP {competitors.length} COMPETITORS IDENTIFIED
            </h3>
            <div className="space-y-2">
              {competitors.map((c, i) => (
                <div key={i}
                  className="rounded-xl border px-4 py-3 flex items-start justify-between gap-4"
                  style={{ background: '#0D1426', borderColor: '#1A2540' }}>
                  <div className="flex items-start gap-3 min-w-0">
                    <span className="flex-shrink-0 w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold mt-0.5"
                      style={{ background: '#111829', color: '#4A5878' }}>
                      {i + 1}
                    </span>
                    <div className="min-w-0">
                      <p className="text-sm font-medium truncate" style={{ color: '#C4D0E8' }}>{c.firm_name}</p>
                      {c.key_differentiator && (
                        <p className="text-xs mt-0.5 line-clamp-1" style={{ color: '#4A5878' }}>{c.key_differentiator}</p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <span className="text-xs" style={{ color: '#4A5878' }}>{c.news_mention_count ?? 0} mentions</span>
                    <GradeBadge grade={c.media_grade} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Article angle ideas */}
        {analysis.article_angle_ideas?.length > 0 && (
          <div className="rounded-2xl border p-6" style={{ background: '#0D1426', borderColor: '#1A2540' }}>
            <h3 className="font-semibold text-sm mb-4" style={{ color: '#E2E8F5' }}>
              💡 Article Angle Ideas for {prospect.firm_name}
            </h3>
            <div className="space-y-2">
              {analysis.article_angle_ideas.map((idea, i) => (
                <div key={i} className="flex items-start gap-2.5">
                  <span className="flex-shrink-0 text-xs font-bold mt-0.5" style={{ color: '#4B83EF' }}>{i + 1}.</span>
                  <p className="text-sm" style={{ color: '#8B9DBF' }}>{idea}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* CTA */}
        <div
          className="rounded-2xl border p-8 text-center relative overflow-hidden"
          style={{ background: 'linear-gradient(135deg, #0D1426 0%, #0A1733 100%)', borderColor: '#2A4E99' }}
        >
          <div className="absolute inset-0 opacity-5 pointer-events-none"
            style={{ background: 'radial-gradient(ellipse at center, #4B83EF 0%, transparent 70%)' }} />
          <div className="relative">
            <p className="text-xs font-bold uppercase tracking-widest mb-3" style={{ color: '#4B83EF' }}>
              Ready to close the gap?
            </p>
            <h3 className="text-xl font-bold mb-2" style={{ color: '#E2E8F5' }}>
              Get featured in national media — in 30 days
            </h3>
            <p className="text-sm mb-6 max-w-sm mx-auto leading-relaxed" style={{ color: '#8B9DBF' }}>
              We write and place articles for {prospect.firm_name} on outlets like MSN, Yahoo, and
              national legal publications — permanently boosting your visibility.
            </p>
            <a
              href="https://personalbranding.com"
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-2 px-6 py-3 rounded-xl font-semibold text-sm text-white transition-all"
              style={{
                background: 'linear-gradient(135deg, #3B73DF 0%, #4B83EF 100%)',
                boxShadow: '0 0 32px rgba(75,131,239,0.35)',
              }}
            >
              Book a Strategy Call →
            </a>
          </div>
        </div>

        {/* Footer */}
        <p className="text-center text-xs pb-6" style={{ color: '#2A3F6A' }}>
          Analysis prepared by PersonalBranding.com · {analysis.report_month_year ?? new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
        </p>
      </div>
    </div>
  )
}

// ─── ErrorState ──────────────────────────────────────────────────────────────

function ErrorState({ message, onReset }) {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-4" style={{ background: '#060A14' }}>
      <div className="text-4xl mb-4">⚠️</div>
      <h2 className="text-lg font-semibold mb-2" style={{ color: '#E2E8F5' }}>Analysis Failed</h2>
      <p className="text-sm mb-6 text-center max-w-sm" style={{ color: '#8B9DBF' }}>
        {message || 'Something went wrong. Please try again.'}
      </p>
      <button
        onClick={onReset}
        className="px-5 py-2.5 rounded-xl font-semibold text-sm text-white"
        style={{ background: '#4B83EF' }}
      >
        ← Try Again
      </button>
    </div>
  )
}

// ─── App ─────────────────────────────────────────────────────────────────────

export default function App() {
  const [view, setView] = useState('form')   // 'form' | 'loading' | 'results' | 'error'
  const [results, setResults] = useState(null)
  const [error, setError] = useState(null)
  const [firmHint, setFirmHint] = useState('')

  async function handleSubmit(form) {
    setFirmHint(new URL(form.website_url.startsWith('http') ? form.website_url : `https://${form.website_url}`).hostname.replace('www.', ''))
    setView('loading')
    setError(null)

    try {
      const res = await fetch(`${API_URL}/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || `Server error ${res.status}`)
      }

      const json = await res.json()
      setResults(json.data)
      setView('results')
    } catch (err) {
      setError(err.message)
      setView('error')
    }
  }

  function reset() {
    setView('form')
    setResults(null)
    setError(null)
  }

  if (view === 'loading') return <LoadingState firmHint={firmHint} />
  if (view === 'results') return <ResultsDashboard data={results} onReset={reset} />
  if (view === 'error')   return <ErrorState message={error} onReset={reset} />
  return <LandingForm onSubmit={handleSubmit} loading={false} />
}
