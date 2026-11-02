from pathlib import Path
import asyncio, math, random, wave, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import markdown
from playwright.async_api import async_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"demo"
SHOTS=ROOT/"screenshots"
DOCS=ROOT/"docs"
for folder in (OUT,SHOTS,DOCS): folder.mkdir(exist_ok=True)
TMP=OUT/"_frames"
TMP.mkdir(exist_ok=True)

def font(size,bold=False):
    candidates = [
      "/usr/share/fonts/truetype/noto/NotoSansArabic-Bold.ttf" if bold else "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
      "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        if Path(path).exists(): return ImageFont.truetype(path,size)
    return ImageFont.load_default()

async def build():
    async with async_playwright() as p:
        browser=await p.chromium.launch(headless=True,args=["--no-sandbox"])
        page=await browser.new_page(viewport={"width":1600,"height":900},device_scale_factor=1)
        await page.goto((ROOT/"index.html").as_uri(),wait_until="load")
        await page.emulate_media(reduced_motion="reduce")
        await page.wait_for_timeout(500)
        async def snap(name):
            await page.wait_for_timeout(300)
            await page.screenshot(path=str(TMP/(name+".png")),animations="disabled")
        await snap("01_home")
        await page.screenshot(path=str(SHOTS/"home.png"),full_page=True,animations="disabled")
        await page.locator("#queryInput").fill("یه لپ‌تاپ تا ۷۰ میلیون می‌خوام")
        await page.locator(".send").click()
        await snap("02_search")
        await page.locator("#personaArad").click()
        await snap("03_persona")
        await page.locator("#personaNiki").click()
        await page.locator("#queryInput").fill("این بار برای گیم لپ‌تاپ می‌خوام")
        await page.locator(".send").click()
        await snap("04_new_need")
        await page.locator("#personalToggle").click()
        await snap("05_privacy")
        await page.locator("#personalToggle").click()
        await page.locator('[data-details="la"]').first.click()
        await snap("06_explain")
        await page.locator("#modalClose").click()
        await page.locator('[data-compare="la"]').click()
        await page.locator('[data-compare="lb"]').click()
        await page.locator("#openCompare").click()
        await snap("07_compare")
        mobile=await browser.new_page(viewport={"width":390,"height":844},device_scale_factor=1)
        await mobile.goto((ROOT/"index.html").as_uri())
        await mobile.wait_for_timeout(350)
        await mobile.screenshot(path=str(SHOTS/"mobile.png"),full_page=True,animations="disabled")
        # Generate the Persian proposal PDF using the same Chromium renderer.
        proposal=(DOCS/"PROPOSAL.md").read_text(encoding="utf-8")
        body=markdown.markdown(proposal,extensions=["tables","fenced_code"])
        styles="""@page{size:A4;margin:18mm}body{direction:rtl;font-family:'Noto Sans Arabic',sans-serif;font-size:11pt;line-height:1.95;color:#272338}h1{font-size:27pt;color:#e91d50}h2{font-size:17pt;border-bottom:2px solid #fbd4e0;padding-bottom:5px;margin-top:25px}h3{font-size:13pt}table{border-collapse:collapse;width:100%;font-size:9pt}td,th{border:1px solid #ddd;padding:7px}th{background:#fee8ef}pre{direction:ltr;text-align:left;white-space:pre-wrap;font-size:9pt;background:#f5f5f8;padding:8px}p,li{overflow-wrap:anywhere}a{color:#d21c51}"""
        doc=await browser.new_page()
        await doc.set_content('<!DOCTYPE html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><style>'+styles+'</style></head><body>'+body+'</body></html>')
        await doc.pdf(path=str(DOCS/"Torobcheh-Proposal.pdf"),format="A4",print_background=True)
        await browser.close()

def make_video():
    items=[
      ("01_home","تربچه AI","کمتر بگرد؛ بهتر انتخاب کن",3.0),
      ("02_search","از نیازت بگو","پیشنهادها متناسب با درخواست تو",5.0),
      ("03_persona","یک سؤال، دو نتیجه","ترجیحات متفاوت؛ انتخاب متفاوت",6.0),
      ("04_new_need","نظرت عوض شد؟","نیاز جدید همیشه اولویت دارد",6.0),
      ("05_privacy","حافظه تحت کنترل تو","شخصی‌سازی اختیاری است",5.0),
      ("06_explain","چرا این انتخاب؟","دلایل هر پیشنهاد را ببین",6.0),
      ("07_compare","مقایسه دقیق","از قیمت تا تناسب با نیاز",6.0),
      ("01_home","تربچه AI","نمونه مستقل با داده آزمایشی، بدون LLM زنده",4.0),
    ]
    W,H=1280,720
    B=font(40,True);S=font(23)
    lines=["ffconcat version 1.0"]
    for i,(name,title,description,duration) in enumerate(items):
        base=Image.new("RGB",(W,H),"#f9f8fc")
        dr=ImageDraw.Draw(base)
        dr.rectangle((0,0,W,78),fill="#ffffff")
        dr.rectangle((0,77,W,83),fill="#e91d50")
        dr.text((1215,11),title,font=B,fill="#232035",direction="rtl",anchor="ra")
        dr.text((1209,676),description,font=S,fill="#b92054",direction="rtl",anchor="ra")
        dr.text((53,691),"TOROBCHEH / AI",font=font(15),fill="#8a8799")
        shot=Image.open(TMP/(name+".png")).convert("RGB")
        shot=shot.resize((1180,545),Image.Resampling.LANCZOS)
        base.paste(shot,(50,98))
        base.save(TMP/(f"slide_{i:02}.png"))
        lines.append("file '"+str(TMP/(f"slide_{i:02}.png"))+"'")
        lines.append("duration "+str(duration))
    lines.append("file '"+str(TMP/(f"slide_{len(items)-1:02}.png"))+"'")
    ffcat=TMP/"slides.ffconcat"
    ffcat.write_text("\n".join(lines)+"\n")
    # Original 142-BPM electronic backing track, generated without third-party music.
    bpm=142; beat=60/bpm; seconds=sum(x[-1] for x in items)
    sr=22050
    N=int((seconds+1)*sr)
    sound=np.zeros(N,dtype=np.float32)
    rng=np.random.default_rng(142)
    chords=[220.0,261.63,293.66,196.0]
    for k in range(int(seconds/beat)+1):
        st=int(k*beat*sr)
        n=int(0.20*sr); t=np.arange(n)/sr
        kick=np.sin(2*np.pi*(58*t+0.5*155*t*t))*np.exp(-t*21)*0.21
        sound[st:min(st+n,N)]+=kick[:min(n,N-st)]
        if k%2:
            noise=rng.normal(0,1,n).astype(np.float32)*np.exp(-t*32)*0.035
            sound[st:min(st+n,N)]+=noise[:min(n,N-st)]
        note=chords[(k//8)%4]
        ns=int(.25*sr); u=np.arange(ns)/sr
        synth=np.sin(2*np.pi*(note*2)*u)*np.exp(-u*11)*.045
        sound[st:min(st+ns,N)]+=synth[:min(ns,N-st)]
        h=int(.07*sr); v=np.arange(h)/sr
        hat=rng.normal(0,1,h)*np.exp(-v*60)*.017
        hst=st+int(sr*beat*.5)
        if hst+h<=N: sound[hst:hst+h]+=hat
    sound=np.tanh(sound)*.83
    fade=int(sr*.8)
    sound[:fade]*=np.linspace(0,1,fade)
    sound[-fade:]*=np.linspace(1,0,fade)
    audio=TMP/"sound.wav"
    with wave.open(str(audio),"wb") as f:
        f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr)
        f.writeframes((sound*32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y","-safe","0","-f","concat","-i",str(ffcat),"-i",str(audio),"-t",str(seconds),"-c:v","libx264","-pix_fmt","yuv420p","-r","24","-preset","veryfast","-crf","25","-c:a","aac","-b:a","128k","-movflags","+faststart",str(OUT/"Torobcheh-Demo-V2.mp4")],check=True)
    for path in TMP.glob("*"):path.unlink()
    TMP.rmdir()

if __name__=="__main__":
    asyncio.run(build())
    make_video()
    for f in [SHOTS/"home.png",SHOTS/"mobile.png",DOCS/"Torobcheh-Proposal.pdf",OUT/"Torobcheh-Demo-V2.mp4"]:
        print(f.relative_to(ROOT),f.stat().st_size)
