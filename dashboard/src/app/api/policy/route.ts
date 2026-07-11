import { NextResponse } from "next/server";
import { prisma } from "@/lib/prisma";

export async function GET(req: Request) {
  try {
    const { searchParams } = new URL(req.url);
    const repoFullName = searchParams.get("repo");

    if (!repoFullName) {
      return NextResponse.json({ error: "Missing repo parameter" }, { status: 400 });
    }

    // Find the repository in our database
    const repository = await prisma.repository.findFirst({
      where: { fullName: repoFullName },
    });

    if (!repository) {
      // If not found or not registered, return 404 so Python falls back to local config
      return NextResponse.json({ error: "Repository not found" }, { status: 404 });
    }

    if (!repository.isEnabled) {
      return NextResponse.json({ error: "Repository GitOwl engine is disabled via Dashboard" }, { status: 403 });
    }

    // Return the policy configuration (snake_case keys match gitowl/dashboard.py's contract)
    const ignorePaths = repository.ignorePaths
      ? repository.ignorePaths.split("\n").map((p) => p.trim()).filter(Boolean)
      : [];

    return NextResponse.json({
      min_severity: repository.minSeverity,
      ai_model: repository.aiModel,
      ignore_paths: ignorePaths,
    }, { status: 200 });

  } catch (error: any) {
    console.error("Policy fetch error:", error);
    return NextResponse.json(
      { error: "Internal server error processing policy fetch." },
      { status: 500 }
    );
  }
}
