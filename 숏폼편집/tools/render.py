# Pick best window per shot (sharp + stable) and render vertical 1080x1920 cut edit with narration
import json,subprocess,numpy as np,sys,os
RAW,OUT=sys.argv[1],sys.argv[2]
cuts=json.load(open(f'{OUT}/cuts.json'))
plan=json.load(open(f'{OUT}/plan.json'))   # [[file, lo, hi, (zoom)], ...] one per shot
MODE=os.environ.get('MODE','stable')  # stable | dynamic
assert len(plan)==len(cuts)-1
def dur(f): return float(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f],capture_output=True,text=True).stdout)
def frames(f,lo,hi,fps=10,w=135,h=240):
    raw=subprocess.run(['ffmpeg','-loglevel','error','-ss',str(lo),'-to',str(hi),'-i',f,'-vf',f'fps={fps},scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},format=gray','-f','rawvideo','-'],capture_output=True).stdout
    return np.frombuffer(raw,np.uint8).reshape(-1,h,w).astype(np.float32)
chosen=[]
for i,entry in enumerate(plan):
    name,lo,hi=entry[:3]
    f=f'{RAW}/{name}'; need=cuts[i+1]-cuts[i]; D=dur(f)
    hi=min(hi if hi else D, D); lo=lo or 0
    speed=1.0
    if hi-lo<need: speed=(hi-lo)/need; chosen.append((f,lo,hi,speed,need)); continue
    fr=frames(f,lo,hi)
    lap=np.abs(fr[:,2:,1:-1]+fr[:,:-2,1:-1]+fr[:,1:-1,2:]+fr[:,1:-1,:-2]-4*fr[:,1:-1,1:-1]).mean((1,2))
    mot=np.r_[0,np.abs(np.diff(fr,axis=0)).mean((1,2))]
    sharp=lap/(lap.max()+1e-6); shake=mot/(np.percentile(mot,95)+1e-6)
    if MODE=='dynamic':
        # favor movement, but drop blurry frames (motion blur / shake)
        mv=np.clip(mot/(np.percentile(mot,90)+1e-6),0,1.5)
        blur=(sharp<0.45*np.percentile(sharp,90)).astype(float)
        score=mv+0.4*sharp-2.0*blur
    else:
        score=sharp-0.5*np.clip(shake,0,2)
    win=max(1,int(round(need*10)))
    cs=np.convolve(score,np.ones(win)/win,'valid')
    k=int(np.argmax(cs)); start=lo+k/10
    chosen.append((f,start,start+need,1.0,need))
    print(f'shot{i+1:2d} {name:9s} {start:7.2f}-{start+need:7.2f} ({need:.2f}s)')
os.makedirs(f'{OUT}/shots',exist_ok=True); lst=[]
for i,(f,s,e,speed,need) in enumerate(chosen):
    o=f'{OUT}/shots/s{i:02d}.mp4'; lst.append(o)
    z=plan[i][3] if len(plan[i])>3 else 0
    vf=f'setpts=(PTS-STARTPTS)/{speed},scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30'
    if z:  # slow push-in: 1.0 -> 1+z over the shot
        n=int(round(need*30))
        vf+=f",scale=2160:3840,zoompan=z='1+{z}*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=1:s=1080x1920:fps=30"
    vf+=f',format=yuv420p,setsar=1,trim=duration={need}'
    if speed!=1.0: print(f'shot{i+1:2d} {os.path.basename(f):9s} slowed x{speed:.2f}')
    subprocess.run(['ffmpeg','-loglevel','error','-y','-ss',str(s),'-to',str(e if speed==1 else s+(e-s)),'-i',f,'-an','-vf',vf,'-c:v','libx264','-preset','medium','-crf','16','-r','30',o],check=True)
open(f'{OUT}/shots/list.txt','w').write(''.join(f"file '{os.path.abspath(p)}'\n" for p in lst))
