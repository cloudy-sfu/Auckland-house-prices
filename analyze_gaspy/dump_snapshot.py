"""
Parse Dart 3.10 AOT isolate snapshot from libapp.so and dump artifacts.

Writes under analyze_gaspy/artifacts/ (or --out):
  meta.json, strings.json, code_names.json, mints.json, pool.json

Usage (PowerShell, repo venv):
  .venv\\Scripts\\python.exe analyze_gaspy\\dump_snapshot.py
  .venv\\Scripts\\python.exe analyze_gaspy\\dump_snapshot.py --libapp path\\to\\libapp.so
"""
import argparse
import json
import logging
import struct
import sys
from pathlib import Path

from paths import (
    find_instructions_image,
    find_snapshot_offset,
    find_xapk_root,
    read_manifest_version,
)

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="[%(levelname)s] %(message)s",
)

ap = argparse.ArgumentParser(description="Dump Dart AOT snapshot artifacts from Gaspy libapp.so")
ap.add_argument("--libapp", type=Path, help="Path to libapp.so")
ap.add_argument("--artifacts", type=Path, help="Output directory")
args = ap.parse_args()

# Predefined cids (Dart 3.10, 32-bit class list).
CID: dict[str, int] = {}
_names = ['Illegal', 'NativePointer', 'FreeListElement', 'ForwardingCorpse', 'Object',
          'Class', 'PatchClass', 'Function', 'TypeParameters', 'ClosureData',
          'FfiTrampolineData', 'Field', 'Script', 'Library', 'Namespace',
          'KernelProgramInfo', 'WeakSerializationReference', 'WeakArray', 'Code',
          'Bytecode', 'Instructions', 'InstructionsSection', 'InstructionsTable',
          'ObjectPool', 'PcDescriptors', 'CodeSourceMap', 'CompressedStackMaps',
          'LocalVarDescriptors', 'ExceptionHandlers', 'Context', 'ContextScope',
          'Sentinel', 'SingleTargetCache', 'MonomorphicSmiableCall', 'CallSiteData',
          'UnlinkedCall', 'ICData', 'MegamorphicCache', 'SubtypeTestCache', 'LoadingUnit',
          'Error', 'ApiError', 'LanguageError', 'UnhandledException', 'UnwindError',
          'Instance', 'LibraryPrefix', 'TypeArguments', 'AbstractType', 'Type',
          'FunctionType', 'RecordType', 'TypeParameter', 'FinalizerBase', 'Finalizer',
          'NativeFinalizer', 'FinalizerEntry', 'Closure', 'Number', 'Integer', 'Smi',
          'Mint', 'Double', 'Bool', 'Float32x4', 'Int32x4', 'Float64x2', 'Record',
          'TypedDataBase', 'TypedData', 'ExternalTypedData', 'TypedDataView', 'Pointer',
          'DynamicLibrary', 'Capability', 'ReceivePort', 'SendPort', 'StackTrace',
          'SuspendState', 'RegExp', 'WeakProperty', 'WeakReference', 'MirrorReference',
          'FutureOr', 'UserTag', 'TransferableTypedData', 'Map', 'ConstMap', 'Set',
          'ConstSet', 'Array', 'ImmutableArray', 'GrowableObjectArray', 'String',
          'OneByteString', 'TwoByteString'
          ]
for i, n in enumerate(_names):
    CID[n] = i
NAME = {v: k for k, v in CID.items()}

FFI_NUMERIC = ["Int8", "Int16", "Int32", "Int64", "Uint8", "Uint16", "Uint32", "Uint64", "Float", "Double"]
FFI = ["NativeFunction"] + FFI_NUMERIC + ["Void", "Handle", "Bool", "NativeType", "Struct"]
ffi_base = len(_names)
for i, n in enumerate(FFI):
    CID["Ffi" + n] = ffi_base + i
    NAME[ffi_base + i] = "Ffi" + n

TD = [
    "Int8", "Uint8", "Uint8Clamped", "Int16", "Uint16", "Int32", "Uint32", "Int64", "Uint64",
    "Float32", "Float64", "Float32x4", "Int32x4", "Float64x2",
]
td_base = ffi_base + len(FFI)
TD_ELEM = {
    "Int8": 1, "Uint8": 1, "Uint8Clamped": 1, "Int16": 2, "Uint16": 2,
    "Int32": 4, "Uint32": 4, "Int64": 8, "Uint64": 8, "Float32": 4, "Float64": 8,
    "Float32x4": 16, "Int32x4": 16, "Float64x2": 16,
}
for i, n in enumerate(TD):
    base = td_base + i * 4
    CID[f"TypedData{n}"] = base
    CID[f"TypedData{n}View"] = base + 1
    CID[f"ExternalTypedData{n}"] = base + 2
    CID[f"UnmodifiableTypedData{n}View"] = base + 3
    for k in range(4):
        NAME[base + k] = ["", "View", "External", "UnmodView"][k] + n
