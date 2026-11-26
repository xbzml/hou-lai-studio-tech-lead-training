#!/usr/bin/env python3
"""Standalone T03 counterexample runner.

Read-only for the ordercheck package. CLI inputs are created in the OS temp
directory. Run from the training project root:

    python -B t03_repro.py
"""
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from ordercheck.checker import check_order
from ordercheck.evidence import make_pointer, verify_pointer

BASE = (ROOT / "fixtures" / "order_ok.txt").read_text(encoding="utf-8")

OK, REPRO, SPEC, INFO = "OK", "REPRODUCED", "SPECULATIVE", "INFO"
records = []


def record(section, case_id, status, detail):
    records.append((section, case_id, status))
    print(f"{case_id:5s} {status:11s} {detail}")


def replace_field(name, value):
    return "\n".join(
        (f"{name}: {value}" if line.startswith(name + ":") else line)
        for line in BASE.splitlines()
    ) + "\n"


# ---------------------------------------------------------------------------
# A. checker.check_order
# ---------------------------------------------------------------------------
print("=== A. checker.check_order  (T03: invalid structure/value => REVIEW or BLOCK) ===")
CHECKER_CASES = [
    ("A1", "duplicate Material: TBD then 316L",
     BASE.replace("Material: 316L\n", "Material: TBD\nMaterial: 316L\n")),
    ("A1", "duplicate Quantity twice",
     BASE.replace("Quantity: 5\n", "Quantity: 5\nQuantity: 5\n")),
    ("A1", "duplicate Product: Valve then Pump",
     BASE.replace("Product: Pump\n", "Product: Valve\nProduct: Pump\n")),
    ("A2", "unknown key Price", BASE + "Price: 100\n"),
    ("A2", "lowercase key order id", BASE + "order id: SYN-999\n"),
    ("A2", "empty key", BASE + ": x\n"),
    ("A3", "line without colon", BASE + "this line has no colon\n"),
    ("A4", "Product Valve", replace_field("Product", "Valve")),
    ("A4", "Product lowercase pump", replace_field("Product", "pump")),
    ("A5", "Flow unit L/s", replace_field("Flow", "50 L/s")),
    ("A5", "Flow negative", replace_field("Flow", "-50 m3/h")),
    ("A5", "Flow nan", replace_field("Flow", "nan m3/h")),
    ("A5", "Flow inf", replace_field("Flow", "inf m3/h")),
    ("A5", "Flow extra text after unit", replace_field("Flow", "50 m3/h extra")),
    ("A5", "Head unit cm", replace_field("Head", "30 cm")),
    ("A5", "Head uppercase M", replace_field("Head", "30 M")),
    ("A6", "Quantity fractional", replace_field("Quantity", "5.5")),
    ("A6", "Quantity zero", replace_field("Quantity", "0")),
    ("A6", "Quantity negative", replace_field("Quantity", "-3")),
    ("A6", "Quantity with unit", replace_field("Quantity", "5 pcs")),
]
for case_id, desc, text in CHECKER_CASES:
    result = check_order(text)
    status = OK if result["decision"] in ("REVIEW", "BLOCK") else REPRO
    record("checker", case_id, status,
           f"expected=REVIEW/BLOCK actual={result['decision']:6s} "
           f"findings={result['findings']} | {desc}")

# ---------------------------------------------------------------------------
# B. CLI fail closed
# ---------------------------------------------------------------------------
print()
print("=== B. python -m ordercheck  (T03: read/encoding/format errors => BLOCK/2 + JSON) ===")


def run_cli(args):
    return subprocess.run(
        [sys.executable, "-B", "-m", "ordercheck"] + args,
        cwd=ROOT, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )


def cli_detail(proc):
    out = proc.stdout.strip()
    err = proc.stderr.strip().splitlines()
    err_last = err[-1] if err else ""
    return (f"actual=exit {proc.returncode} "
            f"stdout={out[:70]!r} stderr_last={err_last[:80]!r}")


