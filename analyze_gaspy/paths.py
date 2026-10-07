"""Resolve libapp.so and XAPK layout paths."""
from __future__ import annotations

from pathlib import Path

# Flutter AOT snapshot magic (little-endian in file).
SNAPSHOT_MAGIC = 0xDCDCF5F5

LIBAPP_REL = Path("config.armeabi_v7a/lib/armeabi-v7a/libapp.so")
LIBAPP_APK_REL = Path("lib/armeabi-v7a/libapp.so")


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def find_xapk_root(start: Path | None = None) -> Path | None:
    """Find an extracted Gaspy XAPK directory (contains config.armeabi_v7a or nz.hwem.gaspy)."""
    start = start or repo_root()
    candidates = [
        start / "gaspy",
        start / "analyze_gaspy" / "xapk",
        start,
    ]
    for base in candidates:
        if not base.is_dir():
            continue
        if (base / LIBAPP_REL).is_file():
            return base
        if (base / "nz.hwem.gaspy" / LIBAPP_APK_REL).is_file():
            return base / "nz.hwem.gaspy"
        for child in base.iterdir():
            if child.is_dir() and (child / LIBAPP_REL).is_file():
                return child
    return None


def find_libapp(explicit: Path | None = None, xapk_root: Path | None = None) -> Path:
    if explicit is not None:
        p = Path(explicit)
        if not p.is_file():
            raise FileNotFoundError(p)
        return p.resolve()
    root = xapk_root or find_xapk_root()
    if root is None:
        raise FileNotFoundError(
            "libapp.so not found. Unzip the XAPK under gaspy/ or pass --libapp."
        )
    for rel in (LIBAPP_REL, LIBAPP_APK_REL):
        candidate = root / rel
        if candidate.is_file():
            return candidate.resolve()
    raise FileNotFoundError(f"No libapp.so under {root}")


def find_snapshot_offset(data: bytes, hint: int | None = None) -> tuple[int, int]:
    """
    Return (snapshot_offset, cluster_length) for the Dart AOT isolate snapshot.
    cluster_length = stored_length + 4 (includes length word).
    """
    if hint is not None and _valid_snapshot(data, hint):
        stored = int.from_bytes(data[hint + 4 : hint + 8], "little")
        return hint, stored + 4

    for off in range(0, len(data) - 12, 4):
        if int.from_bytes(data[off : off + 4], "little") != SNAPSHOT_MAGIC:
            continue
        if _valid_snapshot(data, off):
            stored = int.from_bytes(data[off + 4 : off + 8], "little")
            return off, stored + 4

    if hint is not None:
        raise ValueError(f"Invalid snapshot at hint {hint:#x}")
    raise ValueError("Dart AOT snapshot magic not found in libapp.so")


def _valid_snapshot(data: bytes, off: int) -> bool:
    if off + 8 > len(data):
        return False
    if int.from_bytes(data[off : off + 4], "little") != SNAPSHOT_MAGIC:
        return False
    stored = int.from_bytes(data[off + 4 : off + 8], "little")
    length = stored + 4
    if length < 0x10000 or off + length > len(data):
        return False
    return True


def find_rx_load(data: bytes) -> tuple[int, int]:
    """Return (file_offset, file_size) of the executable PT_LOAD segment."""
    import struct

    if data[:4] != b"\x7fELF":
        raise ValueError("libapp.so is not ELF")
    e_phoff = struct.unpack_from("<I", data, 28)[0]
    e_phentsize, e_phnum = struct.unpack_from("<HH", data, 42)
    for i in range(e_phnum):
        off = e_phoff + i * e_phentsize
        p_type, p_offset, _v, _p, p_filesz, _m, p_flags, _a = struct.unpack_from(
            "<IIIIIIII", data, off
        )
        if p_type == 1 and (p_flags & 1):  # PT_LOAD + PF_X
            return p_offset, p_filesz
    raise ValueError("No executable PT_LOAD in libapp.so")


def find_instructions_image(data: bytes, code_entry_base: int, sample: int = 64) -> int:
    """
    Locate Dart AOT instructions image (IMG) inside the RX segment.

    Code entry PCs are relative to IMG. Score candidate alignments by how often
    IMG+pc starts with a typical Dart ARM prologue (push {fp, lr}).
    """
    import struct

    rx_off, rx_size = find_rx_load(data)
    pcs = []
    for idx in range(0, sample):
        try:
            pc = struct.unpack_from("<I", data, code_entry_base + 16 + idx * 8)[0]
        except struct.error:
            break
        if pc and pc < rx_size:
            pcs.append(pc)
    if not pcs:
        raise ValueError("No usable code entry PCs")

    # push {fp, lr} → e92d4800 (and close variants with extra regs)
    def is_prologue(addr: int) -> bool:
        if addr + 4 > len(data):
            return False
        w = struct.unpack_from("<I", data, addr)[0]
        return (w & 0xFFFF0000) == 0xE92D0000 and (w & 0x4800) == 0x4800

    best_img, best_score = None, -1
    # IMG is inside RX; step 16 keeps ARM alignment. Limit search window.
    for delta in range(0, min(rx_size, 0x20000), 16):
        img = rx_off + delta
        score = 0
        for pc in pcs:
            at = img + pc
            if at + 4 > rx_off + rx_size:
                continue
            if is_prologue(at):
                score += 1
        if score > best_score:
            best_score = score
            best_img = img
    if best_img is None or best_score < max(3, len(pcs) // 10):
        raise ValueError(
            f"Could not locate instructions image (best_score={best_score}/{len(pcs)})"
        )
    return best_img


def read_manifest_version(xapk_root: Path | None) -> str | None:
    if xapk_root is None:
        xapk_root = find_xapk_root()
    if xapk_root is None:
        return None
    manifest = xapk_root / "manifest.json"
    if not manifest.is_file():
        # XAPK root may be gaspy/; manifest often sits there while libapp is nested.
        parent = xapk_root.parent / "manifest.json"
        if parent.is_file():
            manifest = parent
        else:
            return None
    import json

    try:
        meta = json.loads(manifest.read_text(encoding="utf-8"))
        return meta.get("version_name") or meta.get("version")
    except (OSError, json.JSONDecodeError, TypeError):
        return None
