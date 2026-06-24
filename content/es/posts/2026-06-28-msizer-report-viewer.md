---
title: M Sizer Report Viewer — visualizando reportes de sizing de MongoDB
date: 2026-06-28
tags: mongodb, msizer, react, observabilidad
summary: Junto con el equipo de SRE, buscábamos formas de optimizar nuestros MongoDB. La gente de Atlas sugirió correr un script de sizing, y fuera del horario armé un viewer para leer ese JSON de forma clara. Ahora estoy abriendo la herramienta.
---

Hace un tiempo, junto con el equipo de SRE con el que trabajo, veníamos buscando formas de
optimizar nuestras infraestructuras de MongoDB. Después de algunas reuniones, la gente de
Atlas sugirió que corriéramos un script de sizing para recolectar las estadísticas de los
clústeres. El script ayudó bastante: permitió hacer un relevamiento serio del estado de los
clústeres y, a partir de ahí, realizar optimizaciones de verdad.

Pero había una molestia. El script genera un JSON enorme, y no teníamos una herramienta para
visualizar esos datos de forma objetiva y fácil, sin depender de la herramienta propietaria de
Mongo. Así que, fuera del horario de trabajo, empecé a armar un visualizador para facilitar el
análisis. Después de algunas horas, y con la ayuda de algunos agentes de IA, logré estructurar
una visualización decente para ese reporte. Es el **M Sizer Report Viewer**.

Hay una [demo en línea](https://isakruas.github.io/msizer-report-viewer/) y el código está
[en GitHub](https://github.com/isakruas/msizer-report-viewer). El flujo es directo: corrés el
script en el clúster con `mongosh`, guardás la salida en un archivo y después cargás ese JSON
en el viewer (o lo pegás directo) para ver el análisis con sus recomendaciones.

El viewer organiza el reporte en algunos frentes. **Salud del clúster** y **replicación**
(capacidad y ventana de retención del oplog), para mirar de un vistazo y ver si está todo sano.
La **caché de WiredTiger**, donde suele vivir el problema de memoria, con eficiencia de caché,
presión de eviction y uso de memoria; y el **pool de conexiones**, con tasa de utilización y de
rechazo. **Slow queries y profiler**, incluyendo los `COLLSCAN` (barrido de la colección
entera, el síntoma clásico de un índice faltante), detección de operación lenta y la
configuración del profiler por base. **Índices**, con utilización, razón índice/datos y
detección de índices que nadie usa, que son peso muerto en la escritura. **Storage**, con
eficiencia de compresión. Y una parte de seguridad, mirando TLS, autenticación y read/write
concern. La interfaz tiene tema claro y oscuro.

Un punto que para mí hace la diferencia: es un sitio estático, sin backend. Abrís el JSON
directo en el navegador, así que el dato no sale de tu máquina, algo que importa cuando el
reporte trae detalle de un clúster de producción. Por debajo es React con TypeScript, Vite para
el build y Tailwind para el estilo.

Vale aclarar de dónde viene esto. El script de colecta desciende del
[`getMongoData`](https://github.com/mongodb/support-tools/tree/master/getMongoData) de las
Support Tools oficiales de MongoDB. Para llegar a
la versión `getMongoSizingData.js` de este repo, usé como referencia el
[`msizer` de alek-mdb](https://github.com/alek-mdb/msizer) y un
[gist de TravWill-Mongo](https://gist.github.com/TravWill-Mongo/32f9738b9a6768e634126a9616ae38d1).
Sobre esas referencias, extendí el script con más métricas — análisis de slow queries y del
profiler — y construí el viewer. Estoy haciendo todo esto público para que quien esté en un
trabajo de observabilidad y optimización de MongoDB pueda usarlo para entender y ajustar mejor
sus propias bases.

La idea no es reemplazar a quien sabe de sizing, es acortar el camino hasta leerlo: sacar el
reporte del JSON crudo y ponerlo en un formato donde se pueda ver el clúster de una vez.
