import axios from "axios";

const baseURL = import.meta.env.VITE_API_BASE_URL || "";

export const api = axios.create({
  baseURL,
  timeout: 60000,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("cs_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status;
    if (status === 401) {
      localStorage.removeItem("cs_token");
      localStorage.removeItem("cs_user");
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
    }
    const detail = error?.response?.data?.detail || error.message || "Request failed";
    return Promise.reject(new Error(typeof detail === "string" ? detail : "Request failed"));
  }
);

export const AuthAPI = {
  login: (email: string, password: string) => api.post("/api/auth/login", { email, password }).then((r) => r.data),
  me: () => api.get("/api/auth/me").then((r) => r.data),
  logout: () => api.post("/api/auth/logout").then((r) => r.data),
};

export const DashboardAPI = {
  stats: () => api.get("/api/dashboard/stats").then((r) => r.data),
  health: () => api.get("/health").then((r) => r.data),
};

export const IncidentsAPI = {
  list: (params?: Record<string, string>) => api.get("/api/incidents", { params }).then((r) => r.data),
  get: (id: string) => api.get(`/api/incidents/${id}`).then((r) => r.data),
  investigate: (id: string) => api.post(`/api/incidents/${id}/investigate`).then((r) => r.data),
  evidence: (id: string) => api.get(`/api/incidents/${id}/evidence`).then((r) => r.data),
  recommendations: (id: string) => api.get(`/api/incidents/${id}/recommendations`).then((r) => r.data),
  approve: (incidentId: string, actionId: string) =>
    api.post(`/api/incidents/${incidentId}/actions/${actionId}/approve`).then((r) => r.data),
  reject: (incidentId: string, actionId: string, reason?: string) =>
    api.post(`/api/incidents/${incidentId}/actions/${actionId}/reject`, { reason }).then((r) => r.data),
  verify: (id: string) => api.post(`/api/incidents/${id}/verify`).then((r) => r.data),
  resolve: (id: string) => api.post(`/api/incidents/${id}/resolve`).then((r) => r.data),
  report: (id: string) => api.get(`/api/incidents/${id}/report/json`).then((r) => r.data),
  reportPdfUrl: (id: string) => `${baseURL}/api/incidents/${id}/report/pdf`,
};

export const LogsAPI = {
  list: (params?: Record<string, string>) => api.get("/api/logs", { params }).then((r) => r.data),
  get: (id: string) => api.get(`/api/logs/${id}`).then((r) => r.data),
  create: (rows: unknown) => api.post("/api/logs", rows).then((r) => r.data),
  upload: (file: File) => {
    const body = new FormData();
    body.append("file", file);
    return api.post("/api/logs/upload", body, { headers: { "Content-Type": "multipart/form-data" } }).then((r) => r.data);
  },
};

export const AssetsAPI = {
  list: () => api.get("/api/assets").then((r) => r.data),
  get: (id: string) => api.get(`/api/assets/${id}`).then((r) => r.data),
};

export const IntelAPI = {
  list: () => api.get("/api/threat-intel").then((r) => r.data),
  create: (payload: unknown) => api.post("/api/threat-intel", payload).then((r) => r.data),
};

export const DemoAPI = {
  load: () => api.post("/api/demo/load").then((r) => r.data),
  reset: () => api.post("/api/demo/reset").then((r) => r.data),
};
