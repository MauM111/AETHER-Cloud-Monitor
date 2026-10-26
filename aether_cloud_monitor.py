from flask import Flask, jsonify, render_template_string, Response, request
import csv
import io
import os
import platform
import socket
import threading
import time
from collections import deque
from datetime import datetime

import psutil

app = Flask(__name__)
LOG_PATH = os.path.expanduser('~/monitor_log.csv')
EVENT_PATH = os.path.expanduser('~/monitor_events.csv')
DATA_LOCK = threading.Lock()
LATEST = {'cpu': 0.0, 'ram': 0.0, 'disk': 0.0, 'time': '', 'status': 'starting'}
LAST_LEVEL = 'normal'

# The sampler is independent of browser visits.
def sampler():
    global LAST_LEVEL
    psutil.cpu_percent(interval=None)
    while True:
        cpu = round(psutil.cpu_percent(interval=1), 1)
        ram = round(psutil.virtual_memory().percent, 1)
        disk = round(psutil.disk_usage('/').percent, 1)
        stamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        level = 'critical' if max(cpu, ram, disk) >= 95 else 'warning' if max(cpu, ram, disk) >= 80 else 'normal'
        with DATA_LOCK:
            with open(LOG_PATH, 'a', newline='') as f:
                csv.writer(f).writerow([stamp, cpu, ram, disk])
            LATEST.update(cpu=cpu, ram=ram, disk=disk, time=stamp, status=level)
            if level != LAST_LEVEL:
                message = ('All resources returned to normal' if level == 'normal' else
                           'High resource usage detected' if level == 'warning' else
                           'Critical resource usage detected')
                with open(EVENT_PATH, 'a', newline='') as f:
                    csv.writer(f).writerow([stamp, level, message, cpu, ram, disk])
                LAST_LEVEL = level
        time.sleep(1)

