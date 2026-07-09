import OpenAI from "openai";
import { prisma } from "./prisma";

const openrouter = new OpenAI({
  baseURL: "https://openrouter.ai/api/v1",
  apiKey: process.env.OPENROUTER_API_KEY || "missing",
});

export async function analyzeDiffAndPostReview(
  diff: string,
  model: string,
  minSeverity: string,
  repositoryId: string,
  prNumber: number,
  postCommentCallback: (body: string) => Promise<void>
) {
  if (!process.env.OPENROUTER_API_KEY) {
    throw new Error("OPENROUTER_API_KEY is not set");
  }

  // Resolve model names properly with provider prefixes
  let resolvedModel = "google/gemini-2.0-flash:free"; // Default to free model to avoid 404s for 0 balance
  
  if (model === "openrouter/auto") resolvedModel = "google/gemini-2.0-flash:free";
  else if (model === "gpt-4o") resolvedModel = "openai/gpt-4o";
  else if (model === "gpt-4o-mini") resolvedModel = "openai/gpt-4o-mini";
  else if (model === "claude-3.5-sonnet") resolvedModel = "anthropic/claude-3.5-sonnet";
  else if (model) resolvedModel = model;

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
  
  const completion = await openrouter.chat.completions.create({
    model: resolvedModel,
    messages: [
      { role: "system", content: "You are GitOwl, an expert, precise, and ruthless software engineering reviewer." },
      { role: "user", content: prompt }
    ],
  });

  const latency = (Date.now() - startTime) / 1000;
  const responseText = completion.choices[0]?.message?.content || "No review generated.";
  const tokensUsed = completion.usage?.total_tokens || 0;
  
  // Extract risk score from response if possible, otherwise default to Medium
  let riskScore = "Medium";
  if (responseText.includes("High")) riskScore = "High";
  else if (responseText.includes("Low")) riskScore = "Low";

  // Actually post the comment to GitHub
  await postCommentCallback(responseText);

  // Log it to the database
  await prisma.reviewLog.create({
    data: {
      repositoryId,
      prNumber,
      riskScore,
      tokensUsed,
      cost: (tokensUsed / 1000) * 0.001, // Rough estimate
      latency,
    }
  });

  return { responseText, tokensUsed, riskScore };
}
