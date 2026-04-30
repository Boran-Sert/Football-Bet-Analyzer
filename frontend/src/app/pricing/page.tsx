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
        // Redirect to register with plan_id
        window.location.href = `/register?plan=${planId}`;
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
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-primary"></div>
        <span className="text-slate-500 font-bold text-xs uppercase tracking-widest">Planlar Yükleniyor...</span>
      </div>
    );
  }

  return (
    <div className="py-12 relative overflow-hidden">
      {/* Background Glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[600px] bg-primary/5 blur-[120px] rounded-full pointer-events-none"></div>

      <div className="text-center mb-20 relative z-10">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-[10px] font-black uppercase tracking-widest mb-6">
          Premium Üyelik
        </div>
        <h1 className="text-5xl font-black text-white sm:text-6xl tracking-tighter uppercase mb-6">
          Analiz Gücünü <span className="text-primary italic">Serbest Bırak</span>
        </h1>
        <p className="max-w-2xl mx-auto text-lg text-slate-400 font-medium">
          Size en uygun planı seçin, veriye dayalı profesyonel tahminlerle kazanmaya başlayın.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-8 md:grid-cols-3 lg:max-w-7xl lg:mx-auto px-4">
        {plans.map((plan) => {
          const isElite = plan.id === "elite";
          return (
            <div
              key={plan.id}
              className={`relative flex flex-col p-10 glass rounded-[2.5rem] transition-all duration-500 hover:translate-y-[-8px] border ${
                isElite ? "border-primary/30 emerald-glow" : "border-white/5"
              }`}
            >
              {isElite && (
                <div className="absolute top-0 right-10 transform -translate-y-1/2">
                  <span className="inline-flex items-center px-4 py-1.5 rounded-full text-[10px] font-black bg-primary text-black uppercase tracking-widest">
                    EN POPÜLER
                  </span>
                </div>
              )}

              <div className="flex-1">
                <div className="flex items-center justify-between mb-8">
                   <h3 className="text-2xl font-black text-white uppercase tracking-tight">{plan.name}</h3>
                   <div className={`w-12 h-12 rounded-2xl flex items-center justify-center ${isElite ? 'bg-primary/20' : 'bg-white/5'}`}>
                      <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke={isElite ? "#10b981" : "#64748b"} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3z"/></svg>
                   </div>
                </div>

                <div className="mt-4 flex items-baseline text-white mb-10">
                  <span className="text-6xl font-black tracking-tighter">₺{Math.floor(plan.price_try)}</span>
                  <span className="text-2xl font-black text-slate-500 ml-1">.{ (plan.price_try % 1).toFixed(2).split('.')[1] }</span>
                  <span className="ml-2 text-xs font-bold text-slate-500 uppercase tracking-widest">/ aylık</span>
                </div>

                <ul className="space-y-5 mb-12">
                  {plan.features.map((feature, idx) => (
                    <li key={idx} className="flex items-center gap-3">
                      <div className={`p-1 rounded-full ${isElite ? 'bg-primary/20 text-primary' : 'bg-white/10 text-slate-400'}`}>
                        <CheckIcon className="h-3 w-3" />
                      </div>
                      <span className="text-sm font-bold text-slate-300">{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <button
                onClick={() => handleCheckout(plan.id)}
                disabled={processingId !== null}
                className={`w-full py-5 rounded-[1.5rem] font-black uppercase text-xs tracking-[0.2em] transition-all duration-300 ${
                  isElite
                    ? "bg-primary text-black hover:scale-[1.03] active:scale-[0.98] emerald-glow"
                    : "bg-white/5 text-white hover:bg-white/10"
                } disabled:opacity-50`}
              >
                {processingId === plan.id ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    İŞLENİYOR...
                  </span>
                ) : (
                  "HEMEN BAŞLA"
                )}
              </button>
            </div>
          );
        })}
      </div>
      
      <div className="mt-20 text-center relative z-10">
        <div className="p-6 glass inline-block rounded-3xl border border-white/5">
           <div className="flex items-center gap-4 text-slate-500">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
              <span className="text-[10px] font-black uppercase tracking-[0.2em]">Güvenli ödemeler <span className="text-white">Iyzico</span> altyapısıyla sağlanmaktadır.</span>
           </div>
        </div>
      </div>
    </div>
  );
}
