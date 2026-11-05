// SSL Unpinning + Force trust user certs + React Native network intercept
// Para usar com mitmproxy no emulador

Java.perform(function() {
    console.log("[*] === SSL UNPIN + REACT NATIVE INTERCEPT ===");

    // 1. Bypass SSL Pinning - TrustManager
    try {
        var TrustManagerImpl = Java.use("com.android.org.conscrypt.TrustManagerImpl");
        TrustManagerImpl.verifyChain.implementation = function() {
            console.log("[+] SSL: TrustManagerImpl.verifyChain bypassed");
            return arguments[0];
        };
        console.log("[+] HOOKED: TrustManagerImpl.verifyChain");
    } catch(e) { console.log("[-] TrustManagerImpl: " + e.message); }

    // 2. Bypass X509TrustManager
    try {
        var X509TrustManager = Java.use("javax.net.ssl.X509TrustManager");
        var TrustManager = Java.registerClass({
            name: "com.bypass.TrustManager",
            implements: [X509TrustManager],
            methods: {
                checkClientTrusted: function(chain, authType) {},
                checkServerTrusted: function(chain, authType) {},
                getAcceptedIssuers: function() { return []; }
            }
        });
    } catch(e) { console.log("[-] X509TrustManager register: " + e.message); }

    // 3. Bypass SSLContext.init
    try {
        var SSLContext = Java.use("javax.net.ssl.SSLContext");
        SSLContext.init.overload("[Ljavax.net.ssl.KeyManager;", "[Ljavax.net.ssl.TrustManager;", "java.security.SecureRandom").implementation = function(km, tm, sr) {
            console.log("[+] SSL: SSLContext.init intercepted - using permissive TrustManager");
            this.init(km, null, sr);
        };
        console.log("[+] HOOKED: SSLContext.init");
    } catch(e) { console.log("[-] SSLContext.init: " + e.message); }

    // 4. Bypass OkHttp CertificatePinner (if used)
    try {
        var CertificatePinner = Java.use("okhttp3.CertificatePinner");
        CertificatePinner.check.overload("java.lang.String", "java.util.List").implementation = function(hostname, peerCerts) {
            console.log("[+] SSL: OkHttp CertificatePinner bypassed for " + hostname);
        };
        console.log("[+] HOOKED: OkHttp CertificatePinner");
    } catch(e) { console.log("[-] OkHttp CertPinner: " + e.message); }

    // 5. Bypass NetworkSecurityConfig - trust user certs
    try {
        var NetworkSecurityTrustManager = Java.use("android.security.net.config.NetworkSecurityTrustManager");
        NetworkSecurityTrustManager.checkServerTrusted.overload("[Ljava.security.cert.X509Certificate;", "java.lang.String").implementation = function(certs, authType) {
            console.log("[+] SSL: NetworkSecurityTrustManager bypassed");
        };
        console.log("[+] HOOKED: NetworkSecurityTrustManager");
    } catch(e) { console.log("[-] NetworkSecurityTrustManager: " + e.message); }

    // 6. Bypass conscrypt SSL
    try {
        var Platform = Java.use("com.android.org.conscrypt.Platform");
        Platform.checkServerTrusted.overload("javax.net.ssl.X509TrustManager", "[Ljava.security.cert.X509Certificate;", "java.lang.String", "com.android.org.conscrypt.AbstractConscryptSocket").implementation = function() {
            console.log("[+] SSL: conscrypt Platform.checkServerTrusted bypassed");
            return Java.use("java.util.ArrayList").$new();
        };
        console.log("[+] HOOKED: conscrypt Platform");
    } catch(e) { console.log("[-] conscrypt Platform: " + e.message); }

    // 7. Shield anti-tamper bypass
    try {
        Java.enumerateLoadedClasses({
            onMatch: function(cls) {
                if (cls.indexOf("com.shield") !== -1) {
                    console.log("[SHIELD] Found: " + cls);
                }
            },
            onComplete: function() {}
        });
    } catch(e) {}

    // 8. React Native - Hook fetch/XMLHttpRequest at bridge level
    try {
        var RNNetworking = Java.use("com.facebook.react.modules.network.NetworkingModule");
        var methods = RNNetworking.class.getDeclaredMethods();
        console.log("[RN] NetworkingModule methods: " + methods.length);
        for (var i = 0; i < methods.length; i++) {
            console.log("[RN]   " + methods[i].getName());
        }
    } catch(e) { console.log("[-] RN NetworkingModule: " + e.message); }

    // 9. Hook OkHttpClient builder to disable SSL verification
    try {
        var OkHttpClientBuilder = Java.use("okhttp3.OkHttpClient$Builder");

        // Get SSLSocketFactory that trusts all
        var SSLContextClass = Java.use("javax.net.ssl.SSLContext");
        var TrustManagerFactory = Java.use("javax.net.ssl.TrustManagerFactory");

        OkHttpClientBuilder.build.implementation = function() {
            console.log("[+] OkHttpClient.build() - injecting permissive SSL");
            try {
                var sslCtx = SSLContextClass.getInstance("TLS");
                sslCtx.init(null, null, null);
                this.sslSocketFactory(sslCtx.getSocketFactory());
            } catch(ex) {}
            return this.build();
        };
        console.log("[+] HOOKED: OkHttpClient.Builder.build");
    } catch(e) { console.log("[-] OkHttpClient.Builder: " + e.message); }

    // 10. Monitor all HTTP requests via OkHttp interceptor
    try {
        var Interceptor = Java.use("okhttp3.Interceptor");
        var Chain = Java.use("okhttp3.Interceptor$Chain");
        var Request = Java.use("okhttp3.Request");
        var Response = Java.use("okhttp3.Response");
        var Buffer = Java.use("okio.Buffer");

        // Hook RealCall to see requests
        var RealCall = Java.use("okhttp3.internal.connection.RealCall");
        if (RealCall.execute) {
            RealCall.execute.implementation = function() {
                var req = this.request();
                console.log("[HTTP] " + req.method() + " " + req.url().toString());
                var headers = req.headers();
                for (var i = 0; i < headers.size(); i++) {
                    console.log("[HDR]   " + headers.name(i) + ": " + headers.value(i));
                }
                var body = req.body();
                if (body !== null) {
                    try {
                        var buf = Buffer.$new();
                        body.writeTo(buf);
                        var bodyStr = buf.readUtf8();
                        if (bodyStr.length() < 2000) {
                            console.log("[BODY] " + bodyStr);
                        } else {
                            console.log("[BODY] (truncated) " + bodyStr.substring(0, 500));
                        }
                    } catch(ex) {}
                }
                var resp = this.execute();
                console.log("[RESP] " + resp.code());
                return resp;
            };
            console.log("[+] HOOKED: RealCall.execute");
        }
    } catch(e) { console.log("[-] OkHttp RealCall: " + e.message); }

    console.log("[+] SSL Unpinning + Network intercept loaded!");
    console.log("[+] Configure proxy: adb shell settings put global http_proxy <PC_IP>:8080");
});
