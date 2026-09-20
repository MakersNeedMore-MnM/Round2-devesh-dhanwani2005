
INSERT INTO public.profiles (id, full_name, email, role)
VALUES
  ('11111111-1111-4111-8111-111111111111', 'Maya Chen', 'maya.chen@cybersentinel.demo', 'admin'),
  ('22222222-2222-4222-8222-222222222222', 'Daniel Okonkwo', 'daniel.okonkwo@cybersentinel.demo', 'senior_analyst'),
  ('33333333-3333-4333-8333-333333333333', 'Sofia Alvarez', 'sofia.alvarez@cybersentinel.demo', 'analyst')
ON CONFLICT (email) DO UPDATE SET full_name = EXCLUDED.full_name, role = EXCLUDED.role;

INSERT INTO public.assets (id, asset_name, asset_type, ip_address, hostname, status, owner, risk_level, is_demo)
VALUES
  ('aaaaaaaa-0001-4000-8000-000000000001', 'WIN-FINANCE-04', 'workstation', '10.20.4.88', 'win-finance-04.corp.internal', 'healthy', 'alex.morgan', 'low', FALSE),
  ('aaaaaaaa-0001-4000-8000-000000000002', 'FS-FINANCE-01', 'file_server', '10.20.8.12', 'fs-finance-01.corp.internal', 'healthy', 'finance-ops', 'medium', FALSE),
  ('aaaaaaaa-0001-4000-8000-000000000003', 'GW-EDGE-01', 'gateway', '10.20.0.1', 'gw-edge-01.corp.internal', 'healthy', 'network-ops', 'low', FALSE),
  ('aaaaaaaa-0001-4000-8000-000000000004', 'DC-01', 'domain_controller', '10.20.0.10', 'dc-01.corp.internal', 'healthy', 'identity-ops', 'high', FALSE),
  ('aaaaaaaa-0001-4000-8000-000000000005', 'LAPTOP-HR-12', 'laptop', '10.20.6.41', 'laptop-hr-12.corp.internal', 'healthy', 'priya.shah', 'low', FALSE),
  ('aaaaaaaa-0001-4000-8000-000000000006', 'MAIL-RELAY-02', 'mail_gateway', '10.20.0.25', 'mail-relay-02.corp.internal', 'healthy', 'messaging-ops', 'low', FALSE)
ON CONFLICT (id) DO UPDATE SET
  asset_name = EXCLUDED.asset_name,
  status = EXCLUDED.status,
  risk_level = EXCLUDED.risk_level;

INSERT INTO public.detection_rules (id, rule_name, description, event_type, threshold, severity, enabled, weight)
VALUES
  ('bbbbbbbb-0001-4000-8000-000000000001', 'failed_login_burst', 'Multiple failed logins for the same user in the correlation window', 'failed_login', 5, 'medium', TRUE, 12),
  ('bbbbbbbb-0001-4000-8000-000000000002', 'success_after_failures', 'Successful login following repeated failed attempts', 'successful_login', 1, 'high', TRUE, 14),
  ('bbbbbbbb-0001-4000-8000-000000000003', 'unusual_location', 'Login or session from an unusual location relative to prior activity', 'unusual_location', 1, 'high', TRUE, 18),
  ('bbbbbbbb-0001-4000-8000-000000000004', 'privilege_escalation', 'Privilege escalation or unexpected admin role assignment', 'privilege_escalation', 1, 'critical', TRUE, 20),
  ('bbbbbbbb-0001-4000-8000-000000000005', 'large_outbound_transfer', 'Unusually large outbound data transfer', 'large_outbound_transfer', 1, 'critical', TRUE, 27),
  ('bbbbbbbb-0001-4000-8000-000000000006', 'suspicious_ip', 'Activity involving a known or suspected malicious IP', 'suspicious_ip', 1, 'high', TRUE, 0),
  ('bbbbbbbb-0001-4000-8000-000000000007', 'multi_user_suspicious', 'Multiple suspicious event types for the same user', 'multi_user', 3, 'high', TRUE, 0),
  ('bbbbbbbb-0001-4000-8000-000000000008', 'multi_asset_suspicious', 'Multiple suspicious event types involving the same asset', 'multi_asset', 3, 'high', TRUE, 0)
