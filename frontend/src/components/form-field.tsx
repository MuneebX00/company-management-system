"use client";

import type { ReactNode } from "react";
import { Controller, type Control, type FieldPath, type FieldValues } from "react-hook-form";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";

export function FormField<
  TFieldValues extends FieldValues,
  TName extends FieldPath<TFieldValues>
>({
  control,
  name,
  label,
  type = "text",
  placeholder,
  textarea = false,
  className,
}: {
  control: Control<TFieldValues>;
  name: TName;
  label: string;
  type?: string;
  placeholder?: string;
  textarea?: boolean;
  className?: string;
}) {
  return (
    <Controller
      control={control}
      name={name}
      render={({ field, fieldState }) => (
        <div className={`space-y-1.5 ${className ?? ""}`}>
          <Label htmlFor={name}>{label}</Label>
          {textarea ? (
            <Textarea
              id={name}
              placeholder={placeholder}
              {...field}
              value={(field.value as string | number | undefined) ?? ""}
            />
          ) : (
            <Input
              id={name}
              type={type}
              placeholder={placeholder}
              {...field}
              value={(field.value as string | number | undefined) ?? ""}
            />
          )}
          {fieldState.error ? (
            <p className="text-xs text-destructive">{fieldState.error.message}</p>
          ) : null}
        </div>
      )}
    />
  );
}

export function FieldError({ children }: { children?: ReactNode }) {
  return children ? (
    <p className="text-xs text-destructive">{children}</p>
  ) : null;
}
