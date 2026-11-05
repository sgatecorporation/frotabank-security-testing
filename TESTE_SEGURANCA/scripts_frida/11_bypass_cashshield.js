// Bypass CashShield (com.shield.ptr) - usado pelo Frotabank
// Detectado via engenharia reversa de libcashshieldptr-native-lib.so
//
// Classe: com.shield.ptr.internal.NativeUtils
// Metodos de deteccao:
//   isFridaDetected, checkForFridaAgent, getRealTimeFridaValue, checkHooks,
//   isDetectedDevKeys, isDetectedTestKeys, isFoundBusyboxBinary, isFoundMagisk,
//   isFoundSubstrate, isFoundXposed, isFoundXposedPre11, isGboxDetected,
//   isJiaguDetected, isLsplantDetected, isSandHookDetected, isChaosDetected

send("[CS] Script carregado - Java.perform vai aguardar o VM carregar");

Java.perform(function() {
    send("[CS] Java VM disponivel, instalando hooks...");

        // =========================================================
        // 1. BYPASS CashShield NativeUtils (todas as deteccoes)
        // =========================================================
        try {
            var NativeUtils = Java.use("com.shield.ptr.internal.NativeUtils");

            // Metodos que retornam boolean - forcar false (nao detectado)
            var fakeFalse = [
                "isFridaDetected",
                "checkForFridaAgent",
                "checkHooks",
                "isDetectedDevKeys",
                "isDetectedTestKeys",
                "isFoundBusyboxBinary",
                "isFoundMagisk",
                "isFoundSubstrate",
                "isFoundXposed",
                "isFoundXposedPre11",
                "isGboxDetected",
                "isJiaguDetected",
                "isLsplantDetected",
                "isSandHookDetected",
                "isChaosDetected"
            ];

            fakeFalse.forEach(function(methodName) {
                try {
                    var overloads = NativeUtils[methodName].overloads;
                    overloads.forEach(function(ov) {
                        ov.implementation = function() {
                            send("[CS-HOOK] " + methodName + "() -> false (fake)");
                            return false;
                        };
                    });
                    send("[CS] HOOKED: " + methodName);
                } catch(e) {
                    send("[CS] skip " + methodName + ": " + e.message);
                }
            });

            // Metodos que retornam valores int/long - forcar 0
            try {
                NativeUtils.getRealTimeFridaValue.overloads.forEach(function(ov) {
                    ov.implementation = function() {
                        send("[CS-HOOK] getRealTimeFridaValue() -> 0");
                        return 0;
                    };
                });
                send("[CS] HOOKED: getRealTimeFridaValue");
            } catch(e) {
                send("[CS] getRealTimeFridaValue skip: " + e.message);
            }

        } catch(e) {
            send("[CS] NativeUtils nao encontrada ainda (talvez nao carregou): " + e.message);
        }

        // =========================================================
        // 2. BYPASS RootBeer (libtoolChecker.so)
        // =========================================================
        try {
            var RootBeerNative = Java.use("com.scottyab.rootbeer.RootBeerNative");
            RootBeerNative.checkForRoot.implementation = function() {
                send("[RB-HOOK] checkForRoot() -> 0 (not rooted)");
                return 0;
            };
            send("[CS] HOOKED: RootBeer.checkForRoot");
        } catch(e) { send("[CS] RootBeerNative skip: " + e.message); }

        try {
            var RootBeer = Java.use("com.scottyab.rootbeer.RootBeer");
            var methods = ["isRooted", "isRootedWithoutBusyBoxCheck", "detectRootManagementApps",
                           "detectPotentiallyDangerousApps", "detectTestKeys", "checkForBinary",
                           "checkForDangerousProps", "checkForBusyBoxBinary", "checkForSuBinary",
                           "checkSuExists", "checkForRWPaths", "checkForRootNative", "detectRootCloakingApps"];
            methods.forEach(function(m) {
                try {
                    RootBeer[m].overloads.forEach(function(ov) {
                        ov.implementation = function() {
                            send("[RB-HOOK] RootBeer." + m + "() -> false");
                            return false;
                        };
                    });
                } catch(e) {}
            });
            send("[CS] HOOKED: RootBeer java methods");
        } catch(e) { send("[CS] RootBeer java skip: " + e.message); }

        // =========================================================
        // 3. BYPASS deteccoes genericas de root
        // =========================================================
        try {
            var Build = Java.use("android.os.Build");
            Build.TAGS.value = "release-keys";
            send("[CS] Patched: Build.TAGS");
        } catch(e) {}

        try {
            var File = Java.use("java.io.File");
            var exists = File.exists.overload();
            exists.implementation = function() {
                var path = this.getAbsolutePath();
                if (path.indexOf("/su") !== -1 ||
                    path.indexOf("magisk") !== -1 ||
                    path.indexOf("xposed") !== -1 ||
                    path.indexOf("busybox") !== -1 ||
                    path.indexOf("supersu") !== -1 ||
                    path.indexOf("frida") !== -1) {
                    send("[CS-FILE] bloqueado: " + path);
                    return false;
                }
                return exists.call(this);
            };
            send("[CS] HOOKED: File.exists");
        } catch(e) { send("[CS] File.exists skip: " + e.message); }

        // =========================================================
        // 4. BYPASS Unico Liveness (io.unico.internal.isLoggedIn)
        // Detectado via liboz_native.so - Java_io_unico_internal_isLoggedIn_*
        // =========================================================
        try {
            var UnicoNative = Java.use("io.unico.internal.isLoggedIn");

            // isVirtualEnvironmentDetected -> false (nao detecta emulador)
            try {
                UnicoNative.isVirtualEnvironmentDetected.overloads.forEach(function(ov) {
                    ov.implementation = function() {
                        send("[UNICO-HOOK] isVirtualEnvironmentDetected() -> false");
                        return false;
                    };
                });
                send("[CS] HOOKED: Unico.isVirtualEnvironmentDetected");
            } catch(e) { send("[CS] isVirtualEnvironmentDetected skip: " + e.message); }

            // isLicenseValid -> true (sempre valida)
            try {
                UnicoNative.isLicenseValid.overloads.forEach(function(ov) {
                    ov.implementation = function() {
                        send("[UNICO-HOOK] isLicenseValid() -> true");
                        return true;
                    };
                });
                send("[CS] HOOKED: Unico.isLicenseValid");
            } catch(e) { send("[CS] isLicenseValid skip: " + e.message); }

        } catch(e) {
            send("[CS] Unico isLoggedIn skip: " + e.message);
        }

        // =========================================================
        // 5. BYPASS Unico Liveness classes (score, approved)
        // =========================================================
        try {
            var LivenessResult = Java.use("io.unico.liveness.sdk.core.LivenessResult");
            LivenessResult.isApproved.implementation = function() {
                send("[UNICO-HOOK] LivenessResult.isApproved() -> true");
                return true;
            };
            send("[CS] HOOKED: LivenessResult.isApproved");
        } catch(e) { send("[CS] LivenessResult skip: " + e.message); }

        try {
            var OzLiveness = Java.use("io.unico.liveness.sdk.core.OzLivenessSDK");
            OzLiveness.getConfidenceScore.implementation = function() {
                send("[UNICO-HOOK] getConfidenceScore() -> 0.99");
                return 0.99;
            };
            send("[CS] HOOKED: OzLivenessSDK.getConfidenceScore");
        } catch(e) { send("[CS] OzLivenessSDK skip: " + e.message); }

        // =========================================================
        // 6. BYPASS deteccao de emulador via Build props
        // =========================================================
        try {
            var Build = Java.use("android.os.Build");
            Build.FINGERPRINT.value = "google/sdk_gphone64_x86_64/emu64x_arm64:14/UPB4.230623.005/10742024:userdebug/dev-keys".replace("sdk_gphone64_x86_64", "Pixel_6_Pro");
            Build.MODEL.value = "Pixel 6 Pro";
            Build.MANUFACTURER.value = "Google";
            Build.BRAND.value = "google";
            Build.PRODUCT.value = "raven";
            Build.DEVICE.value = "raven";
            Build.HARDWARE.value = "gs101";
            Build.TAGS.value = "release-keys";
            send("[CS] Patched: Build props (device nao parece emulador)");
        } catch(e) { send("[CS] Build props skip: " + e.message); }

        // Esconde propriedades do emulador
        try {
            var SystemProperties = Java.use("android.os.SystemProperties");
            var get1 = SystemProperties.get.overload("java.lang.String");
            get1.implementation = function(key) {
                var val = get1.call(this, key);
                if (key && (key.indexOf("qemu") !== -1 ||
                            key.indexOf("goldfish") !== -1 ||
                            key.indexOf("ranchu") !== -1 ||
                            key.indexOf("ldplayer") !== -1 ||
                            key.indexOf("vbox") !== -1 ||
                            key.indexOf("virtualbox") !== -1)) {
                    send("[CS-PROP] bloqueado: " + key + " = " + val);
                    return "";
                }
                return val;
            };
            send("[CS] HOOKED: SystemProperties.get");
        } catch(e) { send("[CS] SystemProperties skip: " + e.message); }

    send("[CS] === CASHSHIELD + UNICO BYPASS INSTALADO ===");
});

// Hook ClassLoader pra monitorar carregamento das classes shield
Java.perform(function() {
    try {
        var ClassLoader = Java.use("java.lang.ClassLoader");
        var loadClass = ClassLoader.loadClass.overload("java.lang.String", "boolean");
        loadClass.implementation = function(name, resolve) {
            var cls = loadClass.call(this, name, resolve);
            if (name && name.indexOf("com.shield.ptr") !== -1) {
                send("[CS-LOADED] Classe shield carregada: " + name);
            }
            return cls;
        };
    } catch(e) {}
});
