import { useState } from "react";
import { DiffInput } from "./components/DiffInput";
import { ReviewOutput } from "./components/ReviewOutput";
import { reviewDiff, ReviewApiError, type ReviewResponse } from "./api";

function App() {
  const [diff, setDiff] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ReviewResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleReview() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await reviewDiff(diff);
      setResult(res);
    } catch (err) {
      const message = err instanceof ReviewApiError ? err.message : "Something went wrong.";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <div className="hero">
        <span className="badge">AI-assisted code review</span>
        <h1>DevGuard</h1>
        <p className="tagline">
          Paste a diff, get an AI-powered risk score and findings — the same review engine
          DevGuard posts as a comment on real GitHub pull requests.
        </p>
        <p>
          <a href="https://github.com/MarutiDubey/DevGuard" target="_blank" rel="noreferrer">
            View the project on GitHub →
          </a>
        </p>
      </div>

      <h2>Try it</h2>
      <DiffInput diff={diff} onChange={setDiff} onSubmit={handleReview} loading={loading} />

      {error && <div className="error-box">{error}</div>}
      {result && <ReviewOutput result={result} />}

      <footer>
        Diffs are sent to an AI provider for review and are not stored. Static analysis
        (Semgrep) is skipped in this playground — only the AI review layer runs.
      </footer>
    </>
  );
}

export default App;
