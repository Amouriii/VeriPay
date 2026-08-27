import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { VeriPayMark } from '../components/VeriPayMark';

export function BankLogin() {
  const navigate = useNavigate();
  const [showPassword, setShowPassword] = useState(false);
  const [remember, setRemember] = useState(true);
  const [error, setError] = useState('');

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');
    navigate('/fi-ops');
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#43cddd]/15 px-5 py-10 text-[#29265f]">
      <section className="w-full max-w-sm">
        <div className="mb-7 flex justify-center"><VeriPayMark /></div>
        <div className="rounded-2xl border border-[#43cddd]/70 bg-white p-6 shadow-[0_18px_50px_rgba(46,44,131,0.12)] sm:p-8">
          <div className="mb-7"><p className="text-sm font-semibold text-[#007064]">Welcome back</p><h1 className="mt-2 text-2xl font-semibold tracking-tight">Bank Console</h1><p className="mt-3 text-sm leading-6 text-slate-600">Sign in to monitor payment risk and protect your customers.</p></div>
          <form onSubmit={handleSubmit} className="space-y-5">
            <label className="block text-sm font-semibold">Work email<input required type="email" defaultValue="avery.morgan@veripay.example" className="mt-2 w-full rounded-lg border border-[#b9d8d2] bg-white px-4 py-3 font-normal outline-none transition focus:border-[#00a79d] focus:ring-4 focus:ring-[#00a79d]/10" placeholder="name@institution.com" /></label>
            <label className="block text-sm font-semibold">Password<div className="relative mt-2"><input required type={showPassword ? 'text' : 'password'} defaultValue="veripay-demo" className="w-full rounded-lg border border-[#b9d8d2] bg-white px-4 py-3 pr-20 font-normal outline-none transition focus:border-[#00a79d] focus:ring-4 focus:ring-[#00a79d]/10" placeholder="Enter your password" /><button type="button" onClick={() => setShowPassword((value) => !value)} className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-bold text-[#007064]">{showPassword ? 'Hide' : 'Show'}</button></div></label>
            <div className="flex items-center justify-between text-sm"><label className="flex items-center gap-2 text-slate-600"><input type="checkbox" checked={remember} onChange={(event) => setRemember(event.target.checked)} className="h-4 w-4 accent-[#00a79d]" />Remember this device</label><button type="button" className="font-semibold text-[#007064]">Forgot password?</button></div>
            {error && <p className="rounded-lg bg-red-50 p-3 text-sm text-red-700">{error}</p>}
            <button type="submit" className="w-full rounded-lg bg-[#2e2c83] px-4 py-3.5 text-sm font-bold text-white shadow-lg shadow-[#2e2c83]/20 transition hover:bg-[#29265f]">Sign in securely <span aria-hidden="true">-&gt;</span></button>
          </form>
          <div className="mt-6 flex items-start gap-3 rounded-lg border border-[#fac180]/60 bg-[#fac180]/20 p-4 text-xs leading-5 text-[#5a4630]"><span className="text-base">i</span><p><strong>Protected access.</strong> Your activity is recorded for security.</p></div>
        </div>
        <p className="mt-6 text-center text-xs text-slate-500">Need access? Contact your institution administrator.</p>
      </section>
    </main>
  );
}
