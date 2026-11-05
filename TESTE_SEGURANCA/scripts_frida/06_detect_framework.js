console.log("[*] DETECTANDO FRAMEWORK...");

Java.perform(function() {
    console.log("[*] Java.perform OK");

    var flutter = false, react = false, webview = false, retrofit = false;
    var count = 0;

    Java.enumerateLoadedClasses({
        onMatch: function(cls) {
            count++;
            if (cls.indexOf("io.flutter") !== -1) { if (!flutter) { console.log("[!!!] FLUTTER DETECTADO: " + cls); flutter = true; } }
            if (cls.indexOf("com.facebook.react") !== -1) { if (!react) { console.log("[!!!] REACT NATIVE DETECTADO: " + cls); react = true; } }
            if (cls.indexOf("WebView") !== -1 && cls.indexOf("android") === -1) { console.log("[?] WebView: " + cls); webview = true; }
            if (cls.indexOf("retrofit") !== -1) { console.log("[NET] Retrofit: " + cls); retrofit = true; }
            if (cls.indexOf("okhttp3") !== -1 && cls.indexOf("internal") === -1) { console.log("[NET] OkHttp: " + cls); }
            if (cls.indexOf("volley") !== -1) { console.log("[NET] Volley: " + cls); }
            if (cls.indexOf("frotabank") !== -1 || cls.indexOf("frota") !== -1) { console.log("[APP] " + cls); }
        },
        onComplete: function() {
            console.log("[*] Total classes: " + count);
            console.log("[*] Flutter=" + flutter + " React=" + react + " WebView=" + webview + " Retrofit=" + retrofit);
        }
    });
});