ON CONFLICT (rule_name) DO UPDATE SET
  description = EXCLUDED.description,
  threshold = EXCLUDED.threshold,
  severity = EXCLUDED.severity,
  enabled = EXCLUDED.enabled,
  weight = EXCLUDED.weight,
  event_type = EXCLUDED.event_type;

INSERT INTO public.threat_intelligence (id, indicator_type, indicator_value, reputation, confidence, source, details, is_demo)
VALUES
  (
    'cccccccc-0001-4000-8000-000000000001',
    'ip',
    '203.0.113.44',
    'malicious',
    88,
    'internal_blocklist',
    '{"note": "Sample indicator for demonstration only. Not a live feed.", "tags": ["brute_force", "credential_stuffing"]}'::jsonb,
    FALSE
  ),
  (
    'cccccccc-0001-4000-8000-000000000002',
    'ip',
    '198.51.100.77',
    'suspicious',
    70,
    'internal_blocklist',
    '{"note": "Sample indicator for demonstration only.", "tags": ["scanner"]}'::jsonb,
    FALSE
  ),
  (
    'cccccccc-0001-4000-8000-000000000003',
    'domain',
    'exfil-drop.example',
    'suspicious',
    65,
    'internal_research',
    '{"note": "Placeholder domain used only in simulated outbound-transfer demos."}'::jsonb,
    FALSE
  ),
  (
    'cccccccc-0001-4000-8000-000000000004',
    'hash',
    'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa',
    'unknown',
    20,
    'internal_research',
    '{"note": "Placeholder hash. No malware family is asserted."}'::jsonb,
    FALSE
  )
ON CONFLICT (indicator_type, indicator_value) DO UPDATE SET
  reputation = EXCLUDED.reputation,
  confidence = EXCLUDED.confidence,
  details = EXCLUDED.details;

INSERT INTO public.app_settings (key, value)
VALUES
  ('correlation_window_minutes', '15'::jsonb),
  ('demo_incident_number', '"CS-1042"'::jsonb)
ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();


INSERT INTO public.security_logs (
  id, timestamp, user_name, event_type, source_ip, destination_ip, asset_id, location, severity, message, raw_data, is_demo, fingerprint
)
VALUES
  (
    'dddddddd-0001-4000-8000-000000000001',
    TIMESTAMPTZ '2026-09-18 09:12:04+00',
    'priya.shah',
    'successful_login',
    '10.20.6.41',
    '10.20.0.10',
    'aaaaaaaa-0001-4000-8000-000000000005',
    'Austin, US',
    'low',
    'Interactive logon succeeded for priya.shah',
    '{"source": "seed"}'::jsonb,
    FALSE,
    'seed-normal-1'
  ),
  (
    'dddddddd-0001-4000-8000-000000000002',
    TIMESTAMPTZ '2026-09-18 09:18:33+00',
    'james.okonkwo',
    'file_access',
    '10.20.4.21',
    '10.20.8.12',
    'aaaaaaaa-0001-4000-8000-000000000002',
    'Austin, US',
    'low',
    'Authorized finance report accessed',
    '{"source": "seed"}'::jsonb,
    FALSE,
    'seed-normal-2'
  ),
  (
    'dddddddd-0001-4000-8000-000000000003',
    TIMESTAMPTZ '2026-09-18 09:41:10+00',
    'sofia.alvarez',
    'vpn_connect',
    '10.20.0.1',
    '10.20.0.10',
    'aaaaaaaa-0001-4000-8000-000000000003',
    'Austin, US',
    'low',
    'Corporate VPN session established',
    '{"source": "seed"}'::jsonb,
    FALSE,
    'seed-normal-3'
  )
ON CONFLICT (id) DO NOTHING;
