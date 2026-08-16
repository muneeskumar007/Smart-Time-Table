import { Link } from "react-router";
import { ArrowLeft, ShieldQuestion } from "lucide-react";
import { Button } from "../../components/common/Button";

export default function PasswordHelpPage() {
  return (
    <div>
      <div className="flex h-11 w-11 items-center justify-center rounded-full bg-brand-50 text-brand-600 dark:bg-brand-950 dark:text-brand-400">
        <ShieldQuestion size={20} />
      </div>
      <h2 className="mt-4 font-display text-2xl font-bold text-slate-900 dark:text-white">Forgot your password?</h2>
      <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
        This system doesn't send password-reset emails yet. To reset your password, contact your department's{" "}
        <span className="font-medium text-slate-800 dark:text-slate-100">Super Admin</span> (or your HOD, if they manage your
        account) - they can set a new password for you directly from the Users page.
      </p>
      <p className="mt-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300">
        Already know your current password and just want to change it? Sign in and use{" "}
        <span className="font-medium text-slate-800 dark:text-slate-100">My Profile → Change password</span> instead.
      </p>

      <Link to="/login">
        <Button variant="secondary" icon={ArrowLeft} className="mt-6">
          Back to sign in
        </Button>
      </Link>
    </div>
  );
}
