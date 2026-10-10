import { useEffect, useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import api, { errorMessage } from "../api";
import FlagNote from "../components/FlagNote";
import StatusBadge from "../components/StatusBadge";
import { CHART_COLORS } from "../constants";
import { formatCurrency, formatDate } from "../utils";

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .get("/dashboard/summary")
      .then((res) => setData(res.data))
      .catch((err) => setError(errorMessage(err)));
  }, []);

  if (error) return <p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-800">{error}</p>;
  if (!data) return <p className="text-slate-500">Loading the dashboard...</p>;

  const budgetRows = data.budget_vs_spend.map((b) => ({
    category: b.category,
    Budget: b.monthly_limit,
    Spent: b.spent,
  }));
  const overBudget = data.budget_vs_spend.filter((b) => b.used_pct >= 100);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Admin dashboard</h1>
        <p className="mt-1 text-sm text-slate-600">Approved spend, budgets for this month and flagged claims.</p>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <Stat label="Approved spend" value={formatCurrency(data.total_spend)} tone="text-slate-900" />
        <Stat label="Pending" value={data.pending_count} tone="text-amber-600" />
        <Stat label="Rejected" value={data.rejected_count} tone="text-rose-600" />
        <Stat label="Flagged" value={data.flagged_count} tone="text-rose-700" />
      </div>

      {overBudget.length > 0 && (
        <p className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          <b>Over budget this month:</b> {overBudget.map((b) => `${b.category} (${b.used_pct}%)`).join(", ")}
        </p>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        <section className="card">
          <h2 className="mb-3 font-semibold text-slate-900">Spend by category</h2>
          {data.spend_by_category.length === 0 ? (
            <Empty text="No approved expenses yet." />
          ) : (
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data.spend_by_category}
                    dataKey="spend"
                    nameKey="category"
                    innerRadius={55}
                    outerRadius={100}
                    paddingAngle={2}
                  >
                    {data.spend_by_category.map((_, i) => (
                      <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v) => formatCurrency(v)} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </section>

        <section className="card">
          <h2 className="mb-3 font-semibold text-slate-900">Budget vs spend (this month)</h2>
          {budgetRows.length === 0 ? (
            <Empty text="No budgets set." />
          ) : (
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={budgetRows} layout="vertical" margin={{ left: 10, right: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" tickFormatter={(v) => `₹${v / 1000}k`} />
                  <YAxis type="category" dataKey="category" width={105} tick={{ fontSize: 12 }} />
                  <Tooltip formatter={(v) => formatCurrency(v)} />
                  <Legend />
                  <Bar dataKey="Budget" fill="#cbd5e1" radius={[0, 4, 4, 0]} />
                  <Bar dataKey="Spent" fill="#4f46e5" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </section>
      </div>

      <section className="card">
        <h2 className="mb-3 font-semibold text-slate-900">Flagged expenses</h2>
        {data.flagged.length === 0 ? (
          <Empty text="Nothing flagged. Nice." />
        ) : (
          <ul className="divide-y divide-slate-100">
            {data.flagged.map((e) => (
              <li key={e.id} className="py-3 first:pt-0 last:pb-0">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div>
                    <p className="font-medium text-slate-900">{e.description}</p>
                    <p className="text-sm text-slate-500">
                      {e.user_name} · {e.category} · {formatDate(e.expense_date)}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-bold text-slate-900">{formatCurrency(e.amount)}</span>
                    <StatusBadge status={e.status} />
                  </div>
                </div>
                <FlagNote reason={e.ai_reason} />
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

function Stat({ label, value, tone }) {
  return (
    <div className="card">
      <p className="text-sm text-slate-500">{label}</p>
      <p className={`mt-1 text-2xl font-bold ${tone}`}>{value}</p>
    </div>
  );
}

function Empty({ text }) {
  return <p className="py-8 text-center text-sm text-slate-500">{text}</p>;
}
