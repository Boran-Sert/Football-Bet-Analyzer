"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import Sidebar from "@/components/Sidebar";
import TopHeader from "@/components/TopHeader";

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [isAuthChecking, setIsAuthChecking] = useState(true);

  const publicRoutes = ["/login", "/register", "/pricing", "/confirm-email-change", "/billing/success"];
  const isPublicPage = publicRoutes.includes(pathname);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token && !isPublicPage) {
      router.push("/login");
    } else {
      setIsAuthChecking(false);
    }
  }, [pathname, isPublicPage, router]);

  if (isAuthChecking && !isPublicPage) {
    return (
      <div className="flex items-center justify-center w-full min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-primary"></div>
      </div>
    );
  }

  if (isPublicPage) {
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
