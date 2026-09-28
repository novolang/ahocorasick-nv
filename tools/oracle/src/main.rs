// Reads one case per line on standard input:
//
//     <kind> <fold> <pattern>,<pattern>,...|<haystack>
//
// where <kind> is standard, leftmost-first or leftmost-longest and
// <fold> is 0 or 1.  Writes one line per case: the non-overlapping
// matches, a tab, and the overlapping matches sorted by start, end and
// pattern, or `-` when the semantics is not standard.  A match is
// written `pattern:start-end`, and matches are separated by spaces.
use aho_corasick::{AhoCorasick, MatchKind};
use std::io::{self, BufRead, Write};

fn main() {
    let stdin = io::stdin();
    let mut out = io::stdout().lock();
    for line in stdin.lock().lines() {
        let line = line.unwrap();
        let mut head = line.splitn(3, ' ');
        let kind = match head.next().unwrap() {
            "standard" => MatchKind::Standard,
            "leftmost-first" => MatchKind::LeftmostFirst,
            _ => MatchKind::LeftmostLongest,
        };
        let fold = head.next().unwrap() == "1";
        let (pats, hay) = head.next().unwrap().split_once('|').unwrap();
        let pats: Vec<&str> = pats.split(',').collect();
        let ac = AhoCorasick::builder()
            .match_kind(kind)
            .ascii_case_insensitive(fold)
            .build(&pats)
            .unwrap();
        let all: Vec<String> = ac
            .find_iter(hay)
            .map(|m| format!("{}:{}-{}", m.pattern().as_usize(), m.start(), m.end()))
            .collect();
        let over = if kind == MatchKind::Standard {
            let mut v: Vec<(usize, usize, usize)> = ac
                .find_overlapping_iter(hay)
                .map(|m| (m.start(), m.end(), m.pattern().as_usize()))
                .collect();
            v.sort();
            v.iter()
                .map(|(s, e, p)| format!("{}:{}-{}", p, s, e))
                .collect::<Vec<_>>()
                .join(" ")
        } else {
            "-".to_string()
        };
        writeln!(out, "{}\t{}", all.join(" "), over).unwrap();
    }
}
