---
name: product-ideation-workflow
description: Use this skill when the user wants to reuse the Cal AI-style product planning workflow for a new startup, app, AI service, SaaS, mobile app, web app, or consumer product idea. Trigger for Korean or English prompts about "새 아이디어", "서비스 기획", "아이데이션", "deep interview", "경쟁 서비스 조사", "PRD", "TECHSPEC", "PLAN", "DESIGN", "Figma", "사양주도개발", "기획부터 개발까지", or when the user wants to turn a rough idea into reusable product docs and a development-ready project. This skill coordinates interview, research, specification, design, and implementation handoff; do not jump straight to coding unless the user explicitly asks.
---

# Product Ideation Workflow

## Purpose

Run the reusable workflow used for the Cal AI project:

1. Interview and clarify the idea.
2. Research competitors and best practices when needed.
3. Decide the product angle, target user, MVP, UX, AI pipeline, and monetization.
4. Produce the 3 core planning files: `docs/PRD.md`, `docs/TECHSPEC.md`, and `docs/PLAN.md`.
5. Add `DESIGN.md` and optionally a Figma design pass.
6. Hand off to development, setup, verification, git, and deployment.

Use Korean by default unless the user asks for English.

## Core Rule

Do not immediately write final specs or start coding from a vague idea.

Default flow:

1. Clarify the raw idea.
2. Ask concise high-leverage questions.
3. Identify the strongest differentiation.
4. Research the market only when evidence will improve decisions.
5. Lock product decisions.
6. Write docs.
7. Design.
8. Develop from `PLAN.md`.

If the user explicitly says "바로 작성해줘" or "바로 개발해줘", proceed, but label assumptions clearly.

## Phase 1: Intake

Start by restating:

- One-line concept
- Target user
- Core pain or desire
- Current workaround or competitor
- Why the existing solution is annoying, inaccurate, expensive, slow, or incomplete
- Main interaction loop
- Potential AI advantage
- Main risk

Then ask only the questions that materially change the product direction.

Good first questions:

- Who feels this problem most strongly?
- What is the annoying part of the current behavior?
- What result would make the user trust the product?
- What should feel effortless?
- What should the product never do?
- Is this primarily mobile, web, or both?
- Is the product private utility, social/viral, B2B, or creator-led?
- What would users pay for?

## Phase 2: Differentiation

Actively search for a real wedge. Do not accept shallow differentiation like "AI-powered" or "better UX".

Useful wedge categories:

- Less manual work
- More trust or accuracy
- Faster time-to-result
- Better personalization
- Better emotional tone
- Better habit loop
- Better professional workflow
- Better privacy or safety
- Better price or packaging
- Better local market fit
- Better explainability

When the user has not chosen a wedge, propose 3 to 5 options and recommend one.

## Phase 3: Research

Use research when the answer depends on current or external facts:

- Competitor pricing
- App store positioning
- Product UI patterns
- Legal, privacy, medical, financial, or policy constraints
- Current SDK/API/framework behavior
- Market examples and best practices

Prefer official or primary sources when technical accuracy matters. For competitor analysis, summarize patterns instead of copying proprietary design or wording verbatim.

Research output should include:

- Competitor map
- Feature comparison
- Pricing comparison
- UX flow patterns
- Visual/design patterns
- Technical implications
- Differentiation opportunities
- Risks and constraints

## Phase 4: Decision Lock

Before writing final docs, produce a compact decision lock:

- Product name or placeholder
- Target user
- Core problem
- Primary differentiation
- MVP scope
- Explicit non-goals
- Core user flow
- AI or automation pipeline
- Data storage and privacy policy
- Monetization
- Design direction
- Tech stack assumption
- Validation metrics
- Remaining assumptions

Minor unknowns should not block progress. Mark them as assumptions.

## Phase 5: Documentation

Use the 3-file structure by default.

`docs/PRD.md`:

- Product goal
- User personas
- Problem and opportunity
- MVP user journeys
- Feature requirements
- Monetization and packaging
- Success metrics
- Risks and open questions

`docs/TECHSPEC.md`:

- Product principles
- Architecture
- Frontend, backend, AI, database, and integration responsibilities
- API contracts
- Data models
- AI/model-call schemas
- Safety, privacy, retention, and security rules
- Error handling
- Evaluation and quality gates
- Environment variables
- Acceptance criteria

Keep implementation sequencing out of `TECHSPEC.md`.

`docs/PLAN.md`:

- Implementation order
- Milestones
- Task checklist
- Test and verification plan
- Definition of done
- Launch/deployment steps

When design is important, add `DESIGN.md`:

- Brand feel
- Color and typography
- Layout principles
- Component rules
- Key screens
- Interaction patterns
- Motion and feedback
- Accessibility constraints
- Figma/design tool notes

## Phase 6: Design

If the user wants design, proceed in this order:

1. Read existing `DESIGN.md`, PRD, TECHSPEC, and PLAN if present.
2. Define 2 to 3 visual directions.
3. Recommend one direction.
4. Produce or update `DESIGN.md`.
5. Use Figma or Product Design tooling when available and useful.
6. Reflect final design decisions back into `DESIGN.md`.

Do not make the design a generic landing page unless the product truly needs one. Prefer the actual app experience as the first screen.

## Phase 7: Development Handoff

When development starts:

1. Read `docs/PRD.md`, `docs/TECHSPEC.md`, `docs/PLAN.md`, and `DESIGN.md`.
2. Set up the repo and environment.
3. Implement by `PLAN.md` milestone.
4. Verify with tests, typecheck, lint, build, smoke checks, or screenshots as appropriate.
5. Keep docs updated when product decisions change.
6. Commit and push only when requested or clearly part of the requested workflow.

## Invocation Examples

```md
[$product-ideation-workflow] 새 서비스 아이디어를 기획하고 싶어.
아이디어는: ...
Cal AI 때처럼 질문하면서 문제, 타깃, 차별점, MVP, 수익모델, UX 방향을 같이 찾아가고,
충분히 정리되면 PRD.md / TECHSPEC.md / PLAN.md / DESIGN.md까지 만들어줘.
```

```md
[$product-ideation-workflow] 이 아이디어를 바로 개발 가능한 수준으로 정리해줘.
먼저 deep interview로 모호한 부분을 줄이고, 필요하면 경쟁 서비스 리서치 후 3파일 방식으로 문서화해줘.
```

## Quality Bar

The final workflow output should be specific enough that Codex CLI, Codex App, Cursor, Claude Code, or a human developer can continue without rereading the entire chat.

Avoid vague language. Capture decisions, assumptions, tradeoffs, and rejected options.
