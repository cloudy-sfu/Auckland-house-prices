# Analyze Gaspy decrypt constants from XAPK

When Gaspy upgrades, AES key material in `_decode` may change. This folder rebuilds those constants from `libapp.so`.

> [!TIP]
>
> Blutter does not apply. Play Store and XAPK builds ship armeabi-v7a only (ELF32 ARM, Dart 3.x AOT). These scripts parse the isolate snapshot and disassemble the HTTP decrypt function directly.
>
> Do not use JADX for this path. The cipher lives in AOT Dart inside `libapp.so`, not in Java or Kotlin. Do not treat `_decodeAes` (ZIP) as the HTTP cipher.

## Main process

Download the Gaspy XAPK (same version as the live app).

Unzip the XAPK as `gaspy`. Unzip `config.armeabi_v7a.apk` as `gaspy\config.armeabi_v7a`.

Confirm `gaspy\config.armeabi_v7a\lib\armeabi-v7a\libapp.so` exists.

To dump the Dart AOT snapshot, run the following command with arguments.

```powershell
python analyze_gaspy\dump_snapshot.py
```

Arguments:

| Argument | Required? | Description |
| --- | --- | --- |
| `--libapp` | ✓ | Path to `libapp.so` (absolute, or relative to the repo root). |
| `--artifacts` | ✓ | Directory for extracted JSON artifacts. |

To extract decrypt constants, run the following command with arguments.

```powershell
python analyze_gaspy\extract_decrypt_config.py
```

Arguments:

| Argument         | Required? | Description                                                  |
| ---------------- | --------- | ------------------------------------------------------------ |
| `--libapp`       | ✓         | Path to `libapp.so` (absolute, or relative to the repo root). |
| `--artifacts`    | ✓         | Directory for extracted JSON artifacts.                      |
| `--assume-order` |           | Key concatenation order, by default `A_mid_B`.               |

Copy `python_key` from `$artifacts/decrypt_config.json` into `decrypt_blocks_body` in `get_gaspy.py`.

Confirm one chunk decrypts to valid JSON before running the full station loop.

## If `dump_snapshot.py` fails

