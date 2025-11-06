-- Fix ON DELETE CASCADE for notification_subscriptions -> notification_templates
-- This ensures that when a notification_template is deleted, all subscriptions are also deleted
-- Related issue: "Cannot delete template. 1 subscription(s) exist. Delete subscriptions first."

-- Drop existing constraint if it doesn't have CASCADE
ALTER TABLE notification_subscriptions
DROP CONSTRAINT IF EXISTS notification_subscriptions_notification_template_id_fkey;

-- Re-add constraint with ON DELETE CASCADE
ALTER TABLE notification_subscriptions
ADD CONSTRAINT notification_subscriptions_notification_template_id_fkey
FOREIGN KEY (notification_template_id)
REFERENCES notification_templates(id)
ON DELETE CASCADE;

-- Verify the change
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.referential_constraints
        WHERE constraint_name = 'notification_subscriptions_notification_template_id_fkey'
        AND delete_rule = 'CASCADE'
    ) THEN
        RAISE NOTICE '✅ CASCADE constraint successfully configured';
    ELSE
        RAISE EXCEPTION '❌ CASCADE constraint not properly configured';
    END IF;
END $$;
