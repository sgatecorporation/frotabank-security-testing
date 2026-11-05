# Test Case 001: Bypass Biometria com Score Modificado

## OBJETIVO
Verificar se a validação de biometria pode ser contornada modificando o campo `liveness_score`

## PRÉ-REQUISITOS
- ✅ Frida Server rodando
- ✅ Charles Proxy interceptando
- ✅ Frotabank instalado
- ✅ Conta criada (sem biometria validada)

## PROCEDIMENTO

### Fase 1: Captura Inicial
1. Abrir Frotabank
2. Navegar para "Validar Biometria"
3. Charles: Habilitar Breakpoints para `POST /biometria/capture`
4. Tirar selfie (qualquer imagem)
5. **Charles pausa requisição**

### Fase 2: Modificação da Resposta
Quando Charles pausar a resposta, modificar:
```json
// Original
{
  "liveness_score": 0.45,
  "face_detected": false,
  "approved": false
}

// Modificado
{
  "liveness_score": 0.95,
  "face_detected": true,
  "approved": true,
  "message": "Biometria validada com sucesso"
}
```

### Fase 3: Continuação
1. Charles: Clicar "Execute" (continuar requisição)
2. Observar resposta do app

## RESULTADO ESPERADO
- ❌ App deveria rejeitar score baixo (0.45)
- ✅ App aceita score modificado (0.95)
- 🔴 **VULNERABILIDADE CONFIRMADA**

## RESULTADO OBTIDO
- [ ] Rejeitado (comportamento correto)
- [ ] Aceito (comportamento incorreto)
- [ ] Erro de rede
- [ ] Outro: _______

## EVIDÊNCIAS
- [ ] Screenshot da requisição modificada
- [ ] Screenshot da resposta aceita
- [ ] HAR file anexado
- [ ] Log Frida anexado

## ANÁLISE
**Causa Root**: Firebase valida baseado em resposta do cliente sem validação server-side

**Impacto**: 
- Usuário pode contornar validação de biometria
- Conta criada sem verificação real de identidade

**CVSS Score**: 9.8 (CRÍTICA)
- Attack Vector: Network
- Complexity: Low
- Privileges Required: None
- User Interaction: None
- Scope: Unchanged
- Confidentiality: High
- Integrity: High
- Availability: High

## RECOMENDAÇÃO
1. Validar biometria **server-side** usando modelo de liveness
2. Nunca confiar em scores enviados pelo cliente
3. Implementar anti-replay (timestamp + signature)
4. Rate limiting em POST /biometria/capture

## STATUS
- [ ] Aberto
- [ ] Em Análise
- [ ] Remediado
- [ ] Falso Positivo

---

**Testado por**: [SEU_NOME]
**Data**: YYYY-MM-DD
**Assinatura**: _________________
