// Combined bypass CashShield + Unico + Capture requests
// Expoe funcoes via rpc.exports pra serem chamadas DEPOIS do resume

function doInstall() {
    Java.perform(function() {
        send("[*] === BYPASS + CAPTURE INSTALANDO ===");

        // =========================================================
        // 1. CashShield (com.shield.ptr.internal.NativeUtils)
        // =========================================================
        try {
            var NativeUtils = Java.use("com.shield.ptr.internal.NativeUtils");
            var fakeFalse = [
                "isFridaDetected", "checkForFridaAgent", "checkHooks",
                "isDetectedDevKeys", "isDetectedTestKeys", "isFoundBusyboxBinary",
                "isFoundMagisk", "isFoundSubstrate", "isFoundXposed",
                "isFoundXposedPre11", "isGboxDetected", "isJiaguDetected",
                "isLsplantDetected", "isSandHookDetected", "isChaosDetected"
            ];
            fakeFalse.forEach(function(m) {
                try {
                    NativeUtils[m].overloads.forEach(function(ov) {
                        ov.implementation = function() { return false; };
                    });
                    send("[CS] " + m);
                } catch(e) {}
            });
            try {
                NativeUtils.getRealTimeFridaValue.overloads.forEach(function(ov) {
                    ov.implementation = function() { return 0; };
                });
                send("[CS] getRealTimeFridaValue");
            } catch(e) {}
        } catch(e) { send("[CS] NativeUtils skip: " + e.message); }

        // =========================================================
        // 2. RootBeer
        // =========================================================
        try {
            var RBN = Java.use("com.scottyab.rootbeer.RootBeerNative");
            RBN.checkForRoot.implementation = function() { return 0; };
            send("[CS] RootBeerNative.checkForRoot");
        } catch(e) {}
        try {
            var RB = Java.use("com.scottyab.rootbeer.RootBeer");
            ["isRooted", "isRootedWithoutBusyBoxCheck", "detectRootManagementApps",
             "detectPotentiallyDangerousApps", "detectTestKeys", "checkForBinary",
             "checkForDangerousProps", "checkForBusyBoxBinary", "checkForSuBinary",
             "checkSuExists", "checkForRWPaths", "checkForRootNative", "detectRootCloakingApps"
            ].forEach(function(m) {
                try {
                    RB[m].overloads.forEach(function(ov) {
                        ov.implementation = function() { return false; };
                    });
                } catch(e) {}
            });
            send("[CS] RootBeer java methods");
        } catch(e) {}

        // =========================================================
        // 3. Unico isLoggedIn (deteccao virtual env + licenca)
        // =========================================================
        try {
            var U = Java.use("io.unico.internal.isLoggedIn");
            try {
                U.isVirtualEnvironmentDetected.overloads.forEach(function(ov) {
                    ov.implementation = function() { return false; };
                });
                send("[UNICO] isVirtualEnvironmentDetected -> false");
            } catch(e) {}
            try {
                U.isLicenseValid.overloads.forEach(function(ov) {
                    ov.implementation = function() { return true; };
                });
                send("[UNICO] isLicenseValid -> true");
            } catch(e) {}
        } catch(e) { send("[UNICO] isLoggedIn skip: " + e.message); }

        // =========================================================
        // 4. Build props (device nao parece emulador)
        // =========================================================
        try {
            var Build = Java.use("android.os.Build");
            Build.MODEL.value = "Pixel 6 Pro";
            Build.MANUFACTURER.value = "Google";
            Build.BRAND.value = "google";
            Build.PRODUCT.value = "raven";
            Build.DEVICE.value = "raven";
            Build.HARDWARE.value = "gs101";
            Build.TAGS.value = "release-keys";
            send("[CS] Build props = Pixel 6 Pro");
        } catch(e) { send("[CS] Build skip: " + e.message); }

        // SystemProperties hide emulator
        try {
            var SP = Java.use("android.os.SystemProperties");
            SP.get.overload("java.lang.String").implementation = function(key) {
                if (key && (key.indexOf("qemu") !== -1 || key.indexOf("goldfish") !== -1 ||
                            key.indexOf("ranchu") !== -1 || key.indexOf("ldplayer") !== -1 ||
                            key.indexOf("vbox") !== -1)) {
                    return "";
                }
                return this.get(key);
            };
            send("[CS] SystemProperties.get filtrado");
        } catch(e) {}

        // =========================================================
        // 5. CAPTURE REQUESTS (OkHttp RealCall)
        // =========================================================
        function shouldLog(url) {
            if (!url) return false;
            var u = url.toString();
            return u.indexOf("frotabank") !== -1 || u.indexOf("c03.") !== -1;
        }

        try {
            var RealCall = Java.use("okhttp3.internal.connection.RealCall");
            var Buffer = Java.use("okio.Buffer");

            RealCall.execute.implementation = function() {
                var req, url, method;
                try {
                    req = this.request();
                    url = req.url().toString();
                    method = req.method();
                } catch(e) { return this.execute(); }

                if (!shouldLog(url)) return this.execute();

                send("");
                send("================================================================");
                send("[>>>] " + method + " " + url);
                try {
                    var headers = req.headers();
                    send("[HEADERS]");
                    for (var i = 0; i < headers.size(); i++) {
                        send("  " + headers.name(i) + ": " + headers.value(i));
                    }
                } catch(e) {}
                try {
                    var body = req.body();
                    if (body !== null) {
                        var buf = Buffer.$new();
                        body.writeTo(buf);
                        send("[BODY]");
                        send(buf.readUtf8());
                    }
                } catch(e) {}

                var resp;
                try { resp = this.execute(); }
                catch(ex) { send("[RESP-ERR] " + ex); throw ex; }

                try {
                    send("[RESP] " + resp.code() + " " + resp.message());
                    var peek = resp.peekBody(10000);
                    var rs = peek.string();
                    if (rs && rs.length > 0) {
                        send("[RESP-BODY]");
                        send(rs.length > 3000 ? rs.substring(0,3000) + "...(trunc)" : rs);
                    }
                } catch(e) {}
                send("================================================================");
                return resp;
            };
            send("[CAP] RealCall.execute hooked");

            RealCall.enqueue.implementation = function(cb) {
                try {
                    var req = this.request();
                    var url = req.url().toString();
                    if (shouldLog(url)) {
                        send("");
                        send("[ASYNC >>>] " + req.method() + " " + url);
                        var headers = req.headers();
                        for (var i = 0; i < headers.size(); i++) {
                            send("  HDR " + headers.name(i) + ": " + headers.value(i));
                        }
                        var body = req.body();
                        if (body !== null) {
                            var buf = Buffer.$new();
                            body.writeTo(buf);
                            send("[BODY] " + buf.readUtf8());
                        }
                    }
                } catch(e) {}
                return this.enqueue(cb);
            };
            send("[CAP] RealCall.enqueue hooked");
        } catch(e) {
            send("[CAP] OkHttp skip: " + e.message);
        }

        send("[*] === INSTALADO ===");
    });
}

// RPC - sera chamado APOS o resume
rpc.exports = {
    install: function() {
        doInstall();
        return "installed";
    }
};

send("[*] Script carregado. Aguardando RPC install() apos resume...");
