import { EXAMPLE_DIFF } from "../api";

interface DiffInputProps {
  diff: string;
  onChange: (diff: string) => void;
  onSubmit: () => void;
  loading: boolean;
}

export function DiffInput({ diff, onChange, onSubmit, loading }: DiffInputProps) {
  return (
    <>
      <textarea
        value={diff}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Paste a unified diff (git diff output) here..."
        spellCheck={false}
      />
      <div className="actions">
        <button type="button" onClick={onSubmit} disabled={loading || !diff.trim()}>
          {loading ? "Reviewing..." : "Review"}
        </button>
        <button
          type="button"
          className="secondary"
          onClick={() => onChange(EXAMPLE_DIFF)}
          disabled={loading}
        >
          Load example diff
        </button>
      </div>
    </>
  );
}
