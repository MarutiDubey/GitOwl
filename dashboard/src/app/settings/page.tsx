import { SlidersHorizontal } from "lucide-react";

export default function SettingsPage() {
  return (
    <div className="space-y-10">
      <div>
        <h1 className="text-4xl font-bold tracking-tight text-white font-heading">Settings</h1>
        <p className="text-slate-400 mt-2 text-sm max-w-2xl">
          Manage your account, default review policies, and workspace preferences.
        </p>
      </div>

      <div className="rounded-2xl border border-white/[0.05] bg-black/40 backdrop-blur-md p-6 relative overflow-hidden group">
        <div className="absolute top-0 right-0 w-64 h-64 bg-[#F5A623]/5 rounded-full blur-[80px] group-hover:bg-[#F5A623]/10 transition-colors duration-700" />
        <div className="h-[360px] flex flex-col items-center justify-center gap-4 border border-dashed border-white/10 rounded-xl bg-white/[0.02]">
          <div className="w-16 h-16 rounded-full bg-white/5 border border-white/10 flex items-center justify-center">
            <SlidersHorizontal className="w-8 h-8 text-slate-600" />
          </div>
          <span className="text-slate-500 text-sm tracking-widest uppercase font-medium">Settings Panel Coming Soon</span>
        </div>
      </div>
    </div>
  );
}
