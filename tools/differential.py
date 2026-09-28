#!/usr/bin/env python3
"""Write tests/differential_tests.nv from the Rust `aho-corasick` crate.

The crate is the reference implementation this package follows.  This
script makes pseudo-random pattern sets and haystacks from a fixed seed,
over a four-letter alphabet so that patterns overlap and share prefixes
often, and asks the crate for each case's answers under all three match
semantics, with and without ASCII case folding:

1. the non-overlapping matches, which `acfind.find_all` must equal, and
2. under standard semantics, every overlapping match, sorted, which
   `acfind.find_overlapping` must equal.

The oracle is tools/oracle, a small program built against the crate
with `cargo build --offline --release`.

Run from the package root:  python3 tools/differential.py
The output is passed through `novo fmt`.
"""
import os
import random
import subprocess

ORACLE_DIR = os.path.join('tools', 'oracle')
ORACLE = os.path.join(ORACLE_DIR, 'target', 'release', 'ac-oracle')
KINDS = ['standard', 'leftmost-first', 'leftmost-longest']
SEED = 20260928
CASES = 40


def cases():
    rng = random.Random(SEED)
    out = [
        (['he', 'she', 'his', 'hers'], 'ushers'),
        (['Sam', 'Samwise'], 'Samwise and Sam'),
        (['Samwise', 'Sam'], 'Samwise and Sam'),
        (['a', 'ab', 'abc', 'abcd'], 'abcdabcabd'),
        (['abcd', 'bc', 'c'], 'abcx abcd bcd'),
        (['ab', 'abcdefg'], 'abcdefX abcdefg'),
        (['x', 'x', 'xy'], 'xxyxy'),
        (['aaa', 'aa', 'a'], 'aaaaaaa'),
    ]
    while len(out) < CASES:
        alphabet = 'abAB' if rng.random() < 0.5 else 'abcd'
        n = rng.randint(1, 6)
        pats = [''.join(rng.choice(alphabet) for _ in range(rng.randint(1, 5)))
                for _ in range(n)]
        hay = ''.join(rng.choice(alphabet) for _ in range(rng.randint(0, 30)))
        out.append((pats, hay))
    return out


def oracle(lines):
    subprocess.run(['cargo', 'build', '--offline', '--release', '-q',
                    '--manifest-path', os.path.join(ORACLE_DIR, 'Cargo.toml')],
                   check=True)
    r = subprocess.run([ORACLE], input='\n'.join(lines) + '\n',
                       capture_output=True, text=True, check=True)
    return r.stdout.rstrip('\n').split('\n')


def main():
    rows, lines = [], []
    for pats, hay in cases():
        for kind in KINDS:
            for fold in (0, 1):
                rows.append((kind, fold, pats, hay))
                lines.append('%s %d %s|%s' % (kind, fold, ','.join(pats), hay))
    answers = oracle(lines)
    body = []
    for (kind, fold, pats, hay), ans in zip(rows, answers):
        all_, over = ans.split('\t')
        body.append('    ("%s", %s, "%s", "%s", "%s", "%s")' % (
            kind, 'true' if fold else 'false', ','.join(pats), hay, all_, over))
    text = HEADER % len(rows) + ',\n'.join(body) + ']\n' + FOOTER
    path = os.path.join('tests', 'differential_tests.nv')
    open(path, 'w').write(text)
    subprocess.run(['novo', 'fmt', path], check=True)


HEADER = '''// differential_tests.nv — this package against the Rust `aho-corasick`
// crate, version 1.1.3, which answers the same questions independently.
//
// Written by tools/differential.py; do not edit by hand.  Each row is
// a semantics, whether ASCII case folding is on, the patterns joined by
// commas, the haystack, the crate's non-overlapping matches, and under
// standard semantics its overlapping matches sorted by start, end and
// pattern (`-` otherwise).  A match is written `pattern:start-end`.
//
// Every row is also fed to `acstream` in chunks of one, two and three
// bytes, which must report the same non-overlapping matches.

use std.test
use acauto
use acfind
use acmatch
use acstream

// The %d cases.
fn rows() -> [(Str, Bool, Str, Str, Str, Str)]
    ['''

FOOTER = '''
// A list of matches in the form the rows are written in.
fn render(ms: [acmatch.AcMatch]) -> Str
    var parts: [Str] = []
    for m in ms
        list.push(parts, "${m.pattern}:${m.start}-${m.end}")
    str.join(parts, " ")

// The non-overlapping matches of a stream fed `hay` in chunks of `size`
// bytes, then finished.
fn streamed(a: acauto.AcAutomaton, hay: Str, size: Int) -> Str
    var s = acstream.stream(a)
    var out: [acmatch.AcMatch] = []
    let n = str.len(hay)
    for k in 0..(n + size - 1) / size
        let at = k * size
        let f = acstream.feed(s, str.slice(hay, at, math.min(at + size, n)))
        list.append(out, f.matches)
        test.assert(acstream.carried_bytes(f.state) <= acstream.max_carry(a))
        s = f.state
    list.append(out, acstream.finish(s).matches)
    render(out)

@test
fn test_every_row_agrees_with_the_crate() [io]
    for (kind, fold, pats, hay, all, over) in rows()
        test.case("${kind} fold=${fold} [${pats}] over `${hay}`")
        let named = acauto.kind_named(kind) ?? AcStandard
        let c = acauto.with_ascii_case_insensitive(acauto.with_kind(acauto.config(), named), fold)
        match acauto.build_with(str.split(pats, ","), c)
            Err(_) => test.fail("a list of non-empty patterns builds")
            Ok(a)  =>
                test.assert_eq_str(render(acfind.find_all(a, hay)), all)
                test.assert_eq(acfind.count(a, hay), list.len(acfind.find_all(a, hay)))
                match acfind.find_overlapping(a, hay)
                    Ok(ms) => test.assert_eq_str(render(ms), over)
                    Err(_) => test.assert_eq_str("-", over)
                for size in [1, 2, 3]
                    test.assert_eq_str(streamed(a, hay, size), all)
'''

if __name__ == '__main__':
    main()
