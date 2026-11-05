import subprocess, hashlib
cert = open(r"C:\Users\Acer\.mitmproxy\mitmproxy-ca-cert.cer", "rb").read()
from cryptography import x509
c = x509.load_pem_x509_certificate(cert)
h = hashlib.md5(c.subject.public_bytes()).hexdigest()
# Android uses subject_hash_old which is based on MD5 of DER-encoded subject
import struct
hash_val = struct.unpack("<I", bytes.fromhex(h[:8]))[0]
name = f"{hash_val:08x}"
print(f"Hash: {name}")
# Copy cert with correct name
with open(rf"C:\Users\Acer\.mitmproxy\{name}.0", "wb") as f:
    f.write(cert)
print(f"Saved as: C:\\Users\\Acer\\.mitmproxy\\{name}.0")
