import { lazy, Suspense, useState } from "react";
import { motion } from "motion/react";
import { DiffInput } from "./components/DiffInput";
import { ReviewOutput } from "./components/ReviewOutput";
import { HowItWorks } from "./components/HowItWorks";
import { Screenshot } from "./components/Screenshot";
import { Features } from "./components/Features";
import { Setup } from "./components/Setup";
import { reviewDiff, ReviewApiError, EXAMPLE_DIFF, type ReviewResponse } from "./api";

const REPO_URL = "https://github.com/MarutiDubey/GitOwl";

// WebGL orb — lazy so it never blocks first paint; degrades to nothing if it
// fails to load or WebGL is unavailable.
const Orb = lazy(() => import("./components/Orb"));

// Stagger children in on load.
const container = {
  hidden: {},
  show: { transition: { staggerChildren: 0.12, delayChildren: 0.05 } },
};
const item = {
  hidden: { opacity: 0, y: 16 },
  show: { opacity: 1, y: 0, transition: { duration: 0.5, ease: "easeOut" as const } },
};

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

  function handleExample() {
    setDiff(EXAMPLE_DIFF);
    setResult(null);
    setError(null);
  }

  return (
    <>
      <header className="site-header">
        <div className="logo-row">
          <div className="owl-icon" aria-hidden="true">
            <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
              <circle cx="50" cy="50" r="50" fill="#1e3a8a" />
              <ellipse cx="50" cy="62" rx="20" ry="22" fill="white" />
              <circle cx="40" cy="44" r="11" fill="white" />
              <circle cx="60" cy="44" r="11" fill="white" />
              <circle cx="40" cy="44" r="5" fill="#1e3a8a" />
              <circle cx="60" cy="44" r="5" fill="#1e3a8a" />
              <circle cx="42" cy="42" r="1.5" fill="white" />
              <circle cx="62" cy="42" r="1.5" fill="white" />
              <polygon points="50,51 46,57 54,57" fill="#1e3a8a" />
              <polygon points="34,36 30,24 40,32" fill="white" />
              <polygon points="66,36 70,24 60,32" fill="white" />
              <ellipse cx="28" cy="66" rx="8" ry="14" fill="white" transform="rotate(-15 28 66)" />
              <ellipse cx="72" cy="66" rx="8" ry="14" fill="white" transform="rotate(15 72 66)" />
            </svg>
          </div>
          <span className="site-name">GitOwl</span>
        </div>
        <a className="gh-link" href={REPO_URL} target="_blank" rel="noreferrer">
          GitHub →
        </a>
      </header>

      <div className="hero">
        <div className="hero-orb" aria-hidden="true">
          <Suspense fallback={null}>
            <Orb hue={230} hoverIntensity={0.3} backgroundColor="#0d1117" />
          </Suspense>
        </div>
        <motion.div className="hero-content" variants={container} initial="hidden" animate="show">
          <motion.span className="badge" variants={item}>
            AI-assisted code review
          </motion.span>
          <motion.h1 variants={item}>
            Smarter PR reviews,
            <br />
            on autopilot.
          </motion.h1>
          <motion.p className="tagline" variants={item}>
            GitOwl reviews every pull request with AI — flagging bugs, security risks, and scoring
            overall risk, then posting it as a comment. Add it to any repo in 3 steps.
          </motion.p>
          <motion.div className="hero-actions" variants={item}>
            <a className="btn-primary" href={REPO_URL} target="_blank" rel="noreferrer">
              Add to your repo
            </a>
            <button onClick={handleExample} className="secondary">
              Try the live demo ↓
            </button>
          </motion.div>
        </motion.div>
      </div>

      <Reveal>
        <HowItWorks />
      </Reveal>

      <Reveal>
        <Screenshot />
      </Reveal>

      <Reveal>
        <section className="try">
          <h2>Try it live</h2>
          <p className="try-sub">
            Pick an example or paste a diff — see a real GitOwl review right here. No signup,
            nothing stored.
          </p>
          <DiffInput diff={diff} onChange={setDiff} onSubmit={handleReview} loading={loading} />
          {error && <div className="error-box">{error}</div>}
          {result && <ReviewOutput result={result} />}
        </section>
      </Reveal>

      <Reveal>
        <Features />
      </Reveal>

      <Reveal>
        <Setup />
      </Reveal>

      <footer>
        Diffs are sent to an AI provider for review and are not stored. Static analysis (Semgrep) is
        skipped in this playground — only the AI review layer runs.{" "}
        <a href={REPO_URL} target="_blank" rel="noreferrer">
          View source on GitHub
        </a>
      </footer>
    </>
  );
}

// Fade + rise a section into view once. Motion honors prefers-reduced-motion,
// so reduced-motion users get the content without the transform.
function Reveal({ children }: { children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 24 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-80px" }}
      transition={{ duration: 0.5, ease: "easeOut" as const }}
    >
      {children}
    </motion.div>
  );
}

export default App;
