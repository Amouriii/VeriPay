import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { VeriPayMark } from '../components/VeriPayMark';

export function CustomerLogin() {
  const navigate = useNavigate();

  const [showPassword, setShowPassword] = useState(false);
  const [remember, setRemember] = useState(true);
  const [error, setError] = useState('');

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError('');
    navigate('/customer');
  }

  return (
    <main className="flex min-h-screen items-center justify-center bg-gradient-to-br from-[#DCEBFF] via-[#E8E7FF] to-[#DDF5F7] px-5 py-10 text-[#17324D]">

      <section className="w-full max-w-sm">

        <div className="mb-7 flex justify-center">
          <VeriPayMark variant="teal" />
        </div>

        <div className="rounded-2xl border border-[#BFD0EA] bg-gradient-to-br from-[#EDF4FF] via-[#E9EEFF] to-[#EAE7FF] p-6 shadow-[0_18px_50px_rgba(82,104,216,0.16)] sm:p-8">

          <div className="mb-7">

            <p className="text-sm font-semibold text-[#087F7A]">
              Welcome back
            </p>

            <h1 className="mt-2 text-2xl font-semibold tracking-tight text-[#17324D]">
              Personal Banking
            </h1>

            <p className="mt-3 text-sm leading-6 text-[#536B8D]">
              Sign in to securely manage your accounts and review your
              transactions.
            </p>

          </div>

          <form onSubmit={handleSubmit} className="space-y-5">

            <label className="block text-sm font-semibold text-[#17324D]">
              Email

              <input
                required
                type="email"
                defaultValue="jordan.lee@example.com"
                className="mt-2 w-full rounded-lg border border-[#BFD0EA] bg-[#F5F8FF] px-4 py-3 font-normal text-[#17324D] outline-none transition focus:border-[#5268D8] focus:ring-4 focus:ring-[#5268D8]/10"
                placeholder="you@example.com"
              />
            </label>

            <label className="block text-sm font-semibold text-[#17324D]">
              Password

              <div className="relative mt-2">

                <input
                  required
                  type={showPassword ? 'text' : 'password'}
                  defaultValue="veripay-demo"
                  className="w-full rounded-lg border border-[#BFD0EA] bg-[#F5F8FF] px-4 py-3 pr-20 font-normal text-[#17324D] outline-none transition focus:border-[#5268D8] focus:ring-4 focus:ring-[#5268D8]/10"
                  placeholder="Enter your password"
                />

                <button
                  type="button"
                  onClick={() =>
                    setShowPassword((value) => !value)
                  }
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-bold text-[#5268D8]"
                >
                  {showPassword ? 'Hide' : 'Show'}
                </button>

              </div>
            </label>

            <div className="flex items-center justify-between gap-3 text-sm">

              <label className="flex items-center gap-2 text-[#536B8D]">

                <input
                  type="checkbox"
                  checked={remember}
                  onChange={(event) =>
                    setRemember(event.target.checked)
                  }
                  className="h-4 w-4 accent-[#5268D8]"
                />

                Remember me
              </label>

              <button
                type="button"
                className="font-semibold text-[#5268D8]"
              >
                Forgot password?
              </button>

            </div>

            {error && (
              <p className="rounded-lg border border-[#C0392B]/30 bg-[#FFF1F4] p-3 text-sm text-[#C0392B]">
                {error}
              </p>
            )}

            <button
              type="submit"
              className="w-full rounded-lg bg-gradient-to-r from-[#5268D8] via-[#7566C9] to-[#087F7A] px-4 py-3.5 text-sm font-bold text-white shadow-lg shadow-[#5268D8]/25 transition hover:from-[#465BC9] hover:via-[#6656B8] hover:to-[#05635F]"
            >
              Sign in securely

              <span className="ml-2" aria-hidden="true">
                →
              </span>
            </button>

          </form>

          <div className="mt-6 flex items-start gap-3 rounded-lg border border-[#B9DCD9] bg-[#E0F5F4] p-4 text-xs leading-5 text-[#536B8D]">

            <span className="text-base text-[#087A5E]">
              ✓
            </span>

            <p>
              <strong className="text-[#17324D]">
                Secure personal banking.
              </strong>{' '}
              Your account and transaction activity are protected by VeriPay.
            </p>

          </div>

        </div>

        <p className="mt-6 text-center text-xs text-[#536B8D]">
          Having trouble signing in? Contact your bank.
        </p>

      </section>
    </main>
  );
}