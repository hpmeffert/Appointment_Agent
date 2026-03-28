
# CODEX_TASK_DEMO_PHASE_A_AND_RELEASE_SETUP_V1.0.2.md

## Title
Execute Demo Phase A (Sales Demo Optimization) + Prepare GitHub Repository, UI Standardization and Release

---

## Objective
This task has **two main goals**:

### 1. Demo Phase A (NOW)
Optimize the **Demo UI (Sales / Story Mode)** so it is:
- perfectly usable for live presentations
- aligned with the demo dossier and speaker script
- visually consistent and intuitive

### 2. Platform Setup (AFTER Demo A)
Prepare the project for:
- GitHub repository structure
- versioning and release strategy
- UI standardization (Incident Demo Look & Feel)
- documentation integration via UI

---

# PART 1 – DEMO PHASE A (PRIORITY)

## Goal
Create a **high-quality Sales Demo Experience**

---

## Requirements

### 1. Demo UI Refinement

Improve existing UI:
`/ui/demo-monitoring/v1.0.0`

Focus on:

- clearer layout
- larger buttons for actions
- reduced technical clutter in Demo Mode
- smoother step transitions

---

### 2. Speaker Support (VERY IMPORTANT)

UI must visibly support:

#### Section: "What You Can Say"
- short presenter text per step
- easy to read
- aligned with demo dossier

#### Section: "What Happens in System"
- simple explanation (like for 16-year-old)
- optional technical explanation toggle

---

### 3. Scenario Optimization

Ensure following scenarios are perfect:

- Standard Booking (PRIMARY DEMO)
- No Slot → Escalation
- Reschedule (optional)
- Cancellation (optional)

---

### 4. Demo Flow Controls

UI must support:

- Next Step
- Restart
- Autoplay
- Scenario Selection

---

### 5. Language Support

Default:
- English

Selectable:
- German

Requirement:
- UI text switchable
- Documentation language follows selection

---

# PART 2 – UI STANDARDIZATION

## Goal
Align UI with **Incident Demo / Incident Management Look & Feel**

---

## Requirements

- same layout structure
- same spacing and card style
- same button styling
- consistent typography

If needed:
- reuse existing CSS/components
- replicate visual hierarchy

---

# PART 3 – DOCUMENTATION IN UI

## Goal
Make documentation easily accessible during demo

---

## Requirements

### 1. Help Icon

Add:
- question mark icon (?) in top-right

---

### 2. Dropdown Menu

Options:

- Demo Guide
- User Guide
- Admin Guide

---

### 3. Behavior

When clicked:
- open new browser tab
- load corresponding markdown-rendered document

---

## Target Routes

- /docs/demo
- /docs/user
- /docs/admin

---

# PART 4 – GITHUB REPOSITORY SETUP

## Goal
Prepare project for structured versioning and releases

---

## Requirements

### 1. Repository Structure

Ensure:

- apps/
- docs/
- tests/
- scripts/
- docker/
- README.md

---

### 2. Versioning

Current version:
- v1.0.1 → core system
- v1.0.0 → demo UI

Prepare:
- v1.0.2 → demo + integration improvements

---

### 3. Release Creation

Create:

- Git tag: v1.0.2
- Release Notes:
  - Demo UI
  - Orchestrator-Google integration
  - Documentation improvements

---

### 4. README

Update README with:

- project overview
- architecture diagram
- how to run demo
- how to run backend
- demo URL

---

# PART 5 – SECURITY (BASIC)

## Goal
Safe initial public repo

---

## Requirements

- .env excluded via .gitignore
- no credentials committed
- sample config file:
  - `.env.example`

---

# ACCEPTANCE CRITERIA

This task is complete only if:

1. Demo Mode is presentation-ready
2. UI matches Incident Demo style
3. Language switch works (EN/DE)
4. Help menu opens documentation in new tab
5. Demo scenarios run smoothly
6. GitHub repo is structured
7. Version v1.0.2 is created
8. README is complete
9. No sensitive data is committed

---

# DEFINITION OF DONE

Done means:

- You can run a **professional live demo**
- You can explain system clearly to:
  - customers
  - management
  - developers
- The project is ready for GitHub visibility and controlled evolution

---

# NEXT STEP (AFTER THIS TASK)

→ Phase B:
Technical Monitoring Expansion
- deeper event visualization
- correlation tracking
- performance simulation

