#!/usr/bin/env python3
"""Spawn Frotabank with frida and hook Unico SDK to capture the signing key."""

import frida
import sys
import time
import signal

PACKAGE = "br.com.frotabank.app"

HOOK_SCRIPT = r"""
'use strict';

function tryHook() {
    Java.perform(function() {
        console.log("[*] Java bridge OK! Installing hooks...");

        // Hook 1: MACSigner(String)
        try {
            var MACSigner = Java.use("com.nimbusds.jose.crypto.MACSigner");
            MACSigner.$init.overload("java.lang.String").implementation = function(secret) {
                console.log("");
                console.log("============================================================");
                console.log("[!!!] SIGNING KEY CAPTURED via MACSigner(String):");
                console.log("[KEY] " + secret);
                console.log("[KEY_LEN] " + secret.length + " chars");
                console.log("============================================================");
                console.log("");
                send({type: "signing_key", source: "MACSigner", key: secret});
                return this.$init(secret);
            };
            console.log("[+] Hooked MACSigner(String)");
        } catch(e) {
            console.log("[-] MACSigner hook: " + e);
        }

        // Hook 2: MACSigner(byte[])
        try {
            var MACSigner = Java.use("com.nimbusds.jose.crypto.MACSigner");
            MACSigner.$init.overload("[B").implementation = function(secret) {
                var hex = "";
                for (var i = 0; i < secret.length; i++) {
                    hex += (secret[i] & 0xFF).toString(16).padStart(2, "0");
                }
                console.log("============================================================");
                console.log("[!!!] SIGNING KEY (bytes) via MACSigner(byte[]):");
                console.log("[KEY_HEX] " + hex);
                console.log("============================================================");
                send({type: "signing_key_bytes", key: hex});
                return this.$init(secret);
            };
            console.log("[+] Hooked MACSigner(byte[])");
        } catch(e) {
            console.log("[-] MACSigner(byte[]) hook: " + e);
        }

        // Hook 3: JWSObject.sign
        try {
            var JWSObject = Java.use("com.nimbusds.jose.JWSObject");
            JWSObject.sign.implementation = function(signer) {
                console.log("[*] JWSObject.sign() called");
                this.sign(signer);
                var jwt = this.serialize();
                console.log("[JWT] length=" + jwt.length);
                var parts = jwt.split(".");
                if (parts.length === 3) {
                    console.log("[JWT] sig=" + parts[2]);
                }
            };
            console.log("[+] Hooked JWSObject.sign");
        } catch(e) {
            console.log("[-] JWSObject.sign hook: " + e);
        }

        console.log("[*] All hooks ready. Navigate to selfie to capture the key.");
    });
}

// Wait for Java to be ready
function waitForJava() {
    if (Java.available) {
        tryHook();
    } else {
        console.log("[*] Waiting for Java...");
        setTimeout(waitForJava, 2000);
    }
}

setTimeout(waitForJava, 3000);
"""

found_key = None

def on_message(message, data):
    global found_key
    if message["type"] == "send":
        payload = message["payload"]
        if isinstance(payload, dict) and "key" in payload:
            found_key = payload["key"]
            print(f"\n{'='*60}")
            print(f"KEY CAPTURED: {found_key}")
            print(f"{'='*60}\n")
            # Save to file
            with open(r"C:\Users\Acer\Documents\Frota\TESTE_SEGURANCA\original_signing_key.txt", "w") as f:
                f.write(found_key)
            print(f"Key saved to TESTE_SEGURANCA/original_signing_key.txt")
    elif message["type"] == "error":
        print(f"[ERROR] {message.get('description', message)}")
    else:
        print(f"[MSG] {message}")

def on_log(level, text):
    print(f"[frida-{level}] {text}")

print(f"[*] Connecting to USB device...")
device = frida.get_usb_device(timeout=10)
print(f"[*] Device: {device.name}")

print(f"[*] Spawning {PACKAGE}...")
pid = device.spawn([PACKAGE])
print(f"[*] Spawned PID: {pid}")

print(f"[*] Attaching to PID {pid}...")
session = device.attach(pid)
session.enable_child_gating()

print(f"[*] Loading hook script...")
script = session.create_script(HOOK_SCRIPT)
script.on("message", on_message)
script.load()

print(f"[*] Resuming app...")
device.resume(pid)

print(f"[*] Waiting for key capture (300s timeout)...")
print(f"[*] Navigate to the selfie screen in the app to trigger the key.")

# Wait up to 300 seconds
for i in range(300):
    time.sleep(1)
    if found_key:
        print(f"\nKey found after {i+1} seconds!")
        break
    if i % 30 == 0 and i > 0:
        print(f"  [{i}s] Still waiting...")

if not found_key:
    print("\nTimeout: key was not captured.")
    print("The selfie flow was not triggered or hooks didn't fire.")

session.detach()
print("Done.")
