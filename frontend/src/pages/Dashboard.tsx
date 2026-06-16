import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";

interface Summary {
  total_sales: string;
  total_purchases: string;
  total_expenses: string;
  cash_balance: string;
  bank_balance: string;
  receivables: string;
  payables: string;
  recent_transactions: { entry_no: string; date: string; memo: string; amount: string; source_type: string }[];
}

function Kpi({ label, value, accent }: { label: string; value: string; accent?: string }) {
  return (
    <div className="card p-5">
      <div className="text-sm text-slate-500">{label}</div>
      <div className={`mt-2 text-2xl font-bold ${accent || "text-slate-800"}`}>{value}</div>
    </div>
  );
}

export default function Dashboard() {
  const { t } = useTranslation();
  const { user, isAdmin } = useAuth();
  const { data, isLoading } = useQuery({
    queryKey: ["dashboard"],
    queryFn: async () => (await api.get<Summary>("/dashboard/summary/")).data,
  });

  if (isLoading || !data) return <div className="text-slate-500">Loading…</div>;
  const fmt = (v: string) => Number(v).toLocaleString(undefined, { minimumFractionDigits: 2 });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h1 className="text-2xl font-bold text-slate-800">{t("dashboard")}</h1>
        <div className="text-sm text-slate-600">
          Signed in as <span className="font-semibold">{user?.username}</span> ·{" "}
          <span className="px-2 py-0.5 rounded bg-brand-50 text-brand-700">
            {isAdmin ? "Super Admin" : user?.roles?.join(", ") || "No role"}
          </span>
        </div>
      </div>
      {!isAdmin && (
        <div className="rounded-lg bg-amber-50 border border-amber-200 text-amber-800 text-sm px-4 py-2">
          You have role-limited access. Some menus and actions are hidden based on your permissions.
        </div>
      )}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Kpi label={t("totalSales")} value={fmt(data.total_sales)} accent="text-brand-700" />
        <Kpi label={t("totalPurchases")} value={fmt(data.total_purchases)} />
        <Kpi label={t("cashBalance")} value={fmt(data.cash_balance)} />
        <Kpi label={t("bankBalance")} value={fmt(data.bank_balance)} />
        <Kpi label={t("receivables")} value={fmt(data.receivables)} accent="text-amber-600" />
        <Kpi label={t("payables")} value={fmt(data.payables)} accent="text-amber-600" />
      </div>

      <div className="card p-5">
        <h2 className="font-semibold text-slate-700 mb-4">{t("recentTransactions")}</h2>
        <table className="w-full">
          <thead>
            <tr>
              <th className="table-th">Entry</th>
              <th className="table-th">Date</th>
              <th className="table-th">Memo</th>
              <th className="table-th">Amount</th>
            </tr>
          </thead>
          <tbody>
            {data.recent_transactions.map((tx) => (
              <tr key={tx.entry_no}>
                <td className="table-td font-mono text-xs">{tx.entry_no}</td>
                <td className="table-td">{tx.date}</td>
                <td className="table-td">{tx.memo}</td>
                <td className="table-td text-end">{fmt(tx.amount)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
