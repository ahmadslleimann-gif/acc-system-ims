import { useState } from "react";
import { useTranslation } from "react-i18next";
import { useQueryClient } from "@tanstack/react-query";
import { useList, useCreate } from "../api/hooks";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import DataTable from "../components/DataTable";
import SearchBar from "../components/SearchBar";

interface Product {
  id: number;
  code: string;
  name_en: string;
  kind: string;
  unit: string;
  sale_price: string;
  price_retail: string;
  price_wholesale: string;
  price_bulk: string;
  quantity_on_hand: string;
  average_cost?: string;
  stock_value?: string;
  is_low_stock: boolean;
  reorder_level: string;
}

export default function Inventory() {
  const { t } = useTranslation();
  const { can, isAdmin } = useAuth();
  const qc = useQueryClient();
  const canManage = isAdmin || can("inventory.add_product");

  const [search, setSearch] = useState("");
  const listParams: Record<string, unknown> = { page_size: 200 };
  if (search) listParams.search = search;
  const { data, isLoading } = useList<Product>("inventory/products/", listParams);
  const create = useCreate<Product>("inventory/products/");

  const [form, setForm] = useState({
    code: "", name_en: "", kind: "STOCK", unit: "pcs", reorder_level: "0",
    price_retail: "0", price_wholesale: "0", price_bulk: "0",
  });
  const [showProduct, setShowProduct] = useState(false);

  // Stock movement panel
  const [mv, setMv] = useState({ product: "", direction: "IN", reason: "PURCHASE", quantity: "", unit_cost: "" });
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState("");

  async function addProduct(e: React.FormEvent) {
    e.preventDefault();
    await create.mutateAsync({ ...form, sale_price: form.price_retail } as never);
    setForm({ code: "", name_en: "", kind: "STOCK", unit: "pcs", reorder_level: "0", price_retail: "0", price_wholesale: "0", price_bulk: "0" });
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
        <form onSubmit={addProduct} className="card p-4 space-y-3">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 items-end">
            <input className="input col-span-2" placeholder="Product name" value={form.name_en} onChange={(e) => setForm({ ...form, name_en: e.target.value })} required />
            <input className="input" placeholder="Unit" value={form.unit} onChange={(e) => setForm({ ...form, unit: e.target.value })} />
          </div>
          <div className="grid grid-cols-3 gap-3 items-end">
            <div>
              <label className="label">{t("priceRetail")} {!isAdmin && <span className="text-[10px] text-amber-600">({t("adminOnly")})</span>}</label>
              <input className="input" type="number" step="0.01" disabled={!isAdmin} value={form.price_retail} onChange={(e) => setForm({ ...form, price_retail: e.target.value })} />
            </div>
            <div>
              <label className="label">{t("priceWholesale")}</label>
              <input className="input" type="number" step="0.01" disabled={!isAdmin} value={form.price_wholesale} onChange={(e) => setForm({ ...form, price_wholesale: e.target.value })} />
            </div>
            <div>
              <label className="label">{t("priceBulk")}</label>
              <input className="input" type="number" step="0.01" disabled={!isAdmin} value={form.price_bulk} onChange={(e) => setForm({ ...form, price_bulk: e.target.value })} />
            </div>
          </div>
          <div className="flex justify-end">
            <button className="btn-primary" disabled={create.isPending}>{t("save")}</button>
          </div>
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

      <SearchBar onSearch={setSearch} placeholder={`${t("search")} (code, name, barcode…)`} />

      <DataTable
        loading={isLoading}
        rows={products}
        columns={[
          { key: "name_en", label: "Name" },
          {
            key: "quantity_on_hand",
            label: t("onHand"),
            render: (p) => (
              <span className={p.is_low_stock ? "text-red-600 font-semibold" : ""}>
                {Number(p.quantity_on_hand).toLocaleString()} {p.unit}
                {p.is_low_stock && " ⚠"}
              </span>
            ),
          },
          { key: "average_cost", label: "Avg Cost", render: (p) => (p.average_cost == null ? "—" : Number(p.average_cost).toLocaleString()) },
          { key: "stock_value", label: "Value", render: (p) => (p.stock_value == null ? "—" : Number(p.stock_value).toLocaleString()) },
          { key: "price_retail", label: t("priceRetail"), render: (p) => Number(p.price_retail).toLocaleString() },
          { key: "price_wholesale", label: t("priceWholesale"), render: (p) => Number(p.price_wholesale).toLocaleString() },
          { key: "price_bulk", label: t("priceBulk"), render: (p) => Number(p.price_bulk).toLocaleString() },
        ]}
      />
    </div>
  );
}
