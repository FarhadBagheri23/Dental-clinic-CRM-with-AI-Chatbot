import { http } from "@/shared/api/httpClient";

const get = (path, qs, signal) => http.get(`/analytics/${path}${qs}`, { signal });

export const analyticsApi = {
  options: (signal) => http.get("/analytics/filters", { signal }),
  revenueByCategory: (qs, signal) => get("revenue-by-category", qs, signal),
  serviceMix: (qs, signal) => get("service-mix", qs, signal),
  dentists: (qs, signal) => get("dentists", qs, signal),
  appointmentTrend: (qs, signal) => get("appointment-trend", qs, signal),
  heatmap: (qs, signal) => get("heatmap", qs, signal),
  chairs: (qs, signal) => get("chairs", qs, signal),
  receivables: (qs, signal) => get("receivables", qs, signal),
  paymentMethods: (qs, signal) => get("payment-methods", qs, signal),
  consumableCost: (qs, signal) => get("consumable-cost", qs, signal),
  patients: (qs, signal) => get("patients", qs, signal),
};
