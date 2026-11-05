# Implementation Plan: AI brief summary adapter (gated)

**Branch**: `044-ai-summary-adapter` | **Date**: 2026-11-05 | **Spec**: [spec.md](spec.md)

## Task Outline

1. Provider adapter behind `SummarizerPort` with timeouts and resolver.
2. Structured output with fact references; validator.
3. Evaluation set with a fake provider in CI.
4. Web button driven by the manifest; flips.
