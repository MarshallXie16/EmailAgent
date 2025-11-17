// Analytics Types
export interface AnalyticsOverview {
  period: string;
  total_emails: number;
  auto_reply_rate: number;
  escalation_rate: number;
  avg_confidence: number;
  nda_request_rate: number;
}

export interface EmailActivityItem {
  id: number;
  thread_id: string;
  lead_name: string;
  lead_email: string;
  listing_code?: string;
  listing_title?: string;
  subject: string;
  sent_at: string;
  status: string;
  sent_by: string;
  confidence?: number;
  final_action?: string;
  tools_called?: string[];
}

export interface EmailActivityResponse {
  emails: EmailActivityItem[];
  total: number;
  skip: number;
  limit: number;
}

export interface DailyCount {
  date: string;
  count: number;
}

export interface ListingCount {
  listing_code: string;
  listing_title: string;
  count: number;
}

export interface ActionBreakdown {
  answered: number;
  escalated: number;
  nda_requested: number;
  meeting_booked: number;
}

export interface AnalyticsTrends {
  daily_counts: DailyCount[];
  by_listing: ListingCount[];
  by_action: ActionBreakdown;
}

// Review Queue Types
export interface ConfidenceFactor {
  factor: string;
  weight: number;
}

export interface AgentReasoningDetail {
  why_flagged: string;
  confidence: number;
  concerns: string[];
  tools_called: string[];
  confidence_factors?: {
    positive: ConfidenceFactor[];
    negative: ConfidenceFactor[];
  };
}

export interface ReviewQueueMessagePreview {
  id: number;
  direction: string;
  from_email: string;
  to_email: string;
  body_text: string;
  sent_at: string;
  sent_by: string;
}

export interface ReviewQueueLeadInfo {
  id: string;
  name: string;
  email: string;
  type: string;
}

export interface ReviewQueueListingInfo {
  id: string;
  code: string;
  title: string;
  asking_price?: number;
}

export interface ReviewQueueItem {
  id: string;
  lead: ReviewQueueLeadInfo;
  listing?: ReviewQueueListingInfo;
  status: string;
  last_inbound_message: ReviewQueueMessagePreview;
  proposed_response: string;
  agent_reasoning: AgentReasoningDetail;
  created_at: string;
  priority_score: number;
  message_count: number;
}

export interface ReviewQueueResponse {
  threads: ReviewQueueItem[];
  total: number;
}
