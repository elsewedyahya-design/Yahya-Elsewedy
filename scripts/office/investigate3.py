import re
FO=open('unpacked_fulloffer/word/document.xml','r',encoding='utf-8').read()
body=FO.index('<w:body>')+len('<w:body>')
# cover section ends at the paragraph holding the first sectPr
sp=FO.index('<w:sectPr',body)
# the sectPr is inside <w:p><w:pPr>...</w:pPr></w:p>; find enclosing <w:p ...> start and </w:p> end
pstart=max(FO.rfind('<w:p ',body,sp),FO.rfind('<w:p>',body,sp))
spclose=FO.index('</w:sectPr>',sp)+len('</w:sectPr>')
pend=FO.index('</w:p>',spclose)+len('</w:p>')
print("FO body start",body)
print("FO cover-para start",pstart,"end",pend)
print("FO cover sectPr paragraph:")
print(FO[pstart:pend])
# final body-level sectPr (last sectPr, child of body)
fsp=FO.rindex('<w:sectPr')
fspend=FO.index('</w:sectPr>',fsp)+len('</w:sectPr>')
print("\nFO FINAL body sectPr start",fsp,"end",fspend,"  (body ends at",FO.index('</w:body>'),")")
print(FO[fsp:fspend])
open('._fo_finalsectpr.xml','w',encoding='utf-8').write(FO[fsp:fspend])

# master styles: extract NoSpacing, SWDDetails full <w:style ...>...</w:style>
MS=open('unpacked/word/styles.xml','r',encoding='utf-8').read()
def extract_style(sid):
    m=re.search(r'<w:style [^>]*w:styleId="'+re.escape(sid)+'"',MS)
    if not m: return None
    s=MS.rfind('<w:style ',0,m.end())
    e=MS.index('</w:style>',m.start())+len('</w:style>')
    return MS[s:e]
for sid in ['NoSpacing','SWDDetails','Title']:
    st=extract_style(sid)
    if st:
        based=re.findall(r'<w:basedOn w:val="([^"]+)"',st)
        link=re.findall(r'<w:link w:val="([^"]+)"',st)
        nxt=re.findall(r'<w:next w:val="([^"]+)"',st)
        print(f"\n=== {sid}: basedOn={based} link={link} next={nxt} len={len(st)}")
        if sid!='Title':
            open(f'._style_{sid}.xml','w',encoding='utf-8').write(st)

# verify back block start
back=open('._back.xml',encoding='utf-8').read()
print("\nBACK head 300:",back[:300])
print("BACK has txbxContent:", 'txbxContent' in back, " has v:rect/contact:", ('Elsewedy' in back or 'www.' in back or 'SWDDetails' in back))
print("BACK tail 200:",back[-200:])
