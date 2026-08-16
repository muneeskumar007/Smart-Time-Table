import { Link } from "react-router";
import { ShieldAlert } from "lucide-react";
import { Button } from "../../components/common/Button";

export default function UnauthorizedPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-6 text-center dark:bg-slate-950">
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-rose-50 text-rose-600 dark:bg-rose-950 dark:text-rose-400">
        <ShieldAlert size={26} />
      </div>
      <h1 className="mt-5 font-display text-3xl font-bold text-slate-900 dark:text-white">Access restricted</h1>
      <p className="mt-2 max-w-sm text-sm text-slate-500 dark:text-slate-400">
        Your account role doesn't have permission to view this page. If you think this is a mistake, contact your Super Admin.
      </p>
      <Link to="/dashboard">
        <Button className="mt-6">Back to Dashboard</Button>
      </Link>
    </div>
  );
}
