<!-- chapter: 1 -->
<!-- title: The Browser as a System -->
<!-- question: What happens when you enter a URL and press Enter? -->

## The Question

It is 9:07 on a Tuesday morning. You open a laptop that has been asleep since last night, and while the screen is still brightening you type the address of the incident dashboard and press Enter. Perhaps four hundred milliseconds later, the page is there. You do not think about it. You are looking for the incident that paged you at 6:40, and there it is, and you click it.

In those four hundred milliseconds, a name was resolved into an address, possibly by consulting four different caches and two servers on different continents. A connection was negotiated, and inside it a cryptographic handshake established a shared secret between your laptop and a machine you will never see. A request was sent, and the first bytes of a response came back, and before the response had finished arriving the browser had already begun to read it, had discovered from the first kilobyte that it would need a stylesheet and two scripts and a font, and had gone to fetch them. Somewhere in a process you did not know existed, a tokenizer was turning characters into tags, a tree was being built, and a second tree describing how everything should look was being built beside it. A script ran and stopped the first tree from growing, then let it continue. The two trees were combined, geometry was computed, the geometry was turned into paint commands, the paint commands were sorted into layers, the layers were rasterized into bitmaps on a graphics processor, the bitmaps were composited, and a frame was handed to the display. Then you moved your mouse, and a completely separate pipeline began to determine what was under it.

You can be a very good frontend engineer without knowing most of this. The abstractions are excellent. That is what makes them dangerous.

The problems that define senior work are almost all problems where an abstraction failed to hide something. The page that is fast on your machine and slow in São Paulo. The button that is visible but cannot be clicked for two seconds. The stylesheet that arrives late and makes the whole layout jump. The script that works when the cache is warm and breaks when it is cold. In every one of these, the engineer who understands what is underneath the abstraction can reason toward the cause, and the engineer who does not is left changing things until the symptom goes away, which is a form of debugging in the same sense that rolling dice is a form of arithmetic.

So this chapter is about what is underneath. It is long, and it is meant to be. The question of what happens when you press Enter is a question about a system with dozens of cooperating parts, and the goal is not to list them but to understand how they depend on one another, which of them can overlap, where the browser is following a rule and where it is guessing, and how all of it turns into the thing a human being experiences as "the page loaded."

We will start with the answer you already know.

## The Naive Model

If you have interviewed for a frontend job in the last fifteen years, you have probably been asked this question, and you have probably given some version of this answer:

The browser parses the URL. It looks up the hostname in DNS to get an IP address. It opens a TCP connection to that address, and if the scheme is `https`, it performs a TLS handshake. It sends an HTTP request. The server sends back an HTML response. The browser parses the HTML into the DOM. It fetches the CSS and builds the CSSOM. It fetches and runs the JavaScript. It combines DOM and CSSOM into a render tree, computes layout, paints, and displays the page.

```
URL → DNS → TCP → TLS → HTTP request → HTML → DOM
                                        ↓
                                  CSS → CSSOM
                                        ↓
                                  JS → execute
                                        ↓
                            render tree → layout → paint → display
```

We want to be clear that this is a good model. It is correct in the sense that every step in it really happens. It gets the order of dependencies approximately right. It is enough to explain why a slow DNS server makes a page slow, why an HTTPS page has more setup cost than an HTTP one, why a page with no CSS renders faster than one with a lot of it. It is the model most working engineers carry, and they carry it because it works most of the time.

Its virtue is also its limitation: it is a *sequence*. Each arrow says "and then." And the real system is not a sequence. It is a graph, with many things happening at once, with some steps that can begin before the previous one has finished, with some that must wait and some that only *sometimes* wait, and with a great deal of speculation by the browser about what will be needed next. When the sequential model fails, it fails because it cannot represent overlap, and most of the interesting behavior of a loading page lives in the overlap.

Let us break it.

## Breaking the Model

Each of the following is a real thing that happens, and each is something the sequential model cannot explain.

**The page renders before the HTML has finished downloading.** Open a page whose HTML is a few hundred kilobytes over a slow connection, and you will see the top of it appear while the bottom is still in flight. The model says HTML arrives, then DOM is built, then layout, then paint. But the browser does not wait for the HTML. It parses as bytes arrive, it builds the DOM incrementally, and under the right conditions it lays out and paints what it has so far. The arrow from "HTML" to "DOM" is not one arrow; it is a stream.

**A script stops the parser.** Put a `<script src="analytics.js">` in the `<head>` of a page and make the script slow to arrive. The DOM stops growing at that tag. Nothing below it exists until the script has been fetched and executed. The model has parsing in one step and JavaScript in another, later step. In reality JavaScript is interleaved with parsing, and by default it blocks it.

**CSS arrives late and the page appears anyway, or does not.** A stylesheet that is slow to arrive will delay the first paint of a page even though the DOM is complete, because the browser refuses to paint content it does not yet know how to style. But a stylesheet with `media="print"` will not delay the paint at all. And a stylesheet added by a script after the page is visible will cause a re-style of nodes that already exist. The model says "fetch CSS, build CSSOM" as if it were a single step in a fixed position. It is not.

**Cached resources skip most of the path.** On a second visit, the HTML might come from the HTTP cache without any network at all. The DNS lookup might not happen because the resolution is still fresh. The TLS handshake might be a resumption rather than a full negotiation. The bundle might be served by a service worker from Cache Storage, which is a different cache from the HTTP cache, with different rules. The sequential model has one path; the real system has several, and which one a given resource takes depends on state that the page cannot see.

**HTTP/2 changes what "fetching CSS and JS" means.** In HTTP/1.1, the browser opens up to six connections per host and queues everything else. Two dozen resources means four rounds of six. In HTTP/2, one connection carries all of them as interleaved streams, with priorities the browser assigns and the server may or may not respect. The waterfall looks completely different, and the reason has nothing to do with the page and everything to do with the transport.

**A service worker intercepts the navigation.** If the origin has a registered service worker, the request for the HTML itself may never reach the network. A script the browser ran earlier, on a previous visit, gets to decide what the response is. The "HTTP request" step in the model is now optional.

**The user interacts while things are still loading.** The page has painted, the user sees a button, they click it. The bundle that attaches the click handler is still downloading. Nothing happens. Then the bundle arrives, executes, attaches the handler, and the second click works. From the user's point of view the page was "loaded" the moment they could see it. From the system's point of view it was not. The model has "display" as the last step, as though seeing pixels meant the work was done. Seeing pixels means the *rendering* work was done, once, for now.

Each of these breaks the model in the same direction. The real system overlaps, streams, speculates, caches, and re-does work. To understand it we need to stop thinking in sequences and start thinking in dependencies: what must happen before what, and, just as importantly, what does *not* have to wait.

That is the model we will build for the rest of the chapter. We will build it from the bottom, beginning with the URL.

## First Principles, Part One: From Name to Bytes

### The URL is not a string

The thing you typed is text. Before anything else can happen, the browser must decide what that text means, and this is less trivial than it sounds.

The URL standard, maintained by the WHATWG, defines a parser that takes a string and produces a structured record: a scheme, optional credentials, a host, an optional port, a path, an optional query, and an optional fragment. It also defines how to handle the enormous space of inputs that are not quite URLs. If you type `example.com/incidents`, there is no scheme; the browser's address bar, not the URL parser, decides that you probably meant `https://example.com/incidents` (or, in older browsers or specific configurations, `http://`). If you type `Incidents 2024`, that is a search, and no URL parsing happens at all until the search engine's address has been constructed. If you type `EXAMPLE.COM`, the host will be lowercased, because hosts are case-insensitive. If you type a hostname with characters outside ASCII, it will be converted to Punycode according to a set of rules that are themselves the subject of a separate standard, and the result is what actually goes to DNS.

Two pieces of this record matter more than the others for the rest of this chapter.

The first is the *scheme*. It determines which protocol handler is responsible for the rest of the process. `https:` and `http:` go to the network stack. `file:` goes to the filesystem. `blob:` and `data:` are resolved entirely within the browser. `javascript:` is not a fetch at all. We will spend this chapter on `https:`, but the fact that the scheme is a dispatch point, that different schemes have completely different lifecycles behind the same address bar, is worth holding onto.

The second is the *origin*. An origin is the tuple of scheme, host, and port. `https://atlas.example.com` and `https://atlas.example.com:443` are the same origin, because 443 is the default port for `https`. `http://atlas.example.com` is a different origin from `https://atlas.example.com`, because the scheme differs. `https://api.example.com` is a different origin from `https://atlas.example.com`, because the host differs, even though they share a registrable domain. The path is not part of the origin; `https://atlas.example.com/a` and `https://atlas.example.com/b` are the same origin.

We mention the origin here, long before we discuss security, because it is going to determine things you would not expect. It decides which process the page will run in, in browsers that isolate by site. It decides which cookies are sent. It decides whether a script on the page can read the response to a request. It decides which service worker, if any, will intercept the navigation. It decides which entries in the HTTP cache are reachable, because modern browsers partition their caches by the top-level site. The origin is computed from the URL before a single packet is sent, and a great deal of the subsequent behavior is a consequence of it.

*Assumption to notice:* we tend to think of the URL as an address. It is better thought of as a small program: a scheme that selects a handler, an origin that selects a security and storage context, and a path that the server will interpret however it likes.

### The name

The host in the URL is a name. Machines are reached by addresses. Something has to turn one into the other, and that something is the Domain Name System, which is old, distributed, cached at every level, and responsible for a surprising fraction of the latency that engineers attribute to "the server."

Suppose the host is `atlas.example.com`. The browser first checks its own cache: has it resolved this name recently? If not, it asks the operating system, which has its own cache and its own configuration. If the operating system does not know, it sends a query to a *recursive resolver*, which is typically run by your ISP, your corporate network, or a public service. The recursive resolver has a cache too. If the answer is not there, the resolver does the actual work of resolution, which is where the "recursive" part comes in.

The resolver begins with the root. There are thirteen root server addresses (each backed by many physical machines), and every resolver knows them. It asks a root server for `atlas.example.com`. The root server does not know, but it knows who is responsible for `.com`, and it says so. The resolver asks a `.com` server, which does not know either, but knows who is responsible for `example.com`. The resolver asks that server, the *authoritative* nameserver for `example.com`, which does know, and returns the address along with a *time to live*, a number of seconds for which the answer may be cached.

```
  browser cache ─miss→ OS cache ─miss→ recursive resolver cache ─miss→
                                                                       │
        ┌──────────────────────────────────────────────────────────────┘
        ▼
   root ──"ask .com"──▶ .com TLD ──"ask ns.example.com"──▶ authoritative
                                                                  │
        ◀──────────── answer: 203.0.113.42, TTL 300 ──────────────┘
```

Every one of those arrows is a network round trip. On a cold resolver, a name that has never been seen may cost three or four round trips before the browser learns an address, and each of those may go to a server on a different continent. On a warm resolver, the answer comes back in one round trip to the resolver, typically a few milliseconds. On a warm OS cache, it costs nothing at all. Three completely different latencies for the same operation, and the page has no way to know which it will get.

This is the first place the naive model's arrow hides a distribution. "DNS lookup" is not a step with a duration. It is a step whose duration depends on caches the page does not control, and which is frequently either nearly zero or surprisingly large.

The TTL is what makes the cache work and what makes it dangerous. A TTL of 300 means five minutes; a TTL of 86400 means a day. Short TTLs let an operator move a service to a new address quickly, at the cost of more lookups. Long TTLs reduce lookups but mean that when the address changes, some users will be sent to the old one for up to a day. When a company migrates infrastructure and a fraction of users see errors for hours afterward, DNS TTL is a common culprit, and the fact that the engineers doing the migration see the new address immediately, because their own caches were flushed, makes it a particularly confusing one.

Modern browsers also complicate the picture in two ways worth knowing. First, several of them can resolve names over HTTPS (DNS over HTTPS, or DoH) to a resolver of the browser's choosing, bypassing the operating system entirely; this changes which caches are consulted and whether your corporate network's DNS is used at all. Second, browsers speculatively resolve names before they are needed. Hover over a link, and Chrome may resolve its hostname. Add `<link rel="dns-prefetch" href="https://api.example.com">` to a page, and the browser will resolve that name early, so that when a script later calls `fetch("https://api.example.com/...")`, the lookup is already done. This is a heuristic, not a specification requirement, but it is a heuristic every major browser implements in some form.

