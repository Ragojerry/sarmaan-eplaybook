import { LearnerRole } from "./types/api";

/** Learner roles (what a learner does in the field). They decide which
 *  role-specific modules a learner sees; they are never portal permissions. */
export const LEARNER_ROLES: { value: LearnerRole; label: string }[] = [
  { value: "CDD", label: "CDD" },
  { value: "HEALTH_WORKER", label: "Health Worker" },
  { value: "LOGISTICIAN", label: "Logistician" },
  { value: "MONITOR_SUPERVISOR", label: "Monitor/Supervisor" },
  { value: "OTHER", label: "Others" },
];

export function learnerRoleLabel(value: string | null | undefined): string {
  return LEARNER_ROLES.find((r) => r.value === value)?.label ?? "—";
}

/** The portal role CDD is the learner account (phone app only, no portal access). */
export function portalRoleLabel(role: string): string {
  return role === "CDD" ? "Learner (phone app)" : role.replace(/_/g, " ");
}
