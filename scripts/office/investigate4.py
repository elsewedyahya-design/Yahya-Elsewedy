import re
rels=open('unpacked/word/_rels/document.xml.rels','r',encoding='utf-8').read()
for rid in ['rId12','rId17','rId18','rId19','rId20','rId21','rId22','rId23','rId24','rId25','rId26','rId27']:
    m=re.search(r'<Relationship Id="'+rid+'"[^>]*/>',rels)
    print(rid, (m.group(0) if m else 'MISSING'))
# also: cover block - re-extract & list ALL rIds incl nested, verify completeness
M=open('unpacked/word/document.xml','r',encoding='utf-8').read()
cover=open('._cover.xml',encoding='utf-8').read()
print("\nCOVER all rIds:",sorted(set(re.findall(r'r:(?:embed|id|link)="(rId\d+)"',cover))))
print("COVER well-formed-ish: starts",cover[:30],"... ends",cover[-30:])
