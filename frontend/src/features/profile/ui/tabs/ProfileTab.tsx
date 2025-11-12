import { AccountSettings } from './AccountSettings';
import type { ColorScheme } from '@/shared/hooks/useColorScheme';

interface ProfileTabProps {
  user: any;
  scheme: ColorScheme;
  profileLoading: boolean;
  profile: any;
  isInDrawer?: boolean;
}

export function ProfileTab({
  user,
  scheme,
  profileLoading,
  profile,
  isInDrawer = false
}: ProfileTabProps) {
  return (
    <div className="space-y-6">
      {/* User Account Section */}
      <div>
        <h3 className="mb-3 text-lg font-semibold text-slate-900 dark:text-slate-100">
          Información Personal
        </h3>
        <AccountSettings
          user={user}
          scheme={scheme}
          profileLoading={profileLoading}
          profile={profile}
          isInDrawer={false}
          compact={true}
        />
      </div>
    </div>
  );
}
