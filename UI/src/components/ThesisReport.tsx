import ReactMarkdown from "react-markdown";

interface ThesisReportProps {
  thesis: string;
}

export function ThesisReport({ thesis }: ThesisReportProps) {
  if (!thesis.trim()) {
    return <p>No thesis generated yet.</p>;
  }

  return (
    <div className="card">
      <ReactMarkdown>{thesis}</ReactMarkdown>
    </div>
  );
}
