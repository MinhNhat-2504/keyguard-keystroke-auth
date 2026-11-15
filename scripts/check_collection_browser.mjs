// Actual Chrome -> Flask -> isolated local files. No Render/Neon or mocked fetch.
import {spawn} from 'node:child_process';
import {mkdir,readFile,writeFile} from 'node:fs/promises';
import path from 'node:path';
import net from 'node:net';
import assert from 'node:assert/strict';
import {fileURLToPath} from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const out=path.resolve(root,'../keyguard-keystroke-auth/report/preview/collection-browser-20261115');
await mkdir(out,{recursive:true});
// Refuse an accidental rerun into previously collected fixtures.
const data=path.join(out,'data-'+Date.now());
const available=net.createServer();await new Promise(resolve=>available.listen(0,'127.0.0.1',resolve));
const port=available.address().port;await new Promise(resolve=>available.close(resolve));
const base=`http://127.0.0.1:${port}`;
const server=spawn(path.resolve(root,'../keyguard-keystroke-auth/.venv/Scripts/python.exe'),
    ['-c',`import app; app.app.run(host='127.0.0.1',port=${port},debug=False,use_reloader=False)`],
    {cwd:root,env:{...process.env,KEYGUARD_STORAGE:'file',DATABASE_URL:'',KEYGUARD_DATA_DIR:data,KEYGUARD_ADMIN_KEY:''},
     windowsHide:true,stdio:['ignore','ignore','ignore']});
let browser,ws;
try {
    let ready=false;
    for(let i=0;i<200;i++){
        try {if((await fetch(base+'/login')).ok){ready=true;break;}}catch(e){}
        await new Promise(r=>setTimeout(r,100));
    }
    assert.ok(ready,'Flask readiness');
    browser=spawn('C:/Program Files/Google/Chrome/Application/chrome.exe',[
        '--headless=new','--remote-debugging-port=0','--no-first-run','--no-default-browser-check',
        '--disable-extensions','--disable-background-networking',`--user-data-dir=${path.join(out,'chrome-'+Date.now())}`,'about:blank'
    ],{windowsHide:true,stdio:['ignore','ignore','pipe']});
    const endpoint=await new Promise((resolve,reject)=>{
        const t=setTimeout(()=>reject(new Error('Chrome startup timeout')),20000);
        browser.stderr.on('data',b=>{const m=String(b).match(/DevTools listening on (ws:\/\/\S+)/);if(m){clearTimeout(t);resolve(m[1]);}});
        browser.on('error',reject);
    });
    ws=new WebSocket(endpoint);await new Promise(r=>ws.addEventListener('open',r));
    let next=0;const pending=new Map(),exceptions=[];
    ws.addEventListener('message',e=>{
        const m=JSON.parse(e.data);if(m.method==='Runtime.exceptionThrown')exceptions.push(m.params.exceptionDetails);
        const p=pending.get(m.id);if(p){pending.delete(m.id);clearTimeout(p.timer);m.error?p.reject(new Error(JSON.stringify(m.error))):p.resolve(m.result);}
    });
    const send=(method,params={},sessionId)=>new Promise((resolve,reject)=>{
        const id=++next,timer=setTimeout(()=>reject(new Error(method+' timeout')),15000);
        pending.set(id,{resolve,reject,timer});ws.send(JSON.stringify({id,method,params,...(sessionId?{sessionId}:{})}));
    });
    const {targetId}=await send('Target.createTarget',{url:'about:blank'});
    const {sessionId}=await send('Target.attachToTarget',{targetId,flatten:true});
    const page=(m,p)=>send(m,p,sessionId);
    const evaluate=async expression=>{
        const r=await page('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});
        if(r.exceptionDetails)throw new Error(JSON.stringify(r.exceptionDetails));return r.result.value;
    };
    await page('Runtime.enable');await page('Page.enable');
    async function waitFor(expression){
        for(let i=0;i<100;i++){if(await evaluate(expression))return;await new Promise(r=>setTimeout(r,50));}
        throw new Error('Condition timeout: '+expression);
    }
    await page('Page.navigate',{url:base});
    await waitFor(`typeof capture!=='undefined' && capture && currentParticipantId && !inputField.disabled`);
    const pid=await evaluate('currentParticipantId');
    const typeSample=async()=>{
        await evaluate('inputField.focus()');
        for(const key of [...'.tie5Roanl','Enter']){
            await page('Input.dispatchKeyEvent',{type:'keyDown',key,text:key==='Enter'?'\r':key});
            await page('Input.dispatchKeyEvent',{type:'keyUp',key});
        }
    };
    await typeSample();
    await waitFor(`statusMsg.textContent.includes('Nhập mã thiết bị')`);
    assert.equal(await evaluate('counts["1"]'),0);
    await evaluate(`deviceInput.value='MAY_BROWSER_01';deviceInput.dispatchEvent(new Event('change'));`);
    await typeSample();await waitFor('counts["1"]===1');
    const rows=(await readFile(path.join(data,'collected',pid+'.jsonl'),'utf8')).trim().split('\n').map(JSON.parse);
    assert.equal(rows.length,1);assert.equal(rows[0].device_id,'MAY_BROWSER_01');assert.equal(rows[0].collection_schema_version,3);
    await page('Page.reload',{});
    await waitFor(`typeof capture!=='undefined' && capture && currentParticipantId===${JSON.stringify(pid)} && counts['1']===1`);
    assert.equal(await evaluate('deviceInput.value'),'MAY_BROWSER_01');
    const widths=[];
    for(const width of [320,390,1440]){
        await page('Emulation.setDeviceMetricsOverride',{width,height:900,deviceScaleFactor:1,mobile:width<500});
        const sizes=await evaluate('({width:innerWidth,content:document.documentElement.scrollWidth})');
        assert.ok(sizes.content<=sizes.width,JSON.stringify(sizes));widths.push(sizes);
    }
    const screenshot=await page('Page.captureScreenshot',{format:'png'});
    await writeFile(path.join(out,'collector-device-desktop.png'),Buffer.from(screenshot.data,'base64'));
    assert.equal(exceptions.length,0,JSON.stringify(exceptions));
    const result={status:'passed',real_chrome_and_local_flask:true,fetch_mocked:false,missing_device_did_not_write:true,
        real_key_events_saved:rows[0].events.length,device_and_participant_resume:true,widths,runtime_exceptions:0,
        production_access:false,fixture_data_path:data};
    await writeFile(path.join(out,'browser-checks.private.json'),JSON.stringify(result,null,2)+'\n');
    const {fixture_data_path,...publicResult}=result;
    await writeFile(path.resolve(root,'../keyguard-keystroke-auth/results/collection_browser_checks_20261115.json'),JSON.stringify(publicResult,null,2)+'\n');
    console.log(JSON.stringify(publicResult));
} finally {
    if(ws)ws.close();if(browser)browser.kill();server.kill();
}
