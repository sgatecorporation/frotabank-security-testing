'use strict';

function tryHook() {
    Java.perform(function() {
        console.log("[*] Java bridge OK! Installing hooks...");

        // Hook 1: MACSigner(String) - captures the raw signing key
        try {
            var MACSigner = Java.use("com.nimbusds.jose.crypto.MACSigner");
            MACSigner.$init.overload("java.lang.String").implementation = function(secret) {
                console.log("");
                console.log("============================================================");
                console.log("[!!!] SIGNING KEY CAPTURED via MACSigner(String):");
                console.log("[KEY] " + secret);
                console.log("[KEY_HEX] " + strToHex(secret));
                console.log("[KEY_LEN] " + secret.length + " chars");
                console.log("============================================================");
                console.log("");
                send({type: "signing_key", source: "MACSigner", key: secret});
                return this.$init(secret);
            };
            console.log("[+] Hooked MACSigner(String) constructor");
        } catch(e) {
            console.log("[-] MACSigner hook failed: " + e);
        }

        // Hook 2: MACSigner(byte[]) - alternative constructor
        try {
            var MACSigner = Java.use("com.nimbusds.jose.crypto.MACSigner");
            MACSigner.$init.overload("[B").implementation = function(secret) {
                var hex = bytesToHex(secret);
                console.log("");
                console.log("============================================================");
                console.log("[!!!] SIGNING KEY CAPTURED via MACSigner(byte[]):");
                console.log("[KEY_HEX] " + hex);
                console.log("[KEY_LEN] " + secret.length + " bytes");
                console.log("============================================================");
                send({type: "signing_key", source: "MACSigner_bytes", key: hex});
                return this.$init(secret);
            };
            console.log("[+] Hooked MACSigner(byte[]) constructor");
        } catch(e) {
            console.log("[-] MACSigner(byte[]) hook: " + e);
        }

        // Hook 3: JWSObject.sign - confirm JWT signing
        try {
            var JWSObject = Java.use("com.nimbusds.jose.JWSObject");
            JWSObject.sign.implementation = function(signer) {
                console.log("[*] JWSObject.sign() called");
                this.sign(signer);
                var jwt = this.serialize();
                console.log("[JWT] length=" + jwt.length);
                console.log("[JWT] header.payload (first 120)=" + jwt.substring(0, 120));
                var parts = jwt.split(".");
                console.log("[JWT] sig=" + parts[2].substring(0, 60) + "...");
                send({type: "jwt", jwt_preview: jwt.substring(0, 200)});
            };
            console.log("[+] Hooked JWSObject.sign");
        } catch(e) {
            console.log("[-] JWSObject.sign hook: " + e);
        }

        // Hook 4: Key derivation class fields
        try {
            var keyClass = Java.use("io.unico.sdk.capture.getHandwritingBoundsOffsetTop");
            console.log("[+] Loaded getHandwritingBoundsOffsetTop class");
            // Try to read the onErrorAcessoBio field (the signing key)
            var fields = keyClass.class.getDeclaredFields();
            for (var i = 0; i < fields.length; i++) {
                console.log("[FIELD] " + fields[i].getName() + " : " + fields[i].getType().getName());
            }
        } catch(e) {
            console.log("[-] Key derivation class: " + e);
        }

        console.log("[*] All hooks ready. Navigate to selfie screen to trigger.");
    });
}

function strToHex(s) {
    var h = "";
    for (var i = 0; i < s.length; i++) {
        h += s.charCodeAt(i).toString(16).padStart(2, "0");
    }
    return h;
}

function bytesToHex(arr) {
    var h = "";
    for (var i = 0; i < arr.length; i++) {
        h += (arr[i] & 0xFF).toString(16).padStart(2, "0");
    }
    return h;
}

// Try immediately, and also schedule retry in case Java isn't ready yet
if (Java.available) {
    tryHook();
} else {
    console.log("[*] Java not available yet, waiting...");
    setTimeout(function() {
        if (Java.available) {
            tryHook();
        } else {
            console.log("[!] Java still not available after 5s. Retrying in 10s...");
            setTimeout(function() {
                if (Java.available) {
                    tryHook();
                } else {
                    console.log("[!!!] Java bridge NEVER became available.");
                    console.log("[!!!] Try: frida -U -f br.com.frotabank.app --no-pause -l hook_unico_key.js");
                }
            }, 10000);
        }
    }, 5000);
}