BYTE_DATA_VIEW = td_base + len(TD) * 4
UNMOD_BYTE_DATA = BYTE_DATA_VIEW + 1
BYTE_BUFFER = UNMOD_BYTE_DATA + 1
NULL_CID = BYTE_BUFFER + 1
NUM_PREDEFINED = NULL_CID + 4
NAME[BYTE_DATA_VIEW] = "ByteDataView"
NAME[UNMOD_BYTE_DATA] = "UnmodByteDataView"
NAME[BYTE_BUFFER] = "ByteBuffer"

RO_ALIGN = 64
OBJ_ALIGN_LOG2 = 3

RO_CIDS = {
    CID["PcDescriptors"], CID["CodeSourceMap"], CID["CompressedStackMaps"],
    CID["String"], CID["OneByteString"], CID["TwoByteString"],
}
FIXED = {
    CID["TypeParameters"], CID["PatchClass"], CID["Function"], CID["ClosureData"],
    CID["FfiTrampolineData"], CID["Field"], CID["Script"], CID["Library"],
    CID["Namespace"], CID["KernelProgramInfo"], CID["UnlinkedCall"], CID["ICData"],
    CID["MegamorphicCache"], CID["SubtypeTestCache"], CID["LoadingUnit"],
    CID["LanguageError"], CID["UnhandledException"], CID["LibraryPrefix"],
    CID["Type"], CID["FunctionType"], CID["RecordType"], CID["TypeParameter"],
    CID["Closure"], CID["Double"], CID["Float32x4"], CID["Int32x4"], CID["Float64x2"],
    CID["GrowableObjectArray"], CID["StackTrace"], CID["RegExp"], CID["WeakProperty"],
    CID["ConstMap"], CID["Map"], CID["ConstSet"], CID["Set"],
}
LENGTHY = {
    CID["TypeArguments"], CID["ObjectPool"], CID["ExceptionHandlers"], CID["Context"],
    CID["ContextScope"], CID["Record"], CID["Array"], CID["ImmutableArray"],
    CID["WeakArray"],
}
CANON_AFTER_FIXED = {
    CID["Type"], CID["FunctionType"], CID["RecordType"], CID["TypeParameter"],
}
FFI_AS_INSTANCE = {CID["Ffi" + n] for n in FFI_NUMERIC + ["Void", "Handle", "Bool"]}

kMax = 127
kEndU = 128
kEndS = 192


class R:
    def __init__(self, buf: bytes, pos: int, end: int):
        self.b = buf
        self.p = pos
        self.end = end

    def u(self) -> int:
        b = self.b[self.p]
        self.p += 1
        if b > kMax:
            return b - kEndU
        r = 0
        s = 0
        while True:
            r |= b << s
            s += 7
            b = self.b[self.p]
            self.p += 1
            if b > kMax:
                return r | ((b - kEndU) << s)

    def i(self, bits: int) -> int:
        b = self.b[self.p]
        self.p += 1
        if b > kMax:
            return b - kEndS
        r = 0
        s = 0
        while True:
            r |= b << s
            s += 7
            b = self.b[self.p]
            self.p += 1
            if b > kMax:
                r += (b - kEndS) << s
                mask = (1 << bits) - 1
                r &= mask
                sign = 1 << (bits - 1)
                if r & sign:
                    r -= 1 << bits
                return r

    def ref(self) -> int:
        result = 0
        while True:
            byte = self.b[self.p]
            self.p += 1
            signed = byte if byte < 128 else byte - 256
            result = signed + (result << 7)
            if signed < 0:
                rid = result + 128
                if rid <= 0:
                    raise RuntimeError(f"bad ref {rid} at {self.p:#x}")
                return rid

    def u8(self) -> int:
        b = self.b[self.p]
        self.p += 1
        return b

    def bytes(self, n: int) -> bytes:
        b = self.b[self.p : self.p + n]
        self.p += n
        return b


def need_ref(r: R, num_objects: int, what: str) -> int:
    rid = r.ref()
    if rid < 1 or rid > num_objects:
        raise RuntimeError(f"ref {rid} out of range during {what} at {r.p:#x}")
    return rid


libapp = args.libapp
out = args.artifacts

