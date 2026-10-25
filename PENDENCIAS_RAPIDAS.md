# Pendências Não Resolvidas Rapidamente

## P0.9 - Concorrência MySQL 8.0
**Status:** Aguarda execução da CI
- Testes de concorrência configurados em `.github/workflows/ci.yml`
- Job `test-mysql-concurrency` executará no GitHub Actions
- Não é possível testar localmente pois MySQL não está disponível
- Próximo passo: Observar resultado da CI após push

## P0.10 - Confirmação Física da Retirada
**Status:** Bloqueio de negócio
- Não há fluxo implementado para confirmar que o paciente retirou fisicamente o medicamento
- A dispensação via QR é considerada a conclusão da operação
- Próximo passo: Definir e implementar fluxo de confirmação física (requer decisão de negócio)

## P0.10 - Revogação de QR
**Status:** Não implementado
- Não há campo de revogação no modelo `QRNonce`
- Não há rota/mecanismo para revogar QRs ativos
- Invalidação atual cobre apenas expiração e uso
- Próximo passo: Definir e implementar mecanismo de revogação (requer decisão de negócio)

## P0.10 - Validação de Vínculo Específico
**Status:** Parcialmente implementado
- Validação atual baseada apenas em cargo (`@farmaceutico_required`)
- Qualquer farmacêutico pode consumir qualquer QR válido
- Placeholder adicionado para validação de vínculo (não impõe restrição real)
- Próximo passo: Definir e implementar regras de vínculo específico (farmacêutico ↔ paciente/receita)

## P0.5 - Migration de senha_trocada
**Status:** Resolvido para ambiente de teste
- Migration manual criada em `backend/migrations/add_senha_trocada.py`
- Campo adicionado ao banco de teste local
- CI da main ainda falha com este erro
- Próximo passo: Integrar migration no fluxo de Alembic ou executar em produção

## Resumo
- P0.11: ✅ Concluído (testes IoT corrigidos, CI configurada)
- P0.10: ⚠️ Parcial (QR opaco, expiração, uso único implementados; confirmação física, revogação e vínculo específico pendentes)
- P0.9: ⚠️ Parcial (atomicidade implementada; concorrência MySQL aguarda CI)
- P0.5: ⚠️ Parcial (migration criada; integração pendente)
