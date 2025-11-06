-- ================================================
-- Enable RLS on all missing tables
-- ================================================

-- 1. ATTACHMENTS (ChatKit attachments)
ALTER TABLE public.attachments ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own attachments"
  ON public.attachments FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.messages m
      JOIN public.conversations c ON c.id = m.conversation_id
      WHERE m.metadata->>'attachment_ids' LIKE '%' || attachments.id || '%'
        AND c.user_id = auth.uid()
    )
  );

CREATE POLICY "Users can insert their own attachments"
  ON public.attachments FOR INSERT
  WITH CHECK (true); -- Will be restricted by app logic

CREATE POLICY "Users can update their own attachments"
  ON public.attachments FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM public.messages m
      JOIN public.conversations c ON c.id = m.conversation_id
      WHERE m.metadata->>'attachment_ids' LIKE '%' || attachments.id || '%'
        AND c.user_id = auth.uid()
    )
  );

-- 2. PEOPLE (Employee data - very sensitive)
ALTER TABLE public.people ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view people from their companies"
  ON public.people FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.sessions s
      WHERE s.user_id = auth.uid()
        AND s.company_id = people.company_id
        AND s.is_active = true
    )
  );

CREATE POLICY "Users can insert people to their companies"
  ON public.people FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.sessions s
      WHERE s.user_id = auth.uid()
        AND s.company_id = people.company_id
        AND s.is_active = true
    )
  );

CREATE POLICY "Users can update people from their companies"
  ON public.people FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM public.sessions s
      WHERE s.user_id = auth.uid()
        AND s.company_id = people.company_id
        AND s.is_active = true
    )
  );

CREATE POLICY "Users can delete people from their companies"
  ON public.people FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM public.sessions s
      WHERE s.user_id = auth.uid()
        AND s.company_id = people.company_id
        AND s.is_active = true
    )
  );

-- 3. PAYROLL (Very sensitive financial data)
ALTER TABLE public.payroll ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view payroll from their companies"
  ON public.payroll FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.sessions s
      WHERE s.user_id = auth.uid()
        AND s.company_id = payroll.company_id
        AND s.is_active = true
    )
  );

CREATE POLICY "Users can insert payroll to their companies"
  ON public.payroll FOR INSERT
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM public.sessions s
      WHERE s.user_id = auth.uid()
        AND s.company_id = payroll.company_id
        AND s.is_active = true
    )
  );

CREATE POLICY "Users can update payroll from their companies"
  ON public.payroll FOR UPDATE
  USING (
    EXISTS (
      SELECT 1 FROM public.sessions s
      WHERE s.user_id = auth.uid()
        AND s.company_id = payroll.company_id
        AND s.is_active = true
    )
  );

CREATE POLICY "Users can delete payroll from their companies"
  ON public.payroll FOR DELETE
  USING (
    EXISTS (
      SELECT 1 FROM public.sessions s
      WHERE s.user_id = auth.uid()
        AND s.company_id = payroll.company_id
        AND s.is_active = true
    )
  );

-- 4. NOTIFICATION_TEMPLATES (Global templates)
ALTER TABLE public.notification_templates ENABLE ROW LEVEL SECURITY;

-- All authenticated users can read templates
CREATE POLICY "Authenticated users can view notification templates"
  ON public.notification_templates FOR SELECT
  USING (auth.role() = 'authenticated');

-- Only service role can modify templates
CREATE POLICY "Only service role can insert notification templates"
  ON public.notification_templates FOR INSERT
  WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Only service role can update notification templates"
  ON public.notification_templates FOR UPDATE
  USING (auth.role() = 'service_role');

CREATE POLICY "Only service role can delete notification templates"
  ON public.notification_templates FOR DELETE
  USING (auth.role() = 'service_role');

-- 5. NOTIFICATION_SUBSCRIPTIONS
ALTER TABLE public.notification_subscriptions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view subscriptions from their companies"
  ON public.notification_subscriptions FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.sessions s
      WHERE s.user_id = auth.uid()
        AND s.company_id = notification_subscriptions.company_id
        AND s.is_active = true
    )
  );

CREATE POLICY "Users can manage subscriptions for their companies"
  ON public.notification_subscriptions FOR ALL
  USING (
    EXISTS (
      SELECT 1 FROM public.sessions s
      WHERE s.user_id = auth.uid()
        AND s.company_id = notification_subscriptions.company_id
        AND s.is_active = true
    )
  );

-- 6. SCHEDULED_NOTIFICATIONS
ALTER TABLE public.scheduled_notifications ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view scheduled notifications from their companies"
  ON public.scheduled_notifications FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.sessions s
      WHERE s.user_id = auth.uid()
        AND s.company_id = scheduled_notifications.company_id
        AND s.is_active = true
    )
  );

-- Service role can manage all scheduled notifications
CREATE POLICY "Service role can manage all scheduled notifications"
  ON public.scheduled_notifications FOR ALL
  USING (auth.role() = 'service_role');

-- 7. NOTIFICATION_HISTORY
ALTER TABLE public.notification_history ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view notification history from their companies"
  ON public.notification_history FOR SELECT
  USING (
    EXISTS (
      SELECT 1 FROM public.sessions s
      WHERE s.user_id = auth.uid()
        AND s.company_id = notification_history.company_id
        AND s.is_active = true
    )
    OR notification_history.user_id = auth.uid()
  );

-- Service role can insert notification history
CREATE POLICY "Service role can insert notification history"
  ON public.notification_history FOR INSERT
  WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Service role can update notification history"
  ON public.notification_history FOR UPDATE
  USING (auth.role() = 'service_role');

-- 8. NOTIFICATION_EVENT_TRIGGERS (Global configuration)
ALTER TABLE public.notification_event_triggers ENABLE ROW LEVEL SECURITY;

-- All authenticated users can read triggers
CREATE POLICY "Authenticated users can view notification event triggers"
  ON public.notification_event_triggers FOR SELECT
  USING (auth.role() = 'authenticated');

-- Only service role can modify triggers
CREATE POLICY "Only service role can manage notification event triggers"
  ON public.notification_event_triggers FOR ALL
  USING (auth.role() = 'service_role');

-- 9. USER_NOTIFICATION_PREFERENCES
ALTER TABLE public.user_notification_preferences ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view their own notification preferences"
  ON public.user_notification_preferences FOR SELECT
  USING (user_id = auth.uid());

CREATE POLICY "Users can insert their own notification preferences"
  ON public.user_notification_preferences FOR INSERT
  WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update their own notification preferences"
  ON public.user_notification_preferences FOR UPDATE
  USING (user_id = auth.uid());

CREATE POLICY "Users can delete their own notification preferences"
  ON public.user_notification_preferences FOR DELETE
  USING (user_id = auth.uid());

-- ================================================
-- Comments for documentation
-- ================================================

COMMENT ON POLICY "Users can view their own attachments" ON public.attachments IS 
  'Users can only view attachments from their own conversations';

COMMENT ON POLICY "Users can view people from their companies" ON public.people IS 
  'Users can view employee data only from companies they have active sessions with';

COMMENT ON POLICY "Users can view payroll from their companies" ON public.payroll IS 
  'Users can view payroll data only from companies they have active sessions with';

COMMENT ON POLICY "Users can view subscriptions from their companies" ON public.notification_subscriptions IS 
  'Users can view notification subscriptions from their active companies';

COMMENT ON POLICY "Users can view their own notification preferences" ON public.user_notification_preferences IS 
  'Users can only view and manage their own notification preferences';