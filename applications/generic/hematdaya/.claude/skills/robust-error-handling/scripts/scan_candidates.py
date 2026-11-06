#!/usr/bin/env python3
"""List error-handling *candidates* in Python, Java, and TypeScript/JavaScript.

Regex-based and deliberately over-inclusive: every hit is a lead that must be
verified by reading the code. Rule IDs match references/rules.md.

Usage:
    scan_candidates.py [PATH ...] [--include-tests] [--json] [--max-per-rule N]

Exit code is 0 whether or not candidates are found; 2 on bad arguments.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import asdict, dataclass

SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "bower_components",
    "vendor",
    "third_party",
    ".venv",
    "venv",
    "env",
    ".tox",
    ".nox",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".pytest_cache",
    "site-packages",
    "build",
    "dist",
    "out",
    "target",
    ".gradle",
    ".idea",
    ".next",
    ".nuxt",
    "coverage",
    ".worktrees",
    ".tmp",
    "generated",
    "migrations",
}
LANG_BY_EXT = {
    ".py": "python",
    ".java": "java",
    ".ts": "ts",
    ".tsx": "ts",
    ".mts": "ts",
    ".cts": "ts",
    ".js": "ts",
    ".jsx": "ts",
    ".mjs": "ts",
    ".cjs": "ts",
}
TEST_FILE = re.compile(
    r"(^|/)(tests?|__tests__|spec|test_utils)/|(^|/)test_[^/]*\.py$|_test\.py$|Tests?\.java$|IT\.java$"
    r"|\.(test|spec)\.[cm]?[jt]sx?$"
)
MINIFIED = re.compile(r"\.min\.[cm]?js$")

ERR = r"(?:e|ex|exc|err|error|exception)"
SENSITIVE = r"(?:password|passwd|secret|token|api_?key|authorization|cookie|credentials?|private_?key)s?"


@dataclass(frozen=True)
class Rule:
    """A regex check mapped to a rules.md check ID."""

    rule_id: str
    lang: str  # python | java | ts | all
    pattern: re.Pattern[str]
    hint: str
    exclude: re.Pattern[str] | None = None


def rx(pattern: str, flags: int = 0) -> re.Pattern[str]:
    """Compile a multiline regex."""
    return re.compile(pattern, re.MULTILINE | flags)


RULES: list[Rule] = [
    # ---------------- all languages ----------------
    Rule(
        "M1",
        "all",
        rx(
            r"""["'`](?:something went wrong|an? (?:unknown |unexpected )?error(?: has)? occurred|unknown error"""
            r"""|internal (?:server )?error|unexpected error|(?:request|operation) failed|oops[^"'`]{0,20})[.!]?["'`]""",
            re.IGNORECASE,
        ),
        "generic message with no next step",
    ),
    Rule(
        "M1",
        "all",
        rx(
            r"""["'`][^"'`\n]{0,80}(?:see debug info|check the logs|see the logs|for more details)[^"'`\n]{0,40}["'`]""",
            re.IGNORECASE,
        ),
        "message points at logs or debug info the reader cannot open",
    ),
    Rule(
        "M2",
        "all",
        rx(
            r"""["'`](?:\d{3}[ \t]+)?(?:too many requests|bad request|unauthorized|forbidden)["'`]""",
            re.IGNORECASE,
        ),
        "HTTP status text used as the message",
    ),
    Rule(
        "D4",
        "all",
        rx(
            rf"\b(?:log|logger|logging|LOG|LOGGER|console|structlog|Sentry)\.\w+\([^\n]*\b{SENSITIVE}\b",
            re.IGNORECASE,
        ),
        "sensitive-looking value in a log call",
        exclude=rx(r"redact|mask|\*\*\*|\[REDACTED\]", re.IGNORECASE),
    ),
    Rule(
        "R2",
        "all",
        rx(
            r"(?:status_code|status|HttpStatus|statusCode)[ \t]*(?:=|\(|:)[ \t]*(?:429|HTTP_429_TOO_MANY_REQUESTS|TOO_MANY_REQUESTS)\b"
        ),
        "429 response; confirm a matching Retry-After header and recovery fields",
        exclude=rx(r"retry.?after", re.IGNORECASE),
    ),
    # ---------------- python ----------------
    Rule(
        "D6",
        "python",
        rx(r"^[ \t]*except[ \t]*:"),
        "bare except (also traps CancelledError/KeyboardInterrupt)",
    ),
    Rule(
        "D6",
        "python",
        rx(r"^[ \t]*except[ \t]*\(?[ \t]*(?:BaseException|Exception)\b"),
        "broad except; valid only at a boundary that logs and converts",
    ),
    Rule(
        "D1",
        "python",
        rx(
            r"^[ \t]*except\b[^\n]*:[ \t]*(?:#[^\n]*)?\n(?:[ \t]*#[^\n]*\n)*[ \t]+(?:pass|\.\.\.|continue)[ \t]*(?:#[^\n]*)?$"
        ),
        "except body only passes/continues",
    ),
    Rule(
        "D1",
        "python",
        rx(
            r"^[ \t]*except[ \t]*(?:\(?[ \t]*(?:BaseException|Exception)\b[^\n]*)?:[ \t]*(?:#[^\n]*)?\n(?:[ \t]*#[^\n]*\n)*[ \t]+return(?:[ \t]+(?:None|False|\[\]|\{\}|\"\"|''))?[ \t]*(?:#[^\n]*)?$"
        ),
        "broad except silently returns a default",
    ),
    Rule(
        "D2",
        "python",
        rx(r"\braise\b[^\n]*\bfrom[ \t]+None\b"),
        "cause chain discarded with `from None`",
    ),
    Rule(
        "D2",
        "python",
        rx(
            rf"\b(?:log|logger|logging|_log|_logger|LOG|LOGGER)\.(?:error|critical|warning|warn)\([^\n]*(?:\{{{ERR}\}}|str\({ERR}\)|repr\({ERR}\)|,[ \t]*{ERR}[ \t]*\))"
        ),
        "failure logged as text without traceback (use logger.exception / exc_info)",
        exclude=rx(r"exc_info|stack_info"),
    ),
    Rule(
        "D5",
        "python",
        rx(
            rf"""^[ \t]*print\([ \t]*(?:{ERR}[ \t]*[,)]|(?:str|repr)\({ERR}\)|f["'][^"'\n]*\{{{ERR}[}}!:])|traceback\.print_exc\("""
        ),
        "failure printed instead of logged",
    ),
    Rule(
        "M2",
        "python",
        rx(
            rf"""detail[ \t]*=[ \t]*(?:str\({ERR}\)|repr\({ERR}\)|f["'][^"'\n]*\{{{ERR}\b)"""
            rf"""|["'](?:error|message|detail|msg)["'][ \t]*:[ \t]*(?:str\({ERR}\)|repr\({ERR}\)|f["'][^"'\n]*\{{{ERR}\b)"""
            r"""|traceback\.format_exc\(\)"""
        ),
        "raw exception text or traceback placed in a response",
    ),
    Rule(
        "M3",
        "python",
        rx(r"^[ \t]*except\b[^\n]*:\n(?:[^\n]*\n){0,6}?[ \t]+sys\.exit\([ \t]*0?[ \t]*\)"),
        "process exits 0 after a failure",
    ),
    Rule(
        "S5",
        "python",
        rx(
            rf"""["'][^"'\n]+["'][ \t]+in[ \t]+str\({ERR}\)|str\({ERR}\)(?:\.lower\(\))?[ \t]*(?:==|\.startswith|\.endswith)"""
        ),
        "control flow branches on exception message text",
    ),
    Rule(
        "S3",
        "python",
        rx(r"^[ \t]*except\b[^\n]*:\n(?:[^\n]*\n){0,6}?[ \t]+raise[ \t]+(?:RuntimeError|Exception)\b"),
        "catch re-raises a generic type and drops the specific failure",
    ),
    Rule(
        "D11",
        "python",
        rx(
            r"""def[ \t]+__str__[ \t]*\([^)]*\)[ \t]*(?:->[^:]+)?:[^\n]*\n(?:[ \t]+[^\n]*\n){0,6}?[ \t]+return\b[^\n]*(?:debug_info|Debug Info)"""
        ),
        "default string form includes debug info",
    ),
    Rule(
        "D7",
        "python",
        rx(r"^[ \t]*asyncio\.(?:create_task|ensure_future)\("),
        "task result dropped; its exception is never observed",
    ),
    Rule(
        "R3",
        "python",
        rx(
            r"^[ \t]*while[ \t]+True[ \t]*:\n(?:[^\n]*\n){0,12}?[ \t]+except\b[^\n]*\n(?:[^\n]*\n){0,6}?[^\n]*\bsleep\("
        ),
        "retry loop with no visible attempt or time limit",
    ),
    Rule(
        "R3",
        "python",
        rx(r"^[ \t]*@(?:tenacity\.)?retry(?:[ \t]*$|\((?:(?!stop).)*\)[ \t]*$)"),
        "retry decorator without a stop condition",
    ),
    Rule(
        "D6",
        "python",
        rx(
            r"^[ \t]*except[ \t]+(?:asyncio\.)?CancelledError\b[^\n]*:\n(?:[ \t]*#[^\n]*\n)*[ \t]+(?:pass|return\b|continue|break)"
        ),
        "CancelledError swallowed; clean up then re-raise",
    ),
    # ---------------- java ----------------
    Rule(
        "D1",
        "java",
        rx(
            r"catch[ \t]*\([^)]*\)\s*\{(?:\s|//[^\n]*|/\*(?:(?!\*/).)*\*/)*\}",
            re.DOTALL,
        ),
        "empty catch block",
    ),
    Rule(
        "D1",
        "java",
        rx(
            r"catch[ \t]*\([^)]*\)\s*\{\s*return\s+(?:null|false|-1|Optional\.empty\(\)|Collections\.empty\w*\(\)|List\.of\(\))\s*;\s*\}"
        ),
        "catch converts failure into a default value silently",
    ),
    Rule(
        "D6",
        "java",
        rx(r"catch[ \t]*\([ \t]*(?:final[ \t]+)?(?:Exception|Throwable|RuntimeException|Error)[ \t]+\w+[ \t]*\)"),
        "broad catch; valid only at a boundary that logs and converts",
    ),
    Rule(
        "D6",
        "java",
        rx(r"catch[ \t]*\([ \t]*(?:final[ \t]+)?InterruptedException[ \t]+\w+[ \t]*\)\s*\{[^}]*\}"),
        "InterruptedException handled without re-interrupting",
        exclude=rx(r"interrupt\(\)|throw\b"),
    ),
    Rule(
        "D5",
        "java",
        rx(r"\.printStackTrace\([ \t]*\)|System\.(?:out|err)\.print"),
        "printed instead of logged",
    ),
    Rule(
        "D2",
        "java",
        rx(r"throw[ \t]+new[ \t]+\w+\([^;]*?\w+\.get(?:Localized)?Message\(\)[ \t]*\)[ \t]*;"),
        "rethrow keeps the message but drops the cause",
    ),
    Rule(
        "D2",
        "java",
        rx(r"\b(?:log|logger|LOG|LOGGER)\.(?:error|warn)\([^;]*\.get(?:Localized)?Message\(\)[ \t]*\)[ \t]*;"),
        "failure logged as text without the throwable (no stack trace)",
    ),
    Rule(
        "M2",
        "java",
        rx(
            r"(?:ResponseEntity|ProblemDetail|\.body\(|Response\.status)[^;]*\b\w+\.(?:get(?:Localized)?Message|toString|getStackTrace)\(\)"
        ),
        "raw exception text placed in a response",
    ),
    Rule(
        "S5",
        "java",
        rx(r"\.get(?:Localized)?Message\(\)[ \t]*\.(?:contains|equals|equalsIgnoreCase|startsWith|endsWith|matches)\("),
        "control flow branches on exception message text",
    ),
    Rule(
        "S3",
        "java",
        rx(
            r"catch[ \t]*\([^)]*\)\s*\{(?:(?!\bcatch\b).){0,500}?throw[ \t]+new[ \t]+(?:RuntimeException|Exception)\(",
            re.DOTALL,
        ),
        "catch re-raises a generic type and drops the specific failure",
    ),
    Rule(
        "D7",
        "java",
        rx(r"^[ \t]*CompletableFuture\.(?:runAsync|supplyAsync)\([^;]*;"),
        "future dropped; its exception is never observed",
        exclude=rx(r"\.(?:exceptionally|handle|whenComplete|join|get)\("),
    ),
    Rule(
        "R3",
        "java",
        rx(
            r"while[ \t]*\([ \t]*true[ \t]*\)\s*\{(?:(?!\bbreak\b).){0,600}?\bcatch\b.{0,300}?Thread\.sleep\(",
            re.DOTALL,
        ),
        "retry loop with no visible attempt or time limit",
    ),
    # ---------------- typescript / javascript ----------------
    Rule(
        "D1",
        "ts",
        rx(
            r"catch[ \t]*(?:\([^)]*\))?\s*\{(?:\s|//[^\n]*|/\*(?:(?!\*/).)*\*/)*\}",
            re.DOTALL,
        ),
        "empty catch block",
    ),
    Rule(
        "D1",
        "ts",
        rx(
            r"\.catch\(\s*(?:\(\s*\w*\s*(?::\s*\w+)?\s*\)|\w+)\s*=>\s*(?:\{\s*\}|null|undefined|void 0|false|\[\]|\{\s*\}\s*)\s*\)"
        ),
        "promise rejection swallowed",
    ),
    Rule(
        "D2",
        "ts",
        rx(r"""\bthrow[ \t]+["'`]|Promise\.reject\([ \t]*["'`]|\breject\([ \t]*["'`]"""),
        "non-Error thrown/rejected (no stack, no code)",
    ),
    Rule(
        "D2",
        "ts",
        rx(
            r"catch[ \t]*\([ \t]*\w+[^)]*\)\s*\{[^{}]*?\bthrow[ \t]+new[ \t]+\w*Error\([^;]*?\)[ \t]*;",
            re.DOTALL,
        ),
        "rethrow inside catch may drop the cause",
        exclude=rx(r"\bcause\b"),
    ),
    Rule(
        "D6",
        "ts",
        rx(r"catch[ \t]*\([ \t]*\w+[ \t]*:[ \t]*any[ \t]*\)"),
        "catch variable typed any; use unknown and narrow",
    ),
    Rule(
        "D5",
        "ts",
        rx(rf"console\.(?:error|warn)\(|console\.log\([^\n]*\b{ERR}\b"),
        "console used instead of the central logger",
    ),
    Rule(
        "M2",
        "ts",
        rx(
            rf"\.(?:send|json|end|write)\([^\n]*\b{ERR}\.(?:stack|message)\b|\.status\([ \t]*5\d\d[ \t]*\)\.(?:send|json)\([ \t]*{ERR}[ \t]*\)"
        ),
        "raw error text or stack placed in a response",
    ),
    Rule(
        "S5",
        "ts",
        rx(rf"\b{ERR}\.message[ \t]*(?:===?|!==?|\.includes\(|\.startsWith\(|\.endsWith\(|\.match\(|\.indexOf\()"),
        "control flow branches on error message text",
    ),
    Rule(
        "S3",
        "ts",
        rx(
            r"catch[ \t]*\([^{]*\)\s*\{[^{}]*?\bthrow[ \t]+new[ \t]+(?:Error|RuntimeError)\([^;]*?\)[ \t]*;",
            re.DOTALL,
        ),
        "catch re-raises a generic Error and may drop the specific failure",
        exclude=rx(r"\bcause\b"),
    ),
    Rule(
        "D7",
        "ts",
        rx(r"\.forEach\([ \t]*async\b"),
        "async callback in forEach: rejections are never awaited",
    ),
    Rule(
        "R3",
        "ts",
        rx(
            r"(?:while[ \t]*\([ \t]*true[ \t]*\)|for[ \t]*\([ \t]*;[ \t]*;[ \t]*\))\s*\{(?:(?!\bbreak\b).){0,600}?\bcatch\b.{0,300}?(?:sleep|delay|setTimeout|wait)\(",
            re.DOTALL,
        ),
        "retry loop with no visible attempt or time limit",
    ),
]


