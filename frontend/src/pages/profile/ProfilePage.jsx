import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { KeyRound, Save } from "lucide-react";
import { PageHeader } from "../../components/common/PageHeader";
import { Card, CardHeader } from "../../components/common/Card";
import { Button } from "../../components/common/Button";
import { TextField } from "../../components/common/FormControls";
import { Badge } from "../../components/common/Badge";
import { useAuth } from "../../context/AuthContext";
import { useToast } from "../../context/ToastContext";
import { authApi } from "../../services/api/authApi";
import { ROLE_LABELS } from "../../constants";
import { getErrorMessage, getInitials } from "../../utils";

const profileSchema = z.object({
  name: z.string().min(2, "Name must be at least 2 characters"),
  phone: z
    .string()
    .optional()
    .refine((v) => !v || /^\+?[0-9\s\-()]{7,20}$/.test(v), "Enter a valid phone number"),
});

const passwordSchema = z
  .object({
    current_password: z.string().min(1, "Current password is required"),
    new_password: z.string().min(8, "New password must be at least 8 characters"),
    confirm_password: z.string().min(1, "Please confirm your new password"),
  })
  .refine((data) => data.new_password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  });

export default function ProfilePage() {
  const { user, updateUser } = useAuth();
  const toast = useToast();
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [isSavingPassword, setIsSavingPassword] = useState(false);

  const profileForm = useForm({
    resolver: zodResolver(profileSchema),
    defaultValues: { name: user?.name ?? "", phone: user?.phone ?? "" },
  });

  const passwordForm = useForm({
    resolver: zodResolver(passwordSchema),
    defaultValues: { current_password: "", new_password: "", confirm_password: "" },
  });

  const onSaveProfile = async (data) => {
    setIsSavingProfile(true);
    try {
      const res = await authApi.updateProfile({ name: data.name, phone: data.phone || null });
      updateUser(res.data);
      toast.success("Profile updated successfully");
    } catch (error) {
      toast.error(getErrorMessage(error, "Couldn't update your profile."));
    } finally {
      setIsSavingProfile(false);
    }
  };

  const onChangePassword = async (data) => {
    setIsSavingPassword(true);
    try {
      await authApi.changePassword(data.current_password, data.new_password);
      toast.success("Password changed. Please log in again on your other devices.");
      passwordForm.reset();
    } catch (error) {
      toast.error(getErrorMessage(error, "Couldn't change your password."));
    } finally {
      setIsSavingPassword(false);
    }
  };

  return (
    <div>
      <PageHeader title="My Profile" subtitle="Manage your personal information and password." />

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <div className="flex flex-col items-center text-center">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-brand-600 text-xl font-semibold text-white">
              {getInitials(user?.name)}
            </div>
            <p className="mt-3 font-display font-semibold text-slate-900 dark:text-white">{user?.name}</p>
            <p className="text-sm text-slate-500 dark:text-slate-400">{user?.email}</p>
            <Badge variant="brand" className="mt-3">
              {ROLE_LABELS[user?.role]}
            </Badge>
            {user?.department && <p className="mt-3 text-xs text-slate-400">{user.department.name}</p>}
          </div>
        </Card>

        <div className="flex flex-col gap-6 lg:col-span-2">
          <Card>
            <CardHeader title="Personal information" />
            <form onSubmit={profileForm.handleSubmit(onSaveProfile)} className="flex flex-col gap-4" noValidate>
              <TextField label="Full name" error={profileForm.formState.errors.name?.message} {...profileForm.register("name")} />
              <TextField label="Email" value={user?.email ?? ""} disabled hint="Contact your Super Admin to change your email address." />
              <TextField label="Phone" error={profileForm.formState.errors.phone?.message} {...profileForm.register("phone")} />
              <Button type="submit" icon={Save} isLoading={isSavingProfile} className="self-start">
                Save changes
              </Button>
            </form>
          </Card>

          <Card>
            <CardHeader title="Change password" />
            <form onSubmit={passwordForm.handleSubmit(onChangePassword)} className="flex flex-col gap-4" noValidate>
              <TextField
                label="Current password"
                type="password"
                error={passwordForm.formState.errors.current_password?.message}
                {...passwordForm.register("current_password")}
              />
              <TextField
                label="New password"
                type="password"
                hint="At least 8 characters, with a letter and a number."
                error={passwordForm.formState.errors.new_password?.message}
                {...passwordForm.register("new_password")}
              />
              <TextField
                label="Confirm new password"
                type="password"
                error={passwordForm.formState.errors.confirm_password?.message}
                {...passwordForm.register("confirm_password")}
              />
              <Button type="submit" icon={KeyRound} variant="secondary" isLoading={isSavingPassword} className="self-start">
                Update password
              </Button>
            </form>
          </Card>
        </div>
      </div>
    </div>
  );
}
