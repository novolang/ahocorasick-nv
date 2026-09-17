# Changelog

All notable changes to ahocorasick-nv are recorded here. The format is
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
package follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
with the pre-1.0 rule that a breaking change bumps the MINOR number.

## [0.0.1] — 2026-09-17

**The interface, published before anyone implements it.** Every public
type and function carries its full signature, its effect row and its
doc comment; every body is `todo()`; the release is recorded
`implemented = false`.

### Added

- `acauto` — the automaton as a value, and the decision the rest of
  the package follows from: the match semantics is chosen at BUILD,
  not at search. The two leftmost semantics are not a filter over
  standard reports, they are a different construction, and the losing
  candidates are dropped while the tables are made. So no search
  function takes a semantics, and `supports_overlapping` is a
  published predicate rather than a fact a caller discovers when the
  reference implementation panics. ASCII case folding is a build
  option for the same reason, and it is ASCII only: Unicode folding is
  not length-preserving, so a folding automaton could not report byte
  ranges into the caller's own haystack.
- `acmatch` — a match is a pattern index and a byte range, never a
  copied string, because a scan reports many and almost no caller
  wants the copy. `matched_text` is the copy, spelled out.
  `compare` is total, so two scans of the same haystack sort
  identically and a test may assert the whole list.
- `acfind` — `is_match`, `find_all` and the `cursor`/`step` pair are
  three shapes over one automaton, for the caller that wants an
  answer, the caller that wants a list, and the caller that will stop
  early. `find_overlapping` answers a `Result` rather than panicking
  on a leftmost automaton.
- `acstream` — the stream state is a value carrying the automaton
  node, the absolute offset and a tail bounded by `max_carry`, so the
  memory a stream holds does not grow with the stream. Every reported
  offset is into the whole stream. `finish` releases the leftmost
  candidate a later byte could still have beaten, and `is_settled`
  says when one is being held, because a caller that forgets `finish`
  loses the last match of the stream and nothing says so.
- `acreplace` — the replacement list is indexed by pattern and its
  length is CHECKED, which neither reference implementation does.
  `split` is the unmatched pieces, one more than the number of
  matches.
- `acerror` — four refusals, with `code` stable across releases and
  `is_pattern_fault` separating what a start-up check would catch
  from what depends on the call.

### Known

- `novo test` is red, and that is the release's expected state: every
  assertion in the API suite reaches `not implemented:
  ahocorasick-nv.<module>.<fn>`.
- **`replace_all_with` takes a pure function.** A free function in
  novo-lang cannot be effect-polymorphic — SPEC section 5.6 gives
  effect parameters to traits only — so an effectful replacement
  cannot be expressed here without charging every caller of the
  module. The README says what such a caller does instead.
