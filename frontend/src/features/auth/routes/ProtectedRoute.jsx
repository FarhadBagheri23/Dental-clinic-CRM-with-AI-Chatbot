import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "@/features/auth/hooks/useAuth";
import { SplashScreen } from "@/shared/ui/SplashScreen";

export function ProtectedRoute() {
  const { status } = useAuth();
  const location = useLocation();

  if (status === "loading") return <SplashScreen />;

  if (status !== "authenticated") {
    // `state.from` lets the login page send the user back where they aimed.
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }

  return <Outlet />;
}
