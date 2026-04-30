"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";

const NAV_ITEMS = [
  { name: "Dashboard", href: "/", icon: (props: any) => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><rect width="7" height="9" x="3" y="3" rx="1"/><rect width="7" height="5" x="14" y="3" rx="1"/><rect width="7" height="9" x="14" y="12" rx="1"/><rect width="7" height="5" x="3" y="16" rx="1"/></svg>
  )},
  { name: "Analizler", href: "/analysis", icon: (props: any) => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><path d="M3 3v18h18"/><path d="m19 9-5 5-4-4-3 3"/></svg>
  )},
  { name: "Piyasalar", href: "/market", icon: (props: any) => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
  )},
  { name: "Planlar", href: "/pricing", icon: (props: any) => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><rect width="20" height="14" x="2" y="5" rx="2"/><line x1="2" x2="22" y1="10" y2="10"/></svg>
  )},
];

const SECONDARY_NAV = [
  { name: "Profil", href: "/profile", icon: (props: any) => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
  )},
  { name: "Ayarlar", href: "/settings", icon: (props: any) => (
    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" {...props}><path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.72v.18a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.1a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/></svg>
  )},
];

export default function Sidebar() {
  const pathname = usePathname();
  const router = useRouter();

  return (
    <aside className="w-64 h-screen fixed left-0 top-0 bg-[#050505] border-r border-white/5 flex flex-col z-50">
      {/* LOGO */}
      <div className="p-6 flex items-center gap-3">
        <div className="w-8 h-8 rounded bg-primary flex items-center justify-center emerald-glow">
           <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#000" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><path d="m13 2-2 10h3L11 22l2-10h-3l2-10z"/></svg>
        </div>
        <span className="text-xl font-black tracking-tighter text-white uppercase italic">Sports-Analyzer</span>
      </div>

      {/* MAIN NAV */}
      <nav className="flex-1 px-4 mt-4 space-y-1">
        {NAV_ITEMS.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link 
              key={item.name} 
              href={item.href}
              className={`flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all group ${
                isActive 
                  ? "bg-white/5 text-white" 
                  : "text-slate-500 hover:text-white hover:bg-white/[0.02]"
              }`}
            >
              <item.icon className={isActive ? "text-primary" : "group-hover:text-primary transition-colors"} />
              {item.name}
            </Link>
          );
        })}
      </nav>

      {/* SECONDARY NAV */}
      <div className="px-4 pb-8 space-y-1">
         <div className="h-px bg-white/5 mb-4 mx-4"></div>
         {SECONDARY_NAV.map((item) => (
            <Link 
               key={item.name} 
               href={item.href}
               className="flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium text-slate-500 hover:text-white hover:bg-white/[0.02] transition-all group"
            >
               <item.icon className="group-hover:text-primary transition-colors" />
               {item.name}
            </Link>
         ))}

         {/* PRO PROMO */}
         <div className="mt-6 p-4 rounded-2xl bg-gradient-to-br from-primary/20 to-transparent border border-primary/20">
            <h4 className="text-xs font-bold text-white mb-1">Analiz Gücünü Artır</h4>
            <p className="text-[10px] text-slate-400 leading-tight">Daha fazla benzer maç ve detaylı istatistikler için planını yükselt.</p>
            <button 
              onClick={() => router.push("/pricing")}
              className="mt-3 w-full py-2 bg-primary text-black text-[10px] font-black rounded-lg hover:scale-105 transition-transform"
            >
              YÜKSELT
            </button>
         </div>
      </div>
    </aside>
  );
}
