import type { ReviewResponse } from "../api";

const SEVERITY_ICON: Record<string, string> = {
  error: "🔴",
  warning: "🟡",
  info: "🔵",
};

const RISK_ICON: Record<string, string> = {
  low: "✅",
  medium: "⚠️",
  high: "🚨",
};

function riskClass(risk: string): string {
  return risk.toLowerCase();
}

export function ReviewOutput({ result }: { result: ReviewResponse }) {
  const rc = riskClass(result.risk);
  return (
    <div className={`result result--${rc}`}>
      {/* ── Header row ── */}
      <div className="result-header">
        <div className="risk-pill-wrap">
          <span className={`risk-badge ${rc}`}>
            {RISK_ICON[rc] ?? "🔍"} {result.risk} Risk
          </span>
          <span className="stats">
            {result.files_changed} file{result.files_changed === 1 ? "" : "s"}
            &nbsp;·&nbsp;
            <span className="stat-add">+{result.added_lines}</span>
            /
            <span className="stat-del">-{result.removed_lines}</span>
          </span>
        </div>
      </div>

      {/* ── Summary ── */}
      <p className="summary">{result.summary}</p>

      {/* ── Findings ── */}
      <div className="findings">
        {result.findings.length === 0 ? (
          <div className="clean-box">
            <span className="clean-icon">✅</span>
            <span>No issues flagged — looks clean!</span>
          </div>
        ) : (
          <>
            <div className="findings-header">
              Findings
              <span className="findings-count">{result.findings.length}</span>
            </div>
            {result.findings.map((f, i) => {
              const sev = f.severity?.toLowerCase() ?? "info";
              return (
                <div className={`finding finding--${sev}`} key={i}>
                  <div className="finding-top">
                    <span className="finding-icon">{SEVERITY_ICON[sev] ?? "•"}</span>
                    <span className="finding-title">{f.title}</span>
                    {f.file && (
                      <span className="finding-location">
                        {f.file}
                        {f.line ? `:${f.line}` : ""}
                      </span>
                    )}
                  </div>
                  <p className="finding-message">{f.message}</p>
                  {f.suggestion && (
                    <pre className="suggestion">
                      <div className="suggestion-label">💡 Suggested fix</div>
                      {f.suggestion}
                    </pre>
                  )}
                </div>
              );
            })}
          </>
        )}
      </div>
    </div>
  );
}
