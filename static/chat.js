(() => {
 const input = document.getElementById('chat-input');
 const send = document.getElementById('send-btn');
 const messages = document.getElementById('chat-messages');
 const language = document.getElementById('language');
 const voiceBtn = document.getElementById('voice-btn');
 const voiceStatus = document.getElementById('voice-status');
 if (!input || !send || !messages) return;
 function addMessage(text, who) {
   const row = document.createElement('div'); row.className = `message ${who}`;
   if (who === 'bot') { const avatar = document.createElement('span'); avatar.className='message-avatar'; avatar.textContent='✚'; row.appendChild(avatar); }
   const bubble = document.createElement('div'); bubble.className='bubble'; bubble.textContent=text;
   row.appendChild(bubble); messages.appendChild(row); messages.scrollTop=messages.scrollHeight;
 }
 async function sendMessage() {
   const message = input.value.trim(); if (!message) return;
   addMessage(message,'user'); input.value=''; send.disabled=true;
   const wait = document.createElement('div'); wait.className='message bot'; wait.id='typing';
   const b=document.createElement('div'); b.className='bubble'; b.textContent='Thinking…'; wait.appendChild(b); messages.appendChild(wait);
   try {
     const response = await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message,language:language.value})});
     const data=await response.json(); document.getElementById('typing')?.remove();
     addMessage(data.response || data.error || 'Please try again.','bot');
   } catch(e) { document.getElementById('typing')?.remove(); addMessage('Connection error. Please try again.','bot'); }
   finally { send.disabled=false; input.focus(); }
 }
 send.addEventListener('click',sendMessage);
 input.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendMessage();}});
 document.querySelectorAll('.suggestion').forEach(btn=>btn.addEventListener('click',()=>{input.value=btn.dataset.prompt||'';input.focus();}));
 const SpeechRecognition=window.SpeechRecognition||window.webkitSpeechRecognition;
 if (!SpeechRecognition) { voiceBtn.disabled=true; voiceStatus.textContent='Voice recognition is not supported in this browser. Try a recent Chrome browser.'; }
 else {
   voiceBtn.addEventListener('click',()=>{
     const rec=new SpeechRecognition(); rec.lang=language.value==='te'?'te-IN':'en-IN'; rec.interimResults=false; rec.maxAlternatives=1;
     voiceStatus.textContent='Listening…';
     rec.onresult=e=>{input.value=(input.value+' '+e.results[0][0].transcript).trim();voiceStatus.textContent='Voice captured. Press send to submit.';input.focus();};
     rec.onerror=()=>voiceStatus.textContent='Could not capture voice. Check microphone permission.';
     rec.onend=()=>{if(voiceStatus.textContent==='Listening…')voiceStatus.textContent='Voice input ready.';};
     try { rec.start(); } catch(e) { voiceStatus.textContent='Voice recognition is already running.'; }
   });
 }
})();
