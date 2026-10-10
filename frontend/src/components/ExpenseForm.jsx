import { useState } from "react";
import api, { errorMessage } from "../api";
import { CATEGORIES } from "../constants";
import { formatCurrency, todayISO } from "../utils";

// Shared by "Submit Expense" and the "Fix and resubmit" dialog.
// While the user fills the form, the AI suggests a category and flags odd claims.
// If the AI is unavailable, the form keeps working with a manual category.
export default function ExpenseForm({ initial, submitLabel, onSubmit, onCancel }) {
  const [form, setForm] = useState({
    amount: initial?.amount ?? "",
    description: initial?.description ?? "",
    expense_date: initial?.expense_date ?? todayISO(),
    category: initial?.category ?? "",
  });
  const [ai, setAi] = useState(null); // null | { loading } | result
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const set = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  const askAi = async () => {
    const amount = Number(form.amount);
    if (form.description.trim().length < 3 || !(amount > 0)) return;
    setAi({ loading: true });
    try {
      const { data } = await api.post("/ai/categorize", {
        description: form.description.trim(),
        amount,
      });
      setAi(data);
      // Pre-select the suggestion only if the user has not chosen a category yet.
      if (data.category && !form.category) {
        setForm((f) => ({ ...f, category: data.category }));
      }
    } catch {
      setAi({ ai_available: false, category: null, is_unusual: false, reason: "" });
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      await onSubmit({
        amount: Number(form.amount),
        description: form.description.trim(),
        expense_date: form.expense_date,
        category: form.category || null,
      });
    } catch (err) {
      setError(errorMessage(err));
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2">
        <div>
          <label className="label" htmlFor="amount">
            Amount (₹)
          </label>
          <input
            id="amount"
            type="number"
            min="1"
            step="0.01"
            required
            className="input"
            placeholder="e.g. 2500"
            value={form.amount}
            onChange={set("amount")}
            onBlur={askAi}
          />
        </div>
        <div>
          <label className="label" htmlFor="expense_date">
            Expense date
          </label>
          <input
            id="expense_date"
            type="date"
            required
            max={todayISO()}
            className="input"
            value={form.expense_date}
            onChange={set("expense_date")}
          />
        </div>
      </div>

      <div>
        <label className="label" htmlFor="description">
          Description
        </label>
        <textarea
          id="description"
          required
          minLength={3}
          maxLength={500}
          rows={3}
          className="input"
          placeholder="What was this for? Be specific, e.g. Cab to the client office"
          value={form.description}
          onChange={set("description")}
          onBlur={askAi}
        />
      </div>

      <div>
        <div className="mb-1 flex items-center justify-between">
          <label className="label !mb-0" htmlFor="category">
            Category
          </label>
          <button type="button" onClick={askAi} className="text-sm font-medium text-brand-600 hover:underline">
            Check with AI
          </button>
        </div>
        <select id="category" className="input" value={form.category} onChange={set("category")}>
          <option value="">Auto (AI suggestion, or Other)</option>
          {CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </div>

      <AiPanel ai={ai} amount={form.amount} onUse={(c) => setForm((f) => ({ ...f, category: c }))} current={form.category} />

      {error && (
        <p role="alert" className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-800">
          {error}
        </p>
      )}

      <div className="flex justify-end gap-2">
        {onCancel && (
          <button type="button" onClick={onCancel} className="btn btn-ghost">
            Cancel
          </button>
        )}
        <button type="submit" disabled={saving} className="btn btn-primary">
          {saving ? "Saving..." : submitLabel}
        </button>
      </div>
    </form>
  );
}

function AiPanel({ ai, amount, onUse, current }) {
  if (!ai) {
    return (
      <p className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-500">
        AI will suggest a category and check this claim once you enter the amount and description.
      </p>
    );
  }
  if (ai.loading) {
    return <p className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-500">AI is checking your claim...</p>;
  }
  return (
    <div className="space-y-2">
      {ai.ai_available && ai.category ? (
        <div className="flex flex-wrap items-center gap-2 rounded-lg border border-indigo-200 bg-indigo-50 px-3 py-2 text-sm text-indigo-900">
          <span>
            AI suggests: <b>{ai.category}</b>
          </span>
          {current !== ai.category && (
            <button type="button" onClick={() => onUse(ai.category)} className="font-semibold text-brand-600 hover:underline">
              Use this
            </button>
          )}
        </div>
      ) : (
        <p className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-600">
          AI is unavailable right now. Please select a category yourself.
        </p>
      )}
      {ai.is_unusual && (
        <p className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-sm text-amber-900">
          <b>This claim will be flagged for the manager.</b> {ai.reason}
          {Number(amount) > 0 && <span className="text-amber-700"> ({formatCurrency(amount)})</span>}
        </p>
      )}
    </div>
  );
}
