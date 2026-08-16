import { useState } from "react";
import { Plus, Pencil, Trash2, RotateCcw } from "lucide-react";
import { createColumnHelper } from "@tanstack/react-table";
import { PageHeader } from "../common/PageHeader";
import { Button } from "../common/Button";
import { DataTable } from "../common/DataTable";
import { SearchInput } from "../common/SearchInput";
import { ConfirmDialog } from "../common/ConfirmDialog";
import { CheckboxField } from "../common/FormControls";
import { EntityFormModal } from "./EntityFormModal";
import { useEntityList, useEntityMutations } from "../../hooks/useCrudQueries";
import { DEFAULT_PAGE_SIZE } from "../../constants";

const columnHelper = createColumnHelper();

/**
 * @param {{
 *   title: string, subtitle?: string, queryKey: string, api: object, entityLabel: string,
 *   columns: {header: string, accessorKey?: string, accessorFn?: (row:any)=>any, cell?: (info:any)=>React.ReactNode, sortKey?: string}[],
 *   fields: import("./EntityFormModal").FieldConfig[], editFields?: import("./EntityFormModal").FieldConfig[],
 *   schema: import("zod").ZodSchema, updateSchema?: import("zod").ZodSchema,
 *   canCreate?: boolean, canEdit?: boolean, canDelete?: boolean,
 *   searchPlaceholder?: string, extraParams?: object, extraFilters?: React.ReactNode,
 *   getDefaultValues?: (row: any) => object, transformSubmit?: (data: object, mode: "create"|"edit") => object,
 *   emptyTitle?: string, emptyDescription?: string,
 * }} props
 */
