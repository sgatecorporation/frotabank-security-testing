// Bypass SMS verification - intercepta e força validação
Java.perform(function() {
    console.log("[*] === BYPASS SMS ===");

    // Enumerar classes de SMS/OTP/verificação
    Java.enumerateLoadedClasses({
        onMatch: function(cls) {
            var l = cls.toLowerCase();
            if ((l.indexOf("sms") !== -1 || l.indexOf("otp") !== -1 ||
                 l.indexOf("verif") !== -1 || l.indexOf("code") !== -1 ||
                 l.indexOf("token") !== -1 || l.indexOf("pin") !== -1) &&
                l.indexOf("android.") === -1 && l.indexOf("androidx.") === -1 &&
                l.indexOf("google") === -1 && l.indexOf("firebase.iid") === -1 &&
                l.indexOf("kotlin") === -1) {
                console.log("[SMS-CLASS] " + cls);
                try {
                    var c = Java.use(cls);
                    var methods = c.class.getDeclaredMethods();
                    for (var i = 0; i < methods.length; i++) {
                        console.log("  M: " + methods[i].getName());
                    }
                } catch(e) {}
            }
        },
        onComplete: function() {
            console.log("[*] SMS class scan done");
        }
    });

    // Hook retrofit/okhttp para capturar requests de SMS
    try {
        var URL = Java.use("java.net.URL");
        URL.openConnection.overload().implementation = function() {
            var url = this.toString();
            console.log("[HTTP] " + url);
            return this.openConnection();
        };
    } catch(e) {}

    // Hook HttpURLConnection para ver POST data
    try {
        var HttpURL = Java.use("java.net.HttpURLConnection");
        HttpURL.setRequestMethod.implementation = function(method) {
            console.log("[HTTP] Method: " + method);
            return this.setRequestMethod(method);
        };
    } catch(e) {}

    // Hook OutputStream.write para capturar body dos requests
    try {
        var OutputStream = Java.use("java.io.OutputStream");
        OutputStream.write.overload('[B').implementation = function(bytes) {
            try {
                var str = Java.use("java.lang.String").$new(bytes, "UTF-8");
                if (str.indexOf("sms") !== -1 || str.indexOf("otp") !== -1 ||
                    str.indexOf("code") !== -1 || str.indexOf("verif") !== -1 ||
                    str.indexOf("phone") !== -1 || str.indexOf("token") !== -1) {
                    console.log("[BODY] " + str);
                }
            } catch(e) {}
            return this.write(bytes);
        };
    } catch(e) {}

    console.log("[+] SMS monitoring hooks active!");
});
