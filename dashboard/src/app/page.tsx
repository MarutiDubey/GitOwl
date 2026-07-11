import { getServerSession } from "next-auth/next";
import { authOptions } from "@/lib/auth";
import { prisma } from "@/lib/prisma";
import HomeClient from "@/components/HomeClient";

export default async function Home() {
  const session = await getServerSession(authOptions);
  const userId = session?.user ? (session.user as any).id : undefined;

  if (!userId) {
    return <HomeClient stats={{ totalReviews: 0, tokensUsedFormatted: "0", costFormatted: "$0.00", highRiskPRs: 0, bugsCaught: 0 }} recentInterventions={[]} isAuthenticated={false} />;
  }

  // Fetch repositories owned by the user
  const userRepos = await prisma.repository.findMany({
    where: { userId },
    select: { id: true, name: true }
  });

  const repoIds = userRepos.map(r => r.id);

  if (repoIds.length === 0) {
    return <HomeClient stats={{ totalReviews: 0, tokensUsedFormatted: "0", costFormatted: "$0.00", highRiskPRs: 0, bugsCaught: 0 }} recentInterventions={[]} isAuthenticated={true} />;
  }

  // Fetch ReviewLogs for these repositories
  const reviewLogs = await prisma.reviewLog.findMany({
    where: { repositoryId: { in: repoIds } },
    orderBy: { createdAt: 'desc' },
    include: { repository: true }
  });

  const totalReviews = reviewLogs.length;
  const tokensUsed = reviewLogs.reduce((acc, log) => acc + log.tokensUsed, 0);
  const cost = reviewLogs.reduce((acc, log) => acc + (log.cost || 0), 0);
  
  // Assuming riskScore is stored as "Low", "Medium", "High" based on Python CLI
  const highRiskPRs = reviewLogs.filter(log => log.riskScore?.toLowerCase() === 'high').length;
  const bugsCaught = reviewLogs.filter(log => log.riskScore?.toLowerCase() !== 'low').length; // Estimate

  const tokensUsedFormatted = tokensUsed > 1000000 
    ? (tokensUsed / 1000000).toFixed(1) + "M" 
    : tokensUsed > 1000 ? (tokensUsed / 1000).toFixed(1) + "K" : tokensUsed.toString();

  const costFormatted = "$" + cost.toFixed(2);

  const recentInterventions = reviewLogs.slice(0, 5).map(log => ({
    id: log.id,
    repo: log.repository.name,
    pr: `#${log.prNumber}`,
    severity: (log.riskScore?.toLowerCase() || "low") as "low"|"medium"|"high",
    message: `Review completed. Score: ${log.riskScore}. Tokens: ${log.tokensUsed}.`
  }));

  return (
    <HomeClient 
      isAuthenticated={true}
      stats={{
        totalReviews,
        tokensUsedFormatted,
        costFormatted,
        highRiskPRs,
        bugsCaught
      }}
      recentInterventions={recentInterventions}
    />
  );
}
