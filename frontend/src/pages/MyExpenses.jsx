import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { errorMessage } from "../api";
import ExpenseForm from "../components/ExpenseForm";
import FlagNote from "../components/FlagNote";
import StatusBadge from "../components/StatusBadge";
import { useToast } from "../components/Toast";
import { formatCurrency, formatDate } from "../utils";

export default function MyExpenses() {
  const notify = useToast();
  const [expenses, setExpenses] = useState(null);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(null);

  const load = useCallback(async () => {
    try {
      const { data } = await api.get("/expenses/mine");
      setExpenses(data);
      setError("");
    } catch (err) {
      setError(errorMessage(err));
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const remove = async (expense) => {
    if (!window.confirm(`Delete "${expense.description}"?`)) return;
    try {
      await api.delete(`/expenses/${expense.id}`);
      notify("Expense deleted.");
      load();
    } catch (err) {
      notify(errorMessage(err), "error");
    }
  };

  const resubmit = async (payload) => {
    await api.put(`/expenses/${editing.id}`, payload);
    notify("Expense updated and sent for approval again.");
    setEditing(null);
    load();
  };

  const count = (status) => (expenses || []).filter((e) => e.status === status).length;

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">My expenses</h1>
          <p className="mt-1 text-sm text-slate-600">Track every claim and read your manager's comments.</p>
        </div>
        <Link to="/submit" className="btn btn-primary">
          + New expense
        </Link>
      </div>

      {error && <p className="mb-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-800">{error}</p>}

      {expenses === null && !error && <p className="text-slate-500">Loading your expenses...</p>}

      {expenses && expenses.length === 0 && (
        <div className="card py-12 text-center">
          <p className="font-semibold text-slate-800">No expenses yet</p>
          <p className="mt-1 text-sm text-slate-500">Submit your first expense to start the approval flow.</p>
        </div>
      )}

      {expenses && expenses.length > 0 && (
        <>
          <div className="mb-4 grid grid-cols-3 gap-3">
            <Stat label="Pending" value={count("pending")} tone="text-amber-600" />
            <Stat label="Approved" value={count("approved")} tone="text-emerald-600" />
            <Stat label="Rejected" value={count("rejected")} tone="text-rose-600" />
          </div>

          <ul className="space-y-3">
            {expenses.map((e) => (
              <li key={e.id} className="card">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <p className="font-semibold text-slate-900">{e.description}</p>
                    <p className="mt-0.5 text-sm text-slate-500">
                      {e.category} · {formatDate(e.expense_date)}
                    </p>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-lg font-bold text-slate-900">{formatCurrency(e.amount)}</span>
                    <StatusBadge status={e.status} />
                  </div>
                </div>

                {e.ai_flag && <FlagNote reason={e.ai_reason} />}

                {e.manager_comment && (
                  <p
                    className={`mt-2 rounded-lg px-3 py-2 text-sm ${
                      e.status === "rejected"
                        ? "border border-rose-200 bg-rose-50 text-rose-800"
                        : "bg-slate-50 text-slate-700"
                    }`}
                  >
                    <span className="font-semibold">Manager: </span>
                    {e.manager_comment}
                  </p>
                )}

                <div className="mt-3 flex items-center justify-end gap-2">
                  {e.locked ? (
                    <span className="text-sm font-medium text-slate-500">🔒 Approved and locked</span>
                  ) : (
                    <>
                      <button type="button" onClick={() => remove(e)} className="btn btn-ghost">
                        Delete
                      </button>
                      <button type="button" onClick={() => setEditing(e)} className="btn btn-primary">
                        {e.status === "rejected" ? "Fix and resubmit" : "Edit"}
                      </button>
                    </>
                  )}
                </div>
              </li>
            ))}
          </ul>
        </>
      )}

      {editing && (
        <div
          className="fixed inset-0 z-40 flex items-center justify-center bg-slate-900/40 px-4"
          role="dialog"
          aria-modal="true"
          aria-label="Edit expense"
        >
          <div className="card max-h-[90vh] w-full max-w-xl overflow-y-auto">
            <h2 className="mb-1 text-lg font-bold text-slate-900">
              {editing.status === "rejected" ? "Fix and resubmit" : "Edit expense"}
            </h2>
            {editing.status === "rejected" && editing.manager_comment && (
              <p className="mb-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-800">
                Manager said: {editing.manager_comment}
              </p>
            )}
            <ExpenseForm
              initial={editing}
              submitLabel="Save and send for approval"
              onSubmit={resubmit}
              onCancel={() => setEditing(null)}
            />
          </div>
        </div>
      )}
    </div>
  );
}

function Stat({ label, value, tone }) {
  return (
    <div className="card !p-4 text-center">
      <p className={`text-2xl font-bold ${tone}`}>{value}</p>
      <p className="text-sm text-slate-500">{label}</p>
    </div>
  );
}
