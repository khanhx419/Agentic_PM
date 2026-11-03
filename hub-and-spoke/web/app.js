'use strict';
const $=id=>document.getElementById(id),kind=document.body.dataset.kind;
const esc=x=>String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const colors=['#3879b5','#8270b4','#529b83','#bf8b51','#b8667b','#668caa','#9a9b4d','#85776a'];
const sample='import re\n\nSECRET_KEY = "DEMO_ONLY_NOT_REAL"\n\ndef validate_email(email):\n    value = email.strip()\n    return re.fullmatch(r"[^@\\s]+@[^@.\\s]+(?:\\.[^@.\\s]+)+", value) is not None\n';
let config=null,session=null,sessionToken='',busy=false,lastError='';
const storageKey='real-agent-demo-'+kind;
async function api(path,data){
 const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),165000);
 try{const headers={'X-App-Token':config?.app_token||'','X-Session-Token':sessionToken};const options={headers,signal:controller.signal};if(data!==undefined){options.method='POST';headers['Content-Type']='application/json';options.body=JSON.stringify(data)}
 const r=await fetch(path,options);let out;try{out=await r.json()}catch{throw Error('Server không trả JSON. Kiểm tra ứng dụng đang chạy.')}
 if(!r.ok){if(out.session){session=out.session;remember()}throw Error(out.error||'Không thực hiện được yêu cầu.')}
 return out;
 }catch(e){if(e.name==='AbortError')throw Error('Chờ quá lâu. Nạp lại trang để đọc trạng thái đã lưu trước khi thử tiếp.');throw e}finally{clearTimeout(timer)}
}
function remember(){if(session&&sessionToken)sessionStorage.setItem(storageKey,JSON.stringify({id:session.id,token:sessionToken}))}
function forget(){sessionStorage.removeItem(storageKey);session=null;sessionToken='';lastError=''}
function table(headers,rows){return '<div class="table-wrap"><table><thead><tr>'+headers.map(h=>'<th>'+esc(h)+'</th>').join('')+'</tr></thead><tbody>'+rows.map(row=>'<tr>'+row.map(v=>'<td>'+esc(v)+'</td>').join('')+'</tr>').join('')+'</tbody></table></div>'}
function taskTable(data){const rows=[];for(const t of data?.tasks||[])for(let i=0;i<(t.steps||[]).length;i++){const op=t.steps[i];rows.push([t.id,t.name||'',i+1,op.machine,op.duration])}return table(['Nhiệm vụ','Tên','Bước','Tài nguyên','Thời lượng · '+(data?.unit||'theo yêu cầu')],rows)}
function qaGateHtml(tests,gate){let html='<div class="check"><span>QA · kiểm thử chức năng</span><b class="'+(tests?.pass?'pass':'fail')+'">'+(!tests?'Chưa chạy':tests.pass?'PASS':'FAIL')+'</b></div><div class="check"><span>Governance · phân tích AST</span><b class="'+(gate?.pass?'pass':'fail')+'">'+(!gate?'Chưa chạy':gate.pass?'PASS':'FAIL')+'</b></div>';
 if(tests?.cases?.length)html+='<p class="subtle">'+tests.cases.filter(c=>c.pass).length+'/'+tests.cases.length+' ca kiểm thử đạt.</p>';
 let findings=(gate?.findings||[]).map(f=>'<p>Dòng '+esc(f.line)+' · '+esc(f.rule)+': '+esc(f.message)+'</p>').join('');
 if(tests?.error)findings+='<p>QA: '+esc(tests.error)+'</p>';
 const failed=tests?.cases?.filter(c=>!c.pass)||[];for(const c of failed)findings+='<p>Email '+esc(JSON.stringify(c.input))+': cần '+esc(c.expected)+', nhận '+esc(c.actual)+'.</p>';
 if(findings)html+='<div class="findings">'+findings+'</div>';
 return html;
}
function gantt(){const result=session.result||{},validation=session.validation||{},raw=result.schedule;
 let html='';if(!validation.valid)html+='<div class="violations"><b>Lịch chưa đạt kiểm tra</b>'+(validation.errors||[]).map(e=>'<p>'+esc(e)+'</p>').join('')+'</div>';
 if(!Array.isArray(raw))return html;
 const schedule=raw.slice(0,72).filter(r=>r&&typeof r==='object'&&typeof r.start_time==='number'&&Number.isFinite(r.start_time)&&typeof r.end_time==='number'&&Number.isFinite(r.end_time)&&r.start_time>=0&&r.end_time>r.start_time&&r.end_time<=1000000&&typeof r.machine==='string');
 if(!schedule.length)return html;
 const max=Math.max(...schedule.map(r=>r.end_time)),jobs=[...new Set([...(session.verified?.tasks||[]).map(t=>t.id),...schedule.map(r=>String(r.task_id))])],machines=[...new Set(schedule.map(r=>r.machine))],unit=session.verified?.unit||'đơn vị';
 html+='<div class="key">'+jobs.map((id,i)=>'<span><i style="background:'+colors[i%colors.length]+'"></i>'+esc(id)+'</span>').join('')+'</div>';
 for(const m of machines)html+='<div class="g-row"><span>'+esc(m)+'</span><div class="track">'+schedule.filter(r=>r.machine===m).map(r=>'<div class="block" style="left:'+r.start_time/max*100+'%;width:'+(r.end_time-r.start_time)/max*100+'%;background:'+colors[jobs.indexOf(String(r.task_id))%colors.length]+'" title="'+esc(r.task_id)+'.'+esc(r.step_id)+' · '+r.start_time+'–'+r.end_time+'">'+esc(r.task_id)+'<small>'+r.start_time+'–'+r.end_time+'</small></div>').join('')+'</div></div>';
 html+='<div class="axis"><span>0 '+esc(unit)+'</span><span>'+max+' '+esc(unit)+'</span></div>';
 html+='<div class="result-bar"><span>'+(validation.valid?'✓ Lịch đạt các kiểm tra cục bộ':'✕ Lịch có vi phạm')+'</span><b>'+esc(validation.makespan??'—')+' '+esc(unit)+'</b></div><p class="subtle">Gantt hiển thị lịch Gemini trả về, không thay bằng thuật toán mẫu. Hợp lệ không đồng nghĩa đã chứng minh tối ưu.</p>';
 return html;
}
function presentation(){
 if(!config)return {title:'Đang đọc cấu hình',text:'Kết nối server trên máy.',button:'Đang tải…',active:-1};
 if(!config.configured)return {title:'Cần cấu hình Gemini API key',text:'Chạy cau-hinh-api.cmd trong NLTS/real-demo, nhập key của project Free Tier. Sau đó bấm đọc lại cấu hình.',button:'Đọc lại cấu hình key',active:-1};
 if(!session)return {title:kind==='hub'?'Sẵn sàng xử lý yêu cầu bằng Gemini':'Sẵn sàng đọc mô tả công việc',text:kind==='hub'?'Planner tạo story, Developer sinh hoặc sửa mã; QA và Governance kiểm tra bằng Python.':'Gemini xử lý lần lượt bốn vai trò. Sau Verifier, bạn cần đối chiếu dữ liệu trước khi tạo lịch.',button:'Bắt đầu với Gemini →',active:-1};
 const s=session,phase=s.phase;
 if(s.status==='exhausted')return {title:'Đã dừng sau giới hạn thử lại',text:'Kết quả vẫn chưa đạt kiểm tra. Hãy xem lỗi và sửa yêu cầu trước khi tạo phiên mới.',button:'Đã dừng',active:-1,end:true,error:true};
 if(kind==='hub')return ({ready:{title:'Story Planner chuẩn bị xử lý',text:'Gemini sẽ chuyển yêu cầu thành story và tiêu chí chấp nhận.',button:'Tạo story →',active:0},planned:{title:'Planner đã tạo story',text:s.initial_code?'Bạn có mã đầu vào; tiếp nhận mã này trước khi chạy các cổng kiểm tra.':'Chuyển story cho Developer để Gemini tạo mã Python.',button:s.initial_code?'Tiếp nhận mã đã nhập →':'Developer viết mã →',active:1},coded:{title:'Mã đã được nộp · r'+s.revision,text:'Chạy kiểm thử chức năng và các quy tắc AST độc lập. Bước này không gọi API.',button:'Chạy QA và Governance →',active:2},blocked:{title:'Cổng kiểm tra đang chặn mã',text:'Xem lỗi dưới đây. Developer sẽ nhận phản hồi thật để sửa; tối đa 3 lần sửa.',button:s.repairs>=3?'Dừng phiên chưa đạt':'Yêu cầu Developer sửa →',active:1,error:true},review:{title:'Mã đã qua các kiểm tra hiện tại',text:'Bạn cần xem xét mã và phạm vi quy tắc trước khi chấp nhận. Không tự merge hoặc triển khai.',button:'Tôi đã xem xét · chấp nhận',active:3},accepted:{title:'Đã chấp nhận kết quả phiên',text:'Đây là chấp nhận trong hệ thống demo; không thực hiện merge hoặc triển khai.',button:'Đã hoàn thành',active:3,end:true,success:true}})[phase]||{title:'Trạng thái không xác định',text:'Tạo phiên mới.',button:'Dừng',end:true};
 return ({ready:{title:'Seeker chuẩn bị đọc mô tả',text:'Gemini xác định các nhiệm vụ từ văn bản bạn nhập.',button:'Xác định nhiệm vụ →',active:0},sought:{title:'Seeker đã nhận diện nhiệm vụ',text:'Weaver sẽ lấy từng công đoạn, tài nguyên và thời lượng từ mô tả.',button:'Trích xuất công đoạn →',active:1},woven:{title:'Weaver đã trích xuất dữ liệu',text:'Verifier sẽ đối chiếu dữ liệu với yêu cầu gốc và sửa sai hoặc hỏi lại.',button:'Đối chiếu dữ liệu →',active:2},verified:{title:'Cần bạn đối chiếu dữ liệu trước khi lập lịch',text:'Kiểm tra bảng dưới với yêu cầu gốc. Chỉ tiếp tục khi đủ nhiệm vụ, đúng máy, thời lượng và thứ tự.',button:'Xác nhận dữ liệu · lập lịch →',active:2},clarification:{title:'Cần làm rõ yêu cầu',text:'Verifier phát hiện thiếu thông tin hoặc ràng buộc ngoài phạm vi. Sửa mô tả và tạo phiên mới.',button:'Cần sửa yêu cầu',active:2,end:true,error:true},invalid:{title:'Lịch Gemini sinh chưa đạt kiểm tra',text:'Các lỗi được giữ nguyên. Yêu cầu Architect sửa theo phản hồi, không thay bằng lịch mẫu.',button:s.schedule_attempts>=3?'Dừng phiên chưa đạt':'Yêu cầu Architect sửa lịch →',active:3,error:true},complete:{title:'Lịch đạt kiểm tra cục bộ',text:'Đủ công đoạn, đúng thời lượng, đúng thứ tự và không dùng trùng tài nguyên theo dữ liệu đã xác nhận.',button:'Đã hoàn thành',active:3,end:true,success:true}})[phase]||{title:'Trạng thái không xác định',text:'Tạo phiên mới.',button:'Dừng',end:true};
}
function render(){
 const info=presentation();$('status').className='status'+(info.error?' error':info.success?' success':'');$('status').innerHTML='<span class="icon">'+(info.error?'!':info.success?'✓':'→')+'</span><div><h2>'+esc(info.title)+'</h2><p>'+esc(info.text)+'</p></div>';
 $('next').textContent=busy?'Đang xử lý…':info.button;$('next').disabled=busy||!config||!!info.end;$('request').disabled=busy;$('reset').setAttribute('aria-disabled',String(busy));if($('initial-code'))$('initial-code').disabled=busy;
 document.querySelectorAll('.agent').forEach((el,i)=>el.className='agent'+(i===info.active?(info.error?' fail':' active'):''));
 $('connection').textContent=!config?'Đang đọc cấu hình':config.configured?'Gemini · key đã cấu hình':'Gemini · chưa có key';
 $('config-text').textContent=config?config.provider+' · '+config.model+' · '+(config.configured?'Key có trên server, chưa khẳng định API gọi thành công.':'Chưa tìm thấy GEMINI_API_KEY trên server.'):'Chưa kết nối server.';
 $('error').textContent=lastError||session?.last_error||'';
 let html='';if(session){
  if(kind==='hub'){
   if(!session.code&&session.story)html='<div class="story"><h3>'+esc(session.story.title)+'</h3><ul>'+(session.story.acceptance||[]).map(x=>'<li>'+esc(x)+'</li>').join('')+'</ul></div>';
   if(session.code){html='<div class="outputs"><div><p class="subtle">Bản mã r'+session.revision+' · kết quả thực từ agent hoặc mã bạn nhập</p><pre class="code-display" id="source-code"></pre></div><div>'+qaGateHtml(session.qa,session.governance)+'</div></div>'}
  }else if(session.result)html=gantt();
  else if(session.verified){
   if(session.verified.tasks?.length)html=taskTable(session.verified);
   if(session.verified.needs_clarification)html+='<div class="violations">'+(session.verified.questions||[]).map(q=>'<p>'+esc(q)+'</p>').join('')+'</div>';
   if(session.verified.changes?.length)html+='<div class="verify-list"><b>Verifier đã chỉnh:</b> '+session.verified.changes.map(esc).join(' · ')+'</div>';
  }else if(session.weaver)html=taskTable(session.weaver);
  else if(session.seeker)html='<div class="task-cards">'+session.seeker.tasks.map(t=>'<article class="task-card"><h3>'+esc(t.id)+'</h3><p>'+esc(t.name)+'</p></article>').join('')+'</div>';
 }
 $('output').innerHTML=html;if($('source-code'))$('source-code').textContent=session.code;
 $('history').innerHTML=(session?.events||[]).map(e=>'<div class="log-row"><b>'+esc(e.actor)+'</b><span>'+esc(e.message)+'</span></div>').join('')||'<p class="subtle">Chưa có phiên xử lý.</p>';
 const calls=session?.calls||[];$('usage').textContent=calls.length?calls.length+' lượt gọi Gemini thực · '+calls.reduce((n,c)=>n+(c.input_tokens||0),0)+' input tokens · '+calls.reduce((n,c)=>n+(c.output_tokens||0),0)+' output tokens. Các số này từ phản hồi API.':'';
 $('export').hidden=!session;
}
async function boot(){try{config=await api('/api/config');const saved=sessionStorage.getItem(storageKey);if(saved){try{const data=JSON.parse(saved);sessionToken=data.token;session=(await api('/api/session?id='+encodeURIComponent(data.id))).session;$('request').value=session.description;if($('initial-code'))$('initial-code').value=session.initial_code||''}catch{forget()}}}catch(e){lastError='Chưa kết nối server. Chạy start.cmd rồi mở http://127.0.0.1:8766.'}render()}
async function next(){if(busy)return;if(!config?.configured){busy=true;render();try{config=await api('/api/config');lastError=config.configured?'':'Chưa có key. Chạy cau-hinh-api.cmd trên máy.'}catch(e){lastError=e.message}finally{busy=false;render()}return}
 busy=true;lastError='';render();try{
 if(!session){const created=await api('/api/sessions',{kind,description:$('request').value,initial_code:$('initial-code')?.value||''});session=created.session;sessionToken=created.session_token;remember()}
 const data=await api('/api/next',{id:session.id,version:session.version,confirmed:session.phase==='verified'||session.phase==='review'});session=data.session;remember();
 }catch(e){lastError=e.message}finally{busy=false;render()}}
