import { Settings as SettingsIcon } from "lucide-react";
import { PageHeader } from "../../components/common/PageHeader";
import { Card } from "../../components/common/Card";
import { EmptyState } from "../../components/common/EmptyState";
import { useAuth } from "../../context/AuthContext";
import { ROLES } from "../../constants";

export default function SettingsPage() {
  const { user } = useAuth();
  const isSuperAdmin = user?.role === ROLES.SUPER_ADMIN;

  return (
    <div>
      <PageHeader title="Settings" subtitle="Institution-wide and department preferences." />
      <Card>
        <EmptyState
          icon={SettingsIcon}
          title="Settings aren't available yet"
          description={
            isSuperAdmin
              ? "Institution name, working days, default period duration, and notification/email preferences will live here in a future update."
              : "Department-level scheduling preferences will live here in a future update."
          }
        />
      </Card>
    </div>
  );
}
