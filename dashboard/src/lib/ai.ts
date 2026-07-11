import { GoogleGenAI } from "@google/genai";
import { prisma } from "./prisma";

// Initialise Gemini client with GEMINI_API_KEY
// We use a dummy key if undefined to prevent crashing on import, will throw during actual call if missing.
const ai = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY || "missing" });

export async function analyzeDiffAndPostReview(
  diff: string,
  model: string,
  minSeverity: string,
  repositoryId: string,
  prNumber: number,
  postCommentCallback: (body: string) => Promise<void>
) {
  if (!process.env.GEMINI_API_KEY || process.env.GEMINI_API_KEY === "missing") {
    throw new Error("GEMINI_API_KEY is not set. Please add it to your Vercel Environment Variables.");
  }

  const prompt = `You are GitOwl, an elite, enterprise-grade AI code reviewer and security auditor.
Review the following pull request diff.

Severity Threshold: ${minSeverity.toUpperCase()}
- If ERROR: ONLY report critical bugs, security vulnerabilities, and severe performance issues.
- If WARNING: Report bugs, security flaws, and significant anti-patterns.
- If INFO: Report all of the above, plus stylistic improvements.

CRITICAL INSTRUCTION: Your output must look incredibly professional, premium, and visually structured. Use advanced GitHub Markdown features.
Follow this EXACT format structure:

# 🦉 GitOwl Code Review

**Summary:** [Write a 2-3 sentence punchy summary of the PR]

### 📊 Risk Assessment
> **[HIGH / MEDIUM / LOW]** - [1 sentence explanation of why this risk score was given]

---

### 🚨 Issues Found
[If no issues, state: "✅ **All Clear!** No issues found exceeding the ${minSeverity.toUpperCase()} threshold."]

[If issues are found, format EACH issue exactly like this:]

#### 🔴 [Issue Title] (Severity: Critical/High/Medium/Low)
**File:** \`[filename]\`

[1-2 sentences explaining the issue and why it is dangerous or bad practice.]

**Recommendation:**
[What the developer should do to fix it]

<details>
<summary><b>🛠️ Suggested Code Fix</b></summary>

\`\`\`[language]
// Your suggested replacement code here
\`\`\`
</details>

---
*Review generated automatically by GitOwl AI.*

Diff:
\`\`\`diff
\${diff}
\`\`\``;

  const startTime = Date.now();
  
  console.log("🟢 [GEMINI] Sending request to Gemini 2.5 Flash...");
  const completion = await ai.models.generateContent({
    model: 'gemini-2.5-flash',
    contents: prompt,
    config: {
      systemInstruction: 'You are GitOwl, an expert, precise, and ruthless software engineering reviewer.',
    },
  });
  console.log("🟢 [GEMINI] Received response from Gemini");

  const latency = (Date.now() - startTime) / 1000;
  const responseText = completion.text || "No review generated.";
  
  // Extract risk score from response if possible, otherwise default to Medium
  let riskScore = "Medium";
  if (responseText.includes("High")) riskScore = "High";
  else if (responseText.includes("Low")) riskScore = "Low";

  // Actually post the comment to GitHub
  await postCommentCallback(responseText);

  // Get token usage if available
  const tokensUsed = completion.usageMetadata?.totalTokenCount || 0;

  // Log it to the database
  await prisma.reviewLog.create({
    data: {
      repositoryId,
      prNumber,
      riskScore,
      tokensUsed,
      cost: 0, // Free tier
      latency,
    }
  });

  return { responseText, tokensUsed, riskScore };
}
