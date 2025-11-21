import { User, Activity, Calendar } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import type { CompanyDetail } from "@/services/admin/companies.service";

interface CompanyUsersListProps {
  company: CompanyDetail;
}

export function CompanyUsersList({ company }: CompanyUsersListProps) {
  const formatDate = (dateString: string | null) => {
    if (!dateString) return "Nunca";
    return new Date(dateString).toLocaleDateString("es-CL", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  // Group sessions by user_id
  const sessionsByUser = (company.sessions || []).reduce(
    (acc, session) => {
      if (!acc[session.user_id]) {
        acc[session.user_id] = [];
      }
      acc[session.user_id].push(session);
      return acc;
    },
    {} as Record<string, typeof company.sessions>
  );

  if (!company.sessions || company.sessions.length === 0) {
    return (
      <Card className="p-8">
        <div className="text-center text-gray-500">
          <User className="h-12 w-12 mx-auto mb-3 text-gray-400" />
          <p>No hay usuarios asociados a esta empresa</p>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {Object.entries(sessionsByUser).map(([userId, userSessions]) => {
        const firstSession = userSessions[0];
        const activeSessions = userSessions.filter((s) => s.is_active);
        const lastActivity = userSessions.reduce((latest, session) => {
          if (!session.last_accessed_at) return latest;
          if (!latest) return session.last_accessed_at;
          return session.last_accessed_at > latest
            ? session.last_accessed_at
            : latest;
        }, null as string | null);

        return (
          <Card key={userId} className="p-6">
            <div className="flex items-start gap-4">
              <div className="p-2 bg-gray-100 rounded-lg">
                <User className="h-6 w-6 text-gray-600" />
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <h3 className="font-semibold text-gray-900">
                      {firstSession.profile.name || "Sin nombre"}{" "}
                      {firstSession.profile.lastname || ""}
                    </h3>
                    <p className="text-sm text-gray-600">
                      {firstSession.profile.email}
                    </p>
                  </div>
                  {activeSessions.length > 0 && (
                    <Badge className="bg-green-100 text-green-800">
                      {activeSessions.length}{" "}
                      {activeSessions.length === 1
                        ? "sesión activa"
                        : "sesiones activas"}
                    </Badge>
                  )}
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                  <div className="flex items-center gap-2 text-sm">
                    <Activity className="h-4 w-4 text-gray-400" />
                    <div>
                      <span className="text-gray-600">Total sesiones:</span>{" "}
                      <span className="font-medium text-gray-900">
                        {userSessions.length}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <Calendar className="h-4 w-4 text-gray-400" />
                    <div>
                      <span className="text-gray-600">Última actividad:</span>{" "}
                      <span className="font-medium text-gray-900">
                        {formatDate(lastActivity)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        );
      })}
    </div>
  );
}
