// Script de reconhecimento - lista métodos das classes de biometria/liveness
Java.perform(function() {
    console.log("[*] === RECONHECIMENTO DE CLASSES ===");

    var targets = [
        "io.unico.liveness.sdk.core.LivenessResult",
        "io.unico.liveness.sdk.core.OzLivenessSDK",
        "io.unico.liveness.sdk.network.OzForensicsService",
        "io.unico.liveness.sdk.core.OzLivenessSDK$AnalysisRequest"
    ];

    targets.forEach(function(className) {
        try {
            var cls = Java.use(className);
            var methods = cls.class.getDeclaredMethods();
            console.log("\n[CLASS] " + className + " (" + methods.length + " methods):");
            for (var i = 0; i < methods.length; i++) {
                console.log("  " + methods[i].toString());
            }
            var fields = cls.class.getDeclaredFields();
            console.log("  Fields (" + fields.length + "):");
            for (var i = 0; i < fields.length; i++) {
                console.log("  F: " + fields[i].toString());
            }
        } catch(e) {
            console.log("[-] " + className + ": " + e.message);
        }
    });

    // Buscar classes relevantes ao cadastro
    console.log("\n[*] === CLASSES DE CADASTRO/VERIFICACAO ===");
    Java.enumerateLoadedClasses({
        onMatch: function(cls) {
            var l = cls.toLowerCase();
            if ((l.indexOf("biometr") !== -1 || l.indexOf("selfie") !== -1 ||
                 l.indexOf("facetec") !== -1 || l.indexOf("kyc") !== -1 ||
                 l.indexOf("onboard") !== -1 || l.indexOf("cadastro") !== -1 ||
                 l.indexOf("verif") !== -1 || l.indexOf("document") !== -1 ||
                 l.indexOf("ocr") !== -1 || l.indexOf("capture") !== -1) &&
                l.indexOf("android.") === -1 && l.indexOf("androidx.") === -1) {
                console.log("[FOUND] " + cls);
            }
        },
        onComplete: function() {
            console.log("[*] Reconhecimento completo!");
        }
    });
});
