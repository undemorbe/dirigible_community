#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Извлечение контента из выгрузки Craftum (legacy/).

Зачем: при каждой выгрузке Craftum переписывает CSS-хеши и id блоков, поэтому
обычный `git diff` показывает изменения почти во всех файлах даже когда текст
не менялся. Этот скрипт вытаскивает только то, что важно при сверке — тексты,
ссылки и картинки, — пропуская шапку, подвал, скрипты и стили.

Сравнить старую и новую версию страницы:

    git show HEAD:legacy/page10.html > /tmp/old.html
    diff <(python3 tools/legacy_extract.py /tmp/old.html) \\
         <(python3 tools/legacy_extract.py legacy/page10.html)

Зависимостей нет — только стандартная библиотека.
"""

import re
import sys
from html.parser import HTMLParser

VOID = {'img','br','hr','input','meta','link','source','use','path','circle','rect','area','col','embed','param','track','wbr'}

class Node:
    __slots__=('tag','attrs','children','parent','text')
    def __init__(self,tag,attrs,parent):
        self.tag=tag; self.attrs=attrs; self.children=[]; self.parent=parent; self.text=''

class Builder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root=Node('#root',{},None); self.cur=self.root
    def handle_starttag(self,tag,attrs):
        n=Node(tag,dict(attrs),self.cur); self.cur.children.append(n)
        if tag not in VOID: self.cur=n
    def handle_startendtag(self,tag,attrs):
        self.cur.children.append(Node(tag,dict(attrs),self.cur))
    def handle_endtag(self,tag):
        if tag in VOID: return
        n=self.cur
        while n is not None and n.tag!=tag: n=n.parent
        if n is not None and n.parent is not None: self.cur=n.parent
    def handle_data(self,d):
        if d.strip():
            t=Node('#text',{},self.cur); t.text=d; self.cur.children.append(t)

def textof(n):
    if n.tag=='#text': return n.text
    if n.tag in ('script','style','svg'): return ''
    parts=[]
    for c in n.children:
        parts.append(textof(c))
        if c.tag=='br': parts.append('\n')
    return ''.join(parts)

def walk(n,out,in_hf=0):
    a=n.attrs; dt=a.get('data-design-type'); cls=a.get('class') or ''
    if n.tag in ('script','style','svg'): return
    hf = in_hf or ('cli-header' in cls) or ('cli-footer' in cls)
    if dt=='block-wrapper' and not hf:
        out.append(('BLOCK', cls))
    if dt=='background': return
    if n.tag=='img' and not hf:
        out.append(('IMG', a.get('src','')))
        return
    if dt in ('text','title') and not hf:
        t=re.sub(r'[ \t]+',' ',textof(n)).strip()
        if t: out.append(('T', t))
        return
    if dt in ('button','link') and not hf:
        t=re.sub(r'\s+',' ',textof(n)).strip()
        out.append(('B', (a.get('href',''), t)))
        return
    for c in n.children: walk(c,out,hf)

def parse(fn):
    s=open(fn,encoding='utf-8').read()
    b=Builder(); b.feed(s)
    def find(n,tag):
        if n.tag==tag: return n
        for c in n.children:
            r=find(c,tag)
            if r is not None: return r
        return None
    body=find(b.root,'body') or b.root
    out=[]; walk(body,out)
    res=[]
    for it in out:
        if res and res[-1]==it: continue
        res.append(it)
    return res

if __name__=='__main__':
    for k,v in parse(sys.argv[1]):
        if k=='BLOCK': print('\n--BLOCK', v)
        elif k=='T': print('  T:', v)
        elif k=='B': print('  B[%s]: %s' % v)
        elif k=='IMG': print('  IMG:', v.split('/')[-1])
