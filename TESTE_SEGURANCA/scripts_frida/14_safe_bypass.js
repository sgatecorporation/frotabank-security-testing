// Safe bypass - APENAS hooks que nao quebram o ART
// Hook so strstr/strcmp pra esconder strings do Frida.
// NAO redireciona fopen/open (quebra o Android Runtime)

send("[*] Safe bypass carregando...");

var SUSPICIOUS = ["frida", "gum-js-loop", "gmain", "gdbus", "gadget",
                  "re.frida", "frida-agent", "sysmd", "27042", "libfrida"];

function looksSuspicious(ptr) {
    try {
        var s = ptr.readCString();
        if (!s) return false;
        var lower = s.toLowerCase();
        for (var i = 0; i < SUSPICIOUS.length; i++) {
            if (lower.indexOf(SUSPICIOUS[i]) !== -1) return true;
        }
    } catch(e) {}
    return false;
}

// Hook strstr
try {
    var strstr = Module.findGlobalExportByName("strstr");
    if (strstr) {
        Interceptor.attach(strstr, {
            onEnter: function(args) { this.suspicious = looksSuspicious(args[1]); },
            onLeave: function(retval) {
                if (this.suspicious && !retval.isNull()) retval.replace(ptr(0));
            }
        });
        send("[NB] HOOKED: strstr");
    }
} catch(e) { send("[NB] strstr err: " + e); }

// Hook strcmp family
["strcmp", "strncmp", "strcasecmp", "strncasecmp"].forEach(function(fn) {
    try {
        var p = Module.findGlobalExportByName(fn);
        if (p) {
            Interceptor.attach(p, {
                onEnter: function(args) {
                    this.suspicious = looksSuspicious(args[0]) || looksSuspicious(args[1]);
                },
                onLeave: function(retval) {
                    if (this.suspicious && retval.toInt32() === 0) retval.replace(1);
                }
            });
            send("[NB] HOOKED: " + fn);
        }
    } catch(e) {}
});

// Hook pthread_setname_np - esconde threads Frida
try {
    var setname = Module.findGlobalExportByName("pthread_setname_np");
    if (setname) {
        Interceptor.attach(setname, {
            onEnter: function(args) {
                try {
                    var name = args[1].readCString();
                    if (name && (name.indexOf("gum") !== -1 || name.indexOf("frida") !== -1)) {
                        var fake = Memory.allocUtf8String("Binder:" + Math.floor(Math.random()*1000));
                        this.fake = fake;  // keep ref
                        args[1] = fake;
                    }
                } catch(e) {}
            }
        });
        send("[NB] HOOKED: pthread_setname_np");
    }
} catch(e) {}

send("[NB] === SAFE NATIVE BYPASS INSTALADO ===");

