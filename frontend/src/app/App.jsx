import { RouterProvider } from "react-router-dom";

import { AuthProvider } from "@/app/providers/AuthProvider";
import { FiltersProvider } from "@/app/providers/FiltersProvider";
import { router } from "@/app/router";

export function App() {
  return (
    <AuthProvider>
      <FiltersProvider>
        <RouterProvider router={router} />
      </FiltersProvider>
    </AuthProvider>
  );
}
