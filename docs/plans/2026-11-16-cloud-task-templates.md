# Cloud task templates implementation plan

Approved: cloud conversational menu first, no Android changes. Knowledgebase remains sole
standard. Task template is a parameterized invocation, not a second policy or permanent approval.

1. Inspect current governance, checkout state, runtime home and existing workspace instructions.
2. Add knowledgebase templates/tasks/online-delivery.md and README link; add config-owned
   linux/skills/delivery-templates/SKILL.md routing to that file, default read-only preflight.
3. Commit config and knowledgebase on their appropriate branches. Submit knowledgebase PR
   without merging; preserve existing cloud branch content. Install only the reviewed template
   and Skill, append workspace discovery hint without replacing SSH/governance instructions.
4. Verify native skill discovery and actual new-session menu response using the live API;
   confirm template read and no execution requested. Record evidence in unique ledger.

Out of scope: pipeline implementation, workflow dispatch, image build/publication, SSH deployment,
Android APK. Missing native discovery or template read blocks completion. No service restart.
