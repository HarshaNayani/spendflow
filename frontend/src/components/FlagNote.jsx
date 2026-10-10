// Shows why a claim was flagged (AI verdict and/or rule checks).
export default function FlagNote({ reason }) {
  if (!reason) return null;
  return (
    <div className="mt-2 flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-800">
      <span aria-hidden="true">⚑</span>
      <p>
        <span className="font-semibold">Flagged for review: </span>
        {reason}
      </p>
    </div>
  );
}