// ============ Java hooks via auto-polling ============
function doJavaInstall() {
    Java.perform(function() {
        send("[JV] Java OK, instalando hooks...");

        // CashShield NativeUtils
        try {
            var NU = Java.use("com.shield.ptr.internal.NativeUtils");
            ["isFridaDetected","checkForFridaAgent","checkHooks","isDetectedDevKeys",
             "isDetectedTestKeys","isFoundBusyboxBinary","isFoundMagisk","isFoundSubstrate",
             "isFoundXposed","isFoundXposedPre11","isGboxDetected","isJiaguDetected",
             "isLsplantDetected","isSandHookDetected","isChaosDetected"].forEach(function(m) {
                try {
                    NU[m].overloads.forEach(function(ov) {
                        ov.implementation = function() { return false; };
                    });
                    send("[JV-CS] " + m);
                } catch(e) {}
            });
            try { NU.getRealTimeFridaValue.overloads.forEach(function(ov) {
                ov.implementation = function() { return 0; };
            }); send("[JV-CS] getRealTimeFridaValue"); } catch(e) {}
        } catch(e) { send("[JV] NativeUtils skip: " + e.message); }

        // Unico
        try {
            var U = Java.use("io.unico.internal.isLoggedIn");
            try { U.isVirtualEnvironmentDetected.overloads.forEach(function(ov) {
                ov.implementation = function() { return false; };
            }); send("[JV] Unico.isVirtualEnvironmentDetected"); } catch(e) {}
            try { U.isLicenseValid.overloads.forEach(function(ov) {
                ov.implementation = function() { return true; };
            }); send("[JV] Unico.isLicenseValid"); } catch(e) {}
        } catch(e) { send("[JV] Unico skip: " + e.message); }

        // RootBeer
        try {
            var RBN = Java.use("com.scottyab.rootbeer.RootBeerNative");
            RBN.checkForRoot.implementation = function() { return 0; };
            send("[JV] RootBeerNative");
        } catch(e) {}

        // Build props
        try {
            var Build = Java.use("android.os.Build");
            Build.MODEL.value = "Pixel 6 Pro";
            Build.BRAND.value = "google";
            Build.TAGS.value = "release-keys";
            send("[JV] Build props");
        } catch(e) {}

        // CAPTURE requests
        function shouldLog(url) {
            if (!url) return false;
            var u = url.toString();
            return u.indexOf("frotabank") !== -1 || u.indexOf("c03.") !== -1;
        }
        try {
            var RC = Java.use("okhttp3.internal.connection.RealCall");
            var Buffer = Java.use("okio.Buffer");
            RC.execute.implementation = function() {
                var req, url, method;
                try { req = this.request(); url = req.url().toString(); method = req.method(); }
                catch(e) { return this.execute(); }
                if (!shouldLog(url)) return this.execute();
                send(""); send("================================================================");
                send("[>>>] " + method + " " + url);
                try {
                    var h = req.headers();
                    send("[HEADERS]");
                    for (var i = 0; i < h.size(); i++) send("  " + h.name(i) + ": " + h.value(i));
                } catch(e) {}
                try {
                    var body = req.body();
                    if (body !== null) {
                        var buf = Buffer.$new(); body.writeTo(buf);
                        send("[BODY]"); send(buf.readUtf8());
                    }
                } catch(e) {}
                var resp;
                try { resp = this.execute(); } catch(ex) { send("[RESP-ERR] " + ex); throw ex; }
                try {
                    send("[RESP] " + resp.code() + " " + resp.message());
                    var rs = resp.peekBody(10000).string();
                    if (rs && rs.length > 0) {
                        send("[RESP-BODY]"); send(rs.length > 3000 ? rs.substring(0,3000) + "...(trunc)" : rs);
                    }
                } catch(e) {}
                send("================================================================");
                return resp;
            };
            send("[JV] OkHttp RealCall.execute");

            RC.enqueue.implementation = function(cb) {
                try {
                    var req = this.request();
                    var url = req.url().toString();
                    if (shouldLog(url)) {
                        send(""); send("[ASYNC] " + req.method() + " " + url);
                        var h = req.headers();
                        for (var i = 0; i < h.size(); i++) send("  HDR " + h.name(i) + ": " + h.value(i));
                        var body = req.body();
                        if (body !== null) {
                            var buf = Buffer.$new(); body.writeTo(buf);
                            send("[BODY] " + buf.readUtf8());
                        }
                    }
                } catch(e) {}
                return this.enqueue(cb);
            };
            send("[JV] OkHttp RealCall.enqueue");
        } catch(e) { send("[JV] OkHttp skip: " + e.message); }

        send("[JV] === JAVA HOOKS INSTALADOS ===");
    });
}

// Polling: tenta instalar Java hooks ate conseguir
var javaInstalled = false;
function tryAutoInstall(attempts) {
    if (javaInstalled) return;
    attempts = attempts || 0;
    if (attempts > 600) { send("[JV-AUTO] Timeout 60s"); return; }
    try {
        if (typeof Java !== "undefined" && Java.available) {
            javaInstalled = true;
            send("[JV-AUTO] Java OK em " + (attempts * 100) + "ms");
            doJavaInstall();
            return;
        }
    } catch(e) {}
    setTimeout(function() { tryAutoInstall(attempts + 1); }, 100);
}
setTimeout(tryAutoInstall, 100);

rpc.exports = {
    installjava: function() { doJavaInstall(); return "ok"; }
};
