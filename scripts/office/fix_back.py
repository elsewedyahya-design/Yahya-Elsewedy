import re
M=open('unpacked/word/document.xml','r',encoding='utf-8').read()
body=M.index('<w:body>')+len('<w:body>')
endbody=M.index('</w:body>')
e21=M.index('r:embed="rId21"')
# depth-aware: find top-level <w:p> spans in body; locate the one containing e21
tok=re.compile(r'<w:p(?:\s[^>]*)?>|</w:p>')
depth=0; starts=[]; spans=[]
for m in tok.finditer(M, body, endbody):
    if m.group().startswith('</'):
        depth-=1
        if depth==0:
            spans.append((starts.pop(), m.end()))
    else:
        if depth==0: starts.append(m.start())
        depth+=1
# find top-level paragraph containing e21
backpara=None
for s,e in spans:
    if s<=e21<e:
        backpara=(s,e); break
print("top-level para containing rId21:", backpara)
bs=backpara[0]
back=M[bs:endbody]
open('._back.xml','w',encoding='utf-8').write(back)
print("BACK len",len(back))
print("HEAD200:",back[:200])
print("TAIL150:",back[-150:])
print("BACK rIds:",sorted(set(re.findall(r'r:(?:embed|id|link)="(rId\d+)"',back))))
# sanity: count top-level paragraphs in back + presence of final sectPr as last child
print("ends with sectPr:", back.rstrip().endswith('</w:sectPr>'))
print("has txbxContent(contact):", 'txbxContent' in back)
