import { http } from "@/shared/api/httpClient";

export const dashboardApi = {
  summary: (signal) => http.get("/dashboard", { signal }),
  revenueTrend: (signal) => http.get("/dashboard/revenue-trend", { signal }),
  dentists: (signal) => http.get("/dashboard/dentists", { signal }),
  services: (signal) => http.get("/dashboard/services?limit=6", { signal }),
  inventory: (signal) => http.get("/dashboard/inventory", { signal }),
};

export const recordsApi = {
  patients: ({ q = "", page = 1 }, signal) =>
    http.get(`/patients?q=${encodeURIComponent(q)}&page=${page}`, { signal }),
  appointments: ({ status = "", page = 1 }, signal) =>
    http.get(`/appointments?status=${encodeURIComponent(status)}&page=${page}`, { signal }),
  invoices: ({ status = "", page = 1 }, signal) =>
    http.get(`/invoices?status=${encodeURIComponent(status)}&page=${page}`, { signal }),
};
