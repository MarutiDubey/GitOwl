import type { ReviewResponse } from "../api";

function riskClass(risk: string): string {
  return risk.toLowerCase();
}

export function ReviewOutput({ result }: { result: ReviewResponse }) {
  return (
    <div className="result">
      <div className="risk-row">
        <span className={`risk-badge ${riskClass(result.risk)}`}>{result.risk} risk</span>
        <span className="stats">
          {result.files_changed} file{result.files_changed === 1 ? "" : "s"} · +
          {result.added_lines}/-{result.removed_lines}
        </span>
      </div>

      <p className="summary">{result.summary}</p>

      <div className="findings">
        {result.findings.length === 0 ? (
          <p className="clean">No issues flagged.</p>
        ) : (
          <>
            <h3>Findings ({result.findings.length})</h3>
            {result.findings.map((f, i) => (
              <div className="finding" key={i}>
                <div className="finding-title">{f.title}</div>
                {f.file && (
                  <div className="finding-location">
                    {f.file}
                    {f.line ? `:${f.line}` : ""} · {f.severity}
                  </div>
                )}
                <p className="finding-message">{f.message}</p>
                {f.suggestion && <pre className="suggestion">{f.suggestion}</pre>}
              </div>
            ))}
          </>
        )}
      </div>
    </div>
  );
}
