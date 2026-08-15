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
      <h1>📋 Past Runs</h1>
      <div className="card">
        <table>
          <thead>
            <tr>
              <th>Goal</th>
              <th>Status</th>
              <th>Created</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {sessions.map((s) => (
              <tr key={s.id}>
                <td>{s.goal}</td>
                <td>{s.status}</td>
                <td>{new Date(s.created_at).toLocaleString()}</td>
                <td>
                  <Link to={s.status === "completed" ? `/results/${s.id}` : `/analysis/${s.id}`}>
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
