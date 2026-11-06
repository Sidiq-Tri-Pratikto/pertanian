# Implementation Plan for the gated AI brief summary adapter

**Branch**: `044-ai-summary-adapter` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Baseline and scope

Spec 022 ships an editable deterministic brief, document-level export redaction and `POST /briefs/{brief_id}/summary` backed by the off implementation of `SummarizerPort`. Keep that public path and off default. Exercise the existing injection seam with synthetic facts and a fake provider. A real provider, credentialed configuration, network egress and manifest or registry activation wait for the external gate.

## Design

1. Derive the eligible input from the stored template and live server authorization. Verify the active owner, pinned source/target and current source permissions. Reuse the document access evaluation for referenced document versions and exclude ineligible sentences. A provider receives only the authorized candidate sentence text and request-local identifiers. Keep internal references and raw document content on the server. Check access before each attempt and again before returning selected facts so revocation during a call cannot reveal stale content.
2. Replace vocabulary overlap with extractive validation in `app/briefs/service/summarizer_service.py`. The provider returns a structured selection of request-local IDs. The server accepts a nonempty proper subset of candidates with unique valid IDs and no extra fields or provider-generated text. Render whole selected sentences in template order with their existing references. Model identity, model version and prompt template version accompany an accepted result and come from the trusted adapter configuration. The result is a suggestion and the stored template is the fallback.
   Each attempt has a new set of opaque identifiers. The port takes only `{id, text}` candidates and returns exactly `{sentence_ids: string[]}`. Successful API responses include the selected original sentences and references, plus trusted model and prompt provenance.
3. Keep a finite timeout per attempt. Retry one classified transient dependency failure at most and refuse malformed or unsupported output immediately. Use the centralized typed error, sanitized recording and privacy-safe diagnostics for terminal failure. Distinguish the intentional off status from failure without exposing provider payloads. The template fallback still applies live document redaction.
4. After provider approval, implement the concrete async transport and provider resolver, constrain egress and validate explicit settings at startup. Treat candidate text as data in the prompt and restrict the provider to the selection schema. Drive the optional S11 action from the live adapter manifest. Keep the user's edits on failure or if the draft changed while awaiting a response, and require explicit confirmation to replace edited text.

## Evidence

The synthetic CI evaluation covers exact source extraction, recombined known words and numbers, unknown and repeated IDs, extra fields, embedded instructions, unauthorized references, in-flight revocation, bounded retry and fallback. Record the evaluated model and prompt versions and independent review before activation. The fixture proves the local policy and fallback, while the approved provider requires its own contract check.
