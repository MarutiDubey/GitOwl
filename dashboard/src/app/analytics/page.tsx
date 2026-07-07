import { BarChart3 } from "lucide-react";

export default function AnalyticsPage() {
  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-4xl font-bold tracking-tight text-white font-heading">Analytics</h1>
        <p className="text-slate-400 mt-2 text-sm max-w-2xl">
          Deep-dive metrics across all your repositories — token spend, risk distribution, and review velocity over time.
        </p>
      </div>

      <div className="rounded-2xl border border-white/[0.05] bg-black/40 backdrop-blur-md p-6 relative overflow-hidden group">
        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-500/5 rounded-full blur-[80px] group-hover:bg-blue-500/10 transition-colors duration-700" />
        <div className="h-[360px] flex flex-col items-center justify-center gap-4 border border-dashed border-white/10 rounded-xl bg-white/[0.02]">
          <div className="w-16 h-16 rounded-full bg-white/5 border border-white/10 flex items-center justify-center">
            <BarChart3 className="w-8 h-8 text-slate-600" />
          </div>
          <span className="text-slate-500 text-sm tracking-widest uppercase font-medium">Analytics Engine Coming Soon</span>
        </div>
      </div>
    </div>
  );
}
