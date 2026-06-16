import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import DataTable from "../components/DataTable";

interface Role {
  id: number;
  name: string;
}
interface AppUser {
  id: number;
  username: string;
  email: string;
  roles: string[];
  is_active: boolean;
  is_superuser: boolean;
}

export default function UserManagement() {
  const { isAdmin, user: me } = useAuth();
  const qc = useQueryClient();
  const [form, setForm] = useState({ username: "", email: "", password: "", role_ids: [] as number[] });
  const [error, setError] = useState("");

  const { data: roles } = useQuery({
    queryKey: ["roles"],
    queryFn: async () => (await api.get<Role[] | { results: Role[] }>("/auth/roles/")).data,
  });
  const { data: users, isLoading } = useQuery({
    queryKey: ["users"],
    queryFn: async () => (await api.get<{ results: AppUser[] } | AppUser[]>("/auth/users/")).data,
  });

  const roleList = Array.isArray(roles) ? roles : roles?.results || [];
  const userList = Array.isArray(users) ? users : users?.results || [];

  const create = useMutation({
    mutationFn: async () => (await api.post("/auth/users/", form)).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["users"] });
      setForm({ username: "", email: "", password: "", role_ids: [] });
      setError("");
    },
    onError: (e: unknown) => {
      const err = e as { response?: { data?: Record<string, string[]> } };
      const data = err.response?.data;
      setError(data ? Object.entries(data).map(([k, v]) => `${k}: ${v}`).join(" · ") : "Failed to create user");
    },
  });

  const remove = useMutation({
    mutationFn: async (id: number) => api.delete(`/auth/users/${id}/`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["users"] }),
  });

  if (!isAdmin) {
    return <div className="card p-6 text-slate-500">You do not have access to user management.</div>;
  }

  return (
    <div className="space-y-5">
      <h1 className="text-2xl font-bold text-slate-800">User Management</h1>

      <form
        className="card p-4 grid grid-cols-1 md:grid-cols-5 gap-3 items-end"
        onSubmit={(e) => {
          e.preventDefault();
          create.mutate();
        }}
      >
        <div>
          <label className="label">Username</label>
          <input className="input" value={form.username} onChange={(e) => setForm({ ...form, username: e.target.value })} required />
        </div>
        <div>
          <label className="label">Email</label>
          <input className="input" type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
        </div>
        <div>
          <label className="label">Password</label>
          <input className="input" type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} required minLength={8} />
        </div>
        <div>
          <label className="label">Role</label>
          <select
            className="input"
            value={form.role_ids[0] || ""}
            onChange={(e) => setForm({ ...form, role_ids: e.target.value ? [Number(e.target.value)] : [] })}
          >
            <option value="">— No role —</option>
            {roleList.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </select>
        </div>
        <button className="btn-primary" disabled={create.isPending}>
          {create.isPending ? "…" : "+ Create user"}
        </button>
      </form>

      {error && <div className="rounded-lg bg-red-50 text-red-700 text-sm px-3 py-2">{error}</div>}

      <DataTable
        loading={isLoading}
        rows={userList}
        columns={[
          { key: "username", label: "Username", render: (u) => <span className="font-medium">{u.username}</span> },
          { key: "email", label: "Email" },
          {
            key: "roles",
            label: "Role",
            render: (u) =>
              u.is_superuser ? (
                <span className="px-2 py-0.5 rounded bg-brand-700 text-white text-xs">Super Admin</span>
              ) : (
                <span className="px-2 py-0.5 rounded bg-brand-50 text-brand-700 text-xs">{u.roles.join(", ") || "—"}</span>
              ),
          },
          { key: "is_active", label: "Status", render: (u) => (u.is_active ? "Active" : "Inactive") },
          {
            key: "actions",
            label: "",
            render: (u) =>
              u.id === me?.id ? (
                <span className="text-xs text-slate-400">(you)</span>
              ) : (
                <button
                  className="btn-ghost text-xs text-red-600"
                  onClick={() => {
                    if (confirm(`Delete user "${u.username}"?`)) remove.mutate(u.id);
                  }}
                >
                  Delete
                </button>
              ),
          },
        ]}
      />
    </div>
  );
}