with tempfile.TemporaryDirectory() as td:
    tmp = Path(td)
    bad_utf8 = tmp / "bad_utf8.txt"
    bad_utf8.write_bytes(b"\xff\xfeOrder ID: SYN-001\n")
    non_txt = tmp / "order.dat"
    non_txt.write_text(BASE, encoding="utf-8")
    empty_txt = tmp / "empty.txt"
    empty_txt.write_text("", encoding="utf-8")
    bom_txt = tmp / "bom.txt"
    bom_txt.write_bytes(b"\xef\xbb\xbf" + BASE.encode("utf-8"))
    missing = tmp / "missing.txt"

    CLI_CASES = [
        ("B1", "nonexistent file", [str(missing)], REPRO),
        ("B1", "path is a directory", ["fixtures"], REPRO),
        ("B1", "non-UTF8 input", [str(bad_utf8)], REPRO),
        ("B2", "non-TXT .dat with valid order", [str(non_txt)], REPRO),
    ]
    for case_id, desc, args, expected_status in CLI_CASES:
        proc = run_cli(args)
        blocked = proc.returncode == 2 and '"BLOCK"' in proc.stdout
        status = OK if blocked else expected_status
        record("cli", case_id, status,
               f"expected=BLOCK/exit2 {cli_detail(proc)} | {desc}")

    proc = run_cli([])
    record("cli", "B3", INFO,
           f"expected=(unspecified) {cli_detail(proc)} | no args shares BLOCK exit code")

    proc = run_cli([str(bom_txt)])
    record("cli", "B4", SPEC,
           f"expected=(unspecified) {cli_detail(proc)} | UTF-8 BOM makes valid order REVIEW")

    proc = run_cli([str(empty_txt)])
    record("cli", "B5", INFO,
           f"expected=REVIEW/1 {cli_detail(proc)} | empty TXT is treated as missing fields")

# ---------------------------------------------------------------------------
# C. evidence
# ---------------------------------------------------------------------------
print()
print("=== C. evidence  (T03: mismatch => REJECTED; invalid input => UNVERIFIABLE/REJECTED) ===")
raw = b"Flow: 50 m3/h"
pointer = make_pointer("D1", raw, 6, len(raw))
print(f"control: raw={raw!r} len={len(raw)} pointer={pointer}")


def evidence_case(case_id, desc, expected, fn, speculative=False):
    try:
        actual = fn()
        shown = actual
    except Exception as exc:  # noqa: BLE001 - demonstration runner
        actual = None
        shown = f"{type(exc).__name__} (exception)"
    if expected == "VERIFIED":
        ok = actual == "VERIFIED"
    else:
        ok = actual in ("REJECTED", "UNVERIFIABLE")
    if ok:
        status = OK
    elif speculative:
        status = SPEC
    else:
        status = REPRO
    record("evidence", case_id, status,
           f"expected={expected} actual={shown} | {desc}")


evidence_case("E0", "valid pointer (control)", "VERIFIED",
              lambda: verify_pointer("D1", raw, pointer))
evidence_case("E1", "wrong document_id", "REJECTED/UNVERIFIABLE",
              lambda: verify_pointer("OTHER", raw, pointer))
evidence_case("E2", "tampered source_digest", "REJECTED/UNVERIFIABLE",
              lambda: verify_pointer("D1", raw, {**pointer, "source_digest": "0" * 64}))
evidence_case("E3", "tampered start/end", "REJECTED/UNVERIFIABLE",
              lambda: verify_pointer("D1", raw, {**pointer, "start": 0, "end": 4}))
evidence_case("E4", "empty quote", "REJECTED/UNVERIFIABLE",
              lambda: verify_pointer("D1", raw, {
                  "document_id": "D1", "source_digest": "0" * 64,
                  "start": 0, "end": 0, "quote": ""}))
evidence_case("E5", "quote outside declared range", "REJECTED/UNVERIFIABLE",
              lambda: verify_pointer("D1", raw, {
                  "document_id": "D1", "source_digest": "0" * 64,
                  "start": 0, "end": 4, "quote": "50 m3/h"}))
evidence_case("E6", "empty raw + empty quote", "REJECTED/UNVERIFIABLE",
              lambda: verify_pointer("D1", b"", {
                  "document_id": "D1", "source_digest": "0" * 64,
                  "start": 0, "end": 0, "quote": ""}))