data = libapp.read_bytes()
snap, snap_length = find_snapshot_offset(data)
ro = snap + ((snap_length + RO_ALIGN - 1) & ~(RO_ALIGN - 1))
cluster_end = snap + snap_length

ver = data[snap + 20: snap + 52]
feat_end = data.index(b"\x00", snap + 52)
r = R(data, feat_end + 1, cluster_end)
base_objs = r.u()
num_objects = r.u()
num_clusters = r.u()
instr_len = r.u()
instr_off = r.u()

next_ref = 1 + base_objs
strings: dict[int, str] = {}
mints: dict[int, int] = {}
cluster_log: list = []


def canon_layout(count: int) -> None:
    r.u()
    first = r.u()
    gaps = count - first
    if gaps < 0 or gaps > count:
        raise RuntimeError(f"bad canon gaps {gaps} count {count} first {first}")
    for _ in range(gaps):
        r.u()


logging.info(
    f"snapshot={snap:#x} length={snap_length:#x} ro={ro:#x} "
    f"base={base_objs} objects={num_objects} clusters={num_clusters}"
)
logging.info(f"version={ver.decode(errors='replace')} instr_len={instr_len} instr_off={instr_off:#x}")

for ci in range(num_clusters):
    start_pos = r.p
    tags = r.i(32) & 0xFFFFFFFF
    cid = tags >> 12
    canon = (tags >> 1) & 1
    start_ref = next_ref
    kind = NAME.get(cid, f"cid{cid}")
    meta = {"lengths": None, "npre": 0, "ncode": 0, "ndef": 0, "next_w": 0, "size_w": 0}

    if cid in RO_CIDS:
        count = r.u()
        running = 0
        for _ in range(count):
            running += r.u() << OBJ_ALIGN_LOG2
            if cid in (CID["String"], CID["OneByteString"], CID["TwoByteString"]):
                off = ro + running
                tags, _hash_smi, length_smi = struct.unpack_from("<III", data, off)
                _scid = tags >> 12
                if length_smi & 1:
                    text = None
                else:
                    n = length_smi >> 1
                    if n < 0 or n > 100000:
                        text = None
                    else:
                        if _scid == CID["OneByteString"]:
                            raw = data[off + 12: off + 12 + n]
                            try:
                                text = raw.decode("latin1")
                            except Exception:
                                text = None
                        elif _scid == CID["TwoByteString"]:
                            raw = data[off + 12: off + 12 + n * 2]
                            try:
                                text = raw.decode("utf-16-le")
                            except Exception:
                                text = None
                        else:
                            text = None
                if text is not None:
                    strings[next_ref] = text
            next_ref += 1
        if cid == CID["String"] and canon:
            canon_layout(count)
    elif cid == CID["Class"]:
        npre = r.u()
        meta["npre"] = npre
        for _ in range(npre):
            r.i(32)
            next_ref += 1
        nnew = r.u()
        next_ref += nnew
        count = npre + nnew
    elif cid == CID["Code"]:
        ncode = r.u()
        meta["ncode"] = ncode
        for _ in range(ncode):
            r.i(32)
            next_ref += 1
        ndef = r.u()
        meta["ndef"] = ndef
        for _ in range(ndef):
            r.i(32)
            next_ref += 1
        count = ncode + ndef
    elif cid == CID["Mint"]:
        count = r.u()
        for _ in range(count):
            mints[next_ref] = r.i(64)
            next_ref += 1
    elif cid in FIXED or cid in CANON_AFTER_FIXED:
        count = r.u()
        next_ref += count
        if cid in CANON_AFTER_FIXED and canon:
            canon_layout(count)
    elif cid in LENGTHY or cid == CID["ObjectPool"]:
        count = r.u()
        lengths = []
        for _ in range(count):
            lengths.append(r.u())
            next_ref += 1
        meta["lengths"] = lengths
        if cid == CID["TypeArguments"] and canon:
            canon_layout(count)
    elif cid >= td_base and cid < BYTE_DATA_VIEW and (cid - td_base) % 4 == 0:
        count = r.u()
        lengths = []
        for _ in range(count):
            lengths.append(r.u())
            next_ref += 1
        meta["lengths"] = lengths
    elif cid == CID[
        "Instance"] or cid >= NUM_PREDEFINED or cid in FFI_AS_INSTANCE or cid in (
            BYTE_DATA_VIEW, UNMOD_BYTE_DATA
    ) or (cid >= td_base and cid < BYTE_DATA_VIEW and (cid - td_base) % 4 in (1, 2, 3)):
        if (cid >= td_base and cid < BYTE_DATA_VIEW and (cid - td_base) % 4 in (1, 2,
                                                                                3)) or cid in (
                BYTE_DATA_VIEW, UNMOD_BYTE_DATA
        ):
            count = r.u()
            next_ref += count
        else:
            count = r.u()
            meta["next_w"] = r.i(32)
            meta["size_w"] = r.i(32)
            next_ref += count
    else:
        raise RuntimeError(
            f"unhandled cid {cid} ({kind}) at cluster {ci} pos {start_pos:#x}")

    if r.p > cluster_end:
        raise RuntimeError(f"ran past clustered end at cluster {ci} cid {cid}")
    cluster_log.append((ci, cid, kind, canon, count, start_ref, next_ref - 1, meta))

