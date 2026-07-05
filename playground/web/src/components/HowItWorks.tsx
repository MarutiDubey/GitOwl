import ScrollFloat from "./ScrollFloat";
import BorderGlow from "./BorderGlow";

const STEPS = [
  {
    n: "1",
    title: "Open a pull request",
    body: "GitOwl runs automatically as a GitHub Action on every PR — opened, updated, or reopened.",
    glowColor: "240 80 70",
    colors: ["#6366f1", "#a78bfa", "#818cf8"],
  },
  {
    n: "2",
    title: "AI reviews the diff",
    body: "It reads the changes, flags bugs and security risks, filters false positives, and scores overall risk.",
    glowColor: "280 80 70",
    colors: ["#a78bfa", "#c084fc", "#6366f1"],
  },
  {
    n: "3",
    title: "You get a comment",
    body: "A structured review is posted right on the PR — risk badge, findings, and one-click fix suggestions.",
    glowColor: "200 80 70",
    colors: ["#38bdf8", "#6366f1", "#a78bfa"],
  },
];

export function HowItWorks() {
  return (
    <section className="how">
      <ScrollFloat
        animationDuration={1}
        ease="back.inOut(2)"
        scrollStart="center bottom+=50%"
        scrollEnd="bottom bottom-=40%"
        stagger={0.04}
        textClassName="how-heading"
      >
        How it works
      </ScrollFloat>
      <div className="how-grid">
        {STEPS.map((s) => (
          <BorderGlow
            key={s.n}
            glowColor={s.glowColor}
            colors={s.colors}
            backgroundColor="var(--bg)"
            borderRadius={12}
            glowRadius={32}
            glowIntensity={1.2}
            coneSpread={20}
            animated
          >
            <div className="how-step">
              <div className="how-num">{s.n}</div>
              <h3>{s.title}</h3>
              <p>{s.body}</p>
            </div>
          </BorderGlow>
        ))}
      </div>
    </section>
  );
}
