"""
Extract Gaspy HTTP response AES key constants from dumped snapshot + libapp.so.

Finds `_decode` (HTTP body decrypt), reads the CSRF substring bounds and the two
8-hex-digit constants, then writes key concat order (default A_mid_B).

Writes analyze_gaspy/artifacts/decrypt_config.json

Usage:
  .venv\\Scripts\\python.exe analyze_gaspy\\dump_snapshot.py
  .venv\\Scripts\\python.exe analyze_gaspy\\extract_decrypt_config.py
"""
import argparse
import json
import re
import struct
from pathlib import Path

from capstone import Cs, CS_ARCH_ARM, CS_MODE_ARM
from capstone.arm import ARM_OP_IMM, ARM_OP_MEM

from paths import find_libapp

ap = argparse.ArgumentParser(description="Extract Gaspy decrypt key constants from libapp.so")
ap.add_argument("--artifacts", type=Path)
ap.add_argument("--libapp", type=Path)
ap.add_argument(
    "--assume-order",
    choices=["A_mid_B", "mid_A_B", "B_mid_A", "mid_B_A"],
    default="A_mid_B",
    help="Force key concat order (default A_mid_B)",
)
args = ap.parse_args()
art = args.artifacts
libapp = args.libapp
assume_order = args.assume_order

HEX8 = re.compile(r"^[0-9a-f]{8}$")

if not (art / "meta.json").is_file():
    raise Exception(f"Missing {art / 'meta.json'}; run dump_snapshot.py first")
meta = json.loads((art / "meta.json").read_text(encoding="utf-8"))
strings = {int(k): v for k, v in
           json.loads((art / "strings.json").read_text(encoding="utf-8")).items()}
mints = {int(k): v for k, v in
         json.loads((art / "mints.json").read_text(encoding="utf-8")).items()}
pool = json.loads((art / "pool.json").read_text(encoding="utf-8"))
code_names = {int(k): v for k, v in
              json.loads((art / "code_names.json").read_text(encoding="utf-8")).items()}

hits = [(i, n) for i, n in code_names.items() if
        n.startswith("_decode@") or n == "_decode"]
# Prefer the Gaspy API one: also loads csrfValue / e875-style nearby; filter later.
# Exclude image/codec noise by requiring library-looking suffix with digits.
prefer = [(i, n) for i, n in hits if "1131056342" in n or "gaspy" in n.lower()]
decode_hits = prefer or hits

if not decode_hits:
    raise RuntimeError("No _decode code name found in code_names.json")

so = Path(libapp) if libapp else Path(meta["libapp"])
if not so.is_file():
    so = find_libapp()
data = so.read_bytes()

# Score: want two hex8 + csrfValue + substring bounds
best = {"_score": float('-inf')}
for code_index, name in decode_hits:
    img = meta["img"]
    base = meta["code_entry_base"]
    pool_by = {j: (j, k, v) for j, k, v in pool}
    pool_size = len(pool)

    idx = code_index - 1
    pc, = struct.unpack_from("<I", data, base + 16 + idx * 8)
    pc2, = struct.unpack_from("<I", data, base + 16 + (idx + 1) * 8)
    start = img + pc
    code = data[start: img + pc2]
    md = Cs(CS_ARCH_ARM, CS_MODE_ARM)
    md.detail = True

    loaded_strings: list[tuple[int, str]] = []  # order of appearance
    mov_imms: list[int] = []
    r5_off: dict[str, int] = {}

    for insn in md.disasm(code, start):
        ops = insn.operands
        if insn.mnemonic == "mov" and len(ops) >= 2 and ops[1].type == ARM_OP_IMM:
            mov_imms.append(ops[1].imm)
        if insn.mnemonic == "add" and len(ops) == 3 and ops[2].type == ARM_OP_IMM:
            dst = insn.reg_name(ops[0].reg)
            src = insn.reg_name(ops[1].reg)
            imm = ops[2].imm
            if src == "r5":
                r5_off[dst] = imm
            elif src in r5_off:
                r5_off[dst] = r5_off[src] + imm
        elif insn.mnemonic in ("ldr", "ldrb") and len(ops) >= 2 and ops[
            1].type == ARM_OP_MEM:
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
                    item = pool_by.get(pidx)
                    if item:
                        _j, kind, val = item
                        if kind == "ref" and val in strings:
                            s = strings[val]
                            loaded_strings.append((pidx, s))
                        else:
                            s = None
                    else:
                        s = None

    hex8 = [(p, s) for p, s in loaded_strings if HEX8.match(s)]
    # substring(start, end): start is unboxed int 4 (mov #4); end is Smi 0x28 → value 20
    start_idx = 4 if 4 in mov_imms else None
    end_idx = None
    if 0x28 in mov_imms:
        end_idx = 0x28 >> 1  # Smi
    elif 20 in mov_imms:
        end_idx = 20

    # Concat order from interpolate stack pattern in _decode:
    # After substring, first interpolate loads const A then second loads const B.
    # Live key is A + csrf[start:end] + B (confirmed 3.30.12 / APP capture).
    const_a = hex8[0][1] if len(hex8) >= 1 else None
    const_b = hex8[1][1] if len(hex8) >= 2 else None

    # Token comes from get:csrfValue (XSRF-TOKEN cookie). Pool may also mention
    # sessionValue nearby; that is not the AES key material.
    token_source = "csrfValue"
    if any(s == "csrfValue" for _p, s in loaded_strings):
        token_source = "csrfValue"
    elif any(s == "sessionValue" for _p, s in loaded_strings):
        token_source = "sessionValue"

    info = {
        "code_index": code_index,
        "loaded_strings": loaded_strings,
        "hex8_constants": [s for _p, s in hex8],
        "const_a": const_a,
        "const_b": const_b,
        "substring_start": start_idx,
        "substring_end": end_idx,
        "token_source": token_source,
        "code_size": pc2 - pc,
        "code_file_addr": start,
        "code_name": name
    }

    score = 0
    if len(info["hex8_constants"]) >= 2:
        score += 3
    if info["token_source"] == "csrfValue":
        score += 2
    if info["substring_start"] is not None and info["substring_end"] is not None:
        score += 2
    if "Encrypted" in str(info["loaded_strings"]) or any(
            "AES" in s or s == ":" for _p, s in info["loaded_strings"]
    ):
        score += 1
    info["_score"] = score
    if score > best["_score"]:
        best = info