$('next').onclick=next;$('reset').onclick=e=>{e.preventDefault();if(!busy){forget();render()}};
['request','initial-code'].forEach(id=>{if($(id))$(id).addEventListener('input',()=>{if(!busy){forget();render()}})});
$('export').onclick=async e=>{e.preventDefault();if(!session)return;const url=URL.createObjectURL(new Blob([JSON.stringify(session,null,2)],{type:'application/json'}));const link=document.createElement('a');link.href=url;link.download=kind+'-session.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000)};
if(kind==='hub'){
 $('lead').textContent='Planner và Developer gọi Gemini. QA và Governance phân tích mã trên máy trước khi bạn chấp nhận.';
 $('scope').textContent='Phạm vi: một hàm Python validate_email(email), kiểm tra định dạng email cơ bản. Tập con Python được hỗ trợ có if/return, chuỗi, len và re.fullmatch; không có I/O, vòng lặp hay thực thi mã động.';
 $('note').textContent='Governance dùng AST để xét cấu trúc mã. QA thông dịch tập con Python giới hạn trong tiến trình riêng, không exec mã của model. Quy tắc không bảo đảm phát hiện mọi loại secret; không có merge hoặc deploy.';
 $('sample-code').onclick=e=>{e.preventDefault();if(!busy){$('initial-code').value=sample;forget();render()}};
 $('sample-gate').onclick=e=>{e.preventDefault();$('gate-code').value=sample};
 $('gate-code').value=sample;
 $('gate-run').onclick=async()=>{if(!config)return;$('gate-run').disabled=true;$('gate-result').textContent='Đang kiểm tra AST và chạy các ca QA…';try{const result=await api('/api/gate',{code:$('gate-code').value});$('gate-result').innerHTML=qaGateHtml(result.qa,result.governance)+'<p class="subtle">Kiểm tra cục bộ thực, không gọi API.</p>'}catch(e){$('gate-result').textContent=e.message}finally{$('gate-run').disabled=false}};
}else{
 $('lead').textContent='Nhập yêu cầu bằng lời; đối chiếu công đoạn trước khi Gemini tạo lịch và Python kiểm tra ràng buộc.';
 $('scope').textContent='Phạm vi: tối đa 8 nhiệm vụ / 36 công đoạn; mỗi nhiệm vụ là chuỗi bước, mỗi bước dùng một tài nguyên có sức chứa 1; thời lượng xác định. Yêu cầu thiếu dữ liệu hoặc có ràng buộc ngoài phạm vi sẽ cần làm rõ.';
 $('note').textContent='Dựa trên bốn vai trò MANS; có thêm bước bạn xác nhận dữ liệu và bộ kiểm tra lịch độc lập. Đây không phải bản tái lập toàn bộ benchmark. Lịch hợp lệ không được mặc định là tối ưu.';
}
render();boot();
