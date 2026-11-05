#!/usr/bin/env python3
"""Attach to running Frotabank and try to hook Unico SDK signing key."""
import frida, sys, time

PACKAGE = "br.com.frotabank.app"

SCRIPT = r"""
'use strict';

// Check Java availability with retries
function checkAndHook() {
    if (typeof Java === 'undefined') {
        console.log("[!] Java is undefined. Frida Java bridge NOT available.");
        console.log("[!] This is a known issue with LDPlayer emulator.");
        return false;
    }

    if (!Java.available) {
        console.log("[!] Java defined but not available yet.");
        return false;
    }

    Java.perform(function() {
        console.log("[+] Java bridge WORKS! Hooking MACSigner...");

        try {
            var MACSigner = Java.use("com.nimbusds.jose.crypto.MACSigner");
            MACSigner.$init.overload("java.lang.String").implementation = function(secret) {
                console.log("============================================================");
                console.log("SIGNING KEY: " + secret);
                console.log("============================================================");
                send({type: "key", key: secret});
                return this.$init(secret);
            };
            console.log("[+] MACSigner hooked successfully!");
        } catch(e) {
            console.log("[-] MACSigner hook failed: " + e);
        }
    });
    return true;
}

// Try immediately
if (!checkAndHook()) {
    // Retry after delays
    setTimeout(function() { checkAndHook(); }, 3000);
    setTimeout(function() { checkAndHook(); }, 8000);
    setTimeout(function() {
        if (!checkAndHook()) {
            console.log("[FAIL] Java bridge never became available.");
        }
    }, 15000);
}
"""

found_key = None

def on_message(msg, data):
    global found_key
    if msg["type"] == "send" and isinstance(msg.get("payload"), dict):
        if "key" in msg["payload"]:
            found_key = msg["payload"]["key"]
            print(f"\nKEY FOUND: {found_key}")
            with open(r"C:\Users\Acer\Documents\Frota\TESTE_SEGURANCA\original_signing_key.txt", "w") as f:
                f.write(found_key)
    print(f"[msg] {msg}")

print("[*] Getting USB device...")
sys.stdout.flush()
device = frida.get_usb_device(timeout=10)
print(f"[*] Device: {device.name}")
sys.stdout.flush()

print(f"[*] Attaching to {PACKAGE}...")
sys.stdout.flush()
try:
    session = device.attach(PACKAGE)
    print(f"[*] Attached! Loading script...")
    sys.stdout.flush()
    script = session.create_script(SCRIPT)
    script.on("message", on_message)
    script.load()
    print("[*] Script loaded. Waiting 20s for results...")
    sys.stdout.flush()

    for i in range(20):
        time.sleep(1)
        sys.stdout.flush()
        if found_key:
            break

    session.detach()
except Exception as e:
    print(f"[ERROR] {e}")
    sys.stdout.flush()

print(f"\nResult: key={'FOUND: ' + found_key if found_key else 'NOT FOUND (Java bridge issue)'}")
sys.stdout.flush()
