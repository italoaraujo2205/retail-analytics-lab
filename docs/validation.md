# Validação da primeira versão

Ambiente de execução: Python 3.12.14, pandas 2.2.3, NumPy 2.3.5 e SciPy 1.17.0, em Linux.

## Verificações executadas

- Instalação editável do pacote, sem reinstalar as dependências já presentes.
- Pipeline completo do cenário padrão: 24.000 pedidos únicos e 16.000 clientes no experimento.
- 14 testes automatizados de regras de qualidade, integridade, deduplicação, reconciliação financeira, grão de pedido/item, reexecução, preservação do banco em falha, SRM e censura temporal.
- Execução das seis células Python do notebook em ordem e gravação de suas saídas. Essa checagem executou o código em um interpretador Python; não foi um teste da interface Jupyter.
- Reexecução completa com os mesmos parâmetros: os dez arquivos de relatório produziram os mesmos hashes SHA-256.
- Renderização e inspeção visual do SVG do relatório; verificação estrutural de HTML, JSON e XML/SVG.

As verificações locais não equivalem a homologação em produção. A instalação das dependências a partir de uma máquina vazia, o PowerShell/Windows, a interface Jupyter e a interação do relatório em diferentes navegadores não foram testados neste ambiente. O workflow de GitHub Actions repete testes e pipeline após o push; seu resultado é separado da execução local.
