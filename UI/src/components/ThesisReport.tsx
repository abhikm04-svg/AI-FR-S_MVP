import ReactMarkdown from "react-markdown";

interface ThesisReportProps {
  thesis: string;
}

export function ThesisReport({ thesis }: ThesisReportProps) {
  if (!thesis.trim()) {
    return <p>No thesis generated yet.</p>;
  }

  return (
    <div className="prose prose-invert prose-sm md:prose-base max-w-3xl text-on-surface leading-relaxed">
      <ReactMarkdown>{thesis}</ReactMarkdown>
    </div>
  );
}
