import axios from "axios";

export const API_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "");

const api = axios.create({ baseURL: API_URL, timeout: 30000 });

// Send the JWT with every request.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("sf_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// An expired or invalid token logs the user out (but not on the login call itself).
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const url = error.config?.url || "";
    if (error.response?.status === 401 && !url.startsWith("/auth/login")) {
      window.dispatchEvent(new Event("sf-unauthorized"));
    }
    return Promise.reject(error);
  }
);

// Turn any API error into a short message for a toast or form.
export function errorMessage(error) {
  if (!error.response) {
    return "Cannot reach the server. Check your connection and try again.";
  }
  const detail = error.response.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length) {
    return detail
      .map((d) => `${(d.loc || []).slice(1).join(".") || "input"}: ${d.msg}`)
      .join("; ");
  }
  return "Something went wrong. Please try again.";
}

export default api;
