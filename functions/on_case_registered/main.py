"""
on_case_registered — Catalyst Event Function.

Structural placeholder only. See LUMEN_MASTER_SPEC_V3 §19.2: subscribes
to `CaseRegistered`, feeding Resolution, Graph, Quality, Cache, Insight,
Notify. Not yet implemented — the intelligence bus (§19) is Session 12's
scope. This file exists so `catalyst serve`/`catalyst deploy` can resolve
a valid entry point for the function declared in `catalyst.json`; it
contains no event-handling logic.
"""


def handler(event, context):
    context.close_with_success()
