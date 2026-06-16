import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useQueryClient } from "@tanstack/react-query";
import { useList, useCreate } from "../api/hooks";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import DataTable from "../components/DataTable";

interface Product {
  id: number;
  code: string;
  name_en: string;
  kind: string;
  unit: string;
  sale_price: string;
  quantity_on_hand: string;
  average_cost: string;
  stock_value: string;
  is_low_stock: boolean;
  reorder_level: string;
}

export default function Inventory() {
  const { t } = useTranslation();
  const { can, isAdmin } = useAuth();
  const qc = useQueryClient();
  const canManage = isAdmin || can("inventory.add_product");

  const { data, isLoading } = useList<Product>("inventory/products/", { page_size: 200 });
  const create = useCreate<Product>("inventory/products/");

  const [form, setForm] = useState({ code: "", name_en: "", kind: "STOCK", unit: "pcs", sale_price: "0", reorder_level: "0" });
  const [showProduct, setShowProduct] = useState(false);

  // Stock movement panel
  const [mv, setMv] = useState({ product: "", direction: "IN", reason: "PURCHASE", quantity: "", unit_cost: "" });
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  async function addProduct(e: React.FormEvent) {
    e.preventDefault();
    await create.mutateAsync({ ...form, sale_price: form.sale_price, reorder_level: form.reorder_level } as never);
    setForm({ code: "", name_en: "", kind: "STOCK", unit: "pcs", sale_price: "0", reorder_level: "0" });
    setShowProduct(false);
  }

  // Create the movement, then post it (two-step: create -> post_movement)
  async function submitMovement(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setMsg("");
    try {
      const payload: Record<string, unknown> = {
        product: Number(mv.product),
        date: new Date().toISOString().slice(0, 10),
        direction: mv.direction,
        reason: mv.reason,
        quantity: mv.quantity,
      };
      if (mv.direction === "IN") payload.unit_cost = mv.unit_cost || "0";
      const { data: created } = await api.post("/inventory/movements/", payload);
      await api.post(`/inventory/movements/${created.id}/post_movement/`);
      qc.invalidateQueries({ queryKey: ["inventory/products/"] });
      setMsg(`✓ ${mv.direction === "IN" ? "Received" : "Issued"} ${mv.quantity} units`);
      setMv({ product: "", direction: "IN", reason: "PURCHASE", quantity: "", unit_cost: "" });
    } catch (err: unknown) {
      const e2 = err as { response?: { data?: { detail?: string } } };
      setMsg(e2.response?.data?.detail || "Movement failed");
    } finally {
      setBusy(false);
    }
  }

  const products = data?.results || [];
  const totalValue = products.reduce((s, p) => s + Number(p.stock_value || 0), 0);

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <h1 className="text-2xl font-bold text-slate-800">{t("inventory")}</h1>
        <div className="flex items-center gap-3">
          <span className="text-sm text-slate-500">
            Total stock value: <span className="font-semibold text-brand-700">{totalValue.toLocaleString()}</span>
          </span>
          {canManage && (
            <button className="btn-primary" onClick={() => setShowProduct((o) => !o)}>
              + {t("newRecord")} product
            </button>
          )}
        </div>
      </div>

      {showProduct && (
        <form onSubmit={addProduct} className="card p-4 grid grid-cols-2 md:grid-cols-6 gap-3 items-end">
          <input className="input" placeholder="Code" value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} required />
          <input className="input col-span-2" placeholder="Product name" value={form.name_en} onChange={(e) => setForm({ ...form, name_en: e.target.value })} required />
          <select className="input" value={form.kind} onChange={(e) => setForm({ ...form, kind: e.target.value })}>
            <option value="STOCK">Stock item</option>
            <option value="SERVICE">Service</option>
          </select>
          <input className="input" placeholder="Unit" value={form.unit} onChange={(e) => setForm({ ...form, unit: e.target.value })} />
          <input className="input" type="number" step="0.01" placeholder="Sale price" value={form.sale_price} onChange={(e) => setForm({ ...form, sale_price: e.target.value })} />
          <button className="btn-primary" disabled={create.isPending}>{t("save")}</button>
        </form>
      )}

      {canManage && (
        <div className="card p-4">
          <div className="text-sm font-semibold text-slate-600 mb-3">Stock movement (receive / issue)</div>
          <form onSubmit={submitMovement} className="grid grid-cols-2 md:grid-cols-6 gap-3 items-end">
            <select className="input col-span-2" value={mv.product} onChange={(e) => setMv({ ...mv, product: e.target.value })} required>
              <option value="">Select product…</option>
              {products.filter((p) => p.kind === "STOCK").map((p) => (
                <option key={p.id} value={p.id}>{p.code} · {p.name_en} (on hand {p.quantity_on_hand})</option>
              ))}
            </select>
            <select className="input" value={mv.direction} onChange={(e) => setMv({ ...mv, direction: e.target.value, reason: e.target.value === "IN" ? "PURCHASE" : "SALE" })}>
              <option value="IN">Stock In</option>
              <option value="OUT">Stock Out</option>
            </select>
            <input className="input" type="number" step="0.001" placeholder="Quantity" value={mv.quantity} onChange={(e) => setMv({ ...mv, quantity: e.target.value })} required />
            {mv.direction === "IN" ? (
              <input className="input" type="number" step="0.01" placeholder="Unit cost" value={mv.unit_cost} onChange={(e) => setMv({ ...mv, unit_cost: e.target.value })} required />
            ) : (
              <div className="text-xs text-slate-400 self-center">cost = avg cost</div>
            )}
            <button className="btn-primary" disabled={busy}>{busy ? "…" : "Post"}</button>
          </form>
          {msg && <div className="mt-2 text-sm text-slate-600">{msg}</div>}
        </div>
      )}

      <DataTable
        loading={isLoading}
        rows={products}
        columns={[
          { key: "code", label: "Code", render: (p) => <span className="font-mono">{p.code}</span> },
          { key: "name_en", label: "Name" },
          { key: "kind", label: "Type" },
          {
            key: "quantity_on_hand",
            label: "On Hand",
            render: (p) =>
              p.kind === "SERVICE" ? "—" : (
                <span className={p.is_low_stock ? "text-red-600 font-semibold" : ""}>
                  {Number(p.quantity_on_hand).toLocaleString()} {p.unit}
                  {p.is_low_stock && " ⚠"}
                </span>
              ),
          },
          { key: "average_cost", label: "Avg Cost", render: (p) => (p.kind === "SERVICE" ? "—" : Number(p.average_cost).toLocaleString()) },
          { key: "stock_value", label: "Value", render: (p) => (p.kind === "SERVICE" ? "—" : Number(p.stock_value).toLocaleString()) },
          { key: "sale_price", label: "Sale Price", render: (p) => Number(p.sale_price).toLocaleString() },
        ]}
      />
    </div>
  );
}
