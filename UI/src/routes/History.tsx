import { Link } from "react-router-dom";
import { useSessionList } from "../hooks/useSessions";

export function History() {
  const { data: sessions, isLoading } = useSessionList();

  if (isLoading) {
    return <p>Loading history…</p>;
  }

  if (!sessions || sessions.length === 0) {
    return <p>No past analysis runs yet. Start one from the Profile page.</p>;
  }

  return (
    <div>
      <h1 className="text-3xl font-headline font-semibold text-on-surface tracking-tight mb-1">
        Past Runs
      </h1>
      <p className="text-on-surface-variant text-sm mb-8">
        Review the history of your AI-driven financial analyses and market scans.
      </p>
      <div className="bg-surface-container-low rounded-xl shadow-sm border border-outline-variant/40 overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-surface-container/20 text-xs text-on-surface-variant uppercase tracking-wider border-b border-outline-variant/30">
              <th className="py-3 px-6 font-semibold">Financial Goal</th>
              <th className="py-3 px-6 font-semibold">Status</th>
              <th className="py-3 px-6 font-semibold">Created At</th>
              <th className="py-3 px-6 font-semibold">Actions</th>
            </tr>
          </thead>
          <tbody className="text-sm text-on-surface divide-y divide-outline-variant/20">
            {sessions.map((s) => (
              <tr key={s.id} className="hover:bg-surface-container-low/50 transition-colors">
                <td className="py-3 px-6 font-medium">{s.goal}</td>
                <td className="py-3 px-6">
                  <span className={`status-badge status-${s.status}`}>{s.status}</span>
                </td>
                <td className="py-3 px-6 text-on-surface-variant">
                  {new Date(s.created_at).toLocaleString()}
                </td>
                <td className="py-3 px-6">
                  <Link
                    to={s.status === "completed" ? `/results/${s.id}` : `/analysis/${s.id}`}
                    className="text-primary text-sm font-medium hover:underline"
                  >
                    View
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
