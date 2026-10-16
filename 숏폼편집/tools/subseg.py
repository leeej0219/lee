# Detect subtitle change points from a white-text band. usage: subseg.py video y0 y1 out_prefix
import sys, subprocess, numpy as np
from PIL import Image
vid, y0, y1, out = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
W, FPS = 540, 10
probe = subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height','-of','csv=p=0',vid],capture_output=True,text=True).stdout.strip().split(',')
w, h = int(probe[0]), int(probe[1]); H = int(h*W/w)
a, b = int(H*y0), int(H*y1)
raw = subprocess.run(['ffmpeg','-loglevel','error','-i',vid,'-vf',f'fps={FPS},scale={W}:{H}','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True).stdout
fr = np.frombuffer(raw,np.uint8).reshape(-1,H,W,3)
band = fr[:,a:b].astype(int)
mn, mx = band.min(-1), band.max(-1)
mask = (mn>215)&(mx-mn<30)  # white, unsaturated
# require dark nearby (outline): dilate dark map
dark = band.max(-1)<90
from numpy.lib.stride_tricks import sliding_window_view as sw
pad = np.pad(dark,((0,0),(2,2),(2,2)))
near = sw(pad,(5,5),axis=(1,2)).any(axis=(-1,-2))
m = mask&near
cnt = m.sum((1,2))
segs=[]; cur=None
for i in range(len(m)):
    has = cnt[i]>40
    if not has:
        if cur: segs.append(cur); cur=None
        continue
    if cur is None: cur=[i,i]; ref=m[i]; continue
    inter=(m[i]&ref).sum(); uni=(m[i]|ref).sum()
    if inter/uni<0.35: segs.append(cur); cur=[i,i]; ref=m[i]
    else: cur[1]=i
if cur: segs.append(cur)
segs=[s for s in segs if s[1]-s[0]>=2]
crops=[]
with open(out+'.tsv','w') as f:
    for k,(s,e) in enumerate(segs):
        mid=(s+e)//2
        f.write(f'{k}\t{s/FPS:.1f}\t{(e+1)/FPS:.1f}\t{(e+1-s)/FPS:.1f}\n')
        crops.append(fr[mid,a:b])
for p in range(0,len(crops),16):
    chunk=crops[p:p+16]
    img=Image.fromarray(np.concatenate(chunk,0))
    from PIL import ImageDraw
    d=ImageDraw.Draw(img)
    for j in range(len(chunk)): d.text((3,j*(b-a)+2),str(p+j),fill=(255,255,0))
    img.save(f'{out}_segs{p//16}.png')
print(len(segs),'segments')
