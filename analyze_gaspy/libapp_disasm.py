"""
Disassemble a Dart AOT Code object from Gaspy libapp.so.

Requires artifacts from dump_snapshot.py (or pass --libapp + --artifacts).

Usage:
  .venv\\Scripts\\python.exe analyze_gaspy\\libapp_disasm.py 17980
  .venv\\Scripts\\python.exe analyze_gaspy\\libapp_disasm.py _decode
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path

from paths import find_libapp
from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from capstone.arm import ARM_OP_IMM, ARM_OP_MEM



def load_artifacts(art: Path) -> tuple[dict, dict, dict, list]:
    meta = json.loads((art / "meta.json").read_text(encoding="utf-8"))
    strings = {int(k): v for k, v in json.loads((art / "strings.json").read_text(encoding="utf-8")).items()}
    mints = {int(k): v for k, v in json.loads((art / "mints.json").read_text(encoding="utf-8")).items()}
    pool = json.loads((art / "pool.json").read_text(encoding="utf-8"))
    return meta, strings, mints, pool


def resolve_code_index(name_or_idx: str, code_names: dict[int, str]) -> int:
    if name_or_idx.isdigit():
        return int(name_or_idx)
    hits = [(i, n) for i, n in code_names.items() if name_or_idx in n]
    if not hits:
        raise SystemExit(f"No code matching {name_or_idx!r}")
    if len(hits) > 1:
        # Prefer exact / shorter match with _decode@ library suffix
        exact = [h for h in hits if h[1] == name_or_idx or h[1].startswith(name_or_idx + "@")]
        if len(exact) == 1:
            return exact[0][0]
        print("Multiple matches:", file=sys.stderr)
        for i, n in hits[:20]:
            print(f"  {i}: {n}", file=sys.stderr)
        raise SystemExit("Pass a code index")
    return hits[0][0]


def describe(pool_by: dict, strings: dict, mints: dict, idx: int) -> str:
    item = pool_by.get(idx)
    if not item:
        return "MISSING"
    _j, kind, val = item
    if kind == "ref":
        if val in strings:
            return f"ref {val} str {strings[val]!r}"[:180]
        if val in mints:
            return f"ref {val} mint {mints[val]}"
        return f"ref {val}"
    if kind == "imm":
        return f"imm {val}"
    return f"{kind} {val}"


def disassemble(data: bytes, meta: dict, pool: list, strings: dict, mints: dict, code_index: int) -> list[dict]:
    ro = meta["ro"]
    img = meta["img"]
    base = meta["code_entry_base"]
    pool_by = {j: (j, k, v) for j, k, v in pool}
    pool_size = meta.get("pool_size") or len(pool)

    idx = code_index - 1
    pc, = struct.unpack_from("<I", data, base + 16 + idx * 8)
    pc2, = struct.unpack_from("<I", data, base + 16 + (idx + 1) * 8)
    start = img + pc
    code = data[start : img + pc2]
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    md.detail = True

    rows = []
    r5_off: dict[str, int] = {}
    print(f"\n===== code {code_index} file {start:#x} size {pc2 - pc} =====")
    for insn in md.disasm(code, start):
        note = ""
        ops = insn.operands
        if insn.mnemonic == "add" and len(ops) == 3 and ops[2].type == ARM_OP_IMM:
            dst = insn.reg_name(ops[0].reg)
            src = insn.reg_name(ops[1].reg)
            imm = ops[2].imm
            if src == "r5":
                r5_off[dst] = imm
            elif src in r5_off:
                r5_off[dst] = r5_off[src] + imm
        elif insn.mnemonic in ("ldr", "ldrb") and len(ops) >= 2 and ops[1].type == ARM_OP_MEM:
            mem = ops[1].mem
            bname = insn.reg_name(mem.base)
            disp = mem.disp
            off = None
            if bname == "r5":
                off = disp
            elif bname in r5_off:
                off = r5_off[bname] + disp
            if off is not None and (off + 1 - 8) % 4 == 0:
                pidx = (off + 1 - 8) // 4
                if 0 <= pidx < pool_size:
                    note = "  ; " + describe(pool_by, strings, mints, pidx)
        line = f"{insn.address:08x}: {insn.mnemonic:8} {insn.op_str}{note}"
        print(line)
        rows.append({"addr": insn.address, "mnemonic": insn.mnemonic, "op": insn.op_str, "note": note})
    return rows


ap = argparse.ArgumentParser(description="Disassemble Gaspy Dart AOT code")
ap.add_argument("code", help="Code index (e.g. 17980) or name fragment (_decode)")
ap.add_argument("--libapp", type=Path)
ap.add_argument("--artifacts", type=Path, default=None)
args = ap.parse_args()

art = args.artifacts
assert (art / "meta.json").is_file(), f"Missing {art / 'meta.json'}; run dump_snapshot.py first"


meta, strings, mints, pool = load_artifacts(art)
code_names = {int(k): v for k, v in json.loads((art / "code_names.json").read_text(encoding="utf-8")).items()}
code_index = resolve_code_index(args.code, code_names)
name = code_names.get(code_index, "?")
print(f"code {code_index}: {name}")

libapp = Path(args.libapp) if args.libapp else Path(meta["libapp"])
if not libapp.is_file():
    libapp = find_libapp()
data = libapp.read_bytes()
disassemble(data, meta, pool, strings, mints, code_index)