HTML = r'''<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>AETHER / Cloud Intelligence</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<style>
:root{--bg:#0a101b;--panel:#101d2b;--panel2:#142535;--edge:#26394a;--text:#e8f0f3;--muted:#91a6b3;--teal:#5ce1cf;--amber:#e5b76b;--red:#f37e82;--blue:#83a9e7}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(ellipse at 85% -10%,#19364a 0%,transparent 43%),var(--bg);color:var(--text);font-family:Inter,Segoe UI,Arial,sans-serif} .shell{max-width:1450px;margin:auto;padding:30px 35px 70px}
.top{display:flex;align-items:center;justify-content:space-between;gap:18px;border-bottom:1px solid var(--edge);padding-bottom:24px}.brand{display:flex;align-items:center;gap:16px}.glyph{font-size:27px;color:var(--teal);border:1px solid #417a7b;padding:11px 15px;clip-path:polygon(0 0,100% 0,100% 78%,78% 100%,0 100%)}.eyebrow{font-size:10px;letter-spacing:3px;color:var(--teal);font-weight:800}.brand h1{margin:3px 0;font-size:28px;letter-spacing:4px;font-weight:800}.sub{color:var(--muted);font-size:13px}.status{display:flex;gap:10px;align-items:center;border:1px solid var(--edge);padding:13px 17px;border-radius:5px;font-size:12px;letter-spacing:1px}.dot{width:9px;height:9px;border-radius:50%;background:var(--teal);box-shadow:0 0 14px var(--teal)}.status.warning .dot{background:var(--amber);box-shadow:0 0 14px var(--amber)}.status.critical .dot,.status.offline .dot{background:var(--red);box-shadow:0 0 14px var(--red)}
.section{display:flex;justify-content:space-between;align-items:baseline;gap:14px;margin:33px 0 15px}.section h2{margin:0;font-size:15px;letter-spacing:2px;text-transform:uppercase}.section small{color:var(--muted);font-size:11px}.metric-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}.metric{padding:22px 24px;background:linear-gradient(150deg,var(--panel2),var(--panel));border:1px solid var(--edge);border-top:2px solid var(--teal);min-width:0}.metric:nth-child(2){border-top-color:var(--blue)}.metric:nth-child(3){border-top-color:var(--amber)}.metric-head{display:flex;justify-content:space-between;color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:2px}.metric-value{font-size:52px;font-weight:650;letter-spacing:-2px;margin:15px 0 12px;font-variant-numeric:tabular-nums}.metric-value span{font-size:21px;color:var(--muted)}.track{height:4px;background:#2b3d4a}.fill{height:100%;width:0;background:var(--teal);transition:width .5s}.metric:nth-child(2) .fill{background:var(--blue)}.metric:nth-child(3) .fill{background:var(--amber)}
.layout{display:grid;grid-template-columns:minmax(0,1.75fr) minmax(280px,1fr);gap:15px}.panel{background:var(--panel);border:1px solid var(--edge);padding:22px;min-width:0}.panel-head{display:flex;justify-content:space-between;align-items:center;gap:12px;margin-bottom:17px}.panel h3{margin:0;font-size:13px;letter-spacing:1.4px;text-transform:uppercase}.tiny{font-size:11px;color:var(--muted)}.chart-wrap{height:265px;position:relative}.chart-wrap.large{height:325px}.telemetry{display:grid;grid-template-columns:1fr;gap:15px}.telemetry .chart-wrap{height:175px}.side{display:grid;grid-template-columns:1fr;gap:15px}.facts{display:grid;grid-template-columns:1fr 1fr;gap:17px}.fact .label{font-size:10px;text-transform:uppercase;letter-spacing:1.5px;color:var(--muted)}.fact .value{font-size:15px;margin-top:6px;overflow-wrap:anywhere}.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px}.stat{background:#152737;padding:16px;border:1px solid var(--edge)}.stat label{display:block;color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:1px}.stat strong{display:block;margin-top:8px;font-size:23px}.stat small{color:var(--muted);font-size:11px}.controls{display:flex;align-items:center;gap:12px;flex-wrap:wrap}.control{background:#172a39;border:1px solid #3b5567;color:var(--text);border-radius:3px;padding:9px 12px;font-size:12px;cursor:pointer}.control:hover{border-color:var(--teal)}.legend{display:flex;gap:17px;flex-wrap:wrap}.legend label{font-size:12px;color:var(--muted);cursor:pointer}.legend input{accent-color:var(--teal)}.events{max-height:315px;overflow:auto}.event{border-bottom:1px solid var(--edge);padding:12px 0;display:flex;gap:13px;align-items:flex-start}.event:last-child{border:0}.event .stamp{font-size:11px;color:var(--muted);white-space:nowrap}.event .desc{font-size:12px}.event .severity{font-size:10px;color:var(--amber);letter-spacing:1px}.event.critical .severity{color:var(--red)}.event.normal .severity{color:var(--teal)}.footer{color:var(--muted);border-top:1px solid var(--edge);padding-top:20px;margin-top:35px;font-size:11px;display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
@media(max-width:950px){.layout{grid-template-columns:1fr}.telemetry{grid-template-columns:repeat(3,minmax(0,1fr))}.telemetry .chart-wrap{height:155px}.shell{padding:20px}}@media(max-width:650px){.metric-grid,.telemetry,.stats{grid-template-columns:1fr}.top{align-items:flex-start;flex-direction:column}.metric-value{font-size:43px}.facts{grid-template-columns:1fr 1fr}.chart-wrap.large{height:265px}}
</style></head><body><main class="shell">
<header class="top"><div class="brand"><div class="glyph">◈</div><div><div class="eyebrow">INFRASTRUCTURE OBSERVABILITY / 01</div><h1>AETHER</h1><div class="sub">Cloud Intelligence &nbsp; / &nbsp; Linux Telemetry Station</div></div></div><div class="status" id="status"><span class="dot"></span><span id="statusText">CONNECTING TO SERVER</span></div></header>
<div class="section"><h2>Infrastructure pulse</h2><small id="lastUpdate">Awaiting telemetry...</small></div>
<div class="metric-grid"><article class="metric"><div class="metric-head"><span>01 / Processor</span><span>CPU</span></div><div class="metric-value"><b id="cpu">--</b><span>%</span></div><div class="track"><div class="fill" id="cpuBar"></div></div></article><article class="metric"><div class="metric-head"><span>02 / Memory</span><span>RAM</span></div><div class="metric-value"><b id="ram">--</b><span>%</span></div><div class="track"><div class="fill" id="ramBar"></div></div></article><article class="metric"><div class="metric-head"><span>03 / Storage</span><span>DISK</span></div><div class="metric-value"><b id="disk">--</b><span>%</span></div><div class="track"><div class="fill" id="diskBar"></div></div></article></div>
<div class="section"><h2>Resource telemetry</h2><small>Live measurements / rolling 5 minutes</small></div>
<div class="layout"><div class="telemetry"><div class="panel"><div class="panel-head"><h3>CPU activity</h3><span class="tiny">LIVE / %</span></div><div class="chart-wrap"><canvas id="cpuLive"></canvas></div></div><div class="panel"><div class="panel-head"><h3>Memory pressure</h3><span class="tiny">LIVE / %</span></div><div class="chart-wrap"><canvas id="ramLive"></canvas></div></div><div class="panel"><div class="panel-head"><h3>Disk utilisation</h3><span class="tiny">LIVE / %</span></div><div class="chart-wrap"><canvas id="diskLive"></canvas></div></div></div><aside class="side"><div class="panel"><div class="panel-head"><h3>System identity</h3><span class="tiny">HOST / VM</span></div><div class="facts" id="facts"><div class="tiny">Loading...</div></div></div><div class="panel"><div class="panel-head"><h3>Incident timeline</h3><span class="tiny">LAST 12 EVENTS</span></div><div class="events" id="events"><div class="tiny">No incidents recorded</div></div></div></aside></div>
<div class="section"><h2>Historical explorer</h2><small>Persistent CSV / data survives restart</small></div>
<div class="panel"><div class="panel-head"><h3>Comparative resource history</h3><div class="controls"><select id="range" class="control" aria-label="History range"><option value="50">Last 50</option><option value="100">Last 100</option><option value="500">Last 500</option><option value="all">All records</option></select><button class="control" id="export">↓ Export CSV</button></div></div><div class="legend"><label><input type="checkbox" id="showCpu" checked> CPU</label><label><input type="checkbox" id="showRam" checked> RAM</label><label><input type="checkbox" id="showDisk" checked> Disk</label></div><div class="chart-wrap large"><canvas id="historyChart"></canvas></div><div class="tiny" id="historyCount">Loading historical measurements...</div></div>
<div class="section"><h2>Resource analytics</h2><small>Minimum / average / maximum for selected history</small></div><div class="stats" id="stats"></div>
<footer class="footer"><span>AETHER / CLOUD INTELLIGENCE · BUILT WITH FLASK, PSUTIL & CHART.JS</span><span>LOCAL MONITORING · 80% WARNING / 95% CRITICAL</span></footer></main>
<script>
const palette={cpu:'#5ce1cf',ram:'#83a9e7',disk:'#e5b76b'};
const axes={x:{ticks:{color:'#8fa6b4',maxTicksLimit:6,maxRotation:0},grid:{color:'#203141'}},y:{min:0,max:100,ticks:{color:'#8fa6b4',callback:v=>v+'%'},grid:{color:'#203141'}}};
function makeChart(id,keys){return new Chart(document.getElementById(id),{type:'line',data:{labels:[],datasets:keys.map(key=>({label:key.toUpperCase(),data:[],borderColor:palette[key],backgroundColor:palette[key]+'18',borderWidth:2,pointRadius:0,pointHoverRadius:4,tension:.25,fill:false}))},options:{responsive:true,maintainAspectRatio:false,animation:false,interaction:{mode:'index',intersect:false},plugins:{legend:{display:false},tooltip:{backgroundColor:'#172a39',titleColor:'#e8f0f3',bodyColor:'#e8f0f3'}},scales:axes}})}
const live={cpu:makeChart('cpuLive',['cpu']),ram:makeChart('ramLive',['ram']),disk:makeChart('diskLive',['disk'])};
const historical=makeChart('historyChart',['cpu','ram','disk']);
let lastResponse=0;
async function updateLive(){try{const response=await fetch('/api/status',{cache:'no-store'});if(!response.ok)throw Error('Status unavailable');const d=await response.json();lastResponse=Date.now();for(const key of ['cpu','ram','disk']){document.getElementById(key).textContent=Number(d[key]).toFixed(1);document.getElementById(key+'Bar').style.width=Math.min(100,d[key])+'%';const chart=live[key];chart.data.labels.push(d.time?d.time.split(' ')[1]:new Date().toLocaleTimeString());chart.data.datasets[0].data.push(d[key]);if(chart.data.labels.length>150){chart.data.labels.shift();chart.data.datasets[0].data.shift()}chart.update('none')}document.getElementById('lastUpdate').textContent='Last reading / '+(d.time||'just now');const el=document.getElementById('status');el.className='status '+d.status;document.getElementById('statusText').textContent=d.status==='normal'?'SERVER ONLINE / NOMINAL':d.status==='warning'?'WARNING / HIGH UTILISATION':d.status==='critical'?'CRITICAL / HIGH UTILISATION':'INITIALISING';}catch(e){if(Date.now()-lastResponse>3500){document.getElementById('status').className='status offline';document.getElementById('statusText').textContent='CONNECTION LOST';document.getElementById('lastUpdate').textContent='Unable to reach server'}}}
async function updateHistory(){try{const limit=document.getElementById('range').value;const response=await fetch('/api/history?limit='+limit,{cache:'no-store'});if(!response.ok)throw Error('History unavailable');const rows=await response.json();historical.data.labels=rows.map(row=>row.time);['cpu','ram','disk'].forEach((key,i)=>{historical.data.datasets[i].data=rows.map(row=>row[key]);historical.data.datasets[i].hidden=!document.getElementById('show'+key[0].toUpperCase()+key.slice(1)).checked});historical.update('none');document.getElementById('historyCount').textContent=rows.length+' saved measurements displayed';document.getElementById('stats').innerHTML=['cpu','ram','disk'].map(key=>{const vals=rows.map(row=>row[key]).filter(Number.isFinite);const min=vals.length?Math.min(...vals).toFixed(1):'--';const max=vals.length?Math.max(...vals).toFixed(1):'--';const avg=vals.length?(vals.reduce((a,b)=>a+b,0)/vals.length).toFixed(1):'--';return `<div class="stat"><label>${key.toUpperCase()} / selected period</label><strong>${avg}% <small>average</small></strong><small>MIN ${min}% &nbsp; / &nbsp; MAX ${max}%</small></div>`}).join('')}catch(e){document.getElementById('historyCount').textContent='History unavailable'}}
async function updateInfo(){try{const [info,events]=await Promise.all([fetch('/api/system').then(r=>r.json()),fetch('/api/events').then(r=>r.json())]);const values=[['Hostname',info.hostname],['Operating system',info.os],['Uptime',info.uptime],['CPU cores',info.cores],['Total memory',info.memory],['Disk capacity',info.disk]];document.getElementById('facts').innerHTML=values.map(([k,v])=>`<div class="fact"><div class="label">${k}</div><div class="value"></div></div>`).join('');document.querySelectorAll('#facts .value').forEach((el,i)=>el.textContent=values[i][1]);document.getElementById('events').innerHTML=events.length?events.slice().reverse().map(e=>`<div class="event ${e.level}"><div><div class="severity">${e.level.toUpperCase()}</div><div class="stamp">${e.time}</div></div><div class="desc"></div></div>`).join(''):'<div class="tiny">No incidents recorded</div>';document.querySelectorAll('#events .desc').forEach((el,i)=>el.textContent=events.slice().reverse()[i].message)}catch(e){}}
document.getElementById('range').addEventListener('change',updateHistory);['Cpu','Ram','Disk'].forEach(k=>document.getElementById('show'+k).addEventListener('change',updateHistory));document.getElementById('export').addEventListener('click',()=>{window.location.href='/api/export'});
if(typeof Chart==='undefined'){document.getElementById('lastUpdate').textContent='Chart.js unavailable: check internet access'}else{updateLive();updateHistory();updateInfo();setInterval(updateLive,2000);setInterval(updateHistory,10000);setInterval(updateInfo,15000)}
</script></body></html>'''

