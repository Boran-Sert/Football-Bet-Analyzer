"use client";

import { useState, useEffect } from "react";
import { CheckIcon } from "@heroicons/react/24/solid";

interface Plan {
  id: string;
  name: string;
  price_try: number;
  features: string[];
}

export default function PricingPage() {
  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [processingId, setProcessingId] = useState<string | null>(null);

  useEffect(() => {
    const fetchPlans = async () => {
      try {
        const res = await fetch("http://127.0.0.1:8000/api/v1/billing/plans");
        if (res.ok) {
          const data = await res.json();
          setPlans(data);
        }
      } catch (err) {
        console.error("Plans fetch error:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchPlans();
  }, []);

  const handleCheckout = async (planId: string) => {
    setProcessingId(planId);
    try {
      const token = localStorage.getItem("token");
      if (!token) {
        alert("Lütfen önce giriş yapın.");
        window.location.href = "/login";
        return;
      }

      const res = await fetch("http://127.0.0.1:8000/api/v1/billing/checkout", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ plan_id: planId }),
      });

      const data = await res.json();
      if (res.ok && data.checkout_url) {
        window.location.href = data.checkout_url;
      } else {
        const errMsg = Array.isArray(data.detail) ? data.detail.map((e: any) => e.msg).join(", ") : data.detail;
        alert(typeof errMsg === "string" ? errMsg : "Ödeme oturumu oluşturulamadı.");
      }
    } catch (err) {
      console.error("Checkout error:", err);
      alert("Bir hata oluştu.");
    } finally {
      setProcessingId(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-indigo-500"></div>
      </div>
    );
  }

  return (
    <div className="py-12 px-4 sm:px-6 lg:px-8">
      <div className="text-center mb-16">
        <h2 className="text-base font-semibold text-indigo-400 tracking-wide uppercase">Fiyatlandırma</h2>
        <p className="mt-1 text-4xl font-extrabold text-white sm:text-5xl sm:tracking-tight lg:text-6xl">
          Analiz Gücünü Artırın
        </p>
        <p className="max-w-xl mt-5 mx-auto text-xl text-slate-400">
          Size en uygun planı seçin, veriye dayalı tahminlerle kazanmaya başlayın.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:max-w-4xl lg:mx-auto">
        {plans.map((plan) => (
          <div
            key={plan.id}
            className={`relative flex flex-col p-8 bg-[#11111a] border ${
              plan.id === "elite" ? "border-indigo-500 shadow-2xl shadow-indigo-500/20" : "border-slate-800"
            } rounded-2xl transition-all duration-300 hover:scale-[1.02]`}
          >
            {plan.id === "elite" && (
              <div className="absolute top-0 right-0 transform translate-x-2 -translate-y-2">
                <span className="inline-flex items-center px-3 py-0.5 rounded-full text-sm font-medium bg-indigo-500 text-white">
                  En Popüler
                </span>
              </div>
            )}

            <div className="flex-1">
              <h3 className="text-xl font-bold text-white">{plan.name}</h3>
              <p className="mt-4 flex items-baseline text-white">
                <span className="text-5xl font-extrabold tracking-tight">₺{plan.price_try}</span>
                <span className="ml-1 text-xl font-semibold text-slate-400">/aylık</span>
              </p>
              <ul className="mt-8 space-y-4">
                {plan.features.map((feature, idx) => (
                  <li key={idx} className="flex items-start">
                    <CheckIcon className="flex-shrink-0 h-5 w-5 text-indigo-500" />
                    <span className="ml-3 text-slate-300">{feature}</span>
                  </li>
                ))}
              </ul>
            </div>

            <button
              onClick={() => handleCheckout(plan.id)}
              disabled={processingId !== null}
              className={`mt-10 block w-full py-4 px-6 rounded-xl text-center font-bold transition-all duration-300 ${
                plan.id === "elite"
                  ? "bg-indigo-600 hover:bg-indigo-700 text-white shadow-lg shadow-indigo-600/30"
                  : "bg-slate-800 hover:bg-slate-700 text-white"
              } disabled:opacity-50 disabled:cursor-not-allowed`}
            >
              {processingId === plan.id ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Yönlendiriliyor...
                </span>
              ) : (
                "Hemen Başla"
              )}
            </button>
          </div>
        ))}
      </div>
      
      <div className="mt-12 text-center text-slate-500 text-sm">
        Güvenli ödemeler Iyzico altyapısıyla sağlanmaktadır.
      </div>
    </div>
  );
}
