# Estimate camera roll per clip from near-vertical/horizontal straight lines (Hough). usage: tilt.py clip [lo hi]
import sys,subprocess,numpy as np,cv2
f=sys.argv[1]; lo=float(sys.argv[2]) if len(sys.argv)>2 else 0; hi=float(sys.argv[3]) if len(sys.argv)>3 else None
d=float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f],capture_output=True,text=True).stdout)
hi=min(hi or d,d); W,H=540,960
angs=[]
for t in np.linspace(lo+0.1,hi-0.1,8):
    raw=subprocess.run(['ffmpeg','-loglevel','error','-ss',str(t),'-i',f,'-frames:v','1','-vf',f'scale={W}:{H}','-f','rawvideo','-pix_fmt','gray','-'],capture_output=True).stdout
    if len(raw)<W*H: continue
    g=np.frombuffer(raw,np.uint8).reshape(H,W)
    e=cv2.Canny(g,60,160)
    L=cv2.HoughLinesP(e,1,np.pi/720,80,minLineLength=120,maxLineGap=8)
    if L is None: continue
    for x1,y1,x2,y2 in L.reshape(-1,4):
        a=np.degrees(np.arctan2(y2-y1,x2-x1)); ln=np.hypot(x2-x1,y2-y1)
        if abs(abs(a)-90)<12: dev=(a-90) if a>0 else (a+90)   # vertical line deviation
        elif abs(a)<12 or abs(abs(a)-180)<12: dev=a if abs(a)<12 else (a-180 if a>0 else a+180)
        else: continue
        angs+= [dev]*int(ln//40)
if len(angs)<10: print(f'{f} n/a'); sys.exit()
a=np.array(angs); med=np.median(a); spread=np.percentile(np.abs(a-med),50)
print(f'{f.split("/")[-1]} roll={med:+.2f} spread={spread:.2f} n={len(a)}')
