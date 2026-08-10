import { createBrowserRouter, Navigate } from "react-router-dom";

import { ProtectedRoute } from "@/features/auth/routes/ProtectedRoute";
import { DashboardPage } from "@/pages/DashboardPage";
import { LoginPage } from "@/pages/LoginPage";

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    element: <ProtectedRoute />,
    children: [{ path: "/dashboard", element: <DashboardPage /> }],
  },
  { path: "*", element: <Navigate to="/dashboard" replace /> },
]);
