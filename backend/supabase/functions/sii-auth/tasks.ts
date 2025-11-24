/**
 * Celery task launching functions
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
 * Launch all document sync tasks for a new company
 */
export async function launchDocumentSyncTasks(
  backendUrl: string,
  companyId: string
): Promise<void> {
  console.log("[Task] Launching document sync tasks for new company");

  try {
    // Launch all sync tasks in parallel (don't wait for completion)
    await Promise.all([
      // Current month
      launchSyncTask(backendUrl, "sii.sync_documents", {
        company_id: companyId,
        months: 1,
        month_offset: 0,
      }),
      // Previous month
      launchSyncTask(backendUrl, "sii.sync_documents", {
        company_id: companyId,
        months: 1,
        month_offset: 1,
      }),
      // 2 months ago
      launchSyncTask(backendUrl, "sii.sync_documents", {
        company_id: companyId,
        months: 1,
        month_offset: 2,
      }),
      // Last 12 months (starting from 3 months ago)
      launchSyncTask(backendUrl, "sii.sync_documents", {
        company_id: companyId,
        months: 12,
        month_offset: 3,
      }),
      // Form29 sync
      launchSyncTask(backendUrl, "sii.sync_f29", {
        company_id: companyId,
        year: new Date().getFullYear().toString(),
      }),
    ]);

    console.log("[Task] All sync tasks launched successfully");
  } catch (error) {
    console.error("[Task] Error launching sync tasks:", error);
    // Don't fail the auth if task launch fails - log and continue
  }
}
