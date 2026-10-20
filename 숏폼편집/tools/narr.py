# Tighten narration: shrink pauses, concat files, output wav + cut-point candidates
import sys,subprocess,numpy as np,json,wave
sr=48000
def load(f): return np.frombuffer(subprocess.run(['ffmpeg','-loglevel','error','-i',f,'-ac','1','-ar',str(sr),'-f','s16le','-'],capture_output=True).stdout,np.int16).astype(np.float32)/32768
def env(x,hop):
    n=len(x)//hop; return 20*np.log10(np.sqrt((x[:n*hop].reshape(n,hop)**2).mean(1))+1e-9)
THR,MINP,KEEP=-36,0.12,0.04   # pause threshold dB, min pause s, keep each side s
out=[];bounds=[];t=0.0
files=sys.argv[2:]
for fi,f in enumerate(files):
    x=load(f); hop=int(sr*0.01); db=env(x,hop); q=db<THR; n=len(q)
    # speech regions
    segs=[];i=0
    while i<n:
        if not q[i]:
            j=i
            while j<n and not q[j]: j+=1
            segs.append([i,j]); i=j
        else: i+=1
    # merge regions separated by short pauses
    m=[segs[0]]
    for s in segs[1:]:
        if (s[0]-m[-1][1])*0.01<MINP: m[-1][1]=s[1]
        else: m.append(s)
    for k,(a,b) in enumerate(m):
        a=max(0,a*hop-int(KEEP*sr)); b=min(len(x),b*hop+int(KEEP*sr))
        if (b-a)/sr<0.08: continue
        piece=x[a:b].copy(); fade=int(0.005*sr); piece[:fade]*=np.linspace(0,1,fade); piece[-fade:]*=np.linspace(1,0,fade)
        if out: bounds.append(round(t,3))
        out.append(piece); t+=len(piece)/sr
y=np.concatenate(out)
with wave.open(sys.argv[1]+'.wav','wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes((np.clip(y,-1,1)*32767).astype(np.int16).tobytes())
db=env(y,int(sr*0.01))
json.dump({'dur':len(y)/sr,'bounds':bounds,'db':db.round(1).tolist()},open(sys.argv[1]+'.json','w'))
print('tight dur',round(len(y)/sr,2),'phrase bounds',bounds)
