# ahocorasick-nv

Aho–Corasick is an algorithm for finding all occurrences of a set of
strings in a text in one pass, published by Alfred Aho and Margaret
Corasick as
["Efficient string matching: an aid to bibliographic search"](https://dl.acm.org/doi/10.1145/360825.360855),
Communications of the ACM 18(6), 1975. The set is compiled once into a
finite automaton, and the search then runs in time proportional to the
length of the text plus the number of matches, however many strings
the set holds. This package brings it to novo-lang. The reference
implementations are the Rust crate
[`aho-corasick`](https://docs.rs/aho-corasick) and the Python
extension [`pyahocorasick`](https://pyahocorasick.readthedocs.io/).

**Status: NOT IMPLEMENTED — interface only.** Every function is
declared with its full signature, but every body is a `todo()` that
panics when called. The package is published so its design can be
reviewed and depended on before it is implemented. Version 0.1.0 will
be the first working release.

## What Aho–Corasick is

The **patterns** are the strings being looked for. The **haystack** is
the text being searched. The automaton is built from the patterns
alone, so one automaton searches any number of haystacks.

The construction is a trie of the patterns, with two additions. Every
node carries a **failure link**, which says where the search continues
when the next byte does not extend the current prefix. Some nodes
carry an **output set**, the patterns that end there. Searching is then
one byte at a time with no backtracking: the automaton is in one state,
reads a byte, follows a transition or a failure link, and reports
whatever the new state outputs.

Three **match semantics** are in use, and they answer different
questions about the same text.

| Semantics | What is reported |
| --- | --- |
| standard | every occurrence of every pattern |
| leftmost-first | at each position, the pattern earliest in the pattern list |
| leftmost-longest | at each position, the longest pattern, whatever the order |

The classic illustration is the patterns `he`, `she`, `his` and `hers`
over the text `ushers`. Standard semantics reports `she` at byte 1,
`he` at byte 2 and `hers` at byte 2. The three overlap, and a caller
that wants no overlaps gets `she` at byte 1 and nothing else, because
a match consumes the bytes it covers.

Leftmost-first is the semantics of an alternation in a backtracking
regular expression. Over the patterns `Sam` and `Samwise` in that
order, the text `Samwise` reports `Sam`. Leftmost-longest is POSIX
alternation semantics, and over the same two patterns in either order
it reports `Samwise`.

All offsets in this package are **byte** offsets, and a reported match
is the half-open range `[start, end)`.

## Install

```
novo pkg add ahocorasick-nv
```

## Example

```novo
use acauto
use acfind
use acmatch

fn main() [io]
    // Compile the four patterns into one automaton. This is the work
    // that is done once; searching is the cheap part.
    match acauto.build(["he", "she", "his", "hers"])
        Err(_) => println("the pattern set cannot be used")
        Ok(a)  =>
            // Every occurrence of every pattern, overlaps included.
            match acfind.find_overlapping(a, "ushers")
                Err(_) => println("this automaton is not standard")
                Ok(ms) =>
                    for m in ms
                        println("${acmatch.matched_text("ushers", m)} at ${m.start}")
```

Build and test with `novo pkg build` and `novo test`. Today `novo test`
fails on purpose: every test reaches a
`not implemented: ahocorasick-nv.<module>.<fn>` panic. The tests are
the specification the implementation will have to satisfy.

## What the package contains

| Module | Contents |
| --- | --- |
| `acerror` | The four refusals, a stable code for each, and which of them a start-up check would catch. |
| `acmatch` | A match: the pattern index, the byte range, the text it covers, and a total order over matches. |
| `acauto` | The build configuration, the three match semantics, and the automaton with the questions that can be asked of it. |
| `acfind` | Searching a haystack the caller holds whole: a predicate, a list, a cursor, and overlapping iteration. |
| `acstream` | Searching a haystack that arrives in chunks, with the state as a value and every offset absolute. |
| `acreplace` | Replacing matches from a list or from a function, and splitting on the matches. |

## How to choose an entry point

**`acfind.is_match` answers a question.** It stops at the first hit.
Use it when a program only needs to know whether anything matched.

**`acfind.find_all` builds the list.** Use it when the matches will be
read more than once.

**`acfind.cursor` and `acfind.step` walk the haystack one match at a
time**, with no list. Use them when the program may stop early, or
when it writes each match somewhere as it arrives.

**`acfind.find_overlapping` is the only function that reports matches
sharing bytes.** It needs an automaton built with standard semantics.

**`acstream.feed` is for a haystack that does not exist all at once** —
a file read in blocks, a socket, a log being tailed. Use `acfind` when
the whole text is already in memory.

**`acreplace.replace_all` rewrites from a list of replacements.**
`replace_all_with` rewrites from a function of the match.

## The rules a user needs

1. **The match semantics is chosen when the automaton is built.**
   `acauto.build_with` reads it from the configuration, and no search
   function takes one. A program that needs two semantics builds two
   automata.
2. **Overlapping iteration needs standard semantics.**
   `acfind.find_overlapping` on a leftmost automaton answers
   `AcOverlappingNeedsStandard`. `acauto.supports_overlapping` answers
   the same question before the call.
3. **A non-overlapping match consumes the bytes it covers.** Over
   `he`, `she`, `his` and `hers`, the text `ushers` reports one
   non-overlapping match, not three.
4. **The pattern order matters under leftmost-first.** `Sam` before
   `Samwise` reports `Sam`; the other order reports `Samwise`. Under
   leftmost-longest the order does not matter.
5. **An empty pattern is refused.** It would match at every byte
   offset, including the end of the haystack.
6. **An empty pattern list is refused.** An automaton that never
   matches is an answer no caller wants and every caller reaches by
   accident, such as from a filter file that was not there.
7. **Case folding is ASCII only.** `A` to `Z` fold with `a` to `z` and
   no other byte is affected. Unicode case folding is not
   length-preserving — `ß` folds to `ss` — so an automaton that did it
   could not report byte ranges into the caller's own text.
   `acauto.case_fold_notes` names the patterns the option does nothing
   for.
8. **A match carries offsets, not text.** `acmatch.matched_text` takes
   the haystack and makes the copy.
9. **Every offset a stream reports is into the whole stream**, not
   into the chunk that completed the match.
10. **A stream is not finished until `acstream.finish` is called.**
    Under either leftmost semantics a match may still be beaten by
    bytes that have not arrived, so `feed` holds the candidate back.
    `acstream.is_settled` says whether anything is being held.
11. **The memory a stream holds is bounded.** `acstream.max_carry` is
    one byte less than the longest pattern, whatever the length of the
    stream.
12. **A replacement list is indexed by pattern.** The replacement for
    pattern `i` is `replacements[i]`, and a list of a different length
    is refused with both lengths named.
13. **`acreplace.split` answers one more piece than there are
    matches**, counting the empty pieces at the ends.

## Running on a microcontroller

This package makes no device claim and ships no device probe. Every
function in it performs no input or output, so the modules build for a
microcontroller, but the automaton's transition table is 256 entries
per state and the size of a useful pattern set has not been measured
on a device. `acauto.memory_bytes` is the number to measure with.

## What is not included

- **Regular expressions.** A pattern here is a literal string.
  [regex-core-nv](https://novo-lang.org/packages/regex-core-nv) is the
  package for patterns with syntax in them.
- **Unicode case folding.** See rule 7.
- **Word boundaries.** A pattern matches anywhere, including inside a
  longer word. A caller that wants whole words checks the bytes either
  side of the reported range.
- **A tokenizer.** The haystack is bytes, and the patterns are bytes.
- **Anchored search.** Every search here scans forward for a match
  anywhere. A caller that wants a match at one position compares the
  reported `start` with the position it wanted.
- **Reading a pattern file.** Opening a file costs `[fs]`, and this
  package declares no effects.

## Related packages

- [regex-core-nv](https://novo-lang.org/packages/regex-core-nv)
  matches one pattern with syntax in it. Take this package when the
  patterns are literal strings and there are many of them. A set of a
  thousand literals is one automaton here and an alternation with a
  thousand branches there.
- [fuzzy-nv](https://novo-lang.org/packages/fuzzy-nv) scores
  approximate matches for a picker. Take it when the match does not
  have to be exact.
- [unicode-nv](https://novo-lang.org/packages/unicode-nv) has the case
  mapping this package deliberately does not use. A caller that needs
  Unicode folding folds the text and the patterns with it first, and
  accepts that the offsets are then into the folded text.
- [bm25-nv](https://novo-lang.org/packages/bm25-nv) ranks documents
  that have already been tokenised. Take this package to find the
  terms, that one to score them.

## Tests

```bash
novo test tests/acauto_tests.nv      # the three semantics, and what the build refuses
novo test tests/acfind_tests.nv      # the 1975 paper's example, overlapping and not
novo test tests/acstream_tests.nv    # a match across a chunk boundary, and finish
novo test tests/acreplace_tests.nv   # rewriting, the length check, and the match value
```

The normative source is Aho and Corasick's 1975 paper for the
automaton and the `ushers` vector. The semantics vectors are the ones
the `aho-corasick` crate documents its own match kinds with: `Sam` and
`Samwise` over `Samwise`, in both list orders, under all three
semantics.

The suite asserts that the paper's example reports three overlapping
matches and one non-overlapping match, that leftmost-first follows the
pattern order and leftmost-longest does not, that overlapping
iteration on a leftmost automaton is refused rather than fatal, that a
pattern split across two chunks is found once at its absolute offset,
that a one-byte-at-a-time stream finds what a single chunk finds, that
a leftmost stream holds its last candidate until `finish`, and that a
replacement list of the wrong length is refused with both lengths
named.

The tests compile today and fail at run, each on the
`not implemented: ahocorasick-nv.<module>.<fn>` panic that is its
body. That is the expected state of an interface release. They turn
green one at a time as bodies land.

## Implementation status

| Item | Implemented |
| --- | --- |
| `acerror.AcError` and the other public types | the types are declared |
| `acerror.message`, `.code`, `.is_pattern_fault` | no |
| `acmatch.at`, `.len`, `.matched_text`, `.overlaps`, `.compare` | no |
| `acauto.config`, `.with_kind`, `.with_ascii_case_insensitive` | no |
| `acauto.build`, `.build_with` | no |
| `acauto.kind_of`, `.kind_name`, `.kind_named` | no |
| `acauto.pattern_count`, `.pattern_at`, `.min_pattern_len`, `.max_pattern_len` | no |
| `acauto.is_ascii_case_insensitive`, `.supports_overlapping`, `.case_fold_notes` | no |
| `acauto.state_count`, `.memory_bytes` | no |
| `acfind.is_match`, `.find`, `.find_at`, `.find_all`, `.count` | no |
| `acfind.find_overlapping` | no |
| `acfind.cursor`, `.cursor_at`, `.cursor_offset`, `.step` | no |
| `acstream.stream`, `.feed`, `.finish` | no |
| `acstream.stream_offset`, `.carried_bytes`, `.max_carry`, `.is_settled` | no |
| `acreplace.replace_all`, `.replace_first`, `.replace_all_with` | no |
| `acreplace.split`, `.replacements_fit` | no |

## Licence

Apache-2.0. See `LICENSE`.

<!-- docs/writing-a-readme.md is the style guide for this page. -->
