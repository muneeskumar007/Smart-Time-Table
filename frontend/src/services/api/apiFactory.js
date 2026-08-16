import apiClient from "./axiosClient";

/**
 * @typedef {Object} ListParams
 * @property {number} [page]
 * @property {number} [limit]
 * @property {string} [search]
 * @property {string} [sort_by]
 * @property {"asc"|"desc"} [sort_order]
 */

/**
 * Builds a standard set of REST calls for a resource, e.g.
 * `createCrudApi("/departments")` gives you .list/.get/.create/.update/.remove
 * against /api/v1/departments. Every one of the 9 CRUD modules in this
 * app is a thin config object built on top of this, rather than 9
 * hand-duplicated copies of the same axios calls.
 * @param {string} basePath - e.g. "/departments"
 */
export function createCrudApi(basePath) {
  return {
    /** @param {ListParams} [params] */
    list: (params) => apiClient.get(basePath, { params }).then((res) => res.data),

    /** Unpaginated {id, name} list for dropdowns - backend exposes this at `${basePath}/lookup`. */
    lookup: (params) => apiClient.get(`${basePath}/lookup`, { params }).then((res) => res.data),

    get: (id) => apiClient.get(`${basePath}/${id}`).then((res) => res.data),

    create: (payload) => apiClient.post(basePath, payload).then((res) => res.data),

    update: (id, payload) => apiClient.patch(`${basePath}/${id}`, payload).then((res) => res.data),

    remove: (id) => apiClient.delete(`${basePath}/${id}`).then((res) => res.data),

    restore: (id) => apiClient.post(`${basePath}/${id}/restore`).then((res) => res.data),
  };
}
