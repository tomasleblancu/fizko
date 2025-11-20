/**
 * Subscription types for Fizko platform
 *
 * Maps to backend subscription models
 */

export type SubscriptionStatus =
  | "trialing"
  | "active"
  | "past_due"
  | "canceled"
  | "incomplete"
  | "none";

export interface SubscriptionPlan {
  code: string;
  name: string;
  tagname: string | null;
  tagline: string | null;
  description: string;
  price_monthly_uf: number | null;
  price_yearly_uf: number | null;
  price_monthly: number;
  price_yearly: number;
  current_uf_value: number | null;
  currency: string;
  trial_days: number;
  features: Record<string, any>;
  display_order: number;
}

export interface SubscriptionInfo {
  status: SubscriptionStatus;
  plan: {
    code: string;
    name: string;
    tagname: string | null;
  } | null;
  features: Record<string, any>;
  current_period_end?: string;
  trial_end?: string;
  is_trial?: boolean;
}

export interface SubscriptionPlanListResponse {
  plans: SubscriptionPlan[];
}
