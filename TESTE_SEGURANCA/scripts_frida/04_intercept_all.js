// Intercepta TUDO - SSLSocket, OkHttp ofuscado, Retrofit
Java.perform(function() {
    console.log("[*] === INTERCEPTAÇÃO AGRESSIVA ===");

    // Hook SSLOutputStream.write - captura tudo que vai por HTTPS
    try {
        var SSLSocket = Java.use("com.android.org.conscrypt.ConscryptFileDescriptorSocket$SSLOutputStream");
        SSLSocket.write.overload('[B', 'int', 'int').implementation = function(b, off, len) {
            try {
                var s = Java.use("java.lang.String").$new(b, off, len, "UTF-8");
                if (s.length() < 5000) console.log("[SSL-OUT] " + s.substring(0, Math.min(s.length(), 500)));
            } catch(e) {}
            return this.write(b, off, len);
        };
        console.log("[+] HOOKED: SSL OutputStream");
    } catch(e) {
        console.log("[-] SSLOutputStream: " + e.message);
    }

    // Hook SSLInputStream.read - captura respostas
    try {
        var SSLIn = Java.use("com.android.org.conscrypt.ConscryptFileDescriptorSocket$SSLInputStream");
        SSLIn.read.overload('[B', 'int', 'int').implementation = function(b, off, len) {
            var ret = this.read(b, off, len);
            try {
                if (ret > 0) {
                    var s = Java.use("java.lang.String").$new(b, off, ret, "UTF-8");
                    if (s.length() < 5000) console.log("[SSL-IN] " + s.substring(0, Math.min(s.length(), 500)));
                }
            } catch(e) {}
            return ret;
        };
        console.log("[+] HOOKED: SSL InputStream");
    } catch(e) {
        console.log("[-] SSLInputStream: " + e.message);
    }

    // Hook WebView loadUrl
    try {
        var WebView = Java.use("android.webkit.WebView");
        WebView.loadUrl.overload('java.lang.String').implementation = function(url) {
            console.log("[WEBVIEW] " + url);
            return this.loadUrl(url);
        };
    } catch(e) {}

    console.log("[+] Interceptação ativa!");
});
