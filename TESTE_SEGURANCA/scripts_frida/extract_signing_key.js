/**
 * Frida script to extract the Unico SDK JWT signing key.
 *
 * The signing key is a STATIC obfuscated string embedded in:
 *   getHandwritingBoundsOffsetTop$onSystemClosedCameraTimeoutSession.INSTANCE.AcessoBioListener()
 *
 * Hook points (any one is enough):
 *   1. isClickable.AcessoBioListener(String, Map)  - str IS the signing key
 *   2. MACSigner constructor                        - the String arg IS the signing key
 *   3. getHandwritingBoundsOffsetTop.AcessoBioListener() - returns the signing key
 *
 * Usage:
 *   frida -U -f br.com.frotabank.app -l extract_signing_key.js --no-pause
 *   (then trigger a selfie capture in the app)
 */

Java.perform(function () {
    console.log("[*] extract_signing_key.js loaded");

    // ============================================================
    // HOOK 1: isClickable.AcessoBioListener(String, Map) - JWT sign
    // ============================================================
    try {
        var isClickable = Java.use("io.unico.sdk.capture.isClickable");
        isClickable.AcessoBioListener.overload("java.lang.String", "java.util.Map").implementation = function (str, map) {
            console.log("\n[!!!] JWT SIGNING KEY CAPTURED via isClickable.AcessoBioListener:");
            console.log("[KEY] " + str);
            console.log("[KEY-HEX] " + stringToHex(str));
            console.log("[KEY-LEN] " + str.length + " chars");
            console.log("[MAP-KEYS] " + map.keySet().toString());
            return this.AcessoBioListener(str, map);
        };
        console.log("[+] Hooked isClickable.AcessoBioListener(String, Map)");
    } catch (e) {
        console.log("[-] Failed to hook isClickable: " + e);
    }

    // ============================================================
    // HOOK 2: MACSigner(String) constructor
    // ============================================================
    try {
        var MACSigner = Java.use("com.nimbusds.jose.crypto.MACSigner");
        MACSigner.$init.overload("java.lang.String").implementation = function (str) {
            console.log("\n[!!!] SIGNING KEY via MACSigner(String):");
            console.log("[KEY] " + str);
            console.log("[KEY-HEX] " + stringToHex(str));
            console.log("[KEY-LEN] " + str.length + " chars");
            return this.$init(str);
        };
        console.log("[+] Hooked MACSigner(String)");
    } catch (e) {
        console.log("[-] Failed to hook MACSigner: " + e);
        try {
            var MACSigner2 = Java.use("com.nimbusds.jose.crypto.MACSigner");
            MACSigner2.$init.overload("[B").implementation = function (bArr) {
                var key = bytesToString(bArr);
                console.log("\n[!!!] SIGNING KEY via MACSigner(byte[]):");
                console.log("[KEY] " + key);
                console.log("[KEY-HEX] " + bytesToHex(bArr));
                console.log("[KEY-LEN] " + bArr.length + " bytes");
                return this.$init(bArr);
            };
            console.log("[+] Hooked MACSigner(byte[])");
        } catch (e2) {
            console.log("[-] Failed to hook MACSigner(byte[]): " + e2);
        }
    }

    // ============================================================
    // HOOK 3: getHandwritingBoundsOffsetTop.AcessoBioListener()
    // ============================================================
    try {
        var ghbTop = Java.use("io.unico.sdk.capture.getHandwritingBoundsOffsetTop");
        ghbTop.AcessoBioListener.implementation = function () {
            var result = this.AcessoBioListener();
            console.log("\n[!!!] SIGNING KEY via getHandwritingBoundsOffsetTop.AcessoBioListener():");
            console.log("[KEY] " + result);
            console.log("[KEY-HEX] " + stringToHex(result));
            return result;
        };
        console.log("[+] Hooked getHandwritingBoundsOffsetTop.AcessoBioListener()");
    } catch (e) {
        console.log("[-] Failed to hook getHandwritingBoundsOffsetTop: " + e);
    }

    // ============================================================
    // HOOK 4: getHandwritingDelegatorCallback switch
    // ============================================================
    try {
        var ghdc = Java.use("io.unico.sdk.capture.getHandwritingDelegatorCallback");
        ghdc.onSystemChangedTypeCameraTimeoutFaceInference.implementation = function () {
            var result = this.onSystemChangedTypeCameraTimeoutFaceInference();
            console.log("\n[!!!] SIGNING KEY via getHandwritingDelegatorCallback:");
            console.log("[KEY] " + result);
            return result;
        };
        console.log("[+] Hooked getHandwritingDelegatorCallback");
    } catch (e) {
        console.log("[-] Failed to hook getHandwritingDelegatorCallback: " + e);
    }

    // ============================================================
    // HOOK 5: Direct read from INSTANCE at load time
    // ============================================================
    try {
        var innerClass = Java.use("io.unico.sdk.capture.getHandwritingBoundsOffsetTop$onSystemClosedCameraTimeoutSession");
        var instance = innerClass.INSTANCE.value;
        if (instance != null) {
            var key = instance.AcessoBioListener();
            console.log("\n[!!!] SIGNING KEY READ DIRECTLY FROM INSTANCE:");
            console.log("[KEY] " + key);
            console.log("[KEY-HEX] " + stringToHex(key));
            console.log("[KEY-LEN] " + key.length + " chars");
        }
    } catch (e) {
        console.log("[-] Failed to read INSTANCE directly: " + e);
    }

    // ============================================================
    // HOOK 6: Also capture the JWS output to correlate
    // ============================================================
    try {
        var JWSObject = Java.use("com.nimbusds.jose.JWSObject");
        JWSObject.serialize.implementation = function () {
            var result = this.serialize();
            console.log("\n[*] JWSObject.serialize() called:");
            console.log("[JWT] " + result.substring(0, 80) + "...");
            console.log("[JWT-LEN] " + result.length);
            return result;
        };
        console.log("[+] Hooked JWSObject.serialize()");
    } catch (e) {
        console.log("[-] Failed to hook JWSObject: " + e);
    }

    // ============================================================
    // HOOK 7: Read the static field directly (alternative approach)
    // ============================================================
    setTimeout(function () {
        Java.perform(function () {
            try {
                var innerClass = Java.use("io.unico.sdk.capture.getHandwritingBoundsOffsetTop$onSystemClosedCameraTimeoutSession");
                var inst = innerClass.INSTANCE.value;
                if (inst) {
                    var parentClass = Java.cast(inst, Java.use("io.unico.sdk.capture.getHandwritingBoundsOffsetTop"));
                    var field1 = parentClass.onSystemClosedCameraTimeoutSession.value;
                    var field2 = parentClass.class.getDeclaredField("onErrorAcessoBio");
                    field2.setAccessible(true);
                    var signingKey = field2.get(parentClass);
                    console.log("\n[!!!] SIGNING KEY FROM FIELD (delayed read):");
                    console.log("[KEY] " + signingKey);
                    console.log("[KEY-HEX] " + stringToHex(String(signingKey)));
                }
            } catch (e) {
                console.log("[-] Delayed field read failed: " + e);
            }
        });
    }, 5000);

    // ============================================================
    // Helper functions
    // ============================================================
    function stringToHex(str) {
        var hex = "";
        for (var i = 0; i < str.length; i++) {
            var code = str.charCodeAt(i);
            hex += ("0" + code.toString(16)).slice(-2);
        }
        return hex;
    }

    function bytesToHex(bArr) {
        var hex = "";
        for (var i = 0; i < bArr.length; i++) {
            var b = bArr[i] & 0xFF;
            hex += ("0" + b.toString(16)).slice(-2);
        }
        return hex;
    }

    function bytesToString(bArr) {
        var str = "";
        for (var i = 0; i < bArr.length; i++) {
            str += String.fromCharCode(bArr[i] & 0xFF);
        }
        return str;
    }

    console.log("\n[*] All hooks installed. Trigger a selfie capture to extract the signing key.");
    console.log("[*] Or wait 5s for direct field read attempt.");
});