*Assumption to notice:* we assumed a DNS lookup happens for every request. It happens for every request whose answer is not already cached, which in a warm session is almost none of them, and in a cold session on a fresh network is most of them. The same page has a different loading structure depending on which.

### The address, briefly

The resolver returns an IP address, and we will not go deeply into how packets find their way to it, because the browser does not care and mostly neither should you. But two things about addressing affect frontend engineering.

The first is that a name can have several addresses. A large service will return multiple A records (IPv4) and AAAA records (IPv6), and the browser must choose. Most modern browsers implement some version of "Happy Eyeballs," a strategy of attempting connections to more than one address, often preferring IPv6, and using whichever succeeds first. This means the "connect" step is itself sometimes a small race.

The second is that the address you get depends on where you are. Services that run on content delivery networks configure their DNS to return the address of a nearby edge server, and "nearby" is determined by the location of your resolver, not you. A user in Mumbai using a resolver in Frankfurt may be sent to a server in Frankfurt. This is one of the reasons that a CDN can be fast for most users and mysteriously slow for a specific population, and it is invisible from inside the page.

### The connection

The browser now has an address and a port. It needs a connection, and here the naive model's single word, "TCP," conceals a choice that has changed the shape of web loading twice in the last decade.

Begin with TCP, because it is the older path and the easier one to reason about. TCP provides a reliable, ordered byte stream over an unreliable network. Before any bytes can flow, the two sides must agree that a connection exists, and they do this with a three-way handshake: the client sends a SYN, the server replies with SYN-ACK, the client sends ACK. The client can send data with that final ACK, so the cost of establishing a TCP connection is one round trip. If the round-trip time to the server is 20 milliseconds, that is 20 milliseconds. If it is 200, it is 200.

Then, for `https`, comes TLS. TLS 1.3, which is what nearly all modern connections use, needs one additional round trip: the client sends its supported parameters and a key share, the server replies with its own key share, its certificate, and a signature, and from that point both sides have a shared secret and the client can send encrypted application data. Older TLS 1.2 needed two round trips. So a fresh HTTPS connection over TCP costs two round trips before the first byte of an HTTP request can leave the machine: one for TCP, one for TLS.

```
   client                              server
     │── SYN ─────────────────────────▶│
     │◀──────────────────── SYN-ACK ───│    1 RTT: TCP
     │── ACK ─────────────────────────▶│
     │── ClientHello (key share) ─────▶│
     │◀── ServerHello, cert, Finished ─│    1 RTT: TLS 1.3
     │── Finished + HTTP request ─────▶│
     │◀── HTTP response ───────────────│    1 RTT: request/response
```

During the TLS handshake the server presents a certificate, which is a signed statement, made by a certificate authority the browser trusts, that a particular public key belongs to a particular name. The browser checks that the name in the certificate matches the host it asked for, that the signature chain leads to a trusted root, that nothing in the chain has expired, and, by various mechanisms, that nothing has been revoked. We will treat certificates in more detail in Chapter 11. For now it is enough to know that this validation happens, that it is on the critical path, and that when it fails the user sees a full-page warning and the rest of this chapter does not happen.

One detail of the handshake is worth knowing because it is visible to anyone watching the network. The client sends the hostname it wants in the clear, in a field called Server Name Indication, so that a server hosting many sites on one address knows which certificate to present. This means that even with TLS, an observer on the path can see *which site* you are connecting to, though not what you say to it. Encrypted Client Hello is a newer extension that closes this gap, and its deployment is incomplete; whether it is used depends on the browser, the server, and the DNS configuration.

Now QUIC. QUIC is a transport protocol that runs over UDP rather than TCP and that folds the transport handshake and the TLS handshake into a single exchange. A fresh QUIC connection costs one round trip instead of two. If the client has connected to this server before, it can use a stored secret to send application data in its very first packet, at zero round trips, with some restrictions on what that data can be. HTTP/3 is HTTP over QUIC.

QUIC has a second property that matters even more than the faster handshake. In TCP, the bytes are one ordered stream, and if a packet is lost, everything after it must wait until it is retransmitted, even if the later bytes belong to a completely different resource. This is *head-of-line blocking*, and it means that under packet loss, HTTP/2's multiplexing of many resources over one TCP connection can become a liability: one lost packet stalls every stream. QUIC carries streams independently at the transport layer, so a lost packet stalls only the stream it belonged to. On a lossy mobile connection this is the difference between a page that degrades gracefully and one that freezes.

Which transport a given connection uses is not something the page controls. The server advertises HTTP/3 support through an `Alt-Svc` header or a DNS record, and the browser may try QUIC on the next connection, and may fall back to TCP if UDP is blocked, which on some corporate networks it is. From the page's point of view, the same URL loads over a different transport with a different latency profile depending on the network, the browser version, and whether the browser has visited before. Once again, one arrow in the naive model turns out to be a distribution.

*Assumption to notice:* we assumed a connection is a fixed cost. It is one round trip, two round trips, or zero round trips, depending on transport and history, and the round trip itself ranges from under a millisecond on localhost to a third of a second across an ocean.

### The request

With a connection established, the browser sends an HTTP request. For a navigation, it looks something like this, simplified:

```
GET /incidents HTTP/1.1
Host: atlas.example.com
Accept: text/html,application/xhtml+xml,...
Accept-Encoding: gzip, deflate, br
Accept-Language: en-US,en;q=0.9
Cookie: session=...
Sec-Fetch-Mode: navigate
Sec-Fetch-Dest: document
Upgrade-Insecure-Requests: 1
User-Agent: ...
```

The method says what the client wants done. The path says to what. The headers say how, and they are where the interesting negotiation happens. `Accept-Encoding` tells the server which compressions the client can decode, and a good server will send Brotli or gzip, reducing a 300 KB HTML document to 40 KB on the wire. `Accept-Language` is a hint the server may use to choose a locale. `Cookie` carries whatever the origin previously asked the browser to store, which is how the server knows who you are. The `Sec-Fetch-*` headers, added by the browser and unforgeable by scripts, tell the server what kind of request this is, which is useful for security decisions we will meet in Chapter 11.

In HTTP/1.1 these are literal text lines. In HTTP/2 and HTTP/3 they are compressed into a binary format, and repeated headers, like that enormous `User-Agent`, are sent once and referenced by index afterward. The semantics are the same. The bytes are not.

### The response

The server, having done whatever it does, responds:

```
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
Content-Encoding: br
Cache-Control: no-store
Content-Length: 41822
Date: Tue, 29 Sep 2026 03:37:11 GMT

<!doctype html>
<html lang="en">
...
```

The status line says what happened. The headers say how to interpret what follows. And then the body follows, and it is at this point, at the *first byte* of the body, that the naive model's next step begins. But we should stop on the status code, because the most common way for the naive model to be wrong about a navigation is for the status not to be 200.

A response with status 301, 302, 307, or 308 is a redirect. It carries a `Location` header and, usually, no useful body. The browser must now go back to the beginning: parse the new URL, possibly resolve a new name, possibly open a new connection to a new host, possibly perform a new TLS handshake, and send a new request. A single redirect from `http://` to `https://` on the same host costs at least one round trip plus a new TLS handshake, which is to say it can double the setup cost of the navigation. A redirect chain of three, which is not unusual for pages behind marketing tooling or authentication, can cost a second on a slow link before any HTML has been seen.

Redirects are almost invisible from inside the page. `location.href` shows the final URL. The Navigation Timing API, which we will meet shortly, exposes `redirectCount` and `redirectStart`/`redirectEnd`, but only for same-origin redirects; cross-origin ones are hidden for privacy reasons, so the time simply vanishes into an unexplained gap before `fetchStart`. If you have ever seen a page whose "time to first byte" is inexplicably large and whose server logs show fast responses, ask whether the browser made more than one request.

The status codes 304 and, more recently, 103 also matter. A 304 Not Modified is the server's answer to a conditional request: the client said "I have a copy with this validator; is it still good?" and the server said yes, and sent no body. We will come to it under caching. A 103 Early Hints is an *interim* response the server can send before the real one, containing `Link` headers that tell the browser which resources to start fetching while the server is still generating the HTML. It exists precisely because server processing time is on the critical path and the browser would otherwise be idle during it. Support is not universal, and it only helps when the server knows what the page will need before it knows what the page will be, but where it applies it removes a dependency from the graph, and removing dependencies is the theme of this chapter.

### Caching, the first pass

Before we leave the network, we need to establish something the naive model omits entirely: the request we just described may never have been sent, and the response may never have come from the server.

The browser maintains an HTTP cache, keyed (in modern browsers) by the request URL together with the top-level site that made the request, so that a resource cached by one site cannot be observed by another. When a request is about to be made, the cache is consulted. What happens next depends on the headers the *previous* response carried.

If the cached response has a `Cache-Control: max-age=N` and fewer than N seconds have passed since it was stored, the response is *fresh*, and the browser uses it without contacting the server. No DNS, no connection, no request. The resource's timeline in a waterfall shows a few microseconds of disk read and nothing else.

If the cached response is *stale*, because its `max-age` has elapsed, or because it carried `no-cache`, which despite its name means "store, but revalidate before use," the browser may send a conditional request. It includes `If-None-Match` with the `ETag` the server sent previously, or `If-Modified-Since` with the previous `Last-Modified`. If the server still has the same representation, it replies 304 with no body, and the browser uses its cached copy, having spent a round trip but no transfer. If the representation changed, the server sends 200 with the new body.

If the response carried `no-store`, it was never cached at all.

If the response carried none of these, the browser applies a *heuristic*: it may treat the response as fresh for some fraction of the time since its `Last-Modified` date, typically ten percent. This is specified as permitted, not required, and browsers differ in the details. It is the source of a great many "why is the user seeing the old version" bugs, because the server never said the response could be cached, and the browser cached it anyway.

We will treat caching properly in Chapter 7, where the question becomes not just "is this fresh" but "is this consistent with what the user just did." For now the point is structural. Every resource on the page may take one of three network paths: none (fresh in cache), a round trip with no body (revalidated), or a full transfer. The same page on the same machine has a different dependency graph on its first load and its second, and a different one again after `max-age` has elapsed. When we analyze Atlas's loading later in this chapter, we will have to do it three times.

### Connection reuse and multiplexing

One more thing about the network, and it is the one that most changes what a waterfall looks like.

The first request on a connection pays for the connection. Subsequent requests can reuse it. In HTTP/1.1, a connection carries one request at a time: the client sends a request, waits for the full response, then sends the next. To get concurrency, browsers open several connections per host, and the conventional limit is six. A page with thirty resources from one host loads them six at a time, in five waves, each wave taking at least one round trip. Engineers of the HTTP/1.1 era learned to shard resources across multiple hostnames to get more connections, and to concatenate files to need fewer requests, and both of those techniques became harmful the moment the transport changed.

In HTTP/2, one connection carries many concurrent *streams*, interleaved at the frame level. The client can send thirty requests immediately and receive thirty responses in whatever order the server produces them, all on one connection. The six-connection limit is gone, the handshake cost is paid once, and the shape of the waterfall changes from stair steps to a set of overlapping bars that all begin at nearly the same moment.

```
HTTP/1.1, one host, 6 connections:

  a.js   ████████
  b.js   ████████
  c.css  ████
  d.png  ██████
  e.png  ██████
  f.js   ████████
  g.js           ████████        ← waited for a free connection
  h.png          ██████
  ...

HTTP/2, one connection:

  a.js   ████████████
  b.js   ████████████
  c.css  ██████
  d.png  ████████████
  e.png  ████████████
  f.js   ████████████
  g.js   ████████████            ← all begin at once, share bandwidth
  h.png  ████████████
```

Notice that in the HTTP/2 diagram each bar is *longer*. Thirty resources sharing one connection share its bandwidth, and if they are all sent at once, each arrives more slowly than it would alone. This is where prioritization enters. The browser attaches a priority to each request based on what kind of resource it is and where it was found. A stylesheet in the head is highest; a script in the head is high; an image in the viewport is medium; an image far below the fold is low. The server, if it honors priorities, sends the important bytes first. Whether the server honors them is an implementation detail of the server, and for years many did not, which is why HTTP/2 sometimes made pages slower than a well-tuned HTTP/1.1 setup. HTTP/3 carries a simplified priority scheme that servers are more likely to respect.

