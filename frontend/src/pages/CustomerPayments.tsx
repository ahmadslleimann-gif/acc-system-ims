import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useQueryClient } from "@tanstack/react-query";
import { useList, useAction } from "../api/hooks";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import DataTable from "../components/DataTable";
import SearchBar from "../components/SearchBar";

interface Payment {
  id: number;
  doc_no: string;
  customer_name: string;
  date: string;
  amount: string;
  status: string;
}
interface Customer { id: number; name: string; }

export default function CustomerPayments() {
  const { t } = useTranslation();
  const { can, isAdmin } = useAuth();
  const qc = useQueryClient();
  const canAdd = isAdmin || can("sales.add_customerpayment");

  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const params: Record<string, unknown> = { page_size: 100 };
  if (search) params.search = search;
  if (status) params.status = status;

  const { data, isLoading } = useList<Payment>("sales/payments/", params);
  const { data: customers } = useList<Customer>("customers/", { page_size: 500 });
  const action = useAction("sales/payments/");

  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ customer: "", amount: "", notes: "" });
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  async function submit(autoPost: boolean) {
    setBusy(true);
    setMsg("");
    try {
      const { data: pay } = await api.post("/sales/payments/", {
        customer: Number(form.customer),
        date: new Date().toISOString().slice(0, 10),
        amount: form.amount,
        notes: form.notes,
      });
      if (autoPost) await api.post(`/sales/payments/${pay.id}/post_payment/`);
      qc.invalidateQueries({ queryKey: ["sales/payments/"] });
      setOpen(false);
      setForm({ customer: "", amount: "", notes: "" });
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setMsg(err.response?.data?.detail || "Could not save the receipt.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">{t("customerReceipt")}</h1>
        {canAdd && <button className="btn-primary" onClick={() => setOpen((o) => !o)}>+ {t("newReceipt")}</button>}
      </div>

      {open && (
        <div className="card p-4 space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label className="label">{t("customer")}</label>
              <select className="input" value={form.customer} onChange={(e) => setForm({ ...form, customer: e.target.value })} required>
                <option value="">{t("customer")}…</option>
                {(customers?.results || []).map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div>
              <label className="label">{t("amount")}</label>
              <input className="input" type="number" step="0.01" value={form.amount} onChange={(e) => setForm({ ...form, amount: e.target.value })} />
            </div>
            <div>
              <label className="label">Notes</label>
              <input className="input" value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} />
            </div>
          </div>
          {msg && <div className="rounded bg-red-50 text-red-700 text-sm px-3 py-2">{msg}</div>}
          <div className="flex gap-2 justify-end">
            <button className="btn-ghost" onClick={() => setOpen(false)}>{t("cancel")}</button>
            <button className="btn-primary" disabled={busy || !form.customer || !form.amount} onClick={() => submit(true)}>
              {busy ? "…" : t("createAndPost")}
            </button>
          </div>
          <p className="text-xs text-slate-400">Receipt posts: Dr Cash / Cr Accounts Receivable (reduces customer debt).</p>
        </div>
      )}

      <SearchBar
        onSearch={setSearch}
        placeholder={`${t("search")} (receipt no…)`}
        filters={[{ value: status, onChange: setStatus, options: [
          { label: t("all"), value: "" }, { label: t("draft"), value: "DRAFT" }, { label: t("posted"), value: "POSTED" },
        ] }]}
      />

      <DataTable
        loading={isLoading}
        rows={data?.results || []}
        columns={[
          { key: "doc_no", label: "Receipt" },
          { key: "customer_name", label: t("customer") },
          { key: "date", label: "Date" },
          { key: "amount", label: t("amount"), render: (r) => Number(r.amount).toLocaleString() },
          { key: "status", label: t("status") },
          {
            key: "actions", label: "",
            render: (r) => r.status === "DRAFT" && canAdd ? (
              <button className="btn-ghost text-xs" onClick={() => action.mutate({ id: r.id, action: "post_payment" })}>{t("post")}</button>
            ) : null,
          },
        ]}
      />
    </div>
  );
}
