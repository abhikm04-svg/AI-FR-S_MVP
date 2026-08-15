import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCreateSession } from "../hooks/useSessions";
import {
  HORIZON_OPTIONS,
  INSTRUMENT_OPTIONS,
  RETURN_OPTIONS,
  RISK_OPTIONS,
} from "../lib/formOptions";

export function ProfileSetup() {
  const navigate = useNavigate();
  const createSession = useCreateSession();

  const [instruments, setInstruments] = useState<string[]>(["Stocks", "Mutual Funds/ETFs"]);
  const [allowRange, setAllowRange] = useState(false);
  const [riskSingle, setRiskSingle] = useState<string>(RISK_OPTIONS[2]); // "Moderate"
  const [riskStart, setRiskStart] = useState<string>(RISK_OPTIONS[1]); // "Conservative"
  const [riskEnd, setRiskEnd] = useState<string>(RISK_OPTIONS[2]); // "Moderate"
  const [targetReturn, setTargetReturn] = useState("12");
  const [horizon, setHorizon] = useState<string>(HORIZON_OPTIONS[2]);
  const [goal, setGoal] = useState("Wealth Creation");
  const [capital, setCapital] = useState("");

  function toggleInstrument(name: string) {
    setInstruments((prev) => (prev.includes(name) ? prev.filter((i) => i !== name) : [...prev, name]));
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (instruments.length === 0) return;

    const session = await createSession.mutateAsync({
      instruments,
      risk: allowRange ? [riskStart, riskEnd] : riskSingle,
      target_return: targetReturn,
      horizon,
      goal,
      capital: capital ? Number(capital) : undefined,
    });

    navigate(`/analysis/${session.id}`);
  }

  return (
    <div>
      <h1>🇮🇳 FinAgents India: Investor Profile</h1>
      <form onSubmit={handleSubmit} className="card">
        <fieldset>
          <legend>Investment Preference</legend>
          {INSTRUMENT_OPTIONS.map((option) => (
            <label key={option} style={{ display: "block" }}>
              <input
                type="checkbox"
                checked={instruments.includes(option)}
                onChange={() => toggleInstrument(option)}
              />
              {" " + option}
            </label>
          ))}
          {instruments.length === 0 && (
            <p role="alert">Select at least one investment type.</p>
          )}
        </fieldset>

        <fieldset>
          <legend>Risk Appetite</legend>
          <label>
            <input
              type="checkbox"
              checked={allowRange}
              onChange={(e) => setAllowRange(e.target.checked)}
            />
            {" Allow Range Selection"}
          </label>
          {allowRange ? (
            <div style={{ display: "flex", gap: 12 }}>
              <label>
                From
                <select value={riskStart} onChange={(e) => setRiskStart(e.target.value)}>
                  {RISK_OPTIONS.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                To
                <select value={riskEnd} onChange={(e) => setRiskEnd(e.target.value)}>
                  {RISK_OPTIONS.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          ) : (
            <label>
              <select value={riskSingle} onChange={(e) => setRiskSingle(e.target.value)}>
                {RISK_OPTIONS.map((r) => (
                  <option key={r} value={r}>
                    {r}
                  </option>
                ))}
              </select>
            </label>
          )}
        </fieldset>

        <label style={{ display: "block", marginTop: 16 }}>
          Target Return (CAGR %)
          <select value={targetReturn} onChange={(e) => setTargetReturn(e.target.value)}>
            {RETURN_OPTIONS.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </select>
        </label>

        <label style={{ display: "block", marginTop: 16 }}>
          Time Horizon
          <select value={horizon} onChange={(e) => setHorizon(e.target.value)}>
            {HORIZON_OPTIONS.map((h) => (
              <option key={h} value={h}>
                {h}
              </option>
            ))}
          </select>
        </label>

        <label style={{ display: "block", marginTop: 16 }}>
          Financial Goal
          <input type="text" value={goal} onChange={(e) => setGoal(e.target.value)} />
        </label>

        <label style={{ display: "block", marginTop: 16 }}>
          Capital to Deploy (₹, optional)
          <input
            type="number"
            min={0}
            value={capital}
            onChange={(e) => setCapital(e.target.value)}
          />
        </label>

        <button
          type="submit"
          className="button-primary"
          style={{ marginTop: 24 }}
          disabled={instruments.length === 0 || createSession.isPending}
        >
          {createSession.isPending ? "Starting…" : "🚀 Analyze Market"}
        </button>

        {createSession.isError && (
          <p role="alert">Could not start analysis: {createSession.error.message}</p>
        )}
      </form>
    </div>
  );
}
