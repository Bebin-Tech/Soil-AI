"""Install the OFL-licensed Noto Sans Tamil font from its official repository."""
import urllib.request
from pathlib import Path

root=Path(__file__).resolve().parents[1]/'backend/app/assets/fonts'
root.mkdir(parents=True,exist_ok=True)
base='https://raw.githubusercontent.com/notofonts/noto-fonts/main/'
for source,target in [('hinted/ttf/NotoSansTamil/NotoSansTamil-Regular.ttf','NotoSansTamil-Regular.ttf'),('hinted/ttf/NotoSans/NotoSans-Regular.ttf','NotoSans-Regular.ttf'),('LICENSE','OFL.txt')]:
    with urllib.request.urlopen(base+source,timeout=30) as response:
        content=response.read(10*1024*1024)
    (root/target).write_bytes(content)
    print('Installed',target)
from fontTools.merge import Merger
font=Merger().merge([str(root/'NotoSans-Regular.ttf'),str(root/'NotoSansTamil-Regular.ttf')])
for name in font['name'].names:
    if name.nameID in [1,3,4,6]:
        name.string=('SoilAIRecords' if name.nameID==6 else 'SoilAI Records').encode(name.getEncoding())
font.save(root/'SoilAI-Regular.ttf')
print('Built SoilAI Records font with Latin and Tamil shaping tables')
