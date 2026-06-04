import re, os, glob
# master header/footer parts and their rels/media
print("=== master word/ header+footer files ===")
for f in sorted(glob.glob('unpacked/word/header*.xml')+glob.glob('unpacked/word/footer*.xml')):
    print(os.path.basename(f))
print("\n=== their _rels (rIds + targets, images referenced) ===")
for f in sorted(glob.glob('unpacked/word/_rels/header*.xml.rels')+glob.glob('unpacked/word/_rels/footer*.xml.rels')):
    txt=open(f,encoding='utf-8').read()
    rels=re.findall(r'<Relationship [^>]*/>',txt)
    print(os.path.basename(f),'->',rels if rels else 'NO RELS')
print("\n=== r:embed/r:id used inside each header/footer ===")
for f in sorted(glob.glob('unpacked/word/header*.xml')+glob.glob('unpacked/word/footer*.xml')):
    txt=open(f,encoding='utf-8').read()
    ids=sorted(set(re.findall(r'r:(?:embed|id|link)="(rId\d+)"',txt)))
    print(os.path.basename(f), ids)

# FO media + content types + parts
print("\n=== FO media files ===")
print([os.path.basename(x) for x in glob.glob('unpacked_fulloffer/word/media/*')])
print("\n=== FO [Content_Types].xml ===")
print(open('unpacked_fulloffer/[Content_Types].xml',encoding='utf-8').read())

# styles presence
fo_styles=open('unpacked_fulloffer/word/styles.xml',encoding='utf-8').read()
m_styles=open('unpacked/word/styles.xml',encoding='utf-8').read()
for sid in ['Title','NoSpacing','SWDDetails']:
    print(f"\n--- style '{sid}': in FO={('w:styleId=\"'+sid+'\"') in fo_styles}  in MASTER={('w:styleId=\"'+sid+'\"') in m_styles}")
