import { Outlet } from "react-router-dom";

export function AuthLayout() {
  return (
    <main className="min-h-screen bg-[radial-gradient(circle_at_top_right,_rgba(59,130,246,0.2),_transparent_22%),radial-gradient(circle_at_bottom_left,_rgba(34,211,238,0.14),_transparent_24%),linear-gradient(180deg,_rgba(2,6,23,1),_rgba(15,23,42,1))] px-4 py-6 text-slate-100">
      <Outlet />
    </main>
  );
}
