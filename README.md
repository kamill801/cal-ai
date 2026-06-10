# Trust-First AI Nutrition Logger

AI food logging MVP for trustworthy photo analysis, lightweight clarification, daily nutrition tracking, and body-adaptive next-meal guidance.

## Source Documents

- `docs/PRD.md`: product decisions
- `docs/TECHSPEC.md`: architecture, schemas, API contracts, AI pipeline
- `docs/PLAN.md`: implementation milestones
- `DESIGN.md`: provisional design contract and Figma reference

## Workspace

```text
apps/mobile/      Expo React Native app
services/api/     FastAPI backend
packages/shared/  Shared TypeScript contracts
docs/             Product and technical specs
```

## Setup

Install JavaScript dependencies:

```bash
npm install
```

Create and install the Python API environment:

```bash
python3 -m venv services/api/.venv
services/api/.venv/bin/pip install -r services/api/requirements.txt
```

## Run

API:

```bash
npm run dev:api
```

Mobile:

```bash
npm run dev:mobile
```

## Verify

```bash
npm run test:api
npm run typecheck:mobile
```

The first MVP development target is the design-independent scaffold: API health, onboarding target calculation, shared contracts, and mobile mock flow wiring.
