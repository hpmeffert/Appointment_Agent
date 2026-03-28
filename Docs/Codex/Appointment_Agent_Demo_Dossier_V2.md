
# Appointment Agent Demo & Technical Dossier (V2)

## Table of Contents
1. Overview (Simple)
2. Sales Demo Script (Storytelling)
3. Screen Walkthrough (What you see)
4. Technical Deep Dive
5. Concurrency & Performance (20–1000 users)
6. Key Parameters & Events
7. Architecture Mapping
8. Demo Tips
9. Codex Instruction (Integrate into Docs)

---

# 1. Overview (Simple – explain like you're 16)

This system is like a super smart assistant.

You send a message:
👉 "I want an appointment"

The system:
- understands you
- checks available times
- lets you pick one
- books it automatically

BUT inside:
👉 multiple systems work together like a team

---

# 2. Sales Demo Script (What YOU say)

## Opening (30 seconds)
"On the left you see the customer. On the right you see the system thinking and working."

---

## Step 1 – Message
Customer:
"I want to book an appointment"

Say:
👉 "The message comes in via RCS / messaging and enters the system."

---

## Step 2 – System thinks
Say:
👉 "The Orchestrator understands intent and starts the booking process."

---

## Step 3 – Slot Search
Say:
👉 "Now we connect to Google Calendar and check availability."

---

## Step 4 – Selection
Customer clicks slot

Say:
👉 "The user selects a slot – now we have a concrete intent."

---

## Step 5 – Booking
Customer confirms

Say:
👉 "Now we create a real booking and update backend systems."

---

## Closing Statement
👉 "This is not a chatbot. This is process automation."

---

# 3. What you see on screen

## Left (Demo)
- chat
- buttons
- confirmation

## Right (Monitoring)
- system steps
- audit log
- booking info
- events

---

# 4. Technical Deep Dive

## Components
- LEKAB → messaging
- Orchestrator → logic
- Google Adapter → calendar
- CRM → business system

## Flow
User → LEKAB → Orchestrator → Google → Result → CRM

---

# 5. Concurrency & Performance (Important!)

## Question:
"What happens if 20 users book at the same time?"

### Answer:

### 1. Each user = separate journey
- journey_id ensures isolation

### 2. Slot Protection
- temporary holds (soft lock)
- prevents double booking

### 3. Parallel Processing
- async architecture
- each request independent

### 4. Conflict Handling
If 2 users pick same slot:
- first wins
- second gets fallback

---

## Scaling to 1000 users

System handles this by:
- stateless services
- horizontal scaling
- event-driven processing
- queue-based handling (future)

---

# 6. Key Parameters

| Parameter | Meaning |
|----------|--------|
| journey_id | process id |
| correlation_id | connects events |
| trace_id | debug |
| booking_reference | internal |
| provider_reference | Google |

---

# 7. Events

- message.received
- search.requested
- slots.found
- slot.selected
- booking.created
- crm.update
- escalation.requested

---

# 8. Architecture

Customer → LEKAB → Orchestrator → Google → CRM

---

# 9. Demo Tips

- Always use Combined Mode
- Talk slow
- Point left → user
- Point right → system

---

# 10. Codex Instruction

## Task:
Integrate this Demo Guide into documentation.

## Requirements:
- Add to docs/user
- Add to docs/demo
- ensure versioning (v1.0.1)
- include both simple + technical explanation
- keep bilingual optional (EN/DE)

## Files:
- DEMO_GUIDE_V2.md
- USER_GUIDE_EXTENSION.md

## Validation:
- docs not empty
- readable
- matches system behavior

