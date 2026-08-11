import { http } from "@/shared/api/httpClient";

export const chatApi = {
  status: (signal) => http.get("/chat/status", { signal }),
  ask: (message, history, signal) =>
    http.post("/chat", { message, history }, { signal }),
};

/** Persian labels for the tools an answer used.
 *
 *  Shown so the owner can see which report a number came from and open that
 *  page to check it — an assistant's figures are only worth trusting if they
 *  are traceable back to something on screen.
 */
export const TOOL_LABELS = {
  clinic_context: "بازه داده‌ها",
  search_documents: "اسناد کلینیک",
  revenue_overview: "درآمد و وصولی",
  top_services: "خدمات پردرآمد",
  dentist_performance: "عملکرد پزشکان",
  appointment_losses: "اتلاف نوبت",
  chair_utilisation: "بهره‌وری یونیت",
  treatment_plan_status: "طرح‌های درمان",
  patient_recall: "فراخوان بیماران",
  low_stock: "موجودی انبار",
};
