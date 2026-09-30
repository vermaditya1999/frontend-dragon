# Tone Sample

Short excerpts from Chapter 1, chosen to calibrate the voice. Read them before writing;
do not copy them. Each is labelled with what it demonstrates.

## 1. An opening scene (The Question)

> It is 9:07 on a Tuesday morning. You open a laptop that has been asleep since last
> night, and while the screen is still brightening you type the address of the incident
> dashboard and press Enter. Perhaps four hundred milliseconds later, the page is there.
> You do not think about it. You are looking for the incident that paged you at 6:40, and
> there it is, and you click it.
>
> […]
>
> You can be a very good frontend engineer without knowing most of this. The abstractions
> are excellent. That is what makes them dangerous.

*Concrete, specific, unhurried. The short closing sentence does the work.*

## 2. Respecting the naive model before breaking it

> We want to be clear that this is a good model. It is correct in the sense that every
> step in it really happens. It gets the order of dependencies approximately right. […]
> It is the model most working engineers carry, and they carry it because it works most
> of the time.
>
> Its virtue is also its limitation: it is a *sequence*. Each arrow says "and then." And
> the real system is not a sequence.

## 3. An escalating example with a prediction prompt

> What does the script log? Commit to an answer before reading on.
>
> It logs `null`. When the script runs, the tokenizer has emitted the tokens up to and
> including `</script>`, the tree builder has built the head and the script element, and
> the parser has *stopped*. The body does not exist yet because the parser has not
> reached it. The script sees a document with a head and nothing else.
>
> Now move the script.

## 4. Turning a rule into a mechanism

> So *rendering* waits for the stylesheet. That is what "render-blocking" means. It does
> not block parsing. It does not block the DOM. It blocks the first paint, and it blocks
> scripts that come after it.
>
> Now, three complications, each of which turns a rule into a mechanism.

## 5. An assumption callout

> *Assumption to notice:* we assumed a connection is a fixed cost. It is one round trip,
> two round trips, or zero round trips, depending on transport and history, and the round
> trip itself ranges from under a millisecond on localhost to a third of a second across
> an ocean.

## 6. Observation versus hypothesis (failure story)

> Stop here and do what the developer should do next. Write down what has been
> *observed* and what has been *hypothesized*.
>
> Observed: one user, in Singapore, reports a blank page for roughly four to five seconds.
> The developer's own load is fast. The API's server-side latency is low. The deploy
> succeeded.
>
> Hypothesized, so far: nothing has been ruled in or out. "The API is slow" is
> contradicted by the server-side latency only if the API's server-side latency is what
> the user experiences, which it is not; the user experiences server latency plus two
> ocean crossings.

## 7. An engineering decision with variables, not a winner

> That is what "it depends" looks like when it is done properly: a list of variables, an
> honest assessment of which ones dominate now, a choice, and a note about what would
> change it.

## 8. Closing a chapter (looking down and forward)

> Each of those is a layer beneath the one we just exposed, and each will do to this
> chapter's model what this chapter did to the naive one: keep it, and show where it
> stops.
>
> The next chapter goes down one layer into the rendering pipeline we sketched, and
> begins with a question that sounds as innocent as this chapter's: how wide is a
> `<div>`?

## What these have in common

Every paragraph is doing one job. Mechanism is explained with *because*. The reader is
asked to commit before being told. Certainty is calibrated ("in most engines", "at the
time of writing"). There is no throat-clearing, no announcement of what comes next, and no
recap of what just happened.
