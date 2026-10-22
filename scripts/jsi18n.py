"""Add a third language to tr(english, vietnamese) calls in JS source at build time.

static/js/results.js writes its text as tr(`English`, `Vietnamese`). For another
language, the build looks up each call's English source text (template literal and
all, so ${...} expressions match exactly) in that language's RESULTS dictionary
and inserts the translation as the third argument, which tr() then returns.
"""
import re
import sys

def skip_string(src, i):
    """Index just past the quoted string starting at src[i]."""
    q = src[i]; i += 1
    while src[i] != q:
        i += 2 if src[i] == "\\" else 1
    return i + 1

def skip_template(src, i):
    """Index just past the template literal starting at src[i]."""
    i += 1
    while src[i] != "`":
        if src[i] == "\\": i += 2; continue
        if src.startswith("${", i):
            i = skip_expr(src, i + 2, "}") + 1; continue
        i += 1
    return i + 1

def skip_expr(src, i, close):
    """Advance over a JS expression until the matching `close` at depth 0; return its index."""
    depth = 0
    while True:
        ch = src[i]
        if ch in "'\"": i = skip_string(src, i); continue
        if ch == "`": i = skip_template(src, i); continue
        if src.startswith("//", i): i = src.index("\n", i); continue
        if ch in "([{": depth += 1
        elif ch in ")]}":
            if depth == 0 and ch == close: return i
            depth -= 1
        i += 1

def args_of(src, i):
    """i points just after '('. Return (list of arg sources, index after ')')."""
    args, start, depth = [], i, 0
    while True:
        ch = src[i]
        if ch in "'\"": i = skip_string(src, i); continue
        if ch == "`": i = skip_template(src, i); continue
        if ch in "([{": depth += 1
        elif ch in ")]}":
            if depth == 0:
                args.append(src[start:i].strip()); return args, i + 1
            depth -= 1
        elif ch == "," and depth == 0:
            args.append(src[start:i].strip()); start = i + 1
        i += 1

def calls(src):
    """(start, end, [argument sources]) for every tr( call, outermost first."""
    out = []
    for m in re.finditer(r"(?<![\w.$])tr\(", src):
        if src[max(0, m.start() - 6):m.start()].endswith("const "):
            continue
        args, end = args_of(src, m.end())
        out.append((m.start(), end, args))
    return out

def english_sources(src):
    """The distinct English arguments of tr() calls, in order of appearance."""
    seen = []
    for _, _, args in calls(src):
        if args[0] not in seen:
            seen.append(args[0])
    return seen


def inject(src, translations):
    """Return src with translations[english] added as the third argument of each tr() call.

    Calls without a translation are left alone (tr() falls back to English). Returns the
    new source and the English texts that had no translation.
    """
    out, pos, missing = [], 0, []
    for start, end, args in calls(src):
        if start < pos:  # nested inside a call already rewritten
            continue
        if len(args) == 2 and args[0] in translations:
            out.append(src[pos:start] + f"tr({args[0]}, {args[1]}, {translations[args[0]]})")
        else:
            if len(args) == 2:
                missing.append(args[0])
            out.append(src[pos:end])
        pos = end
    out.append(src[pos:])
    return "".join(out), missing


if __name__ == "__main__":
    text = open(sys.argv[1]).read()
    found = calls(text)
    print(len(found), "calls,", len(english_sources(text)), "distinct English texts")
