import { forwardRef } from "react";
import { AlertCircle } from "lucide-react";
import { cn } from "../../utils";

function FieldWrapper({ label, error, required, hint, children, id }) {
  return (
    <div className="flex flex-col gap-1.5">
      {label && (
        <label htmlFor={id} className="text-sm font-medium text-slate-700 dark:text-slate-200">
          {label} {required && <span className="text-rose-500">*</span>}
        </label>
      )}
      {children}
      {hint && !error && <p className="text-xs text-slate-500 dark:text-slate-400">{hint}</p>}
      {error && (
        <p className="flex items-center gap-1 text-xs font-medium text-rose-600 dark:text-rose-400" role="alert">
          <AlertCircle size={12} />
          {error}
        </p>
      )}
    </div>
  );
}

const baseInputClasses =
  "h-10 w-full rounded-lg border bg-white px-3 text-sm text-slate-900 placeholder:text-slate-400 " +
  "transition-colors focus:outline-none focus:ring-2 focus:ring-brand-500/30 " +
  "dark:bg-slate-800 dark:text-slate-100 dark:placeholder:text-slate-500 disabled:opacity-50 disabled:cursor-not-allowed";

/**
 * @param {{label?: string, error?: string, required?: boolean, hint?: string} & React.InputHTMLAttributes<HTMLInputElement>} props
 */
export const TextField = forwardRef(function TextField({ label, error, required, hint, className, id, ...props }, ref) {
  const fieldId = id || props.name;
  return (
    <FieldWrapper label={label} error={error} required={required} hint={hint} id={fieldId}>
      <input
        ref={ref}
        id={fieldId}
        className={cn(baseInputClasses, error ? "border-rose-300 dark:border-rose-800" : "border-slate-200 dark:border-slate-700", className)}
        aria-invalid={Boolean(error)}
        {...props}
      />
    </FieldWrapper>
  );
});

/**
 * @param {{label?: string, error?: string, required?: boolean, hint?: string, rows?: number} & React.TextareaHTMLAttributes<HTMLTextAreaElement>} props
 */
export const TextareaField = forwardRef(function TextareaField(
  { label, error, required, hint, className, id, rows = 3, ...props },
  ref
) {
  const fieldId = id || props.name;
  return (
    <FieldWrapper label={label} error={error} required={required} hint={hint} id={fieldId}>
      <textarea
        ref={ref}
        id={fieldId}
        rows={rows}
        className={cn(baseInputClasses, "h-auto py-2 resize-y", error ? "border-rose-300 dark:border-rose-800" : "border-slate-200 dark:border-slate-700", className)}
        aria-invalid={Boolean(error)}
        {...props}
      />
    </FieldWrapper>
  );
});

/**
 * @param {{label?: string, error?: string, required?: boolean, hint?: string, options: {value: string, label: string}[], placeholder?: string} & React.SelectHTMLAttributes<HTMLSelectElement>} props
 */
export const SelectField = forwardRef(function SelectField(
  { label, error, required, hint, className, id, options, placeholder = "Select…", ...props },
  ref
) {
  const fieldId = id || props.name;
  return (
    <FieldWrapper label={label} error={error} required={required} hint={hint} id={fieldId}>
      <select
        ref={ref}
        id={fieldId}
        className={cn(baseInputClasses, "appearance-none bg-no-repeat", error ? "border-rose-300 dark:border-rose-800" : "border-slate-200 dark:border-slate-700", className)}
        aria-invalid={Boolean(error)}
        {...props}
      >
        <option value="">{placeholder}</option>
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </FieldWrapper>
  );
});

/**
 * @param {{label: string, error?: string, hint?: string} & React.InputHTMLAttributes<HTMLInputElement>} props
 */
export const CheckboxField = forwardRef(function CheckboxField({ label, error, hint, className, id, ...props }, ref) {
  const fieldId = id || props.name;
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={fieldId} className="flex cursor-pointer items-center gap-2.5 text-sm font-medium text-slate-700 dark:text-slate-200">
        <input
          ref={ref}
          type="checkbox"
          id={fieldId}
          className={cn(
            "h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-2 focus:ring-brand-500/30 dark:border-slate-600 dark:bg-slate-800",
            className
          )}
          {...props}
        />
        {label}
      </label>
      {hint && !error && <p className="pl-6 text-xs text-slate-500 dark:text-slate-400">{hint}</p>}
      {error && <p className="pl-6 text-xs font-medium text-rose-600 dark:text-rose-400">{error}</p>}
    </div>
  );
});

/**
 * @param {{label?: string, error?: string, required?: boolean, hint?: string} & React.InputHTMLAttributes<HTMLInputElement>} props
 */
export const DateField = forwardRef(function DateField({ label, error, required, hint, className, id, ...props }, ref) {
  const fieldId = id || props.name;
  return (
    <FieldWrapper label={label} error={error} required={required} hint={hint} id={fieldId}>
      <input
        ref={ref}
        type="date"
        id={fieldId}
        className={cn(baseInputClasses, error ? "border-rose-300 dark:border-rose-800" : "border-slate-200 dark:border-slate-700", className)}
        aria-invalid={Boolean(error)}
        {...props}
      />
    </FieldWrapper>
  );
});

/**
 * A plain 24h "HH:MM" text input (kept simple/dependency-free rather
 * than a full time-picker widget) with basic format hinting.
 * @param {{label?: string, error?: string, required?: boolean} & React.InputHTMLAttributes<HTMLInputElement>} props
 */
export const TimeField = forwardRef(function TimeField({ label, error, required, className, id, ...props }, ref) {
  const fieldId = id || props.name;
  return (
    <FieldWrapper label={label} error={error} required={required} id={fieldId}>
      <input
        ref={ref}
        type="time"
        id={fieldId}
        className={cn(baseInputClasses, error ? "border-rose-300 dark:border-rose-800" : "border-slate-200 dark:border-slate-700", className)}
        aria-invalid={Boolean(error)}
        {...props}
      />
    </FieldWrapper>
  );
});
