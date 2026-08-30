# Deck Workflow and Verification

## Story Contract

Write a compact contract before slide production:

| Field | Question |
|---|---|
| Audience | Who is present, and what do they already know? |
| Outcome | What should they understand, decide, remember, or do? |
| Duration | How much speaking and reading time exists? |
| Evidence | Which claims, numbers, quotations, demos, and sources must survive? |
| Constraints | Venue, projector, remote sharing, language, brand, offline, print, privacy |
| Close | What is the last decision, action, or thought? |

Estimate slide count from the speaking job, not from a default ratio. A fast keynote, product demo, workshop, and asynchronous reading deck have different densities.

## Slide Jobs and Layouts

- **Cover:** identify topic, promise, speaker/context; avoid a paragraph.
- **Section:** reset attention and name the next question.
- **Bullets:** a short parallel set whose order matters. Use prose or notes if items need explanations.
- **Two-column:** compare two concepts or pair evidence with interpretation. Do not use it merely to fill space.
- **Metrics:** 1–4 values with units, definitions, time scope, and sources.
- **Quote:** a necessary voice with correct attribution and context; not generic inspiration.
- **Image:** one essential figure with alt, detailed explanation, caption, source, and rights.
- **Closing:** decision, synthesis, contact, or next action; not an automatic “thank you” slide.

Use assertion headings. “Revenue mix changed before margin did” is more useful than “Financials.” Keep citations on the slide that uses the claim, even if a reference appendix also exists.

## Content Limits

The builder enforces conservative structural limits because overflow is easier to prevent before rendering:

- bullets: 1–6 items;
- metrics: 1–4 values;
- two-column: exactly two columns, each with a heading and body or short list;
- image: local PNG, JPEG, or WebP up to the configured size, with alt, rights, and a visible description;
- slides: 1–50.

These limits do not prove fit. Long strings and multilingual content still require browser review. Split reasoning across slides or move detail to notes before shrinking type.

## Direction Specimens

When direction is unresolved, produce two or three title-slide specimens from the same source title. Vary only decisions that matter—contrast, typography role, density, geometry, and image behavior. Keep the content and viewport identical so the user compares direction rather than copy.

Do not ask the user to choose when project brand, an accepted reference, or an explicit direction already resolves the decision. Do not build three full decks before alignment.

## Verification Matrix

### Every deck

- source JSON passes `--check`;
- no unsupported layout, unsafe asset, missing alt/rights, or failed contrast gate;
- all names, numbers, dates, quotations, and links reconcile to the evidence inventory;
- every slide has one clear job and a meaningful heading or label;
- citations and `as_of` dates are present where time-sensitive facts appear;
- no unresolved placeholder or invented stand-in remains.

### Browser

- target presentation size plus at least 1280×720;
- narrow viewport at or below 375px; add 320px when controls or long titles are close to the edge;
- previous/next buttons, Arrow/Page/Home/End, focus order, link activation, and hash reload;
- note panel if notes exist; browser full-screen if promised;
- reduced-motion preference;
- JavaScript disabled: all slides remain readable in source order;
- offline load with the network disabled when offline was promised.

### Print/export

- one intended slide per landscape page;
- no clipped overflow, hidden controls leaking into print, blank pages, or lost backgrounds when those backgrounds carry meaning;
- URLs, source footers, image descriptions, and page order remain available;
- exported PDF page count equals the deck count and every page is visually inspected.

## Failure Handling

- If content overflows, shorten or split it before reducing the type scale.
- If a system font fallback changes fit, keep the verified fallback or explicitly package a licensed font; never silently add a remote dependency.
- If the requested visual reference is copyrighted or recognizable, extract general properties and build a new composition. Do not reproduce distinctive layout, ornament, illustration, or typography treatment.
- If HTML is the wrong format, preserve the story/content model and route to a native presentation tool rather than faking editability.
- If browser or print inspection cannot run, deliver source as `draft` and name the missing evidence.
