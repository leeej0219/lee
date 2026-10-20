import sys,json,wave,numpy as np,sherpa_onnx
M=sys.argv[1]; W=sys.argv[2]; J=sys.argv[3]
rec=sherpa_onnx.OfflineRecognizer.from_sense_voice(model=f'{M}/model.int8.onnx',tokens=f'{M}/tokens.txt',language='ko',use_itn=True,num_threads=4)
w=wave.open(W); sr=w.getframerate(); x=np.frombuffer(w.readframes(w.getnframes()),np.int16).astype(np.float32)/32768
d=json.load(open(J)); b=[0]+d['bounds']+[d['dur']]
for a,c in zip(b,b[1:]):
    s=rec.create_stream(); s.accept_waveform(sr,x[int(a*sr):int(c*sr)]); rec.decode_stream(s)
    r=s.result
    ts=' '.join(f'{t}@{a+tt:.2f}' for t,tt in zip(r.tokens,r.timestamps)) if r.timestamps else ''
    print(f'{a:6.2f}-{c:6.2f} | {r.text}'); print('     ',ts)
