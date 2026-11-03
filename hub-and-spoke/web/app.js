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
function qaGateHtml(tests,gate){let html='<div class="check"><span>QA · kiểm thử chức năng</span><b class="'+(tests?.pass?'pass':'fail')+'">'+(!tests?'Chưa chạy':tests.pass?'PASS':'FAIL')+'</b></div><div class="check"><span>Governance · phân tích AST</span><b class="'+(gate?.pass?'pass':'fail')+'">'+(!gate?'Chưa chạy':gate.pass?'PASS':'FAIL')+'</b></div>';
 if(tests?.cases?.length)html+='<p class="subtle">'+tests.cases.filter(c=>c.pass).length+'/'+tests.cases.length+' ca kiểm thử đạt.</p>';
 let findings=(gate?.findings||[]).map(f=>'<p>Dòng '+esc(f.line)+' · '+esc(f.rule)+': '+esc(f.message)+'</p>').join('');
 if(tests?.error)findings+='<p>QA: '+esc(tests.error)+'</p>';
 const failed=tests?.cases?.filter(c=>!c.pass)||[];for(const c of failed)findings+='<p>Email '+esc(JSON.stringify(c.input))+': cần '+esc(c.expected)+', nhận '+esc(c.actual)+'.</p>';
 if(findings)html+='<div class="findings">'+findings+'</div>';
 return html;
}
function presentation(){
 if(!config)return {title:'Đang đọc cấu hình',text:'Kết nối server trên máy.',button:'Đang tải…',active:-1};
 if(!config.configured)return {title:'Cần cấu hình Gemini API key',text:'Chạy cau-hinh-api.cmd trong Agentic_PM/hub-and-spoke, nhập key của project Free Tier. Sau đó bấm đọc lại cấu hình.',button:'Đọc lại cấu hình key',active:-1};
 if(!session)return {title:'Sẵn sàng xử lý yêu cầu bằng Gemini',text:'Planner tạo story, Developer sinh hoặc sửa mã; QA và Governance kiểm tra bằng Python.',button:'Bắt đầu với Gemini →',active:-1};
 const s=session,phase=s.phase;
 if(s.status==='exhausted')return {title:'Đã dừng sau giới hạn thử lại',text:'Kết quả vẫn chưa đạt kiểm tra. Hãy xem lỗi và sửa yêu cầu trước khi tạo phiên mới.',button:'Đã dừng',active:-1,end:true,error:true};
 if(kind==='hub')return ({ready:{title:'Story Planner chuẩn bị xử lý',text:'Gemini sẽ chuyển yêu cầu thành story và tiêu chí chấp nhận.',button:'Tạo story →',active:0},planned:{title:'Planner đã tạo story',text:s.initial_code?'Bạn có mã đầu vào; tiếp nhận mã này trước khi chạy các cổng kiểm tra.':'Chuyển story cho Developer để Gemini tạo mã Python.',button:s.initial_code?'Tiếp nhận mã đã nhập →':'Developer viết mã →',active:1},coded:{title:'Mã đã được nộp · r'+s.revision,text:'Chạy kiểm thử chức năng và các quy tắc AST độc lập. Bước này không gọi API.',button:'Chạy QA và Governance →',active:2},blocked:{title:'Cổng kiểm tra đang chặn mã',text:'Xem lỗi dưới đây. Developer sẽ nhận phản hồi thật để sửa; tối đa 3 lần sửa.',button:s.repairs>=3?'Dừng phiên chưa đạt':'Yêu cầu Developer sửa →',active:1,error:true},review:{title:'Mã đã qua các kiểm tra hiện tại',text:'Bạn cần xem xét mã và phạm vi quy tắc trước khi chấp nhận. Không tự merge hoặc triển khai.',button:'Tôi đã xem xét · chấp nhận',active:3},accepted:{title:'Đã chấp nhận kết quả phiên',text:'Đây là chấp nhận trong hệ thống demo; không thực hiện merge hoặc triển khai.',button:'Đã hoàn thành',active:3,end:true,success:true}})[phase]||{title:'Trạng thái không xác định',text:'Tạo phiên mới.',button:'Dừng',end:true};
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
  }
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
}

render();boot();
