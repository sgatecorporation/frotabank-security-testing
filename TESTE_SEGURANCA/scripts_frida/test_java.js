setTimeout(function() {
    console.log("Java available: " + Java.available);
    if (Java.available) {
        Java.perform(function() {
            console.log("Java.perform OK!");
            console.log("Enumerating loaded classes (first 5 with unico)...");
            Java.enumerateLoadedClasses({
                onMatch: function(name) {
                    if (name.indexOf("unico") !== -1 || name.indexOf("MACSigner") !== -1) {
                        console.log("  CLASS: " + name);
                    }
                },
                onComplete: function() {
                    console.log("Class enumeration done.");
                }
            });
        });
    } else {
        console.log("Java NOT available!");
    }
}, 8000);
