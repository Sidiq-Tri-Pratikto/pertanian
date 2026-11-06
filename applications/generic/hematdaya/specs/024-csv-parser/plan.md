# Implementation Plan: CSV parser

**Branch**: `024-csv-parser` | **Date**: 2026-10-30 | **Spec**: [spec.md](spec.md)

## Summary

A pure parser with no database, ported rule by rule with its tests.

## Project Structure

```text
app/imports/
├── model/models.py                  # ParsedFile, RowResult, MappingQuestion
└── service/{dialect.py, columns.py, numbers.py, times.py, cadence.py, parser.py}
tests/unit/imports/
```

## Design

Do not use `csv.Sniffer`. Detect the delimiter from the header outside quotes, as the prototype does. Use `csv.reader` for tokenizing so quoting matches the standard, and track physical lines with `reader.line_num`. Numbers go through `decimal.Decimal` to integer milli-units, three places maximum. Parse validated timestamp shapes with `datetime.fromisoformat`. Resolve confirmed local timestamps with `zoneinfo`. Require an offset or correction for ambiguous or nonexistent local times.

Cadence uses the positive gaps between sorted distinct timestamps per mapped source. Use the median only when at least 90% of those gaps are within one second of it. Confirm inferred durations in preview or require a declared duration or explicit start/end when inference fails. Convert timestamp-only interval rows to `[timestamp, timestamp + duration)`, including the final row, and keep counter points for the counter path. Validate explicit end after start. The preview in 025 classifies overlapping intervals after source identity is resolved.

## Prototype Reference

`tokenize`, `detectDelimiter`, `parseDecimal`, `parseTime`, `parseCsv`, `inferCadence`, `mappingIssues`, tests AT-26 to AT-32.

## Test Plan

Port AT-26, AT-27, AT-28, AT-29, AT-31, AT-32. Add: mixed line endings, duplicate meaning columns, extra columns, blank-line numbering, quoted newline numbering, nonexistent local time, two sources with different cadences, repeated timestamps excluded from the cadence denominator, irregular gaps, final-row interval, counter points, 60 and 61 character names, 10 MiB boundary, performance run.

## Out of Scope

Storage, duplicates against stored data (025), commit (026), screens (027).

## Task Outline

1. Port tests, failing.
2. Dialect and tokenizer.
3. Column aliases.
4. Numbers and times.
5. Cadence.
6. Assemble `parse()`; performance note.
