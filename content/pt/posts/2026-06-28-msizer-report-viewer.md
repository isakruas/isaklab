---
title: M Sizer Report Viewer — visualizando relatório de sizing de MongoDB
date: 2026-06-28
tags: mongodb, msizer, react, observabilidade
summary: Junto com o time de SRE, a gente buscava formas de otimizar nossos MongoDB. O pessoal do Atlas sugeriu rodar um script de sizing, e fora do horário eu montei um viewer pra ler aquele JSON de forma objetiva. Agora estou abrindo a ferramenta.
---

Faz um tempo, junto com o time de SRE com quem trabalho, a gente vinha buscando formas de
otimizar nossas infraestruturas de MongoDB. Depois de algumas reuniões, o pessoal do Atlas
sugeriu que rodássemos um script de sizing para coletar as estatísticas dos clusters. O
script ajudou bastante: deu para fazer um levantamento sério do estado dos clusters e, a
partir dele, realizar otimizações de verdade.

Só que tinha um incômodo. O script gera um JSON enorme, e a gente não tinha uma ferramenta
para visualizar aqueles dados de forma objetiva e fácil, sem depender da ferramenta
proprietária do Mongo. Então, fora do horário de trabalho, comecei a montar um visualizador
para facilitar a análise. Depois de algumas horas, e com a ajuda de alguns agentes de IA,
consegui estruturar uma visualização decente para aquele relatório. É o **M Sizer Report
Viewer**.

Tem uma [demo no ar](https://isakruas.github.io/msizer-report-viewer/) e o código está
[no GitHub](https://github.com/isakruas/msizer-report-viewer). O fluxo é direto: você roda o
script no cluster com o `mongosh`, salva a saída num arquivo e depois carrega esse JSON no
viewer (ou cola direto) para ver a análise com as recomendações.

O viewer organiza o relatório em algumas frentes. **Saúde do cluster** e **replicação**
(capacidade e janela de retenção do oplog), para bater o olho e ver se está tudo em ordem. **Cache
do WiredTiger**, onde costuma morar o problema de memória, com eficiência de cache, pressão
de eviction e uso de memória; e o **pool de conexões**, com taxa de utilização e de rejeição.
**Slow queries e profiler**, incluindo os `COLLSCAN` (varredura de coleção inteira, o clássico
sintoma de índice faltando), detecção de operação lenta e a configuração do profiler por
banco. **Índices**, com utilização, razão índice/dados e detecção de índice que ninguém usa,
que é peso morto na escrita. **Storage**, com eficiência de compressão. E uma parte de
segurança, olhando TLS, autenticação e read/write concern. A interface tem tema claro e
escuro.

Um ponto que para mim faz diferença: é um site estático, sem backend. Você abre o JSON
direto no navegador, então o dado não sai da sua máquina, o que importa quando o relatório
carrega detalhe de um cluster de produção. Por baixo é React com TypeScript, Vite para o
build e Tailwind para o estilo.

Vale deixar claro de onde isso vem. O script de coleta descende do
[`getMongoData`](https://github.com/mongodb/support-tools/tree/master/getMongoData) das
Support Tools oficiais do MongoDB. Para
chegar na versão `getMongoSizingData.js` deste repo, usei como referência o
[`msizer` do alek-mdb](https://github.com/alek-mdb/msizer) e um
[gist do TravWill-Mongo](https://gist.github.com/TravWill-Mongo/32f9738b9a6768e634126a9616ae38d1).
Em cima dessas referências, estendi o script com mais métricas — análise de slow queries e do
profiler — e construí o viewer. Estou tornando tudo isso público para quem estiver num
trabalho de observabilidade e otimização de MongoDB poder usar para entender e ajustar melhor
os próprios bancos.

A ideia não é substituir quem entende de sizing, é encurtar o caminho até a leitura: tirar o
relatório do JSON cru e botar num formato em que dá para enxergar o cluster de uma vez.
