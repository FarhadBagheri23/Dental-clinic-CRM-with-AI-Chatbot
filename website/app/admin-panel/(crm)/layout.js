import { redirect } from "next/navigation";

import { currentUser } from "../../../lib/auth";
import Sidebar from "./sidebar";

export const metadata = {
  title: "پنل مدیریت کلینیک",
  robots: { index: false, follow: false },
};

// Every CRM page reads live data; never cache or prerender it.
export const dynamic = "force-dynamic";

export default async function CrmLayout({ children }) {
  // The middleware already redirected anonymous requests; this is the
  // second line of defence and gives the pages a guaranteed user object.
  const user = await currentUser();
  if (!user) redirect("/admin-panel");

  return (
    <div className="flex min-h-screen flex-col bg-slate-100 lg:flex-row">
      <Sidebar user={user} />
      <main className="min-w-0 flex-1 px-4 py-8 sm:px-8">{children}</main>
    </div>
  );
}
