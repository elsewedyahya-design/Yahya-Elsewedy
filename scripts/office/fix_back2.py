import re
M=open('unpacked/word/document.xml','r',encoding='utf-8').read()
body=M.index('<w:body>')+len('<w:body>')
endbody=M.index('</w:body>')
e21=M.index('r:embed="rId21"')
tok=re.compile(r'<w:p(?:\s[^>]*?)?>|</w:p>|<w:p/>|<w:p\s[^>]*?/>')
# stack from body to e21
stack=[]
opens=closes=selfc=0
for m in tok.finditer(M, body, e21):
    g=m.group()
    if g.endswith('/>'):   # self-closing empty paragraph
        selfc+=1; continue
    if g.startswith('</'):
        closes+=1
        if stack: stack.pop()
    else:
        opens+=1; stack.append(m.start())
print("up to e21: opens",opens,"closes",closes,"selfclose",selfc,"stackdepth",len(stack))
print("outermost enclosing <w:p> start:", stack[0] if stack else None)
if stack:
    s=stack[0]
    print("enclosing para open tag:", M[s:s+120])
    # find its matching close after e21
    depth=0; pos=s; endp=None
    for m in tok.finditer(M, s, endbody):
        g=m.group()
        if g.endswith('/>'): continue
        if g.startswith('</'):
            depth-=1
            if depth==0: endp=m.end(); break
        else: depth+=1
    print("enclosing para end:", endp)
    back=M[s:endbody]
    open('._back.xml','w',encoding='utf-8').write(back)
    print("BACK len",len(back),"HEAD120:",back[:120])
    print("TAIL120:",back[-120:])
    print("rIds:",sorted(set(re.findall(r'r:(?:embed|id|link)="(rId\d+)"',back))))
    print("ends sectPr:",back.rstrip().endswith('</w:sectPr>')," has contact txbx:",'txbxContent' in back)
