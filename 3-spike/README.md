# Spike: Crypto-Shredding para Conformidade LGPD vs Auditoria

Este spike valida e prova a decisão documentada no **ADR 05: Resolução de Conflito Legal (Trilha Imutável vs LGPD)**, escolhida como a decisão mais arriscada da arquitetura do Monólito Modular adotado.

## O que este código prova

A arquitetura do Sistema Unificado de Saúde Municipal (SUSM) exige o armazenamento imutável do histórico de alterações do sistema (retenção clínica de 20 anos) para satisfazer a auditoria sanitária rigorosa. Isso impõe uma trilha de eventos do tipo "append-only". Simultaneamente, o sistema precisa cumprir a Lei Geral de Proteção de Dados (LGPD), permitindo que o paciente exerça seu direito ao esquecimento. 

Este código comprova que é viável aplicar o padrão de **Crypto-Shredding (Destruição Criptográfica)** para conciliar essas duas restrições fundamentais e contraditórias:
1. Os dados sensíveis do paciente (PII) são criptografados antes de serem inseridos no banco de eventos usando uma chave única pertencente ao paciente, gerenciada de forma apartada por um serviço de chaves (simulado como `KMS`).
2. Os dados públicos, de dispensação ou regulação - essenciais para a auditoria sanitária e contábil - são mantidos abertos para inspeção rápida.
3. Quando o direito ao esquecimento é acionado, apenas a **chave criptográfica do paciente é deletada** do KMS. O registro no Event Store permanece estruturalmente intacto, mantendo a veracidade da auditoria, mas o dado sensível contido ali torna-se irreversível e inútil, garantindo o "esquecimento" jurídico.

## Como rodar

Para executar este spike, não é necessário instalar nenhum pacote de terceiros. Ele foi inteiramente construído com bibliotecas padrão do Python 3.12.

No terminal, posicionado no diretório em que este arquivo se encontra, execute:

```bash
python3 spike.py
```

O resultado impresso será equivalente ao conteúdo salvo no arquivo `saida-esperada.txt`. A execução primeiro exibe os registros abertos de forma visível e, em seguida, simula a destruição da chave, demonstrando que a mesma listagem passa a exibir os registros sensíveis como esquecidos/inacessíveis, mantendo as informações de auditoria íntegras.

## O que aconteceria se a decisão estivesse errada

O conflito de restrições entre o "Envelope E" (auditoria rígida sanitária) e a legislação comum impõe um risco arquitetural sério. Caso a decisão estivesse errada, teríamos dois caminhos catastróficos para o negócio e a operação legal da cidade:

- **Se os dados fossem fisicamente apagados da Trilha (Violando a Auditoria):** Realizar *DELETE* ou *UPDATE* sobrescrevendo informações sensíveis nos eventos apagaria as provas da cadeia de custódia clínica. Em uma auditoria, a Secretaria não conseguiria provar por que um lote foi dispensado, sendo autuada por fraude ou má gestão documental pelos órgãos reguladores.
- **Se a exigência da exclusão fosse ignorada (Violando a LGPD):** Optar por manter todos os dados abertos com a desculpa da imutabilidade da trilha traria pesadas multas da Autoridade Nacional de Proteção de Dados (ANPD). A arquitetura tornaria o sistema municipal legalmente insustentável. O *Crypto-shredding* é a ponte que evita ambos os colapsos.
