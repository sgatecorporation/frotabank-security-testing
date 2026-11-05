// Frida Script: Bypass completo de biometria + liveness
// Carrega com delay para esperar classes serem inicializadas

console.log("[*] Aguardando classes carregarem...");

setTimeout(function() {
    Java.perform(function() {
        console.log("[*] Instalando hooks de biometria...");

        // Hook 1: LivenessResult.isApproved
        try {
            var LivenessResult = Java.use("io.unico.liveness.sdk.core.LivenessResult");
            LivenessResult.isApproved.implementation = function() {
                console.log("[+] LivenessResult.isApproved() -> TRUE");
                return true;
            };
            console.log("[+] HOOKED: LivenessResult.isApproved");
        } catch(e) {
            console.log("[-] LivenessResult: " + e.message);
        }

        // Hook 2: Confidence Score
        try {
            var OzLiveness = Java.use("io.unico.liveness.sdk.core.OzLivenessSDK");
            OzLiveness.getConfidenceScore.implementation = function() {
                console.log("[+] getConfidenceScore() -> 0.99");
                return 0.99;
            };
            console.log("[+] HOOKED: getConfidenceScore");
        } catch(e) {
            console.log("[-] OzLivenessSDK: " + e.message);
        }

        // Hook 3: Dorothy Analysis
        try {
            var Dorothy = Java.use("io.unico.liveness.dorothy.DorothyAnalysis");
            Dorothy.isLivenessDetected.implementation = function() {
                console.log("[+] isLivenessDetected() -> TRUE");
                return true;
            };
            console.log("[+] HOOKED: DorothyAnalysis.isLivenessDetected");
        } catch(e) {
            console.log("[-] DorothyAnalysis: " + e.message);
        }

        // Hook 4: Firebase setValue monitor
        try {
            var DbRef = Java.use("com.google.firebase.database.DatabaseReference");
            DbRef.setValue.overload("java.lang.Object").implementation = function(value) {
                console.log("[*] Firebase setValue: " + value);
                return this.setValue(value);
            };
            console.log("[+] HOOKED: Firebase DatabaseReference.setValue");
        } catch(e) {
            console.log("[-] Firebase: " + e.message);
        }

        // Hook 5: OkHttp interceptor para ver requests
        try {
            var Interceptor = Java.use("okhttp3.Interceptor");
            var RealCall = Java.use("okhttp3.RealCall");
            RealCall.execute.implementation = function() {
                var request = this.request();
                console.log("[*] HTTP: " + request.method() + " " + request.url().toString());
                var response = this.execute();
                console.log("[*] Response: " + response.code());
                return response;
            };
            console.log("[+] HOOKED: OkHttp RealCall.execute");
        } catch(e) {
            console.log("[-] OkHttp: " + e.message);
        }

        // Hook 6: Enumerar classes Unico quando carregarem
        try {
            Java.enumerateLoadedClasses({
                onMatch: function(cls) {
                    if (cls.indexOf("unico") !== -1 && cls.indexOf("liveness") !== -1) {
                        console.log("[*] Classe encontrada: " + cls);
                    }
                },
                onComplete: function() {
                    console.log("[*] Enumeração de classes concluída");
                }
            });
        } catch(e) {}

        console.log("[+] Hooks de biometria instalados!");
    });
}, 3000);
