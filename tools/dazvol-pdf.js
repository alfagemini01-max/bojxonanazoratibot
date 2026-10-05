'use strict';
// Render at 200 dpi so browser fonts cover Uzbek, Cyrillic and English offline.
async function createResultPDF(result,lang){
 const tr=key=>TEXT[lang][key]||key;
 const format=n=>new Intl.NumberFormat(lang==='ru'?'ru-RU':lang==='uz'?'uz-UZ':'en-US',{maximumFractionDigits:2}).format(n)+' USD';
 const imageFrom=src=>new Promise((resolve,reject)=>{const image=new Image();image.onload=()=>resolve(image);image.onerror=reject;image.src=src});
 const emblem=await imageFrom(DATA.emblems.uzbekistan);
 await emblem.decode();
 const canvas=document.createElement('canvas');const scale=2.1;canvas.width=Math.round(794*scale);canvas.height=Math.round(1123*scale);
 const ctx=canvas.getContext('2d');ctx.scale(scale,scale);const left=48,right=746,width=right-left;
 function font(size,bold=false){ctx.font=`${bold?'700':'400'} ${size}px Arial, sans-serif`}
 function wrap(text,maxWidth,size,bold=false){font(size,bold);const lines=[];for(const paragraph of String(text).split('\n')){let line='';for(const word of paragraph.split(/\s+/)){if(!word)continue;const candidate=line?line+' '+word:word;if(ctx.measureText(candidate).width<=maxWidth){line=candidate;continue}if(line){lines.push(line);line=''}if(ctx.measureText(word).width<=maxWidth){line=word;continue}for(const ch of word){if(ctx.measureText(line+ch).width>maxWidth){lines.push(line);line=''}line+=ch}}if(line)lines.push(line)}return lines.length?lines:['']}
 const permitted=result.rule?.p;const permission=tr(permitted==='1'?'required':permitted==='2'?'notRequired':permitted==='3'?'prohibited':'unknown');
 const exceptions=(DATA.exceptions[result.input.vehicle]||[]).filter(e=>e.mask[result.type-1]==='1');
 const rows=[];
 if(!result.blocked){rows.push([tr('base'),result.base===null?tr('unknown'):result.base===0?tr('noFee'):format(result.baseBefore??result.base)]);if(result.baseBefore!==null)rows.push([tr('discount'),'-'+format(result.baseBefore-result.base)]);if(result.extra)rows.push([tr('extra'),format(result.extra)]);if(result.purchase)rows.push([tr('permitSale'),format(result.purchase)])}
 const conditionParts=[];
 if(result.kind==='days')conditionParts.push(tr('days')+': '+result.input.days);
 if(result.kind==='weight')conditionParts.push(tr('capacity')+': '+result.input.weight);
 if(result.input.humanitarian)conditionParts.push(tr('humanitarian'));
 if(result.input.heavy)conditionParts.push(tr('heavy'));
 const notes=[...result.notes.map(tr)];
 if(!result.blocked&&exceptions.length)notes.push(`${tr('reportExceptions')}: ${exceptions.length}. ${tr('reportExceptionNote')}`);
 if(result.rule?.notes?.[lang])notes.push(tr('reportOriginal'));
 if(!result.blocked&&!exceptions.length&&result.rule?.exception==='2')notes.push(tr('exceptionMissing'));
 let contentBottom=0;
 function draw(bodySize){
  ctx.fillStyle='#fff';ctx.fillRect(0,0,794,1123);ctx.textBaseline='top';let y=42;
  ctx.drawImage(emblem,left,y,51,52);ctx.fillStyle='#174b73';font(11,true);ctx.fillText(tr('republic').toUpperCase(),left+67,y+1);
  const heading=wrap(tr('title'),width-70,17,true);heading.forEach((line,i)=>ctx.fillText(line,left+67,y+21+i*21));y+=Math.max(76,heading.length*21+30);
  ctx.fillStyle='#167f73';ctx.fillRect(left,y,width,3);y+=19;
  ctx.fillStyle='#142d3f';font(19,true);ctx.fillText(tr('report'),left,y);y+=28;
  ctx.fillStyle='#697c86';font(11);ctx.fillText(tr('checked')+': '+new Date(result.timestamp).toLocaleString(lang==='ru'?'ru-RU':lang==='uz'?'uz-UZ':'en-GB'),left,y);y+=28;
  function text(value,size=bodySize,color='#263e4e',bold=false,space=7){const lines=wrap(value,width,size,bold);ctx.fillStyle=color;font(size,bold);for(const line of lines){ctx.fillText(line,left,y);y+=size*1.35}y+=space}
  function labelValue(label,value){const lines=wrap(value,width-239,bodySize,true);ctx.fillStyle='#627883';font(bodySize-1);ctx.fillText(label,left,y);ctx.fillStyle='#18394d';font(bodySize,true);lines.forEach((line,i)=>ctx.fillText(line,left+239,y+i*bodySize*1.3));y+=Math.max(1,lines.length)*bodySize*1.3+10}
  for(const field of ['origin','destination','vehicle'])labelValue(tr(field),countryName(result.input[field],lang)+' ('+result.input[field]+')');
  labelValue(tr('type'),TEXT[lang].types[result.type]);
  ctx.fillStyle='#f0f5f8';ctx.fillRect(left,y,width,39);ctx.fillStyle='#516a7b';font(bodySize);ctx.fillText(tr('permit'),left+12,y+12);ctx.fillStyle=result.blocked?'#ae3535':permitted==='2'?'#087563':'#925d0c';font(bodySize,true);ctx.fillText(permission,left+239,y+12);y+=53;
  if(rows.length){ctx.fillStyle='#174b73';ctx.fillRect(left,y,width,29);ctx.fillStyle='white';font(bodySize-1,true);ctx.fillText(tr('feeName'),left+12,y+8);ctx.textAlign='right';ctx.fillText(tr('amount'),right-12,y+8);ctx.textAlign='left';y+=29;
   rows.forEach(([name,amount],index)=>{const lines=wrap(name,width-194,bodySize);const h=lines.length*bodySize*1.3+17;ctx.fillStyle=index%2?'#f1f5f7':'#fafbfc';ctx.fillRect(left,y,width,h);ctx.fillStyle='#253f4e';font(bodySize);lines.forEach((line,i)=>ctx.fillText(line,left+12,y+8+i*bodySize*1.3));ctx.textAlign='right';font(bodySize,true);ctx.fillText(amount,right-12,y+8);ctx.textAlign='left';y+=h});
   ctx.fillStyle='#e4f1ec';ctx.fillRect(left,y,width,43);ctx.fillStyle='#1d594b';font(bodySize,true);ctx.fillText(tr(result.unknown?'knownTotal':'total'),left+12,y+14);ctx.textAlign='right';font(21,true);ctx.fillText(format(result.total),right-12,y+9);ctx.textAlign='left';y+=58;
  }
  if(conditionParts.length)text(tr('reportConditions')+': '+conditionParts.join(' · '),bodySize-1,'#3e6174',false,10);
  if(notes.length){text(tr('reportNotes'),bodySize,'#173f59',true,5);notes.forEach((line,i)=>text((i+1)+'. '+line,bodySize-1,'#3e5260',false,5))}
  y+=3;text(tr('law')+' | '+tr('snapshot')+': '+DATA.sourceDate,11,'#547083',false,2);text(DATA.law,10,'#1a6294',false,0);contentBottom=y;
  const footerTop=1033;ctx.fillStyle='#cbd7df';ctx.fillRect(left,footerTop,width,1);y=1045;text(tr('disclaimer')+' '+tr('independent'),9.2,'#61727c',false,0);ctx.fillStyle='#577383';font(9);ctx.fillText(tr('page'),right-22,1098);
 }
 let size=14;draw(size);while(contentBottom>1014&&size>11){size-=.5;draw(size)}
 if(contentBottom>1014)throw new Error('Summary exceeds one page; refusing to truncate it');
 const pdf=await PDFLib.PDFDocument.create();pdf.setTitle(tr('report'));pdf.setSubject(tr('title'));pdf.setCreator('Offline permit information service');
 const page=pdf.addPage([595.28,841.89]);const png=await pdf.embedPng(canvas.toDataURL('image/png'));page.drawImage(png,{x:0,y:0,width:595.28,height:841.89});
 const bytes=await pdf.save();return {bytes,preview:canvas.toDataURL('image/png'),bodySize:size,contentBottom};
}
async function downloadResultPDF(){
 if(!state.result)return;const button=$('download-pdf'),result=structuredClone(state.result),lang=state.lang;
 button.disabled=true;button.classList.add('busy');button.textContent=TEXT[lang].pdfBusy;
 try{await new Promise(resolve=>requestAnimationFrame(resolve));const {bytes}=await createResultPDF(result,lang);const url=URL.createObjectURL(new Blob([bytes],{type:'application/pdf'}));const anchor=document.createElement('a');anchor.href=url;anchor.download=`Dazvol_${result.input.vehicle}_${result.timestamp.slice(0,10)}_${lang}.pdf`;document.body.append(anchor);anchor.click();anchor.remove();setTimeout(()=>URL.revokeObjectURL(url),60000)}catch(error){console.error('PDF export:',error);showToast('pdfError')}finally{button.disabled=false;button.classList.remove('busy');button.textContent='↓ '+TEXT[lang].pdf}
}
