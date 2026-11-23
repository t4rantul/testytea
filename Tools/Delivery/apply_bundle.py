#!/usr/bin/env python3
"""Apply one Basalt text bundle as a set of repository file changes."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path, PurePosixPath
import sys

PREFIX = "%%%"
VERSION = "1"

class BundleError(Exception):
    pass

def directive(line: str) -> bool:
    return line.startswith(PREFIX) and not line.startswith(PREFIX + "%")

def unescape(line: str) -> str:
    return line[1:] if line.startswith(PREFIX + "%") else line

def parse(text: str, incoming: str = "Incoming") -> dict:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    i = 0
    def take(expected=None):
        nonlocal i
        while i < len(lines) and not lines[i].strip():
            i += 1
        if i >= len(lines) or not directive(lines[i]):
            raise BundleError(f"line {i + 1}: expected {expected or 'a directive'}")
        raw = lines[i][len(PREFIX):].strip()
        i += 1
        key, _, arg = raw.partition(" ")
        return key, arg.strip(), i
    def content():
        nonlocal i
        out=[]
        while i < len(lines) and not directive(lines[i]):
            out.append(unescape(lines[i])); i += 1
        return "\n".join(out)
    key, arg, line = take("basalt-bundle")
    if (key, arg) != ("basalt-bundle", VERSION):
        raise BundleError(f"line {line}: expected '%%% basalt-bundle {VERSION}'")
    key, message, line = take("message")
    if key != "message" or not message:
        raise BundleError(f"line {line}: expected '%%% message <summary>'")
    body=""; ops=[]; claimed=set()
    def path_arg(value, lineno):
        if not value or "\\" in value:
            raise BundleError(f"line {lineno}: invalid path")
        p=PurePosixPath(value)
        if p.is_absolute() or str(p) != value or any(x in ("", ".", "..") for x in p.parts):
            raise BundleError(f"line {lineno}: unsafe or non-normalized path '{value}'")
        if p.parts[0] == ".git" or value.startswith(".github/workflows/"):
            raise BundleError(f"line {lineno}: protected path '{value}'")
        incoming_dir=incoming.strip("/")
        if value == incoming_dir or value.startswith(incoming_dir + "/"):
            raise BundleError(f"line {lineno}: incoming files cannot be changed by a bundle")
        return value
    def claim(p, lineno):
        if p in claimed: raise BundleError(f"line {lineno}: '{p}' is changed more than once")
        claimed.add(p)
    while True:
        while i < len(lines) and not lines[i].strip(): i += 1
        if i == len(lines): break
        key,arg,line=take()
        if key == "body":
            if ops or body: raise BundleError(f"line {line}: body must follow message")
            body=content().strip("\n")
        elif key == "write":
            p=path_arg(arg,line); claim(p,line); data=content()
            data=data.rstrip("\n") + "\n"
            ops.append(("write",p,data,line))
        elif key == "delete":
            p=path_arg(arg,line); claim(p,line)
            if content(): raise BundleError(f"line {line}: delete takes no content")
            ops.append(("delete",p,"",line))
        elif key == "rename":
            a,sep,b=arg.partition(" ")
            if not sep: raise BundleError(f"line {line}: rename needs source and target")
            a=path_arg(a,line); b=path_arg(b.strip(),line); claim(a,line); claim(b,line)
            if content(): raise BundleError(f"line {line}: rename takes no content")
            ops.append(("rename",a,b,line))
        elif key == "edit":
            p=path_arg(arg,line); claim(p,line)
            if content().strip(): raise BundleError(f"line {line}: expected search directive")
            pairs=[]
            while True:
                k,a,ln=take("search")
                if k == "end": break
                if k != "search" or a not in ("", "all"):
                    raise BundleError(f"line {ln}: expected search, search all, or end")
                old=content()
                k,_,rl=take("replace")
                if k != "replace": raise BundleError(f"line {rl}: expected replace")
                new=content()
                if not old.strip(): raise BundleError(f"line {ln}: search cannot be empty")
                pairs.append((old,new,a == "all",ln))
            if not pairs: raise BundleError(f"line {line}: edit has no replacements")
            ops.append(("edit",p,pairs,line))
        else:
            raise BundleError(f"line {line}: unknown directive '{key}'")
    if not ops: raise BundleError("bundle contains no changes")
    return {"message":message,"body":body,"operations":ops}

def safe_file(root: Path, rel: str, lineno: int) -> Path:
    root=root.resolve(); p=root / rel
    if root not in p.parent.resolve().parents and p.parent.resolve() != root:
        raise BundleError(f"line {lineno}: path escapes the repository through a symlink")
    if p.is_symlink(): raise BundleError(f"line {lineno}: symlink targets are not allowed")
    return p

def replace_text(text: str, old: str, new: str, all_matches: bool, lineno: int, path: str) -> str:
    n=text.count(old)
    old_lines=[x.strip() for x in old.split("\n")]
    while old_lines and old_lines[0] == "": old_lines.pop(0)
    while old_lines and old_lines[-1] == "": old_lines.pop()
    whole_line = ("\n" not in old and any(line.strip() == old.strip() for line in text.splitlines()))
    if n and not whole_line:
        if n > 1 and not all_matches:
            raise BundleError(f"line {lineno}: search matches {n} times in '{path}'")
        return text.replace(old,new)
    if not old_lines: raise BundleError(f"line {lineno}: empty search in '{path}'")
    spans=[]; start=0
    while start < len(text):
        end=text.find("\n",start)
        if end < 0: spans.append((start,len(text))); break
        spans.append((start,end)); start=end+1
    stripped=[text[a:b].strip() for a,b in spans]; width=len(old_lines)
    matches=[x for x in range(len(spans)-width+1) if stripped[x:x+width] == old_lines]
    if not matches: raise BundleError(f"line {lineno}: search text not found in '{path}'")
    if len(matches)>1 and not all_matches:
        raise BundleError(f"line {lineno}: search matches {len(matches)} times in '{path}' ignoring indentation")
    out=[]; cursor=0
    for first in matches:
        a=spans[first][0]; end=spans[first+width-1][1]
        newline=end < len(text) and text[end] == "\n"
        original=text[a:end]
        indent=original[:len(original)-len(original.lstrip())]
        replacement=new
        if replacement and indent and not replacement.startswith(indent):
            replacement="\n".join((indent+part) if part else "" for part in replacement.split("\n"))
        out.append(text[cursor:a])
        if replacement:
            out.append(replacement)
            if newline and not replacement.endswith("\n"): out.append("\n")
        cursor=end+(1 if newline else 0)
    out.append(text[cursor:])
    return "".join(out)

def apply(bundle: dict, root: Path) -> list[str]:
    root=root.resolve(); staged={}; changed=[]
    def read(rel,line):
        if rel in staged:
            if staged[rel] is None: raise BundleError(f"line {line}: '{rel}' was deleted earlier")
            return staged[rel]
        p=safe_file(root,rel,line)
        if not p.is_file(): raise BundleError(f"line {line}: '{rel}' does not exist")
        return p.read_text(encoding="utf-8")
    for kind,p,value,line in bundle["operations"]:
        if kind == "write": staged[p]=value
        elif kind == "delete":
            if p not in staged and not safe_file(root,p,line).is_file(): raise BundleError(f"line {line}: '{p}' does not exist")
            staged[p]=None
        elif kind == "rename":
            if p in staged and staged[p] is None: raise BundleError(f"line {line}: source '{p}' was deleted")
            if p not in staged and not safe_file(root,p,line).is_file(): raise BundleError(f"line {line}: '{p}' does not exist")
            if value in staged and staged[value] is not None or (value not in staged and safe_file(root,value,line).exists()):
                raise BundleError(f"line {line}: target '{value}' already exists")
            staged[value]=read(p,line); staged[p]=None
        elif kind == "edit":
            data=read(p,line)
            for old,new,all_matches,ln in value:
                data=replace_text(data,old,new,all_matches,ln,p)
            staged[p]=data
    for rel,data in staged.items():
        safe_file(root,rel,0)
        if data is not None and (root/rel).exists() and (root/rel).is_dir():
            raise BundleError(f"cannot replace directory '{rel}'")
    for rel,data in staged.items():
        p=root/rel
        if data is None:
            if p.exists(): p.unlink()
        else:
            p.parent.mkdir(parents=True,exist_ok=True)
            tmp=p.with_name(p.name+".bundle-tmp")
            tmp.write_text(data,encoding="utf-8",newline="")
            os.replace(tmp,p)
        changed.append(rel)
    return changed

def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("bundles",nargs="*")
    ap.add_argument("--root",default=".")
    ap.add_argument("--incoming",default="Incoming")
    ap.add_argument("--summary-file")
    args=ap.parse_args(argv); root=Path(args.root).resolve()
    paths=[Path(x).resolve() for x in args.bundles]
    if not paths:
        d=root/args.incoming
        paths=sorted(d.rglob("*.bundle")) if d.is_dir() else []
    summaries=[]
    try:
        if not paths: print("No bundles found."); return 0
        for path in paths:
            if root not in path.parents: raise BundleError(f"bundle '{path}' is outside the repository")
            rel=path.relative_to(root).as_posix()
            bundle=parse(path.read_text(encoding="utf-8"),args.incoming)
            changed=apply(bundle,root)
            path.unlink()
            summaries.append({"bundle":rel,"message":bundle["message"],"body":bundle["body"],"changed":changed})
            print(f"Applied {rel}: {len(changed)} file(s)")
        if args.summary_file:
            out=Path(args.summary_file); out.parent.mkdir(parents=True,exist_ok=True)
            out.write_text(json.dumps(summaries,indent=2)+"\n",encoding="utf-8")
    except (BundleError,OSError,UnicodeError) as e:
        print(f"error: {e}",file=sys.stderr); return 1
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
