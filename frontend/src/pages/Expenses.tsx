import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useQueryClient } from "@tanstack/react-query";
import { useList, useAction } from "../api/hooks";
import { api } from "../api/client";
import DataTable from "../components/DataTable";
import SearchBar from "../components/SearchBar";
import { payBadge } from "./SalesInvoices";

interface Expense {
  id: number;
  doc_no: string;
  description: string;
  category_name: string;
  date: string;
  total: string;
  status: string;
}
interface Category { id: number; name: string; }

export default function Expenses() {
  const { t } = useTranslation();
  const qc = useQueryClient();

  const [search, setSearch] = useState("");
  const params: Record<string, unknown> = { page_size: 100 };
  if (search) params.search = search;

  const { data, isLoading } = useList<Expense>("expenses/", params);
  const { data: cats } = useList<Category>("expenses/categories/", { page_size: 200 });
  const action = useAction("expenses/");

  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ category: "", description: "", amount: "" });
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  const categories = cats?.results || [];

  async function addCategory() {
    const name = window.prompt("New expense category name (e.g. Rent, Fuel, Salaries):");
    if (!name) return;
    const { data: c } = await api.post("/expenses/categories/", { name });
    qc.invalidateQueries({ queryKey: ["expenses/categories/"] });
    setForm((f) => ({ ...f, category: String(c.id) }));
  }

  async function submit() {
    setBusy(true);
    setMsg("");
    try {
      const { data: exp } = await api.post("/expenses/", {
        category: Number(form.category),
        date: new Date().toISOString().slice(0, 10),
        description: form.description || "Expense",
        amount: form.amount,
      });
      await api.post(`/expenses/${exp.id}/post_expense/`);
      qc.invalidateQueries({ queryKey: ["expenses/"] });
      setOpen(false);
      setForm({ category: "", description: "", amount: "" });
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setMsg(err.response?.data?.detail || "Could not save the expense.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">{t("expenses")}</h1>
        <button className="btn-primary" onClick={() => setOpen((o) => !o)}>+ {t("newRecord")} {t("expenses")}</button>
      </div>

      {open && (
        <div className="card p-4 space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-3 items-end">
            <div>
              <label className="label">Category</label>
              <div className="flex gap-1">
                <select className="input" value={form.category} onChange={(e) => setForm({ ...form, category: e.target.value })} required>
                  <option value="">Category…</option>
                  {categories.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
                <button type="button" className="btn-ghost px-2" title="Add category" onClick={addCategory}>+</button>
              </div>
            </div>
            <div className="md:col-span-2">
              <label className="label">Description</label>
              <input className="input" value={form.description} onChange={(e) => setForm({ ...form, description: e.target.value })} placeholder="e.g. June office rent" />
            </div>
            <div>
              <label className="label">{t("amount")}</label>
              <input className="input" type="number" step="0.01" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} />
            </div>
          </div>
          {msg && <div className="rounded bg-red-50 text-red-700 text-sm px-3 py-2">{msg}</div>}
          <div className="flex gap-2 justify-end">
            <button className="btn-ghost" onClick={() => setOpen(false)}>{t("cancel")}</button>
            <button className="btn-primary" disabled={busy || !form.category || !form.amount} onClick={submit}>
              {busy ? "…" : t("createAndPost")}
            </button>
          </div>
          <p className="text-xs text-slate-400">Posts: Dr Expense / Cr Cash (paid in cash).</p>
        </div>
      )}

      <SearchBar onSearch={setSearch} placeholder={`${t("search")} (no., description…)`} />

      <DataTable
        loading={isLoading}
        rows={data?.results || []}
        columns={[
          { key: "doc_no", label: "No." },
          { key: "description", label: "Description" },
          { key: "category_name", label: "Category" },
          { key: "date", label: "Date" },
          { key: "total", label: t("total"), render: (r) => Number(r.total).toLocaleString() },
          { key: "status", label: t("status"), render: (r) => payBadge(r.status === "POSTED" ? "PAID" : r.status, t) },
          {
            key: "actions",
            label: "",
            render: (r) =>
              r.status !== "POSTED" ? (
                <button className="btn-ghost text-xs" onClick={() => action.mutate({ id: r.id, action: "post_expense" })}>{t("post")}</button>
              ) : null,
          },
        ]}
      />
    </div>
  );
}