@dataclass
class Hit:
    """One candidate location found by a rule."""

    rule_id: str
    path: str
    line: int
    snippet: str
    hint: str


def _report_walk_error(err: OSError) -> None:
    print(
        f"warning: skipped unreadable path {err.filename}: {err.strerror}",
        file=sys.stderr,
    )


def iter_files(roots: list[str], include_tests: bool):
    """Yield (path, language) for every scannable source file under the roots."""
    for root in roots:
        if os.path.isfile(root):
            candidates = [root]
        else:
            candidates = []
            for dirpath, dirnames, filenames in os.walk(root, onerror=_report_walk_error):
                dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
                candidates.extend(os.path.join(dirpath, f) for f in filenames)
        for path in candidates:
            lang = LANG_BY_EXT.get(os.path.splitext(path)[1])
            norm = path.replace(os.sep, "/")
            if lang is None or MINIFIED.search(norm) or norm.endswith(".d.ts"):
                continue
            if not include_tests and TEST_FILE.search(norm):
                continue
            yield path, lang


def scan_file(path: str, lang: str) -> list[Hit]:
    """Return the candidates found in one file."""
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError as exc:
        print(f"warning: cannot read {path}: {exc.strerror}", file=sys.stderr)
        return []
    lines = text.splitlines()
    hits: list[Hit] = []
    seen: set[tuple[str, int]] = set()
    for rule in RULES:
        if rule.lang not in (lang, "all"):
            continue
        for match in rule.pattern.finditer(text):
            line_no = text.count("\n", 0, match.start()) + 1
            line_text = lines[line_no - 1] if line_no <= len(lines) else ""
            if rule.exclude and (rule.exclude.search(match.group(0)) or rule.exclude.search(line_text)):
                continue
            if (rule.rule_id, line_no) in seen:
                continue
            seen.add((rule.rule_id, line_no))
            hits.append(Hit(rule.rule_id, path, line_no, line_text.strip()[:160], rule.hint))
    return hits


