import { Octokit } from "octokit";
import { createAppAuth } from "@octokit/auth-app";

export async function getInstallationOctokit(installationId: number) {
  const appId = process.env.GITHUB_APP_ID;
  const privateKey = process.env.GITHUB_PRIVATE_KEY;

  if (!appId || !privateKey) {
    throw new Error("Missing GITHUB_APP_ID or GITHUB_PRIVATE_KEY environment variables.");
  }

  // Handle potentially escaped newlines in environment variables
  const formattedPrivateKey = privateKey.replace(/\\n/g, "\n");

  const octokit = new Octokit({
    authStrategy: createAppAuth,
    auth: {
      appId: appId,
      privateKey: formattedPrivateKey,
      installationId: installationId,
    },
  });

  return octokit;
}
