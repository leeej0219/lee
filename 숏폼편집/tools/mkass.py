# Build ASS subtitles in the reference style. usage: mkass.py subs.tsv end_time out.ass
import sys
rows=[l.rstrip('\n').split('\t') for l in open(sys.argv[1]) if l.strip()]
end=float(sys.argv[2])
def ts(t): h=int(t//3600); m=int(t%3600//60); s=t%60; return f'{h}:{m:02d}:{s:05.2f}'
head='''[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Body,Pretendard,56,&H00FFFFFF,&H00FFFFFF,&H00141414,&H80000000,-1,0,0,0,100,100,-1,0,1,3.2,1.5,5,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
ev=[]
for i,(t,txt) in enumerate(rows):
    s=float(t); e=float(rows[i+1][0]) if i+1<len(rows) else end
    ev.append(f'Dialogue: 0,{ts(s)},{ts(e)},Body,,0,0,0,,{{\\pos(540,1305)}}{txt}')
open(sys.argv[3],'w').write(head+'\n'.join(ev)+'\n')
print(len(ev),'subs')
