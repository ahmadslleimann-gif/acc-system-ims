import { useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../auth/AuthContext";
import i18n, { applyDirection } from "../i18n";
import Brand from "./Brand";

// `perm`: required permission to see the item (undefined = any logged-in user).
// `admin`: only Super Admin / superuser.
const NAV = [
  { to: "/", key: "dashboard", icon: "📊" },
  { to: "/inventory", key: "inventory", icon: "📦", perm: "inventory.view_product" },
  { to: "/sales", key: "sales", icon: "🧾", perm: "sales.view_salesinvoice" },
  { to: "/purchases", key: "purchases", icon: "🛒", perm: "purchases.view_purchaseinvoice" },
  { to: "/customers", key: "customers", icon: "👤", perm: "customers.view_customer" },
  { to: "/suppliers", key: "suppliers", icon: "🏭", perm: "suppliers.view_supplier" },
  { to: "/reports", key: "reports", icon: "📈" },
  // --- admin only (full control) ---
  { to: "/chart-of-accounts", key: "chartOfAccounts", icon: "📒", admin: true, section: true },
  { to: "/journal", key: "journal", icon: "✍️", admin: true },
  { to: "/cash-banks", key: "cashBanks", icon: "🏦", admin: true },
  { to: "/users", key: "users", icon: "🛡️", admin: true },
];

export default function Layout() {
  const { t } = useTranslation();
  const { user, logout, can, isAdmin } = useAuth();
  const location = useLocation();
  const [open, setOpen] = useState(false); // mobile drawer

  function toggleLang() {
    const next = i18n.language === "ar" ? "en" : "ar";
    i18n.changeLanguage(next);
    localStorage.setItem("lang", next);
    applyDirection(next);
  }

  const visibleNav = NAV.filter((item) => {
    if (item.admin) return isAdmin;
    if (item.perm) return isAdmin || can(item.perm);
    return true;
  });

  const isRtl = i18n.language === "ar";
  // Drawer slides in from the inline-start edge; closed state pushes it off-screen
  // toward that edge (RTL = right, LTR = left).
  const closedTransform = open
    ? "translate-x-0"
    : isRtl
    ? "translate-x-full"
    : "-translate-x-full";

  const currentTitle = (() => {
    const active = NAV.find((n) => (n.to === "/" ? location.pathname === "/" : location.pathname.startsWith(n.to)));
    return active ? t(active.key) : t("app");
  })();

  return (
    <div className="min-h-screen flex bg-slate-50">
      {/* Backdrop (mobile only) */}
      {open && (
        <div
          className="fixed inset-0 bg-black/50 z-30 md:hidden"
          onClick={() => setOpen(false)}
          aria-hidden
        />
      )}

      {/* Sidebar: static on md+, fixed slide-out drawer on mobile */}
      <aside
        className={`fixed md:static inset-y-0 start-0 z-40 w-64 shrink-0 bg-gradient-to-b from-slate-900 via-slate-900 to-slate-950 text-white flex flex-col
          transform transition-transform duration-200 md:translate-x-0 ${closedTransform}`}
      >
        <div className="px-5 pt-6 pb-5 border-b border-white/10 flex items-start justify-between">
          <div className="mx-auto w-32">
            <Brand layout="vertical" variant="light" />
          </div>
          <button
            className="md:hidden text-slate-300 hover:text-white text-xl leading-none -mt-1"
            onClick={() => setOpen(false)}
            aria-label="Close menu"
          >
            ✕
          </button>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
          {visibleNav.map((item) => (
            <div key={item.to}>
              {item.section && (
                <div className="px-3 pt-5 pb-2 text-[10px] uppercase tracking-[0.15em] text-slate-500">
                  {t("administration")}
                </div>
              )}
              <NavLink
                to={item.to}
                end={item.to === "/"}
                onClick={() => setOpen(false)}
                className={({ isActive }) =>
                  `group flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors ${
                    isActive
                      ? "bg-brand-600 text-white font-semibold shadow-sm shadow-brand-900/40"
                      : "text-slate-300 hover:bg-white/5 hover:text-white"
                  }`
                }
              >
                <span className="text-base w-5 text-center">{item.icon}</span>
                {t(item.key)}
              </NavLink>
            </div>
          ))}
        </nav>

        <div className="px-5 py-4 border-t border-white/10 flex items-center gap-2.5">
          <div className="h-8 w-8 rounded-full bg-brand-600 grid place-items-center text-xs font-bold uppercase">
            {(user?.username || "?").slice(0, 2)}
          </div>
          <div className="leading-tight min-w-0">
            <div className="text-sm font-medium truncate">{user?.username}</div>
            <div className="text-[11px] text-slate-400 truncate">
              {isAdmin ? "Super Admin" : user?.roles?.join(", ") || "No role"}
            </div>
          </div>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 bg-white/80 backdrop-blur border-b border-slate-200 flex items-center justify-between gap-3 px-4 sm:px-6 sticky top-0 z-20">
          <div className="flex items-center gap-3 min-w-0">
            <button
              className="md:hidden h-9 w-9 grid place-items-center rounded-lg border border-slate-200 text-slate-700"
              onClick={() => setOpen(true)}
              aria-label="Open menu"
            >
              <span className="text-lg leading-none">☰</span>
            </button>
            {/* Page title on mobile, user info on desktop */}
            <span className="md:hidden font-semibold text-slate-800 truncate">{currentTitle}</span>
            <div className="hidden md:block text-sm text-slate-500">
              <span className="font-semibold text-slate-800">{user?.username}</span>
              <span className="mx-2 text-slate-300">·</span>
              <span className="inline-block px-2 py-0.5 rounded-full bg-brand-50 text-brand-700 text-xs font-medium">
                {user?.roles?.join(", ") || (user?.is_superuser ? "Super Admin" : "—")}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            <button
              onClick={toggleLang}
              className="h-9 w-9 grid place-items-center rounded-lg border border-slate-200 text-sm font-semibold text-slate-600 hover:bg-slate-50"
              title={i18n.language === "ar" ? "English" : "العربية"}
            >
              {i18n.language === "ar" ? "EN" : "ع"}
            </button>
            <button onClick={logout} className="btn-ghost text-xs px-3">
              {t("logout")}
            </button>
          </div>
        </header>
        <main className="flex-1 p-4 sm:p-6 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
