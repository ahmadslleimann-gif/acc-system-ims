import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import { api } from "../api/client";

type Tab =
  | "customer-debts"
  | "supplier-debts"
  | "inventory-valuation"
  | "trial-balance"
  | "income-statement"
  | "balance-sheet";

export default function Reports() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<Tab>("customer-debts");

  const TABS: { key: Tab; label: string }[] = [
    { key: "customer-debts", label: t("customerDebts") },
    { key: "supplier-debts", label: t("supplierDebts") },
    { key: "inventory-valuation", label: t("inventoryValuation") },
    { key: "trial-balance", label: "Trial Balance" },
    { key: "income-statement", label: "Income Statement" },
    { key: "balance-sheet", label: "Balance Sheet" },
  ];

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-slate-800">{t("reports")}</h1>
      <div className="flex flex-wrap gap-2">
        {TABS.map((r) => (
          <button key={r.key} onClick={() => setTab(r.key)} className={tab === r.key ? "btn-primary" : "btn-ghost"}>
            {r.label}
          </button>
        ))}
      </div>
      <div className="card p-5 overflow-auto">
        {tab === "customer-debts" && <PartnerDebts endpoint="customers/" who={t("customer")} />}
        {tab === "supplier-debts" && <PartnerDebts endpoint="suppliers/" who={t("supplier")} />}
        {tab === "inventory-valuation" && <InventoryValuation />}
        {tab === "trial-balance" && <AccountingReport endpoint="trial-balance" />}
        {tab === "income-statement" && <AccountingReport endpoint="income-statement" />}
        {tab === "balance-sheet" && <AccountingReport endpoint="balance-sheet" />}
      </div>
    </div>
  );
}

function PartnerDebts({ endpoint, who }: { endpoint: string; who: string }) {
  const { t } = useTranslation();
  const { data, isLoading } = useQuery({
    queryKey: [endpoint, "debts"],
    queryFn: async () => (await api.get(`/${endpoint}?page_size=1000`)).data,
  });
  if (isLoading) return <div className="text-slate-400">Loading…</div>;
  const rows = (data?.results || []).filter((r: { balance: string }) => Number(r.balance) !== 0);
  const total = rows.reduce((s: number, r: { balance: string }) => s + Number(r.balance), 0);
  if (!rows.length) return <div className="text-slate-400">No outstanding balances. 🎉</div>;
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-slate-500 border-b">
          <th className="text-start py-2">{who}</th>
          <th className="text-start">Code</th>
          <th className="text-end">{t("debt")}</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r: { id: number; name: string; code: string; balance: string }) => (
          <tr key={r.id} className="border-b border-slate-100">
            <td className="py-2 font-medium">{r.name}</td>
            <td className="text-slate-500">{r.code}</td>
            <td className={`text-end font-semibold ${Number(r.balance) > 0 ? "text-red-600" : "text-emerald-600"}`}>
              {Number(r.balance).toLocaleString()}
            </td>
          </tr>
        ))}
        <tr className="font-bold">
          <td className="py-2" colSpan={2}>{t("total")}</td>
          <td className="text-end">{total.toLocaleString()}</td>
        </tr>
      </tbody>
    </table>
  );
}

function InventoryValuation() {
  const { data, isLoading } = useQuery({
    queryKey: ["inventory-valuation"],
    queryFn: async () => (await api.get("/inventory/products/valuation/")).data,
  });
  if (isLoading) return <div className="text-slate-400">Loading…</div>;
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-slate-500 border-b">
          <th className="text-start py-2">Code</th>
          <th className="text-start">Product</th>
          <th className="text-end">Qty</th>
          <th className="text-end">Avg Cost</th>
          <th className="text-end">Value</th>
        </tr>
      </thead>
      <tbody>
        {(data?.rows || []).map((r: { code: string; name: string; qty: string; avg_cost: string; value: string }) => (
          <tr key={r.code} className="border-b border-slate-100">
            <td className="py-2 font-mono">{r.code}</td>
            <td>{r.name}</td>
            <td className="text-end">{Number(r.qty).toLocaleString()}</td>
            <td className="text-end">{Number(r.avg_cost).toLocaleString()}</td>
            <td className="text-end font-semibold">{Number(r.value).toLocaleString()}</td>
          </tr>
        ))}
        <tr className="font-bold">
          <td className="py-2" colSpan={4}>Total stock value</td>
          <td className="text-end">{Number(data?.total_value || 0).toLocaleString()}</td>
        </tr>
      </tbody>
    </table>
  );
}

function AccountingReport({ endpoint }: { endpoint: string }) {
  const { data, isLoading } = useQuery({
    queryKey: ["report", endpoint],
    queryFn: async () => (await api.get(`/reports/${endpoint}/`)).data,
  });
  if (isLoading) return <div className="text-slate-400">Loading…</div>;
  return (
    <div className="space-y-2">
      <a className="btn-ghost text-xs" href={`${import.meta.env.VITE_API_BASE_URL}/reports/${endpoint}/export/?format=excel`} target="_blank">
        ⬇ Excel
      </a>
      <pre className="text-xs text-slate-700 whitespace-pre-wrap">{JSON.stringify(data, null, 2)}</pre>
    </div>
  );
}
