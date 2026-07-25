/**
 * Lead sorting (Part 3) — pure, shared, testable. "Relevance" ranks by overlap
 * with the current investigation context (case/persons/districts), so relevance
 * is DEFINED, not vibes: one point per matching related entity.
 */
import type { IntelligenceLead, LeadSort } from "@/types/intelligence";

const PRIORITY_RANK: Record<IntelligenceLead["priority"], number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
};

export interface RelevanceContext {
  caseId: string | null;
  persons: string[];
  districts: string[];
}

function relevanceScore(lead: IntelligenceLead, ctx: RelevanceContext): number {
  let score = 0;
  if (ctx.caseId && lead.related_cases.includes(ctx.caseId)) score += 1;
  score += lead.related_persons.filter((p) => ctx.persons.includes(p)).length;
  score += lead.related_locations.filter((d) => ctx.districts.includes(d)).length;
  return score;
}

export function sortLeads(
  leads: IntelligenceLead[],
  sort: LeadSort,
  ctx: RelevanceContext,
): IntelligenceLead[] {
  const copy = [...leads];
  switch (sort) {
    case "confidence":
      return copy.sort((a, b) => b.confidence - a.confidence);
    case "priority":
      return copy.sort(
        (a, b) => PRIORITY_RANK[a.priority] - PRIORITY_RANK[b.priority],
      );
    case "newest":
      return copy.sort((a, b) => b.generated_at.localeCompare(a.generated_at));
    case "relevance":
      return copy.sort((a, b) => relevanceScore(b, ctx) - relevanceScore(a, ctx));
  }
}
