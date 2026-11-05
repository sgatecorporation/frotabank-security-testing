// Captura requests do Frotabank
// Java.perform aguarda o VM carregar automaticamente

send("[*] Script carregado, Java.perform vai aguardar VM...");

Java.perform(function() {
        send("[*] === CAPTURE REQUESTS ===");

        function shouldLog(url) {
            if (!url) return false;
            var u = url.toString();
            return u.indexOf("/user") !== -1 ||
                   u.indexOf("/phone/confirmation") !== -1 ||
                   u.indexOf("/v2/") !== -1 ||
                   u.indexOf("/device_key") !== -1 ||
                   u.indexOf("/zipcode") !== -1 ||
                   u.indexOf("/person") !== -1 ||
                   u.indexOf("frotabank") !== -1 ||
                   u.indexOf("c03.") !== -1;
        }

        // ============ HOOK OkHttp RealCall.execute ============
        try {
            var RealCall = Java.use("okhttp3.internal.connection.RealCall");
            var Buffer = Java.use("okio.Buffer");

            RealCall.execute.implementation = function() {
                var req = null, url = "", method = "";
                try {
                    req = this.request();
                    url = req.url().toString();
                    method = req.method();
                } catch(e) {
                    return this.execute();
                }

                if (!shouldLog(url)) {
                    return this.execute();
                }

                send("");
                send("================================================================");
                send("[>>>] " + method + " " + url);
                send("================================================================");

                try {
                    send("[HEADERS]");
                    var headers = req.headers();
                    for (var i = 0; i < headers.size(); i++) {
                        send("  " + headers.name(i) + ": " + headers.value(i));
                    }
                } catch(e) { send("[HDR-ERR] " + e); }

                try {
                    var body = req.body();
                    if (body !== null) {
                        var buf = Buffer.$new();
                        body.writeTo(buf);
                        var bodyStr = buf.readUtf8();
                        send("[BODY]");
                        send(bodyStr);
                    } else {
                        send("[BODY] (none)");
                    }
                } catch(e) { send("[BODY-ERR] " + e); }

                var resp;
                try {
                    resp = this.execute();
                } catch(ex) {
                    send("[RESP-ERR] " + ex);
                    throw ex;
                }

                try {
                    send("[RESP] " + resp.code() + " " + resp.message());
                    var respBodyPeek = resp.peekBody(10000);
                    var respStr = respBodyPeek.string();
                    if (respStr && respStr.length > 0) {
                        send("[RESP-BODY]");
                        send(respStr.length > 3000 ? respStr.substring(0, 3000) + "...(trunc)" : respStr);
                    }
                } catch(ex) { send("[RESP-BODY-ERR] " + ex); }

                send("================================================================");
                return resp;
            };
            send("[+] HOOKED: okhttp3.internal.connection.RealCall.execute");
        } catch(e) {
            send("[-] RealCall.execute: " + e.message);
        }

        // Hook enqueue (async)
        try {
            var RealCall2 = Java.use("okhttp3.internal.connection.RealCall");
            RealCall2.enqueue.implementation = function(cb) {
                try {
                    var req = this.request();
                    var url = req.url().toString();
                    if (shouldLog(url)) {
                        send("");
                        send("================================================================");
                        send("[ASYNC >>>] " + req.method() + " " + url);
                        send("================================================================");
                        var Buffer2 = Java.use("okio.Buffer");
                        var headers = req.headers();
                        send("[HEADERS]");
                        for (var i = 0; i < headers.size(); i++) {
                            send("  " + headers.name(i) + ": " + headers.value(i));
                        }
                        var body = req.body();
                        if (body !== null) {
                            var buf = Buffer2.$new();
                            body.writeTo(buf);
                            send("[BODY]");
                            send(buf.readUtf8());
                        } else {
                            send("[BODY] (none)");
                        }
                        send("================================================================");
                    }
                } catch(e) {
                    send("[ASYNC-ERR] " + e);
                }
                return this.enqueue(cb);
            };
            send("[+] HOOKED: RealCall.enqueue");
        } catch(e) {
            send("[-] RealCall.enqueue: " + e.message);
        }

    send("[+] PRONTO. Faca o fluxo no app agora.");
});