evidence_case("E7", "bool range", "REJECTED/UNVERIFIABLE",
              lambda: verify_pointer("D1", raw, {
                  "document_id": "D1", "source_digest": "0" * 64,
                  "start": True, "end": 4, "quote": "Flow"}))
evidence_case("E8", "range beyond raw", "REJECTED/UNVERIFIABLE",
              lambda: verify_pointer("D1", raw, {
                  "document_id": "D1", "source_digest": "0" * 64,
                  "start": 0, "end": 9999, "quote": "Flow: 50 m3/h"}))
evidence_case("E9", "raw modified, old pointer", "REJECTED/UNVERIFIABLE",
              lambda: verify_pointer("D1", b"XX" + raw + b"YY", pointer))
evidence_case("E10", "cross-document same bytes", "REJECTED/UNVERIFIABLE",
              lambda: verify_pointer("D2", raw, pointer))
evidence_case("E11", "start>end + empty quote", "REJECTED/UNVERIFIABLE",
              lambda: verify_pointer("D1", raw, {
                  "document_id": "D1", "source_digest": "0" * 64,
                  "start": 6, "end": 3, "quote": ""}))
evidence_case("E12", "missing quote key", "REJECTED/UNVERIFIABLE",
              lambda: verify_pointer("D1", raw, {"document_id": "D1"}))
evidence_case("E13", "quote is None", "REJECTED/UNVERIFIABLE",
              lambda: verify_pointer("D1", raw, {"quote": None}))
evidence_case("E14", "raw is str", "REJECTED/UNVERIFIABLE",
              lambda: verify_pointer("D1", "Flow: 50 m3/h", pointer))
bad_raw = b"\xffFlow: 50 m3/h"
evidence_case("E15", "invalid UTF-8 raw, valid slice", "REJECTED/UNVERIFIABLE",
              lambda: verify_pointer("D1", bad_raw, {
                  "document_id": "D1",
                  "source_digest": __import__("hashlib").sha256(bad_raw).hexdigest(),
                  "start": 1, "end": 5, "quote": "Flow"}),
              speculative=True)

# ---------------------------------------------------------------------------
# make_pointer boundary
# ---------------------------------------------------------------------------
print()
print("=== C2. make_pointer boundary  (T03: invalid interval => ValueError/UnicodeError) ===")
for case_id, start, end in [
    ("P1", 6, 3), ("P2", -100, 4), ("P3", 0, 9999),
    ("P4", True, 4), ("P5", 5, 5), ("P6", 1.5, 4), ("P7", "0", 4),
]:
    try:
        made = make_pointer("D1", raw, start, end)
        record("make_pointer", case_id, REPRO,
               f"expected=ValueError actual=no exception quote={made['quote']!r} "
               f"| start={start!r}, end={end!r}")
    except Exception as exc:  # noqa: BLE001 - demonstration runner
        ok = isinstance(exc, (ValueError, UnicodeError))
        record("make_pointer", case_id, OK if ok else REPRO,
               f"expected=ValueError/UnicodeError actual={type(exc).__name__} "
               f"| start={start!r}, end={end!r}")

try:
    make_pointer("D1", "流".encode("utf-8"), 0, 1)
except UnicodeDecodeError:
    record("make_pointer", "P8", OK,
           "expected=UnicodeError actual=UnicodeDecodeError | multibyte split")
except Exception as exc:  # noqa: BLE001 - demonstration runner
    record("make_pointer", "P8", REPRO,
           f"expected=UnicodeError actual={type(exc).__name__} | multibyte split")
else:
    record("make_pointer", "P8", REPRO,
           "expected=UnicodeError actual=no exception | multibyte split")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print()
print("=== SUMMARY ===")
for section in ("checker", "cli", "evidence", "make_pointer"):
    rows = [status for sec, _, status in records if sec == section]
    print(f"{section:12s} total={len(rows):2d} "
          f"reproduced={rows.count(REPRO):2d} ok={rows.count(OK):2d} "
          f"speculative={rows.count(SPEC):2d} info={rows.count(INFO):2d}")
