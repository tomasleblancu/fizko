-- =====================================================================
-- Fix Security Definer Views
-- =====================================================================
-- This migration converts views from SECURITY DEFINER to SECURITY INVOKER
-- to resolve security linter warnings. SECURITY INVOKER is safer because
-- it uses the permissions of the querying user rather than the view creator.

-- 1. Fix pending_notifications_ready view
CREATE OR REPLACE VIEW pending_notifications_ready
WITH (security_invoker = true)
AS
SELECT
    sn.id,
    sn.company_id,
    sn.notification_template_id,
    sn.entity_type,
    sn.entity_id,
    sn.recipients,
    sn.message_content,
    sn.scheduled_for,
    sn.send_attempts,
    nt.name AS template_name,
    nt.priority,
    nt.category
FROM scheduled_notifications sn
JOIN notification_templates nt ON sn.notification_template_id = nt.id
WHERE sn.status = 'pending'
  AND sn.scheduled_for <= NOW()
  AND sn.send_attempts < 3
ORDER BY nt.priority DESC, sn.scheduled_for;

COMMENT ON VIEW pending_notifications_ready IS 'Notifications ready to be sent (SECURITY INVOKER)';

-- 2. Fix subscription_plans_with_clp view
CREATE OR REPLACE VIEW subscription_plans_with_clp
WITH (security_invoker = true)
AS
SELECT
    id,
    code,
    name,
    tagname,
    tagline,
    description,
    price_monthly_uf,
    price_yearly_uf,
    uf_to_clp(price_monthly_uf) AS price_monthly,
    uf_to_clp(price_yearly_uf) AS price_yearly,
    get_current_uf_value() AS current_uf_value,
    currency,
    trial_days,
    features,
    display_order,
    is_active,
    is_public,
    created_at,
    updated_at
FROM subscription_plans sp
WHERE price_monthly_uf IS NOT NULL;

COMMENT ON VIEW subscription_plans_with_clp IS 'Subscription plans with real-time CLP prices calculated from UF values (SECURITY INVOKER)';

-- 3. Fix active_subscriptions view
CREATE OR REPLACE VIEW active_subscriptions
WITH (security_invoker = true)
AS
SELECT
    s.id AS subscription_id,
    s.company_id,
    c.business_name AS company_name,
    s.status,
    s.current_period_end,
    sp.code AS plan_code,
    sp.name AS plan_name,
    sp.features,
    s.cancel_at_period_end
FROM subscriptions s
JOIN companies c ON c.id = s.company_id
JOIN subscription_plans sp ON sp.id = s.plan_id
WHERE s.status IN ('trialing', 'active');

COMMENT ON VIEW active_subscriptions IS 'Active subscriptions with company and plan details (SECURITY INVOKER)';

-- 4. Fix notification_stats_by_company view
CREATE OR REPLACE VIEW notification_stats_by_company
WITH (security_invoker = true)
AS
SELECT
    company_id,
    COUNT(*) as total_notifications,
    COUNT(*) FILTER (WHERE status = 'sent') as sent_count,
    COUNT(*) FILTER (WHERE status = 'failed') as failed_count,
    COUNT(*) FILTER (WHERE status = 'delivered') as delivered_count,
    COUNT(*) FILTER (WHERE status = 'read') as read_count,
    DATE_TRUNC('day', sent_at) as date
FROM notification_history
WHERE sent_at >= NOW() - INTERVAL '30 days'
GROUP BY company_id, DATE_TRUNC('day', sent_at);

COMMENT ON VIEW notification_stats_by_company IS 'Notification statistics by company for the last 30 days (SECURITY INVOKER)';

-- Ensure permissions are maintained
GRANT SELECT ON pending_notifications_ready TO authenticated, service_role;
GRANT SELECT ON subscription_plans_with_clp TO authenticated, service_role;
GRANT SELECT ON active_subscriptions TO authenticated, service_role;
GRANT SELECT ON notification_stats_by_company TO authenticated, service_role;
