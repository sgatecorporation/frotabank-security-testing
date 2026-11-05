// Bypass de deteccao de Frida (anti-anti-Frida)
// Hookha strstr/strcmp/fopen/open pra esconder marcas do Frida
// Roda ANTES do app carregar (spawn pausado + resume)

send("[AAF] Carregando bypass de deteccao de Frida...");

// Palavras que anti-tamper procura
var SUSPICIOUS = [
    "frida",
    "gum-js-loop",
    "gmain",
    "gdbus",
    "linjector",
    "gadget",
    "re.frida",
    "frida-agent",
    "frida-server",
    "sysmd",   // nosso binary renomeado (nao detecta ele por nome)
    "27042",
    "27043"
];

function looksSuspicious(str) {
    if (!str) return false;
    var s = str.toLowerCase();
    for (var i = 0; i < SUSPICIOUS.length; i++) {
        if (s.indexOf(SUSPICIOUS[i]) !== -1) return true;
    }
    return false;
}

// ============ Hook strstr (C) ============
try {
    var strstr = Module.findExportByName(null, "strstr");
    if (strstr) {
        Interceptor.attach(strstr, {
            onEnter: function(args) {
                try {
                    var needle = args[1].readCString();
                    this.needle = needle;
                    this.suspicious = looksSuspicious(needle);
                } catch(e) {}
            },
            onLeave: function(retval) {
                if (this.suspicious && !retval.isNull()) {
                    retval.replace(ptr(0));
                }
            }
        });
        send("[AAF] HOOKED: strstr");
    }
} catch(e) { send("[AAF] strstr falhou: " + e); }

// ============ Hook strcmp/strncmp ============
try {
    ["strcmp", "strncmp", "strcasecmp"].forEach(function(fn) {
        var ptrFn = Module.findExportByName(null, fn);
        if (ptrFn) {
            Interceptor.attach(ptrFn, {
                onEnter: function(args) {
                    try {
                        var s1 = args[0].readCString();
                        var s2 = args[1].readCString();
                        this.suspicious = looksSuspicious(s1) || looksSuspicious(s2);
                    } catch(e) {}
                },
                onLeave: function(retval) {
                    if (this.suspicious && retval.toInt32() === 0) {
                        retval.replace(1);  // nao iguais
                    }
                }
            });
            send("[AAF] HOOKED: " + fn);
        }
    });
} catch(e) { send("[AAF] str*cmp falhou: " + e); }

// ============ Hook fopen (C) ============
try {
    var fopen = Module.findExportByName(null, "fopen");
    if (fopen) {
        Interceptor.attach(fopen, {
            onEnter: function(args) {
                try {
                    var path = args[0].readCString();
                    this.path = path;
                    // Redireciona leituras de /proc/self/maps pra arquivo vazio se app tiver detectando
                    if (path && (path.indexOf("/proc/self/maps") !== -1 ||
                                 path.indexOf("/proc/self/status") !== -1 ||
                                 path.indexOf("/proc/self/task") !== -1)) {
                        this.redirect = true;
                    }
                } catch(e) {}
            },
            onLeave: function(retval) {
                // Nao redirecionamos pra nao quebrar legitimo, so logamos
                if (this.redirect) {
                    // Pode-se redirecionar pra /dev/null:
                    // (nao faz por padrao pra nao quebrar app)
                }
            }
        });
        send("[AAF] HOOKED: fopen");
    }
} catch(e) { send("[AAF] fopen falhou: " + e); }

// ============ Hook open (syscall wrapper) ============
try {
    var openPtr = Module.findExportByName(null, "open");
    if (openPtr) {
        Interceptor.attach(openPtr, {
            onEnter: function(args) {
                try {
                    var path = args[0].readCString();
                    if (path && path.indexOf("maps") !== -1) {
                        // app pode estar lendo /proc/<pid>/maps
                    }
                } catch(e) {}
            }
        });
    }
} catch(e) {}

// ============ Hide Frida threads (muda nomes de threads) ============
try {
    var pthread_setname_np = Module.findExportByName(null, "pthread_setname_np");
    // Nao bloqueia o setname, so loga pra debug
} catch(e) {}

// ============ Hook File.list (Java) - usado pra ler /proc ============
Java.perform(function() {
    try {
        var File = Java.use("java.io.File");
        var FileCtor = File.$init.overload("java.lang.String");
        FileCtor.implementation = function(path) {
            if (path && looksSuspicious(path)) {
                send("[AAF-FILE] bloqueado: " + path);
                return FileCtor.call(this, "/does/not/exist/" + Math.random());
            }
            return FileCtor.call(this, path);
        };
        send("[AAF] HOOKED: java.io.File()");
    } catch(e) { send("[AAF] File hook falhou: " + e); }

    // ============ Hook Runtime.exec - usado pra 'ps' / 'netstat' ============
    try {
        var Runtime = Java.use("java.lang.Runtime");
        var exec1 = Runtime.exec.overload("java.lang.String");
        exec1.implementation = function(cmd) {
            if (cmd && (cmd.indexOf("frida") !== -1 || cmd.indexOf("27042") !== -1 ||
                        cmd.indexOf("netstat") !== -1 || cmd.indexOf("ps -A") !== -1)) {
                send("[AAF-EXEC] bloqueado: " + cmd);
                return exec1.call(this, "echo");
            }
            return exec1.call(this, cmd);
        };
        send("[AAF] HOOKED: Runtime.exec(String)");
    } catch(e) { send("[AAF] Runtime.exec falhou: " + e); }
});

send("[AAF] === BYPASS INSTALADO ===");
