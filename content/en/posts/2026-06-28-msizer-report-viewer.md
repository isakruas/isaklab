---
title: M Sizer Report Viewer — visualizing MongoDB sizing reports
date: 2026-06-28
tags: mongodb, msizer, react, observability
summary: Together with the SRE team, we were looking for ways to optimize our MongoDB. The Atlas folks suggested running a sizing script, and after hours I built a viewer to read that JSON clearly. Now I'm opening the tool up.
---

A while back, together with the SRE team I work with, we'd been looking for ways to optimize
our MongoDB infrastructure. After a few meetings, the Atlas folks suggested we run a sizing
script to collect cluster statistics. The script helped a lot: it let us do a proper survey of
the state of the clusters and, from there, carry out real optimizations.

There was one annoyance, though. The script produces a huge JSON, and we didn't have a tool to
visualize that data objectively and easily, without depending on Mongo's proprietary tooling.
So, outside work hours, I started building a viewer to make the analysis easier. After a few
hours, and with the help of some AI agents, I managed to put together a decent visualization
for that report. That's the **M Sizer Report Viewer**.

There's a [live demo](https://isakruas.github.io/msizer-report-viewer/) and the code is
[on GitHub](https://github.com/isakruas/msizer-report-viewer). The flow is straightforward:
you run the script on the cluster with `mongosh`, save the output to a file, then load that
JSON into the viewer (or paste it directly) to see the analysis with its recommendations.

The viewer organizes the report into a few fronts. **Cluster health** and **replication**
(oplog capacity and retention window), to glance at and see whether everything is sound. The
**WiredTiger cache**, where memory trouble usually lives, with cache efficiency, eviction
pressure and memory usage; and the **connection pool**, with utilization and rejection rates.
**Slow queries and profiler**, including `COLLSCAN`s (full collection scans, the classic
symptom of a missing index), slow operation detection and per-database profiler configuration.
**Indexes**, with utilization, index-to-data ratio and detection of indexes nobody uses, which
are dead weight on writes. **Storage**, with compression efficiency. And a security section,
looking at TLS, authentication and read/write concern. The interface has light and dark themes.

One point that matters to me: it's a static site, no backend. You open the JSON straight in the
browser, so the data never leaves your machine, which counts when the report carries detail
about a production cluster. Under the hood it's React with TypeScript, Vite for the build and
Tailwind for styling.

It's worth being clear about where this comes from. The collection script descends from
[`getMongoData`](https://github.com/mongodb/support-tools/tree/master/getMongoData) in
MongoDB's official Support Tools. To reach the
`getMongoSizingData.js` version in this repo, I used
[alek-mdb's `msizer`](https://github.com/alek-mdb/msizer) and a
[gist by TravWill-Mongo](https://gist.github.com/TravWill-Mongo/32f9738b9a6768e634126a9616ae38d1)
as references. On top of those, I extended the script with more metrics — slow query and
profiler analysis — and built the viewer. I'm making all of it public so anyone doing
observability and optimization work on MongoDB can use it to better understand and tune their
own databases.

The idea isn't to replace someone who knows sizing, it's to shorten the path to reading it:
take the report out of raw JSON and put it in a shape where you can see the cluster at a glance.