logging.info(f"alloc done next_ref={next_ref} fill_start={r.p:#x} strings={len(strings)} mints={len(mints)}")

code_names: dict[int, str] = {}
pool_entries: list[list] = []
img = ro + instr_off  # instructions usually at RO + instr_off from header; verify below
# Dart stores instructions separately; known layout: IMG = RO + 64 + 12 + code-table...
# We keep RO and IMG derived the same way as prior tooling.
# empirically: IMG = RO + ((instr related)); for 3.30.12 RO=0x2b3480 IMG=0x68acc0
# instr_off from header is relative; prefer: IMG = snap region end alignment + instr?
# Prior notes: RO=0x2b3480, IMG=0x68acc0. Difference = 0x3d7840.
# Keep computing: after clustered objects, instructions live at RO + instr_off for some builds;
# for Gaspy 3.30.12 instr_off from header was used differently.
# Store both; disasm uses: base = RO+64+12 for code entry table.

code_entry_base = ro + 64 + 12


def refs(n: int, what: str) -> list[int]:
    return [need_ref(r, num_objects, what) for _ in range(n)]


for rec in cluster_log:
    ci, cid, kind, canon, count, start_ref, end_ref, meta = rec
    what = f"cluster {ci} {kind}"
    if cid in RO_CIDS or cid == CID["Mint"]:
        continue
    if cid == CID["Double"]:
        for _ in range(count):
            r.i(64)
    elif cid in (CID["Float32x4"], CID["Int32x4"], CID["Float64x2"]):
        raise RuntimeError(f"simd fill not implemented at {what}")
    elif cid == CID["TypeParameter"]:
        for _ in range(count):
            refs(3, what)
            r.i(16)
            r.i(16)
            r.u8()
    elif cid == CID["Type"]:
        for _ in range(count):
            refs(3, what)
            r.u()
    elif cid == CID["FunctionType"]:
        for _ in range(count):
            refs(6, what)
            r.u8()
            r.i(32)
            r.i(16)
    elif cid == CID["RecordType"]:
        for _ in range(count):
            refs(4, what)
            r.u8()
    elif cid == CID["TypeArguments"]:
        for n in meta["lengths"]:
            r.u()
            r.i(32)
            r.u()
            need_ref(r, num_objects, what)
            refs(n, what)
    elif cid == CID["Code"]:
        for _ in range(meta["ncode"]):
            r.u()
            refs(6, what)
        for _ in range(meta["ndef"]):
            refs(6, what)
    elif cid == CID["Function"]:
        for _ in range(count):
            name, _owner, _sig, _data = refs(4, what)
            code_index = r.u()
            r.i(32)
            if name in strings:
                code_names.setdefault(code_index, strings[name])
    elif cid == CID["Closure"]:
        for _ in range(count):
            refs(6, what)
    elif cid == CID["Record"]:
        for n in meta["lengths"]:
            r.u()
            refs(n, what)
    elif cid in (CID["ConstMap"], CID["Map"], CID["ConstSet"], CID["Set"]):
        for _ in range(count):
            refs(5, what)
    elif cid in (CID["Array"], CID["ImmutableArray"]):
        for n in meta["lengths"]:
            got = r.u()
            if got != n:
                raise RuntimeError(f"array length {got} != alloc {n} at {what}")
            need_ref(r, num_objects, what)
            refs(n, what)
    elif cid == CID["GrowableObjectArray"]:
        for _ in range(count):
            refs(3, what)
    elif cid == CID["WeakArray"]:
        for n in meta["lengths"]:
            got = r.u()
            if got != n:
                raise RuntimeError(f"weakarray {got} != {n}")
            refs(n, what)
    elif cid == CID["Class"]:
        def one_class(predefined: bool) -> None:
            refs(13, what)
            class_id = r.i(32)
            r.i(32)
            r.i(32)
            r.i(32)
            r.i(16)
            r.i(16)
            r.i(32)
            if predefined or class_id < (1 << 20):
                r.u()


        for _ in range(meta["npre"]):
            one_class(True)
        for _ in range(count - meta["npre"]):
            one_class(False)
    elif cid == CID["PatchClass"]:
        for _ in range(count):
            refs(2, what)
    elif cid == CID["TypeParameters"]:
        for _ in range(count):
            refs(4, what)
    elif cid == CID["ClosureData"]:
        for _ in range(count):
            refs(2, what)
            r.u()
    elif cid == CID["Field"]:
        for _ in range(count):
            refs(4, what)
            r.i(32)
            need_ref(r, num_objects, what)
    elif cid == CID["Script"]:
        for _ in range(count):
            refs(1, what)
            r.i(32)
    elif cid == CID["Library"]:
        for _ in range(count):
            refs(10, what)
            r.i(32)
            r.i(16)
            r.u8()
            r.u8()
    elif cid == CID["ObjectPool"]:
        length = r.u()
        if length != meta["lengths"][0]:
            raise RuntimeError(f"pool len {length} != {meta['lengths']}")
        for j in range(length):
            bits = r.u8()
            beh = bits >> 5
            typ = bits & 0xF
            if beh == 0:
                if typ == 1:
                    pool_entries.append([j, "ref", need_ref(r, num_objects, what)])
                elif typ == 0:
                    pool_entries.append([j, "imm", r.i(32)])
                elif typ == 2:
                    pool_entries.append([j, "native", None])
                else:
                    raise RuntimeError(f"pool type {typ} bits {bits:#x} at {j}")
            elif beh in (2, 3, 4):
                pool_entries.append([j, "skip", beh])
            else:
                raise RuntimeError(f"pool behavior {beh} bits {bits:#x} at {j}")
        logging.info(f"pool entries={len(pool_entries)} pos={r.p:#x}")
        break  # rest of fill not required for decrypt extraction
    elif cid == CID["Instance"] or cid >= NUM_PREDEFINED or cid in FFI_AS_INSTANCE:
        bitmap = r.u()
        next_w = meta["next_w"]
        offs = list(range(4, next_w * 4, 4))
        for _ in range(count):
            for off in offs:
                if bitmap & (1 << (off // 4)):
                    r.i(32)
                else:
                    need_ref(r, num_objects, what)
    elif meta["lengths"] is not None and cid >= td_base and (cid - td_base) % 4 == 0:
        elem = TD_ELEM[TD[(cid - td_base) // 4]]
        for n in meta["lengths"]:
            got = r.u()
            if got != n:
                raise RuntimeError(f"typed len {got} != {n}")
            r.bytes(n * elem)
    else:
        raise RuntimeError(f"no fill handler for {what} cid {cid} pos {r.p:#x}")

    if r.p > cluster_end:
        raise RuntimeError(f"fill ran past end at {what}")

img = find_instructions_image(data, code_entry_base)
logging.info(f"instructions image IMG={img:#x}")

meta_out = {
    "libapp": str(libapp),
    "app_version": read_manifest_version(find_xapk_root()),
    "snapshot_offset": snap,
    "snapshot_length": snap_length,
    "ro": ro,
    "img": img,
    "code_entry_base": code_entry_base,
    "base_objects": base_objs,
    "num_objects": num_objects,
    "num_clusters": num_clusters,
    "instr_len": instr_len,
    "instr_off": instr_off,
    "dart_version": ver.decode(errors="replace").strip("\x00"),
    "pool_size": len(pool_entries),
    "string_count": len(strings),
    "code_name_count": len(code_names),
}

out.mkdir(parents=True, exist_ok=True)
(out / "meta.json").write_text(json.dumps(meta_out, indent=2) + "\n",
                                   encoding="utf-8")
(out / "strings.json").write_text(
    json.dumps({str(k): v for k, v in strings.items()}, ensure_ascii=False,
               indent=None) + "\n",
    encoding="utf-8",
)
(out / "code_names.json").write_text(
    json.dumps({str(k): v for k, v in code_names.items()}, ensure_ascii=False,
               indent=2) + "\n",
    encoding="utf-8",
)
(out / "mints.json").write_text(
    json.dumps({str(k): v for k, v in mints.items()}) + "\n",
    encoding="utf-8",
)
(out / "pool.json").write_text(json.dumps(pool_entries) + "\n", encoding="utf-8")
logging.info(f"wrote artifacts to {out}")