def main(argv: list[str]) -> int:
    """Run the scanner CLI and return the exit code."""
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paths", nargs="*", default=["."])
    parser.add_argument("--include-tests", action="store_true", help="also scan test files")
    parser.add_argument("--json", action="store_true", help="emit JSON lines instead of text")
    parser.add_argument(
        "--max-per-rule",
        type=int,
        default=0,
        help="cap printed hits per rule (0 = no cap)",
    )
    args = parser.parse_args(argv)
    if args.max_per_rule < 0:
        parser.error("--max-per-rule must be 0 or greater")

    missing = [p for p in args.paths if not os.path.exists(p)]
    if missing:
        print(f"error: path not found: {', '.join(missing)}", file=sys.stderr)
        return 2

    hits: list[Hit] = []
    files = 0
    for path, lang in iter_files(args.paths, args.include_tests):
        files += 1
        hits.extend(scan_file(path, lang))
    hits.sort(key=lambda h: (h.rule_id, h.path, h.line))

    counts: dict[str, int] = {}
    for hit in hits:
        counts[hit.rule_id] = counts.get(hit.rule_id, 0) + 1
        if args.max_per_rule and counts[hit.rule_id] > args.max_per_rule:
            continue
        if args.json:
            print(json.dumps(asdict(hit)))
        else:
            print(f"{hit.rule_id}\t{hit.path}:{hit.line}\t{hit.snippet}\t# {hit.hint}")
    if args.json:
        return 0
    summary = ", ".join(f"{rule_id}={n}" for rule_id, n in sorted(counts.items())) or "none"
    print(f"\n# scanned {files} files; {len(hits)} candidates ({summary}). Verify each by reading the code.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
