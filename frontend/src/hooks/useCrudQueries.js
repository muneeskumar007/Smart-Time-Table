import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useToast } from "../context/ToastContext";
import { getErrorMessage } from "../utils";

/**
 * @typedef {Object} CrudApi
 * @property {(params?: object) => Promise<any>} list
 * @property {(id: string) => Promise<any>} get
 * @property {(payload: object) => Promise<any>} create
 * @property {(id: string, payload: object) => Promise<any>} update
 * @property {(id: string) => Promise<any>} remove
 */

/**
 * Paginated list query. `params` typically includes page/limit/search/
 * sort_by/sort_order plus any entity-specific filters (e.g. department_id).
 * @param {string} queryKey - cache key prefix, e.g. "departments"
 * @param {CrudApi} api
 * @param {object} params
 */
export function useEntityList(queryKey, api, params) {
  return useQuery({
    queryKey: [queryKey, "list", params],
    queryFn: () => api.list(params),
    placeholderData: (previousData) => previousData, // keeps the table's rows visible while the next page loads
  });
}

/**
 * Unpaginated {id, name}[] list for populating dropdowns.
 * @param {string} queryKey
 * @param {CrudApi} api
 * @param {object} [params]
 * @param {boolean} [enabled]
 */
export function useEntityLookup(queryKey, api, params = {}, enabled = true) {
  return useQuery({
    queryKey: [queryKey, "lookup", params],
    queryFn: () => api.lookup(params),
    enabled,
    staleTime: 60_000,
  });
}

/**
 * Bundles create/update/delete mutations for one entity, each wired to
 * invalidate that entity's list queries and show a toast on
 * success/failure - every one of the 9 CRUD pages uses this instead of
 * hand-writing the same three mutations nine times over.
 * @param {string} queryKey
 * @param {CrudApi} api
 * @param {string} entityLabel - e.g. "Department", used in toast copy
 */
export function useEntityMutations(queryKey, api, entityLabel) {
  const queryClient = useQueryClient();
  const toast = useToast();

  const invalidate = () => queryClient.invalidateQueries({ queryKey: [queryKey] });

  const create = useMutation({
    mutationFn: (payload) => api.create(payload),
    onSuccess: (res) => {
      invalidate();
      toast.success(res?.message ?? `${entityLabel} created successfully`);
    },
    onError: (error) => toast.error(getErrorMessage(error, `Couldn't create this ${entityLabel.toLowerCase()}.`)),
  });

  const update = useMutation({
    mutationFn: ({ id, payload }) => api.update(id, payload),
    onSuccess: (res) => {
      invalidate();
      toast.success(res?.message ?? `${entityLabel} updated successfully`);
    },
    onError: (error) => toast.error(getErrorMessage(error, `Couldn't update this ${entityLabel.toLowerCase()}.`)),
  });

  const remove = useMutation({
    mutationFn: (id) => api.remove(id),
    onSuccess: (res) => {
      invalidate();
      toast.success(res?.message ?? `${entityLabel} deleted successfully`);
    },
    onError: (error) => toast.error(getErrorMessage(error, `Couldn't delete this ${entityLabel.toLowerCase()}.`)),
  });

  const restore = useMutation({
    mutationFn: (id) => api.restore(id),
    onSuccess: (res) => {
      invalidate();
      toast.success(res?.message ?? `${entityLabel} restored successfully`);
    },
    onError: (error) => toast.error(getErrorMessage(error, `Couldn't restore this ${entityLabel.toLowerCase()}.`)),
  });

  return { create, update, remove, restore };
}
