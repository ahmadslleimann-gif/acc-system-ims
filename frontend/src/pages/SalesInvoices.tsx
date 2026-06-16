import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useQueryClient } from "@tanstack/react-query";
import { useList, useAction } from "../api/hooks";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import DataTable from "../components/DataTable";

interface Invoice {
  id: number;
  doc_no: string;
  customer_name: string;
  date: string;
  status: string;
  total: string;
}
interface Customer { id: number; name: string; }
interface Product { id: number; code: string; name_en: string; kind: string; sale_price: string; quantity_on_hand: string; tax_rate: number | null; }
interface Line { product: string; description: string; quantity: string; unit_price: string; tax_rate: number | null; }

export default function SalesInvoices() {
  const { t } = useTranslation();
  const { can, isAdmin } = useAuth();
  const qc = useQueryClient();
  const canAdd = isAdmin || can("sales.add_salesinvoice");

  const { data, isLoading } = useList<Invoice>("sales/invoices/", { page_size: 100 });
  const { data: customers } = useList<Customer>("customers/", { page_size: 500 });
  const { data: products } = useList<Product>("inventory/products/", { page_size: 500 });
  const action = useAction("sales/invoices/");

  const [open, setOpen] = useState(false);
  const [customer, setCustomer] = useState("");
  const [lines, setLines] = useState<Line[]>([{ product: "", description: "", quantity: "1", unit_price: "0", tax_rate: null }]);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  const productList = products?.results || [];

  function pickProduct(idx: number, productId: string) {
    const p = productList.find((x) => String(x.id) === productId);
    setLines((ls) =>
      ls.map((l, i) =>
        i === idx
          ? { ...l, product: productId, description: p?.name_en || l.description, unit_price: p?.sale_price || l.unit_price, tax_rate: p?.tax_rate ?? null }
          : l
      )
    );
  }

  function updateLine(idx: number, patch: Partial<Line>) {
    setLines((ls) => ls.map((l, i) => (i === idx ? { ...l, ...patch } : l)));
  }

  const grandTotal = lines.reduce((s, l) => s + Number(l.quantity || 0) * Number(l.unit_price || 0), 0);

  async function submit(autoPost: boolean) {
    setBusy(true);
    setMsg("");
    try {
      const payload = {
        customer: Number(customer),
        date: new Date().toISOString().slice(0, 10),
        items: lines
          .filter((l) => Number(l.quantity) > 0)
          .map((l) => ({
            product: l.product ? Number(l.product) : null,
            description: l.description || "Item",
            quantity: l.quantity,
            unit_price: l.unit_price,
            tax_rate: l.tax_rate,
          })),
      };
      const { data: inv } = await api.post("/sales/invoices/", payload);
      if (autoPost) await api.post(`/sales/invoices/${inv.id}/post_invoice/`);
      qc.invalidateQueries({ queryKey: ["sales/invoices/"] });
      qc.invalidateQueries({ queryKey: ["inventory/products/"] });
      setOpen(false);
      setCustomer("");
      setLines([{ product: "", description: "", quantity: "1", unit_price: "0", tax_rate: null }]);
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setMsg(e.response?.data?.detail || "Could not create the sale.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-800">{t("sales")}</h1>
        {canAdd && (
          <button className="btn-primary" onClick={() => setOpen((o) => !o)}>
            + {t("newSale")}
          </button>
        )}
      </div>

      {open && (
        <div className="card p-4 space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label className="label">{t("customer")}</label>
              <select className="input" value={customer} onChange={(e) => setCustomer(e.target.value)} required>
                <option value="">{t("customer")}…</option>
                {(customers?.results || []).map((c) => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="overflow-x-auto">
          <table className="w-full text-sm min-w-[520px]">
            <thead>
              <tr className="text-slate-500 text-start">
                <th className="text-start py-1">{t("product")}</th>
                <th className="text-start">{t("quantity")}</th>
                <th className="text-start">{t("unitPrice")}</th>
                <th className="text-start">{t("total")}</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {lines.map((l, idx) => {
                const p = productList.find((x) => String(x.id) === l.product);
                const onHand = p ? Number(p.quantity_on_hand) : null;
                const qty = Number(l.quantity || 0);
                const low = onHand !== null && qty > onHand;
                return (
                  <tr key={idx}>
                    <td className="py-1 pe-2">
                      <select className="input" value={l.product} onChange={(e) => pickProduct(idx, e.target.value)}>
                        <option value="">— free text —</option>
                        {productList.map((p) => (
                          <option key={p.id} value={p.id}>
                            {p.code} · {p.name_en} {p.kind === "STOCK" ? `(${p.quantity_on_hand})` : ""}
                          </option>
                        ))}
                      </select>
                      {l.product === "" && (
                        <input className="input mt-1" placeholder="Description" value={l.description} onChange={(e) => updateLine(idx, { description: e.target.value })} />
                      )}
                      {low && <div className="text-xs text-red-600">⚠ {t("noStock")} (on hand {onHand})</div>}
                    </td>
                    <td className="pe-2"><input className="input w-24" type="number" step="0.001" value={l.quantity} onChange={(e) => updateLine(idx, { quantity: e.target.value })} /></td>
                    <td className="pe-2"><input className="input w-28" type="number" step="0.01" value={l.unit_price} onChange={(e) => updateLine(idx, { unit_price: e.target.value })} /></td>
                    <td className="pe-2 font-medium">{(qty * Number(l.unit_price || 0)).toLocaleString()}</td>
                    <td>
                      {lines.length > 1 && (
                        <button className="text-red-500 text-xs" onClick={() => setLines((ls) => ls.filter((_, i) => i !== idx))}>✕</button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          </div>

          <div className="flex items-center justify-between flex-wrap gap-2">
            <button className="btn-ghost text-sm" onClick={() => setLines((ls) => [...ls, { product: "", description: "", quantity: "1", unit_price: "0", tax_rate: null }])}>
              + {t("addLine")}
            </button>
            <div className="text-sm text-slate-600">
              {t("total")} (ex-VAT): <span className="font-bold">{grandTotal.toLocaleString()}</span>
            </div>
          </div>

          {msg && <div className="rounded bg-red-50 text-red-700 text-sm px-3 py-2">{msg}</div>}

          <div className="flex gap-2 justify-end">
            <button className="btn-ghost" onClick={() => setOpen(false)}>{t("cancel")}</button>
            <button className="btn-ghost" disabled={busy || !customer} onClick={() => submit(false)}>{t("save")} (draft)</button>
            <button className="btn-primary" disabled={busy || !customer} onClick={() => submit(true)}>
              {busy ? "…" : t("createAndPost")}
            </button>
          </div>
          <p className="text-xs text-slate-400">{t("createAndPost")} will deduct sold stock from inventory automatically.</p>
        </div>
      )}

      <DataTable
        loading={isLoading}
        rows={data?.results || []}
        columns={[
          { key: "doc_no", label: "Invoice" },
          { key: "customer_name", label: t("customer") },
          { key: "date", label: "Date" },
          { key: "total", label: t("total"), render: (r) => Number(r.total).toLocaleString() },
          { key: "status", label: "Status" },
          {
            key: "actions",
            label: "",
            render: (r) => (
              <div className="flex gap-2">
                {r.status === "DRAFT" && canAdd && (
                  <button className="btn-ghost text-xs" onClick={() => action.mutate({ id: r.id, action: "post_invoice" })}>
                    {t("post")}
                  </button>
                )}
                <a className="btn-ghost text-xs" href={`${import.meta.env.VITE_API_BASE_URL}/sales/invoices/${r.id}/pdf/`} target="_blank">
                  PDF
                </a>
              </div>
            ),
          },
        ]}
      />
    </div>
  );
}
