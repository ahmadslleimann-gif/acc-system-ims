import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./auth/AuthContext";
import Layout from "./components/Layout";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import ChartOfAccounts from "./pages/ChartOfAccounts";
import JournalEntries from "./pages/JournalEntries";
import Customers from "./pages/Customers";
import Suppliers from "./pages/Suppliers";
import SalesInvoices from "./pages/SalesInvoices";
import PurchaseInvoices from "./pages/PurchaseInvoices";
import CashBanks from "./pages/CashBanks";
import Inventory from "./pages/Inventory";
import Reports from "./pages/Reports";
import UserManagement from "./pages/UserManagement";

function Protected({ children }: { children: JSX.Element }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-8 text-slate-500">Loading…</div>;
  return user ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <Protected>
            <Layout />
          </Protected>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="chart-of-accounts" element={<ChartOfAccounts />} />
        <Route path="journal" element={<JournalEntries />} />
        <Route path="customers" element={<Customers />} />
        <Route path="suppliers" element={<Suppliers />} />
        <Route path="sales" element={<SalesInvoices />} />
        <Route path="purchases" element={<PurchaseInvoices />} />
        <Route path="cash-banks" element={<CashBanks />} />
        <Route path="inventory" element={<Inventory />} />
        <Route path="reports" element={<Reports />} />
        <Route path="users" element={<UserManagement />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
