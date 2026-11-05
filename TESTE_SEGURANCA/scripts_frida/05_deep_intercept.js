Java.perform(function() {
    console.log("[*] === DEEP INTERCEPT ===");

    // Detectar se é WebView/React Native/Flutter
    Java.enumerateLoadedClasses({
        onMatch: function(cls) {
            var l = cls.toLowerCase();
            if (l.indexOf("reactnative") !== -1 || l.indexOf("react_native") !== -1 ||
                l.indexOf("flutter") !== -1 || l.indexOf("webview") !== -1 ||
                l.indexOf("cordova") !== -1 || l.indexOf("capacitor") !== -1 ||
                l.indexOf("retrofit") !== -1 || l.indexOf("okhttp") !== -1 ||
                l.indexOf("volley") !== -1 || l.indexOf("httpurl") !== -1) {
                if (l.indexOf("android.webkit") === -1 && l.indexOf("androidx") === -1)
                    console.log("[FRAMEWORK] " + cls);
            }
        },
        onComplete: function() { console.log("[*] Framework scan done"); }
    });

    // Hook ALL conscrypt classes
    try {
        Java.enumerateLoadedClasses({
            onMatch: function(cls) {
                if (cls.indexOf("conscrypt") !== -1 && cls.indexOf("Stream") !== -1) {
                    console.log("[CONSCRYPT] " + cls);
                }
            },
            onComplete: function() {}
        });
    } catch(e) {}

    // Hook at Socket level
    try {
        var Socket = Java.use("java.net.Socket");
        Socket.connect.overload("java.net.SocketAddress", "int").implementation = function(addr, timeout) {
            console.log("[SOCKET] connect -> " + addr.toString());
            return this.connect(addr, timeout);
        };
        console.log("[+] HOOKED: Socket.connect");
    } catch(e) { console.log("[-] Socket: " + e.message); }

    // Hook InetAddress
    try {
        var InetAddr = Java.use("java.net.InetAddress");
        InetAddr.getByName.overload("java.lang.String").implementation = function(host) {
            console.log("[DNS] " + host);
            return this.getByName(host);
        };
        console.log("[+] HOOKED: InetAddress.getByName");
    } catch(e) {}

    // Hook SharedPreferences para ver tokens/dados salvos
    try {
        var Editor = Java.use("android.app.SharedPreferencesImpl$EditorImpl");
        Editor.putString.implementation = function(key, value) {
            console.log("[PREF] " + key + " = " + (value ? value.substring(0, Math.min(value.length(), 200)) : "null"));
            return this.putString(key, value);
        };
        console.log("[+] HOOKED: SharedPreferences.putString");
    } catch(e) { console.log("[-] SharedPrefs: " + e.message); }

    // Hook Log para ver debug interno do app
    try {
        var Log = Java.use("android.util.Log");
        Log.d.overload("java.lang.String", "java.lang.String").implementation = function(tag, msg) {
            if (tag.indexOf("Frota") !== -1 || tag.indexOf("SMS") !== -1 ||
                tag.indexOf("API") !== -1 || tag.indexOf("Http") !== -1 ||
                tag.indexOf("OkHttp") !== -1 || tag.indexOf("Retrofit") !== -1 ||
                msg.indexOf("sms") !== -1 || msg.indexOf("code") !== -1 ||
                msg.indexOf("verif") !== -1 || msg.indexOf("token") !== -1) {
                console.log("[LOG.d] " + tag + ": " + msg.substring(0, Math.min(msg.length(), 300)));
            }
            return this.d(tag, msg);
        };
        Log.i.overload("java.lang.String", "java.lang.String").implementation = function(tag, msg) {
            if (tag.indexOf("Frota") !== -1 || tag.indexOf("SMS") !== -1 ||
                tag.indexOf("API") !== -1 || tag.indexOf("Http") !== -1 ||
                msg.indexOf("sms") !== -1 || msg.indexOf("verif") !== -1) {
                console.log("[LOG.i] " + tag + ": " + msg.substring(0, Math.min(msg.length(), 300)));
            }
            return this.i(tag, msg);
        };
        Log.e.overload("java.lang.String", "java.lang.String").implementation = function(tag, msg) {
            console.log("[LOG.e] " + tag + ": " + msg.substring(0, Math.min(msg.length(), 300)));
            return this.e(tag, msg);
        };
        console.log("[+] HOOKED: android.util.Log");
    } catch(e) { console.log("[-] Log: " + e.message); }

    console.log("[+] Deep intercept ativo!");
});
