# Chaves e Dados Capturados - Unico SDK (Frotabank)

## Data: 2026-10-20

## Signing Key (HS256) - APK Modificado
```
7bbc34af2d387f668bc324a9d002c34776f6dd8ec3c4cdcacd0eb7ca8b5a1ed0
```

**Formato**: String passada a `MACSigner(String)` do nimbus-jose-jwt.
Internamente o `MACSigner` faz `secret.getBytes(StandardCharsets.UTF_8)` para gerar o `SecretKeySpec`.

**Onde capturada**: Tag `UNICO_SIGNING_KEY` no logcat, via hook `Log.d` adicionado no método:
`io.unico.sdk.capture.isClickable.AcessoBioListener(String, Map) -> String`

**Uso**: `new MACSigner(key)` -> `jwsObject.sign(signer)` -> JWT HS256

## Dados do Construtor Unico SDK
```
v0 (URL backend): https://backend-sdk.prod.private.unico.run/sdk/
v1 (nome SDK):    backend-sdk
```

**Classe**: `io.unico.sdk.capture.getHandwritingBoundsOffsetTop$onSystemClosedCameraTimeoutSession`
**Capturado via**: Tags `UNICO_KEY_INIT` e `UNICO_KEY_INIT_V1` no logcat

## JWT Structure (observada no capture.flows)
```json
{
  "alg": "HS256"
}
{
  "iss": "unico-sdk-android",
  "capture": {
    "image": "<base64 JPEG da selfie>"
  },
  "keyBody": "<...>",
  "jti": "<UUID>",
  "info": {
    "cpf": "<CPF do usuario>",
    "name": "<nome>"
  }
}
```

## Observacoes

1. A chave capturada NAO bateu com o JWT do capture.flows antigo.
   Possivel causa: o APK modificado usa cert de debug diferente do original,
   e a derivacao da chave (via DexGuard) pode incluir o hash do certificado APK.

2. Para capturar a chave do APK ORIGINAL, alternativas:
   - Frida gadget injetado no APK original
   - JDWP debugging do processo
   - Interceptar via Xposed/LSPosed no emulador

3. A chave eh derivada no construtor da classe obfuscada usando o array
   `getHeightPixels` (58 bytes) e operacoes XOR/aritmeticas via DexGuard.
