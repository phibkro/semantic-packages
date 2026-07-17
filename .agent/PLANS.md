# Execution plans

An ExecPlan is a living design and implementation document that lets an agent complete substantial work using only the repository and the plan.

Each ExecPlan must contain:

1. **Purpose and observable outcome**
2. **Context and repository map**
3. **Non-goals and constraints**
4. **Specification changes**
5. **Implementation steps in dependency order**
6. **Quality gates and evidence required**
7. **Progress checklist**
8. **Discoveries and changed assumptions**
9. **Decision log**
10. **Result and remaining work**

Plans must describe commands and expected observations. Update the plan whenever implementation reveals that the original design is wrong or incomplete. Completed plans move from `docs/exec-plans/active/` to `docs/exec-plans/completed/`.
