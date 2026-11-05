# Implementation Plan: Discussion, tasks, notifications and whose turn

**Branch**: `027-discussion-notifications-api` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Project Structure

```text
app/discussion/
├── router.py                     # /pitches/{id}/messages, /pitches/{id}/tasks, /tasks/{id}/complete,
│                                 #   /notifications, /notifications/{id}/read, /pitches/{id}/next-action, /me/queue
├── service/next_action.py        # whose turn per party; Beranda queue across pitches
├── service/notifications.py      # outbox consumers
└── repository/sqlalchemy/        # messages, tasks, notifications
migrations/versions/0014_discussion.py
```

## API Contract

`GET /api/v1/pitches/{id}/next-action` → `{"who": "you", "title": "Pilih waktu pertemuan", "text": "...", "tab": "jadwal", "action": "choose_slot"}`; `who` is `you`, `other` or `null`.

`GET /api/v1/me/queue` → ordered items for Beranda, "Menunggu Anda" first.

## Prototype Reference

`pitchTurn`, `queue`, `turnAction` in `views.js`.

## Test Plan

Whose-turn table; AC46 with a failing fake consumer; AC48 through the isolation harness; notifications once per event; polling with `since`; message validation; isolation.

## Out of Scope

Email (042), web (029).

## Task Outline

1. Whose-turn table tests from the prototype.
2. Messages and tasks.
3. Notification consumers.
4. Queue for Beranda; contract.
