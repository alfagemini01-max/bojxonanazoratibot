const fs=require('node:fs');
const path=require('node:path');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const {pathToFileURL}=require('node:url');
const root=path.resolve(__dirname,'..');
const html=fs.readFileSync(path.join(root,'Dazvol.html'),'utf8');
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
new vm.Script(script);
const pure=script.slice(0,script.indexOf('const combos={}'));
const context={window:{},Intl,document:{getElementById(){}},console};
vm.createContext(context);vm.runInContext(pure,context);
const {calculate,searchCountries,data}=context.window.DazvolEngine;
let count=0;
function check(name,input,expect){const result=calculate({origin:'156',destination:'860',vehicle:'398',mode:'cargo',weight:20,days:14,via:true,...input});for(const [key,value]of Object.entries(expect))assert.equal(result[key],value,name+': '+key);count++;return result}
check('Kazakhstan third-country no fee',{}, {type:5,base:0,total:0});
check('All foreign countries identical',{origin:'276',destination:'276',vehicle:'276'},{error:'same'});
check('Transit outside Uzbekistan',{origin:'643',destination:'004',vehicle:'398',via:false},{error:'noUz'});
check('Foreign transit valid',{origin:'643',destination:'004',vehicle:'398'},{type:3,base:0});
check('Afghan transit',{origin:'643',destination:'398',vehicle:'004'},{type:3,base:50,total:50});
for(const [weight,base]of [[10,130],[10.01,180],[20,180],[20.01,250]])check('Turkmen capacity '+weight,{origin:'795',vehicle:'795',weight},{base,total:base});
check('Turkmen third-country surcharge',{vehicle:'795',weight:21},{base:250,extra:375,total:625});
check('Turkmen outbound surcharge independent of base',{origin:'860',destination:'795',vehicle:'795'},{type:1,base:0,extra:375,total:375});
check('Turkmen humanitarian',{vehicle:'795',weight:21,humanitarian:true},{base:125,baseBefore:250,extra:375,total:500});
for(const [days,base]of [[14,80],[15,280]])check('Azerbaijan stay '+days,{origin:'031',vehicle:'031',days},{base,total:base});
check('Exempt EU fee remains zero',{origin:'276',vehicle:'276',days:15},{base:0,total:0});
check('Humanitarian exempt',{humanitarian:true},{base:0,baseBefore:null,total:0});
check('Explicit form purchase',{purchase:true},{base:0,purchase:800,total:800});
check('No implicit form purchase',{}, {purchase:0,total:0});
check('Transit form purchase',{origin:'643',destination:'004',purchase:true},{purchase:200,total:200});
check('National vehicle',{vehicle:'860'},{base:0,total:0});
check('Prohibited cabotage',{origin:'860',destination:'860',vehicle:'398'},{blocked:true});
check('Empty entry',{origin:'795',vehicle:'795',mode:'7',weight:10},{type:7,base:130,extra:0});
check('Invalid empty entry',{destination:'398',mode:'7'},{error:'emptyInvalid'});
check('Invalid capacity',{origin:'795',vehicle:'795',weight:0},{error:'badWeight'});
check('Invalid stay',{origin:'031',vehicle:'031',days:14.5},{error:'badDays'});
check('Unknown countries not treated as identical',{origin:'000',vehicle:'000'},{error:'unknownRelation'});
check('Humanitarian stay',{origin:'031',vehicle:'031',days:15,humanitarian:true},{base:140,total:140});
assert(searchCountries('qozogston').includes('398'));count++;
assert(searchCountries('росия').includes('643'));count++;
assert(searchCountries('Uzbekstan').includes('860'));count++;
assert.equal(searchCountries('004')[0],'004');count++;
assert.equal(Object.keys(data.countries).length,138);count++;
for(const [country,rules]of Object.entries(data.rules))for(const [type,rule]of Object.entries(rules)){
 let origin='156',destination='860',mode='cargo';
 if(type==='1'){origin='860';destination=country}else if(type==='2'){origin=country;destination='860'}else if(type==='3'){origin='643';destination='004'}else if(type==='4'){origin='860';destination=country==='156'?'643':'156'}else if(type==='5'){origin=country==='156'?'643':'156'}else if(type==='6'){origin='860';destination='860'}else if(type==='7'){mode='7'}else if(type==='8'){origin='643';destination='004';mode='8'}
 const r=calculate({origin,destination,vehicle:country,mode,via:true,weight:21,days:15});
 if(r.error)continue;
 assert(!Number.isNaN(r.total));
 if(rule.d==='2'&&!r.blocked)assert.equal(r.base,0,country+'/'+type);
 count++;
}
console.log('Logic checks:',count);
async function browserTests(){
 const {chromium}=require('C:/Users/h.hayitov/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 try{
 const page=await browser.newPage({viewport:{width:1366,height:960}});const errors=[],requests=[];
 page.on('pageerror',e=>errors.push(e.message));page.on('request',r=>{if(/^https?:/.test(r.url()))requests.push(r.url())});
 await page.goto(pathToFileURL(path.join(root,'Dazvol.html')).href);
 await page.locator('#origin').fill('xitoy');await page.locator('#origin-list [data-code="156"]').click();
 await page.locator('#destination').fill('uzbekstan');await page.locator('#destination-list [data-code="860"]').click();
 await page.locator('#vehicle').fill('turkman');await page.locator('#vehicle-list [data-code="795"]').click();
 await page.locator('#weight').fill('21');await page.locator('#calculate').click();
 await page.locator('#result').waitFor({state:'visible'});assert.match(await page.locator('.total').innerText(),/625 USD/);
 assert.equal(await page.locator('#origin').inputValue(),'Xitoy');
 await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:path.join(root,'tools/dazvol-desktop.png'),fullPage:true,animations:'disabled'});
 for(const lang of ['ru','en','uz']){await page.locator('[data-lang="'+lang+'"]').click();assert.equal(await page.locator('html').getAttribute('lang'),lang);assert.equal(await page.locator('#result').isVisible(),true)}
 await page.locator('#vehicle').fill('Ozarbayjon');await page.locator('#vehicle-list [data-code="031"]').click();
 await page.locator('#origin').fill('Ozarbayjon');await page.locator('#origin-list [data-code="031"]').click();
 await page.locator('#days').fill('15');await page.locator('#calculate').click();assert.match(await page.locator('.total').innerText(),/280 USD/);
 await page.setViewportSize({width:390,height:844});await page.evaluate(()=>window.scrollTo(0,0));
 await page.screenshot({path:path.join(root,'tools/dazvol-mobile.png'),fullPage:true,animations:'disabled'});
 for(const width of [320,390,768,1366,1920]){await page.setViewportSize({width,height:900});assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'No horizontal overflow '+width)}
 const broken=await page.locator('img').evaluateAll(images=>images.filter(i=>!i.complete||!i.naturalWidth).length);assert.equal(broken,0,'Embedded flags');assert.equal(requests.length,0,'No runtime network requests');assert.deepEqual(errors,[],'No JavaScript errors');
 await page.locator('#reset').click();assert.equal(await page.locator('#result').isVisible(),false);await page.locator('#calculate').click();assert.equal(await page.locator('#error').isVisible(),true);assert.deepEqual(errors,[],'No JavaScript errors after reset');
 console.log('Browser checks passed: 3 languages, 5 widths, country selection, calculation, reset, embedded flags, no network, no JS errors.');
 }finally{await browser.close()}
}
browserTests().catch(e=>{console.error(e);process.exitCode=1});