@app.get('/')
def home():
    return render_template_string(HTML)

@app.get('/api/status')
def status():
    with DATA_LOCK:
        return jsonify(dict(LATEST))

@app.get('/api/history')
def history():
    limit_arg = request.args.get('limit', '50')
    if limit_arg != 'all':
        try:
            limit = int(limit_arg)
        except ValueError:
            return jsonify({'error': 'Invalid limit'}), 400
        if limit < 1 or limit > 50000:
            return jsonify({'error': 'Limit must be 1 to 50000'}), 400
    else:
        limit = None
    records = deque(maxlen=limit) if limit else []
    try:
        with DATA_LOCK, open(LOG_PATH, newline='') as f:
            for row in csv.reader(f):
                if len(row) != 4:
                    continue
                try:
                    item = {'time': row[0], 'cpu': float(row[1]), 'ram': float(row[2]), 'disk': float(row[3])}
                    records.append(item)
                except ValueError:
                    continue
    except FileNotFoundError:
        pass
    return jsonify(list(records))

@app.get('/api/export')
def export():
    try:
        with DATA_LOCK, open(LOG_PATH, 'rb') as f:
            content = f.read()
    except FileNotFoundError:
        content = b''
    if not content.startswith(b'time,cpu,ram,disk'):
        content = b'time,cpu,ram,disk\n' + content
    return Response(content, mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=aether_monitor_history.csv'})

@app.get('/api/events')
def events():
    result = deque(maxlen=12)
    try:
        with DATA_LOCK, open(EVENT_PATH, newline='') as f:
            for row in csv.reader(f):
                if len(row) >= 3:
                    result.append({'time': row[0], 'level': row[1], 'message': row[2]})
    except FileNotFoundError:
        pass
    return jsonify(list(result))

@app.get('/api/system')
def system():
    boot = psutil.boot_time()
    uptime = int(time.time() - boot)
    return jsonify({'hostname': socket.gethostname(), 'os': platform.platform(), 'uptime': f'{uptime//86400}d {(uptime%86400)//3600}h {(uptime%3600)//60}m', 'cores': psutil.cpu_count(logical=True), 'memory': f'{psutil.virtual_memory().total / 1024**3:.1f} GB', 'disk': f'{psutil.disk_usage("/").total / 1024**3:.1f} GB'})

if __name__ == '__main__':
    threading.Thread(target=sampler, daemon=True).start()
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
