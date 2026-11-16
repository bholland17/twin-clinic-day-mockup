import subprocess,glob,json,re,sys
U=sys.argv[1] if len(sys.argv)>1 else '/mnt/user-data/uploads/'
LEAD,GAP,TAIL=0.9,0.8,2.0
def segs(f):
    out=subprocess.run(['ffmpeg','-hide_banner','-i',f,'-af','highpass=f=90,silencedetect=noise=-38dB:d=0.12','-f','null','-'],capture_output=True,text=True).stderr
    dur=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f]).decode())
    ss=[float(x) for x in re.findall(r'silence_start: ([\d.]+)',out)]; se=[float(x) for x in re.findall(r'silence_end: ([\d.]+)',out)]
    if len(se)<len(ss): se.append(dur)
    sound=[];t=0.0
    for a,b in zip(ss,se):
        if a>t+0.005: sound.append((t,a))
        t=b
    if t<dur-0.005: sound.append((t,dur))
    return sound,dur
starts=[];durs=[];t=LEAD
for i in range(1,13):
    f=glob.glob(U+'*-%d.m4a'%i)[0]
    sound,dur=segs(f)
    # speech = segments at least 0.2 s long; shorter blips at the edges are taps on the phone
    # taps: a sound touching the very start or end of the file with a clear silence next to it, and tiny clicks at the edges
    real=list(sound)
    if len(real)>1 and real[0][0]<0.02 and real[1][0]-real[0][1]>=0.4: real=real[1:]
    if len(real)>1 and real[-1][1]>dur-0.02 and real[-1][0]-real[-2][1]>=0.4: real=real[:-1]
    while len(real)>1 and real[0][1]-real[0][0]<0.08: real=real[1:]
    while len(real)>1 and real[-1][1]-real[-1][0]<0.08: real=real[:-1]
    a=max(real[0][0]-0.10,0); b=min(real[-1][1]+0.18,dur)
    print(i,'speech %.2f to %.2f of %.2f'%(a,b,dur))
    d=b-a
    af="atrim=%.3f:%.3f,asetpts=PTS-STARTPTS,highpass=f=70,loudnorm=I=-17:TP=-1.5:LRA=11,afade=t=in:d=0.05,afade=t=out:st=%.3f:d=0.12"%(a,b,d-0.12)
    subprocess.run(['ffmpeg','-y','-v','error','-i',f,'-af',af,'-ac','1','-ar','48000','c%02d.wav'%i],check=True)
    d=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0','c%02d.wav'%i]).decode())
    starts.append(round(t,3));durs.append(round(d,3));t+=d+GAP
total=t-GAP+TAIL
inputs=[];fl=[]
for i in range(12):
    inputs+=['-i','c%02d.wav'%(i+1)]; fl.append('[%d:a]adelay=%d:all=1[a%d]'%(i,int(starts[i]*1000),i))
fc=';'.join(fl)+';'+''.join('[a%d]'%i for i in range(12))+'amix=inputs=12:normalize=0:duration=longest,apad=whole_dur=%.3f[out]'%total
subprocess.run(['ffmpeg','-y','-v','error']+inputs+['-filter_complex',fc,'-map','[out]','-ar','48000','narration.wav'],check=True)
json.dump({'starts':starts,'durs':durs,'total':round(total,3)},open('timing.json','w'))
print('starts',starts);print('durs',durs);print('total',round(total,2))
