import re, json
M = open('unpacked/word/document.xml','r',encoding='utf-8').read()

# ---- COVER: first <w:sdt> at body start through its matching </w:sdt> ----
body = M.index('<w:body>')+len('<w:body>')
cs = M.index('<w:sdt>', body)
# find matching </w:sdt> by depth
depth=0; i=cs; 
while True:
    o=M.find('<w:sdt>',i); c=M.find('</w:sdt>',i)
    if c==-1: break
    if o!=-1 and o<c:
        depth+=1; i=o+7
    else:
        depth-=1; i=c+8
        if depth==0:
            ce=c+8; break
cover=M[cs:ce]
open('._cover.xml','w',encoding='utf-8').write(cover)
print("COVER len",len(cover),"start",cs,"end",ce)
print("COVER rIds:",sorted(set(re.findall(r'r:(?:embed|id|link)="(rId\d+)"',cover))))
print("COVER pStyles:",sorted(set(re.findall(r'<w:pStyle w:val="([^"]+)"',cover))))
print("COVER docPr ids:",re.findall(r'<wp:docPr id="(\d+)"',cover))

# ---- BACK PAGE: from the paragraph that starts the back cover to end of body ----
final_sect = M.rindex('<w:sectPr')
# back page begins at the <w:p ...> containing the full-bleed rId21 image's paragraph.
# find rId21 embed, then back up to the <w:p that contains it
e21 = M.index('r:embed="rId21"')
# back up to nearest '<w:p ' or '<w:p>' before e21
pstart = max(M.rfind('<w:p ',0,e21), M.rfind('<w:p>',0,e21))
# but the contact textbox/rect likely is in the SAME paragraph (it's one para with anchors). confirm:
backstart = pstart
back = M[backstart:]   # to end of </w:body>
# trim to before </w:body>
endbody = back.index('</w:body>')
back = back[:endbody]
open('._back.xml','w',encoding='utf-8').write(back)
print("\nBACK start",backstart,"len",len(back))
print("BACK rIds:",sorted(set(re.findall(r'r:(?:embed|id|link)="(rId\d+)"',back))))
print("BACK pStyles:",sorted(set(re.findall(r'<w:pStyle w:val="([^"]+)"',back))))
print("BACK docPr ids:",re.findall(r'<wp:docPr id="(\d+)"',back))

# ---- master rels of interest ----
rels = open('unpacked/word/_rels/document.xml.rels','r',encoding='utf-8').read()
print("\n--- master rels for cover/back ids ---")
for rid in ['rId11','rId12','rId21','rId22','rId23','rId24','rId25','rId26','rId27']:
    m=re.search(r'<Relationship Id="'+rid+'"[^>]*/>',rels)
    print(rid, m.group(0) if m else "MISSING")