The page can influence priorities. `<link rel="preload">` tells the browser to fetch a resource early and at the priority appropriate to its type. The `fetchpriority` attribute on `<img>`, `<link>`, and `<script>`, and the `priority` option to `fetch()`, let the page say "this one matters more than the browser would guess" or "this one matters less." These are hints. The browser's own heuristics, the server's scheduling, and the state of the network all have a say.

*Assumption to notice:* we assumed network requests run sequentially. They run concurrently, up to a limit that depends on the protocol, and they compete for bandwidth in an order the browser and server negotiate.

## An Interlude on Latency, Sums, and Critical Paths

We have now seen enough of the network to write down the equation the naive model implies:

```
T_navigation ≈ T_DNS + T_connect + T_TLS + T_request
             + T_server + T_transfer + T_processing
```

This is a useful equation. It names the components, and each of them can be measured separately, and when a page is slow the first question is which term is large. With a cold cache and a distant server, plausible values might be: DNS 60 ms, TCP 100 ms, TLS 100 ms, request in flight 50 ms, server 200 ms, transfer 150 ms, processing 300 ms, for a total of around 960 ms before the page is usable.

And it is wrong, in an instructive way. It is wrong because it assumes each term must finish before the next begins, and the entire lesson of this chapter is that they do not. Processing begins during transfer, because the parser is streaming. Transfer of subresources begins during processing, because the preload scanner finds them early. The connection for the API may be opened during the HTML transfer, because the page hinted it. On a second visit, DNS and TLS may be nearly zero. The sum overstates the time, sometimes by a lot.

The right way to think about it is as a *graph* of tasks with dependencies, where each task has a duration and cannot begin until the tasks it depends on have finished. The total time is then not the sum of all durations but the length of the longest dependency chain through the graph. That chain is the *critical path*. Work that is not on the critical path can be made arbitrarily faster without changing the total. Work that is on it determines the total directly.

Here is a small example. Suppose the HTML takes 300 ms to arrive, the stylesheet 200 ms, the bundle 400 ms, and the first API call 250 ms, and suppose the API call cannot begin until the bundle has executed, and rendering cannot begin until stylesheet and DOM are ready, and the interface cannot be usable until the API data has arrived. If all four resources were discovered at the start, the naive sum is 1,150 ms. But the stylesheet and bundle can download in parallel with the tail of the HTML, so the picture looks more like this:

```
time →   0         300       500       700       950
HTML     ██████████
CSS         ████████
bundle      ████████████████
API                          ██████████
                                       ▲ usable at ~950 ms
```

The critical path is HTML-start → bundle → API → usable, and it is 950 ms, not 1,150. The stylesheet is not on the critical path; making it twice as fast changes nothing. Making the bundle 100 ms faster saves 100 ms. Making the API call begin *before* the bundle finishes, by hinting it from the HTML, could save 400 ms, which is more than any optimization of the bundle itself could achieve.

That last move, restructuring the graph rather than shrinking a node, is the most powerful kind of performance work, and it is invisible to anyone who thinks in sums. We will use critical-path reasoning throughout the book, in rendering, in data fetching, in build systems, and in organizational planning, because it applies to any system where work has dependencies. Which is every system.

Two cautions before we move on. First, the critical path is not fixed. Change the network and a different chain may become longest; on a fast connection the bundle's *execution* may dominate, on a slow one its *transfer*. Second, the critical path is only visible once you have the graph, and the graph is only visible once you have understood the dependencies, which is why the rest of this chapter is about the dependencies inside the browser.
## Inside the Platform

Up to this point we have spoken of "the browser" as though it were one program. It is not, and the way it is divided explains a good deal about how pages behave.

Every major browser today is a multi-process system. The exact division differs by engine and is an implementation detail, but the shape is similar enough across Chromium, Firefox, and WebKit that we can describe it once and note the differences.

