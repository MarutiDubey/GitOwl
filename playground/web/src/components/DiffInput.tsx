import { EXAMPLES, type Example } from "../api";

interface DiffInputProps {
  diff: string;
  onChange: (diff: string) => void;
  onSubmit: () => void;
  loading: boolean;
}

const RISK_DOT: Record<Example["expectedRisk"], string> = {
  high: "🔴",
  medium: "🟡",
  low: "🔵",
  clean: "🟢",
};

export function DiffInput({ diff, onChange, onSubmit, loading }: DiffInputProps) {
  return (
    <>
      <div className="examples">
        <span className="examples-label">Try an example:</span>
        {EXAMPLES.map((ex) => (
          <button
            type="button"
            key={ex.label}
            className="chip"
            onClick={() => onChange(ex.diff)}
            disabled={loading}
            title={ex.blurb}
          >
            <span className="chip-dot" aria-hidden="true">
              {RISK_DOT[ex.expectedRisk]}
            </span>
            {ex.label}
          </button>
        ))}
      </div>

      <textarea
        value={diff}
        onChange={(e) => onChange(e.target.value)}
        placeholder="…or paste a unified diff (git diff output) here"
        spellCheck={false}
      />

      <div className="actions">
        <button type="button" onClick={onSubmit} disabled={loading || !diff.trim()}>
          {loading ? "Reviewing…" : "Review"}
        </button>
      </div>
    </>
  );
}
