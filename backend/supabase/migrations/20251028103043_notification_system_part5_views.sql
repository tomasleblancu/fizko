-- 7. VIEWS ÚTILES
CREATE OR REPLACE VIEW pending_notifications_ready AS
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
    nt.name as template_name,
    nt.priority,
    nt.category
FROM scheduled_notifications sn
JOIN notification_templates nt ON sn.notification_template_id = nt.id
WHERE sn.status = 'pending'
  AND sn.scheduled_for <= NOW()
  AND sn.send_attempts < 3
ORDER BY nt.priority DESC, sn.scheduled_for ASC;

CREATE OR REPLACE VIEW notification_stats_by_company AS
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