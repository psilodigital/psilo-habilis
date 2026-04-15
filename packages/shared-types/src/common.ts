/** Possible run statuses */
export type RunStatus =
  | "completed"
  | "awaiting_approval"
  | "running"
  | "error"
  | "timeout";

/** Possible approval statuses for artifacts */
export type ApprovalStatus =
  | "pending"
  | "approved"
  | "rejected"
  | "not_required";

/** Email classification intents */
export type Intent =
  | "inquiry"
  | "complaint"
  | "booking_request"
  | "follow_up"
  | "internal"
  | "spam"
  | "other";

/** Urgency levels */
export type Urgency = "high" | "medium" | "low";

/** Sentiment values */
export type Sentiment = "positive" | "neutral" | "negative";

/** Worker blueprint status */
export type BlueprintStatus = "draft" | "stable" | "deprecated";

/** Worker blueprint category */
export type BlueprintCategory =
  | "communication"
  | "content"
  | "operations"
  | "admin"
  | "sales";

/** Company tier */
export type CompanyTier = "internal" | "starter" | "professional" | "enterprise";
