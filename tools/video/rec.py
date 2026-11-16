import asyncio,base64,json,os,time,shutil
from playwright.async_api import async_playwright
tm=json.load(open('timing.json')); TOTAL=tm['total']
W,H,DSF=1920,1080,1
async def main():
    shutil.rmtree('frames',ignore_errors=True); os.makedirs('frames')
    async with async_playwright() as p:
        b=await p.chromium.launch()
        ctx=await b.new_context(viewport={'width':W,'height':H},device_scale_factor=DSF)
        pg=await ctx.new_page()
        await pg.goto('file:///home/claude/twin-clinic-day-mockup/demo.html')
        await pg.add_style_tag(content='#play{display:none} html{zoom:1.5}')
        await pg.wait_for_timeout(800)
        cdp=await ctx.new_cdp_session(pg)
        frames=[]
        async def on(ev):
            frames.append((ev['metadata']['timestamp'],ev['data']))
            await cdp.send('Page.screencastFrameAck',{'sessionId':ev['sessionId']})
        cdp.on('Page.screencastFrame',lambda ev: asyncio.ensure_future(on(ev)))
        await cdp.send('Page.startScreencast',{'format':'jpeg','quality':92,'maxWidth':1920,'maxHeight':1080,'everyNthFrame':1})
        await pg.wait_for_timeout(500)
        t0=time.time(); await pg.evaluate('tour()')
        await pg.wait_for_timeout(int((TOTAL+1.0)*1000))
        await cdp.send('Page.stopScreencast'); await b.close()
    frames.sort(key=lambda x:x[0])
    # keep last frame before t0 as the opening frame
    pre=[f for f in frames if f[0]<=t0]; post=[f for f in frames if f[0]>t0]
    seq=([(t0,pre[-1][1])] if pre else [])+post
    lines=[]
    for i,(ts,data) in enumerate(seq):
        fn='frames/f%05d.jpg'%i; open(fn,'wb').write(base64.b64decode(data))
        nxt=seq[i+1][0] if i+1<len(seq) else t0+TOTAL
        d=max(nxt-ts,0.001)
        lines.append("file '%s'\nduration %.4f"%(fn,d))
    lines.append("file 'frames/f%05d.jpg'"%(len(seq)-1))
    open('list.txt','w').write('\n'.join(lines)+'\n')
    print('frames',len(seq),'span',seq[-1][0]-t0)
asyncio.run(main())
