/**
 * Celery task launching functions for company setup
 */

/**
 * Launch a Celery task via backend API
 */
export async function launchSyncTask(
  backendUrl: string,
  taskType: string,
  params: any
): Promise<void> {
  console.log(`[Task] Launching ${taskType} task`);

  const response = await fetch(`${backendUrl}/api/celery/tasks/launch`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      task_type: taskType,
      params,
    }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    console.error(`[Task] Error launching ${taskType}:`, errorText);
    throw new Error(`Failed to launch task: ${errorText}`);
  }

  const result = await response.json();
  console.log(`[Task] ${taskType} launched with task_id: ${result.task_id}`);
}

/**
 * Launch calendar sync task for a company
 *
 * This will:
 * 1. Auto-initialize company_events (if none exist) using internal business logic
 *    - Mandatory templates are always enabled
 *    - Additional templates determined by company settings (has_formal_employees, etc.)
 * 2. Generate concrete calendar_events from company_events
 *
 * @param backendUrl - Backend API URL
 * @param companyId - Company UUID
 */
export async function launchCalendarSyncTask(
  backendUrl: string,
  companyId: string
): Promise<void> {
  console.log("[Task] Launching calendar sync task for company setup");

  try {
    await launchSyncTask(backendUrl, "calendar.sync_company_calendar", {
      company_id: companyId,
    });

    console.log("[Task] Calendar sync task launched successfully");
  } catch (error) {
    console.error("[Task] Error launching calendar sync task:", error);
    // Don't fail the setup if task launch fails - log and continue
  }
}
