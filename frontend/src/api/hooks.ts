import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "./client";

export interface Paginated<T> {
  count: number;
  results: T[];
}

export function useList<T>(resource: string, params?: Record<string, unknown>) {
  return useQuery({
    queryKey: [resource, params],
    queryFn: async () => {
      const { data } = await api.get<Paginated<T> | T[]>(`/${resource}`, { params });
      return Array.isArray(data) ? { count: data.length, results: data } : data;
    },
  });
}

export function useItem<T>(resource: string, id?: number | string) {
  return useQuery({
    queryKey: [resource, id],
    enabled: id != null,
    queryFn: async () => (await api.get<T>(`/${resource}${id}/`)).data,
  });
}

export function useCreate<T>(resource: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async (payload: Partial<T>) => (await api.post<T>(`/${resource}`, payload)).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: [resource] }),
  });
}

export function useAction(resource: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async ({ id, action, body }: { id: number | string; action: string; body?: unknown }) =>
      (await api.post(`/${resource}${id}/${action}/`, body || {})).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: [resource] }),
  });
}
