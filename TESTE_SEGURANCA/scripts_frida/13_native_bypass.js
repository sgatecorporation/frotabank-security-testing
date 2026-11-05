// Bypass CashShield em NIVEL NATIVO (antes do Java carregar)
// Hookha strstr, strcmp, fopen pra esconder marcas do Frida.
// Depois instala tambem o Java hooks via RPC.

send("[NB] Native hooks instalando...");

// ============ Palavras suspeitas ============
var SUSPICIOUS = [
    "frida", "gum-js-loop", "gmain", "gdbus", "linjector",
    "gadget", "re.frida", "frida-agent", "frida-server",
    "sysmd", "27042", "27043", "libfrida"
];

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

// ============ Hook strstr ============
try {
    var strstr = Module.findGlobalExportByName("strstr");
    if (strstr) {
        Interceptor.attach(strstr, {
            onEnter: function(args) {
                this.suspicious = looksSuspicious(args[1]);
            },
            onLeave: function(retval) {
                if (this.suspicious && !retval.isNull()) {
                    retval.replace(ptr(0));
                }
            }
        });
        send("[NB] HOOKED: strstr @ " + strstr);
    }
} catch(e) { send("[NB] strstr erro: " + e); }

// ============ Hook strcmp family ============
["strcmp", "strncmp", "strcasecmp", "strncasecmp"].forEach(function(fn) {
    try {
        var p = Module.findGlobalExportByName(fn);
        if (p) {
            Interceptor.attach(p, {
                onEnter: function(args) {
                    this.suspicious = looksSuspicious(args[0]) || looksSuspicious(args[1]);
                },
                onLeave: function(retval) {
                    if (this.suspicious && retval.toInt32() === 0) {
                        retval.replace(1);
                    }
                }
            });
            send("[NB] HOOKED: " + fn);
        }
    } catch(e) {}
});

// ============ Hook fopen (bloqueia leitura de /proc/*/maps etc) ============
try {
    var fopen = Module.findGlobalExportByName("fopen");
    if (fopen) {
        var fopenImpl = new NativeFunction(fopen, "pointer", ["pointer", "pointer"]);
        Interceptor.replace(fopen, new NativeCallback(function(pathPtr, modePtr) {
            try {
                var path = pathPtr.readCString();
                if (path && (path.indexOf("maps") !== -1 ||
                             path.indexOf("status") !== -1 ||
                             path.indexOf("cmdline") !== -1)) {
                    // Redireciona pra /dev/null (vazio)
                    var devnull = Memory.allocUtf8String("/dev/null");
                    return fopenImpl(devnull, modePtr);
                }
            } catch(e) {}
            return fopenImpl(pathPtr, modePtr);
        }, "pointer", ["pointer", "pointer"]));
        send("[NB] HOOKED: fopen (redireciona /proc/*/maps)");
    }
} catch(e) { send("[NB] fopen erro: " + e); }

// ============ Hook open syscall ============
try {
    var openPtr = Module.findGlobalExportByName("open");
    if (openPtr) {
        var openImpl = new NativeFunction(openPtr, "int", ["pointer", "int", "...", "int"]);
        Interceptor.attach(openPtr, {
            onEnter: function(args) {
                try {
                    var path = args[0].readCString();
                    if (path && path.indexOf("/proc/") !== -1 && path.indexOf("maps") !== -1) {
                        // Troca o path pra /dev/null
                        this.devnull = Memory.allocUtf8String("/dev/null");
                        args[0] = this.devnull;
                    }
                } catch(e) {}
            }
        });
        send("[NB] HOOKED: open");
    }
} catch(e) { send("[NB] open erro: " + e); }

// ============ Hook android_dlopen_ext - detecta carga das libs ============
try {
    var dlopen = Module.findGlobalExportByName("android_dlopen_ext") || Module.findGlobalExportByName("dlopen");
    if (dlopen) {
        Interceptor.attach(dlopen, {
            onEnter: function(args) {
                try {
                    this.name = args[0].readCString();
                } catch(e) {}
            },
            onLeave: function(retval) {
                if (this.name && (this.name.indexOf("cashshield") !== -1 ||
                                  this.name.indexOf("toolChecker") !== -1 ||
                                  this.name.indexOf("oz_native") !== -1 ||
                                  this.name.indexOf("iproov") !== -1)) {
                    send("[NB-LIB] carregada: " + this.name);
                }
            }
        });
        send("[NB] HOOKED: dlopen (monitora libs anti-tamper)");
    }
} catch(e) { send("[NB] dlopen erro: " + e); }

// ============ Hide Frida threads via pthread_setname_np ============
try {
    var setname = Module.findGlobalExportByName("pthread_setname_np");
    if (setname) {
        Interceptor.attach(setname, {
            onEnter: function(args) {
                try {
                    var name = args[1].readCString();
                    if (name && (name.indexOf("gum") !== -1 || name.indexOf("frida") !== -1)) {
                        // Troca o nome
                        var fakeName = Memory.allocUtf8String("system_server");
                        args[1] = fakeName;
                    }
                } catch(e) {}
            }
        });
        send("[NB] HOOKED: pthread_setname_np");
    }
} catch(e) {}

send("[NB] === NATIVE BYPASS INSTALADO ===");

// ============ RPC pro Java hooks (chamado depois do resume) ============
function doJavaInstall() {
    Java.perform(function() {
        send("[JV] Java hooks instalando...");

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
                    send("[JV] CS." + m);
                } catch(e) {}
            });
            try { NU.getRealTimeFridaValue.overloads.forEach(function(ov) {
                ov.implementation = function() { return 0; };
            }); send("[JV] CS.getRealTimeFridaValue"); } catch(e) {}
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
            send("[JV] RootBeerNative.checkForRoot");
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
                try { resp = this.execute(); }
                catch(ex) { send("[RESP-ERR] " + ex); throw ex; }
                try {
                    send("[RESP] " + resp.code() + " " + resp.message());
                    var rs = resp.peekBody(10000).string();
                    if (rs && rs.length > 0) {
                        send("[RESP-BODY]");
                        send(rs.length > 3000 ? rs.substring(0,3000) + "...(trunc)" : rs);
                    }
                } catch(e) {}
                send("================================================================");
                return resp;
            };
            send("[JV] OkHttp RealCall hooked");
        } catch(e) { send("[JV] OkHttp skip: " + e.message); }

        send("[JV] === JAVA HOOKS INSTALADOS ===");
    });
}

rpc.exports = {
    installjava: function() {
        doJavaInstall();
        return "ok";
    }
};

// Auto-install em polling - tenta ate Java estar disponivel
var javaInstalled = false;
function tryAutoInstall(attempts) {
    if (javaInstalled) return;
    attempts = attempts || 0;
    if (attempts > 300) {  // 30s de retry
        send("[JV-AUTO] Timeout 30s, desistindo");
        return;
    }
    try {
        if (typeof Java !== "undefined" && Java.available) {
            send("[JV-AUTO] Java detectado em " + (attempts * 100) + "ms, instalando...");
            javaInstalled = true;
            doJavaInstall();
            return;
        }
    } catch(e) {}
    setTimeout(function() { tryAutoInstall(attempts + 1); }, 100);
}
setTimeout(tryAutoInstall, 500);  // comeca 500ms depois
