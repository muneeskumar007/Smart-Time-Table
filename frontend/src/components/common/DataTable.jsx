import { flexRender, getCoreRowModel, useReactTable } from "@tanstack/react-table";
import { ChevronLeft, ChevronRight, ChevronsUpDown, ChevronUp, ChevronDown } from "lucide-react";
import { cn } from "../../utils";
import { TableSkeleton } from "./LoadingState";
import { EmptyState, ErrorState } from "./EmptyState";
import { PAGE_SIZE_OPTIONS } from "../../constants";

/**
 * @param {{
 *   columns: import("@tanstack/react-table").ColumnDef<any>[],
 *   data: any[],
 *   isLoading?: boolean,
 *   isError?: boolean,
 *   onRetry?: () => void,
 *   emptyTitle?: string,
 *   emptyDescription?: string,
 *   sortBy?: string, sortOrder?: "asc"|"desc", onSortChange?: (field: string) => void,
 *   page: number, limit: number, total: number, totalPages: number,
 *   onPageChange: (page: number) => void, onLimitChange: (limit: number) => void,
 * }} props
 */
export function DataTable({
  columns,
  data,
  isLoading,
  isError,
  onRetry,
  emptyTitle = "No records found",
  emptyDescription = "Try adjusting your search or filters.",
  sortBy,
  sortOrder = "asc",
  onSortChange,
  page,
  limit,
  total,
  totalPages,
  onPageChange,
  onLimitChange,
}) {
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    manualSorting: true,
    manualPagination: true,
  });

  return (
    <div className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white dark:border-slate-800 dark:bg-slate-900">
      <div className="overflow-x-auto">
        <table className="w-full min-w-full text-left text-sm">
          <thead className="border-b border-slate-100 bg-slate-50/60 dark:border-slate-800 dark:bg-slate-800/40">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => {
                  const sortKey = header.column.columnDef.meta?.sortKey;
                  const isSortable = Boolean(sortKey && onSortChange);
                  const isActive = sortKey === sortBy;
                  return (
                    <th
                      key={header.id}
                      scope="col"
                      className={cn(
                        "whitespace-nowrap px-4 py-3 text-xs font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400",
                        isSortable && "cursor-pointer select-none hover:text-slate-700 dark:hover:text-slate-200"
                      )}
                      onClick={isSortable ? () => onSortChange(sortKey) : undefined}
                      aria-sort={isActive ? (sortOrder === "asc" ? "ascending" : "descending") : "none"}
                    >
                      <span className="inline-flex items-center gap-1">
                        {flexRender(header.column.columnDef.header, header.getContext())}
                        {isSortable &&
                          (isActive ? (
                            sortOrder === "asc" ? (
                              <ChevronUp size={13} />
                            ) : (
                              <ChevronDown size={13} />
                            )
                          ) : (
                            <ChevronsUpDown size={13} className="opacity-40" />
                          ))}
                      </span>
                    </th>
                  );
                })}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
            {!isLoading &&
              !isError &&
              table.getRowModel().rows.map((row) => (
                <tr key={row.id} className="transition-colors hover:bg-slate-50/80 dark:hover:bg-slate-800/40">
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-4 py-3 text-slate-700 dark:text-slate-200">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))}
          </tbody>
        </table>

        {isLoading && <TableSkeleton columns={columns.length} />}
        {!isLoading && isError && <ErrorState onRetry={onRetry} />}
        {!isLoading && !isError && data.length === 0 && <EmptyState title={emptyTitle} description={emptyDescription} />}
      </div>

      {!isLoading && !isError && data.length > 0 && (
        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 px-4 py-3 dark:border-slate-800">
          <div className="flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
            <span>
              Showing {(page - 1) * limit + 1}–{Math.min(page * limit, total)} of {total}
            </span>
            {onLimitChange && (
              <select
                value={limit}
                onChange={(e) => onLimitChange(Number(e.target.value))}
                className="ml-2 rounded-md border border-slate-200 bg-white px-1.5 py-1 text-xs dark:border-slate-700 dark:bg-slate-800"
                aria-label="Rows per page"
              >
                {PAGE_SIZE_OPTIONS.map((n) => (
                  <option key={n} value={n}>
                    {n} / page
                  </option>
                ))}
              </select>
            )}
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => onPageChange(page - 1)}
              disabled={page <= 1}
              aria-label="Previous page"
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 text-slate-500 transition-colors hover:bg-slate-50 disabled:opacity-40 disabled:hover:bg-transparent dark:border-slate-700 dark:text-slate-400 dark:hover:bg-slate-800"
            >
              <ChevronLeft size={16} />
            </button>
            <span className="min-w-[5.5rem] text-center text-xs font-medium text-slate-600 dark:text-slate-300">
              Page {page} of {totalPages || 1}
            </span>
            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page >= totalPages}
              aria-label="Next page"
              className="flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 text-slate-500 transition-colors hover:bg-slate-50 disabled:opacity-40 disabled:hover:bg-transparent dark:border-slate-700 dark:text-slate-400 dark:hover:bg-slate-800"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
