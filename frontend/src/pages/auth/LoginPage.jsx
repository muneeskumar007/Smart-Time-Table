import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useNavigate, useLocation } from "react-router";
import { LogIn } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import { TextField, CheckboxField } from "../../components/common/FormControls";
import { Button } from "../../components/common/Button";

const loginSchema = z.object({
  email: z.string().min(1, "Email is required").email("Enter a valid email address"),
  password: z.string().min(1, "Password is required"),
  rememberMe: z.boolean().optional(),
});

export default function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [formError, setFormError] = useState("");

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm({ resolver: zodResolver(loginSchema), defaultValues: { email: "", password: "", rememberMe: false } });

  const onSubmit = async (data) => {
    setFormError("");
    const result = await login(data.email, data.password, data.rememberMe);
    if (result.success) {
      const redirectTo = location.state?.from?.pathname ?? "/dashboard";
      navigate(redirectTo, { replace: true });
    } else {
      setFormError(result.message);
    }
  };

  return (
    <div>
      <h2 className="font-display text-2xl font-bold text-slate-900 dark:text-white">Welcome back</h2>
      <p className="mt-1.5 text-sm text-slate-500 dark:text-slate-400">Sign in to manage your department's timetable.</p>

      <form onSubmit={handleSubmit(onSubmit)} className="mt-8 flex flex-col gap-4" noValidate>
        {formError && (
          <div
            role="alert"
            className="rounded-lg border border-rose-200 bg-rose-50 px-3.5 py-2.5 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950 dark:text-rose-300"
          >
            {formError}
          </div>
        )}

        <TextField
          label="Email address"
          type="email"
          autoComplete="email"
          placeholder="you@college.edu"
          error={errors.email?.message}
          {...register("email")}
        />

        <TextField
          label="Password"
          type="password"
          autoComplete="current-password"
          placeholder="••••••••"
          error={errors.password?.message}
          {...register("password")}
        />

        <CheckboxField label="Remember me on this device" {...register("rememberMe")} />

        <Button type="submit" icon={LogIn} isLoading={isSubmitting} className="mt-1 w-full">
          Sign in
        </Button>
      </form>

      <p className="mt-8 text-center text-xs text-slate-400">Trouble signing in? Contact your department's Super Admin.</p>
    </div>
  );
}
