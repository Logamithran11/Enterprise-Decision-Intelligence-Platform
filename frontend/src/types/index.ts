export interface User {
  username: string;
  email: string;
  role: string;
  id?: number;
  is_active?: boolean;
}

export interface AuthState {
  token: string | null;
  user: User | null;
  role: string | null;
}

export interface ExecutiveOverview {
  total_revenue: number;
  total_orders: number;
  active_customers: number;
  average_gross_margin_rate: number;
  revenue_forecast_next_month: number;
}

export interface FinanceMetric {
  order_month: string;
  revenue: number;
  gross_margin: number;
  order_count: number;
  cogs: number;
  opex: number;
  ebitda: number;
  cash_balance: number;
  debt_balance: number;
  dscr: number;
}

export interface OperationsMetric {
  operating_date: string;
  warehouse_id: string;
  throughput_units: number;
  on_time_delivery_rate: number;
  fulfillment_rate: number;
  incident_count: number;
  labor_hours: number;
  downtime_minutes: number;
}

export interface CustomerMetric {
  customer_id: string;
  segment: string;
  industry: string;
  region: string;
  annual_revenue: number;
  engagement_score: number;
  customer_health_score: number;
  customer_activity_score: number;
}

export interface BusinessRecommendation {
  business_insight: string;
  root_cause: string;
  recommendation: string;
  confidence: number;
  expected_impact: string;
  priority: string;
  estimated_roi: number;
  estimated_time_to_benefit: string;
}

export interface ModelMetadata {
  name: string;
  model_path: string;
  metrics: Record<string, number>;
  feature_names: string[];
  trained_at: string;
  model_type: string;
  description: string;
}

export interface DriftMetric {
  method: string;
  stat?: number;
  p_value?: number;
  drift_detected: boolean;
  ref_mean?: number;
  inc_mean?: number;
}

export interface DriftReport {
  dataset_name: string;
  timestamp: string;
  schema_valid: boolean;
  drift_detected: boolean;
  missing_columns: string[];
  out_of_bound_columns: Record<string, any>;
  unexpected_categories: Record<string, string[]>;
  drift_metrics: Record<string, DriftMetric>;
}

export interface RiskOutput {
  risk_score: number;
  risk_category: string;
  risk_confidence: number;
}

