import { useCallback, useEffect, useState } from "react";
import api, { errorMessage } from "../api";
import FlagNote from "../components/FlagNote";
import { useToast } from "../components/Toast";
import { formatCurrency, formatDate } from "../utils";

export default function Approvals() {
  const notify = useToast();
  const [queue, setQueue] = useState(null);
  const [error, setError] = useState("");
  const [comments, setComments] = useState({});
  const [busyId, setBusyId] = useState(null);

  const load = useCallback(async () => {
    try {
      const { data } = await api.get("/expenses/pending");
      setQueue(data);
      setError("");
    } catch (err) {
      setError(errorMessage(err));
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const decide = async (expense, decision) => {
    const comment = (comments[expense.id] || "").trim();
    if (decision === "rejected" && comment.length < 3) {
      notify("Add a short comment so the employee knows what to fix.", "error");
      return;
    }
    setBusyId(expense.id);
    try {
      await api.patch(`/expenses/${expense.id}/decision`, { decision, comment });
      notify(decision === "approved" ? "Expense approved and locked." : "Expense rejected with your comment.");
      setQueue((list) => list.filter((e) => e.id !== expense.id));
    } catch (err) {
      notify(errorMessage(err), "error");
    } finally {
      setBusyId(null);
    }
  };

  const flaggedCount = (queue || []).filter((e) => e.ai_flag).length;

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">Approval queue</h1>
        <p className="mt-1 text-sm text-slate-600">
          Flagged claims are listed first. Approved expenses are locked and cannot be edited.
        </p>
      </div>

      {error && <p className="mb-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-800">{error}</p>}
      {queue === null && !error && <p className="text-slate-500">Loading the queue...</p>}

      {queue && queue.length === 0 && (
        <div className="card py-12 text-center">
          <p className="font-semibold text-slate-800">All caught up</p>
          <p className="mt-1 text-sm text-slate-500">There are no expenses waiting for your decision.</p>
        </div>
      )}

      {queue && queue.length > 0 && (
        <>
          <p className="mb-3 text-sm text-slate-600">
            {queue.length} waiting{flaggedCount > 0 && <> · <span className="font-semibold text-rose-700">{flaggedCount} flagged</span></>}
          </p>
          <ul className="space-y-4">
            {queue.map((e) => (
              <li key={e.id} className={`card ${e.ai_flag ? "border-rose-300 ring-1 ring-rose-200" : ""}`}>
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div className="min-w-0 flex-1">
                    <p className="font-semibold text-slate-900">{e.description}</p>
                    <p className="mt-0.5 text-sm text-slate-500">
                      {e.user_name} · {e.category} · {formatDate(e.expense_date)}
                    </p>
                  </div>
                  <span className="text-xl font-bold text-slate-900">{formatCurrency(e.amount)}</span>
                </div>

                {e.ai_flag && <FlagNote reason={e.ai_reason} />}

                <label className="label mt-4" htmlFor={`comment-${e.id}`}>
                  Comment <span className="font-normal text-slate-400">(required when rejecting)</span>
                </label>
                <textarea
                  id={`comment-${e.id}`}
                  rows={2}
                  maxLength={500}
                  className="input"
                  placeholder="e.g. Approved, or please attach the bill and resubmit"
                  value={comments[e.id] || ""}
                  onChange={(ev) => setComments((c) => ({ ...c, [e.id]: ev.target.value }))}
                />

                <div className="mt-3 flex justify-end gap-2">
                  <button
                    type="button"
                    disabled={busyId === e.id}
                    onClick={() => decide(e, "rejected")}
                    className="btn btn-danger"
                  >
                    Reject
                  </button>
                  <button
                    type="button"
                    disabled={busyId === e.id}
                    onClick={() => decide(e, "approved")}
                    className="btn btn-success"
                  >
                    Approve
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
