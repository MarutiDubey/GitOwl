import { getServerSession } from "next-auth/next";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import PolicyClient from "@/components/PolicyClient";
import { redirect } from "next/navigation";

export default async function PolicyEditorPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const session = await getServerSession(authOptions);
  const userId = session?.user ? (session.user as any).id : undefined;

  if (!userId) {
    redirect("/");
  }

  const repo = await prisma.repository.findUnique({
    where: { id }
  });

  if (!repo || repo.userId !== userId) {
    return <div className="p-10 text-white">Repository not found or access denied.</div>;
  }

  return <PolicyClient repo={repo} />;
}
