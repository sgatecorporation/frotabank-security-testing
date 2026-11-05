Java.perform(function() {
    console.log("[*] Bypass Google Play Store check...");

    // Bypass Google Play availability check
    try {
        var GoogleApiAvailability = Java.use("com.google.android.gms.common.GoogleApiAvailability");
        GoogleApiAvailability.isGooglePlayServicesAvailable.overload('android.content.Context').implementation = function(ctx) {
            console.log("[+] isGooglePlayServicesAvailable -> SUCCESS (0)");
            return 0; // ConnectionResult.SUCCESS
        };
        console.log("[+] Hooked: GoogleApiAvailability.isGooglePlayServicesAvailable");
    } catch(e) {
        console.log("[-] GoogleApiAvailability: " + e);
    }

    try {
        var GoogleApiAvailability2 = Java.use("com.google.android.gms.common.GoogleApiAvailability");
        GoogleApiAvailability2.isGooglePlayServicesAvailable.overload('android.content.Context', 'int').implementation = function(ctx, v) {
            console.log("[+] isGooglePlayServicesAvailable(ctx,v) -> SUCCESS (0)");
            return 0;
        };
    } catch(e) {}

    // Bypass ConnectionResult check
    try {
        var ConnectionResult = Java.use("com.google.android.gms.common.ConnectionResult");
        ConnectionResult.isSuccess.implementation = function() {
            console.log("[+] ConnectionResult.isSuccess -> true");
            return true;
        };
    } catch(e) {}

    // Bypass PackageManager check for Play Store
    try {
        var PackageManager = Java.use("android.app.ApplicationPackageManager");
        PackageManager.getPackageInfo.overload('java.lang.String', 'int').implementation = function(pkg, flags) {
            if (pkg === "com.android.vending") {
                console.log("[+] getPackageInfo(com.android.vending) -> allowing");
            }
            return this.getPackageInfo(pkg, flags);
        };
    } catch(e) {}

    console.log("[+] Play Store bypass hooks loaded!");
});
