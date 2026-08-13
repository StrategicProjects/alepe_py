# Em português

O pacote é escrito em inglês, mas o público é brasileiro e o vocabulário da API
é português. Para não obrigar ninguém a alternar de idioma no meio de um
pipeline, cada função tem um alias com o nome do próprio endpoint que ela
consulta.

## Os aliases

| Português | Inglês | Endpoint |
| --- | --- | --- |
| `parlamentares()` | `representatives()` | `/parlamentares` |
| `servidores()` | `staff()` | `/servidores` |
| `cargos()` | `positions()` | `/cargos` |
| `lotacoes()` | `departments()` | `/lotacoes` |
| `remuneracao()` | `remuneration()` | `/remuneracao` |
| `contratos()` | `contracts()` | `/contratos` |
| `licitacoes()` | `procurements()` | `/licitacoes` |
| `projetos()` | `bills()` | `/proposicoes/projetos` |
| `indicacoes()` | `indications()` | `/proposicoes/indicacoes` |
| `requerimentos()` | `requests()` | `/proposicoes/requerimentos` |
| `limpar_cache()` | `cache_clear()` | — |

Os nomes são escritos sem acento: identificadores acentuados são legais em
Python, mas incômodos de digitar e frágeis entre codificações.

## Argumentos

Os aliases de proposições também aceitam os argumentos em português:

```python
import alepe

alepe.projetos(ano=2024)
alepe.projetos(numero=3, ano=2024)
alepe.requerimentos(ano=2024, legislatura=20)
```

Os demais aliases são a mesma função, com os mesmos argumentos:

```python
alepe.servidores(status="efetivo")
alepe.contratos(refresh=True)
```

## Valores de filtro

O filtro `status` aceita os dois vocabulários, então estas duas chamadas são a
mesma consulta:

```python
alepe.servidores(status="efetivo")
alepe.staff(status="permanent")
```

Os valores originais da API são `efetivo`, `comissionado` e `a-disposicao`; os
equivalentes em inglês são `permanent`, `commissioned` e `seconded`.

## Nomes de coluna

Os nomes de coluna **não** são traduzidos. Eles mantêm o campo oficial da API,
normalizado para snake_case — `nome_lotacao`, `vigencia_inicio`,
`cargo_nivel` — para que qualquer resultado continue rastreável até a fonte.
Traduzir os nomes tornaria impossível conferir um número contra o portal da
ALEPE sem um dicionário na cabeça.
