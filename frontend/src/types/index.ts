export type Role = "analyst" | "senior_analyst" | "admin";

export type Incident = {
  id: string;
  incident_number: string;
  title: string;
  description?: string;
  severity: string;
  risk_score: number;
  confidence_score: number;
  status: string;
  detected_at: string;
  resolved_at?: string | null;
  affected_user?: string | null;
  affected_asset?: string | null;
  ai_summary?: string | null;
  potential_impact?: string[] | unknown;
  risk_factors?: unknown;
  events?: SecurityLog[];
  recommendations?: Recommendation[];
  investigation?: Investigation | null;
};

export type SecurityLog = {
  id: string;
  timestamp: string;
  user_name?: string | null;
  event_type: string;
  source_ip?: string | null;
  destination_ip?: string | null;
  asset_id?: string | null;
  location?: string | null;
  severity: string;
  message?: string | null;
};

export type Recommendation = {
  id: string;
  incident_id: string;
  action_type: string;
  description: string;
  priority: string;
  requires_approval: boolean;
  status: string;
};

export type Investigation = {
  id: string;
  ai_assessment?: Record<string, unknown>;
  reasoning_summary?: string;
  evidence?: unknown;
  attack_pattern?: string;
  potential_impact?: unknown;
  confidence_score: number;
};

export type Asset = {
  id: string;
  asset_name: string;
  asset_type: string;
  ip_address?: string;
  hostname?: string;
  status: string;
  owner?: string;
  risk_level: string;
};

export type User = {
  id: string;
  full_name: string;
  email: string;
  role: Role;
};
