import { type FormEvent, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCreateSession } from "../hooks/useSessions";
import {
  HORIZON_OPTIONS,
  INSTRUMENT_OPTIONS,
  RETURN_OPTIONS,
  RISK_OPTIONS,
} from "../lib/formOptions";

const inputClass =
  "block w-full mt-1.5 px-3 py-2 border border-outline-variant rounded-md bg-surface-container-high text-on-surface text-sm focus:outline-none focus:border-primary";

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
    <div className="w-full">
      <h1 className="text-2xl sm:text-3xl font-headline font-semibold text-on-surface tracking-tight mb-1">
        Investor Profile Setup
      </h1>
      <p className="text-on-surface-variant text-sm mb-6 sm:mb-8">
        Configure your parameters to initialize the AI analyst agents.
      </p>
      <form
        onSubmit={handleSubmit}
        className="bg-surface-container-low rounded-xl shadow-sm border border-outline-variant/40 p-5 sm:p-8 lg:p-10"
      >
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-x-12 gap-y-8">
          <fieldset className="border-none p-0 m-0">
            <legend className="font-headline font-semibold text-on-surface mb-2">
              Investment Preference
            </legend>
            <div className="flex flex-wrap gap-2">
              {INSTRUMENT_OPTIONS.map((option) => {
                const selected = instruments.includes(option);
                return (
                  <button
                    key={option}
                    type="button"
                    aria-pressed={selected}
                    onClick={() => toggleInstrument(option)}
                    className={`rounded-full px-4 py-2 text-sm border transition-colors ${
                      selected
                        ? "bg-primary/10 text-primary border-primary/40 font-semibold"
                        : "text-on-surface-variant border-outline-variant hover:bg-surface-container-high"
                    }`}
                  >
                    {option}
                  </button>
                );
              })}
            </div>
            {instruments.length === 0 && (
              <p role="alert" className="text-error text-sm mt-2">
                Select at least one investment type.
              </p>
            )}

            <div className="mt-8">
              <span className="font-headline font-semibold text-on-surface mb-2 block">
                Risk Appetite
              </span>
              <label className="flex items-center gap-2 text-sm text-on-surface-variant mb-3">
                <input
                  type="checkbox"
                  checked={allowRange}
                  onChange={(e) => setAllowRange(e.target.checked)}
                />
                Allow Range Selection
              </label>
              {allowRange ? (
                <div className="flex flex-col sm:flex-row gap-4">
                  <label className="text-sm text-on-surface-variant flex-1">
                    From
                    <select
                      className={inputClass}
                      value={riskStart}
                      onChange={(e) => setRiskStart(e.target.value)}
                    >
                      {RISK_OPTIONS.map((r) => (
                        <option key={r} value={r}>
                          {r}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label className="text-sm text-on-surface-variant flex-1">
                    To
                    <select
                      className={inputClass}
                      value={riskEnd}
                      onChange={(e) => setRiskEnd(e.target.value)}
                    >
                      {RISK_OPTIONS.map((r) => (
                        <option key={r} value={r}>
                          {r}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
              ) : (
                <div className="segmented" role="radiogroup" aria-label="Risk Appetite">
                  {RISK_OPTIONS.map((r) => (
                    <button
                      key={r}
                      type="button"
                      role="radio"
                      aria-checked={riskSingle === r}
                      className={riskSingle === r ? "selected" : undefined}
                      onClick={() => setRiskSingle(r)}
                    >
                      {r}
                    </button>
                  ))}
                </div>
              )}
            </div>
          </fieldset>

          <div className="flex flex-col">
            <div className="flex flex-col sm:flex-row gap-4">
              <label className="text-sm text-on-surface-variant flex-1">
                Target Return (CAGR %)
                <select
                  className={inputClass}
                  value={targetReturn}
                  onChange={(e) => setTargetReturn(e.target.value)}
                >
                  {RETURN_OPTIONS.map((r) => (
                    <option key={r} value={r}>
                      {r}
                    </option>
                  ))}
                </select>
              </label>
              <label className="text-sm text-on-surface-variant flex-1">
                Time Horizon
                <select className={inputClass} value={horizon} onChange={(e) => setHorizon(e.target.value)}>
                  {HORIZON_OPTIONS.map((h) => (
                    <option key={h} value={h}>
                      {h}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <label className="block text-sm text-on-surface-variant mt-6">
              Financial Goal
              <input
                type="text"
                className={inputClass}
                value={goal}
                onChange={(e) => setGoal(e.target.value)}
              />
            </label>

            <label className="block text-sm text-on-surface-variant mt-6">
              Capital to Deploy (₹, optional)
              <div className="relative mt-1.5">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-sm">
                  ₹
                </span>
                <input
                  type="number"
                  min={0}
                  value={capital}
                  onChange={(e) => setCapital(e.target.value)}
                  className="block w-full pl-8 pr-12 py-2 border border-outline-variant rounded-lg bg-surface-container-high text-on-surface text-sm focus:outline-none focus:border-primary"
                />
                <span className="absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant text-xs">
                  INR
                </span>
              </div>
            </label>
          </div>
        </div>

        <button
          type="submit"
          disabled={instruments.length === 0 || createSession.isPending}
          className="w-full lg:max-w-md lg:mx-auto lg:flex mt-10 flex items-center justify-center gap-2 bg-primary text-on-primary rounded-md py-3 px-6 font-semibold text-sm transition-opacity hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {createSession.isPending ? (
            "Starting…"
          ) : (
            <>
              Analyze Market
              <span className="material-symbols-outlined text-lg" aria-hidden="true">
                arrow_forward
              </span>
            </>
          )}
        </button>
        <p className="text-xs text-on-surface-variant text-center mt-3">
          Agents will take approximately 2-3 minutes to compile the initial report.
        </p>

        {createSession.isError && (
          <p role="alert" className="text-error text-sm mt-3 text-center">
            Could not start analysis: {createSession.error.message}
          </p>
        )}
      </form>
    </div>
  );
}
