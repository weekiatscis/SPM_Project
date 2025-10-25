-- Migration: Add project reminder preferences table
-- This migration adds support for custom notification schedules for projects

-- Create project_reminder_preferences table
CREATE TABLE IF NOT EXISTS public.project_reminder_preferences (
  project_id uuid NOT NULL,
  reminder_days integer[] NOT NULL DEFAULT '{7,3,1}'::integer[],
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT project_reminder_preferences_pkey PRIMARY KEY (project_id),
  CONSTRAINT project_reminder_preferences_project_id_fkey FOREIGN KEY (project_id) REFERENCES project (project_id) ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT valid_reminder_days CHECK (
    (
      (array_length(reminder_days, 1) <= 5)
      AND (
        reminder_days <@ array[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
      )
    )
  )
) TABLESPACE pg_default;

-- Create index for project_reminder_preferences
CREATE INDEX IF NOT EXISTS idx_project_reminder_preferences_project_id 
ON public.project_reminder_preferences USING btree (project_id) TABLESPACE pg_default;

-- Create project_notification_preferences table for individual user preferences
CREATE TABLE IF NOT EXISTS public.project_notification_preferences (
  user_id uuid NOT NULL,
  project_id uuid NOT NULL,
  email_enabled boolean NOT NULL DEFAULT true,
  in_app_enabled boolean NOT NULL DEFAULT true,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT project_notification_preferences_pkey PRIMARY KEY (user_id, project_id),
  CONSTRAINT project_notification_preferences_project_id_fkey FOREIGN KEY (project_id) REFERENCES project (project_id) ON UPDATE CASCADE ON DELETE CASCADE,
  CONSTRAINT project_notification_preferences_user_id_fkey FOREIGN KEY (user_id) REFERENCES "user" (user_id) ON UPDATE CASCADE ON DELETE CASCADE
) TABLESPACE pg_default;

-- Create indexes for project_notification_preferences
CREATE INDEX IF NOT EXISTS idx_project_notification_preferences_user_id 
ON public.project_notification_preferences USING btree (user_id) TABLESPACE pg_default;

CREATE INDEX IF NOT EXISTS idx_project_notification_preferences_project_id 
ON public.project_notification_preferences USING btree (project_id) TABLESPACE pg_default;

-- Add project_id column to notifications table if it doesn't exist
-- (This might already exist based on the user's description)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'notifications' 
        AND column_name = 'project_id'
    ) THEN
        ALTER TABLE public.notifications ADD COLUMN project_id uuid NULL;
        CREATE INDEX IF NOT EXISTS idx_notifications_project_id 
        ON public.notifications USING btree (project_id) TABLESPACE pg_default;
    END IF;
END $$;

-- Create a function to get project reminder preferences
CREATE OR REPLACE FUNCTION get_project_reminder_preferences(p_project_id uuid)
RETURNS TABLE(
    project_id uuid,
    reminder_days integer[]
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        prp.project_id,
        prp.reminder_days
    FROM public.project_reminder_preferences prp
    WHERE prp.project_id = p_project_id;
END;
$$ LANGUAGE plpgsql;

-- Create a function to save project reminder preferences
CREATE OR REPLACE FUNCTION save_project_reminder_preferences(
    p_project_id uuid,
    p_reminder_days integer[]
)
RETURNS boolean AS $$
BEGIN
    -- Validate reminder days
    IF array_length(p_reminder_days, 1) > 5 OR NOT (p_reminder_days <@ array[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]) THEN
        RETURN false;
    END IF;
    
    -- Insert or update reminder preferences
    INSERT INTO public.project_reminder_preferences (project_id, reminder_days, updated_at)
    VALUES (p_project_id, p_reminder_days, now())
    ON CONFLICT (project_id) 
    DO UPDATE SET 
        reminder_days = EXCLUDED.reminder_days,
        updated_at = now();
    
    RETURN true;
END;
$$ LANGUAGE plpgsql;

-- Create a function to get project notification preferences
CREATE OR REPLACE FUNCTION get_project_notification_preferences(
    p_user_id uuid,
    p_project_id uuid
)
RETURNS TABLE(
    user_id uuid,
    project_id uuid,
    email_enabled boolean,
    in_app_enabled boolean
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pnp.user_id,
        pnp.project_id,
        pnp.email_enabled,
        pnp.in_app_enabled
    FROM public.project_notification_preferences pnp
    WHERE pnp.user_id = p_user_id AND pnp.project_id = p_project_id;
END;
$$ LANGUAGE plpgsql;

-- Create a function to save project notification preferences
CREATE OR REPLACE FUNCTION save_project_notification_preferences(
    p_user_id uuid,
    p_project_id uuid,
    p_email_enabled boolean,
    p_in_app_enabled boolean
)
RETURNS boolean AS $$
BEGIN
    -- Insert or update notification preferences
    INSERT INTO public.project_notification_preferences (user_id, project_id, email_enabled, in_app_enabled, updated_at)
    VALUES (p_user_id, p_project_id, p_email_enabled, p_in_app_enabled, now())
    ON CONFLICT (user_id, project_id) 
    DO UPDATE SET 
        email_enabled = EXCLUDED.email_enabled,
        in_app_enabled = EXCLUDED.in_app_enabled,
        updated_at = now();
    
    RETURN true;
END;
$$ LANGUAGE plpgsql;

-- Add comments for documentation
COMMENT ON TABLE public.project_reminder_preferences IS 'Stores custom reminder schedules for projects';
COMMENT ON TABLE public.project_notification_preferences IS 'Stores individual user notification preferences for projects';
COMMENT ON COLUMN public.project_reminder_preferences.reminder_days IS 'Array of days before due date to send reminders (1-10, max 5)';
COMMENT ON COLUMN public.project_notification_preferences.email_enabled IS 'Whether email notifications are enabled for this user and project';
COMMENT ON COLUMN public.project_notification_preferences.in_app_enabled IS 'Whether in-app notifications are enabled for this user and project';