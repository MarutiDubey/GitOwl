import GlitchText from "./GlitchText";
import { ShimmerButton } from "./ShimmerButton";

export function Setup() {
  return (
    <section className="setup">
      <GlitchText
        speed={1}
        enableShadows={true}
        enableOnHover={false}
        className="setup-heading"
      >
        Install in seconds
      </GlitchText>
      <p>GitOwl is a GitHub App. There's no python package to install, and no workflow files to maintain. Just 3 clicks:</p>
      
      <ol className="setup-steps" style={{ marginTop: '2rem', marginBottom: '3rem' }}>
        <li>
          <strong>Sign in</strong> to the GitOwl Dashboard using your GitHub account.
        </li>
        <li>
          <strong>Install the App</strong> by clicking "Connect Repository" and authorizing GitOwl on your chosen repos.
        </li>
        <li>
          <strong>Open a Pull Request</strong> — GitOwl automatically reviews the code and posts a professional, structured comment.
        </li>
      </ol>

      <div style={{ display: 'flex', justifyContent: 'center' }}>
        <ShimmerButton 
          href="https://gitowl-dashboard.vercel.app" 
          background="#2ea043" 
          shimmerColor="#3fb950"
        >
          Sign in to GitHub
        </ShimmerButton>
      </div>

      <p className="setup-note" style={{ marginTop: '3rem' }}>
        Your code is processed securely using Google Gemini API. Diffs are never used for AI training.
      </p>
    </section>
  );
}
