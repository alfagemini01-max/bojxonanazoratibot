const fs=require('node:fs/promises');
const path=require('node:path');
const assert=require('node:assert/strict');
const {pathToFileURL}=require('node:url');
const {chromium}=require('C:/Users/h.hayitov/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const {PDFDocument}=require('C:/Users/h.hayitov/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/pdf-lib');
const root=path.resolve(__dirname,'..');
async function main(){
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 try{
 const page=await browser.newPage({viewport:{width:1366,height:1000},acceptDownloads:true});const errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 await page.goto(pathToFileURL(path.join(root,'Dazvol.html')).href);
 const cases=[
  {name:'simple',input:{origin:'156',destination:'860',vehicle:'398'}},
  {name:'complex',input:{origin:'156',destination:'860',vehicle:'795',weight:21,humanitarian:true,heavy:true,purchase:true}},
  {name:'stay',input:{origin:'031',destination:'860',vehicle:'031',days:15,humanitarian:true,heavy:true,purchase:true}},
  {name:'blocked',input:{origin:'860',destination:'860',vehicle:'398'}},
  {name:'unknown',input:{origin:'156',destination:'860',vehicle:'031',heavy:true,purchase:true}},
  {name:'exceptions',input:{origin:'643',destination:'004',vehicle:'276'}},
 ];
 for(const lang of ['uz','ru','en'])for(const scenario of cases){
  const exported=await page.evaluate(async({lang,input})=>{const result=DazvolEngine.calculate({mode:'cargo',via:true,weight:20,days:14,...input});const output=await createResultPDF(result,lang);return {bytes:Array.from(output.bytes),bodySize:output.bodySize,bottom:output.contentBottom,preview:output.preview}}, {lang,input:scenario.input});
  const bytes=Uint8Array.from(exported.bytes);const doc=await PDFDocument.load(bytes);assert.equal(doc.getPageCount(),1);assert(Math.abs(doc.getPage(0).getWidth()-595.28)<.1);assert(exported.bottom<1015);
  await fs.writeFile(path.join(root,`tools/pdf-${scenario.name}-${lang}.pdf`),bytes);
  if(scenario.name==='complex')await fs.writeFile(path.join(root,`tools/pdf-canvas-${lang}.png`),Buffer.from(exported.preview.split(',')[1],'base64'));
  console.log(`${lang}/${scenario.name}: 1 A4 page, size=${exported.bodySize}, bottom=${exported.bottom.toFixed(0)}`);
 }
 await page.evaluate(()=>{state.result=DazvolEngine.calculate({origin:'156',destination:'860',vehicle:'795',mode:'cargo',via:true,weight:21,days:14});renderResult(state.result)});
 const downloadPromise=page.waitForEvent('download');await page.locator('#download-pdf').click();const download=await downloadPromise;assert.match(download.suggestedFilename(),/^Dazvol_795_.*_uz\.pdf$/);assert.equal(await download.failure(),null);
 await download.saveAs(path.join(root,'tools/pdf-downloaded-uz.pdf'));
 assert.equal(await page.locator('#download-pdf').isDisabled(),false);assert.deepEqual(errors,[]);
 console.log('PDF download button: passed. All 18 exports are single-page A4.');
 }finally{await browser.close()}
}
main().catch(e=>{console.error(e);process.exitCode=1});
