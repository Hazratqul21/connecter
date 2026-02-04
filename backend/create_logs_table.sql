-- Create a Logs table to debug incoming webhooks from Binotel
CREATE TABLE IF NOT EXISTS webhook_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    received_at TIMESTAMPTZ DEFAULT NOW(),
    headers JSONB,
    payload JSONB,
    status VARCHAR(50),
    error_message TEXT
);

-- Allow public/anon to insert (if needed for testing, but mostly for service_role)
ALTER TABLE webhook_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow service_role full access" ON webhook_logs
    FOR ALL
    USING (auth.role() = 'service_role');

-- Allow anon read for debugging (optional)
CREATE POLICY "Allow anon read logs" ON webhook_logs
    FOR SELECT
    USING (true);
