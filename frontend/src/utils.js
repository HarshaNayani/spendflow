const currency = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

export const formatCurrency = (value) => currency.format(Number(value) || 0);

export function formatDate(value) {
  if (!value) return "";
  const iso = value.length === 10 ? `${value}T00:00:00` : value;
  return new Date(iso).toLocaleDateString("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

// Today's date as YYYY-MM-DD in the user's own time zone.
export function todayISO() {
  const now = new Date();
  const local = new Date(now.getTime() - now.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 10);
}

export function homePath(role) {
  if (role === "admin") return "/dashboard";
  if (role === "manager") return "/approvals";
  return "/my-expenses";
}
