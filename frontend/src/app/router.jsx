import { createBrowserRouter, Navigate } from "react-router-dom";

import { PanelLayout } from "@/app/layouts/PanelLayout";
import { ProtectedRoute } from "@/features/auth/routes/ProtectedRoute";
import { AppointmentsPage } from "@/pages/AppointmentsPage";
import { DashboardPage } from "@/pages/DashboardPage";
import { DentistsPage } from "@/pages/DentistsPage";
import { FinancePage } from "@/pages/FinancePage";
import { InventoryPage } from "@/pages/InventoryPage";
import { InvoicesPage } from "@/pages/InvoicesPage";
import { LoginPage } from "@/pages/LoginPage";
import { OperationsPage } from "@/pages/OperationsPage";
import { PatientsPage } from "@/pages/PatientsPage";
import { RevenuePage } from "@/pages/RevenuePage";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    // ProtectedRoute gates, PanelLayout frames. Every page added under here
    // is authenticated by default — forgetting a check cannot leak data.
    element: <ProtectedRoute />,
    children: [
      {
        element: <PanelLayout />,
        children: [
          { path: "/dashboard", element: <DashboardPage /> },
          { path: "/revenue", element: <RevenuePage /> },
          { path: "/dentists", element: <DentistsPage /> },
          { path: "/operations", element: <OperationsPage /> },
          { path: "/finance", element: <FinancePage /> },
          { path: "/patients", element: <PatientsPage /> },
          { path: "/appointments", element: <AppointmentsPage /> },
          { path: "/invoices", element: <InvoicesPage /> },
          { path: "/inventory", element: <InventoryPage /> },
        ],
      },
    ],
  },
  { path: "*", element: <Navigate to="/dashboard" replace /> },
]);
