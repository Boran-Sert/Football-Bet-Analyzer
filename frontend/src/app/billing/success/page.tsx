"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { CheckCircleIcon } from "@heroicons/react/24/outline";

export default function PaymentSuccessPage() {
  const [countdown, setCountdown] = useState(5);

  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown((prev) => prev - 1);
    }, 1000);

    const redirect = setTimeout(() => {
      window.location.href = "/";
    }, 5000);

    return () => {
      clearInterval(timer);
      clearTimeout(redirect);
    };
  }, []);

  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] text-center px-4">
      <div className="bg-[#11111a] p-10 rounded-3xl border border-slate-800 shadow-2xl max-w-md w-full">
        <CheckCircleIcon className="h-20 w-20 text-emerald-500 mx-auto mb-6 animate-bounce" />
        <h1 className="text-3xl font-black text-white mb-4">Ödeme Başarılı!</h1>
        <p className="text-slate-400 mb-8">
          Aboneliğiniz başarıyla aktif edildi. Artık tüm premium özellikleri kullanabilirsiniz.
        </p>
        
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl mb-8">
          <p className="text-emerald-400 text-sm font-medium">
            {countdown} saniye içinde ana sayfaya yönlendiriliyorsunuz...
          </p>
        </div>

        <Link
          href="/"
          className="block w-full py-4 bg-indigo-600 hover:bg-indigo-700 text-white font-bold rounded-xl transition-colors"
        >
          Hemen Analize Başla
        </Link>
      </div>
    </div>
  );
}
