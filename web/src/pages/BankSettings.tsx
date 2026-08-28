export function BankSettings() {
  return (
    <main className="mx-auto max-w-4xl px-6 py-8">
      <header className="mb-8">
        <p className="text-xs font-bold uppercase tracking-[0.18em] text-[#2e2c83]">
          Administration
        </p>

        <h1 className="mt-2 text-3xl font-semibold tracking-tight text-[#29265f]">
          Settings
        </h1>

        <p className="mt-2 text-sm text-slate-600">
          Manage your account, review preferences, and security controls.
        </p>
      </header>

      <div className="space-y-5">
        {/* Account */}
        <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-6 py-5">
            <h2 className="font-semibold text-[#29265f]">Account</h2>
            <p className="mt-1 text-sm text-slate-500">
              Administrator account information.
            </p>
          </div>

          <div className="grid gap-5 px-6 py-5 sm:grid-cols-2">
            <InfoItem label="Name" value="Avery Morgan" />
            <InfoItem label="Role" value="Risk Manager" />
            <InfoItem label="Email" value="avery.morgan@veripay.com" />

            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-500">
                Account status
              </p>

              <div className="mt-2 flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-emerald-500" />
                <span className="text-sm font-semibold text-emerald-700">
                  Active
                </span>
              </div>
            </div>
          </div>
        </section>

        {/* Security */}
        <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-6 py-5">
            <h2 className="font-semibold text-[#29265f]">Security</h2>
            <p className="mt-1 text-sm text-slate-500">
              Security controls for administrator access.
            </p>
          </div>

          <div className="divide-y divide-slate-100">
            <SecurityItem
              title="Multi-factor authentication"
              description="Additional verification is required when signing in."
              value="Enabled"
            />

            <SecurityItem
              title="Session timeout"
              description="Automatic sign-out after a period of inactivity."
              value="30 minutes"
            />

            <SecurityItem
              title="Last sign-in"
              description="Most recent administrator access."
              value="Today, 09:14"
            />
          </div>
        </section>

        {/* Review preferences */}
        <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-6 py-5">
            <h2 className="font-semibold text-[#29265f]">
              Review preferences
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Defaults used when reviewing transactions and fraud alerts.
            </p>
          </div>

          <div className="divide-y divide-slate-100">
            <PreferenceItem
              title="Default transaction view"
              description="The transaction information shown when opening the review queue."
              value="Detailed"
            />

            <PreferenceItem
              title="Transactions per page"
              description="Number of transactions displayed in the review table."
              value="25"
            />

            <PreferenceItem
              title="High-risk action confirmation"
              description="Require confirmation before applying a high-risk decision."
              value="Required"
            />
          </div>
        </section>

        {/* Risk controls */}
        <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="border-b border-slate-200 px-6 py-5">
            <h2 className="font-semibold text-[#29265f]">
              Risk & review controls
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Current rules used to prioritize suspicious transactions.
            </p>
          </div>

          <div className="grid gap-5 px-6 py-5 sm:grid-cols-2">
            <InfoItem
              label="Critical risk threshold"
              value="90+ risk score"
            />

            <InfoItem
              label="High risk threshold"
              value="70–89 risk score"
            />

            <InfoItem
              label="Automatic blocking"
              value="Critical transactions"
            />

            <InfoItem
              label="Customer baseline"
              value="Enabled"
            />
          </div>
        </section>

        {/* Audit */}
        <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="flex items-center justify-between gap-6 px-6 py-5">
            <div>
              <h2 className="font-semibold text-[#29265f]">
                Audit & compliance
              </h2>

              <p className="mt-1 text-sm leading-6 text-slate-500">
                Administrator sign-ins, policy changes, and transaction
                decisions are recorded in the audit log.
              </p>
            </div>

            <span className="shrink-0 rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-bold text-emerald-700">
              Active
            </span>
          </div>
        </section>
      </div>
    </main>
  );
}

function InfoItem({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div>
      <p className="text-xs font-semibold uppercase tracking-[0.1em] text-slate-500">
        {label}
      </p>

      <p className="mt-2 text-sm font-semibold text-[#29265f]">
        {value}
      </p>
    </div>
  );
}

function SecurityItem({
  title,
  description,
  value,
}: {
  title: string;
  description: string;
  value: string;
}) {
  return (
    <div className="flex items-center justify-between gap-6 px-6 py-5">
      <div>
        <p className="text-sm font-semibold text-[#29265f]">{title}</p>

        <p className="mt-1 max-w-2xl text-sm text-slate-500">
          {description}
        </p>
      </div>

      <span className="shrink-0 rounded-full bg-emerald-50 px-3 py-1.5 text-xs font-bold text-emerald-700">
        {value}
      </span>
    </div>
  );
}

function PreferenceItem({
  title,
  description,
  value,
}: {
  title: string;
  description: string;
  value: string;
}) {
  return (
    <div className="flex items-center justify-between gap-6 px-6 py-5">
      <div>
        <p className="text-sm font-semibold text-[#29265f]">{title}</p>

        <p className="mt-1 max-w-2xl text-sm text-slate-500">
          {description}
        </p>
      </div>

      <span className="shrink-0 rounded-md bg-[#f7fbff] px-3 py-1.5 text-xs font-bold text-[#29265f]">
        {value}
      </span>
    </div>
  );
}