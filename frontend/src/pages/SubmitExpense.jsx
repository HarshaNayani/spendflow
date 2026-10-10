import { useNavigate } from "react-router-dom";
import api from "../api";
import ExpenseForm from "../components/ExpenseForm";
import { useToast } from "../components/Toast";

export default function SubmitExpense() {
  const navigate = useNavigate();
  const notify = useToast();

  const submit = async (payload) => {
    const { data } = await api.post("/expenses", payload);
    notify(
      data.ai_flag
        ? "Expense submitted. It was flagged, so the manager will look at it first."
        : "Expense submitted for approval."
    );
    navigate("/my-expenses");
  };

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="text-2xl font-bold text-slate-900">Submit an expense</h1>
      <p className="mb-6 mt-1 text-sm text-slate-600">
        Your manager will approve or reject it. AI suggests a category and flags anything unusual.
      </p>
      <div className="card">
        <ExpenseForm submitLabel="Submit for approval" onSubmit={submit} />
      </div>
    </div>
  );
}
