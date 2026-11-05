/**
 * Frida script - Le a signing key diretamente do INSTANCE sem precisar trigger.
 *
 * Usage:
 *   frida -U br.com.frotabank.app -l read_signing_key_instant.js
 *
 * OU spawn:
 *   frida -U -f br.com.frotabank.app -l read_signing_key_instant.js --no-pause
 */

Java.perform(function () {
    console.log("[*] Tentando ler a signing key diretamente...");

    // Approach 1: Read from onSystemClosedCameraTimeoutSession.INSTANCE
    try {
        var cls = Java.use("io.unico.sdk.capture.getHandwritingBoundsOffsetTop$onSystemClosedCameraTimeoutSession");
        var inst = cls.INSTANCE.value;
        if (inst) {
            var parent = Java.cast(inst, Java.use("io.unico.sdk.capture.getHandwritingBoundsOffsetTop"));

            // AcessoBioListener() returns the signing key (field onErrorAcessoBio)
            var key = parent.AcessoBioListener();
            console.log("\n=== SIGNING KEY (onSystemClosedCameraTimeoutSession) ===");
            console.log("KEY: " + key);
            console.log("LEN: " + key.length);
            console.log("HEX: " + toHex(key));
        } else {
            console.log("[-] INSTANCE is null - class not yet initialized");
        }
    } catch (e) {
        console.log("[-] Erro reading onSystemClosedCameraTimeoutSession: " + e);
    }

    // Approach 2: Read from startdefault.INSTANCE
    try {
        var cls2 = Java.use("io.unico.sdk.capture.getHandwritingBoundsOffsetTop$startdefault");
        var inst2 = cls2.INSTANCE.value;
        if (inst2) {
            var parent2 = Java.cast(inst2, Java.use("io.unico.sdk.capture.getHandwritingBoundsOffsetTop"));
            var key2 = parent2.AcessoBioListener();
            console.log("\n=== SIGNING KEY (startdefault) ===");
            console.log("KEY: " + key2);
            console.log("LEN: " + key2.length);
        }
    } catch (e) {
        console.log("[-] Erro reading startdefault: " + e);
    }

    // Approach 3: Read from onRequestPermissionsResult.INSTANCE
    try {
        var cls3 = Java.use("io.unico.sdk.capture.getHandwritingBoundsOffsetTop$onRequestPermissionsResult");
        var inst3 = cls3.INSTANCE.value;
        if (inst3) {
            var parent3 = Java.cast(inst3, Java.use("io.unico.sdk.capture.getHandwritingBoundsOffsetTop"));
            var key3 = parent3.AcessoBioListener();
            console.log("\n=== SIGNING KEY (onRequestPermissionsResult) ===");
            console.log("KEY: " + key3);
            console.log("LEN: " + key3.length);
        }
    } catch (e) {
        console.log("[-] Erro reading onRequestPermissionsResult: " + e);
    }

    // Approach 4: Use reflection to read private field directly
    try {
        var cls4 = Java.use("io.unico.sdk.capture.getHandwritingBoundsOffsetTop$onSystemClosedCameraTimeoutSession");
        var inst4 = cls4.INSTANCE.value;
        if (inst4) {
            var parentCls = Java.use("io.unico.sdk.capture.getHandwritingBoundsOffsetTop").class;

            // Try field name "onErrorAcessoBio" (the private field name from metadata)
            var fields = parentCls.getDeclaredFields();
            console.log("\n=== ALL FIELDS ===");
            for (var i = 0; i < fields.length; i++) {
                var f = fields[i];
                f.setAccessible(true);
                try {
                    var val = f.get(inst4);
                    if (val !== null && typeof val === "object" && val.toString) {
                        val = val.toString();
                    }
                    console.log("  " + f.getName() + " = " + (val !== null ? val : "null"));
                } catch (fe) {
                    console.log("  " + f.getName() + " = [error: " + fe + "]");
                }
            }
        }
    } catch (e) {
        console.log("[-] Reflection approach failed: " + e);
    }

    // Approach 5: Hook the getHandwritingDelegatorCallback to see which variant is used
    try {
        var callback = Java.use("io.unico.sdk.capture.getHandwritingDelegatorCallback");
        callback.onSystemChangedTypeCameraTimeoutFaceInference.implementation = function () {
            var result = this.onSystemChangedTypeCameraTimeoutFaceInference();
            console.log("\n=== SIGNING KEY FROM CALLBACK ===");
            console.log("KEY: " + result);
            console.log("LEN: " + result.length);
            console.log("HEX: " + toHex(result));
            return result;
        };
        console.log("[+] Hook on getHandwritingDelegatorCallback installed");
    } catch (e) {
        console.log("[-] " + e);
    }

    // Approach 6: Hook getHandwritingBoundsOffsetLeft to see the key with newlines stripped
    try {
        var ghbLeft = Java.use("io.unico.sdk.capture.getHandwritingBoundsOffsetLeft");
        ghbLeft.onUserClosedCameraManually.implementation = function () {
            var result = this.onUserClosedCameraManually();
            console.log("\n=== FINAL SIGNING KEY (newlines stripped) ===");
            console.log("KEY: " + result);
            console.log("LEN: " + result.length);
            console.log("HEX: " + toHex(result));
            return result;
        };
        console.log("[+] Hook on getHandwritingBoundsOffsetLeft installed");
    } catch (e) {
        console.log("[-] " + e);
    }

    function toHex(str) {
        var hex = "";
        for (var i = 0; i < str.length; i++) {
            hex += ("0" + str.charCodeAt(i).toString(16)).slice(-2);
        }
        return hex;
    }

    console.log("\n[*] Done. Se a classe ja foi carregada, a key deve aparecer acima.");
    console.log("[*] Se nao, abra o app e faca qualquer acao que inicialize o Unico SDK.");
});
