/**
 * `AnalystQueryBox` — the workbench query input. A command-line register (mono
 * prompt, Ctrl/⌘+Enter submits), NOT a chat composer. Shows the active
 * investigation context as chips (what will scope the question) and suggested
 * queries phrased from the §17.1 golden-set categories — suggestions are
 * QUESTION AFFORDANCES, not data; answers only ever come from `/ai/ask`.
 */
import { useState, type KeyboardEvent } from "react";
import { CornerDownLeft, Loader2 } from "lucide-react";

import { Badge, Button } from "@/design/primitives";

/** Suggested queries — one per §17.1 golden-set category (phrasing mirrors
 *  data/eval/golden.yaml; ids/districts are placeholders the analyst edits). */
const SUGGESTED: Array<{ category: string; question: string }> = [
  { category: "case lookup", question: "Tell me about case 1000." },
  { category: "person history", question: "What is the case history of this person?" },
  { category: "district comparison", question: "Compare burglary trends across districts this year." },
  { category: "legal", question: "What does IPC 302 cover?" },
  { category: "network", question: "Who connects the accused in case 1000 to other cases?" },
  { category: "forecast", question: "Which districts are at elevated risk next month?" },
];

interface AnalystQueryBoxProps {
  onAsk: (question: string) => void;
  busy: boolean;
  /** Context chips (case / persons / districts) included with the question. */
  contextChips: string[];
  /** Follow-up suggestions from the last answer's subject, if any. */
  followUps?: string[];
}

export function AnalystQueryBox({
  onAsk,
  busy,
  contextChips,
  followUps = [],
}: AnalystQueryBoxProps) {
  const [draft, setDraft] = useState("");

  function submit() {
    const q = draft.trim();
    if (!q || busy) return;
    onAsk(q);
    setDraft("");
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      e.preventDefault();
      submit();
    }
  }

  const suggestions = followUps.length
    ? followUps.map((question) => ({ category: "follow-up", question }))
    : SUGGESTED;

  return (
    <div className="flex flex-col gap-2 border-t border-line bg-panel p-3">
      {contextChips.length ? (
        <div className="flex flex-wrap items-center gap-1.5">
          <span className="text-caption text-ink-faint">context:</span>
          {contextChips.map((chip) => (
            <Badge key={chip} tone="var(--signal)">
              {chip}
            </Badge>
          ))}
        </div>
      ) : null}

      <div className="flex items-end gap-2">
        <span aria-hidden className="pb-2 font-mono text-body text-signal">
          ❯
        </span>
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={onKeyDown}
          rows={2}
          placeholder="Ask the intelligence layer — grounded in canonical records…"
          aria-label="Analyst query"
          className="min-h-[3rem] flex-1 resize-y rounded border border-line bg-void px-3 py-2 font-mono text-dense text-ink-primary outline-none placeholder:font-body placeholder:text-ink-faint focus:border-signal/50"
        />
        <Button variant="primary" onClick={submit} disabled={busy || !draft.trim()}>
          {busy ? (
            <Loader2 size={14} className="animate-spin" aria-hidden />
          ) : (
            <CornerDownLeft size={14} aria-hidden />
          )}
          Ask
        </Button>
      </div>

      <div className="flex flex-wrap gap-1.5">
        {suggestions.map((s) => (
          <button
            key={s.question}
            type="button"
            onClick={() => setDraft(s.question)}
            className="rounded border border-line px-2 py-1 text-caption text-ink-muted transition-colors duration-DEFAULT ease-ease hover:border-signal/40 hover:text-ink-primary"
            title={s.category}
          >
            {s.question}
          </button>
        ))}
      </div>
    </div>
  );
}
