-- =========================================================
-- FIXED SCRIPT: SAFE PUBLIC ACCESS & REALTIME
-- =========================================================

-- 1. Drop existing policies first (to avoid "policy already exists" error)
DROP POLICY IF EXISTS "Allow anon read calls" ON calls;
DROP POLICY IF EXISTS "Allow anon read analytics" ON analytics_agent_daily;
DROP POLICY IF EXISTS "Allow anon read agents" ON agents;
DROP POLICY IF EXISTS "Allow anon read enrichments" ON call_enrichments;

-- 2. Create Permissive Policies (Allow Dashboard to Read Data)
-- We use USING (true) to allow anyone (anon) to read.
CREATE POLICY "Allow anon read calls" ON calls FOR SELECT USING (true);
CREATE POLICY "Allow anon read analytics" ON analytics_agent_daily FOR SELECT USING (true);
CREATE POLICY "Allow anon read agents" ON agents FOR SELECT USING (true);
CREATE POLICY "Allow anon read enrichments" ON call_enrichments FOR SELECT USING (true);

-- 3. Safe Realtime Setup
-- This block checks if the table is already added. If yes, it does nothing.
DO $$
BEGIN
    BEGIN ALTER PUBLICATION supabase_realtime ADD TABLE calls; EXCEPTION WHEN duplicate_object THEN NULL; END;
    BEGIN ALTER PUBLICATION supabase_realtime ADD TABLE analytics_agent_daily; EXCEPTION WHEN duplicate_object THEN NULL; END;
    BEGIN ALTER PUBLICATION supabase_realtime ADD TABLE agents; EXCEPTION WHEN duplicate_object THEN NULL; END;
END $$;