if best["_score"] < 5:
    raise RuntimeError(
        f"Best _decode candidate looks weak (score={best['_score']}): {best['code_name']}. "
        f"hex8={best['hex8_constants']} start/end={best['substring_start']}/{best['substring_end']}"
    )

const_a = best["const_a"]
const_b = best["const_b"]
start = best["substring_start"]
end = best["substring_end"]
if not const_a or not const_b or start is None or end is None:
    raise RuntimeError(f"Incomplete extract: {best}")

order = assume_order or "A_mid_B"
mid = f"csrf_token[{start}:{end}]"
if order == "A_mid_B":
    expr = f'("{const_a}" + {mid} + "{const_b}").encode("utf-8")'
elif order == "mid_A_B":
    expr = f'({mid} + "{const_a}" + "{const_b}").encode("utf-8")'
elif order == "B_mid_A":
    expr = f'("{const_b}" + {mid} + "{const_a}").encode("utf-8")'
else:
    expr = f'({mid} + "{const_b}" + "{const_a}").encode("utf-8")'
python_key = (
    f"key = {expr}\n"
    "# AES-256-CBC, PKCS7; body is base64(IV) + ':' + base64(ciphertext)\n"
)
python_key = python_key.strip()

config = {
    "app_version": meta.get("app_version"),
    "libapp": str(so),
    "code_index": best["code_index"],
    "code_name": best["code_name"],
    "token_source": best["token_source"],
    "token_cookie": "XSRF-TOKEN",
    "substring_start": start,
    "substring_end": end,
    "const_a": const_a,
    "const_b": const_b,
    "key_order": order,
    "key_template": {
        "A_mid_B": f"{const_a}" + "{csrf[start:end]}" + f"{const_b}",
        "description": "UTF-8 bytes of 32 ASCII chars → AES-256 key",
    },
    "cipher": {
        "algorithm": "AES",
        "mode": "CBC",
        "padding": "PKCS7",
        "key_encoding": "utf-8",
        "body_format": "base64(IV):base64(ciphertext)",
    },
    "python_key": python_key,
}
# Fix template for actual order
mid = f"{{csrf[{start}:{end}]}}"
if order == "A_mid_B":
    config["key_template"]["pattern"] = f"{const_a}{mid}{const_b}"
elif order == "mid_A_B":
    config["key_template"]["pattern"] = f"{mid}{const_a}{const_b}"
elif order == "B_mid_A":
    config["key_template"]["pattern"] = f"{const_b}{mid}{const_a}"
else:
    config["key_template"]["pattern"] = f"{mid}{const_b}{const_a}"

out = art / "decrypt_config.json"
with open(out, "w") as f:
    json.dump(config, f, indent=2)
