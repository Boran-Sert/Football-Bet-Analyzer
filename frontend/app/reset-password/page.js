"use client";

import { useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { api } from "../../lib/api";
import { Suspense } from "react";

function ResetForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const tokenFromUrl = searchParams.get("token") || "";

  const [form, setForm] = useState({ token: tokenFromUrl, new_password: "" });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);
    try {
      const data = await api.resetPassword(form);
      setSuccess(data.message);
      setTimeout(() => router.push("/login"), 2000);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-wrapper">
      <div className="auth-card">
        <h1>🔐 Yeni Şifre Belirle</h1>
        <p className="subtitle">Yeni şifrenizi girin.</p>

        {error && <div className="error-msg">{error}</div>}
        {success && <div className="success-msg">{success}</div>}

        <form onSubmit={handleSubmit}>
          {!tokenFromUrl && (
            <div className="form-group">
              <label>Sıfırlama Token</label>
              <input
                className="input"
                type="text"
                placeholder="E-posta ile gelen token"
                value={form.token}
                onChange={(e) => setForm({ ...form, token: e.target.value })}
                required
              />
            </div>
          )}
          <div className="form-group">
            <label>Yeni Şifre</label>
            <input
              className="input"
              type="password"
              placeholder="en az 6 karakter"
              value={form.new_password}
              onChange={(e) => setForm({ ...form, new_password: e.target.value })}
              required
              minLength={6}
            />
          </div>
          <button className="btn btn-primary btn-block" disabled={loading}>
            {loading ? "Güncelleniyor..." : "Şifremi Güncelle"}
          </button>
          <div className="form-footer">
            <Link href="/login">Giriş sayfasına dön</Link>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="spinner" />}>
      <ResetForm />
    </Suspense>
  );
}
