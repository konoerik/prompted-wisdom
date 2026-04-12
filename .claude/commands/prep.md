Run a pre-ship checklist before I open a PR or push a release.

Work through each item and report pass/fail/skip with a brief reason:

**Code**
- [ ] All tests pass
- [ ] No leftover debug logs, commented-out code, or TODOs in changed files
- [ ] No hardcoded secrets or environment-specific values

**Docs**
- [ ] docs/PLAN.md ## Active updated — completed items moved to ## Done
- [ ] If an architectural decision was made, it's recorded in docs/ARCHITECTURE.md
- [ ] docs/CONTEXT.md reflects the current state

**Review**
- [ ] Changes are scoped to what was planned — no unrelated modifications
- [ ] Any new dependencies are intentional and noted in docs/ARCHITECTURE.md ## Quick Reference

If any item fails, surface it clearly and ask whether to fix it now or proceed anyway.