Re-run the dump. Note the log line `version=...` (Dart snapshot version) and the `RuntimeError` text. Snapshot magic is currently `0xdcdcf5f5` (search `kMagicValue` in [`runtime/vm/snapshot.h`](https://github.com/dart-lang/sdk/blob/main/runtime/vm/snapshot.h)).

Match that version to a [dart-lang/sdk](https://github.com/dart-lang/sdk) tag with the same major.minor as the app’s Flutter or Dart version. Prefer that tag over `main`.

Sync the predefined cid table at the top of `dump_snapshot.py` with that SDK’s [`runtime/vm/class_id.h`](https://github.com/dart-lang/sdk/blob/main/runtime/vm/class_id.h). Expand the `CLASS_LIST*` macros into sequential IDs, then rebuild `CID`, `NAME`, FFI, and TypedData blocks as the file already does.

If parsing still fails during fill or desync, sync the failing cluster’s alloc and fill handlers with that SDK’s [`runtime/vm/app_snapshot.cc`](https://github.com/dart-lang/sdk/blob/main/runtime/vm/app_snapshot.cc). Compare `*DeserializationCluster::ReadAlloc` and `ReadFill` for the cid named in the error. Change only the number and order of `ref`, `u`, `i`, and `u8` reads for that type.

Re-run until `$artifacts` contains `meta.json`, `strings.json`, `code_names.json`, `mints.json`, and `pool.json`. Then continue the main process from extract.

> [!NOTE]
>
> How to read common errors:
>
> - `unhandled cid N`: the cid table is wrong, or a new predefined class was added. Fix `CID` and `NAME` first.
> - `no fill handler for … cid N`: the cid is mapped, but fill is missing. Add or adjust that fill branch.
> - `ran past clustered end`, `fill ran past end`, `ref … out of range`, or `bad ref`: an earlier cluster’s fill field count or order is wrong. Fix the last cluster that was being filled, not only the one that finally crashed.
> - The dump stops after `ObjectPool` on purpose (`break`). Later clusters are not needed for decrypt extraction.

## If `extract_decrypt_config.py` fails or picks the wrong `_decode`

Find candidate `code_index` values in `$artifacts/code_names.json`. Use entries whose values are `_decode` or start with `_decode@`. Each JSON key is a `code_index`.

```powershell
python -c "import json; d=json.load(open(r'analyze_gaspy\artifacts\code_names.json',encoding='utf-8')); print('\n'.join(f'{k}: {v}' for k,v in d.items() if v=='_decode' or v.startswith('_decode@')))"
```

You can also run the disassembler by name. If several functions match, it prints `code_index: name` lines and asks you to pass one:

```powershell
python analyze_gaspy\libapp_disasm.py _decode
```

Disassemble each candidate until the listing loads `csrfValue` (or the CSRF settings string) and two 8-character hex constants:

```powershell
python analyze_gaspy\libapp_disasm.py <code_index>
```

That `<code_index>` is the HTTP `_decode` for this build. Fix extraction logic, or force that index, until `decrypt_config.json` looks right. Then finish the main process from updating `get_gaspy.py`.

> [!TIP]
>
> Use this path after a Dart or Flutter layout change when pool loads around substring or string interpolate shift.
>
> Wrong key or IV yields a random first block and a PKCS7 failure. That indicates a bad key, not a padding-only bug.
>
> A successful extract also writes `code_index` into `$artifacts/decrypt_config.json`. That value is build-specific (for example `17980` on Gaspy 3.30.12) and is not reusable across upgrades.

## Reference

> [!NOTE]
>
> **Cipher shape.** Package `nz.hwem.gaspy`. Cipher binary: `gaspy/config.armeabi_v7a/lib/armeabi-v7a/libapp.so`.
>
> Call chain: `blocks`, then `_sendRequest`, then `_sendRequestBase`, then `sendRequest`, then `_handleResponse`, then `_decode`.
>
> Inside `_decode`:
>
> - Read settings key `csrfValue`, which is the raw `XSRF-TOKEN` cookie (64 hex characters, with no percent-decode).
> - Take `substring(4, 20)` for 16 characters (Smi end `0x28` means 20).
> - Interpolate as `const_a + slice + const_b` (32 ASCII characters). Live order places constants around the slice, not `slice + const_a + const_b`.
> - Encode those bytes as UTF-8 for the AES-256 key. `AES.` forces CBC and PKCS7.
> - Split the body on `:` into IV base64 and ciphertext base64, decrypt, then parse UTF-8 JSON (gunzip first if the plaintext starts with `1f 8b`).
>
> Reference form (re-extract after upgrades):
>
> ```python
> key = ("e875c333" + csrf_token[4:20] + "8f97b3e6").encode("utf-8")
> # AES-256-CBC, PKCS7. Body is base64(IV) + ":" + base64(ciphertext).
> ```
>
> Expected plaintext is JSON with `success` and `data` (station list fields such as `stationKey`, `brandId`, and `price`).
> Login fuel type ids: 1 for 91, 2 for Diesel (D), 3 for 95, 5 for 98.
> Map responses do not refresh cookies. Login `Set-Cookie` is the source of `XSRF-TOKEN` and `SESSION`.
>
> **Closed checks** (do not reopen casually): cookie percent-decode, substring end equal to 40, `fromUtf8` versus a hex key, CBC versus other modes, `sessionValue` as key material (the pool may load it near `_decode`, but the AES key still uses `csrfValue`), map responses replacing cookies, zero IV or ASCII IV, hex of the 32-character key or the full 64-character token, nearby slices of the token or `SESSION`, login `user_key` as key, and `_decodeAes` (ZIP).

Prefer JSON under `$artifacts` (human-diffable). Large dumps are gitignored. Keep `decrypt_config.json` when useful. Do not print or commit passwords or full session tokens.
