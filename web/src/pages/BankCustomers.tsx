import { Link } from 'react-router-dom';
import { customers } from '../bankData';

export function BankCustomers() {
  return (
    <main className="mx-auto max-w-6xl px-6 py-8">
      <header className="mb-7">
        <p className="text-xs font-bold uppercase tracking-[0.18em] text-[#29265f]">
          Customer monitoring
        </p>

        <h1 className="mt-2 text-3xl font-semibold text-[#29265f]">
          Customers
        </h1>

        <p className="mt-2 max-w-2xl text-sm text-slate-600">
          Review customer activity and compare suspicious transactions with
          established behavioral patterns.
        </p>
      </header>

      <section className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
        <div className="border-b border-slate-200 bg-[#f7fbff] px-5 py-4">
          <h2 className="font-semibold text-[#29265f]">
            Customer directory
          </h2>

          <p className="mt-1 text-xs text-slate-500">
            Customer information is masked for operational privacy.
          </p>
        </div>

        <div className="divide-y divide-slate-100">
          {customers.map((customer) => (
            <Link
              key={customer.id}
              to={`/bank/customers/${customer.id}`}
              className="block px-5 py-5 transition hover:bg-[#43cddd]/10"
            >
              <div className="grid gap-5 md:grid-cols-[1.5fr_1fr_0.9fr_0.9fr_auto] md:items-center">
                
                <div>
                  <p className="font-semibold text-[#29265f]">
                    {customer.name}
                  </p>

                  <p className="mt-1 text-xs text-slate-500">
                    {customer.id} · {customer.email}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-slate-500">
                    Card
                  </p>

                  <p className="mt-1 font-mono text-sm">
                    •••• {customer.cardLast4}
                  </p>
                </div>

                <div>
                  <p className="text-xs text-slate-500">
                    Activity
                  </p>

                  <p className="mt-1 text-sm font-medium">
                    {customer.transactions} transactions
                  </p>

                  <p className="text-xs text-slate-500">
                    {customer.volume} volume
                  </p>
                </div>

                <div>
                  <p className="text-xs text-slate-500">
                    Risk
                  </p>

                  <span
                    className={`mt-1 inline-flex rounded-full px-2.5 py-1 text-xs font-bold ${
                      customer.risk === 'HIGH'
                        ? 'bg-orange-100 text-orange-800'
                        : customer.risk === 'MEDIUM'
                        ? 'bg-amber-100 text-amber-800'
                        : 'bg-emerald-100 text-emerald-800'
                    }`}
                  >
                    {customer.risk}
                  </span>
                </div>

                <div className="text-sm font-bold text-[#29265f]">
                  Review customer →
                </div>
              </div>
            </Link>
          ))}
        </div>
      </section>
    </main>
  );
}