
# Appointment Agent Demo Guide (Simple & Technical)

## 1. Introduction (Simple Explanation)

This system is like a smart assistant that helps people book appointments.

Think of it like this:
- You (the customer) send a message
- The system understands what you want
- It checks available times
- It books the appointment for you

But in the background, many systems work together.

---

## 2. Demo Script (For Presentation)

### Start

Say:

"On the left you see the customer. On the right you see what the system is doing."

---

### Step 1 – Customer sends message

Customer:
"I want to book an appointment"

System:
- Message received (LEKAB)
- Orchestrator starts process

---

### Step 2 – System searches slots

System:
- Google Adapter searches available times
- Returns possible slots

---

### Step 3 – Customer selects slot

Customer clicks:
"Tomorrow 10:00"

System:
- Slot selected
- Waiting for confirmation

---

### Step 4 – Booking

Customer clicks:
"Confirm"

System:
- Booking created
- CRM updated
- Confirmation sent

---

### Key Message

"This is not a chatbot. This is a system that connects communication, decisions and backend systems."

---

## 3. What You See on Screen

Left side:
- Customer chat
- Buttons
- Messages

Right side:
- Flow steps
- Status (pending, active, done)
- Audit log
- Booking info

---

## 4. Technical Explanation (Advanced)

### Core Components

- LEKAB → messaging layer
- Orchestrator → brain
- Google Adapter → calendar
- CRM → business system

---

### Important Parameters

- journey_id → unique process
- correlation_id → connects everything
- trace_id → debugging
- booking_reference → internal ID
- provider_reference → Google ID

---

### Example Flow Events

- message.received
- search.requested
- slots.found
- booking.created
- crm.update

---

## 5. What happens with 20 users?

Good question!

The system handles many users like this:

### 1. Independent journeys
Each user gets its own journey_id.

### 2. No collisions
Slots are managed carefully:
- temporary holds
- booking confirmation step

### 3. Performance
- system runs async
- components scale separately

### 4. Example
20 users request slots:
- all requests processed in parallel
- only one can confirm a specific slot
- others get updated options

---

## 6. Key Message for Engineers

"This is an event-driven system with clear separation of concerns:
- communication
- orchestration
- provider integration
- state management"

---

## 7. Summary

- Easy for users
- Powerful inside
- Scalable
- Transparent
