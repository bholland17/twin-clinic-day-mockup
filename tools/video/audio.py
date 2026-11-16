import subprocess,glob,json,re
U='/mnt/user-data/uploads/'
LEAD,GAP,TAIL=0.9,0.75,2.0
starts=[];durs=[];t=LEAD;parts=[]
for i in range(1,13):
    f=glob.glob(U+'*-%d.m4a'%i)[0]
    out='c%02d.wav'%i
    # trim silence at both ends, keep a short pad, even out loudness
    af=("silenceremove=start_periods=1:start_threshold=-38dB:start_silence=0.12,areverse,"
        "silenceremove=start_periods=1:start_threshold=-38dB:start_silence=0.2,areverse,"
        "highpass=f=70,loudnorm=I=-17:TP=-1.5:LRA=11,afade=t=in:d=0.03")
    subprocess.run(['ffmpeg','-y','-v','error','-i',f,'-af',af,'-ac','1','-ar','48000',out],check=True)
    d=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',out]).decode())
    starts.append(round(t,3));durs.append(round(d,3));t+=d+GAP
total=t-GAP+TAIL
# assemble: silence + clips with gaps
inputs=[];fl=[]
for i in range(12):
    inputs+=['-i','c%02d.wav'%(i+1)]
    fl.append('[%d:a]adelay=%d:all=1[a%d]'%(i,int(starts[i]*1000),i))
fc=';'.join(fl)+';'+''.join('[a%d]'%i for i in range(12))+'amix=inputs=12:normalize=0:duration=longest,apad=whole_dur=%.3f[out]'%total
subprocess.run(['ffmpeg','-y','-v','error']+inputs+['-filter_complex',fc,'-map','[out]','-ar','48000','narration.wav'],check=True)
json.dump({'starts':starts,'durs':durs,'total':round(total,3)},open('timing.json','w'))
for i in range(12): print(i+1,starts[i],durs[i])
print('total',total)
