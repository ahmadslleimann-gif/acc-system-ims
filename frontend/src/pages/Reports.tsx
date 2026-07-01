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

async function downloadReport(report: string, fmt: "excel" | "pdf") {
  const res = await api.get(`/reports/${report}/export/`, {
    params: { fmt },
    responseType: "blob",
  });
  const url = URL.createObjectURL(res.data as Blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${report}.${fmt === "pdf" ? "pdf" : "xlsx"}`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export default function Reports() {
  const { t } = useTranslation();
  const [tab, setTab] = useState<Tab>("customer-debts");
  const [downloading, setDownloading] = useState<"" | "excel" | "pdf">("");

  async function handleDownload(fmt: "excel" | "pdf") {
    setDownloading(fmt);
    try {
      await downloadReport(tab, fmt);
    } catch {
      alert("Export failed. Please try again.");
    } finally {
      setDownloading("");
    }
  }

  const TABS: { key: Tab; label: string }[] = [
    { key: "customer-debts", label: t("customerDebts") },
    { key: "supplier-debts", label: t("supplierDebts") },
    { key: "inventory-valuation", label: t("inventoryValuation") },
    { key: "trial-balance", label: t("trialBalance") },
    { key: "income-statement", label: t("incomeStatement") },
    { key: "balance-sheet", label: t("balanceSheet") },
  ];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h1 className="text-2xl font-bold text-slate-800">{t("reports")}</h1>
        <div className="flex gap-2">
          <button className="btn-ghost text-sm" disabled={!!downloading} onClick={() => handleDownload("excel")}>
            {downloading === "excel" ? "…" : "⬇ Excel"}
          </button>
          <button className="btn-ghost text-sm" disabled={!!downloading} onClick={() => handleDownload("pdf")}>
            {downloading === "pdf" ? "…" : "⬇ PDF"}
          </button>
        </div>
      </div>
      <div className="flex flex-wrap gap-2">
        {TABS.map((r) => (
          <button key={r.key} onClick={() => setTab(r.key)} className={tab === r.key ? "btn-primary" : "btn-ghost"}>
            {r.label}
          </button>
        ))}
      </div>
      <div className="card p-5 overflow-auto">
        {tab === "customer-debts" && <PartnerDebts report="customer-debts" who={t("customer")} />}
        {tab === "supplier-debts" && <PartnerDebts report="supplier-debts" who={t("supplier")} />}
        {tab === "inventory-valuation" && <InventoryValuation />}
        {tab === "trial-balance" && <AccountingReport endpoint="trial-balance" />}
        {tab === "income-statement" && <AccountingReport endpoint="income-statement" />}
        {tab === "balance-sheet" && <AccountingReport endpoint="balance-sheet" />}
      </div>
    </div>
  );
}

function PartnerDebts({ report, who }: { report: string; who: string }) {
  const { t } = useTranslation();
  const { data, isLoading } = useQuery({
    queryKey: ["reports", report],
    queryFn: async () => (await api.get(`/reports/${report}/`)).data,
  });
  if (isLoading) return <div className="text-slate-400">Loading…</div>;
  const rows = data?.rows || [];
  if (!rows.length) return <div className="text-slate-400">No outstanding balances. 🎉</div>;
  return (
    <table className="w-full text-sm">
      <thead>
        <tr className="text-slate-500 border-b">
          <th className="text-start py-2">{who}</th>
          <th className="text-start">Code</th>
          <th className="text-end">{t("invoices")}</th>
          <th className="text-end">{t("payments")}</th>
          <th className="text-end">{t("balance")}</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r: { code: string; name: string; invoices: string; payments: string; balance: string }) => (
          <tr key={r.code} className="border-b border-slate-100">
            <td className="py-2 font-medium">{r.name}</td>
            <td className="text-slate-500">{r.code}</td>
            <td className="text-end">{Number(r.invoices).toLocaleString()}</td>
            <td className="text-end">{Number(r.payments).toLocaleString()}</td>
            <td className={`text-end font-semibold ${Number(r.balance) > 0 ? "text-red-600" : "text-emerald-600"}`}>
              {Number(r.balance).toLocaleString()}
            </td>
          </tr>
        ))}
        <tr className="font-bold">
          <td className="py-2" colSpan={2}>{t("total")}</td>
          <td className="text-end">{Number(data.total_invoices).toLocaleString()}</td>
          <td className="text-end">{Number(data.total_payments).toLocaleString()}</td>
          <td className="text-end">{Number(data.total_balance).toLocaleString()}</td>
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

const money = (v: unknown) => Number(v || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function AccountingReport({ endpoint }: { endpoint: string }) {
  const { t } = useTranslation();
  const { data, isLoading } = useQuery({
    queryKey: ["report", endpoint],
    queryFn: async () => (await api.get(`/reports/${endpoint}/`)).data,
  });
  if (isLoading) return <div className="text-slate-400">Loading…</div>;
  if (!data) return null;

  if (endpoint === "trial-balance") {
    return (
      <table className="w-full text-sm">
        <thead>
          <tr className="text-slate-500 border-b">
            <th className="text-start py-2">{t("account")}</th>
            <th className="text-end">{t("debit")}</th>
            <th className="text-end">{t("creditSide")}</th>
          </tr>
        </thead>
        <tbody>
          {data.rows.map((r: { code: string; name: string; debit: string; credit: string }) => (
            <tr key={r.code} className="border-b border-slate-100">
              <td className="py-2"><span className="text-slate-400 me-2">{r.code}</span>{r.name}</td>
              <td className="text-end">{Number(r.debit) ? money(r.debit) : "—"}</td>
              <td className="text-end">{Number(r.credit) ? money(r.credit) : "—"}</td>
            </tr>
          ))}
          <tr className="font-bold">
            <td className="py-2">{t("total")}</td>
            <td className="text-end">{money(data.total_debit)}</td>
            <td className="text-end">{money(data.total_credit)}</td>
          </tr>
        </tbody>
      </table>
    );
  }

  if (endpoint === "income-statement") {
    const Section = ({ title, rows, total }: { title: string; rows: { code: string; name: string; amount: string }[]; total: string }) => (
      <>
        <tr className="bg-slate-50"><td className="py-2 font-semibold" colSpan={2}>{title}</td></tr>
        {rows.map((r) => (
          <tr key={r.code} className="border-b border-slate-100">
            <td className="py-1 ps-4"><span className="text-slate-400 me-2">{r.code}</span>{r.name}</td>
            <td className="text-end">{money(r.amount)}</td>
          </tr>
        ))}
        <tr className="border-b font-medium"><td className="py-1 ps-4">{t("total")} {title}</td><td className="text-end">{money(total)}</td></tr>
      </>
    );
    return (
      <table className="w-full text-sm">
        <tbody>
          <Section title={t("revenue")} rows={data.revenue} total={data.total_revenue} />
          <Section title={t("expenses")} rows={data.expenses} total={data.total_expenses} />
          <tr className="font-bold text-base">
            <td className="py-3">{t("netIncome")}</td>
            <td className={`text-end ${Number(data.net_income) >= 0 ? "text-emerald-600" : "text-red-600"}`}>{money(data.net_income)}</td>
          </tr>
        </tbody>
      </table>
    );
  }

  if (endpoint === "balance-sheet") {
    const Section = ({ title, rows, total }: { title: string; rows: { code: string; name: string; amount: string }[]; total: string }) => (
      <>
        <tr className="bg-slate-50"><td className="py-2 font-semibold" colSpan={2}>{title}</td></tr>
        {rows.map((r) => (
          <tr key={r.code} className="border-b border-slate-100">
            <td className="py-1 ps-4"><span className="text-slate-400 me-2">{r.code}</span>{r.name}</td>
            <td className="text-end">{money(r.amount)}</td>
          </tr>
        ))}
        <tr className="border-b font-medium"><td className="py-1 ps-4">{t("total")} {title}</td><td className="text-end">{money(total)}</td></tr>
      </>
    );
    return (
      <table className="w-full text-sm">
        <tbody>
          <Section title={t("assets")} rows={data.assets} total={data.total_assets} />
          <Section title={t("liabilities")} rows={data.liabilities} total={data.total_liabilities} />
          <Section title={t("equity")} rows={data.equity} total={data.total_equity} />
          <tr className="font-bold">
            <td className="py-2">{t("total")} ({t("liabilities")} + {t("equity")})</td>
            <td className="text-end">{money(data.total_liabilities_equity)}</td>
          </tr>
        </tbody>
      </table>
    );
  }

  return <pre className="text-xs text-slate-700 whitespace-pre-wrap">{JSON.stringify(data, null, 2)}</pre>;
}
