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

  const prompt = `You are GitOwl, an elite AI code reviewer and security auditor.
Review the following pull request diff.

Severity Threshold: ${minSeverity.toUpperCase()}
- If threshold is ERROR: ONLY report critical bugs, security vulnerabilities, and severe performance issues. Ignore minor styling or refactoring suggestions.
- If threshold is WARNING: Report bugs, security flaws, and significant anti-patterns or logic errors.
- If threshold is INFO: Report all of the above, plus stylistic improvements, code organization, and optimization suggestions.

Your output must be formatted in Markdown.
1. Start with a brief, punchy summary of the changes.
2. Provide a Risk Assessment (Low/Medium/High).
3. If issues are found, list them clearly with file names and specific code snippets if possible.
4. If the code looks perfect according to the threshold, state clearly that no issues were found.

Diff:
\`\`\`diff
${diff}
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
