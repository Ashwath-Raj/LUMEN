/**
 * The ten named network queries (§14.4) as the query rail (E.6) — each labelled
 * with the plain-language question it answers. These are the INSTRUMENT (the
 * selectable analyses), not data: running one calls `/network/query/{q}` (no
 * backend endpoint yet → degraded). No relationships are fabricated.
 */
import type { NamedQuery } from "@/types/graph";

export const NAMED_QUERIES: NamedQuery[] = [
  { id: "q1", question: "Who is associated with this person?" },
  { id: "q2", question: "Who is the only link between two groups?" },
  { id: "q3", question: "Which individuals are most central?" },
  { id: "q4", question: "What communities exist in this network?" },
  { id: "q5", question: "What is the shortest path between two people?" },
  { id: "q6", question: "Who operates across the most districts?" },
  { id: "q7", question: "Which co-accused pairs recur across cases?" },
  { id: "q8", question: "Which clusters are emerging over time?" },
  { id: "q9", question: "Which nodes bridge separate communities?" },
  { id: "q10", question: "Who are the isolated versus the central actors?" },
];
