"use client";

import { useState } from "react";
import Link from "next/link";
import { api } from "../../lib/api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setMessage("");
    setLoading(true);
    try {
      const data = await api.forgotPassword({ email });
      setMessage(data.message);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-wrapper">
      <div className="auth-card">
        <h1>🔑 Şifremi Unuttum</h1>
        <p className="subtitle">Kayıtlı e-posta adresinize sıfırlama bağlantısı göndereceğiz.</p>

        {error && <div className="error-msg">{error}</div>}
        {message && <div className="success-msg">{message}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>E-posta Adresi</label>
            <input
              className="input"
              type="email"
              placeholder="ornek@mail.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <button className="btn btn-primary btn-block" disabled={loading}>
            {loading ? "Gönderiliyor..." : "Sıfırlama Bağlantısı Gönder"}
          </button>
          <div className="form-footer">
            <Link href="/login">Giriş sayfasına dön</Link>
          </div>
        </form>
      </div>
    </div>
  );
}
