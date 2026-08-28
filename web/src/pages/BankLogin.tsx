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
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-br from-[#17163a] via-[#1f1d49] to-[#2a2760] px-5 py-10 text-white">
      <section className="w-full max-w-sm">
        <div className="mb-7 flex justify-center">
          <VeriPayMark variant="indigo" />
        </div>

        <div className="rounded-2xl border border-white/10 bg-[#221f4f] p-6 shadow-[0_18px_50px_rgba(0,0,0,0.35)] sm:p-8">
          <div className="mb-7">
            <span className="inline-flex items-center gap-1.5 rounded-full bg-white/10 px-2.5 py-1 text-[10px] font-bold uppercase tracking-[0.18em] text-[#fac180]">
              FI Operations Console
            </span>

            <h1 className="mt-3 text-2xl font-semibold tracking-tight text-white">
              Institutional Access
            </h1>

            <p className="mt-3 text-sm leading-6 text-[#c7c9f5]">
              Sign in to monitor payment risk and protect your customers.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <label className="block text-sm font-semibold text-[#e7e8ff]">
              Work email
              <input
                required
                type="email"
                defaultValue="avery.morgan@veripay.example"
                className="mt-2 w-full rounded-md border border-white/15 bg-white/5 px-4 py-3 font-normal text-white outline-none transition placeholder:text-white/40 focus:border-[#43cddd] focus:ring-4 focus:ring-[#43cddd]/15"
                placeholder="name@institution.com"
              />
            </label>

            <label className="block text-sm font-semibold text-[#e7e8ff]">
              Password
              <div className="relative mt-2">
                <input
                  required
                  type={showPassword ? 'text' : 'password'}
                  defaultValue="veripay-demo"
                  className="w-full rounded-md border border-white/15 bg-white/5 px-4 py-3 pr-20 font-normal text-white outline-none transition placeholder:text-white/40 focus:border-[#43cddd] focus:ring-4 focus:ring-[#43cddd]/15"
                  placeholder="Enter your password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((value) => !value)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-bold text-[#43cddd]"
                >
                  {showPassword ? 'Hide' : 'Show'}
                </button>
              </div>
            </label>

            <div className="flex items-center justify-between text-sm">
              <label className="flex items-center gap-2 text-[#c7c9f5]">
                <input
                  type="checkbox"
                  checked={remember}
                  onChange={(event) => setRemember(event.target.checked)}
                  className="h-4 w-4 accent-[#43cddd]"
                />
                Remember this device
              </label>
              <button type="button" className="font-semibold text-[#43cddd]">
                Forgot password?
              </button>
            </div>

            {error && (
              <p className="rounded-md bg-[#4a1f1f] p-3 text-sm text-[#ffb4ab]">
                {error}
              </p>
            )}

            <button
              type="submit"
              className="w-full rounded-md bg-[#8b8ff2] px-4 py-3.5 text-sm font-bold text-[#1b1a3d] shadow-lg shadow-black/30 transition hover:bg-[#a5a8f7]"
            >
              Sign in securely <span aria-hidden="true">→</span>
            </button>
          </form>

          <div className="mt-6 flex items-start gap-3 rounded-md border border-[#fac180]/30 bg-[#fac180]/10 p-4 text-xs leading-5 text-[#f3d9ae]">
            <span className="text-base">ⓘ</span>
            <p>
              <strong className="text-white">Protected access.</strong> Your
              activity is recorded for security.
            </p>
          </div>
        </div>

        <p className="mt-6 text-center text-xs text-[#9496c9]">
          Need access? Contact your institution administrator.
        </p>
      </section>
    </main>
  );
}