There is a *browser process* (Chromium's term; Firefox calls it the parent process). It owns the user interface: the tabs, the address bar, the bookmarks, the back button. It owns the storage: cookies, the HTTP cache, IndexedDB, and so on. It coordinates everything else, and it is the only process trusted to talk to the operating system on the user's behalf.

There is a *network service*, which may be a thread in the browser process or a process of its own. It owns the sockets. It performs DNS resolution, opens connections, runs the TLS handshakes, speaks HTTP in its several versions, and consults the cache. Everything we described in the previous section happens here. Renderers do not have sockets; they ask the network service for resources and receive bytes back over inter-process communication.

There are *renderer processes*, one or more. A renderer takes bytes of HTML, CSS, and JavaScript and turns them into a document and, eventually, into a description of what to draw. The parser, the DOM, the style engine, the layout engine, and the JavaScript engine all live here. A renderer is where untrusted content runs, and so it is *sandboxed*: it has no direct access to the filesystem, the network, or most of the operating system. If a malicious page finds a bug in the JavaScript engine and takes control of the renderer, it is in a process that cannot, on its own, do anything harmful. It must ask the browser process, which checks.

There is a *GPU process* (or in Chromium's current architecture, a display compositor called Viz that lives there). It takes the layer descriptions produced by renderers and turns them into pixels on the screen using the graphics hardware. It is separate because graphics drivers crash, and it is better for a crashed GPU process to be restarted than for the whole browser to die.

And there are various *utility processes* for things like audio, storage, and extensions, which we can ignore.

```
   ┌─────────────────────────────────────────────────────────┐
   │  Browser process                                        │
   │  UI · storage · navigation · permissions · coordination │
   └───┬──────────────────┬───────────────────┬──────────────┘
       │ IPC              │ IPC               │ IPC
   ┌───▼─────────┐   ┌────▼───────────┐   ┌───▼──────────┐
   │ Network     │   │ Renderer       │   │ GPU / Viz    │
   │ service     │   │ (sandboxed)    │   │              │
   │ DNS · TLS   │   │ parse · DOM    │   │ raster       │
   │ HTTP · cache│   │ style · layout │   │ composite    │
   │ sockets     │   │ JS · paint     │   │ display      │
   └─────────────┘   └────────────────┘   └──────────────┘
                        (one per site,
                         in isolating browsers)
```

How pages are assigned to renderers is where the browsers differ most, and where the origin we computed at the very beginning comes back. Chromium, since 2018, implements *site isolation*: pages from different sites go in different renderer processes, always, and a cross-site iframe runs in a different process from its parent. Firefox has a similar system called Fission. WebKit on macOS and iOS isolates less aggressively, partly because of memory constraints on mobile devices. The reason for isolation is that a renderer's memory can be read by a sufficiently clever exploit, and the Spectre class of hardware vulnerabilities in 2018 made "sufficiently clever" much less clever than it had been. If a bank's page and an attacker's page share a process, the attacker may be able to read the bank's page. If they do not, it cannot.

Within a renderer there are threads, and one of them matters more than the others. The *main thread* runs the parser, builds the DOM, computes style, performs layout, runs JavaScript, and dispatches events. It does all of these one at a time. That serialization is why a long-running script freezes a page; the same thread that would repaint or handle the click is busy. The *compositor thread* takes the layers the main thread produced and can scroll and animate them without the main thread's involvement, which is why scrolling usually stays smooth even when a script is running. *Raster threads* turn paint commands into bitmaps. *Worker threads* run web workers, which have their own JavaScript heaps and cannot touch the DOM. We will make heavy use of the compositor thread's independence in Chapter 2 and of workers in Chapter 3; for now, hold onto the idea that "the page is frozen" almost always means "the main thread is busy," and that some things, notably scrolling and certain animations, can survive a busy main thread while others, notably clicks, cannot.

This is a good moment to name the teaching simplification we are making. The description above is closest to Chromium's architecture, because Chromium's is the most extensively documented and the one whose DevTools most readers use. Firefox and WebKit make different choices about what goes in which process and what the threads are called. The *principles*, that network and rendering are separated, that untrusted content is sandboxed, that a single main thread serializes parsing and scripting and layout, and that compositing is offloaded, hold across all of them.

### The navigation lifecycle

We can now put the network and the processes together and describe what actually happens when you press Enter, at the level of who does what.

The browser process receives the input, parses the URL, and decides it is a navigation. It may consult a service worker registration for the origin; if one exists and has a `fetch` handler, the request will be routed through it, and the worker's script decides whether to answer from a cache or go to the network. Otherwise, the browser process asks the network service to fetch the URL. This is the point at which everything in "From Name to Bytes" happens.

The response headers arrive first. The browser process reads them and makes several decisions before the body is touched. It decides, from `Content-Type`, whether this is an HTML document to render or a file to download. It reads security headers, `Content-Security-Policy` among them, that will govern the page. It determines the origin and the site, and from those it selects or creates a renderer process. Only then does it hand the response body, still streaming, to that renderer and tell it to begin.

This has a consequence people find surprising: the renderer that will display the page may not exist until after the response headers have arrived, and the previous page is still visible until the new document *commits*, which happens shortly after the renderer accepts the response. That is why, when you navigate to a slow server, the old page stays on screen with a spinner in the tab, and then, when headers finally arrive, the old page is replaced. The browser does not show a blank page while waiting, because showing nothing is worse than showing the past.

There is one more thing the browser process may do at this moment, and it is a heuristic rather than a rule. When you press Enter, before any response has arrived, Chromium may already be creating a renderer process on speculation, so that it is warm by the time the headers show up. And when you begin typing in the address bar, it may resolve the name of the site it predicts you will visit, and open a connection to it, and in some configurations *prerender* the page in a hidden renderer. If you then press Enter, the navigation is nearly instant, not because anything got faster but because the work was done before you asked. The Speculation Rules API lets pages request this behavior for links they expect the user to follow. All of this is invisible to the page and to the naive model, and it is a good example of why measured navigation times have such wide distributions: some of the population got a head start.

## First Principles, Part Two: From Bytes to a Tree

### Streaming, tokenization, and the tree

The renderer receives HTML as a stream of bytes. The first thing it must do is decide what encoding they are in, which is less obvious than it sounds; the encoding may be declared in the `Content-Type` header, or in a `<meta charset>` tag within the first kilobyte, or, failing both, guessed from the bytes themselves. Assuming UTF-8, which you should always declare so that the browser does not have to guess, the bytes become characters.

The characters go to the *tokenizer*, a state machine defined in exhaustive detail by the HTML standard. It emits tokens: start tags with their attributes, end tags, text, comments, the doctype. It does this incrementally. It does not need the whole document; it needs the next character. When it reaches the end of the bytes it has, it waits.

The tokens go to the *tree builder*, another state machine, which turns them into DOM nodes and inserts them into a tree. The tree builder is where HTML's famous error tolerance lives. If you open a `<p>` and then open a `<div>` without closing the paragraph, the tree builder closes it for you. If you put a `<td>` outside a table, it may create the table. If you nest tags improperly, it will produce *some* tree, and the standard specifies exactly which one, so that every browser produces the same tree from the same broken markup. This was one of the great achievements of the HTML5 standardization effort. Before it, each browser had its own tolerance, and a page that rendered in one might collapse in another.

Both machines are streaming. The DOM grows as bytes arrive. The first hundred nodes of a document can exist, be styled, be laid out, and be painted while the last thousand are still being transmitted.

```
time →
bytes    ▐██▌▐██▌▐██▌▐██▌    ▐██▌▐██▌           ▐██▌▐██▌▐██▌
         (network chunks; gaps are waiting)

tokens   ─┬──┬──┬──┬──┬──┬────┬──┬──┬───────────┬──┬──┬──┬──
DOM      ▲ grows                 ▲ grows               ▲ grows
                                                               ▲ complete
```

This is the first place the naive model's "HTML → DOM" arrow dissolves into something continuous. And there is an experiment you can do to see it. Later in this chapter we will write a tiny server that sends the top of a page, sleeps for two seconds, and then sends the rest; you will watch the top render while the rest is in transit. Before we get there, we need to understand two things that interrupt the stream.

### The script that stops the world

Consider this document.

```html
<!doctype html>
<html>
<head>
  <script>
    console.log(document.body);
  </script>
</head>
<body>
  Hello
</body>
</html>
```

What does the script log? Commit to an answer before reading on.

It logs `null`. When the script runs, the tokenizer has emitted the tokens up to and including `</script>`, the tree builder has built the head and the script element, and the parser has *stopped*. The body does not exist yet because the parser has not reached it. The script sees a document with a head and nothing else.

Now move the script.

```html
<!doctype html>
<html>
<body>
  Hello
  <script>
    console.log(document.body);
  </script>
</body>
</html>
```

Now it logs the body element, whose text content is `"Hello"` and some whitespace. The parser reached the body, created it, added the text, reached the script, and stopped. The script sees everything before it and nothing after.

This is the fundamental rule, and it is worth stating precisely. When the parser encounters a `<script>` element without `async`, `defer`, or `type="module"`, it stops building the tree, fetches the script if it is external, waits for it to arrive, executes it, and only then resumes. The script can see every node created before it and can use `document.write` to insert markup at its own position, which the parser will then process as though it had been in the source. Because the script *might* do that, the parser cannot safely proceed past it. This is the historical reason for the blocking: `document.write` was one of the earliest ways to generate dynamic content, and its semantics require that the document be in a known state at the moment the script runs. The web is still paying for that decision.

The cost is severe when the script is external. The parser stops at the tag, the network service fetches the script, and nothing below the tag exists until the bytes have arrived and run. On a slow connection, a single external script in the `<head>` can delay the appearance of the entire page by hundreds of milliseconds, during which the browser has the rest of the HTML sitting in a buffer and is not allowed to look at it.

Except that it does look at it. The parser proper is blocked, but browsers run a second, lightweight scanner ahead of it, the *preload scanner* (or speculative parser), which tokenizes the buffered HTML without building a tree and looks for things that will need fetching: scripts, stylesheets, images, fonts declared in `<link>`, and so on. It starts those fetches immediately. When the real parser eventually reaches those tags, the resources are already in flight or already arrived. The preload scanner is a heuristic, not a specification requirement, but every major engine has one, and it is the single most important reason that a page with a blocking script in the head is not as slow as the rule above implies. It also has a well-known blind spot: it can only find resources that appear as markup. Resources whose URLs are constructed by JavaScript, or referenced in CSS, or loaded by an import inside a module, are invisible to it, and the parser (or the script) must discover them the slow way.

*Assumption to notice:* we assumed downloaded JavaScript executes immediately. A parser-blocking script does execute as soon as it arrives. But a script that arrived early because the preload scanner found it still waits for the parser to reach its tag, because execution order must match document order. Download and execution are separate events with separate dependencies.

### Async, defer, and modules

Because the default is so costly, the platform offers three ways to opt out of it.

`<script defer src="...">` tells the parser: fetch this now, do not wait for it, keep going, and run it after the document has been completely parsed, in the order the defer scripts appeared, but before the `DOMContentLoaded` event. Deferred scripts see the whole DOM. They run in order. They cannot use `document.write` meaningfully, because the document is finished.

`<script async src="...">` tells the parser: fetch this now, keep going, and run it as soon as it arrives, whenever that is, stopping the parser briefly if the parser happens to be running at that moment. Async scripts run in arrival order, not document order, and they may run before or after `DOMContentLoaded` depending on the network. They are appropriate for scripts that do not depend on the DOM or on each other: analytics, for example.

`<script type="module" src="...">` behaves as though `defer` were set, by default. It also has its own dependency graph: a module can `import` other modules, and the browser fetches the whole graph before executing any of it, in dependency order. Adding `async` to a module script makes it execute as soon as its graph is ready rather than waiting for the parser. Modules are also strict mode, have their own scope, and are fetched with CORS, all of which we will come back to in Chapter 14.

```
            fetch                     execute
default     ─────┐                    │
  parser    ═════╪════ blocked ═══════╪═════════════════▶
            ─────┘  (script arrives)  └── runs, then parser resumes

defer       ─────┐
  parser    ═════╪══════════════════════════════════════╡ end of parse
                 └──────── fetched in parallel ─────────┘ then run (in order)
                                                          then DOMContentLoaded

async       ─────┐
  parser    ═════╪═════════════╪════════════════════════▶
                 └── fetched ──┘ runs immediately on arrival (order unknown)
```

Here is the earlier example a third time.

```html
<!doctype html>
<html>
<head>
  <script defer src="log-body.js"></script>
</head>
<body>
  Hello
</body>
</html>
```

If `log-body.js` contains `console.log(document.body)`, what does it log, and why does moving the script back to the head no longer matter?

It logs the body, because deferred execution happens after parsing is complete. The position of the tag now affects only *when the fetch begins*, which is why the head is actually the best place for a deferred script: the fetch starts as early as possible and the execution happens as late as necessary.

A small warning about inline scripts. `defer` and `async` have no effect on a `<script>` with inline content; the attributes are ignored and the script runs immediately, blocking the parser. This is specified behavior, and it surprises people regularly. A `<script type="module">` with inline content, on the other hand, *is* deferred.

### CSS: what "render-blocking" actually means

Now the second interruption, which is subtler than the first because it does not stop the parser. It stops something else.

Consider a document with a stylesheet in its head.

```html
<head>
  <link rel="stylesheet" href="app.css">
</head>
<body>
  <h1>Incidents</h1>
  <script>
    console.log(getComputedStyle(document.querySelector("h1")).color);
  </script>
</body>
```

Suppose `app.css` is slow. What does the browser do?

The parser does not stop at the `<link>`. The stylesheet is requested, and parsing continues. The `<h1>` is created. And then the parser reaches the inline script, and here it *does* stop, and it stops for a reason that has nothing to do with the script's own fetch: the script might read computed style, as this one does, and the computed style depends on `app.css`, which has not arrived. So the browser waits for the stylesheet before running the script. The standard describes this as the script waiting for pending stylesheets that precede it; the effect is that a slow stylesheet blocks every script after it in the document, even inline ones, even ones that never touch style.

Take the script away. The parser finishes the document. The DOM is complete. Can the browser paint?

Not yet. The browser will not paint content whose style it does not know, because painting it unstyled and then repainting it styled would produce a visible flash of wrongly styled content, which browsers of the late 1990s did produce and which everyone agreed was worse than waiting. So *rendering* waits for the stylesheet. That is what "render-blocking" means. It does not block parsing. It does not block the DOM. It blocks the first paint, and it blocks scripts that come after it.

Now, three complications, each of which turns a rule into a mechanism.

First, what if the stylesheet has a media attribute that does not match? `<link rel="stylesheet" href="print.css" media="print">` on a screen. The browser still fetches it, at low priority, because the media might change. But it does not block rendering, because the browser knows the rules will not apply. The same is true of `media="(max-width: 600px)"` on a wide viewport. This means you can split a stylesheet by media and pay the render-blocking cost only for the part that applies. (A stylesheet whose media *does* match blocks rendering just like one with no media attribute.)

Second, what if the stylesheet is added *after* the page is visible, by a script inserting a `<link>` into the head? The DOM already exists. The page has already painted. When the new stylesheet arrives, the browser recomputes style for every affected node, re-lays out whatever changed, and repaints. If the sheet changes the size of things, the page jumps. This is the same machinery as the first render, run again, and it has a name in the performance literature, layout shift, that we will meet later.

Third, what does a stylesheet block, exactly, in a streaming document? In most engines, the answer depends on where the stylesheet is. A `<link>` in the head blocks the painting of the whole document. A `<link>` in the body, in Chromium and in WebKit, blocks the painting of content *after* it but allows content before it to render. Firefox historically blocked the whole document regardless of position, and its behavior has changed over time. This is one of those places where the specification says relatively little, the engines have converged on similar behavior for different reasons, and any precise claim should be tested against the browsers you care about.

There is one more subtlety about CSS that the naive model gets exactly backwards. Its diagram has CSS and JavaScript as independent branches. They are not. A stylesheet blocks the scripts after it. A parser-blocking script blocks the discovery of stylesheets after it (except by the preload scanner). Change the order of a `<link>` and a `<script>` in the head and you change the dependency graph.

```
   <link rel=stylesheet href=a.css>      <script src=b.js>
   <script src=b.js>                     <link rel=stylesheet href=a.css>

   a.css ████████                        b.js  ██████
   b.js  ████                            a.css       ████████  (found by
         └── b.js waits for a.css              │              preload scanner,
             before executing                  │              but the parser
                                               └── parser blocked here,
                                                   so <link> tag reached late)
   first paint after a.css AND b.js      first paint after b.js AND a.css
```

In this particular case the totals may be similar. But add a third script, or a font, or an image, and the two orderings produce different critical paths. The rules are simple; the graph they produce is not, and you have to draw it.

### Fonts, images, and the things that do not block

Not everything on the page participates in blocking. Images do not block parsing, style, layout (a `<img>` without dimensions gets laid out at zero size and then re-laid out when the image arrives, which is a different problem), or paint. Fonts are stranger: the browser lays out text with the font it knows, and when a web font arrives, it may re-lay out and repaint, or it may have been showing invisible text until then, depending on the `font-display` descriptor. We will spend real time on fonts in Chapter 2. The point for now is that the loading of a page is not one event. Content appears, then changes, then changes again, and each change is a paint, and the user experiences the sequence.

### DOMContentLoaded and load

Two events mark milestones in this process, and it is worth being exact about what they mean, because they are often used to mean something else.

`DOMContentLoaded` fires on the document when the parser has finished the HTML and all deferred scripts (and module scripts) have executed. It does *not* wait for stylesheets, unless a script was waiting for them, in which case it waits for the script. It does not wait for images. It does not wait for async scripts. It does not wait for fonts. It means: the tree is complete and the scripts that promised to run after the tree is complete have run.

`load` fires on the window when the document *and all its subresources* have loaded: every image, every stylesheet, every script, every iframe, every font that was requested during parsing. It is the older event, and for years it was what people meant by "the page has loaded." For a modern application it is nearly meaningless, because it can fire long after the user has begun interacting and long before the application has fetched its data, or it can be delayed indefinitely by a single slow image in a footer.

Neither event tells you when the page was *visible*, which is the thing users care about. For that you need the paint timings, which we will meet under measurement.

```
parser ═══════════════════════════════╡
deferred scripts                        ██
                                          ▲ DOMContentLoaded
images   ████████████████████████████████████████
fonts          ████████████
async    ██████████
                                                  ▲ load
```

## First Principles, Part Three: From Tree to Pixels

We now have a DOM and a CSSOM. The naive model says "render tree, layout, paint, display." Each of those words is hiding a stage, and the stages are more numerous, more separable, and more frequently re-run than the model suggests. We will describe them once, in order, and then in Chapter 2 we will spend a great deal more time in each.

**Style.** For each element in the DOM, the browser determines which CSS rules match it, resolves the cascade to find the winning value for every property, and computes the final value, resolving `em` to pixels, `inherit` to the parent's value, and so on. The output is a computed style per element. This is proportionate to the number of elements times the complexity of the selectors, and on a large document with expensive selectors it can take tens of milliseconds. It also produces the *render tree*, or in modern engines a *layout tree*: a tree of boxes that omits elements with `display: none`, adds pseudo-elements, and splits text into runs.

**Layout.** For each box, the browser computes geometry: position and size. This is where the formatting contexts of CSS do their work: block layout stacks boxes, inline layout flows text into lines, flexbox and grid distribute space. Layout is expensive and, critically, it is *global-ish*: changing one element's width can change the height of everything below it. Engines work hard to limit layout to the subtree that changed, and there are CSS properties (`contain`, `content-visibility`) whose purpose is to help them.

**Paint.** For each box, the browser generates a list of drawing commands: fill this rectangle with this color, draw this text with this font at this position, clip here, apply this shadow. The output is not pixels; it is a *display list*, an ordered set of instructions. Paint order is determined by stacking contexts and z-index, which is why those concepts are more than a nuisance.

**Layerize (or compositing assignment).** The browser decides which parts of the display list should be drawn into separate *layers*: rectangular bitmaps that can be moved, scaled, and faded independently of each other. Anything that will animate with `transform` or `opacity`, anything with `will-change`, anything that scrolls independently, and a handful of other cases get their own layer. Everything else shares the root layer. Too few layers means animation requires repainting; too many means memory exhaustion. The heuristics for this are among the least stable across engines and versions.

**Raster.** Each layer's display list is executed to produce actual pixels, typically on the GPU, typically in tiles so that a large layer need not be rasterized all at once. This happens on raster threads, not the main thread. When you scroll quickly and see a blank region that fills in a moment later, you are seeing tiles that were not yet rasterized.

**Composite and display.** The compositor takes the rasterized layers, applies their transforms and opacities, and draws them in order into a frame buffer, which the display then shows. This stage runs on the compositor thread and, in Chromium, in the Viz process. It is the reason that a `transform` animation stays smooth while the main thread is busy: the compositor can move an already-rasterized layer without asking the main thread for anything.

```
   DOM ─┐
        ├──▶ Style ──▶ Layout ──▶ Paint ──▶ Layerize ──┐  (main thread)
  CSSOM ┘                                              │
                                                       ▼
                                          Raster (raster threads / GPU)
                                                       │
                                                       ▼
                                          Composite (compositor / Viz)
                                                       │
                                                       ▼
                                                    Display  (vsync, ~60–120 Hz)
```

Two things about this pipeline change how you think about the page.

The first is that it is not run once. It is run every time something changes, and the cost depends on *how far up the pipeline the change enters*. A change to `transform` on a layered element enters at composite; it costs almost nothing. A change to `background-color` enters at paint; it requires re-rasterizing that layer but not re-laying out. A change to `width` enters at layout; it may re-lay out a large subtree and repaint all of it. A change that adds a stylesheet enters at style, for everything. The pipeline is a ladder, and cheap changes are the ones that skip rungs.

The second is that the whole thing is paced by the display. A monitor refreshing at 60 Hz wants a new frame every 16.7 milliseconds. The browser tries to produce one on that schedule, and everything the main thread does, JavaScript included, has to fit into the gaps. When it does not, frames are dropped, and the user sees jank. We will make this precise in Chapter 3, when we meet the event loop and its rendering opportunity, and in Chapter 9, when we measure it.

*Assumption to notice:* we assumed rendering happens once. It happens continuously, in stages of varying cost, and "the page has rendered" is not a state but a moment in an ongoing process.

## First Principles, Part Four: From Input to the Next Frame

The user sees the page and moves the mouse over an incident row and clicks. What happens?

The operating system delivers the click to the browser process, which knows which tab is focused and forwards the event to the appropriate renderer. In modern engines it does not go straight to the main thread. It goes first to the compositor thread, which asks a question: can I handle this without the main thread? For a scroll wheel event on a region with no scroll listeners, the answer is often yes, and the compositor scrolls the layer immediately, which is why scrolling stays smooth during heavy JavaScript. For a click, the answer is no; something on the main thread needs to decide what was clicked and run whatever handlers exist. So the event is queued for the main thread.

When the main thread gets to it, the first job is *hit testing*: given a point in the viewport, which element is under it? This is a walk of the layout tree, in reverse paint order, checking each box's geometry, respecting clipping, `pointer-events`, and stacking. The result is the *target*. Hit testing requires up-to-date layout, so if something has changed since the last frame, the browser may have to run style and layout first, before it can even decide who receives the click.

Then comes *dispatch*. The event travels from the root of the document down to the target (the capture phase), fires on the target, and travels back up (the bubble phase), invoking listeners at each step. A listener may call `preventDefault()`, which suppresses the *default action*: following the link, submitting the form, toggling the checkbox. The default action runs after dispatch, if it was not prevented. Chapter 5 will spend real time here, because forms and focus and accessibility all live in this machinery.

The listener, being application code, changes something: it sets state, the framework updates the DOM, a class is added, a row is highlighted. That DOM change invalidates style, and possibly layout, and paint. Nothing is drawn yet. The change is drawn at the next *rendering opportunity*, when the browser decides it is time to produce a frame, at which point it runs the pipeline from wherever the changes entered it and hands the result to the compositor, which produces the frame, which the display shows at its next refresh.

```
  OS input ──▶ browser process ──▶ compositor thread
                                       │ "needs main thread?"
                                       ▼ yes
                                   main thread queue
                                       │
                                   (style/layout if dirty)
                                       │
                                   hit test ──▶ target
                                       │
                                   dispatch: capture → target → bubble
                                       │
                                   listeners run, DOM mutated
                                       │
                                   default action
                                       │
                          … wait for rendering opportunity …
                                       │
                                   style ─ layout ─ paint ─ layerize
                                       │
                                   commit to compositor ──▶ raster ──▶ frame
                                                                        │
                                                                     display
```

The time from the click to the frame that shows its effect is what users perceive as responsiveness, and it has three components that can each dominate. The *input delay* is the time the event sits in the queue before the main thread gets to it; if a script is running, this can be hundreds of milliseconds, and it is the number-one cause of "I clicked and nothing happened." The *processing time* is the listener itself. The *presentation delay* is the rendering work after the listener plus the wait for the next frame. The Event Timing API exposes all three, and Interaction to Next Paint, the metric built on it, is how the industry now summarizes them. We will use it in Chapter 9.

*Assumption to notice:* we assumed seeing pixels means the application is ready. The user can click a visible button while the handler that would respond to it has not been attached, or while the main thread is too busy to dispatch the event. Visible and interactive are different states, and the gap between them is where a large fraction of frontend frustration lives.

## The Whole Graph

We have now walked the entire path, and it is time to draw what the naive model could not: the dependency graph, with concurrency made visible.

```
 URL parse ─ origin
   │
   ▼
 DNS ─▶ connect ─▶ TLS ─▶ request ─▶ headers ─▶ renderer chosen
 (each may be skipped: cache, resumption, speculation)  │
                                                        ▼
                        HTML body streams in ═══════════════════════▶
                          │
   ┌── preload scanner ───┼──▶ CSS fetch ──┐  JS fetch ──┐  font/img fetch
   │                      ▼                │             │
   │           tokenize ─▶ tree build ═════╪═════════════╪═══▶ DOM complete
   │                          ║            │             │          │
   │        parser blocks ────╢◀───────────┼── sync script runs     │
   │        at <script>       ║            │   (waits for earlier   │
   │                          ║            ▼    CSS)                ▼
   │                          ║       CSSOM ready          deferred scripts run
   │                          ▼            │                        │
   │                 style ─▶ layout ─▶ paint ─▶ layerize      DOMContentLoaded
   │                 (needs DOM so far + all blocking CSS)
   │                                       │
   │                                       ▼
   │                          raster ─▶ composite ─▶ FIRST PAINT
   │                                                     │
   └── images, fonts, async scripts arrive ─▶ re-style / layout / paint …
                                                         │
 app script runs ─▶ fetch(API) ─▶ (new origin? DNS/connect/TLS again)
                                     ─▶ data ─▶ render UI
                                                         │
 user input can arrive at any point after first paint ◀──┘
 (handled only when the main thread is free and handlers exist)
```

Read this diagram not as a sequence but as a set of constraints. Solid dependencies are few: you cannot tokenize bytes you do not have, cannot paint without the blocking stylesheets, cannot run a deferred script before the parse is done, cannot dispatch a click without hit testing. Everything else is free to overlap, and the browser overlaps it aggressively. The double lines are the stream; the parser runs along it, and things branch off as they are discovered.

The critical path through this graph, for a typical single-page application, is usually: HTML headers → enough HTML to discover the bundle → bundle transfer → bundle execution → API request → API response → framework render → paint. Notice how much of that chain is *sequential by construction*, because each step discovers the next. The chapter's second half is about seeing that chain in Atlas, measuring it, and deciding whether to break it.

Before that, experiments.
## Experiments

Everything above is a claim. Here is how to check it. These experiments use Chrome DevTools because its Network and Performance panels are the most widely used, but every one of them can be repeated in Firefox or Safari with minor translation, and doing so is instructive, because the places where browsers differ are exactly the places where you have been mistaking an implementation detail for a law.

For several of them you will need a server you control that can delay responses. Here is one, in about twenty lines of Node, which will serve as the laboratory for this chapter. It serves files from the current directory and honors a `?delay=ms` query parameter on any path.

```js
// lab.js — run with: node lab.js
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname } from "node:path";

const types = {
  ".html": "text/html", ".css": "text/css",
  ".js": "text/javascript", ".json": "application/json",
};

createServer(async (req, res) => {
  const url = new URL(req.url, "http://localhost");
  const delay = Number(url.searchParams.get("delay") ?? 0);
  await new Promise(r => setTimeout(r, delay));
  try {
    const body = await readFile("." + url.pathname);
    res.writeHead(200, {
      "Content-Type": types[extname(url.pathname)] ?? "text/plain",
      "Cache-Control": "no-store",
    });
    res.end(body);
  } catch {
    res.writeHead(404); res.end();
  }
}).listen(8080);
```

Each experiment follows the same discipline: read the setup, write down your prediction, run it, compare. The prediction is not optional. If you skip it, you will read the result and nod and learn nothing, because a result that you did not predict cannot surprise you.

### Experiment 1: The blocking script

Create `index.html`:

```html
<!doctype html>
<html>
<head>
  <script src="/slow.js?delay=3000"></script>
</head>
<body>
  <h1>Hello</h1>
</body>
</html>
```

And an empty `slow.js`. Open the page with the Network panel visible.

*Predict:* when does "Hello" appear? What does the Network panel show for the HTML request versus the script request?

Then move the script tag to the end of the body and repeat. Then add `defer`. Then add `async`. For each, predict when the heading appears and when `DOMContentLoaded` fires (the Network panel draws it as a blue vertical line; `load` is red).

What you should find: with the script in the head, the heading appears after three seconds, though the HTML arrived almost immediately. With the script at the end of the body, the heading appears at once and the page is "done" three seconds later. With `defer`, the heading appears at once and `DOMContentLoaded` waits three seconds. With `async`, the heading appears at once and `DOMContentLoaded` fires at once, before the script has arrived.

Now put *two* slow scripts in the head, one at 3000 ms and one at 1000 ms. With no attributes, do they download in parallel or in series? With `async`, in which order do they execute? With `defer`? Add a `console.log` to each and find out.

### Experiment 2: What CSS actually blocks

Create:

```html
<!doctype html>
<html>
<head>
  <link rel="stylesheet" href="/slow.css?delay=3000">
</head>
<body>
  <h1>Hello</h1>
  <script>console.log("script ran at", performance.now());</script>
  <p>World</p>
</body>
</html>
```

With `slow.css` containing `h1 { color: red; }`.

*Predict:* when does "Hello" appear? When does the script run? When does `DOMContentLoaded` fire?

Now add `media="print"` to the link. Predict again. Now remove the inline script and add `media="print"` back off. Now move the `<link>` into the body between the `<h1>` and the `<p>`, and try it in two different browsers.

What you should find: the stylesheet in the head delays the paint of everything by three seconds and delays the inline script by three seconds, which in turn delays `DOMContentLoaded`. With `media="print"`, none of that happens; the page paints immediately and the script runs immediately. The body-position case is the one that varies by engine and is left for you to observe.

### Experiment 3: Streaming HTML

Modify the lab server to handle one special path:

```js
if (url.pathname === "/stream") {
  res.writeHead(200, { "Content-Type": "text/html" });
  res.write("<!doctype html><html><body><h1>Top of page</h1>");
  await new Promise(r => setTimeout(r, 3000));
  res.write("<p>Bottom of page</p></body></html>");
  res.end();
  return;
}
```

*Predict:* what does the user see at 0 ms, 1000 ms, 3000 ms? What does the Network panel show as the document's status during the wait? What does `document.readyState` return if you type it into the console at 1000 ms?

What you should find: the heading is visible almost immediately, the tab shows a spinner, the document request shows as pending with bytes received, and `readyState` is `"loading"`. The page rendered before the response completed. Try it with a `<link rel="stylesheet">` for a slow stylesheet in the head, and watch the top of the page wait for the stylesheet even though the bytes are there.

### Experiment 4: The waterfall under throttling

Take any real page you work on. Open the Network panel. Check "Disable cache." Set throttling to "Slow 4G" (or define a custom profile with 400 ms latency and 1 Mbps download). Reload.

Before you look: sketch what you expect the waterfall to look like. Which resource do you expect to finish last? Which do you expect to be on the critical path?

Then look. Hover over each row's timing bar and read the phases: queueing, DNS, initial connection, SSL, request sent, waiting (TTFB), content download. Find a resource whose "waiting" is large and one whose "content download" is large; those are two different problems with two different fixes. Find the resource that started latest and ask what discovered it. Was it in the HTML, or did a script have to run first? If a script, the preload scanner could not have found it, and it is on a chain.

Now uncheck "Disable cache" and reload. Compare. Which resources disappeared from the network entirely? Which show a 304? What is the ratio of the two total load times? That ratio is a rough measure of how much your page depends on cache state, and it tells you how different the first visit is from the second.

### Experiment 5: Timing entries

On any page, in the console:

```js
const [nav] = performance.getEntriesByType("navigation");
console.table({
  redirect:   nav.redirectEnd - nav.redirectStart,
  dns:        nav.domainLookupEnd - nav.domainLookupStart,
  connect:    nav.connectEnd - nav.connectStart,
  tls:        nav.secureConnectionStart
                ? nav.connectEnd - nav.secureConnectionStart : 0,
  ttfb:       nav.responseStart - nav.requestStart,
  transfer:   nav.responseEnd - nav.responseStart,
  domInteractive: nav.domInteractive,
  dcl:        nav.domContentLoadedEventEnd,
  load:       nav.loadEventEnd,
});
```

This is the Navigation Timing API, and every number in it corresponds to a stage we have discussed. Run it on a cold load and a warm one. Which numbers go to zero? Run it on a page you reached via a redirect, and notice whether the redirect shows up or whether it vanished into the gap between `startTime` and `fetchStart` (it vanishes if the redirect was cross-origin).

Then do the same with `performance.getEntriesByType("resource")` and find the resource with the largest `responseEnd`, and the one with the largest gap between `startTime` and `fetchStart` (that gap is time spent waiting for a connection or a service worker), and the one with the largest `requestStart - connectEnd` (queueing after the connection was ready). Each is a different bottleneck.

And in Chrome specifically, the `PerformanceObserver` for `"largest-contentful-paint"` and `"paint"` entries will tell you when the user actually saw something, which none of the numbers above do.

### Experiment 6: Introduce a redirect

Add to the lab server a route that responds `302` with a `Location` pointing at `/index.html`. Load it, and observe the Network panel and the navigation timing. Then chain two. Then make the redirect go to a different port (which is a different origin) and observe what the timing API stops telling you.

## Atlas: The First Load

It is time to build something.

Atlas at the end of this chapter is a small single-page application. It has an HTML shell, a stylesheet, a JavaScript bundle (React, a router, and about two hundred lines of application code), a web font, and one API endpoint, `GET /api/incidents`, which returns a JSON array. The bundle, on load, renders a header and a list; the list component fetches the incidents and renders a row per incident; clicking a row navigates to `/incidents/:id`, which renders a detail view with a status dropdown; changing the dropdown sends `PATCH /api/incidents/:id`. That is the whole application. It is the least an incident tool can be.

The HTML shell is this:

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Atlas</title>
  <link rel="stylesheet" href="/assets/atlas.3f9a1c.css">
  <link rel="stylesheet" href="https://fonts.example.net/inter.css">
</head>
<body>
  <div id="root"></div>
  <script src="/assets/atlas.8b2e7d.js"></script>
</body>
</html>
```

It is served from a CDN, along with the assets, which have content hashes in their names and are sent with `Cache-Control: public, max-age=31536000, immutable`. The HTML itself is sent with `Cache-Control: no-cache`, so the browser revalidates it on every load. The API is on the same origin, behind the CDN, which passes API requests through to an application server, and API responses are `no-store`.

We chose this architecture because it is what a great many teams would build first, and because every decision in it is defensible. Let us apply the chapter to it.

### Predicting the load

Before measuring anything, draw the dependency graph. Try it before reading on.

The navigation fetches the HTML. Because it is `no-cache`, even a repeat visit sends a conditional request to the CDN and waits for a 304 (or a 200 if the HTML changed, which it does on every deploy, because the asset hashes change). The parser begins, and the preload scanner discovers two stylesheets and a script. The application stylesheet is on the same origin, so it reuses the connection. The font stylesheet is on a *different* origin, `fonts.example.net`, so it requires a new DNS lookup, a new connection, and a new TLS handshake before its first byte, and it is render-blocking. When it arrives it contains `@font-face` rules pointing at font files, which are discovered only when the stylesheet is parsed; the preload scanner could not see them. Those files are on the same font origin, so they reuse that second connection.

The script is at the end of the body, so it does not block parsing, but it has no `defer`, so when the parser reaches it, the parser stops until it has executed. Since it is at the end, that is nearly free. The script is 280 KB compressed. When it has arrived and executed, React mounts, the list component's effect runs, and `fetch("/api/incidents")` is called. That request reuses the main connection but goes through the CDN to the application server. When it returns, the list renders.

The critical path is: HTML → bundle transfer → bundle execution → API → render. The stylesheets and fonts affect *when the first paint happens*, but the first paint is of an empty `<div id="root">` and a header, which is not useful. The user cannot do anything until the API has returned.

```
                  0     200    400    600    800   1000  1200  1400
HTML (304)        ███
atlas.css            ████
fonts.css            ▒▒▒▒▒▒▒▒         ◀ new origin: DNS+TCP+TLS then transfer
inter.woff2                  ████
atlas.js             ████████████████
  execute                            ████
API /incidents                           ████████
  render list                                    ██
                                                   ▲ usable
first paint (empty shell)      ▲ ~600, after both stylesheets
```

Notice three things about this picture. The bundle's transfer is the long bar, and it starts as early as it can, but its *execution* cannot overlap with anything, and neither can the API call, which cannot begin until execution has finished. Notice that the font origin costs a full connection setup that the main origin does not. And notice that the first paint, the thing a user would call "the page appeared," is of nothing useful.

### Measuring it

Now we run it, and this is where the chapter's insistence on environments matters, because the same application, measured in four environments, gives four different answers.

On the developer's laptop, against a local server, with a warm cache: usable at about 180 ms. The bundle is served from memory cache. The API responds in 8 ms. Nothing is on the network. This is the environment in which the application was built and in which it feels instant, and it is the least representative environment that exists.

On the same laptop, against the production CDN, warm cache: usable at about 450 ms. HTML revalidation costs one round trip to the CDN edge, about 30 ms. The assets are served from cache without network. The API round trip through the CDN to the origin server is about 180 ms. Bundle execution is about 120 ms. The page is fast.

On the same laptop, cold cache: usable at about 1,300 ms. Now the bundle's 280 KB transfer is on the path, and the font origin's connection setup, and the font files. First paint happens at about 600 ms, of an empty shell.

On a mid-range Android phone, on a 4G connection with 150 ms RTT, from a city 9,000 km from the origin server, cold cache: usable at about 4,200 ms. Every round trip is five times longer. The bundle takes 1,400 ms to arrive and, on this CPU, 700 ms to execute. The font origin's setup costs 450 ms, and because the font stylesheet is render-blocking, the empty shell does not appear until nearly 1,000 ms. The API call, which cannot start until 2,900 ms, takes 600 ms because the origin is distant and the CDN does not cache it.

Here are those four measurements side by side.

| Environment | First paint | Usable | Bundle transfer | Bundle execute | API |
|---|---|---|---|---|---|
| Localhost, warm | 40 ms | 180 ms | 0 | 90 ms | 8 ms |
| Production, warm | 90 ms | 450 ms | 0 | 120 ms | 180 ms |
| Production, cold | 600 ms | 1,300 ms | 420 ms | 120 ms | 190 ms |
| Distant 4G phone, cold | 980 ms | 4,200 ms | 1,400 ms | 700 ms | 600 ms |

These are not four measurements of one system. They are measurements of four systems that happen to share code. The dependency graph is the same in all of them; the *weights* on the edges differ by an order of magnitude, and so the critical path shifts. On localhost the critical path is execution. On the phone it is transfer, then execution, then a distant API. Any optimization argument that does not say which environment it is about is not an argument.

*Assumption to notice:* Atlas assumed all users begin with the developer's network. Fast hardware and localhost hide dependency structure. The structure was always there; it was just weighted with zeros.

### Changing it

Suppose the product requirement is that users in that distant region see the incident list within two seconds on a cold load. Atlas is at 4,200 ms. What do we change?

The intuitive answer is "make the bundle smaller," and it is not wrong, but it is not a plan. A plan starts with the critical path: HTML → bundle transfer → bundle execution → API → render. Every millisecond removed from that chain is a millisecond saved; every millisecond removed elsewhere is not. Three changes attack the chain directly.

First, the API request does not need to wait for the bundle. The HTML knows the user is going to need `/api/incidents`; it can say so. Adding `<link rel="preload" href="/api/incidents" as="fetch" crossorigin>` to the head causes the browser to start that request while the bundle is still downloading, and when the application's `fetch()` call is eventually made, the response is already in the cache waiting for it. This removes the API's entire duration from the critical path when the bundle takes longer than the API, which on the phone it does by a wide margin. Alternatively, and with the same effect, a small inline script in the head can start the fetch and stash the promise on `window` for the application to pick up.

Second, the font origin is costing a connection setup on the render-blocking path. Two options. Self-host the font on the main origin, so it reuses the existing connection and the preload scanner can find the font file directly if we add a `<link rel="preload" as="font">`. Or, at minimum, add `<link rel="preconnect" href="https://fonts.example.net">` so the DNS and TLS work begins at the top of the document instead of when the stylesheet link is parsed. And make the font stylesheet non-render-blocking, since a system font for the first 800 ms is a better experience than an empty page.

Third, the bundle. 280 KB compressed is not outrageous for an application of this shape, but the list view does not need the detail view's code, the status editor, or the router's lazy-loading machinery. Splitting the detail route into a separately loaded chunk removes perhaps 90 KB from the initial transfer and a proportionate amount from execution. This is the change everyone reaches for first, and it is the third most effective of the three.

We make all three changes and measure again, on the phone, cold.

| Change | First paint | Usable | Notes |
|---|---|---|---|
| Baseline | 980 ms | 4,200 ms | |
| + preload API | 980 ms | 3,600 ms | API now overlaps bundle |
| + font preconnect, non-blocking | 520 ms | 3,150 ms | shell appears earlier; font swaps in later |
| + split detail route | 520 ms | 2,400 ms | ~90 KB less to transfer and execute |

We are at 2,400 ms, and the requirement was 2,000. The remaining critical path is HTML → bundle transfer (~950 ms) → bundle execution (~450 ms) → render. The API is no longer on the path at all. What remains is the structural cost of the architecture: the interface cannot appear until a large script has arrived and run, because the interface *is* the script's output. Removing that dependency means the server has to produce the interface, which is the decision we will consider below.

Before that, notice what we did not do. We did not guess. We drew the graph, measured the weights in the environment that mattered, identified the chain, and attacked it in order of effect. The intuitive fix, bundle size, was applied third and mattered least. Had we started with it, we would have spent a week on code splitting and moved the number from 4,200 to about 3,400, and then been puzzled.

## A Failure Story

Atlas ships. Two weeks later, a message arrives from a customer's on-call engineer in Singapore: "The incident dashboard shows a blank white page for four or five seconds when I open it during an incident. It is very stressful. Can you fix it?"

The developer who receives the message opens Atlas. It loads in under half a second. They open it in an incognito window to defeat the cache; 1.3 seconds. They check the deploy; it went out cleanly, all health checks green. They check the API's latency dashboard; p50 is 60 ms, p99 is 210 ms. They reply asking for a HAR file, and the customer, who is mid-incident, does not answer.

Stop here and do what the developer should do next. Write down what has been *observed* and what has been *hypothesized*.

Observed: one user, in Singapore, reports a blank page for roughly four to five seconds. The developer's own load is fast. The API's server-side latency is low. The deploy succeeded.

Hypothesized, so far: nothing has been ruled in or out. "The API is slow" is contradicted by the server-side latency only if the API's server-side latency is what the user experiences, which it is not; the user experiences server latency plus two ocean crossings. "The deploy is bad" is contradicted only if the deploy that reached the user is the one that was tested, which, with a CDN in the path, is not guaranteed.

The developer, sensibly, looks at what they can measure without the user. They open the CDN's analytics and filter by region. The cache hit ratio for `atlas.*.js` in the Asia-Pacific edge is 40 percent over the last hour, against 97 percent in North America. That is an observation, and it is interesting. Why would a hashed, immutable asset miss the cache?

Because the deploy was two hours ago, and the new hash has never been requested from most of the Asia-Pacific edges, and every first request to each edge is a miss that goes back to the origin in Virginia. A cold edge plus a distant origin means the bundle's transfer, which was measured at 420 ms from a warm edge, is now paying an extra 200 ms round trip and a slow origin-to-edge transfer, possibly 1,500 ms. That alone does not explain five seconds.

The developer sets up a real device in a cloud testing service in Singapore, cold cache, and loads Atlas with the Performance panel recording. The trace shows: HTML at 380 ms (TTFB, through the cold edge). The application stylesheet at 700 ms. The font stylesheet, from `fonts.example.net`, *at 2,900 ms*. First paint at 2,950 ms. Bundle arrived at 2,100 ms, executed by 2,600 ms, but could not paint anything until the font stylesheet arrived because it was render-blocking. API preloaded, returned at 1,400 ms. Usable at 3,100 ms.

So the blank page is the font stylesheet. Why is it slow from Singapore? The developer runs a DNS lookup for `fonts.example.net` from the Singapore machine and gets an address in Europe. The font provider's DNS is returning a European edge for Asia-Pacific resolvers, either because of a misconfiguration or because their Asia-Pacific capacity is limited. It is a third party's problem, and it is on Atlas's render-blocking path.

The user said "four or five seconds." The trace says 3.1. The difference is the user's actual network, a corporate one with its own DNS resolver and TLS inspection proxy, which the developer cannot reproduce. But the *shape* is reproduced, and the shape is enough.

The fix is the one we already identified: stop letting a third-party origin block rendering. The font stylesheet becomes non-blocking with a system-font fallback, and the font files are self-hosted on the next release. Blank-page time in Singapore drops to about 700 ms, which is still the cold-edge HTML time and is a separate conversation about deploy warming.

What should you take from this story? Not the specific cause. The method. The developer did not know the answer, and did not pretend to. They separated observation from hypothesis, found a measurement they could take without the user, followed the anomaly it exposed, reproduced the environment as closely as they could, and read the trace rather than the dashboard. "The API is slow" was never the answer, and the server-side dashboard that seemed to rule it out was measuring the wrong thing anyway. The failure was in a dependency nobody had drawn, on a path nobody had measured, in a region nobody had tested from. Every one of those "nobody"s is a place where a systems model would have prompted a question.

## Measurement: Observations and Theories

The story above turned on a distinction we should make explicit, because it is the foundation of every debugging chapter in this book.

An *observation* is something you measured. "The document's `responseStart` is 700 ms after `requestStart`." A *hypothesis* is an explanation you have proposed for it. "The server is slow." The temptation, under time pressure, is to skip from the first to the second without noticing that the second does not follow.

Consider what could make TTFB 700 ms. The DNS lookup could have been slow, but no, `domainLookupEnd - domainLookupStart` says 12 ms. The connection could have been slow; `connectEnd - connectStart` says 210 ms, and `secureConnectionStart` shows most of that was TLS. The request could have followed a redirect; `redirectCount` is 0, but if the redirect was cross-origin it would be hidden, so check `fetchStart - startTime` for an unexplained gap. The server could be slow. The CDN edge could have been cold and gone to origin. The user could be far from the edge. The connection could be congested, so that the request itself took a long time to be transmitted. The response could be large and slow to *begin* because the server buffers the whole thing before sending the first byte, which many application frameworks do by default.

That is eight explanations for one number, and the number cannot distinguish between them. Distinguishing requires more numbers, from different vantage points: the server's own log of how long it took, the CDN's log of whether it hit or missed, the timing breakdown from the browser, and, ideally, the same measurement from several locations. Each new number rules out some hypotheses and leaves others. That is the whole method. It is not fast at first and it is much faster than guessing.

The tools for this, at the browser level, are the Performance Timeline family of APIs: Navigation Timing for the document, Resource Timing for every subresource, Paint Timing for first paint and first contentful paint, Largest Contentful Paint, Event Timing for input responsiveness, Long Tasks and Long Animation Frames for main-thread contention, and `PerformanceObserver` for receiving all of them as they happen. Chrome's Performance panel shows the same information as a trace, with the main thread's activity laid out against time, and the Network panel shows it as a waterfall. These are the instruments. Chapter 9 teaches their use in detail and Chapter 16 teaches how to collect them from real users. For now, the lesson is that they exist, that each number in them corresponds to a stage in the model you now have, and that a number without the model is a fact you cannot interpret.

One further distinction, which the story also illustrated. Server-side latency and user-experienced latency are different quantities, related by the entire network path, and a dashboard of the former tells you nothing certain about the latter. When someone says "the API is fast, look at the dashboard," ask which dashboard, measured from where.

## An Engineering Decision

Atlas is at 2,400 ms in the target environment against a requirement of 2,000, and the remaining critical path is the structural one: interface cannot appear until the bundle has arrived and run. There are four broad options, and we will lay them out without declaring a winner, because there is not one.

**A. Keep client-side rendering and accept a larger bundle.** Do nothing further to the architecture. Continue optimizing the bundle and its execution. This is cheapest, changes nothing about the deployment, and keeps the mental model simple. It will probably get to around 2,000 ms with sustained effort, and it will get harder with every feature added, because every feature adds to the thing on the critical path.

**B. Server-render the initial incident list.** The server, on a navigation request, fetches the incidents itself, renders the list to HTML, and sends it. The user sees the list as soon as the HTML arrives, before any JavaScript. The bundle then *hydrates* the list, attaching event handlers. Usable-for-reading time drops to roughly the HTML's TTFB plus the paint, perhaps 800 ms on the phone. Usable-for-interaction time is still gated on the bundle, though a smaller one. The cost: the HTML is now personalized and cannot be cached at the CDN; the server must be able to run the rendering code, which changes the deployment; the server's own call to the API is on the critical path, so a slow API now delays *everything* rather than only the list; and there is a class of bugs, hydration mismatches, that did not exist before.

**C. Stream the shell before the data.** A refinement of B. The server sends the HTML head and the static shell immediately, then fetches the incidents, then streams the rendered list into the document as it becomes available. The user sees the frame of the interface at TTFB and the list a moment later, and a slow API delays only the list, not the shell. This is the best user experience of the four and the most complex to build and operate: it needs a server that can stream, a framework that supports streaming rendering, and care around what happens when the stream is interrupted.

**D. Keep client rendering, but prerender and cache aggressively.** Keep the architecture but attack the weights. Use Speculation Rules so that the dashboard is prerendered when the user is on the page they usually arrive from. Use a service worker to serve the shell and bundle from Cache Storage on repeat visits, so that the only network request on a warm load is the API. Warm CDN edges on deploy. This can make repeat loads nearly instant and does nothing for a true cold load in a new region, which was the requirement.

Now the variables. Whether B or C is worth its cost depends on how often loads are cold; on whether the API's latency is stable enough to put on the server's critical path; on whether the team can operate a rendering server, which is a different skill from operating a static CDN; on whether the HTML was ever cacheable in the first place (Atlas's is personalized by tenant, so not really, which weakens one of the arguments against B); on how much of the interface is useful to *look at* before it is interactive (an incident list is very useful to read; a form is not); and on where the users are relative to the servers, because SSR moves work to the server and if the server is far away, that work's output still has to cross the ocean.

For Atlas, at this stage of the book, we choose **A with the option to move to C**, and we choose it for a reason that has nothing to do with performance: Atlas has one route, one API, and a team of two, and the requirement is 2,000 ms, which A can reach with the remaining bundle work. Introducing a rendering server for a 400 ms gain on one route is a large fixed cost for a small variable gain. But we record that the structural limit of A has been reached, that the next constraint (which will arrive in Chapter 10, when Atlas has many routes and a public status page that must render instantly for anonymous users) will likely change the answer, and that the decision should be revisited then.

That is what "it depends" looks like when it is done properly: a list of variables, an honest assessment of which ones dominate now, a choice, and a note about what would change it.

## What Would Change Your Mind?

We chose to keep client rendering. What evidence would make that wrong?

If real-user measurements showed that cold loads were a majority of loads rather than a minority, the calculus flips, because the structural cost of A is paid on every cold load. If a route appeared whose content had to be visible before any JavaScript could be trusted to run, a public status page for example, C becomes necessary for that route regardless of the rest. If the bundle's execution time on low-end devices grew past the point where splitting could contain it, the interface-is-the-script's-output dependency becomes unaffordable. If the API became reliably fast and geographically distributed, B's biggest risk, a slow API on the server's critical path, would shrink. If the team grew and acquired the operational competence to run a rendering tier, the fixed cost of B and C would drop.

Conversely, what would make us *more* confident in A? Evidence that most users arrive with a warm cache and a warm edge. Evidence that the interface is rarely useful before the user can interact with it. A successful reduction of the bundle to a size where its transfer no longer dominates on the target device.

Write these down. When Chapter 10 arrives and Atlas has grown, we will check which of them came true.

## Atlas: Decisions So Far

Here is what Atlas has decided, in a form we will refine into proper decision records in Chapter 17. Each is revisable, and several will be revised.

*Decision 1. Client-side rendering with a static HTML shell served from a CDN.* Chosen for simplicity of deployment and because a single route with one API call does not justify a rendering server. Structural cost accepted: interface appears only after bundle transfer and execution. Revisit when routes multiply or when an anonymous, must-render-instantly route appears.

*Decision 2. Content-hashed, immutable assets with a no-cache HTML shell.* Chosen so that assets are cached indefinitely and the shell is revalidated on every load. Known weakness: every deploy cold-starts every CDN edge for the new hashes. Revisit when we address deploy warming in Chapter 14.

*Decision 3. The initial API request is preloaded from the HTML.* Chosen because it removed the API from the critical path with one line. Known weakness: it duplicates knowledge of the route's data dependency between the shell and the application, which will drift. Revisit in Chapter 7 when data fetching is redesigned.

*Decision 4. Fonts are self-hosted and non-render-blocking, with a system-font fallback.* Chosen after the Singapore incident. No third-party origin is permitted on the render-blocking path. This one we expect to keep.

*Decision 5. The target environment for performance requirements is a mid-range Android device on 4G with 150 ms RTT, cold cache.* Chosen because it is the environment in which the requirement was failing and because localhost measurements were found to be uninformative. All performance claims in Atlas are stated against this environment unless otherwise noted.

*Decision 6. Atlas assumes the data it fetches is the current state of the incident.* Not chosen so much as inherited. Unexamined. Chapter 7 will examine it.

## The Layer Beneath

At the start of this chapter you knew what happens when you enter a URL and press Enter, and the answer was a sequence of seven or eight steps. You now know that the sequence is a graph; that most of its edges can be skipped, overlapped, speculated, or cached; that the browser is several processes and the important one is a single thread; that a stream of bytes becomes a tree while it is still arriving; that scripts stop the tree and stylesheets stop the paint and the two interact; that rendering is a pipeline with a ladder of costs and is run continuously; that input has its own path through the same machinery; and that all of this is weighted differently on every device and network in the world, so that a single application is really a family of systems that share code.

You also know how to find out what a given page is actually doing: predict, measure, compare, and treat the difference as the interesting part.

We should be honest about what we have not done. We have described the network as though it were one thing, and it is a stack of protocols each of which has its own failure modes; the retries and timeouts and congestion behavior that determine what happens on a *bad* network are still ahead. We have described the parser and skipped the enormous edifice of CSS layout that Chapter 2 will open. We have mentioned the main thread a dozen times and not once explained the event loop that schedules it, which Chapter 3 will do in more detail than you may want. We have said "cache" as though caches were simple, and Chapter 7 will disabuse you of that. We have said "service worker" and "origin" and "sandbox" and left Chapters 8 and 11 to say what those words cost. We have measured a page load and not yet said how to measure ten thousand of them and believe the result, which is Chapter 9's job.

Each of those is a layer beneath the one we just exposed, and each will do to this chapter's model what this chapter did to the naive one: keep it, and show where it stops.

The next chapter goes down one layer into the rendering pipeline we sketched, and begins with a question that sounds as innocent as this chapter's: how wide is a `<div>`?
## Exercises

Exercises are grouped by the operation they practice. Those marked ◆ are difficult; those marked ◆◆ are difficult and open-ended, and some have no single correct answer. For prediction exercises, write your answer down before testing it.

### Prediction

**1.1** A page contains, in order in its `<head>`: a `<link rel="stylesheet">` to a stylesheet that takes 2 s to arrive; an inline `<script>` that does `document.title = "loaded"`; a `<script async src>` to a script that takes 100 ms to arrive and sets `document.title = "async"`. What is the title at 500 ms? At 2,500 ms? What changes if the stylesheet has `media="print"`?

**1.2** Two `<script defer>` tags appear in the head, the first pointing at a 3 s script, the second at a 100 ms script. Each logs its name on execution. In what order do the logs appear, and at roughly what time does the second one appear? Now change both to `async` and answer again. Now change both to `type="module"` and answer again.

**1.3** The following markup is served over HTTP/1.1 from a single host. Sketch the Network waterfall you expect, assuming each resource takes 200 ms to transfer and the browser opens at most six connections to the host.

```html
<head>
  <link rel="stylesheet" href="a.css">
  <script src="b.js"></script>
  <link rel="stylesheet" href="c.css">
</head>
<body>
  <img src="1.png"><img src="2.png"><img src="3.png">
  <img src="4.png"><img src="5.png"><img src="6.png">
  <script src="d.js"></script>
</body>
```

Which resource is discovered by the preload scanner but cannot execute until the parser reaches it? When does the first paint occur? Then answer the same questions for HTTP/2.

**1.4** ◆ A page is loaded twice, ten seconds apart. Its HTML is served with `Cache-Control: max-age=60`. It references a script served with no caching headers at all and a `Last-Modified` date one year in the past. On the second load, how many network requests does the browser make, and what does each return? Now the user presses the browser's reload button. How does the answer change? (Browsers differ; state which one you are predicting for and then check another.)

**1.5** A user clicks a button 50 ms after the page's first contentful paint. The bundle that attaches the button's click handler is still 400 ms from arriving. Describe exactly what happens to the click event: where it is dispatched, which listeners run, what the default action is, and what the user sees. Now suppose the button is inside a `<form>` with no `action` attribute. Answer again.

### Explanation

**1.6** A stylesheet in the `<head>` is observed to block an inline script that appears after it, even though the script only calls `console.log("hi")`. Explain, from the browser's point of view, why it cannot run the script. Then explain why moving the script *above* the stylesheet changes the behavior, and what the script can and cannot see in that position.

**1.7** A team moves its static assets from `cdn-a.example.com` to `cdn-b.example.com` by changing the DNS record for `assets.example.com`. Some users see broken images for several hours; the team members themselves see the new assets immediately. Explain both observations. What single number, chosen differently in advance, would have changed the duration of the problem?

**1.8** An engineer notes that their page's `load` event fires at 6 s but the page "felt ready" at 1.2 s. Explain what could account for the 4.8 s gap, list three different kinds of resource that could each cause it, and say which of them a user would notice.

**1.9** ◆ On an HTTP/2 connection with 2% packet loss, a page with forty small resources loads more slowly than the same page over six HTTP/1.1 connections with the same loss. Explain the mechanism. Then explain why HTTP/3 does not suffer from it, and identify a network condition under which HTTP/3 may nonetheless be *unavailable* to the browser.

### Debugging

**1.10** A single-page application's users in one country report that the page is blank for three seconds and then appears all at once. Users elsewhere see the page appear in under a second. The application's server-side latency dashboard shows p99 under 100 ms globally. List, in order, the measurements you would take, what each one could rule in or out, and the point at which you would expect to be able to say what is wrong. Do not assume the cause is the same as in this chapter's failure story.

**1.11** After a deploy, a fraction of users report that clicking any button does nothing, and that a reload fixes it. The bundle is content-hashed and the HTML is `no-cache`. Construct at least two mechanisms by which this chapter's material could produce that symptom. For each, say what evidence would distinguish it from the others.

**1.12** ◆ The Resource Timing entry for a page's main bundle shows `startTime` at 40 ms, `fetchStart` at 1,240 ms, `responseEnd` at 1,400 ms. The bundle is 40 KB. What happened in the 1,200 ms between `startTime` and `fetchStart`? Propose three explanations, say how to distinguish them, and say which one is most likely if the page has a registered service worker.

### Experiment

**1.13** Using the lab server from this chapter, construct a page in which reordering two tags in the `<head>` changes the time of first paint by at least one second, without changing any resource's size or delay. Explain the dependency that the reordering changes.

**1.14** Take a page you work on. Using `PerformanceObserver`, record `first-contentful-paint`, `largest-contentful-paint`, and the `responseEnd` of every resource. Determine which resource's arrival immediately preceded the LCP. Is it on the critical path? Make it 500 ms slower (with a proxy or a query parameter) and measure whether LCP moves by 500 ms, by less, or not at all. Explain the result in terms of the dependency graph.

**1.15** Write a page that renders a list of 200 items, then registers a click handler on each. Load it under CPU throttling (6× slowdown in Chrome's Performance panel) and, using Event Timing, measure the input delay of a click made 100 ms after first paint. Then restructure the page so that the handler is attached by event delegation on the list's container, and measure again. Explain any difference, and explain why there might be *no* difference.

**1.16** ◆ Serve a page with `Content-Encoding: br` and again uncompressed. Under a 1 Mbps throttle, measure the difference in `responseEnd` for the document. Then measure `domInteractive`. Is the improvement in the second the same as in the first? Why might it not be?

### Design

**1.17** Atlas must add a public, unauthenticated status page at `/status` that shows the current state of all ongoing incidents. Requirements: it must render readable content within 1 s on the target environment (cold cache, distant 4G); it will be embedded in an iframe on customers' own sites; it must remain correct if the incident API is unavailable. Choose an architecture from A through D in this chapter (or a hybrid), justify it against each requirement, and state what would change your choice.

**1.18** ◆ A team proposes moving Atlas's fonts, icons, and analytics to three separate third-party origins for operational convenience. Write a one-page assessment of the loading consequences under this chapter's model, identify which of the three is acceptable on which path (render-blocking, parser-blocking, neither), and propose the mitigations you would require as a condition of approval.

**1.19** ◆◆ Design a HTML document structure for Atlas's incident list that allows the browser to paint the list's *frame* (header, filters, column headings) before the application bundle has arrived, without server rendering the data. State precisely which resources are render-blocking in your design, which are parser-blocking, and what the user sees at 200 ms, 800 ms, and 2 s in the target environment. Then identify a way this design could produce a worse experience than the baseline, and how you would detect it.

### Source exploration

**1.20** In the WHATWG HTML standard, find the section describing what happens when the parser encounters a `<script>` element (search for "prepare the script element"). Identify the exact condition under which the parser waits for a pending stylesheet, and quote the sentence. Does the standard require the browser to run a preload scanner? Find the passage that permits, but does not require, speculative fetching.

**1.21** In the Fetch standard, find the definition of a request's "priority" and the `fetchpriority` attribute's effect. Then find, in the Chromium source or its published documentation, how Chromium maps resource types to network priorities. Which of the two documents specifies behavior, and which describes an implementation?

**1.22** In RFC 9111 (HTTP Caching), find the section on heuristic freshness. What does it say about the use of `Last-Modified` for computing a heuristic lifetime, and what does it say about the maximum? Then determine, by experiment, what fraction Chrome and Firefox actually use.

**1.23** ◆ Record a Performance panel trace of any page load in Chrome. In the trace, find: the moment the renderer process received the first bytes of HTML; the first "ParseHTML" task; the first "EvaluateScript" task; the first "Layout"; the first "Paint"; and the first "Commit" to the compositor. Draw them on a timeline and mark which of them were on the main thread and which on other threads. Identify the longest gap between consecutive events and explain what the main thread was doing during it.

**1.24** ◆◆ Using the URL standard's parser (there is a live reference implementation at jsdom's `whatwg-url` project and a testing page at the standard's site), determine what `new URL("http://example.com:80/a/../b?x#y")` produces for each component, and why the port is absent. Then find an input that the URL standard parses differently from `Node.js`'s legacy `url.parse()`, and explain which one browsers follow.

---

## Further Exploration

The web has excellent primary documentation and an enormous amount of secondary noise. What follows is short by design. Each item is here because it will change how you think about something in this chapter, not because it is comprehensive.

### Read next

*High Performance Browser Networking* by Ilya Grigorik, freely available online. The first half is the best single treatment of the network layer for web engineers: TCP behavior, TLS costs, and the reasoning behind HTTP/2. It predates HTTP/3 but the reasoning transfers directly. Read the chapters on latency and on TLS if nothing else.

*Inside look at modern web browser*, a four-part series on Chrome's developer site by Mariko Kosaka. It covers the process model, the navigation lifecycle, the rendering pipeline, and input handling with unusually clear illustrations. It is Chromium-specific, and says so; read it as a well-drawn instance of the principles in this chapter.

The MDN pages on *Populating the page: how browsers work* and on *Critical rendering path*. Shorter than this chapter, useful for review, and they link to the relevant specifications at each step.

*web.dev*'s guides on the preload scanner, on `fetchpriority`, and on render-blocking resources. Each is short, each has an experiment, and each is explicit about what is heuristic.

### Read deeper

The WHATWG HTML standard, sections on parsing (particularly the tokenizer and tree construction, which are long, and the "speculative HTML parsing" section, which is short and states exactly what the preload scanner may and may not do) and on scripting (the "prepare the script element" algorithm is the authoritative answer to every `async`/`defer`/module question). Do not read it linearly. Search for the algorithm you need and read that.

The WHATWG Fetch standard. It defines what a "request" is, what "CORS" means, how caching interacts with fetching, and what a service worker sees. Its definitions are used by every other web specification, and once you have read the "main fetch" algorithm you will find that many APIs that seemed unrelated are the same algorithm with different parameters.

The WHATWG URL standard. Short, and it will correct several things you believe about URLs.

RFC 9110 (HTTP Semantics), RFC 9111 (HTTP Caching), RFC 9112 (HTTP/1.1), RFC 9113 (HTTP/2), RFC 9114 (HTTP/3), and RFC 9000 (QUIC). You do not need all of these. RFC 9111 is the one to read in full; it is the source of truth for every caching question in this chapter and Chapter 7. RFC 9113's section on stream prioritization and RFC 9000's introduction are enough to understand the multiplexing discussion.

RFC 8446 (TLS 1.3), the introduction and the handshake overview. You do not need the cryptography; you need the message flow and the round-trip count.

The W3C Navigation Timing Level 2, Resource Timing, Paint Timing, and Event Timing specifications. Short, and each one has a diagram of exactly which moment each attribute records.

### Inspect real systems

Chromium's design documents, particularly *Multi-process Architecture*, *Site Isolation*, and the *Life of a Navigation* and *RenderingNG* series. These are the engineers' own descriptions of the system, they are candid about tradeoffs, and they are explicit about what is Chromium-specific.

Firefox's documentation on Fission (its site isolation project) and on the Gecko rendering pipeline (*Gecko profiler* documentation and the *Layout* section of the Firefox source docs). Reading these alongside Chromium's is the fastest way to learn which of the things in this chapter are principles and which are one engine's choices.

WebKit's blog posts on the rendering and loading pipeline, and the WebKit source's `Source/WebCore/loader` and `Source/WebCore/html/parser` directories, which are readable in a way that surprises people.

The Chrome DevTools Performance panel documentation, and in particular the pages on the "Performance insights" and on reading the main-thread flame chart. Then record a trace of a page you know and read every task on the main thread for the first second.

WebPageTest. Run a page you work on from a location on another continent, on a real mobile device, with a cold cache. Read the connection view, which draws each connection as a row and shows exactly when it was opened and what it carried. Then read the filmstrip, which shows what the user saw at every 100 ms.

### Optional rabbit holes

The HTML5 parsing algorithm's history: the "Web Applications 1.0" era discussions about reverse-engineering browser error handling into a specification. Understanding why every browser now builds the same tree from broken markup is understanding a large part of what "standards" mean on the web.

The `document.write` problem: Chromium's intervention that blocks `document.write`-inserted scripts on slow connections, the discussion that led to it, and the argument about whether a browser should ever refuse to do what a page asks. It is a small window onto how browser engineers think about backward compatibility.

Head-of-line blocking through the ages: from HTTP/1.1 pipelining (which failed), to HTTP/2's stream-level solution (which moved the problem to TCP), to QUIC (which moved it to the transport). Each generation solved the previous generation's problem and exposed a new one, and the pattern recurs at every layer.

The Happy Eyeballs RFCs (6555 and 8305), for the pleasure of reading a specification whose entire purpose is to race two things and take whichever wins, and for an example of how much complexity sits behind "the browser connects."

Cache partitioning: Chromium's and Firefox's explanations of why the HTTP cache is now keyed by top-level site as well as URL, what tracking technique this defeated, and what it cost. It is a good example of a performance feature being deliberately weakened for a privacy reason, and of why "the cache" is not one thing.

Speculation Rules and prerendering: the specification and Chrome's documentation. Once you understand that a browser may have loaded, parsed, executed, and rendered a page *before the user asked for it*, several things about measured navigation timing become clear, and several new problems appear, which you can then go and think about.