export function EntityListPage({
  title,
  subtitle,
  queryKey,
  api,
  entityLabel,
  columns,
  fields,
  editFields,
  schema,
  updateSchema,
  canCreate = true,
  canEdit = true,
  canDelete = true,
  searchPlaceholder,
  extraParams = {},
  extraFilters,
  getDefaultValues,
  transformSubmit,
  emptyTitle,
  emptyDescription,
}) {
  const [page, setPage] = useState(1);
  const [limit, setLimit] = useState(DEFAULT_PAGE_SIZE);
  const [search, setSearch] = useState("");
  const [sortBy, setSortBy] = useState(undefined);
  const [sortOrder, setSortOrder] = useState("asc");

  const [modalState, setModalState] = useState({ open: false, mode: "create", row: null });
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [showInactive, setShowInactive] = useState(false);

  const params = {
    page,
    limit,
    search: search || undefined,
    sort_by: sortBy,
    sort_order: sortOrder,
    include_inactive: showInactive || undefined,
    ...extraParams,
  };
  const { data, isLoading, isError, refetch } = useEntityList(queryKey, api, params);
  const { create, update, remove, restore } = useEntityMutations(queryKey, api, entityLabel);

  const items = data?.data ?? [];
  const meta = data?.meta ?? { page: 1, limit, total: 0, total_pages: 0 };

  const handleSortChange = (key) => {
    if (sortBy !== key) {
      setSortBy(key);
      setSortOrder("asc");
    } else {
      setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"));
    }
    setPage(1);
  };

  const tableColumns = [
    ...columns.map((col) =>
      columnHelper.accessor(col.accessorFn ?? col.accessorKey, {
        id: col.accessorKey ?? col.header,
        header: col.header,
        cell: col.cell ?? ((info) => info.getValue() ?? "—"),
        meta: { sortKey: col.sortKey },
      })
    ),
    columnHelper.display({
      id: "actions",
      header: "",
      cell: ({ row }) => {
        const isInactive = row.original.is_active === false;
        return (
          <div className="flex justify-end gap-1">
            {isInactive && canDelete && (
              <button
                onClick={() => restore.mutate(row.original.id)}
                aria-label={`Restore ${entityLabel}`}
                title="Restore"
                className="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-emerald-50 hover:text-emerald-600 dark:hover:bg-emerald-950"
              >
                <RotateCcw size={15} />
              </button>
            )}
            {canEdit && (
              <button
                onClick={() => setModalState({ open: true, mode: "edit", row: row.original })}
                aria-label={`Edit ${entityLabel}`}
                className="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-slate-100 hover:text-brand-600 dark:hover:bg-slate-800"
              >
                <Pencil size={15} />
              </button>
            )}
            {canDelete && !isInactive && (
              <button
                onClick={() => setDeleteTarget(row.original)}
                aria-label={`Delete ${entityLabel}`}
                className="rounded-lg p-1.5 text-slate-400 transition-colors hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950"
              >
                <Trash2 size={15} />
              </button>
            )}
          </div>
        );
      },
    }),
  ];

  const closeModal = () => setModalState({ open: false, mode: "create", row: null });

  const handleSubmit = async (formData) => {
    const payload = transformSubmit ? transformSubmit(formData, modalState.mode) : formData;
    if (modalState.mode === "create") {
      await create.mutateAsync(payload);
    } else {
      await update.mutateAsync({ id: modalState.row.id, payload });
    }
    closeModal();
  };

  const handleDelete = async () => {
    await remove.mutateAsync(deleteTarget.id);
    setDeleteTarget(null);
  };

  const defaultValuesForEdit = modalState.row && getDefaultValues ? getDefaultValues(modalState.row) : modalState.row;

  return (
    <div>
      <PageHeader
        title={title}
        subtitle={subtitle}
        action={
          canCreate && (
            <Button icon={Plus} onClick={() => setModalState({ open: true, mode: "create", row: null })}>
              Add {entityLabel}
            </Button>
          )
        }
      />

      <div className="mb-4 flex flex-wrap items-center gap-3">
        <SearchInput
          value={search}
          onChange={(v) => {
            setSearch(v);
            setPage(1);
          }}
          placeholder={searchPlaceholder ?? `Search ${title.toLowerCase()}…`}
          className="w-full max-w-xs"
        />
        {extraFilters}
        {canDelete && (
          <CheckboxField
            label="Show inactive"
            checked={showInactive}
            onChange={(e) => {
              setShowInactive(e.target.checked);
              setPage(1);
            }}
          />
        )}
      </div>

      <DataTable
        columns={tableColumns}
        data={items}
        isLoading={isLoading}
        isError={isError}
        onRetry={refetch}
        emptyTitle={emptyTitle ?? `No ${title.toLowerCase()} yet`}
        emptyDescription={emptyDescription ?? `Add your first ${entityLabel.toLowerCase()} to get started.`}
        sortBy={sortBy}
        sortOrder={sortOrder}
        onSortChange={handleSortChange}
        page={meta.page}
        limit={meta.limit}
        total={meta.total}
        totalPages={meta.total_pages}
        onPageChange={setPage}
        onLimitChange={(l) => {
          setLimit(l);
          setPage(1);
        }}
      />

      <EntityFormModal
        isOpen={modalState.open}
        onClose={closeModal}
        onSubmit={handleSubmit}
        title={modalState.mode === "create" ? `Add ${entityLabel}` : `Edit ${entityLabel}`}
        fields={modalState.mode === "edit" && editFields ? editFields : fields}
        schema={modalState.mode === "create" ? schema : (updateSchema ?? schema)}
        defaultValues={modalState.mode === "edit" ? defaultValuesForEdit : undefined}
        isSubmitting={create.isPending || update.isPending}
        submitLabel={modalState.mode === "create" ? "Create" : "Save changes"}
      />

      <ConfirmDialog
        isOpen={Boolean(deleteTarget)}
        onClose={() => setDeleteTarget(null)}
        onConfirm={handleDelete}
        title={`Delete this ${entityLabel.toLowerCase()}?`}
        description="This deactivates the record rather than permanently erasing it - tick “Show inactive” afterwards to find and restore it."
        confirmLabel="Delete"
        isLoading={remove.isPending}
      />
    </div>
  );
}
