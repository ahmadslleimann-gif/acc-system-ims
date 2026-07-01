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
  supplier_name: string;
  date: string;
  amount: string;
  status: string;
}
interface Supplier { id: number; name: string; }

export default function SupplierPayments() {
  const { t } = useTranslation();
  const { can, isAdmin } = useAuth();
  const qc = useQueryClient();
  const canAdd = isAdmin || can("purchases.add_supplierpayment");

  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const params: Record<string, unknown> = { page_size: 100 };
  if (search) params.search = search;
  if (status) params.status = status;

  const { data, isLoading } = useList<Payment>("purchases/payments/", params);
  const { data: suppliers } = useList<Supplier>("suppliers/", { page_size: 500 });
  const action = useAction("purchases/payments/");

  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ supplier: "", amount: "", notes: "" });
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  async function submit() {
    setBusy(true);
    setMsg("");
    try {
      const { data: pay } = await api.post("/purchases/payments/", {
        supplier: Number(form.supplier),
        date: new Date().toISOString().slice(0, 10),
        amount: form.amount,
        notes: form.notes,
      });
      await api.post(`/purchases/payments/${pay.id}/post_payment/`);
      qc.invalidateQueries({ queryKey: ["purchases/payments/"] });
      setOpen(false);
      setForm({ supplier: "", amount: "", notes: "" });
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setMsg(err.response?.data?.detail || "Could not save the payment.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">{t("supplierPayment")}</h1>
        {canAdd && <button className="btn-primary" onClick={() => setOpen((o) => !o)}>+ {t("newPayment")}</button>}
      </div>

      {open && (
        <div className="card p-4 space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label className="label">{t("supplier")}</label>
              <select className="input" value={form.supplier} onChange={(e) => setForm({ ...form, supplier: e.target.value })} required>
                <option value="">{t("supplier")}…</option>
                {(suppliers?.results || []).map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
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
            <button className="btn-primary" disabled={busy || !form.supplier || !form.amount} onClick={submit}>
              {busy ? "…" : t("createAndPost")}
            </button>
          </div>
          <p className="text-xs text-slate-400">Payment posts: Dr Accounts Payable / Cr Cash (reduces supplier debt).</p>
        </div>
      )}

      <SearchBar
        onSearch={setSearch}
        placeholder={`${t("search")} (payment no…)`}
        filters={[{ value: status, onChange: setStatus, options: [
          { label: t("all"), value: "" }, { label: t("draft"), value: "DRAFT" }, { label: t("posted"), value: "POSTED" },
        ] }]}
      />

      <DataTable
        loading={isLoading}
        rows={data?.results || []}
        columns={[
          { key: "doc_no", label: "Payment" },
          { key: "supplier_name", label: t("supplier") },
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
