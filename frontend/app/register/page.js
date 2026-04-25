"use client";

import { useState } from "react";
import Link from "next/link";
import { api } from "../../lib/api";

export default function RegisterPage() {
  const [form, setForm] = useState({ username: "", email: "", password: "" });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setLoading(true);
    try {
      const data = await api.register(form);
      setSuccess(data.message + " Giriş yapabilirsiniz.");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-wrapper">
      <div className="auth-card">
        <h1>⚽ Kayıt Ol</h1>
        <p className="subtitle">Ücretsiz hesap oluşturun.</p>

        {error && <div className="error-msg">{error}</div>}
        {success && <div className="success-msg">{success}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Kullanıcı Adı</label>
            <input
              className="input"
              type="text"
              placeholder="en az 3 karakter"
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
              required
              minLength={3}
            />
          </div>
          <div className="form-group">
            <label>E-posta</label>
            <input
              className="input"
              type="email"
              placeholder="ornek@mail.com"
              value={form.email}
              onChange={(e) => setForm({ ...form, email: e.target.value })}
              required
            />
          </div>
          <div className="form-group">
            <label>Şifre</label>
            <input
              className="input"
              type="password"
              placeholder="en az 6 karakter"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
              required
              minLength={6}
            />
          </div>
          <button className="btn btn-primary btn-block" disabled={loading}>
            {loading ? "Kayıt oluşturuluyor..." : "Kayıt Ol"}
          </button>
          <div className="form-footer">
            <Link href="/login">Zaten hesabım var</Link>
          </div>
        </form>
      </div>
    </div>
  );
}
