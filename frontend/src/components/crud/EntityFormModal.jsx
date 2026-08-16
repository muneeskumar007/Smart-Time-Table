import { useEffect } from "react";
import { useForm, Controller } from "react-hook-form";
import { useQuery } from "@tanstack/react-query";
import { zodResolver } from "@hookform/resolvers/zod";
import { Modal } from "../common/Modal";
import { Button } from "../common/Button";
import { TextField, TextareaField, SelectField, CheckboxField, DateField, TimeField } from "../common/FormControls";

/**
 * @typedef {Object} FieldConfig
 * @property {string} name
 * @property {string} label
 * @property {"text"|"email"|"number"|"textarea"|"select"|"checkbox"|"date"|"time"|"password"} type
 * @property {boolean} [required]
 * @property {string} [hint]
 * @property {{value:string,label:string}[]} [options] - static options, for type="select"
 * @property {{queryKey: any[], fetcher: () => Promise<any>, labelKey?: string}} [optionsSource] - live-fetched options, for type="select"
 */

function useLiveOptions(optionsSource) {
  const { data } = useQuery({
    queryKey: optionsSource?.queryKey ?? ["__disabled"],
    queryFn: optionsSource?.fetcher,
    enabled: Boolean(optionsSource),
    staleTime: 30_000,
  });
  if (!optionsSource) return [];
  const labelKey = optionsSource.labelKey ?? "name";
  return (data?.data ?? []).map((item) => ({ value: item.id, label: item[labelKey] }));
}

function SelectFieldWithSource({ field, rhfField, error }) {
  const liveOptions = useLiveOptions(field.optionsSource);
  const options = field.optionsSource ? liveOptions : (field.options ?? []);
  return (
    <SelectField
      {...rhfField}
      label={field.label}
      required={field.required}
      hint={field.hint}
      error={error}
      options={options}
      disabled={field.disabled}
    />
  );
}

/**
 * @param {{
 *   isOpen: boolean, onClose: () => void, onSubmit: (data: object) => void,
 *   title: string, fields: FieldConfig[], schema: import("zod").ZodSchema,
 *   defaultValues?: object, isSubmitting?: boolean, submitLabel?: string
 * }} props
 */
export function EntityFormModal({ isOpen, onClose, onSubmit, title, fields, schema, defaultValues, isSubmitting, submitLabel = "Save" }) {
  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: defaultValues ?? {},
  });

  useEffect(() => {
    if (isOpen) reset(defaultValues ?? {});
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isOpen, defaultValues]);

  const submit = handleSubmit((data) => onSubmit(data));

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      footer={
        <>
          <Button variant="secondary" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </Button>
          <Button onClick={submit} isLoading={isSubmitting}>
            {submitLabel}
          </Button>
        </>
      }
    >
      <form onSubmit={submit} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {fields.map((field) => {
          const wrapClass = field.fullWidth === false ? "" : field.type === "textarea" ? "sm:col-span-2" : "";
          const errorMessage = errors[field.name]?.message;

          if (field.type === "select") {
            return (
              <div key={field.name} className={wrapClass}>
                <Controller
                  name={field.name}
                  control={control}
                  render={({ field: rhfField }) => <SelectFieldWithSource field={field} rhfField={rhfField} error={errorMessage} />}
                />
              </div>
            );
          }

          if (field.type === "checkbox") {
            return (
              <div key={field.name} className={wrapClass}>
                <CheckboxField label={field.label} hint={field.hint} error={errorMessage} {...register(field.name)} />
              </div>
            );
          }

          if (field.type === "textarea") {
            return (
              <div key={field.name} className="sm:col-span-2">
                <TextareaField label={field.label} required={field.required} hint={field.hint} error={errorMessage} {...register(field.name)} />
              </div>
            );
          }

          if (field.type === "date") {
            return (
              <div key={field.name} className={wrapClass}>
                <DateField label={field.label} required={field.required} hint={field.hint} error={errorMessage} {...register(field.name)} />
              </div>
            );
          }

          if (field.type === "time") {
            return (
              <div key={field.name} className={wrapClass}>
                <TimeField label={field.label} required={field.required} error={errorMessage} {...register(field.name)} />
              </div>
            );
          }

          return (
            <div key={field.name} className={wrapClass}>
              <TextField
                type={field.type === "password" ? "password" : field.type === "number" ? "number" : field.type === "email" ? "email" : "text"}
                label={field.label}
                required={field.required}
                hint={field.hint}
                error={errorMessage}
                disabled={field.disabled}
                {...register(field.name, field.type === "number" ? { valueAsNumber: true } : undefined)}
              />
            </div>
          );
        })}
      </form>
    </Modal>
  );
}
