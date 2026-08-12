"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Pencil, Save } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { z } from "zod";

import { PageHeader } from "@/components/page-header";
import { ErrorState, LoadingState } from "@/components/data-state";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { getOwnCompany, updateCompany } from "@/lib/api/companies";
import { getErrorMessage } from "@/lib/api/client";
import { formatDate } from "@/lib/format";

const companySchema = z.object({
  name: z.string().min(1, "Company name is required"),
  email: z.string().email("Enter a valid email").or(z.literal("")).optional(),
  phone: z.string().optional(),
  address: z.string().optional(),
});

type CompanyFormValues = z.infer<typeof companySchema>;

export default function CompanyPage() {
  const [editing, setEditing] = useState(false);
  const queryClient = useQueryClient();

  const query = useQuery({ queryKey: ["company"], queryFn: getOwnCompany });

  const form = useForm<CompanyFormValues>({
    resolver: zodResolver(companySchema),
    values: query.data
      ? {
          name: query.data.name ?? "",
          email: query.data.email ?? "",
          phone: query.data.phone ?? "",
          address: query.data.address ?? "",
        }
      : { name: "", email: "", phone: "", address: "" },
  });

  const mutation = useMutation({
    mutationFn: (values: CompanyFormValues) =>
      updateCompany(query.data!.id, {
        name: values.name,
        email: values.email || null,
        phone: values.phone || null,
        address: values.address || null,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["company"] });
      toast.success("Company updated");
      setEditing(false);
    },
    onError: (error) => {
      toast.error(getErrorMessage(error, "Failed to update company"));
    },
  });

  if (query.isLoading) return <LoadingState rows={3} />;
  if (query.isError) {
    return <ErrorState message={(query.error as Error).message} />;
  }
  if (!query.data) return null;

  const company = query.data;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Company"
        description="View and edit your company information."
        actions={
          editing ? null : (
            <Button onClick={() => setEditing(true)}>
              <Pencil className="h-4 w-4" />
              Edit
            </Button>
          )
        }
      />

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="text-base">Details</CardTitle>
            <CardDescription>
              {editing
                ? "Update the details below and save your changes."
                : "Company details shown below."}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {editing ? (
              <form
                onSubmit={form.handleSubmit((v) => mutation.mutate(v))}
                className="space-y-4"
                noValidate
              >
                <div className="space-y-1.5">
                  <Label htmlFor="name">Name</Label>
                  <Input id="name" {...form.register("name")} />
                  {form.formState.errors.name ? (
                    <p className="text-xs text-destructive">
                      {form.formState.errors.name.message}
                    </p>
                  ) : null}
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <Label htmlFor="email">Email</Label>
                    <Input id="email" type="email" {...form.register("email")} />
                    {form.formState.errors.email ? (
                      <p className="text-xs text-destructive">
                        {form.formState.errors.email.message}
                      </p>
                    ) : null}
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="phone">Phone</Label>
                    <Input id="phone" {...form.register("phone")} />
                  </div>
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="address">Address</Label>
                  <Textarea id="address" rows={3} {...form.register("address")} />
                </div>
                <div className="flex justify-end gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => {
                      form.reset();
                      setEditing(false);
                    }}
                    disabled={mutation.isPending}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" disabled={mutation.isPending}>
                    <Save className="h-4 w-4" />
                    {mutation.isPending ? "Saving…" : "Save changes"}
                  </Button>
                </div>
              </form>
            ) : (
              <dl className="grid gap-4 sm:grid-cols-2">
                <div>
                  <dt className="text-sm font-medium">Name</dt>
                  <dd className="text-sm text-muted-foreground">
                    {company.name}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium">Email</dt>
                  <dd className="text-sm text-muted-foreground">
                    {company.email ?? "—"}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium">Phone</dt>
                  <dd className="text-sm text-muted-foreground">
                    {company.phone ?? "—"}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium">Status</dt>
                  <dd className="text-sm text-muted-foreground">
                    {company.is_active ? "Active" : "Inactive"}
                  </dd>
                </div>
                <div className="sm:col-span-2">
                  <dt className="text-sm font-medium">Address</dt>
                  <dd className="text-sm text-muted-foreground">
                    {company.address ?? "—"}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium">Created</dt>
                  <dd className="text-sm text-muted-foreground">
                    {formatDate(company.created_at)}
                  </dd>
                </div>
                <div>
                  <dt className="text-sm font-medium">Last updated</dt>
                  <dd className="text-sm text-muted-foreground">
                    {formatDate(company.updated_at)}
                  </dd>
                </div>
              </dl>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
