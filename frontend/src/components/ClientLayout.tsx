"use client";

import { usePathname } from "next/navigation";
import Sidebar from "@/components/Sidebar";
import TopHeader from "@/components/TopHeader";

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isAuthPage = pathname === "/login" || pathname === "/register";

  if (isAuthPage) {
    return <main className="w-full">{children}</main>;
  }

  return (
    <>
      <Sidebar />
      <div className="flex-1 ml-64 min-h-screen flex flex-col">
        <TopHeader />
        <main className="flex-grow p-8 max-w-[1600px]">
          {children}
        </main>
      </div>
    </>
  );
}
