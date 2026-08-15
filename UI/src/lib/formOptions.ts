// Ported from Application/app.py's sidebar inputs -- the two Streamlit
// copies had drifted here (Multi Page Test/Home.py used different horizon
// labels); Application/app.py's set is kept as canonical.

export const INSTRUMENT_OPTIONS = ["Stocks", "Mutual Funds/ETFs", "Gold/Commodities"] as const;

// Must match backend/backend/agents/nodes/analyst.py's RISK_SLABS keys.
export const RISK_OPTIONS = [
  "Ultra Conservative",
  "Conservative",
  "Moderate",
  "Aggressive",
  "Very Aggressive",
  "Speculative / High Alpha",
] as const;

export const RETURN_OPTIONS = [...Array.from({ length: 25 }, (_, i) => String(i + 6)), "30+"];

export const HORIZON_OPTIONS = [
  "Short Term (<1 yr)",
  "Medium Term (3-5 yrs)",
  "Long Term (5+ yrs)",
] as const;
