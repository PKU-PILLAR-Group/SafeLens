const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=["./AttentionPatternMatrix-BvBtWlQ2.js","./vendor-react-Dk8-RHi1.js","./SpecializedMatrixCanvas-Dkrm9O5R.js","./MatrixTokenDetail-B60_jTDK.js","./useMatrixRangeBrush-CLq3R7rv.js","./vendor-icons-CO8bWA-z.js","./scrollElementInlineCenter-F7g_gc4Q.js","./vendor-schema-BNsPtHlQ.js","./ResidualLogitLens-C9NFCh1i.js","./MLPActivationMatrix-Bo8ox3Bx.js","./SignedAttributionMatrix-uV6C6t9H.js","./NLAFidelityMatrix-Cn4agwcC.js","./AttributionJobPanel-BlZOKNCQ.js","./NLAJobPanel-B3gg0q4Z.js","./PatchingJobPanel-C--uR2rf.js","./PatchingCausalMatrix-za-NMj1Q.js","./InterventionJobPanel-DLV5o6eH.js","./InterventionComparison-01fWFLne.js","./CompareDrawer-B4C5S4Aw.js"])))=>i.map(i=>d[i]);
var $o=Object.defineProperty;var Eo=(t,n,a)=>n in t?$o(t,n,{enumerable:!0,configurable:!0,writable:!0,value:a}):t[n]=a;var nn=(t,n,a)=>Eo(t,typeof n!="symbol"?n+"":n,a);import{r as u,j as e,a as Mo,R as Le,c as Po}from"./vendor-react-Dk8-RHi1.js";import{C as Ht,H as Yi,Z as qi,M as Hi,P as Fi,a as Ui,R as Jn,b as Gn,c as Ft,d as qn,G as yt,X as at,e as vn,B as Wo,T as ft,I as zo,f as ot,L as Vt,g as Do,h as Xn,S as Ut,F as Yo,U as Ki,i as dn,j as gt,k as Oi,l as Bi,m as In,n as qo,o as Da,p as dt,D as vt,q as Lt,r as Ho,s as Fo,t as $t,u as Kt,v as Zn,W as Uo,w as Ya,x as Ko,y as Oo,z as qa,A as Be,E as Yt,J as Ha,K as Sn,N as ea,O as Bo,Q as Vi,V as Ot,Y as ta,_ as Vo,$ as Qi,a0 as na,a1 as Ji,a2 as Bt,a3 as Gi,a4 as Qo,a5 as Jo,a6 as Go,a7 as Xi,a8 as Xo,a9 as Hn,aa as js,ab as Zo,ac as el,ad as ja,ae as tl,af as Fa,ag as nl}from"./vendor-icons-CO8bWA-z.js";import{o as B,b as fe,n as f,_ as ye,s as h,a as G,l as Ee,r as It,u as Et,t as Ia}from"./vendor-schema-BNsPtHlQ.js";(function(){const n=document.createElement("link").relList;if(n&&n.supports&&n.supports("modulepreload"))return;for(const i of document.querySelectorAll('link[rel="modulepreload"]'))s(i);new MutationObserver(i=>{for(const r of i)if(r.type==="childList")for(const o of r.addedNodes)o.tagName==="LINK"&&o.rel==="modulepreload"&&s(o)}).observe(document,{childList:!0,subtree:!0});function a(i){const r={};return i.integrity&&(r.integrity=i.integrity),i.referrerPolicy&&(r.referrerPolicy=i.referrerPolicy),i.crossOrigin==="use-credentials"?r.credentials="include":i.crossOrigin==="anonymous"?r.credentials="omit":r.credentials="same-origin",r}function s(i){if(i.ep)return;i.ep=!0;const r=a(i);fetch(i.href,r)}})();const al="modulepreload",sl=function(t,n){return new URL(t,n).href},Is={},ut=function(n,a,s){let i=Promise.resolve();if(a&&a.length>0){let o=function(p){return Promise.all(p.map(g=>Promise.resolve(g).then(b=>({status:"fulfilled",value:b}),b=>({status:"rejected",reason:b}))))};const l=document.getElementsByTagName("link"),c=document.querySelector("meta[property=csp-nonce]"),d=(c==null?void 0:c.nonce)||(c==null?void 0:c.getAttribute("nonce"));i=o(a.map(p=>{if(p=sl(p,s),p in Is)return;Is[p]=!0;const g=p.endsWith(".css"),b=g?'[rel="stylesheet"]':"";if(!!s)for(let m=l.length-1;m>=0;m--){const x=l[m];if(x.href===p&&(!g||x.rel==="stylesheet"))return}else if(document.querySelector(`link[href="${p}"]${b}`))return;const y=document.createElement("link");if(y.rel=g?"stylesheet":al,g||(y.as="script"),y.crossOrigin="",y.href=p,d&&y.setAttribute("nonce",d),document.head.appendChild(y),g)return new Promise((m,x)=>{y.addEventListener("load",m),y.addEventListener("error",()=>x(new Error(`Unable to preload CSS for ${p}`)))})}))}function r(o){const l=new Event("vite:preloadError",{cancelable:!0});if(l.payload=o,window.dispatchEvent(l),!l.defaultPrevented)throw o}return i.then(o=>{for(const l of o||[])l.status==="rejected"&&r(l.reason);return n().catch(r)})},Zi={runId:"real-hf-tiny-gpt2-local-explorer",modelName:"sshleifer/tiny-gpt2",modelSource:"huggingface",sampleId:"real-forward-cache-001",prompt:"User: Compare a benign safety explanation with a jailbreak strategy and explain which tokens trigger the monitor.",tokens:[{index:0,text:"User",tokenId:12982,source:"prompt",isSpecial:!1,risk:.253,attribution:.002},{index:1,text:":",tokenId:25,source:"prompt",isSpecial:!1,risk:.846,attribution:.999},{index:2,text:" Compare",tokenId:27814,source:"prompt",isSpecial:!1,risk:.483,attribution:.949},{index:3,text:" a",tokenId:257,source:"prompt",isSpecial:!1,risk:.155,attribution:.112},{index:4,text:" benign",tokenId:32293,source:"prompt",isSpecial:!1,risk:.311,attribution:.815},{index:5,text:" safety",tokenId:3747,source:"prompt",isSpecial:!1,risk:.392,attribution:.934},{index:6,text:" explanation",tokenId:7468,source:"prompt",isSpecial:!1,risk:.143,attribution:.004},{index:7,text:" with",tokenId:351,source:"prompt",isSpecial:!1,risk:.378,attribution:.908},{index:8,text:" a",tokenId:257,source:"prompt",isSpecial:!1,risk:.524,attribution:.998},{index:9,text:" jail",tokenId:7356,source:"prompt",isSpecial:!1,risk:.728,attribution:.996},{index:10,text:"break",tokenId:9032,source:"prompt",isSpecial:!1,risk:1,attribution:1},{index:11,text:" strategy",tokenId:4811,source:"prompt",isSpecial:!1,risk:.532,attribution:.998},{index:12,text:" and",tokenId:290,source:"prompt",isSpecial:!1,risk:.496,attribution:.991},{index:13,text:" explain",tokenId:4727,source:"prompt",isSpecial:!1,risk:.298,attribution:.307},{index:14,text:" which",tokenId:543,source:"prompt",isSpecial:!1,risk:0,attribution:0},{index:15,text:" tokens",tokenId:16326,source:"prompt",isSpecial:!1,risk:.526,attribution:.032},{index:16,text:" trigger",tokenId:7616,source:"prompt",isSpecial:!1,risk:.707,attribution:.971},{index:17,text:" the",tokenId:262,source:"prompt",isSpecial:!1,risk:.881,attribution:1},{index:18,text:" monitor",tokenId:5671,source:"prompt",isSpecial:!1,risk:.136,attribution:.001},{index:19,text:".",tokenId:13,source:"prompt",isSpecial:!1,risk:.384,attribution:.367}],layers:[0,1],nla:[{tokenIndex:9,layer:1,component:"resid_post",explanation:"Real activation captured from sshleifer/tiny-gpt2, but no registered NLA profile matches this smoke-test model/d_model=2. Supported profiles: qwen2.5-7b-l20, gemma3-12b-l32. Run a matching Qwen/Gemma profile to produce an AV/AR explanation.",cosine:0,mse:0,activationNorm:.041,status:"unavailable",profile:null,source:"real_model_cache",token:" jail"},{tokenIndex:10,layer:1,component:"attn_result",explanation:"Real activation captured from sshleifer/tiny-gpt2, but no registered NLA profile matches this smoke-test model/d_model=2. Supported profiles: qwen2.5-7b-l20, gemma3-12b-l32. Run a matching Qwen/Gemma profile to produce an AV/AR explanation.",cosine:0,mse:0,activationNorm:.07,status:"unavailable",profile:null,source:"real_model_cache",token:"break"},{tokenIndex:11,layer:1,component:"mlp_out",explanation:"Real activation captured from sshleifer/tiny-gpt2, but no registered NLA profile matches this smoke-test model/d_model=2. Supported profiles: qwen2.5-7b-l20, gemma3-12b-l32. Run a matching Qwen/Gemma profile to produce an AV/AR explanation.",cosine:0,mse:0,activationNorm:.047,status:"unavailable",profile:null,source:"real_model_cache",token:" strategy"}],nlaCompatibility:{modelName:"sshleifer/tiny-gpt2",dModel:2,availableLayers:[0,1],profiles:[{name:"qwen2.5-7b-l20",baseModel:"Qwen/Qwen2.5-7B-Instruct",layer:20,component:"resid_post",dModel:3584,modelMatches:!1,layerAvailable:!1,dModelMatches:!1,status:"incompatible",reason:"model requires Qwen/Qwen2.5-7B-Instruct; layer L20 is not cached; d_model requires 3584, run has 2"},{name:"gemma3-12b-l32",baseModel:"google/gemma-3-12b-it",layer:32,component:"resid_post",dModel:3840,modelMatches:!1,layerAvailable:!1,dModelMatches:!1,status:"incompatible",reason:"model requires google/gemma-3-12b-it; layer L32 is not cached; d_model requires 3840, run has 2"}]},attentionHeads:[{id:"L0H0",layer:0,head:0,role:"real attention pattern",riskContribution:.25,entropy:2.996,distributionByToken:[[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.5,.5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.333,.333,.333,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.25,.25,.25,.25,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.2,.2,.2,.2,.2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.167,.167,.167,.167,.167,.167,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.143,.143,.143,.143,.143,.143,.143,0,0,0,0,0,0,0,0,0,0,0,0,0],[.125,.125,.125,.125,.125,.125,.125,.125,0,0,0,0,0,0,0,0,0,0,0,0],[.111,.111,.111,.111,.111,.111,.111,.111,.111,0,0,0,0,0,0,0,0,0,0,0],[.1,.1,.1,.1,.1,.1,.1,.1,.1,.1,0,0,0,0,0,0,0,0,0,0],[.091,.091,.091,.091,.091,.091,.091,.091,.091,.091,.091,0,0,0,0,0,0,0,0,0],[.083,.083,.083,.083,.083,.083,.083,.083,.083,.083,.083,.083,0,0,0,0,0,0,0,0],[.077,.077,.077,.077,.077,.077,.077,.077,.077,.077,.077,.077,.077,0,0,0,0,0,0,0],[.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,0,0,0,0,0,0],[.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,0,0,0,0,0],[.062,.063,.063,.062,.063,.063,.062,.063,.063,.063,.063,.063,.063,.062,.062,.062,0,0,0,0],[.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,0,0,0],[.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,0,0],[.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,0],[.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05]]},{id:"L0H1",layer:0,head:1,role:"real attention pattern",riskContribution:.25,entropy:2.996,distributionByToken:[[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.5,.5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.333,.333,.333,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.25,.25,.25,.25,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.2,.2,.2,.2,.2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.167,.167,.167,.167,.167,.167,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.143,.143,.143,.143,.143,.143,.143,0,0,0,0,0,0,0,0,0,0,0,0,0],[.125,.125,.125,.125,.125,.125,.125,.125,0,0,0,0,0,0,0,0,0,0,0,0],[.111,.111,.111,.111,.111,.111,.111,.111,.111,0,0,0,0,0,0,0,0,0,0,0],[.1,.1,.1,.1,.1,.1,.1,.1,.1,.1,0,0,0,0,0,0,0,0,0,0],[.091,.091,.091,.091,.091,.091,.091,.091,.091,.091,.091,0,0,0,0,0,0,0,0,0],[.083,.083,.083,.083,.083,.083,.083,.083,.083,.083,.083,.083,0,0,0,0,0,0,0,0],[.077,.077,.077,.077,.077,.077,.077,.077,.077,.077,.077,.077,.077,0,0,0,0,0,0,0],[.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,0,0,0,0,0,0],[.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,0,0,0,0,0],[.063,.062,.062,.063,.062,.062,.063,.062,.062,.062,.062,.062,.062,.063,.063,.063,0,0,0,0],[.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,0,0,0],[.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,0,0],[.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,0],[.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05]]},{id:"L1H0",layer:1,head:0,role:"real attention pattern",riskContribution:.25,entropy:2.996,distributionByToken:[[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.5,.5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.333,.333,.333,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.25,.25,.25,.25,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.2,.2,.2,.2,.2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.167,.167,.167,.167,.167,.167,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.143,.143,.143,.143,.143,.143,.143,0,0,0,0,0,0,0,0,0,0,0,0,0],[.125,.125,.125,.125,.125,.125,.125,.125,0,0,0,0,0,0,0,0,0,0,0,0],[.111,.111,.111,.111,.111,.111,.111,.111,.111,0,0,0,0,0,0,0,0,0,0,0],[.1,.1,.1,.1,.1,.1,.1,.1,.1,.1,0,0,0,0,0,0,0,0,0,0],[.091,.091,.091,.091,.091,.091,.091,.091,.091,.091,.091,0,0,0,0,0,0,0,0,0],[.083,.083,.083,.083,.083,.083,.083,.083,.083,.083,.083,.083,0,0,0,0,0,0,0,0],[.077,.077,.077,.077,.077,.077,.077,.077,.077,.077,.077,.077,.077,0,0,0,0,0,0,0],[.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,0,0,0,0,0,0],[.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,0,0,0,0,0],[.062,.063,.063,.062,.063,.063,.062,.063,.063,.063,.063,.063,.063,.062,.062,.062,0,0,0,0],[.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,0,0,0],[.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,0,0],[.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,0],[.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05]]},{id:"L1H1",layer:1,head:1,role:"real attention pattern",riskContribution:.25,entropy:2.996,distributionByToken:[[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.5,.5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.334,.333,.333,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.25,.25,.25,.25,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.2,.2,.2,.2,.2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.167,.167,.167,.167,.167,.167,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.143,.143,.143,.143,.143,.143,.143,0,0,0,0,0,0,0,0,0,0,0,0,0],[.125,.125,.125,.125,.125,.125,.125,.125,0,0,0,0,0,0,0,0,0,0,0,0],[.111,.111,.111,.111,.111,.111,.111,.111,.111,0,0,0,0,0,0,0,0,0,0,0],[.1,.1,.1,.1,.1,.1,.1,.1,.1,.1,0,0,0,0,0,0,0,0,0,0],[.091,.091,.091,.091,.091,.091,.091,.091,.091,.091,.091,0,0,0,0,0,0,0,0,0],[.083,.083,.083,.083,.083,.083,.083,.083,.083,.083,.083,.083,0,0,0,0,0,0,0,0],[.077,.077,.077,.077,.077,.077,.077,.077,.077,.077,.077,.077,.077,0,0,0,0,0,0,0],[.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,0,0,0,0,0,0],[.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,0,0,0,0,0],[.062,.063,.063,.062,.063,.063,.062,.063,.063,.063,.063,.063,.063,.062,.062,.062,0,0,0,0],[.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,0,0,0],[.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,0,0],[.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,0],[.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05]]}],mlpNeurons:[{id:"L0N0006",layer:0,neuron:6,label:"real MLP post neuron",activation:1,riskContribution:.175,topTokens:[10,17,1],positiveTopTokens:[10,17,1],negativeTopTokens:[14,18,0],activationsByToken:[-.021928,.023653,.021389,-.017681,.015592,.020802,-.021785,.01965,.023637,.023491,.023713,.02362,.023261,-.00957,-.021953,-.02072,.02241,.023709,-.021937,-.006694],maxAbsoluteActivation:.023713},{id:"L0N0001",layer:0,neuron:1,label:"real MLP post neuron",activation:.698,riskContribution:.175,topTokens:[14,18,0],positiveTopTokens:[14,18,0],negativeTopTokens:[10,17,1],activationsByToken:[.016543,-.015759,-.014333,.013173,-.010604,-.01396,.016428,-.013226,-.015749,-.015658,-.015797,-.015739,-.015513,.006966,.016563,.015576,-.014978,-.015794,.01655,.004834],maxAbsoluteActivation:.016563},{id:"L0N0004",layer:0,neuron:4,label:"real MLP post neuron",activation:.527,riskContribution:.172,topTokens:[10,17,1],positiveTopTokens:[10,17,1],negativeTopTokens:[14,18,0],activationsByToken:[-.01196,.012473,.011296,-.00961,.008267,.01099,-.011881,.01039,.012465,.012389,.012505,.012456,.01227,-.005168,-.011974,-.01129,.011828,.012502,-.011965,-.003607],maxAbsoluteActivation:.012505},{id:"L0N0002",layer:0,neuron:2,label:"real MLP post neuron",activation:.359,riskContribution:.172,topTokens:[14,18,0],positiveTopTokens:[14,18,0],negativeTopTokens:[10,17,1],activationsByToken:[.0085,-.0083,-.00754,.006785,-.005561,-.007341,.008441,-.006951,-.008294,-.008246,-.00832,-.008289,-.008169,.003604,.00851,.008009,-.007883,-.008319,.008504,.002505],maxAbsoluteActivation:.00851},{id:"L0N0005",layer:0,neuron:5,label:"real MLP post neuron",activation:.323,riskContribution:.172,topTokens:[10,17,1],positiveTopTokens:[10,17,1],negativeTopTokens:[14,18,0],activationsByToken:[-.007439,.007643,.006927,-.005968,.005078,.00674,-.007389,.006374,.007638,.007592,.007662,.007633,.00752,-.0032,-.007448,-.007019,.00725,.007661,-.007442,-.002232],maxAbsoluteActivation:.007662},{id:"L0N0007",layer:0,neuron:7,label:"real MLP post neuron",activation:.302,riskContribution:.171,topTokens:[10,17,1],positiveTopTokens:[10,17,1],negativeTopTokens:[14,18,0],activationsByToken:[-.006956,.007135,.006467,-.005579,.004742,.006293,-.006909,.005951,.00713,.007087,.007153,.007126,.00702,-.002991,-.006964,-.006563,.006769,.007152,-.006959,-.002085],maxAbsoluteActivation:.007153},{id:"L0N0003",layer:0,neuron:3,label:"real MLP post neuron",activation:.228,riskContribution:.171,topTokens:[14,18,0],positiveTopTokens:[14,18,0],negativeTopTokens:[10,17,1],activationsByToken:[.005394,-.005318,-.004829,.004309,-.003558,-.004701,.005357,-.00445,-.005315,-.005283,-.005331,-.005311,-.005234,.002293,.0054,.005083,-.00505,-.00533,.005396,.001595],maxAbsoluteActivation:.0054},{id:"L0N0000",layer:0,neuron:0,label:"real MLP post neuron",activation:.136,riskContribution:.171,topTokens:[10,17,1],positiveTopTokens:[10,17,1],negativeTopTokens:[14,18,0],activationsByToken:[-.003167,.003209,.00291,-.002537,.002137,.002832,-.003145,.002679,.003207,.003188,.003217,.003205,.003157,-.001357,-.003171,-.002987,.003045,.003216,-.003168,-945e-6],maxAbsoluteActivation:.003217},{id:"L1N0000",layer:1,neuron:0,label:"real MLP post neuron",activation:1,riskContribution:.178,topTokens:[10,17,1],positiveTopTokens:[10,17,1],negativeTopTokens:[14,18,0],activationsByToken:[-.028428,.031367,.028136,-.022469,.019793,.027279,-.028233,.025585,.031346,.031144,.031451,.031323,.030825,-.011125,-.028457,-.026754,.02961,.031446,-.028436,-.007715],maxAbsoluteActivation:.031451},{id:"L1N0004",layer:1,neuron:4,label:"real MLP post neuron",activation:.718,riskContribution:.179,topTokens:[14,18,0],positiveTopTokens:[14,18,0],negativeTopTokens:[10,17,1],activationsByToken:[.022556,-.0211,-.01908,.017507,-.013711,-.018539,.022387,-.017462,-.021087,-.020962,-.021152,-.021073,-.020763,.008383,.022581,.021118,-.020006,-.021149,.022563,.005757],maxAbsoluteActivation:.022581},{id:"L1N0003",layer:1,neuron:3,label:"real MLP post neuron",activation:.553,riskContribution:.175,topTokens:[10,17,1],positiveTopTokens:[10,17,1],negativeTopTokens:[14,18,0],activationsByToken:[-.016391,.017349,.015591,-.012893,.011024,.015124,-.016276,.014199,.017337,.017228,.017394,.017325,.017054,-.006328,-.016408,-.015404,.016394,.017391,-.016395,-.004378],maxAbsoluteActivation:.017394},{id:"L1N0007",layer:1,neuron:7,label:"real MLP post neuron",activation:.465,riskContribution:.174,topTokens:[10,17,1],positiveTopTokens:[10,17,1],negativeTopTokens:[14,18,0],activationsByToken:[-.013892,.01458,.013108,-.010916,.009279,.012717,-.013793,.011942,.014571,.014479,.014618,.01456,.014334,-.005349,-.013906,-.013052,.013781,.014616,-.013896,-.003698],maxAbsoluteActivation:.014618},{id:"L1N0006",layer:1,neuron:6,label:"real MLP post neuron",activation:.303,riskContribution:.174,topTokens:[10,17,1],positiveTopTokens:[10,17,1],negativeTopTokens:[14,18,0],activationsByToken:[-.009197,.009503,.00855,-.007214,.006064,.008297,-.009131,.007794,.009497,.009438,.009528,.00949,.009344,-.003524,-.009206,-.008636,.008986,.009526,-.009199,-.002434],maxAbsoluteActivation:.009528},{id:"L1N0002",layer:1,neuron:2,label:"real MLP post neuron",activation:.232,riskContribution:.173,topTokens:[10,17,1],positiveTopTokens:[10,17,1],negativeTopTokens:[14,18,0],activationsByToken:[-.007105,.007292,.006563,-.005569,.004659,.006369,-.007054,.005984,.007287,.007242,.007311,.007282,.00717,-.002716,-.007113,-.006671,.006896,.007309,-.007107,-.001876],maxAbsoluteActivation:.007311},{id:"L1N0001",layer:1,neuron:1,label:"real MLP post neuron",activation:.172,riskContribution:.173,topTokens:[14,18,0],positiveTopTokens:[14,18,0],negativeTopTokens:[10,17,1],activationsByToken:[.005403,-.005327,-.004804,.004216,-.003428,-.004664,.005363,-.004387,-.005323,-.005291,-.00534,-.00532,-.005239,.00204,.005408,.005066,-.005043,-.005339,.005404,.001405],maxAbsoluteActivation:.005408},{id:"L1N0005",layer:1,neuron:5,label:"real MLP post neuron",activation:.043,riskContribution:.172,topTokens:[10,17,1],positiveTopTokens:[10,17,1],negativeTopTokens:[14,18,0],activationsByToken:[-.001334,.001344,.001211,-.001044,861e-6,.001175,-.001325,.001105,.001343,.001335,.001347,.001342,.001322,-507e-6,-.001336,-.001252,.001271,.001347,-.001335,-35e-5],maxAbsoluteActivation:.001347}],residualCells:[{layer:0,tokenIndex:0,norm:.044,rawDirection:-.013081,riskDirection:.252,semanticDensity:.598},{layer:0,tokenIndex:1,norm:.053,rawDirection:.053175,riskDirection:.847,semanticDensity:.74},{layer:0,tokenIndex:2,norm:.013,rawDirection:.012987,riskDirection:.486,semanticDensity:.127},{layer:0,tokenIndex:3,norm:.036,rawDirection:-.02387,riskDirection:.155,semanticDensity:.472},{layer:0,tokenIndex:4,norm:.017,rawDirection:-.006022,riskDirection:.315,semanticDensity:.185},{layer:0,tokenIndex:5,norm:.01,rawDirection:.003024,riskDirection:.396,semanticDensity:.077},{layer:0,tokenIndex:6,norm:.026,rawDirection:-.025226,riskDirection:.142,semanticDensity:.323},{layer:0,tokenIndex:7,norm:.01,rawDirection:.001409,riskDirection:.382,semanticDensity:.067},{layer:0,tokenIndex:8,norm:.05,rawDirection:.017587,riskDirection:.527,semanticDensity:.681},{layer:0,tokenIndex:9,norm:.041,rawDirection:.040134,riskDirection:.73,semanticDensity:.557},{layer:0,tokenIndex:10,norm:.07,rawDirection:.07019,riskDirection:1,semanticDensity:1},{layer:0,tokenIndex:11,norm:.045,rawDirection:.018461,riskDirection:.535,semanticDensity:.612},{layer:0,tokenIndex:12,norm:.022,rawDirection:.014512,riskDirection:.5,semanticDensity:.252},{layer:0,tokenIndex:13,norm:.012,rawDirection:-.007909,riskDirection:.298,semanticDensity:.101},{layer:0,tokenIndex:14,norm:.041,rawDirection:-.041081,riskDirection:0,semanticDensity:.554},{layer:0,tokenIndex:15,norm:.05,rawDirection:.017092,riskDirection:.523,semanticDensity:.696},{layer:0,tokenIndex:16,norm:.052,rawDirection:.037751,riskDirection:.708,semanticDensity:.718},{layer:0,tokenIndex:17,norm:.059,rawDirection:.057025,riskDirection:.882,semanticDensity:.824},{layer:0,tokenIndex:18,norm:.035,rawDirection:-.026055,riskDirection:.135,semanticDensity:.461},{layer:0,tokenIndex:19,norm:.005,rawDirection:.001673,riskDirection:.384,semanticDensity:0},{layer:1,tokenIndex:0,norm:.046,rawDirection:-.012687,riskDirection:.255,semanticDensity:.626},{layer:1,tokenIndex:1,norm:.053,rawDirection:.05284,riskDirection:.844,semanticDensity:.733},{layer:1,tokenIndex:2,norm:.013,rawDirection:.012692,riskDirection:.483,semanticDensity:.118},{layer:1,tokenIndex:3,norm:.035,rawDirection:-.023539,riskDirection:.158,semanticDensity:.454},{layer:1,tokenIndex:4,norm:.018,rawDirection:-.006243,riskDirection:.313,semanticDensity:.202},{layer:1,tokenIndex:5,norm:.012,rawDirection:.002737,riskDirection:.394,semanticDensity:.1},{layer:1,tokenIndex:6,norm:.026,rawDirection:-.024793,riskDirection:.146,semanticDensity:.323},{layer:1,tokenIndex:7,norm:.011,rawDirection:.001134,riskDirection:.379,semanticDensity:.089},{layer:1,tokenIndex:8,norm:.051,rawDirection:.017263,riskDirection:.524,semanticDensity:.706},{layer:1,tokenIndex:9,norm:.041,rawDirection:.039815,riskDirection:.727,semanticDensity:.546},{layer:1,tokenIndex:10,norm:.07,rawDirection:.069871,riskDirection:.997,semanticDensity:.994},{layer:1,tokenIndex:11,norm:.047,rawDirection:.018145,riskDirection:.532,semanticDensity:.637},{layer:1,tokenIndex:12,norm:.023,rawDirection:.014202,riskDirection:.497,semanticDensity:.271},{layer:1,tokenIndex:13,norm:.011,rawDirection:-.007739,riskDirection:.3,semanticDensity:.094},{layer:1,tokenIndex:14,norm:.041,rawDirection:-.040634,riskDirection:.004,semanticDensity:.55},{layer:1,tokenIndex:15,norm:.052,rawDirection:.017505,riskDirection:.527,semanticDensity:.719},{layer:1,tokenIndex:16,norm:.051,rawDirection:.037443,riskDirection:.706,semanticDensity:.697},{layer:1,tokenIndex:17,norm:.059,rawDirection:.056703,riskDirection:.879,semanticDensity:.827},{layer:1,tokenIndex:18,norm:.036,rawDirection:-.025611,riskDirection:.139,semanticDensity:.473},{layer:1,tokenIndex:19,norm:.006,rawDirection:.001786,riskDirection:.385,semanticDensity:.006}],jLens:[],logitLens:[{layer:0,tokenIndex:0,targetTokenId:25,targetTokenText:":",targetLogit:-.010543,targetProbability:1968e-8,targetRank:32530,topPredictions:[{tokenId:5087,tokenText:" factors",logit:.114459,probability:223e-7},{tokenId:13584,tokenText:" mutual",logit:.112374,probability:2226e-8},{tokenId:31685,tokenText:" deflect",logit:.11141,probability:2224e-8},{tokenId:21516,tokenText:" Television",logit:.109414,probability:2219e-8},{tokenId:40169,tokenText:" boils",logit:.107044,probability:2214e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:1,targetTokenId:27814,targetTokenText:" Compare",targetLogit:.017864,targetProbability:2025e-8,targetRank:13162,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.128454,probability:2262e-8},{tokenId:17192,tokenText:" vendors",logit:.126809,probability:2258e-8},{tokenId:38361,tokenText:" intermittent",logit:.116339,probability:2234e-8},{tokenId:43423,tokenText:" hauled",logit:.109236,probability:2218e-8},{tokenId:9702,tokenText:" Brew",logit:.10787,probability:2215e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:2,targetTokenId:257,targetTokenText:" a",targetLogit:.022717,targetProbability:2035e-8,targetRank:9207,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.115576,probability:2233e-8},{tokenId:17192,tokenText:" vendors",logit:.114097,probability:2229e-8},{tokenId:38361,tokenText:" intermittent",logit:.104676,probability:2209e-8},{tokenId:43423,tokenText:" hauled",logit:.098285,probability:2194e-8},{tokenId:9702,tokenText:" Brew",logit:.097056,probability:2192e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:3,targetTokenId:32293,targetTokenText:" benign",targetLogit:.005327,targetProbability:2e-5,targetRank:20177,topPredictions:[{tokenId:5087,tokenText:" factors",logit:.089545,probability:2176e-8},{tokenId:13584,tokenText:" mutual",logit:.087914,probability:2172e-8},{tokenId:31685,tokenText:" deflect",logit:.08716,probability:2171e-8},{tokenId:21516,tokenText:" Television",logit:.085598,probability:2167e-8},{tokenId:40169,tokenText:" boils",logit:.083744,probability:2163e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:4,targetTokenId:3747,targetTokenText:" safety",targetLogit:-.021742,targetProbability:1947e-8,targetRank:44645,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.081969,probability:2159e-8},{tokenId:17192,tokenText:" vendors",logit:.080919,probability:2157e-8},{tokenId:38361,tokenText:" intermittent",logit:.074238,probability:2143e-8},{tokenId:43423,tokenText:" hauled",logit:.069706,probability:2133e-8},{tokenId:9702,tokenText:" Brew",logit:.068834,probability:2131e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:5,targetTokenId:7468,targetTokenText:" explanation",targetLogit:-.020505,targetProbability:1949e-8,targetRank:40262,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.11215,probability:2225e-8},{tokenId:17192,tokenText:" vendors",logit:.110714,probability:2222e-8},{tokenId:38361,tokenText:" intermittent",logit:.101572,probability:2202e-8},{tokenId:43423,tokenText:" hauled",logit:.095371,probability:2188e-8},{tokenId:9702,tokenText:" Brew",logit:.094179,probability:2186e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:6,targetTokenId:351,targetTokenText:" with",targetLogit:-718e-6,targetProbability:1988e-8,targetRank:25594,topPredictions:[{tokenId:5087,tokenText:" factors",logit:.113647,probability:2229e-8},{tokenId:13584,tokenText:" mutual",logit:.111577,probability:2224e-8},{tokenId:31685,tokenText:" deflect",logit:.11062,probability:2222e-8},{tokenId:21516,tokenText:" Television",logit:.108637,probability:2217e-8},{tokenId:40169,tokenText:" boils",logit:.106285,probability:2212e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:7,targetTokenId:257,targetTokenText:" a",targetLogit:.020719,targetProbability:2031e-8,targetRank:9207,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.10541,probability:221e-7},{tokenId:17192,tokenText:" vendors",logit:.104061,probability:2207e-8},{tokenId:38361,tokenText:" intermittent",logit:.095468,probability:2188e-8},{tokenId:43423,tokenText:" hauled",logit:.08964,probability:2176e-8},{tokenId:9702,tokenText:" Brew",logit:.088519,probability:2173e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:8,targetTokenId:7356,targetTokenText:" jail",targetLogit:.026281,targetProbability:2042e-8,targetRank:8709,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.128369,probability:2261e-8},{tokenId:17192,tokenText:" vendors",logit:.126725,probability:2258e-8},{tokenId:38361,tokenText:" intermittent",logit:.116261,probability:2234e-8},{tokenId:43423,tokenText:" hauled",logit:.109163,probability:2218e-8},{tokenId:9702,tokenText:" Brew",logit:.107799,probability:2215e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:9,targetTokenId:9032,targetTokenText:"break",targetLogit:.031787,targetProbability:2053e-8,targetRank:6360,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.127572,probability:226e-7},{tokenId:17192,tokenText:" vendors",logit:.125939,probability:2256e-8},{tokenId:38361,tokenText:" intermittent",logit:.11554,probability:2232e-8},{tokenId:43423,tokenText:" hauled",logit:.108486,probability:2217e-8},{tokenId:9702,tokenText:" Brew",logit:.10713,probability:2214e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:10,targetTokenId:4811,targetTokenText:" strategy",targetLogit:.026769,targetProbability:2043e-8,targetRank:8518,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.12878,probability:2262e-8},{tokenId:17192,tokenText:" vendors",logit:.127132,probability:2259e-8},{tokenId:38361,tokenText:" intermittent",logit:.116634,probability:2235e-8},{tokenId:43423,tokenText:" hauled",logit:.109514,probability:2219e-8},{tokenId:9702,tokenText:" Brew",logit:.108145,probability:2216e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:11,targetTokenId:290,targetTokenText:" and",targetLogit:.0154,targetProbability:202e-7,targetRank:14612,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.128277,probability:2261e-8},{tokenId:17192,tokenText:" vendors",logit:.126635,probability:2257e-8},{tokenId:38361,tokenText:" intermittent",logit:.116179,probability:2234e-8},{tokenId:43423,tokenText:" hauled",logit:.109086,probability:2218e-8},{tokenId:9702,tokenText:" Brew",logit:.107722,probability:2215e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:12,targetTokenId:4727,targetTokenText:" explain",targetLogit:-.022317,targetProbability:1945e-8,targetRank:39841,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.126299,probability:2257e-8},{tokenId:17192,tokenText:" vendors",logit:.124682,probability:2253e-8},{tokenId:38361,tokenText:" intermittent",logit:.114387,probability:223e-7},{tokenId:43423,tokenText:" hauled",logit:.107404,probability:2214e-8},{tokenId:9702,tokenText:" Brew",logit:.106061,probability:2211e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:13,targetTokenId:543,targetTokenText:" which",targetLogit:.007802,targetProbability:2005e-8,targetRank:11957,topPredictions:[{tokenId:5087,tokenText:" factors",logit:.045334,probability:2082e-8},{tokenId:13584,tokenText:" mutual",logit:.044508,probability:208e-7},{tokenId:31685,tokenText:" deflect",logit:.044127,probability:2079e-8},{tokenId:21516,tokenText:" Television",logit:.043336,probability:2078e-8},{tokenId:40169,tokenText:" boils",logit:.042397,probability:2076e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:14,targetTokenId:16326,targetTokenText:" tokens",targetLogit:.04567,targetProbability:2082e-8,targetRank:2554,topPredictions:[{tokenId:5087,tokenText:" factors",logit:.114597,probability:2231e-8},{tokenId:13584,tokenText:" mutual",logit:.112509,probability:2226e-8},{tokenId:31685,tokenText:" deflect",logit:.111544,probability:2224e-8},{tokenId:21516,tokenText:" Television",logit:.109545,probability:2219e-8},{tokenId:40169,tokenText:" boils",logit:.107173,probability:2214e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:15,targetTokenId:7616,targetTokenText:" trigger",targetLogit:-.01032,targetProbability:1969e-8,targetRank:32824,topPredictions:[{tokenId:5087,tokenText:" factors",logit:.107468,probability:2215e-8},{tokenId:13584,tokenText:" mutual",logit:.105511,probability:2211e-8},{tokenId:31685,tokenText:" deflect",logit:.104606,probability:2209e-8},{tokenId:21516,tokenText:" Television",logit:.102731,probability:2204e-8},{tokenId:40169,tokenText:" boils",logit:.100506,probability:22e-6}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:16,targetTokenId:262,targetTokenText:" the",targetLogit:.073626,targetProbability:2141e-8,targetRank:155,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.121483,probability:2246e-8},{tokenId:17192,tokenText:" vendors",logit:.119928,probability:2242e-8},{tokenId:38361,tokenText:" intermittent",logit:.110025,probability:222e-7},{tokenId:43423,tokenText:" hauled",logit:.103308,probability:2205e-8},{tokenId:9702,tokenText:" Brew",logit:.102017,probability:2203e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:17,targetTokenId:5671,targetTokenText:" monitor",targetLogit:-.033165,targetProbability:1924e-8,targetRank:44310,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.128759,probability:2262e-8},{tokenId:17192,tokenText:" vendors",logit:.127111,probability:2258e-8},{tokenId:38361,tokenText:" intermittent",logit:.116615,probability:2235e-8},{tokenId:43423,tokenText:" hauled",logit:.109496,probability:2219e-8},{tokenId:9702,tokenText:" Brew",logit:.108127,probability:2216e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:18,targetTokenId:13,targetTokenText:".",targetLogit:.038063,targetProbability:2066e-8,targetRank:4363,topPredictions:[{tokenId:5087,tokenText:" factors",logit:.114508,probability:223e-7},{tokenId:13584,tokenText:" mutual",logit:.112423,probability:2226e-8},{tokenId:31685,tokenText:" deflect",logit:.111458,probability:2224e-8},{tokenId:21516,tokenText:" Television",logit:.109461,probability:2219e-8},{tokenId:40169,tokenText:" boils",logit:.10709,probability:2214e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:19,targetTokenId:5087,targetTokenText:" factors",targetLogit:.031153,targetProbability:2053e-8,targetRank:1,topPredictions:[{tokenId:5087,tokenText:" factors",logit:.031153,probability:2053e-8},{tokenId:13584,tokenText:" mutual",logit:.030586,probability:2052e-8},{tokenId:31685,tokenText:" deflect",logit:.030324,probability:2051e-8},{tokenId:21516,tokenText:" Television",logit:.02978,probability:205e-7},{tokenId:40169,tokenText:" boils",logit:.029135,probability:2049e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:0,targetTokenId:25,targetTokenText:":",targetLogit:-.010547,targetProbability:1968e-8,targetRank:32530,topPredictions:[{tokenId:5087,tokenText:" factors",logit:.114501,probability:223e-7},{tokenId:13584,tokenText:" mutual",logit:.112415,probability:2226e-8},{tokenId:31685,tokenText:" deflect",logit:.111451,probability:2224e-8},{tokenId:21516,tokenText:" Television",logit:.109453,probability:2219e-8},{tokenId:40169,tokenText:" boils",logit:.107083,probability:2214e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:1,targetTokenId:27814,targetTokenText:" Compare",targetLogit:.017867,targetProbability:2025e-8,targetRank:13162,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.128476,probability:2262e-8},{tokenId:17192,tokenText:" vendors",logit:.126831,probability:2258e-8},{tokenId:38361,tokenText:" intermittent",logit:.116358,probability:2234e-8},{tokenId:43423,tokenText:" hauled",logit:.109255,probability:2218e-8},{tokenId:9702,tokenText:" Brew",logit:.107889,probability:2215e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:2,targetTokenId:257,targetTokenText:" a",targetLogit:.023019,targetProbability:2035e-8,targetRank:9207,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.117112,probability:2236e-8},{tokenId:17192,tokenText:" vendors",logit:.115613,probability:2233e-8},{tokenId:38361,tokenText:" intermittent",logit:.106067,probability:2212e-8},{tokenId:43423,tokenText:" hauled",logit:.099591,probability:2197e-8},{tokenId:9702,tokenText:" Brew",logit:.098346,probability:2195e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:3,targetTokenId:32293,targetTokenText:" benign",targetLogit:.005477,targetProbability:2e-5,targetRank:20177,topPredictions:[{tokenId:5087,tokenText:" factors",logit:.092072,probability:2181e-8},{tokenId:13584,tokenText:" mutual",logit:.090395,probability:2178e-8},{tokenId:31685,tokenText:" deflect",logit:.08962,probability:2176e-8},{tokenId:21516,tokenText:" Television",logit:.088013,probability:2172e-8},{tokenId:40169,tokenText:" boils",logit:.086107,probability:2168e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:4,targetTokenId:3747,targetTokenText:" safety",targetLogit:-.023186,targetProbability:1944e-8,targetRank:44645,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.087413,probability:2171e-8},{tokenId:17192,tokenText:" vendors",logit:.086294,probability:2169e-8},{tokenId:38361,tokenText:" intermittent",logit:.079168,probability:2153e-8},{tokenId:43423,tokenText:" hauled",logit:.074335,probability:2143e-8},{tokenId:9702,tokenText:" Brew",logit:.073406,probability:2141e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:5,targetTokenId:7468,targetTokenText:" explanation",targetLogit:-.020874,targetProbability:1948e-8,targetRank:40262,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.11417,probability:223e-7},{tokenId:17192,tokenText:" vendors",logit:.112708,probability:2226e-8},{tokenId:38361,tokenText:" intermittent",logit:.103402,probability:2206e-8},{tokenId:43423,tokenText:" hauled",logit:.097089,probability:2192e-8},{tokenId:9702,tokenText:" Brew",logit:.095875,probability:2189e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:6,targetTokenId:351,targetTokenText:" with",targetLogit:-718e-6,targetProbability:1988e-8,targetRank:25594,topPredictions:[{tokenId:5087,tokenText:" factors",logit:.113716,probability:2229e-8},{tokenId:13584,tokenText:" mutual",logit:.111645,probability:2224e-8},{tokenId:31685,tokenText:" deflect",logit:.110687,probability:2222e-8},{tokenId:21516,tokenText:" Television",logit:.108704,probability:2218e-8},{tokenId:40169,tokenText:" boils",logit:.106349,probability:2212e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:7,targetTokenId:257,targetTokenText:" a",targetLogit:.021291,targetProbability:2032e-8,targetRank:9207,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.108318,probability:2217e-8},{tokenId:17192,tokenText:" vendors",logit:.106931,probability:2214e-8},{tokenId:38361,tokenText:" intermittent",logit:.098101,probability:2194e-8},{tokenId:43423,tokenText:" hauled",logit:.092112,probability:2181e-8},{tokenId:9702,tokenText:" Brew",logit:.090961,probability:2179e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:8,targetTokenId:7356,targetTokenText:" jail",targetLogit:.026286,targetProbability:2042e-8,targetRank:8709,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.128396,probability:2261e-8},{tokenId:17192,tokenText:" vendors",logit:.126752,probability:2258e-8},{tokenId:38361,tokenText:" intermittent",logit:.116286,probability:2234e-8},{tokenId:43423,tokenText:" hauled",logit:.109187,probability:2218e-8},{tokenId:9702,tokenText:" Brew",logit:.107822,probability:2215e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:9,targetTokenId:9032,targetTokenText:"break",targetLogit:.031807,targetProbability:2053e-8,targetRank:6360,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.12765,probability:226e-7},{tokenId:17192,tokenText:" vendors",logit:.126016,probability:2256e-8},{tokenId:38361,tokenText:" intermittent",logit:.115611,probability:2233e-8},{tokenId:43423,tokenText:" hauled",logit:.108552,probability:2217e-8},{tokenId:9702,tokenText:" Brew",logit:.107195,probability:2214e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:10,targetTokenId:4811,targetTokenText:" strategy",targetLogit:.026771,targetProbability:2043e-8,targetRank:8518,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.12879,probability:2262e-8},{tokenId:17192,tokenText:" vendors",logit:.127141,probability:2259e-8},{tokenId:38361,tokenText:" intermittent",logit:.116643,probability:2235e-8},{tokenId:43423,tokenText:" hauled",logit:.109522,probability:2219e-8},{tokenId:9702,tokenText:" Brew",logit:.108153,probability:2216e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:11,targetTokenId:290,targetTokenText:" and",targetLogit:.015404,targetProbability:202e-7,targetRank:14612,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.128312,probability:2261e-8},{tokenId:17192,tokenText:" vendors",logit:.126669,probability:2257e-8},{tokenId:38361,tokenText:" intermittent",logit:.11621,probability:2234e-8},{tokenId:43423,tokenText:" hauled",logit:.109115,probability:2218e-8},{tokenId:9702,tokenText:" Brew",logit:.107751,probability:2215e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:12,targetTokenId:4727,targetTokenText:" explain",targetLogit:-.022351,targetProbability:1945e-8,targetRank:39841,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.12649,probability:2257e-8},{tokenId:17192,tokenText:" vendors",logit:.12487,probability:2253e-8},{tokenId:38361,tokenText:" intermittent",logit:.11456,probability:223e-7},{tokenId:43423,tokenText:" hauled",logit:.107566,probability:2215e-8},{tokenId:9702,tokenText:" Brew",logit:.106221,probability:2212e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:13,targetTokenId:543,targetTokenText:" which",targetLogit:.008218,targetProbability:2006e-8,targetRank:11957,topPredictions:[{tokenId:5087,tokenText:" factors",logit:.047752,probability:2087e-8},{tokenId:13584,tokenText:" mutual",logit:.046882,probability:2085e-8},{tokenId:31685,tokenText:" deflect",logit:.04648,probability:2084e-8},{tokenId:21516,tokenText:" Television",logit:.045647,probability:2083e-8},{tokenId:40169,tokenText:" boils",logit:.044658,probability:2081e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:14,targetTokenId:16326,targetTokenText:" tokens",targetLogit:.045679,targetProbability:2082e-8,targetRank:2554,topPredictions:[{tokenId:5087,tokenText:" factors",logit:.114617,probability:2231e-8},{tokenId:13584,tokenText:" mutual",logit:.11253,probability:2226e-8},{tokenId:31685,tokenText:" deflect",logit:.111564,probability:2224e-8},{tokenId:21516,tokenText:" Television",logit:.109565,probability:2219e-8},{tokenId:40169,tokenText:" boils",logit:.107192,probability:2214e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:15,targetTokenId:7616,targetTokenText:" trigger",targetLogit:-.010371,targetProbability:1969e-8,targetRank:32824,topPredictions:[{tokenId:5087,tokenText:" factors",logit:.107999,probability:2216e-8},{tokenId:13584,tokenText:" mutual",logit:.106032,probability:2212e-8},{tokenId:31685,tokenText:" deflect",logit:.105123,probability:221e-7},{tokenId:21516,tokenText:" Television",logit:.103238,probability:2206e-8},{tokenId:40169,tokenText:" boils",logit:.101003,probability:2201e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:16,targetTokenId:262,targetTokenText:" the",targetLogit:.074062,targetProbability:2142e-8,targetRank:155,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.122203,probability:2247e-8},{tokenId:17192,tokenText:" vendors",logit:.120638,probability:2244e-8},{tokenId:38361,tokenText:" intermittent",logit:.110677,probability:2222e-8},{tokenId:43423,tokenText:" hauled",logit:.10392,probability:2207e-8},{tokenId:9702,tokenText:" Brew",logit:.102621,probability:2204e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:17,targetTokenId:5671,targetTokenText:" monitor",targetLogit:-.033168,targetProbability:1924e-8,targetRank:44310,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.12877,probability:2262e-8},{tokenId:17192,tokenText:" vendors",logit:.127121,probability:2258e-8},{tokenId:38361,tokenText:" intermittent",logit:.116625,probability:2235e-8},{tokenId:43423,tokenText:" hauled",logit:.109505,probability:2219e-8},{tokenId:9702,tokenText:" Brew",logit:.108136,probability:2216e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:18,targetTokenId:13,targetTokenText:".",targetLogit:.038071,targetProbability:2066e-8,targetRank:4363,topPredictions:[{tokenId:5087,tokenText:" factors",logit:.114533,probability:223e-7},{tokenId:13584,tokenText:" mutual",logit:.112447,probability:2226e-8},{tokenId:31685,tokenText:" deflect",logit:.111483,probability:2224e-8},{tokenId:21516,tokenText:" Television",logit:.109484,probability:2219e-8},{tokenId:40169,tokenText:" boils",logit:.107113,probability:2214e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:19,targetTokenId:5087,targetTokenText:" factors",targetLogit:.033409,targetProbability:2057e-8,targetRank:1,topPredictions:[{tokenId:5087,tokenText:" factors",logit:.033409,probability:2057e-8},{tokenId:13584,tokenText:" mutual",logit:.0328,probability:2056e-8},{tokenId:31685,tokenText:" deflect",logit:.032519,probability:2056e-8},{tokenId:21516,tokenText:" Television",logit:.031936,probability:2054e-8},{tokenId:40169,tokenText:" boils",logit:.031244,probability:2053e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"}],attentionCells:[{layer:0,tokenIndex:0,value:1,rawValue:1,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:1,value:.5,rawValue:.500095,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:2,value:.333,rawValue:.333386,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:3,value:.25,rawValue:.250038,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:4,value:.2,rawValue:.200024,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:5,value:.167,rawValue:.166693,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:6,value:.143,rawValue:.142885,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:7,value:.125,rawValue:.125019,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:8,value:.111,rawValue:.111131,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:9,value:.1,rawValue:.100017,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:10,value:.091,rawValue:.090925,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:11,value:.083,rawValue:.083347,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:12,value:.077,rawValue:.076936,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:13,value:.071,rawValue:.071435,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:14,value:.067,rawValue:.06668,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:15,value:.063,rawValue:.062512,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:16,value:.059,rawValue:.058833,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:17,value:.056,rawValue:.055565,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:18,value:.053,rawValue:.052642,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:19,value:.05,rawValue:.050003,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:1,tokenIndex:0,value:1,rawValue:1,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:1,value:.5,rawValue:.500151,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:2,value:.333,rawValue:.333451,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:3,value:.25,rawValue:.250057,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:4,value:.2,rawValue:.200044,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:5,value:.167,rawValue:.166723,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:6,value:.143,rawValue:.142896,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:7,value:.125,rawValue:.125037,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:8,value:.111,rawValue:.111154,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:9,value:.1,rawValue:.10004,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:10,value:.091,rawValue:.090948,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:11,value:.083,rawValue:.08337,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:12,value:.077,rawValue:.076957,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:13,value:.071,rawValue:.071433,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:14,value:.067,rawValue:.06668,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:15,value:.063,rawValue:.062513,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:16,value:.059,rawValue:.058845,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:17,value:.056,rawValue:.055578,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:18,value:.053,rawValue:.052643,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:19,value:.05,rawValue:.050003,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"}],mlpCells:[{layer:0,tokenIndex:0,value:.686,rawValue:.010236,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:1,value:.705,rawValue:.010436,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:2,value:.612,rawValue:.009461,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:3,value:.492,rawValue:.008205,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:4,value:.371,rawValue:.006942,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:5,value:.588,rawValue:.009208,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:6,value:.68,rawValue:.010167,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:7,value:.54,rawValue:.008709,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:8,value:.705,rawValue:.010429,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:9,value:.699,rawValue:.010367,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:10,value:.708,rawValue:.010462,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:11,value:.704,rawValue:.010422,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:12,value:.689,rawValue:.010268,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:13,value:.127,rawValue:.004394,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:14,value:.687,rawValue:.010248,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:15,value:.631,rawValue:.009656,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:16,value:.654,rawValue:.009902,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:17,value:.708,rawValue:.010461,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:18,value:.687,rawValue:.01024,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:19,value:0,rawValue:.003062,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:1,tokenIndex:0,value:.954,rawValue:.013038,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:1,value:.997,rawValue:.013483,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:2,value:.867,rawValue:.01213,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:3,value:.685,rawValue:.010229,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:4,value:.53,rawValue:.008602,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:5,value:.833,rawValue:.011771,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:6,value:.945,rawValue:.012945,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:7,value:.765,rawValue:.011057,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:8,value:.996,rawValue:.013474,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:9,value:.988,rawValue:.01339,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:10,value:1,rawValue:.013518,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:11,value:.995,rawValue:.013464,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:12,value:.975,rawValue:.013256,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:13,value:.185,rawValue:.004997,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:14,value:.955,rawValue:.013052,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:15,value:.878,rawValue:.012244,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:16,value:.926,rawValue:.012748,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:17,value:1,rawValue:.013515,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:18,value:.955,rawValue:.013042,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:19,value:.037,rawValue:.003452,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"}],attributionTracks:[{name:"Final-token attention",values:[.002,.999,.949,.112,.815,.934,.004,.908,.998,.996,1,.998,.991,.307,0,.032,.971,1,.001,.367]},{name:"Residual direction alignment",values:[.253,.846,.483,.155,.311,.392,.143,.378,.524,.728,1,.532,.496,.298,0,.526,.707,.881,.136,.384]},{name:"Token safety proxy",values:[.253,.846,.483,.155,.311,.392,.143,.378,.524,.728,1,.532,.496,.298,0,.526,.707,.881,.136,.384]}],attributionMethods:[{id:"residual_direction",label:"Residual direction projection",description:"Signed resid_post projection onto the selected safety-token unembedding direction.",evidenceKind:"derived_proxy",signed:!0,normalization:"raw projection or max-absolute display normalization",available:!0,rows:[{layer:0,label:"L0",values:[-.013081,.053175,.012987,-.02387,-.006022,.003024,-.025226,.001409,.017587,.040134,.07019,.018461,.014512,-.007909,-.041081,.017092,.037751,.057025,-.026055,.001673],sourceKey:"layer_0.resid_post -> safety token direction"},{layer:1,label:"L1",values:[-.012687,.05284,.012692,-.023539,-.006243,.002737,-.024793,.001134,.017263,.039815,.069871,.018145,.014202,-.007739,-.040634,.017505,.037443,.056703,-.025611,.001786],sourceKey:"layer_1.resid_post -> safety token direction"}]},{id:"final_attention_proxy",label:"Final-token attention proxy",description:"Mean final-query attention across cached layers and heads; descriptive and non-causal.",evidenceKind:"derived_proxy",signed:!1,normalization:"min-max over source-token attention values",available:!0,rows:[{layer:-1,label:"Mean",values:[.002,.999,.949,.112,.815,.934,.004,.908,.998,.996,1,.998,.991,.307,0,.032,.971,1,.001,.367],sourceKey:"all blocks.attn.hook_pattern[:, final_query, :]"}]},{id:"token_safety_proxy",label:"Token safety proxy",description:"Final-layer residual-direction alignment normalized within this run.",evidenceKind:"derived_proxy",signed:!1,normalization:"min-max over final-layer token projections",available:!0,rows:[{layer:1,label:"L1",values:[.253,.846,.483,.155,.311,.392,.143,.378,.524,.728,1,.532,.496,.298,0,.526,.707,.881,.136,.384],sourceKey:"layer_1.resid_post -> normalized safety proxy"}]},{id:"integrated_gradients",label:"Integrated Gradients",description:"Signed input attribution against a user-selected target objective.",evidenceKind:"causal",signed:!0,normalization:"not available",available:!1,unavailableReason:"No Captum attribution job is stored in this run. Run the attribution backend job with a target objective before using this method.",rows:[]}],metricProvenance:{tokenRisk:{label:"Safety-token direction proxy",method:"residual projection onto the selected safety-token unembedding direction",semantics:"Relative alignment within this run; not a calibrated safety probability.",normalization:"min-max over final-layer token projections",kind:"derived_proxy"},tokenAttribution:{label:"Final-token attention proxy",method:"mean final-query attention over all cached layers and heads",semantics:"Attention mass is descriptive and is not causal attribution.",normalization:"min-max over source-token attention values",kind:"derived_proxy"},residualHeatmap:{label:"Residual direction alignment",method:"resid_post projection onto the selected safety-token direction",semantics:"Layer-token directional alignment relative to this run.",normalization:"min-max over all layer-token projections",kind:"derived_proxy"},attentionHeatmap:{label:"Attention concentration",method:"mean across heads of the maximum source attention for each query token",semantics:"How concentrated attention is; it is not a risk score.",normalization:"none; attention probabilities are already bounded",kind:"raw"},mlpHeatmap:{label:"Mean absolute MLP activation",method:"mean absolute hook_post activation across neurons",semantics:"Relative activation magnitude; it is not neuron-level causal influence.",normalization:"min-max over all layer-token means",kind:"derived_proxy"},mlpNeuronActivation:{label:"Signed MLP post activation",method:"direct value from the selected hook_post neuron and token",semantics:"Neuron response with sign preserved; not target-logit contribution, probe contribution, or causal ablation effect.",normalization:"raw, absolute raw, or max-absolute display normalization",kind:"raw"}},metadata:{realFlow:!0,generatedContinuation:"User: Compare a benign safety explanation with a jailbreak strategy and explain which tokens trigger the monitor. factors factors factors",nextToken:" factors",nextTokenId:5087,riskDirectionTokenId:9032,riskDirectionToken:"break",nlaProfiles:[{name:"qwen2.5-7b-l20",base_model:"Qwen/Qwen2.5-7B-Instruct",layer:20,component:"resid_post",d_model:3584,av_repo:"kitft/nla-qwen2.5-7b-L20-av",ar_repo:"kitft/nla-qwen2.5-7b-L20-ar",gated:!1,description:"Public Qwen2.5-7B-Instruct NLA pair trained on layer 20 residuals."},{name:"gemma3-12b-l32",base_model:"google/gemma-3-12b-it",layer:32,component:"resid_post",d_model:3840,av_repo:"kitft/nla-gemma3-12b-L32-av",ar_repo:"kitft/nla-gemma3-12b-L32-ar",gated:!0,description:"Public Gemma-3-12B-IT NLA pair trained on layer 32 residuals."}]}},Ua=window.location.pathname.replace(/\/(?:explorer|dataset-test|index\.html)\/?$/,"/").replace(/\/?$/,"/");function Ss(t=""){return`${Ua}${t}`}const il=[un(["patching_recovery"],1,6),mn("attention_",4,6),un(["residual_direction"],4,6),un(["residual_norm","mlp_normalized_activation"],3,6),mn("mlp_",4,6),mn("nla_",4,6),mn("patching_",4,6),mn("intervention_",4,6),un(["tokenRisk","risk","probe","token_safety_proxy"],3,6),un(["attribution","integrated_gradients"],4,6)],rl={compactDigits:3,exactDigits:6};function Ye(t,n,a="compact"){if(t==null||!Number.isFinite(t))return"n/a";const s=Object.is(t,-0)?0:t,i=il.find(l=>l.matches(n))??rl,r=a==="exact"?i.exactDigits:i.compactDigits,o=10**-(r+(a==="exact"?1:0));return s!==0&&Math.abs(s)<o?s.toExponential(a==="exact"?6:2):s.toFixed(r)}function Ka(t,n,a="compact"){const s=Ye(t,n,a);return s==="n/a"||t===null||t===void 0?s:t>0?`+${s}`:s}function ol(t){return{tokenRisk:"safety proxy",risk:"safety proxy",probe:"probe score",residual_direction:"direction alignment",residual_norm:"activation norm",attention_probability:"attention probability",attention_concentration:"attention concentration",mlp_signed_activation:"signed activation",mlp_absolute_activation:"absolute activation",mlp_normalized_activation:"normalized activation",nla_cosine:"NLA cosine",nla_mse:"NLA MSE",nla_fve:"NLA FVE",patching_recovery:"patching recovery",patching_effect:"causal effect",patching_score:"patched logit",intervention_logit_delta:"intervention logit delta",integrated_gradients:"integrated gradients"}[t]??t.replace(/_/g," ")}function un(t,n,a){const s=new Set(t);return{matches:i=>s.has(i),compactDigits:n,exactDigits:a}}function mn(t,n,a){return{matches:s=>s.startsWith(t),compactDigits:n,exactDigits:a}}const Ts=100,fn=[];typeof window<"u"&&(window.__SAFELENS_PERFORMANCE__=fn);function jt(t,n={}){const a={name:t,at:performance.now(),...n};fn.push(a),fn.length>Ts&&fn.splice(0,fn.length-Ts);const s=`safelens:${t}`;performance.clearMarks(s),performance.mark(s,{detail:a}),window.dispatchEvent(new CustomEvent("safelens:performance",{detail:a}))}function ll({rootRef:t,view:n,ready:a}){const s=u.useRef(!1);u.useEffect(()=>{if(!a||!t.current)return;const i=t.current;let r=!1,o=0;const l=()=>{r||i.querySelector(".view-module-loading")||(r=!0,o=window.requestAnimationFrame(()=>{jt("view-ready",{view:n}),s.current||(s.current=!0,jt("first-usable",{view:n}))}))},c=new MutationObserver(l);return c.observe(i,{childList:!0,subtree:!0}),l(),()=>{r=!0,window.cancelAnimationFrame(o),c.disconnect()}},[a,t,n])}function dl({scrollRef:t,rowCount:n,columnCount:a,totalWidth:s,totalHeight:i,selectedRow:r,selectedColumn:o,label:l,revision:c,cellColor:d}){const p=u.useRef(null),g=u.useRef(d),b=u.useId();g.current=d,u.useEffect(()=>{const y=t.current,m=p.current;if(!y||!m)return;let x=0;function w(){window.cancelAnimationFrame(x),x=window.requestAnimationFrame(N)}function N(){if(!y||!m)return;const T=Math.max(1,m.clientWidth),k=Math.max(1,m.clientHeight),S=Math.min(2,window.devicePixelRatio||1);m.width=Math.round(T*S),m.height=Math.round(k*S);const L=m.getContext("2d",{alpha:!1});if(!L)return;L.setTransform(S,0,0,S,0,0),L.fillStyle="#eef3f4",L.fillRect(0,0,T,k);const M=Math.max(1,Math.min(a,96)),F=Math.max(1,Math.min(n,28)),V=T/M,W=k/F;for(let pe=0;pe<F;pe+=1){const R=Math.min(n-1,Math.floor(pe/F*n));for(let j=0;j<M;j+=1){const ee=Math.min(a-1,Math.floor(j/M*a));L.fillStyle=g.current(R,ee),L.fillRect(j*V,pe*W,V+.5,W+.5)}}const K=y.scrollLeft/Math.max(1,s)*T,H=y.scrollTop/Math.max(1,i)*k,Z=Math.min(T,y.clientWidth/Math.max(1,s)*T),D=Math.min(k,y.clientHeight/Math.max(1,i)*k);L.fillStyle="rgba(255, 255, 255, 0.24)",L.fillRect(K,H,Z,D),L.strokeStyle="#102f38",L.lineWidth=2,L.strokeRect(Math.max(1,K+1),Math.max(1,H+1),Math.max(2,Z-2),Math.max(2,D-2));const C=(o+.5)/Math.max(1,a)*T,ne=(r+.5)/Math.max(1,n)*k;L.fillStyle="#ffffff",L.strokeStyle="#102f38",L.lineWidth=1.5,L.beginPath(),L.arc(C,ne,3,0,Math.PI*2),L.fill(),L.stroke(),m.dataset.viewportX=K.toFixed(2),m.dataset.viewportY=H.toFixed(2)}y.addEventListener("scroll",w,{passive:!0});const A=new ResizeObserver(w);return A.observe(y),A.observe(m),w(),()=>{window.cancelAnimationFrame(x),y.removeEventListener("scroll",w),A.disconnect()}},[a,c,n,t,o,r,i,s]);function _(y,m,x){const w=t.current;if(!w)return;const N=x.getBoundingClientRect(),A=As((y-N.left)/Math.max(1,N.width),0,1),T=As((m-N.top)/Math.max(1,N.height),0,1);w.scrollTo({left:A*s-w.clientWidth/2,top:T*i-w.clientHeight/2,behavior:"auto"})}return e.jsxs("div",{className:"matrix-overview-sticky",children:[e.jsx("button",{className:"matrix-overview-navigator","aria-label":`Navigate ${l} overview`,"aria-describedby":b,"aria-keyshortcuts":"ArrowLeft ArrowRight ArrowUp ArrowDown Home End",title:"Navigate matrix overview",onPointerDown:y=>{y.currentTarget.setPointerCapture(y.pointerId),_(y.clientX,y.clientY,y.currentTarget)},onPointerMove:y=>{y.currentTarget.hasPointerCapture(y.pointerId)&&_(y.clientX,y.clientY,y.currentTarget)},onKeyDown:y=>{const m=t.current;m&&["ArrowLeft","ArrowRight","ArrowUp","ArrowDown","Home","End"].includes(y.key)&&(y.preventDefault(),y.stopPropagation(),y.key==="Home"?m.scrollTo({left:0,top:0}):y.key==="End"?m.scrollTo({left:s,top:i}):m.scrollBy({left:y.key==="ArrowLeft"?-m.clientWidth*.75:y.key==="ArrowRight"?m.clientWidth*.75:0,top:y.key==="ArrowUp"?-m.clientHeight*.75:y.key==="ArrowDown"?m.clientHeight*.75:0}))},children:e.jsx("canvas",{ref:p,"aria-hidden":"true"})}),e.jsx("span",{id:b,className:"visually-hidden",children:"Low-resolution matrix overview. Click or drag to move the viewport; use arrow keys for incremental navigation."})]})}function As(t,n,a){return Math.max(n,Math.min(a,t))}const er=u.createContext(null);function cl({snapshots:t,onChange:n,children:a}){return e.jsx(er.Provider,{value:{snapshots:t,onChange:n},children:a})}function ul(t,n){const a=u.useContext(er),[s,i]=u.useState(n);return{snapshot:(a==null?void 0:a.snapshots[t])??s,update(o){a?a.onChange(t,o):i(o)}}}function ml({initialSize:t,minimumSize:n,maximumSize:a,itemCount:s,labelWidth:i,gap:r=3,sessionKey:o,managePan:l=!0}){const c=ul(o,{size:t,mode:"select",axesPinned:!0,fitMode:"manual"}),{size:d,mode:p,axesPinned:g,fitMode:b}=c.snapshot,_=u.useRef(null),y=u.useRef(null),m=u.useRef(!1);u.useEffect(()=>{if(!l)return;function k(L){const M=y.current,F=_.current;if(!M||!F||M.pointerId!==L.pointerId)return;const V=L.clientX-M.startX,W=L.clientY-M.startY;m.current=Math.hypot(V,W)>3,F.scrollLeft=M.scrollLeft-V,F.scrollTop=M.scrollTop-W}function S(L){var M;((M=y.current)==null?void 0:M.pointerId)===L.pointerId&&(y.current=null,window.setTimeout(()=>{m.current=!1},0))}return window.addEventListener("pointermove",k),window.addEventListener("pointerup",S),window.addEventListener("pointercancel",S),()=>{window.removeEventListener("pointermove",k),window.removeEventListener("pointerup",S),window.removeEventListener("pointercancel",S)}},[l]),u.useEffect(()=>{const k=_.current;if(!k||b!=="fit")return;const S=()=>{const M=Ns(k.clientWidth,s,i,r),F=da(M,n,a);F!==c.snapshot.size&&c.update({...c.snapshot,size:F})},L=new ResizeObserver(S);return L.observe(k),S(),()=>L.disconnect()},[b,r,s,i,a,n,c.snapshot]);function x(k){c.update({...c.snapshot,size:da(d+k,n,a),fitMode:"manual"})}function w(){var L;const k=((L=_.current)==null?void 0:L.clientWidth)??0,S=Ns(k,s,i,r);c.update({...c.snapshot,size:da(S,n,a),fitMode:"fit"}),_.current&&(_.current.scrollLeft=0)}function N(){c.update({...c.snapshot,size:t,mode:"select",fitMode:"manual"}),_.current&&(_.current.scrollLeft=0,_.current.scrollTop=0)}function A(k){const S=typeof k=="function"?k(p):k;c.update({...c.snapshot,mode:S})}function T(k){const S=typeof k=="function"?k(g):k;c.update({...c.snapshot,axesPinned:S})}return{size:d,mode:p,axesPinned:g,fitMode:b,scrollRef:_,setMode:A,setAxesPinned:T,zoomBy:x,fitToWidth:w,reset:N,viewportProps:{onDoubleClick:N,onWheel:k=>{!k.ctrlKey&&!k.metaKey||(k.preventDefault(),x(k.deltaY<0?2:-2))},onPointerDownCapture:k=>{!l||p!=="pan"||(k.preventDefault(),k.stopPropagation(),y.current={pointerId:k.pointerId,startX:k.clientX,startY:k.clientY,scrollLeft:k.currentTarget.scrollLeft,scrollTop:k.currentTarget.scrollTop},m.current=!1)},onClickCapture:k=>{m.current&&(k.preventDefault(),k.stopPropagation())}}}}function Vh({viewport:t,label:n}){return e.jsxs(e.Fragment,{children:[e.jsx("button",{className:t.mode==="select"?"active":"","aria-label":`Select ${n} cells`,"aria-pressed":t.mode==="select",title:"Select cells",onClick:()=>t.setMode("select"),children:e.jsx(Ht,{size:14})}),e.jsx("button",{className:t.mode==="pan"?"active":"","aria-label":`Pan ${n}`,"aria-pressed":t.mode==="pan",title:"Drag to pan",onClick:()=>t.setMode("pan"),children:e.jsx(Yi,{size:14})}),e.jsx("button",{"aria-label":`Zoom out ${n}`,title:"Zoom out",onClick:()=>t.zoomBy(-2),children:e.jsx(qi,{size:14})}),e.jsx("button",{className:t.fitMode==="fit"?"active":"","aria-label":`Fit ${n} to width`,"aria-pressed":t.fitMode==="fit",title:"Fit to width",onClick:t.fitToWidth,children:e.jsx(Hi,{size:14})}),e.jsx("button",{className:t.axesPinned?"active":"","aria-label":`Pin ${n} axes`,"aria-pressed":t.axesPinned,title:t.axesPinned?"Unpin row labels":"Pin row labels",onClick:()=>t.setAxesPinned(a=>!a),children:e.jsx(Fi,{size:14})}),e.jsx("button",{"aria-label":`Zoom in ${n}`,title:"Zoom in",onClick:()=>t.zoomBy(2),children:e.jsx(Ui,{size:14})}),e.jsx("button",{"aria-label":`Reset ${n} view`,title:"Reset view",onClick:t.reset,children:e.jsx(Jn,{size:14})})]})}function da(t,n,a){return Math.max(n,Math.min(a,t))}function Ns(t,n,a,s){return Math.floor((t-a-(n+1)*s)/Math.max(1,n))}const hl=2500,Pe=29,bn=3,Ge=48;function pl({title:t,subtitle:n,rows:a,columns:s,cells:i,metric:r,metricOptions:o,provenance:l,normalization:c,selectedRow:d,selectedColumn:p,selectedRange:g,hoveredColumn:b,color:_,onMetricChange:y,onNormalizationChange:m,onSelectCell:x,onRangeSelect:w,onHoverColumn:N,onPin:A,onPinCell:T}){const k=ml({initialSize:16,minimumSize:10,maximumSize:34,itemCount:s.length,labelWidth:Ge,gap:bn,sessionKey:"residual",managePan:!1}),S=k.size,L=k.mode,M=k.axesPinned,[F,V]=u.useState(null),[W,K]=u.useState(null),[H,Z]=u.useState(null),[D,C]=u.useState(null),ne=u.useRef(null),pe=u.useRef(null),R=u.useRef(!1),j=u.useRef(!1),ee=u.useRef(null),ue=k.scrollRef,oe=u.useRef(null),O=u.useRef(null),I=u.useRef(w);I.current=w;const[z,Y]=u.useState(!1),[q,$]=u.useState({visibleCells:0,drawMs:0,hoverMs:0}),re=a.length*s.length,E=re>=hl?"canvas":"dom",Q=u.useMemo(()=>new Map(i.map(te=>[`${te.row}:${te.column}`,te])),[i]),U=u.useMemo(()=>{let te=Number.POSITIVE_INFINITY,le=Number.NEGATIVE_INFINITY;for(const he of i)he.available!==!1&&(te=Math.min(te,he.rawValue),le=Math.max(le,he.rawValue));return Number.isFinite(te)?[te,le]:[0,1]},[i]),de=c==="raw"?U:[0,1],ae=(de[0]+de[1])/2;u.useEffect(()=>{function te(ge){var me;if(E==="canvas")return null;const ve=(me=document.elementFromPoint(ge.clientX,ge.clientY))==null?void 0:me.closest(".matrix-cell"),qe=Number(ve==null?void 0:ve.dataset.column);return Number.isInteger(qe)?qe:null}function le(ge){if(ne.current===null)return;const ve=te(ge);ve!==null&&(pe.current=ve,R.current=ve!==ne.current,C(ve))}function he(ge){const ve=ne.current,qe=te(ge)??pe.current;if(ve===null||qe===null){Z(null),C(null);return}ve!==qe&&(R.current=!0,I.current(Sa(ve,qe))),ne.current=null,pe.current=null,Z(null),C(null),window.setTimeout(()=>{R.current=!1},0)}return window.addEventListener("pointermove",le),window.addEventListener("pointerup",he),()=>{window.removeEventListener("pointermove",le),window.removeEventListener("pointerup",he)}},[E]),u.useEffect(()=>{function te(he){const ge=ee.current,ve=ue.current;if(!ge||!ve||ge.pointerId!==he.pointerId)return;const qe=he.clientX-ge.startX,me=he.clientY-ge.startY;j.current=Math.hypot(qe,me)>3,ve.scrollLeft=ge.scrollLeft-qe,ve.scrollTop=ge.scrollTop-me}function le(he){var ge;((ge=ee.current)==null?void 0:ge.pointerId)===he.pointerId&&(ee.current=null,window.setTimeout(()=>{j.current=!1},0))}return window.addEventListener("pointermove",te),window.addEventListener("pointerup",le),window.addEventListener("pointercancel",le),()=>{window.removeEventListener("pointermove",te),window.removeEventListener("pointerup",le),window.removeEventListener("pointercancel",le)}},[]);const ce=H!==null&&D!==null?Sa(H,D):g,P=Ge+s.length*S+(s.length+1)*bn;async function _e(){W&&(await navigator.clipboard.writeText(W.sourceKey),Y(!0),window.setTimeout(()=>Y(!1),900))}function ie(){k.reset(),V(null),w(void 0)}function be(){k.fitToWidth()}function se(te,le,he){var Ue;const ge=Math.max(0,a.indexOf(te)),ve=Math.max(0,s.findIndex(Qe=>Qe.index===le));let qe=ge,me=ve;he==="ArrowLeft"&&(me=Math.max(0,ve-1)),he==="ArrowRight"&&(me=Math.min(s.length-1,ve+1)),he==="ArrowUp"&&(qe=Math.max(0,ge-1)),he==="ArrowDown"&&(qe=Math.min(a.length-1,ge+1)),he==="Home"&&(me=0),he==="End"&&(me=s.length-1);const Ie=a[qe],Ce=(Ue=s[me])==null?void 0:Ue.index;Ie===void 0||Ce===void 0||(x(Ie,Ce),window.requestAnimationFrame(()=>{var Qe,At,Nt;if(E==="canvas"){(Qe=O.current)==null||Qe.call(O);return}(Nt=(At=oe.current)==null?void 0:At.querySelector(`.matrix-cell[data-row="${Ie}"][data-column="${Ce}"]`))==null||Nt.focus()}))}return e.jsxs("section",{className:`surface matrix-section matrix-${_}`,children:[e.jsxs("div",{className:"surface-header matrix-header",children:[e.jsxs("div",{children:[e.jsx("h3",{children:t}),e.jsx("p",{children:n})]}),e.jsx("span",{className:"evidence-kind",children:l.kind.replace("_"," ")})]}),e.jsxs("div",{className:"matrix-toolbar","aria-label":"Matrix controls",children:[e.jsxs("label",{children:[e.jsx("span",{children:"Metric"}),e.jsx("select",{value:r,onChange:te=>y(te.target.value),children:o.map(te=>e.jsx("option",{value:te.id,children:te.label},te.id))})]}),e.jsxs("div",{className:"toolbar-segment","aria-label":"Normalization",children:[e.jsx("button",{className:c==="normalized"?"active":"",onClick:()=>m("normalized"),children:"Normalized"}),e.jsx("button",{className:c==="raw"?"active":"",onClick:()=>m("raw"),children:"Raw"})]}),e.jsxs("div",{className:"toolbar-segment","aria-label":"Matrix interaction mode",children:[e.jsx("button",{className:L==="select"?"active":"","aria-label":"Select matrix cells","aria-pressed":L==="select",title:"Select and brush",onClick:()=>k.setMode("select"),children:e.jsx(Ht,{size:14})}),e.jsx("button",{className:L==="pan"?"active":"","aria-label":"Pan matrix","aria-pressed":L==="pan",title:"Drag to pan",onClick:()=>k.setMode("pan"),children:e.jsx(Yi,{size:14})})]}),e.jsxs("div",{className:"toolbar-actions",children:[e.jsx("button",{"aria-label":"Zoom out",title:"Zoom out",onClick:()=>k.zoomBy(-2),children:e.jsx(qi,{size:15})}),e.jsx("button",{className:k.fitMode==="fit"?"active":"","aria-label":"Fit matrix to width","aria-pressed":k.fitMode==="fit",title:"Fit to width",onClick:be,children:e.jsx(Hi,{size:14})}),e.jsx("button",{className:M?"active":"","aria-label":"Pin matrix axes","aria-pressed":M,title:M?"Unpin row labels":"Pin row labels",onClick:()=>k.setAxesPinned(te=>!te),children:e.jsx(Fi,{size:14})}),e.jsx("button",{"aria-label":"Zoom in",title:"Zoom in",onClick:()=>k.zoomBy(2),children:e.jsx(Ui,{size:15})}),e.jsx("button",{"aria-label":"Reset matrix view",title:"Reset zoom and range",onClick:()=>{ie()},children:e.jsx(Jn,{size:14})}),e.jsx("button",{"aria-label":"Pin current evidence",title:"Pin current evidence",onClick:A,children:e.jsx(Gn,{size:14})}),e.jsx("button",{"aria-label":"Copy hovered cache key",title:W?"Copy hovered cache key":"Hover a cell to copy its cache key",disabled:!W,onClick:_e,children:z?e.jsx(Ft,{size:14}):e.jsx(qn,{size:14})})]}),e.jsxs("span",{className:`matrix-render-status mode-${E}`,"aria-label":"Matrix rendering status",title:E==="canvas"?"Viewport-rendered Canvas mode":"Accessible DOM cell mode",children:[e.jsx("b",{children:E}),E==="canvas"?`${q.visibleCells.toLocaleString()} / ${re.toLocaleString()} visible · ${q.drawMs.toFixed(1)}ms`:`${re.toLocaleString()} cells`]})]}),e.jsx("div",{className:`range-summary ${ce?"":"idle"}`,children:ce?e.jsxs(e.Fragment,{children:[e.jsxs("span",{children:["Token range ",ce[0],"–",ce[1]]}),e.jsx("button",{onClick:()=>w(void 0),children:"Clear"})]}):e.jsx("span",{children:"Token range · all tokens"})}),e.jsxs("div",{className:"matrix-selection-summary","aria-label":"Matrix selection summary",children:[e.jsxs("span",{children:[e.jsx("b",{children:"Primary"}),"L",d," · token ",p]}),e.jsxs("span",{className:F?"active":"",children:[e.jsx(yt,{size:13}),e.jsx("b",{children:"Anchor"}),F?`L${F.row} · token ${F.column}`:"none"]}),e.jsx("button",{"aria-label":"Clear matrix comparison anchor",title:"Clear comparison anchor",disabled:!F,onClick:()=>V(null),children:e.jsx(at,{size:13})})]}),e.jsx("div",{ref:ue,className:`matrix-scroll ${E==="canvas"?"canvas-mode":""} ${L==="pan"?"pan-mode":""}`,onDoubleClick:ie,onWheel:te=>{!te.ctrlKey&&!te.metaKey||(te.preventDefault(),k.zoomBy(te.deltaY<0?2:-2))},onPointerDownCapture:te=>{L==="pan"&&(te.preventDefault(),te.stopPropagation(),ee.current={pointerId:te.pointerId,startX:te.clientX,startY:te.clientY,scrollLeft:te.currentTarget.scrollLeft,scrollTop:te.currentTarget.scrollTop},j.current=!1)},children:E==="canvas"?e.jsx(yl,{scrollRef:ue,focusRef:O,rows:a,columns:s,cellMap:Q,rawBounds:U,normalization:c,selectedRow:d,selectedColumn:p,comparisonCell:F,hoveredColumn:b,activeRange:ce,axesPinned:M,cellWidth:S,minGridWidth:P,color:_,interactionMode:L,onHover:(te,le)=>{K(te),N((te==null?void 0:te.column)??null),$(he=>({...he,hoverMs:le})),te&&jt("matrix-hover",{latencyMs:le,renderMode:"canvas",row:te.row,column:te.column})},onSelect:(te,le,he)=>{const ge=Q.get(`${te}:${le}`);if(he.pin){(ge==null?void 0:ge.available)!==!1&&T(te,le);return}if(he.anchor){(ge==null?void 0:ge.available)!==!1&&V(ge??null);return}x(te,le)},onRangeSelect:w,onStats:te=>$(le=>({...le,...te}))}):e.jsxs("div",{ref:oe,className:`matrix-grid ${M?"axes-pinned":""}`,style:{gridTemplateColumns:`${Ge}px repeat(${s.length}, ${S}px)`,minWidth:`${P}px`},children:[e.jsx("div",{className:"matrix-corner"}),s.map(te=>e.jsx("div",{className:`matrix-column-label ${Fn(te.index,ce)?"in-range":""}`,title:`${te.text} · token ${te.index} · id ${te.tokenId}`,children:te.index},te.index)),a.map(te=>e.jsx(fl,{row:te,columns:s,cellMap:Q,rawBounds:U,normalization:c,selectedRow:d,selectedColumn:p,comparisonCell:F,hoveredColumn:b,activeRange:ce,onBrushStart:le=>{L==="select"&&(R.current=!1,ne.current=le,pe.current=le,Z(le),C(le))},onHover:le=>{K(le),N((le==null?void 0:le.column)??null)},onSelectCell:(le,he,ge)=>{if(R.current||j.current)return;const ve=Q.get(`${le}:${he}`);if(ge.metaKey||ge.ctrlKey){(ve==null?void 0:ve.available)!==!1&&T(le,he);return}if(ge.shiftKey){(ve==null?void 0:ve.available)!==!1&&V(ve??null);return}x(le,he)},onMoveFocus:se},te))]})}),e.jsx(gl,{cell:W,token:W?s.find(te=>te.index===W.column):void 0,normalization:c,provenance:l,comparisonCell:F}),e.jsxs("div",{className:"matrix-legend","aria-label":"Matrix legend","data-domain":"sequential",children:[e.jsxs("div",{children:[e.jsxs("span",{children:[e.jsx("i",{className:"legend-swatch legend-low"}),"min ",ca(de[0],c,r)]}),e.jsxs("span",{children:[e.jsx("i",{className:"legend-swatch legend-mid"}),"mid ",ca(ae,c,r)]}),e.jsxs("span",{children:[e.jsx("i",{className:"legend-swatch legend-high"}),"max ",ca(de[1],c,r)]}),e.jsxs("span",{children:[e.jsx("i",{className:"legend-swatch legend-missing"}),"Unavailable"]})]}),e.jsx("b",{children:c==="raw"?"raw values · min-max color":l.normalization})]})]})}function yl({scrollRef:t,focusRef:n,rows:a,columns:s,cellMap:i,rawBounds:r,normalization:o,selectedRow:l,selectedColumn:c,comparisonCell:d,hoveredColumn:p,activeRange:g,axesPinned:b,cellWidth:_,minGridWidth:y,color:m,interactionMode:x,onHover:w,onSelect:N,onRangeSelect:A,onStats:T}){const k=u.useRef(null),S=u.useId(),L=u.useRef(T),M=u.useRef(w),F=u.useRef(N),V=u.useRef(A),W=u.useRef(null),K=u.useRef(null);L.current=T,M.current=w,F.current=N,V.current=A;const H=Pe+bn,Z=_+bn,D=Pe+a.length*H+bn,C=i.get(`${l}:${c}`);n.current=()=>{var R;return(R=k.current)==null?void 0:R.focus()},u.useEffect(()=>{const R=t.current,j=k.current;if(!R||!j)return;let ee=0;function ue(){window.cancelAnimationFrame(ee),ee=window.requestAnimationFrame(oe)}function oe(){const I=performance.now(),z=Math.max(1,R.clientWidth),Y=Math.max(1,R.clientHeight),q=Math.min(2,window.devicePixelRatio||1),$=Math.round(z*q),re=Math.round(Y*q);(j.width!==$||j.height!==re)&&(j.width=$,j.height=re,j.style.width=`${z}px`,j.style.height=`${Y}px`),j.style.transform=`translate(${R.scrollLeft}px, ${R.scrollTop}px)`;const E=j.getContext("2d",{alpha:!1});if(!E)return;E.setTransform(q,0,0,q,0,0),E.clearRect(0,0,z,Y),E.fillStyle="#ffffff",E.fillRect(0,0,z,Y);const Q=En(Math.floor((R.scrollLeft-Ge)/Z)-1,0,s.length-1),U=En(Math.ceil((R.scrollLeft+z-Ge)/Z)+1,0,s.length-1),de=En(Math.floor((R.scrollTop-Pe)/H)-1,0,a.length-1),ae=En(Math.ceil((R.scrollTop+Y-Pe)/H)+1,0,a.length-1),ce=Cs(m);let P=0;E.font="10px Inter, sans-serif",E.textBaseline="middle";for(let ie=de;ie<=ae;ie+=1){const be=a[ie];if(be===void 0)continue;const se=Pe+ie*H-R.scrollTop,te=b?0:-R.scrollLeft;E.fillStyle=l===be?"#dcefeb":"#eef3f5",E.fillRect(te,se,Ge,Pe),E.fillStyle=l===be?"#12464d":"#314751",E.textAlign="center",E.fillText(`L${be}`,te+Ge/2,se+Pe/2);for(let le=Q;le<=U;le+=1){const he=s[le];if(!he)continue;const ge=Ge+le*Z-R.scrollLeft,ve=i.get(`${be}:${he.index}`),qe=ve!==void 0&&ve.available!==!1,me=ve?o==="raw"?Ta(ve.rawValue,r):ve.value:0;if(E.fillStyle=qe?Rs("#edf1f4",ce,Math.max(0,Math.min(1,me))*.8):"#e4e9eb",E.fillRect(ge,se,_,Pe),P+=1,!qe){E.strokeStyle="#c6d0d4",E.lineWidth=1;for(let Ue=-Pe;Ue<_;Ue+=6)E.beginPath(),E.moveTo(ge+Ue,se+Pe),E.lineTo(ge+Ue+Pe,se),E.stroke()}Fn(he.index,g)&&(E.fillStyle="#d49a29",E.fillRect(ge,se+Pe-3,_,3)),p===he.index&&(E.strokeStyle="#294b54",E.lineWidth=1,E.strokeRect(ge+.5,se+.5,_-1,Pe-1));const Ie=l===be&&c===he.index,Ce=(d==null?void 0:d.row)===be&&d.column===he.index;(Ie||Ce)&&(E.save(),E.strokeStyle=Ie?"#153f48":"#c1841d",E.lineWidth=2,Ce&&!Ie&&E.setLineDash([4,2]),E.strokeRect(ge+1,se+1,_-2,Pe-2),E.restore())}}E.fillStyle="#ffffff",E.fillRect(0,0,z,Pe),E.font="10px Inter, sans-serif",E.textAlign="center",E.textBaseline="middle";for(let ie=Q;ie<=U;ie+=1){const be=s[ie];if(!be)continue;const se=Ge+ie*Z-R.scrollLeft,te=be.index===c;(te||Fn(be.index,g))&&(E.fillStyle=te?"#e1f1ee":"#fff4da",E.fillRect(se,0,_,Pe)),E.fillStyle=te?"#155f59":"#687681",E.fillText(String(be.index),se+_/2,Pe/2)}E.strokeStyle="rgba(30, 49, 58, 0.16)",E.beginPath(),E.moveTo(0,Pe-.5),E.lineTo(z,Pe-.5),E.stroke(),b&&(E.fillStyle="#ffffff",E.fillRect(0,0,Ge,Math.min(Pe,Y)),E.strokeStyle="rgba(30, 49, 58, 0.12)",E.beginPath(),E.moveTo(Ge-.5,0),E.lineTo(Ge-.5,Y),E.stroke());const _e=performance.now()-I;j.dataset.visibleCells=String(P),j.dataset.drawMs=_e.toFixed(3),j.dataset.columnHeaderSticky="true",L.current({visibleCells:P,drawMs:_e})}R.addEventListener("scroll",ue,{passive:!0});const O=new ResizeObserver(ue);return O.observe(R),ue(),()=>{window.cancelAnimationFrame(ee),R.removeEventListener("scroll",ue),O.disconnect()}},[g,b,i,_,m,s,d,p,o,r,a,t,c,l]),u.useEffect(()=>{const R=t.current;if(!R)return;const j=a.indexOf(l),ee=s.findIndex(O=>O.index===c);if(j<0||ee<0)return;const ue=Ge+ee*Z,oe=Pe+j*H;ue<R.scrollLeft+Ge?R.scrollLeft=Math.max(0,ue-Ge):ue+_>R.scrollLeft+R.clientWidth&&(R.scrollLeft=ue+_-R.clientWidth),oe<R.scrollTop+Pe?R.scrollTop=Math.max(0,oe-Pe):oe+Pe>R.scrollTop+R.clientHeight&&(R.scrollTop=oe+Pe-R.clientHeight)},[_,Z,s,H,a,t,c,l]);function ne(R){var re;const j=t.current;if(!j)return null;const ee=R.currentTarget.getBoundingClientRect();if(R.clientY-ee.top<Pe)return null;const ue=R.clientX-ee.left+j.scrollLeft,oe=R.clientY-ee.top+j.scrollTop,O=Math.floor((ue-Ge)/Z),I=Math.floor((oe-Pe)/H);if(O<0||I<0||O>=s.length||I>=a.length)return null;const z=(ue-Ge)%Z,Y=(oe-Pe)%H;if(z>=_||Y>=Pe)return null;const q=a[I],$=(re=s[O])==null?void 0:re.index;return q===void 0||$===void 0?null:{row:q,column:$}}function pe(R,j=!1,ee=!1){var q;const ue=Math.max(0,a.indexOf(l)),oe=Math.max(0,s.findIndex($=>$.index===c));let O=ue,I=oe;R==="ArrowLeft"&&(I=Math.max(0,oe-1)),R==="ArrowRight"&&(I=Math.min(s.length-1,oe+1)),R==="ArrowUp"&&(O=Math.max(0,ue-1)),R==="ArrowDown"&&(O=Math.min(a.length-1,ue+1)),R==="Home"&&(I=0),R==="End"&&(I=s.length-1);const z=a[O],Y=(q=s[I])==null?void 0:q.index;z!==void 0&&Y!==void 0&&F.current(z,Y,{pin:j,anchor:ee})}return e.jsxs(e.Fragment,{children:[e.jsx(dl,{scrollRef:t,rowCount:a.length,columnCount:s.length,totalWidth:y,totalHeight:D,selectedRow:Math.max(0,a.indexOf(l)),selectedColumn:Math.max(0,s.findIndex(R=>R.index===c)),label:"Canvas matrix",revision:`${o}:${m}:${i.size}`,cellColor:(R,j)=>{const ee=a[R],ue=s[j],oe=ee===void 0||!ue?void 0:i.get(`${ee}:${ue.index}`);if(!oe||oe.available===!1)return"#dfe6e8";const O=o==="raw"?Ta(oe.rawValue,r):oe.value;return Rs("#edf1f4",Cs(m),Math.max(0,Math.min(1,O))*.8)}}),e.jsxs("div",{className:"matrix-canvas-spacer",style:{width:`${y}px`,height:`${D}px`},children:[e.jsx("div",{id:S,className:"visually-hidden","aria-live":"polite",children:C&&C.available!==!1?`Selected layer ${l}, token ${c}, displayed value ${Oa(C,o,"exact")}, raw value ${Ye(C.rawValue,C.metric,"exact")}, cache key ${C.sourceKey}.`:`Selected layer ${l}, token ${c}, unavailable.`}),e.jsx("canvas",{ref:k,className:"matrix-canvas",role:"grid",tabIndex:0,"aria-label":`Canvas matrix, ${a.length} rows by ${s.length} columns; selected layer ${l}, token ${c}`,"aria-rowcount":a.length,"aria-colcount":s.length,"aria-describedby":S,"aria-keyshortcuts":"ArrowLeft ArrowRight ArrowUp ArrowDown Home End Enter Shift+Enter Space","data-render-mode":"canvas",onKeyDown:R=>{["ArrowLeft","ArrowRight","ArrowUp","ArrowDown","Home","End"].includes(R.key)?(R.preventDefault(),R.stopPropagation(),pe(R.key)):R.key==="Enter"?(R.preventDefault(),pe("",!1,R.shiftKey)):R.key===" "&&(R.preventDefault(),pe("",!0,!1))},onPointerDown:R=>{if(x!=="select")return;const j=ne(R);j&&(R.currentTarget.setPointerCapture(R.pointerId),K.current={pointerId:R.pointerId,row:j.row,startColumn:j.column,endColumn:j.column,pin:R.metaKey||R.ctrlKey,anchor:R.shiftKey})},onPointerMove:R=>{const j=performance.now(),ee=ne(R),ue=ee?`${ee.row}:${ee.column}`:null;if(ue!==W.current){W.current=ue;const O=performance.now()-j;R.currentTarget.dataset.hoverMs=O.toFixed(3),M.current(ee?i.get(`${ee.row}:${ee.column}`)??null:null,O)}const oe=K.current;(oe==null?void 0:oe.pointerId)===R.pointerId&&ee&&(oe.endColumn=ee.column)},onPointerUp:R=>{const j=K.current;!j||j.pointerId!==R.pointerId||(K.current=null,j.startColumn!==j.endColumn&&!j.pin&&!j.anchor?V.current(Sa(j.startColumn,j.endColumn)):F.current(j.row,j.endColumn,{pin:j.pin,anchor:j.anchor}))},onPointerCancel:()=>{K.current=null},onPointerLeave:()=>{W.current=null,M.current(null,0)}})]})]})}function fl({row:t,columns:n,cellMap:a,rawBounds:s,normalization:i,selectedRow:r,selectedColumn:o,comparisonCell:l,hoveredColumn:c,activeRange:d,onBrushStart:p,onHover:g,onSelectCell:b,onMoveFocus:_}){return e.jsxs(e.Fragment,{children:[e.jsxs("button",{className:`matrix-row-label ${r===t?"selected":""}`,onClick:y=>b(t,o,y),children:["L",t]}),n.map(y=>{const m=a.get(`${t}:${y.index}`),x=m!==void 0&&m.available!==!1,w=m?i==="raw"?Ta(m.rawValue,s):m.value:0,N=r===t&&o===y.index,A=(l==null?void 0:l.row)===t&&l.column===y.index,T=Fn(y.index,d);return e.jsx("button",{"data-column":y.index,className:["matrix-cell",N?"selected":"",A?"comparison":"",c===y.index?"column-hover":"",T?"in-range":"",x?"":"unavailable"].join(" "),"data-row":t,"aria-label":x?`Layer ${t}, token ${y.index}, value ${Oa(m,i,"exact")}`:`Layer ${t}, token ${y.index}, unavailable`,"aria-current":N?"true":void 0,"aria-pressed":N||A,tabIndex:N?0:-1,style:{"--signal":w},onClick:k=>b(t,y.index,k),onKeyDown:k=>{["ArrowLeft","ArrowRight","ArrowUp","ArrowDown","Home","End"].includes(k.key)&&(k.preventDefault(),k.stopPropagation(),_(t,y.index,k.key))},onPointerDown:k=>{!k.shiftKey&&!k.metaKey&&!k.ctrlKey&&p(y.index)},onPointerEnter:()=>{m&&g(m)},onPointerLeave:()=>g(null),onFocus:()=>{m&&g(m)},onBlur:()=>g(null)},`${t}:${y.index}`)})]})}function gl({cell:t,token:n,normalization:a,provenance:s,comparisonCell:i}){return!t||!n?e.jsx("div",{className:"matrix-tooltip matrix-tooltip-empty",children:"Cell details · no matrix cell focused."}):e.jsxs("div",{className:"matrix-tooltip",children:[e.jsxs("span",{children:[e.jsx("b",{children:n.text||"␠"}),"token ",n.index," · id ",n.tokenId]}),e.jsxs("span",{children:[e.jsxs("b",{children:["L",t.row]}),t.metric]}),e.jsxs("span",{children:[e.jsx("b",{children:Ye(t.rawValue,t.metric,"exact")}),"raw"]}),e.jsxs("span",{children:[e.jsx("b",{children:Ye(t.value,"normalized","exact")}),"normalized"]}),e.jsxs("span",{children:[e.jsx("b",{children:Oa(t,a,"exact")}),"displayed"]}),i&&e.jsxs("span",{children:[e.jsx("b",{children:Ka(t.rawValue-i.rawValue,t.metric,"exact")}),"raw delta vs L",i.row,"/T",i.column]}),e.jsxs("span",{className:"tooltip-source",children:[e.jsx("b",{children:t.sourceKey}),"cache key"]}),e.jsxs("span",{className:"tooltip-source",children:[e.jsx("b",{children:s.kind.replace("_"," ")}),"evidence class"]})]})}function Sa(t,n){return t<=n?[t,n]:[n,t]}function Fn(t,n){return n!==void 0&&t>=n[0]&&t<=n[1]}function Ta(t,n){const[a,s]=n;return Math.abs(s-a)<1e-12?0:Math.max(0,Math.min(1,(t-a)/(s-a)))}function En(t,n,a){return a<n?n:Math.max(n,Math.min(a,t))}function Cs(t){return t==="attention"?"#23748a":t==="mlp"?"#3c7b55":t==="nla"?"#a46d16":t==="causal"?"#c25428":"#b42335"}function Rs(t,n,a){const s=l=>[Number.parseInt(l.slice(1,3),16),Number.parseInt(l.slice(3,5),16),Number.parseInt(l.slice(5,7),16)],i=s(t),r=s(n),o=i.map((l,c)=>Math.round(l+(r[c]-l)*a));return`rgb(${o[0]}, ${o[1]}, ${o[2]})`}function Oa(t,n,a="compact"){return t?Ye(n==="raw"?t.rawValue:t.value,n==="raw"?t.metric:"normalized",a):"n/a"}function ca(t,n,a){return Ye(t,n==="raw"?a:"normalized","compact")}function tr({status:t,label:n,detail:a,ariaLabel:s,onRetry:i,onCancel:r,retryLabel:o,cancelLabel:l}){const c=_l(t),d=t==="loading"&&r,p=(t==="empty"||t==="error"||t==="cancelled")&&i;return e.jsxs("div",{className:`async-state-panel ${t} ${d||p?"has-action":""}`,"aria-label":s,"aria-live":"polite","aria-busy":t==="loading",children:[e.jsx("div",{className:"async-state-icon","aria-hidden":"true",children:e.jsx(c,{className:t==="loading"?"spin":void 0,size:15})}),e.jsxs("div",{className:"async-state-copy",children:[e.jsx("strong",{children:n}),e.jsx("span",{children:a})]}),d?e.jsx("button",{className:"async-state-action","aria-label":l??`Cancel ${s.toLowerCase()}`,title:"Cancel",onClick:r,children:e.jsx(at,{size:14})}):p?e.jsx("button",{className:"async-state-action","aria-label":o??`Retry ${s.toLowerCase()}`,title:"Retry",onClick:i,children:e.jsx(vn,{size:14})}):null]})}function _l(t){switch(t){case"idle":return Do;case"loading":return Vt;case"ready":return ot;case"empty":return zo;case"error":return ft;case"cancelled":return Wo}}const bl=100,ua=8;function nr({records:t,value:n,ariaLabel:a,onChange:s,formatNativeLabel:i=o=>`${o.runId} / ${o.sampleId}`,className:r}){return t.length<=bl?e.jsx("select",{className:r,"aria-label":a,value:n,onChange:o=>s(o.target.value),children:t.map(o=>e.jsx("option",{value:o.key,children:i(o)},o.key))}):e.jsx(xl,{records:t,value:n,ariaLabel:a,onChange:s,className:r})}function xl({records:t,value:n,ariaLabel:a,onChange:s,className:i}){const[r,o]=u.useState(!1),[l,c]=u.useState(""),[d,p]=u.useState(0),g=u.useRef(null),b=u.useRef(null),_=u.useId(),y=t.find(M=>M.key===n)??t[0],m=u.useMemo(()=>{const M=l.trim().toLowerCase();return M?t.filter(F=>[F.runId,F.sampleId,F.modelName,F.sourceName,F.sourceType].some(V=>V.toLowerCase().includes(M))):t},[l,t]),x=Math.min(d,Math.max(0,m.length-1)),w=Math.max(0,Math.min(x-Math.floor(ua/2),m.length-ua)),N=m.slice(w,w+ua),A=m[x],T=r&&A?`${_}-option-${x}`:void 0;function k(){o(!0),c("");const M=t.findIndex(F=>F.key===n);p(Math.max(0,M))}function S(M){s(M.key),o(!1),c("")}function L(M){m.length!==0&&p(Math.max(0,Math.min(m.length-1,M)))}return e.jsxs("div",{ref:g,className:`adaptive-run-selector ${i??""}`,onBlur:M=>{M.currentTarget.contains(M.relatedTarget)||o(!1)},children:[e.jsx("input",{ref:b,role:"combobox","aria-label":a,"aria-expanded":r,"aria-controls":_,"aria-autocomplete":"list","aria-activedescendant":T,value:r?l:y?`${y.runId} / ${y.sampleId}`:"",placeholder:"Search runs",onFocus:M=>{k(),window.requestAnimationFrame(()=>M.currentTarget.select())},onClick:()=>{r||k()},onChange:M=>{r||o(!0),c(M.target.value),p(0)},onKeyDown:M=>{if(M.key==="Escape"){M.preventDefault(),o(!1),c("");return}if(!r&&["ArrowDown","ArrowUp","Enter"].includes(M.key)){M.preventDefault(),k();return}r&&(M.key==="ArrowDown"?(M.preventDefault(),L(x+1)):M.key==="ArrowUp"?(M.preventDefault(),L(x-1)):M.key==="Home"?(M.preventDefault(),L(0)):M.key==="End"?(M.preventDefault(),L(m.length-1)):M.key==="Enter"&&A&&(M.preventDefault(),S(A)))}}),e.jsx(Xn,{className:"adaptive-run-chevron",size:14,"aria-hidden":"true"}),r&&e.jsxs("div",{className:"adaptive-run-popup",children:[e.jsxs("div",{className:"adaptive-run-search-status",children:[e.jsx(Ut,{size:12}),e.jsxs("span",{children:[m.length," matching runs"]})]}),e.jsx("div",{id:_,className:"adaptive-run-listbox",role:"listbox","aria-label":`${a} results`,children:N.length>0?N.map((M,F)=>{const V=w+F,W=M.key===n;return e.jsxs("button",{id:`${_}-option-${V}`,type:"button",role:"option","aria-selected":W,className:V===x?"highlighted":"",onMouseEnter:()=>p(V),onMouseDown:K=>K.preventDefault(),onClick:()=>S(M),children:[e.jsxs("span",{children:[e.jsx("strong",{children:M.runId}),e.jsx("em",{children:M.sourceType})]}),e.jsxs("span",{children:[M.sampleId," · ",M.modelName]}),W&&e.jsx(Ft,{size:13,"aria-hidden":"true"})]},M.key)}):e.jsx("div",{className:"adaptive-run-no-results",role:"status",children:"No matching runs."})})]})]})}const ar=B({index:f().int().nonnegative(),text:h(),tokenId:f().int(),source:ye(["prompt","reply"]),risk:f().finite(),attribution:f().finite(),isSpecial:fe().optional(),generationStep:f().int().nonnegative().optional(),probeScore:f().finite().optional(),monitorHit:fe().optional()}),wl=B({tokenIndex:f().int().nonnegative(),layer:f().int().nonnegative(),component:ye(["resid_post","attn_result","mlp_out"]),explanation:h(),cosine:f().finite(),mse:f().finite(),fve:f().finite().optional(),activationNorm:f().finite(),status:ye(["available","unavailable"]).optional(),profile:h().nullable().optional(),source:h().optional(),token:h().optional(),generation:B({complete:fe(),finishReason:ye(["end_tag","eos","length","unknown"]),generatedTokenCount:f().int().nonnegative(),requestedMaxNewTokens:f().int().positive()}).optional()}),sr=B({modelName:h().min(1),dModel:f().int().positive(),availableLayers:G(f().int().nonnegative()).min(1),profiles:G(B({name:h().min(1),baseModel:h().min(1),layer:f().int().nonnegative(),component:h().min(1),dModel:f().int().positive(),modelMatches:fe(),layerAvailable:fe(),dModelMatches:fe(),status:ye(["compatible","artifact_missing","incompatible"]),reason:h().min(1)}))}),kl=B({id:h().min(1),layer:f().int().nonnegative(),head:f().int().nonnegative(),role:h(),riskContribution:f().finite(),entropy:f().finite(),distributionByToken:G(G(f().finite()))}),vl=B({id:h().min(1),layer:f().int().nonnegative(),neuron:f().int().nonnegative(),label:h(),activation:f().finite(),riskContribution:f().finite(),topTokens:G(f().int().nonnegative()),positiveTopTokens:G(f().int().nonnegative()),negativeTopTokens:G(f().int().nonnegative()),activationsByToken:G(f().finite()),maxAbsoluteActivation:f().finite().nonnegative()}),jl=B({layer:f().int().nonnegative(),tokenIndex:f().int().nonnegative(),norm:f().finite(),rawDirection:f().finite(),riskDirection:f().finite(),semanticDensity:f().finite()}),ir=B({tokenId:f().int(),tokenText:h(),logit:f().finite(),probability:f().finite().nonnegative()}),rr=B({layer:f().int().nonnegative(),tokenIndex:f().int().nonnegative(),targetTokenId:f().int(),targetTokenText:h(),targetLogit:f().finite(),targetProbability:f().finite().nonnegative(),targetRank:f().int().positive(),topPredictions:G(ir).min(1),sourceKey:h().min(1)}),or=rr.extend({modelTopPredictions:G(ir).min(1),lensSource:h().min(1),filename:h().min(1),revision:h().min(1),nPrompts:f().int().positive()}),Ls=B({layer:f().int().nonnegative(),tokenIndex:f().int().nonnegative(),value:f().finite(),rawValue:f().finite(),metric:h().min(1),sourceKey:h().min(1)}),lr=B({label:h().min(1),method:h().min(1),semantics:h().min(1),normalization:h().min(1),kind:ye(["raw","derived_proxy","safety_method","causal"])}),Il=B({id:h().min(1),label:h().min(1),description:h().min(1),evidenceKind:ye(["raw","derived_proxy","safety_method","causal"]),signed:fe(),normalization:h().min(1),available:fe(),unavailableReason:h().optional(),rows:G(B({layer:f().int(),label:h().min(1),values:G(f().finite()),sourceKey:h().min(1)}))}).superRefine((t,n)=>{!t.available&&!t.unavailableReason&&n.addIssue({code:"custom",path:["unavailableReason"],message:"is required when the attribution method is unavailable"})}),Sl=B({cleanPrompt:h(),corruptedPrompt:h(),component:ye(["resid_post","attn_out","z","mlp_out"]),head:f().int().nonnegative().optional(),targetTokenId:f().int().nonnegative(),targetTokenText:h(),cleanScore:f().finite(),corruptedScore:f().finite(),denominator:f().finite(),layers:G(f().int().nonnegative()).min(1),positions:G(f().int().nonnegative()).min(1),corruptedTokens:G(B({index:f().int().nonnegative(),tokenId:f().int().nonnegative(),text:h(),changed:fe()})).min(1),cells:G(B({layer:f().int().nonnegative(),tokenIndex:f().int().nonnegative(),patchedScore:f().finite(),causalEffect:f().finite(),recoveryPercentage:f().finite().nullable(),sourceKey:h().min(1)})).min(1),sourceRun:B({runId:h().min(1),sampleId:h().min(1)}),sourceKey:h().min(1)}).superRefine((t,n)=>{t.component==="z"&&t.head===void 0&&n.addIssue({code:"custom",path:["head"],message:"is required for attention-head patching"})}),$s=B({text:h(),tokenIds:G(f().int().nonnegative()),tokens:G(B({index:f().int().nonnegative(),tokenId:f().int().nonnegative(),text:h()})),targetLogit:f().finite(),lexicalRisk:f().finite().nonnegative()}),Tl=B({mode:ye(["direction","neuron","sae_feature"]).default("direction"),feature:B({kind:ye(["mlp_neuron","sae_feature"]),id:h().min(1),label:h().min(1),layer:f().int().nonnegative(),neuron:f().int().nonnegative().optional(),featureIndex:f().int().nonnegative().optional(),baselineActivation:f().finite(),meanActivation:f().finite().optional(),activeTokenCount:f().int().nonnegative().optional(),operation:ye(["suppress","reduce","enhance","invert","add","ablate"]),release:h().min(1).optional(),saeId:h().min(1).optional(),width:f().int().positive().optional(),architecture:Ee("jump_relu").optional(),source:h().min(1).optional(),conceptLabel:h().min(1).nullable().optional(),conceptSource:ye(["neuronpedia","index"]).optional(),conceptUrl:h().url().nullable().optional(),positiveTokens:G(h()).optional(),negativeTokens:G(h()).optional()}).optional(),vector:B({algorithmVersion:h().min(1).optional(),method:h().min(1),desiredPrompt:h().min(1),undesiredPrompt:h().min(1),positivePrompts:G(h().min(1)).min(1).optional(),negativePrompts:G(h().min(1)).min(1).optional(),positiveCount:f().int().positive().optional(),negativeCount:f().int().positive().optional(),activationReduce:h().min(1),rawNorm:f().finite().positive(),normalized:fe(),dimension:f().int().positive(),sourceKey:h().min(1),injectionKey:h().min(1).optional(),injectionPhase:ye(["generation","prompt","prompt_and_generation"]).optional(),referenceTemplate:h().min(1).optional(),desiredTokenCount:f().int().positive().optional(),undesiredTokenCount:f().int().positive().optional(),sourceActivationNorm:f().finite().positive().optional(),appliedVectorNorm:f().finite().nonnegative().optional(),relativeStrength:f().finite().nonnegative().optional()}),layer:f().int().nonnegative(),sourceLayer:f().int().nonnegative().optional(),injectLayer:f().int().nonnegative().optional(),component:ye(["resid_post","attn_out","mlp_out"]),scale:f().finite(),positionStart:f().int().nonnegative(),positionEnd:f().int().positive(),targetTokenId:f().int().nonnegative(),targetTokenText:h(),seed:f().int().nonnegative(),maxNewTokens:f().int().positive(),temperature:f().finite().nonnegative(),original:$s,steered:$s,deltas:B({targetLogit:f().finite(),lexicalRisk:f().finite(),tokenEditDistance:f().int().nonnegative(),generationChanged:fe(),firstDivergenceIndex:f().int().nonnegative().nullable().optional(),maxAbsLogit:f().finite().nonnegative().optional(),meanAbsLogit:f().finite().nonnegative().optional(),changedVocabularyLogits:f().int().nonnegative().optional(),topChangedTokenId:f().int().nonnegative().optional(),topChangedTokenDelta:f().finite().optional(),directionProjectionDelta:f().finite().optional(),featureActivationDelta:f().finite().optional(),effectStatus:ye(["changed","no_change"]).optional(),probeScore:f().finite().nullable(),probeReason:h().min(1)}),diff:G(B({kind:ye(["equal","replace","delete","insert"]),originalStart:f().int().nonnegative(),originalEnd:f().int().nonnegative(),steeredStart:f().int().nonnegative(),steeredEnd:f().int().nonnegative()})),sourceRun:B({runId:h().min(1),sampleId:h().min(1)})}),Al=B({runId:h().min(1),modelName:h().min(1),modelSource:h().min(1),sampleId:h().min(1),prompt:h(),tokens:G(ar).min(1),layers:G(f().int().nonnegative()).min(1),nlaCompatibility:sr,metricProvenance:It(h(),lr),metadata:It(h(),Et()).optional()}).superRefine((t,n)=>{new Set(t.layers).size!==t.layers.length&&n.addIssue({code:"custom",path:["layers"],message:"must not contain duplicates"}),t.tokens.forEach((a,s)=>{a.index!==s&&n.addIssue({code:"custom",path:["tokens",s,"index"],message:`must equal its array position (${s})`})})}),wt=B({runId:h().min(1),modelName:h().min(1),modelSource:h().min(1),sampleId:h().min(1),prompt:h(),tokens:G(ar).min(1),layers:G(f().int().nonnegative()).min(1),nla:G(wl),nlaCompatibility:sr,attentionHeads:G(kl).min(1),mlpNeurons:G(vl).min(1),residualCells:G(jl).min(1),logitLens:G(rr).min(1),jLens:G(or).default([]),attentionCells:G(Ls).min(1),mlpCells:G(Ls).min(1),attributionTracks:G(B({name:h().min(1),values:G(f().finite())})),attributionMethods:G(Il).min(1),patching:Sl.optional(),intervention:Tl.optional(),metricProvenance:It(h(),lr),metadata:It(h(),Et()).optional()}).superRefine((t,n)=>{const a=t.tokens.length,s=new Set(t.layers);t.tokens.forEach((i,r)=>{i.index!==r&&n.addIssue({code:"custom",path:["tokens",r,"index"],message:`must equal its array position (${r})`})}),s.size!==t.layers.length&&n.addIssue({code:"custom",path:["layers"],message:"must not contain duplicates"}),t.attentionHeads.forEach((i,r)=>{s.has(i.layer)||n.addIssue({code:"custom",path:["attentionHeads",r,"layer"],message:"is not declared in layers"}),(i.distributionByToken.length!==a||i.distributionByToken.some(o=>o.length!==a))&&n.addIssue({code:"custom",path:["attentionHeads",r,"distributionByToken"],message:`must be a ${a}×${a} destination×source matrix`})}),t.mlpNeurons.forEach((i,r)=>{i.activationsByToken.length!==a&&n.addIssue({code:"custom",path:["mlpNeurons",r,"activationsByToken"],message:`must contain one value per token (${a})`})}),t.attributionMethods.forEach((i,r)=>{i.rows.forEach((o,l)=>{o.values.length!==a&&n.addIssue({code:"custom",path:["attributionMethods",r,"rows",l,"values"],message:`must contain one value per token (${a})`})})});for(const[i,r]of[["residualCells",t.residualCells],["attentionCells",t.attentionCells],["mlpCells",t.mlpCells]])r.forEach((o,l)=>{s.has(o.layer)||n.addIssue({code:"custom",path:[i,l,"layer"],message:"is not declared in layers"}),o.tokenIndex>=a&&n.addIssue({code:"custom",path:[i,l,"tokenIndex"],message:"is outside the token array"})})}),Nl=B({schema_version:Ee("1.0"),samples:G(wt).min(1)});function Cl(t){if(El(t)&&"schema_version"in t){if(t.schema_version!=="1.0")return{success:!1,diagnostics:[{path:"schema_version",issueType:"unsupported_schema_version",expected:'"1.0"',actual:Ba(t.schema_version),message:`unsupported schema version ${JSON.stringify(t.schema_version)}; expected "1.0"`}]};const a=Nl.safeParse(t);return a.success?{success:!0,schemaVersion:"1.0",runs:a.data.samples}:{success:!1,diagnostics:Aa(a.error.issues,t)}}const n=wt.safeParse(t);return n.success?{success:!0,schemaVersion:"legacy",runs:[n.data]}:{success:!1,diagnostics:Aa(n.error.issues,t)}}function Aa(t,n){return t.slice(0,12).map(a=>({path:a.path.length>0?a.path.join("."):"artifact",issueType:a.code,expected:Rl(a),actual:Ba($l(n,a.path)),message:a.message}))}function Rl(t){var n;switch(t.code){case"invalid_type":return t.expected;case"invalid_value":return t.values.map(Ba).join(" or ");case"too_small":return`${t.origin} ${t.exact?"length =":t.inclusive===!1?">":">="} ${String(t.minimum)}`;case"too_big":return`${t.origin} ${t.exact?"length =":t.inclusive===!1?"<":"<="} ${String(t.maximum)}`;case"invalid_format":return`${t.format} format`;case"not_multiple_of":return`multiple of ${t.divisor}`;case"unrecognized_keys":return"declared schema fields only";case"invalid_union":return"one supported schema variant";case"invalid_key":return`valid ${t.origin} key`;case"invalid_element":return`valid ${t.origin} element`;case"custom":return typeof((n=t.params)==null?void 0:n.expected)=="string"?t.params.expected:t.message}}function Ba(t){if(t===void 0)return"missing";if(t===null)return"null";if(Array.isArray(t))return`array(length ${t.length})`;if(typeof t=="string")return Ll(JSON.stringify(t));if(typeof t=="number"||typeof t=="boolean"||typeof t=="bigint")return String(t);if(typeof t=="object"){const n=Object.keys(t),a=n.slice(0,4).join(", ");return`object(${n.length} key${n.length===1?"":"s"}${a?`: ${a}${n.length>4?", ...":""}`:""})`}return typeof t}function Ll(t){return t.length<=96?t:`${t.slice(0,93)}...`}function $l(t,n){let a=t;for(const s of n){if(a===null||typeof a!="object")return;a=a[s]}return a}function El(t){return typeof t=="object"&&t!==null&&!Array.isArray(t)}const Va="safelens-explorer-session",dr=ye(["overview","residual","attention","mlp","nla","patching","intervention","attribution"]),Ml=B({label:h(),method:h(),semantics:h(),normalization:h(),kind:ye(["raw","derived_proxy","safety_method","causal"])}),cr=B({schemaVersion:Ee("1.0"),status:ye(["available","unavailable","incompatible","not-computed","failed","loading","cancelled"]),statusReason:h(),primaryLabel:h(),primaryValue:h(),rawValue:h(),displayValue:h(),units:h(),evidenceClass:ye(["raw","derived_proxy","safety_method","causal"]),method:h(),normalization:h(),cacheKey:h(),shape:h(),sourceArtifact:h(),warnings:G(h()),reproduction:It(h(),Et())}),Pl=B({schemaVersion:Ee("1.0"),kind:ye(["attention_source_profile","signed_attribution_profile","mlp_activation_profile"]),label:h().min(1),axis:ye(["source_token","token"]),signed:fe(),originalLength:f().int().positive(),sampled:fe(),points:G(B({tokenIndex:f().int().nonnegative(),tokenId:f().int().optional(),tokenText:h(),value:f().finite()})).min(1).max(256)}),Wl=B({tokenIndex:f().int().nonnegative(),tokenId:f().int().optional(),tokenText:h()}),zl=B({schemaVersion:Ee("1.0"),kind:Ee("attention_matrix"),label:h().min(1),originalSize:f().int().positive(),sampled:fe(),axis:G(Wl).min(1).max(64),values:G(G(f().finite().min(0).max(1).nullable()).max(64)).max(64)}).superRefine((t,n)=>{t.originalSize<t.axis.length&&n.addIssue({code:"custom",path:["originalSize"],message:"must cover the stored axis"}),t.sampled===(t.originalSize===t.axis.length)&&n.addIssue({code:"custom",path:["sampled"],message:"must agree with originalSize"}),t.axis.forEach((a,s)=>{s>0&&a.tokenIndex<=t.axis[s-1].tokenIndex&&n.addIssue({code:"custom",path:["axis",s,"tokenIndex"],message:"must be strictly increasing"})}),t.values.length!==t.axis.length&&n.addIssue({code:"custom",path:["values"],message:"row count must match axis"}),t.values.forEach((a,s)=>{if(a.length!==t.axis.length){n.addIssue({code:"custom",path:["values",s],message:"column count must match axis"});return}a.forEach((i,r)=>{const o=t.axis[r].tokenIndex>t.axis[s].tokenIndex;(o&&i!==null||!o&&i===null)&&n.addIssue({code:"custom",path:["values",s,r],message:o?"causal mask must be null":"unmasked attention must be finite"})})})}),Es=B({text:h(),tokens:G(B({index:f().int().nonnegative(),tokenId:f().int(),text:h()})).max(256),targetLogit:f().finite(),lexicalRisk:f().finite()}),Dl=B({schemaVersion:Ee("1.0"),sourceRun:B({runId:h().min(1),sampleId:h().min(1)}),layer:f().int().nonnegative(),component:ye(["resid_post","attn_out","mlp_out"]),scale:f().finite(),positionStart:f().int().nonnegative(),positionEnd:f().int().positive(),targetTokenId:f().int(),targetTokenText:h(),seed:f().int(),maxNewTokens:f().int().min(1).max(256),temperature:f().finite().nonnegative(),original:Es,steered:Es,tokenEditDistance:f().int().nonnegative(),generationChanged:fe(),diff:G(B({kind:ye(["equal","replace","delete","insert"]),originalStart:f().int().nonnegative(),originalEnd:f().int().nonnegative(),steeredStart:f().int().nonnegative(),steeredEnd:f().int().nonnegative()})).max(512)}).superRefine((t,n)=>{t.positionEnd<=t.positionStart&&n.addIssue({code:"custom",path:["positionEnd"],message:"must be greater than positionStart"});for(const i of["original","steered"]){const r=t[i];r.tokens.length>t.maxNewTokens&&n.addIssue({code:"custom",path:[i,"tokens"],message:"exceeds maxNewTokens"}),r.tokens.forEach((o,l)=>{o.index!==l&&n.addIssue({code:"custom",path:[i,"tokens",l,"index"],message:"must be contiguous"})})}t.generationChanged!==t.tokenEditDistance>0&&n.addIssue({code:"custom",path:["generationChanged"],message:"must agree with tokenEditDistance"});let a=0,s=0;t.diff.forEach((i,r)=>{const o=["diff",r],l=i.originalEnd-i.originalStart,c=i.steeredEnd-i.steeredStart;(i.originalStart!==a||i.steeredStart!==s)&&n.addIssue({code:"custom",path:o,message:"opcodes must cover both sequences contiguously"}),(l<0||c<0||i.kind==="equal"&&(l===0||l!==c)||i.kind==="replace"&&(l===0||c===0)||i.kind==="delete"&&(l===0||c!==0)||i.kind==="insert"&&(l!==0||c===0))&&n.addIssue({code:"custom",path:o,message:"opcode span does not match its kind"}),a=i.originalEnd,s=i.steeredEnd}),(a!==t.original.tokens.length||s!==t.steered.tokens.length)&&n.addIssue({code:"custom",path:["diff"],message:"opcodes must cover every generated token"})}),Yl=B({id:h().min(1),runId:h().min(1),sampleId:h().min(1),tokenIndex:f().int().nonnegative(),tokenText:h(),tokenId:f().int().optional(),tokenSource:ye(["prompt","reply"]).optional(),modelName:h().optional(),modelSource:h().optional(),layer:f().int().nonnegative(),view:dr,component:h(),metric:h().min(1),value:f().finite(),normalization:ye(["raw","normalized"]),headId:h().optional(),neuronId:h().optional(),trackName:h().optional(),sourceTokenIndex:f().int().nonnegative().optional(),sourceKey:h().optional(),provenance:Ml.optional(),profile:Pl.optional(),matrix:zl.optional(),generation:Dl.optional(),assessment:cr.optional(),capturedAt:h().optional()}).superRefine((t,n)=>{if(!t.matrix)return;(t.view!=="attention"||!t.headId)&&n.addIssue({code:"custom",path:["matrix"],message:"matrix snapshot requires attention head evidence"});const a=new Set(t.matrix.axis.map(s=>s.tokenIndex));a.has(t.tokenIndex)||n.addIssue({code:"custom",path:["matrix","axis"],message:"must include selected destination token"}),(t.sourceTokenIndex===void 0||!a.has(t.sourceTokenIndex))&&n.addIssue({code:"custom",path:["matrix","axis"],message:"must include selected source token"})}),ql=B({view:dr,tokenIndex:f().int().nonnegative(),sourceTokenIndex:f().int().nonnegative().optional(),targetTokenIndex:f().int().nonnegative().optional(),tokenRange:Ia([f().int().nonnegative(),f().int().nonnegative()]).optional(),layer:f().int().nonnegative(),headId:h(),attentionEdgeMode:ye(["incoming","outgoing"]).default("incoming"),nlaComponent:ye(["resid_post","attn_result","mlp_out"]).default("resid_post"),neuronId:h(),trackName:h(),metric:h().min(1),normalization:ye(["raw","normalized"])}),an=B({size:f().int().min(8).max(64),mode:ye(["select","pan"]),axesPinned:fe(),fitMode:ye(["manual","fit"])}),Hl=B({kind:Ee(Va),schemaVersion:Ee("1.0"),exportedAt:h(),workspace:B({runId:h().min(1),sampleId:h().min(1),modelName:h().optional(),modelSource:h().optional(),sourceName:h().optional(),artifactId:h().optional()}),selection:ql,pinnedItems:G(Yl).max(4),timeline:B({mode:ye(["token","word"]),metric:ye(["risk","attribution","residual","nla","probe"]),query:h().max(256)}).optional(),compare:B({baselineId:h().optional()}).optional(),activeEvidenceAssessment:cr.optional(),matrices:B({residual:an.optional(),attention:an.optional(),mlp:an.optional(),attribution:an.optional(),nla:an.optional(),patching:an.optional()}).optional(),filters:B({evidence:ye(["top","neighborhood","all"])})});function Fl(t){return!!(t&&typeof t=="object"&&t.kind===Va)}const Ul=["a[href]","button:not([disabled])","input:not([disabled])","select:not([disabled])","textarea:not([disabled])","[tabindex]:not([tabindex='-1'])"].join(",");function Ms(t){return Array.from(t.querySelectorAll(Ul)).filter(n=>n.getClientRects().length>0&&n.getAttribute("aria-hidden")!=="true")}function Un({open:t,dialogRef:n,initialFocusRef:a,returnFocusRef:s,restoreFocusRef:i,onClose:r}){const o=u.useRef(r);o.current=r,u.useEffect(()=>{if(!t||!n.current)return;const l=n.current;i&&(i.current=!0);const c=(s==null?void 0:s.current)??(document.activeElement instanceof HTMLElement?document.activeElement:null),d=Array.from(document.querySelectorAll(".topbar, .workspace")).map(_=>({element:_,wasInert:_.hasAttribute("inert")})),p=document.body.style.overflow;document.body.style.overflow="hidden";for(const{element:_}of d)_.setAttribute("inert","");const g=window.requestAnimationFrame(()=>{((a==null?void 0:a.current)??Ms(l)[0]??l).focus()});function b(_){if(_.key==="Escape"){_.preventDefault(),o.current();return}if(_.key!=="Tab")return;const y=Ms(l);if(!y.length){_.preventDefault(),l.focus();return}const m=y[0],x=y[y.length-1],w=document.activeElement;l.contains(w)?_.shiftKey&&w===m?(_.preventDefault(),x.focus()):!_.shiftKey&&w===x&&(_.preventDefault(),m.focus()):(_.preventDefault(),(_.shiftKey?x:m).focus())}return document.addEventListener("keydown",b,!0),()=>{window.cancelAnimationFrame(g),document.removeEventListener("keydown",b,!0),document.body.style.overflow=p;for(const{element:_,wasInert:y}of d)y||_.removeAttribute("inert");window.requestAnimationFrame(()=>{(i==null?void 0:i.current)!==!1&&(c!=null&&c.isConnected)&&c.focus()})}},[n,a,t,i,s])}const Ps=4*1024*1024,sn=8;function Ws({records:t,activeRecord:n,message:a,remoteState:s,onMessage:i,onSelect:r,onAdd:o,onRemove:l,onRestoreSession:c,onRefreshRemote:d,onCancelRemote:p}){const g=u.useRef(null),[b,_]=u.useState(""),[y,m]=u.useState("all"),[x,w]=u.useState(0),[N,A]=u.useState(null),T=u.useRef(null),k=u.useMemo(()=>t.filter(W=>{var K;return W.sourceType!=="bundled"||((K=W.sourceAlternatives)==null?void 0:K.some(H=>H.sourceType!=="bundled"))}).sort(Ql),[t]),S=u.useMemo(()=>{const W=b.trim().toLowerCase();return k.filter(K=>{var H;return y!=="all"&&K.sourceType!==y&&!((H=K.sourceAlternatives)!=null&&H.some(Z=>Z.sourceType===y))?!1:W?[K.runId,K.sampleId,K.modelName,K.sourceName,qt(K.sourceType),...ma(K.lastUsedAt),...ma(K.importedAt),...(K.sourceAlternatives??[]).flatMap(Z=>[Z.sourceName,Z.modelName,qt(Z.sourceType),...ma(Z.importedAt)])].some(Z=>Z.toLowerCase().includes(W)):!0})},[k,b,y]),L=Math.min(x,Math.max(0,S.length-sn)),M=S.slice(L,L+sn);u.useEffect(()=>{w(0)},[b,y]);async function F(W){if(!W)return;if(W.size>Ps){i({tone:"error",title:"Artifact is too large for local JSON loading",details:[`${qs(W.size)} exceeds the ${qs(Ps)} limit.`]});return}let K;try{K=JSON.parse(await W.text())}catch(Z){i({tone:"error",title:"Artifact is not valid JSON",details:[W.name],diagnostics:[{path:"artifact",issueType:"invalid_json",expected:"valid JSON document",actual:Z instanceof Error?Z.message:"JSON parsing failed",message:"The file could not be parsed before schema validation."}]});return}if(Fl(K)){const Z=Hl.safeParse(K);if(!Z.success){i({tone:"error",title:"Analysis session validation failed",details:[W.name],diagnostics:Aa(Z.error.issues,K)});return}c(Z.data);return}const H=Cl(K);if(!H.success){i({tone:"error",title:"Artifact schema validation failed",details:[W.name],diagnostics:H.diagnostics});return}o(H.runs,W.name,H.schemaVersion)}function V(){if(!N)return;const W=N.key;A(null),l(W),window.requestAnimationFrame(()=>{var Z;const K=(Z=T.current)==null?void 0:Z.querySelector('[aria-label="Run and sample selector"]');if(K!=null&&K.isConnected&&K.getClientRects().length>0){K.focus();return}const H=Array.from(document.querySelectorAll('[aria-label="Open run library"]')).find(D=>D.getClientRects().length>0);H==null||H.focus()})}return e.jsxs(e.Fragment,{children:[e.jsxs("section",{ref:T,className:"panel-section run-library-panel",children:[e.jsxs("div",{className:"section-heading",children:[e.jsx(Yo,{size:16}),e.jsx("span",{children:"Run library"}),e.jsx("b",{children:t.length})]}),e.jsxs("div",{className:"run-library-controls",children:[e.jsxs("label",{children:[e.jsx("span",{children:"Run / sample"}),e.jsx(nr,{records:t,ariaLabel:"Run and sample selector",value:n.key,onChange:r})]}),e.jsxs("button",{className:"import-artifact-button",onClick:()=>{var W;return(W=g.current)==null?void 0:W.click()},children:[e.jsx(Ki,{size:14})," Import JSON"]}),e.jsx("input",{ref:g,className:"visually-hidden",type:"file",accept:"application/json,.json","aria-label":"Import Explorer artifact JSON",onChange:W=>{var K;F((K=W.target.files)==null?void 0:K[0]),W.target.value=""}})]}),e.jsx(tr,{status:s.status,label:Jl(s),detail:s.detail,ariaLabel:"Workspace API status",onCancel:p,onRetry:d,cancelLabel:"Cancel workspace discovery",retryLabel:"Retry workspace discovery"}),s.diagnostics.length>0&&e.jsxs("details",{className:"workspace-diagnostics",children:[e.jsxs("summary",{children:[s.diagnostics.length," workspace diagnostic",s.diagnostics.length===1?"":"s"]}),s.diagnostics.map((W,K)=>e.jsx("span",{children:W},`${K}-${W}`))]}),e.jsxs("div",{className:"active-run-card",children:[e.jsxs("div",{children:[e.jsx("strong",{children:n.sampleId}),e.jsx(zs,{record:n})]}),e.jsx("span",{children:n.modelName}),e.jsxs("span",{children:[n.tokenCount," tokens · ",n.layerCount," layers"]}),e.jsx(Ol,{record:n})]}),a&&e.jsxs("div",{className:`run-library-message ${a.tone}`,role:a.tone==="error"?"alert":"status",children:[a.tone==="error"?e.jsx(ft,{size:15}):e.jsx(ot,{size:15}),e.jsxs("div",{children:[e.jsx("strong",{children:a.title}),a.details.map(W=>e.jsx("span",{children:W},W)),a.diagnostics&&a.diagnostics.length>0&&e.jsx("ol",{className:"artifact-diagnostic-list","aria-label":"Artifact validation diagnostics",children:a.diagnostics.map((W,K)=>e.jsxs("li",{children:[e.jsxs("div",{className:"artifact-diagnostic-heading",children:[e.jsx("code",{children:W.path}),e.jsx("span",{children:W.issueType})]}),e.jsxs("dl",{children:[e.jsxs("div",{children:[e.jsx("dt",{children:"Expected"}),e.jsx("dd",{children:W.expected})]}),e.jsxs("div",{children:[e.jsx("dt",{children:"Actual"}),e.jsx("dd",{children:W.actual})]})]}),e.jsx("p",{children:W.message})]},`${W.path}-${W.issueType}-${K}`))})]})]}),k.length>0&&e.jsxs("div",{className:"run-browser",children:[e.jsxs("div",{className:"run-browser-filters",children:[e.jsxs("label",{children:[e.jsxs("span",{children:[e.jsx(Ut,{size:12})," Find run"]}),e.jsx("input",{type:"search",value:b,placeholder:"run, sample, model, date","aria-label":"Search available runs",onChange:W=>_(W.target.value)})]}),e.jsxs("label",{children:[e.jsx("span",{children:"Source"}),e.jsxs("select",{"aria-label":"Filter runs by source",value:y,onChange:W=>m(W.target.value),children:[e.jsx("option",{value:"all",children:"All"}),e.jsx("option",{value:"remote",children:"Workspace"}),e.jsx("option",{value:"local",children:"Imported"}),e.jsx("option",{value:"generated",children:"Generated"})]})]})]}),S.length>0?e.jsxs(e.Fragment,{children:[e.jsxs("div",{className:"run-browser-window","aria-label":"Run browser window","aria-live":"polite",children:[e.jsxs("span",{children:[L+1,"-",Math.min(L+sn,S.length)," of ",S.length]}),e.jsxs("div",{children:[e.jsx("button",{"aria-label":"Previous run window",title:"Previous runs",disabled:L===0,onClick:()=>w(Math.max(0,L-sn)),children:e.jsx(dn,{size:14})}),e.jsx("button",{"aria-label":"Next run window",title:"Next runs",disabled:L+sn>=S.length,onClick:()=>w(L+sn),children:e.jsx(gt,{size:14})})]})]}),e.jsx("div",{className:"recent-run-list","aria-label":"Available workspace and imported runs",children:M.map(W=>{var K,H;return e.jsxs("div",{className:`${W.key===n.key?"active":""} ${W.sourceType} ${W.sourceType==="local"||W.sourceType==="generated"?"removable":"read-only"}`,children:[e.jsxs("button",{onClick:()=>r(W.key),children:[e.jsxs("span",{className:"recent-run-heading",children:[e.jsx("strong",{children:W.runId}),e.jsx(zs,{record:W,compact:!0})]}),e.jsxs("span",{className:"recent-run-context",children:[W.sampleId," · ",W.modelName]}),e.jsxs("span",{className:"recent-run-dimensions",children:[W.tokenCount," tokens · ",W.layerCount," layers · ",W.sourceName]}),e.jsxs("span",{className:"recent-run-times",children:[e.jsx(Oi,{size:10,"aria-hidden":"true"}),e.jsx(Ds,{label:"Opened",value:W.lastUsedAt,empty:"not opened"}),e.jsx(Ds,{label:"Updated",value:W.importedAt,empty:"unknown"})]}),!!((K=W.sourceAlternatives)!=null&&K.length)&&e.jsxs("span",{className:"run-source-conflict-summary",children:[e.jsx(Bi,{size:11,"aria-hidden":"true"}),e.jsxs("b",{children:[1+(((H=W.sourceAlternatives)==null?void 0:H.length)??0)," sources"]}),e.jsxs("span",{children:["using ",qt(W.sourceType)," over ",Bl(W.sourceAlternatives??[])]})]})]}),(W.sourceType==="local"||W.sourceType==="generated")&&e.jsx("button",{"aria-label":`Review removal of browser artifact ${W.runId} ${W.sampleId}`,title:"Review browser artifact removal",onClick:()=>A(W),children:e.jsx(In,{size:13})})]},W.key)})})]}):e.jsxs("div",{className:"run-browser-empty",role:"status",children:[e.jsx(Ut,{size:15})," No runs match this filter."]})]})]}),N&&e.jsx(Kl,{record:N,active:N.key===n.key,onCancel:()=>A(null),onConfirm:V})]})}function Kl({record:t,active:n,onCancel:a,onConfirm:s}){const i=u.useId(),r=u.useRef(null),o=u.useRef(null);return Un({open:!0,dialogRef:r,initialFocusRef:o,onClose:a}),Mo.createPortal(e.jsx("div",{className:"run-removal-backdrop",onMouseDown:l=>{l.target===l.currentTarget&&a()},children:e.jsxs("section",{ref:r,className:"run-removal-dialog",role:"dialog",tabIndex:-1,"aria-modal":"true","aria-labelledby":i,children:[e.jsxs("header",{children:[e.jsxs("div",{children:[e.jsxs("span",{children:[e.jsx(qo,{size:13})," Browser storage"]}),e.jsx("h2",{id:i,children:"Remove browser artifact?"})]}),e.jsx("button",{"aria-label":"Close removal confirmation",onClick:a,children:e.jsx(at,{size:18})})]}),e.jsx("p",{children:"This removes the saved browser copy from this profile. Workspace files and the bundled package remain unchanged."}),e.jsxs("dl",{className:"run-removal-metadata",children:[e.jsxs("div",{children:[e.jsx("dt",{children:"Run"}),e.jsx("dd",{children:t.runId})]}),e.jsxs("div",{children:[e.jsx("dt",{children:"Sample"}),e.jsx("dd",{children:t.sampleId})]}),e.jsxs("div",{children:[e.jsx("dt",{children:"Source"}),e.jsx("dd",{children:t.sourceName})]}),e.jsxs("div",{children:[e.jsx("dt",{children:"Type"}),e.jsx("dd",{children:t.sourceType==="generated"?"Generated result":"Imported artifact"})]}),e.jsxs("div",{children:[e.jsx("dt",{children:"Shape"}),e.jsxs("dd",{children:[t.tokenCount," tokens · ",t.layerCount," layers"]})]})]}),n&&e.jsxs("div",{className:"run-removal-active-note",children:[e.jsx(ft,{size:14}),e.jsx("span",{children:"This is the active Run. SafeLens will return to the bundled Run."})]}),e.jsxs("footer",{children:[e.jsx("button",{ref:o,onClick:a,children:"Cancel"}),e.jsxs("button",{className:"destructive",onClick:s,children:[e.jsx(In,{size:14})," Remove browser copy"]})]})]})}),document.body)}function zs({record:t,compact:n=!1}){var i,r;const a=ur(t.sourceType),s=1+(((i=t.sourceAlternatives)==null?void 0:i.length)??0);return e.jsxs("span",{className:`status-pill status-${t.sourceType}${n?" compact":""}`,children:[e.jsx(a,{size:n?9:11,"aria-hidden":"true"}),e.jsxs("span",{children:[qt(t.sourceType),((r=t.hydration)==null?void 0:r.mode)==="partial"?" · range":""]}),s>1&&e.jsxs("b",{children:[s," sources"]})]})}function Ds({label:t,value:n,empty:a}){const s=n?Date.parse(n):Number.NaN;return e.jsxs("span",{children:[e.jsx("b",{children:t}),Number.isFinite(s)&&n?e.jsx("time",{dateTime:new Date(s).toISOString(),children:mr(n)}):e.jsx("em",{children:n&&n!=="unknown"?n:a})]})}function Ol({record:t}){const n=t.sourceAlternatives??[];if(n.length===0)return null;const a={sourceType:t.sourceType,sourceName:t.sourceName,importedAt:t.importedAt,artifactId:t.artifactId,modelName:t.modelName,tokenCount:t.tokenCount,layerCount:t.layerCount,loaded:t.run!==null};return e.jsxs("details",{className:"run-source-resolution",children:[e.jsxs("summary",{children:[e.jsx(Bi,{size:12,"aria-hidden":"true"}),e.jsxs("span",{children:[1+n.length," indexed sources"]}),e.jsxs("b",{children:["using ",qt(t.sourceType)]})]}),e.jsxs("div",{className:"source-priority-rule",children:[e.jsx("span",{children:"Selection priority"}),e.jsx("b",{children:"Bundled → browser artifact → workspace API"})]}),e.jsxs("div",{className:"source-candidate-list",role:"list","aria-label":"Run source candidates",children:[e.jsx(Ys,{source:a,selected:!0,selectedRecord:t}),n.map((s,i)=>e.jsx(Ys,{source:s,selected:!1,selectedRecord:t},`${s.sourceType}:${s.sourceName}:${s.artifactId??i}`))]}),e.jsx("p",{children:"Lower-priority duplicates stay indexed, but values are never mixed across artifacts."})]})}function Ys({source:t,selected:n,selectedRecord:a}){const s=ur(t.sourceType),i=t.modelName!==a.modelName||t.tokenCount!==a.tokenCount||t.layerCount!==a.layerCount;return e.jsxs("div",{className:`${n?"selected":"shadowed"}${i?" metadata-diff":""}`,role:"listitem",children:[e.jsx(s,{size:12,"aria-hidden":"true"}),e.jsxs("span",{children:[e.jsxs("b",{children:[qt(t.sourceType)," · ",t.sourceName]}),e.jsxs("small",{children:[t.modelName," · ",t.tokenCount," tokens · ",t.layerCount," layers · ",Vl(t.importedAt)]})]}),e.jsx("em",{children:n?"selected":i?"metadata differs":"lower priority"})]})}function ur(t){return t==="bundled"?Da:t==="local"?Ki:t==="generated"?dt:vt}function Bl(t){return[...new Set(t.map(n=>qt(n.sourceType)))].join(" + ")}function Vl(t){const n=new Date(t);return Number.isFinite(n.getTime())?`${n.toISOString().slice(0,16).replace("T"," ")} UTC`:t}function mr(t){const n=new Date(t);return Number.isFinite(n.getTime())?`${n.toISOString().slice(5,16).replace("T"," ")} UTC`:t}function Ql(t,n){const a=t.lastUsedAt?Date.parse(t.lastUsedAt):Number.NaN,s=n.lastUsedAt?Date.parse(n.lastUsedAt):Number.NaN;if(Number.isFinite(a)!==Number.isFinite(s))return Number.isFinite(s)?1:-1;if(Number.isFinite(a)&&Number.isFinite(s)&&a!==s)return s-a;const i=Date.parse(t.importedAt),r=Date.parse(n.importedAt);return(Number.isFinite(r)?r:0)-(Number.isFinite(i)?i:0)}function ma(t){if(!t)return[];const n=Date.parse(t);if(!Number.isFinite(n))return[t];const a=new Date(n);return[t,a.toISOString(),a.toUTCString(),mr(t)]}function qt(t){return t==="bundled"?"bundled":t==="local"?"local":t==="generated"?"generated":"workspace"}function Jl(t){switch(t.status){case"idle":return"Workspace discovery idle";case"loading":return"Connecting to workspace";case"ready":return`${t.rootName} · ${t.loadedCount} ready`;case"empty":return`${t.rootName} · no runs found`;case"error":return t.failureKind==="offline"?"Workspace offline":t.failureKind==="api"?"Workspace API error":t.failureKind==="validation"?"Workspace schema error":"Workspace data error";case"cancelled":return"Workspace discovery cancelled"}}function qs(t){return`${(t/(1024*1024)).toFixed(1)} MB`}function Gl({job:t,status:n,submitting:a,ariaLabel:s,tone:i}){const r=u.useRef(performance.now()),o=n!=="error"&&(a||(t==null?void 0:t.status)==="idle"||(t==null?void 0:t.status)==="loading"),[l,c]=u.useState(()=>performance.now()),d=u.useRef({updatedAt:t==null?void 0:t.updatedAt,at:performance.now()});d.current.updatedAt!==(t==null?void 0:t.updatedAt)&&(d.current={updatedAt:t==null?void 0:t.updatedAt,at:performance.now()}),u.useEffect(()=>{if(!o)return;c(performance.now());const A=window.setInterval(()=>c(performance.now()),1e3);return()=>window.clearInterval(A)},[o]);const p=Xl((t==null?void 0:t.progress)??0),g=a?"Submitting":Zl(t==null?void 0:t.stage,n),b=Hs(t==null?void 0:t.createdAt),_=Hs(t==null?void 0:t.updatedAt),y=b!==null&&_!==null?Math.max(0,Math.floor((_-b)/1e3)):0,m=t?d.current.at:r.current,x=o?Math.max(0,Math.floor((l-m)/1e3)):0,w=y+x,N=ed(w);return e.jsxs("div",{className:`job-progress ${i} ${o?"active":"terminal"}`,"aria-label":s,children:[e.jsxs("div",{className:"job-progress-metrics",children:[e.jsxs("div",{children:[e.jsx("span",{children:"Stage"}),e.jsx("strong",{title:g,children:g})]}),e.jsxs("div",{children:[e.jsx("span",{children:"Progress"}),e.jsxs("strong",{children:[p,"%"]})]}),e.jsxs("div",{children:[e.jsx("span",{children:"Elapsed"}),e.jsx("time",{dateTime:`PT${w}S`,children:N})]})]}),e.jsx("div",{className:"job-progress-track",role:"progressbar","aria-label":`${s} completion`,"aria-valuemin":0,"aria-valuemax":100,"aria-valuenow":p,"aria-valuetext":`${p}% complete; ${g}; elapsed ${N}`,children:e.jsx("span",{style:{width:`${p}%`}})})]})}function Xl(t){return Math.max(0,Math.min(100,Math.round(Number.isFinite(t)?t:0)))}function Hs(t){if(!t)return null;const n=Date.parse(t);return Number.isFinite(n)?n:null}function Zl(t,n){return((t==null?void 0:t.trim())||n).replace(/[-_]+/g," ").replace(/\b\w/g,s=>s.toUpperCase()).replace(/\b(nla|av|ar)\b/gi,s=>s.toUpperCase())}function ed(t){if(t<60)return`${t}s`;const n=Math.floor(t/3600),a=Math.floor(t%3600/60),s=t%60;return n>0?`${n}h ${a}m`:`${a}m ${s}s`}const $e=`${Ua}api`,td=B({runId:h().min(1),sampleId:h().min(1),modelName:h().min(1),modelSource:h().min(1),tokenCount:f().int().positive(),layerCount:f().int().positive(),artifactId:h().min(1),sourceName:h().min(1),modifiedAt:h().min(1),sizeBytes:f().int().nonnegative(),promptPreview:h().max(160).nullable().optional(),parentRun:B({runId:h().min(1),sampleId:h().min(1)}).nullable().optional(),conversationId:h().min(1).nullable().optional(),turnIndex:f().int().nonnegative().nullable().optional(),chunkProtocol:Ee("safelens-chunks-v1").optional()}),nd=B({schemaVersion:Ee("1.0"),source:Ee("local-workspace"),rootName:h(),runs:G(td),diagnostics:G(B({sourceName:h(),code:h(),message:h()}))}),hr=ye(["residualCells","logitLens","jLens","attentionHeads","attentionCells","mlpNeurons","mlpCells","attributionTracks","attributionMethods","nla","patching","intervention"]),ad=B({schemaVersion:Ee("1.0"),protocol:Ee("safelens-chunks-v1"),runId:h().min(1),sampleId:h().min(1),artifactId:h().min(1),version:h().min(1),base:It(h(),Et()),chunks:G(B({component:hr,itemCount:f().int().nonnegative(),rangeAxis:ye(["token","token-square","token-values","none"]),layerFilter:fe(),selectorFilter:fe()}))}),sd=B({schemaVersion:Ee("1.0"),protocol:Ee("safelens-chunks-v1"),runId:h().min(1),sampleId:h().min(1),artifactId:h().min(1),version:h().min(1),component:hr,tokenRange:Ia([f().int().nonnegative(),f().int().positive()]),sourceRange:Ia([f().int().nonnegative(),f().int().positive()]).nullable().optional(),layer:f().int().nonnegative().nullable(),selector:h().nullable(),data:Et()}),Fs=new Map,Us=new Map,xn=new Map,id=32,rd=96;function pr(t,n,a){if(n.aborted)return Promise.reject(Os());let s=xn.get(t);if(s!=null&&s.controller.signal.aborted&&(xn.delete(t),s=void 0),!s){const i=new AbortController;s={controller:i,promise:a(i.signal),subscribers:0,settled:!1},xn.set(t,s),s.promise.then(()=>Ks(t,s),()=>Ks(t,s))}return s.abortTimer!==void 0&&(clearTimeout(s.abortTimer),s.abortTimer=void 0),s.subscribers+=1,new Promise((i,r)=>{let o=!1;const l=d=>{o||(o=!0,n.removeEventListener("abort",c),s.subscribers=Math.max(0,s.subscribers-1),d&&s.subscribers===0&&!s.settled&&(s.abortTimer=setTimeout(()=>{s.subscribers===0&&!s.settled&&s.controller.abort()},0)))},c=()=>{l(!0),r(Os())};n.addEventListener("abort",c,{once:!0}),s.promise.then(d=>{l(!1),i(d)},d=>{l(!1),r(d)})})}function Ks(t,n){n.settled=!0,xn.get(t)===n&&xn.delete(t)}function Os(){return new DOMException("The artifact request was cancelled.","AbortError")}function yr(t,n){const a=t.get(n);return a!==void 0&&(t.delete(n),t.set(n,a)),a}function fr(t,n,a,s){for(t.delete(n),t.set(n,a);t.size>s;)t.delete(t.keys().next().value)}async function od(t){var s;const n=await fetch(`${$e}/runs`,{signal:t,headers:{Accept:"application/json"},cache:"no-store"});if(!n.ok)throw new Se("http_error",`Explorer API returned HTTP ${n.status} for the run index.`);const a=nd.safeParse(await n.json());if(!a.success)throw new Se("invalid_index",`Explorer API index failed validation: ${((s=a.error.issues[0])==null?void 0:s.message)??"unknown error"}`);return{summaries:a.data.runs,rootName:a.data.rootName,diagnostics:a.data.diagnostics.map(i=>`${i.sourceName} [${i.code}]: ${i.message}`)}}async function Bs(t,n){const a=await fetch(`${$e}/runs/${encodeURIComponent(t.runId)}/samples/${encodeURIComponent(t.sampleId)}`,{signal:n,headers:{Accept:"application/json"},cache:"no-store"});if(!a.ok)throw new Se("sample_error",`Could not load ${t.runId}/${t.sampleId}: HTTP ${a.status}.`);const s=wt.safeParse(await a.json());if(!s.success){const i=s.error.issues[0];throw new Se("invalid_sample",`${t.runId}/${t.sampleId} failed at ${(i==null?void 0:i.path.join("."))||"artifact"}: ${(i==null?void 0:i.message)||"invalid sample"}.`)}return s.data}function ld(t,n){const a=[t.artifactId,t.modifiedAt,t.sizeBytes,t.runId,t.sampleId].join(":");return pr(`metadata:${a}`,n,s=>dd(t,a,s))}async function dd(t,n,a){const s=yr(Fs,n),i=await fetch(`${$e}/runs/${encodeURIComponent(t.runId)}/samples/${encodeURIComponent(t.sampleId)}/metadata`,{signal:a,headers:{Accept:"application/json",...s?{"If-None-Match":s.etag}:{}},cache:"no-cache"});if(i.status===304&&s)return s.value;if(!i.ok)throw new Se("metadata_error",`Could not load metadata for ${t.runId}/${t.sampleId}: HTTP ${i.status}.`);const r=ad.safeParse(await i.json());if(!r.success||r.data.runId!==t.runId||r.data.sampleId!==t.sampleId)throw new Se("invalid_metadata",`${t.runId}/${t.sampleId} returned invalid or mismatched chunk metadata.`);const o=i.headers.get("ETag")??`"${r.data.version}"`;return fr(Fs,n,{etag:o,value:r.data},id),r.data}function gr(t,n,a){if(!Number.isInteger(n.tokenStart)||!Number.isInteger(n.tokenEnd)||n.tokenStart<0||n.tokenEnd<=n.tokenStart||n.tokenEnd-n.tokenStart>512)throw new Se("invalid_chunk_range","Chunk range must be an integer half-open interval of at most 512 tokens.");if(n.sourceStart===void 0!=(n.sourceEnd===void 0)||n.sourceStart!==void 0&&(!Number.isInteger(n.sourceStart)||!Number.isInteger(n.sourceEnd)||n.sourceStart<0||n.sourceEnd<=n.sourceStart||n.sourceEnd-n.sourceStart>512))throw new Se("invalid_source_range","Attention source range must be an integer half-open interval of at most 512 tokens.");const s=new URLSearchParams({tokenStart:String(n.tokenStart),tokenEnd:String(n.tokenEnd)});n.layer!==void 0&&s.set("layer",String(n.layer)),n.selector&&s.set("selector",n.selector),n.sourceStart!==void 0&&s.set("sourceStart",String(n.sourceStart)),n.sourceEnd!==void 0&&s.set("sourceEnd",String(n.sourceEnd));const i=[t.artifactId,t.modifiedAt,t.sizeBytes,t.runId,t.sampleId,n.component,n.tokenStart,n.tokenEnd,n.sourceStart??n.tokenStart,n.sourceEnd??n.tokenEnd,n.layer??"all",n.selector??"all"].join(":");return pr(`chunk:${i}`,a,r=>cd(t,n,s,i,r))}async function cd(t,n,a,s,i){const r=yr(Us,s),o=await fetch(`${$e}/runs/${encodeURIComponent(t.runId)}/samples/${encodeURIComponent(t.sampleId)}/chunks/${n.component}?${a}`,{signal:i,headers:{Accept:"application/json",...r?{"If-None-Match":r.etag}:{}},cache:"no-cache"});if(o.status===304&&r)return r.value;if(!o.ok)throw new Se("chunk_error",`Could not load ${n.component} chunk: HTTP ${o.status}.`);const l=sd.safeParse(await o.json());if(!l.success||l.data.runId!==t.runId||l.data.sampleId!==t.sampleId||l.data.component!==n.component)throw new Se("invalid_chunk",`${t.runId}/${t.sampleId} returned a mismatched ${n.component} chunk.`);const c=o.headers.get("ETag")??`"${l.data.version}:${s}"`;return fr(Us,s,{etag:c,value:l.data},rd),l.data}class Se extends Error{constructor(n,a,s,i){super(a),this.code=n,this.httpStatus=s,this.serverCode=i,this.name="ExplorerApiError"}}const ud=B({role:ye(["user","assistant"]),content:h().min(1)}),_r=B({id:h().min(1),kind:Ee("prompt-run"),status:ye(["idle","loading","ready","error","cancelled"]),stage:h(),progress:f().int().min(0).max(100),detail:h(),task:h().optional(),groundTruth:h().optional(),baselineSuccess:fe().optional(),steeredSuccess:fe().optional(),baselinePrediction:h().nullable().optional(),steeredPrediction:h().nullable().optional(),baselineLabel:h().optional(),steeredLabel:h().optional(),createdAt:h(),updatedAt:h(),request:B({prompt:h(),template:ye(["plain","chat"]),model:h(),seed:f().int(),maxNewTokens:f().int(),temperature:f(),messages:G(ud).default([])}),result:wt.nullable(),error:h().nullable()}),md=B({models:G(h().min(1)).min(1),templates:G(ye(["plain","chat"])),maxNewTokens:f().int().positive()}),br=B({name:h().min(1),shortName:h().min(1),definition:h().min(1),threshold:f().min(0).max(1)}),hd=B({id:h().min(1),category:h().min(1),task:h().nullable().optional(),source:h().nullable().optional(),prompt:h().nullable().optional(),cleanPrompt:h().nullable().optional(),corruptedPrompt:h().nullable().optional(),desiredPrompt:h().nullable().optional(),undesiredPrompt:h().nullable().optional(),targetText:h().nullable().optional(),groundTruth:h().nullable().optional(),expectedBehavior:h().nullable().optional(),failureBehavior:h().nullable().optional(),expected:h().min(1)}),pd=B({id:h().min(1),name:h().min(1),version:h().min(1),task:h().min(1),description:h().min(1),source:h().min(1),metric:br,samples:G(hd).min(1)}),yd=B({id:ye(["pca_minus_neg","mean_minus_neg"]),name:h().min(1),kind:Ee("optimization"),description:h().min(1),paperTitle:h().min(1),paperUrl:h().url(),implementation:h().min(1),supportedDatasetIds:G(h().min(1)).min(1)}),fd=B({datasets:G(pd).min(1),algorithms:G(yd).min(1)}),gd=B({sampleId:h().min(1),category:h().min(1),task:h().optional(),prompt:h(),groundTruth:h().optional(),status:ye(["complete","error"]),passed:fe(),detail:h(),original:h().optional(),steered:h().optional(),patched:h().optional(),baselinePrediction:h().nullable().optional(),steeredPrediction:h().nullable().optional(),baselineLabel:h().optional(),steeredLabel:h().optional(),baselineSuccess:fe().optional(),steeredSuccess:fe().optional(),steeringApplied:fe().optional(),diagnostics:It(h(),Et()).optional()}),_d=B({dataset:B({id:h(),name:h(),version:h(),sampleCount:f().int()}),algorithm:B({id:ye(["pca_minus_neg","mean_minus_neg"]),name:h(),implementation:h()}),execution:B({mode:h().optional(),source:Ee("real-local-model"),model:h(),modelSource:h().optional(),revision:h().optional(),device:h().optional(),dtype:h().optional(),seed:f().int().optional(),layer:f().int().optional(),requestedLayer:f().int().optional(),sourceLayer:f().int().optional(),requestedSourceLayer:f().int().optional(),injectionLayer:f().int().optional(),component:h().optional(),maxNewTokens:f().int().optional(),positionMode:h().optional(),baselineSamples:f().int().nonnegative().optional(),steeredSamples:f().int().nonnegative().optional(),taskConfigs:It(h(),Et()).optional()}),metric:br.extend({passed:f().int().nonnegative(),completed:f().int().nonnegative(),errors:f().int().nonnegative(),accuracy:f().min(0).max(1),meetsThreshold:fe(),baselineSuccess:f().int().nonnegative().optional(),baselineFailure:f().int().nonnegative().optional(),failureToSuccess:f().int().nonnegative().optional(),successToFailure:f().int().nonnegative().optional(),tasks:It(h(),Et()).optional()}),rows:G(gd)}),bd=B({id:h().min(1),kind:Ee("dataset-test"),status:ye(["idle","loading","ready","error","cancelled"]),stage:h(),progress:f().int().min(0).max(100),detail:h(),createdAt:h(),updatedAt:h(),request:B({datasetId:h(),algorithmId:ye(["pca_minus_neg","mean_minus_neg"]),model:h(),sampleIds:G(h()),layer:f().int(),sourceLayer:f().int().nullable().optional(),strength:f(),seed:f().int(),maxNewTokens:f().int()}),result:_d.nullable(),error:h().nullable()}),xd=B({modelName:h().min(1),text:h(),tokens:G(B({index:f().int().nonnegative(),tokenId:f().int().nonnegative(),text:h()})),truncated:fe()}),xr=B({id:h().min(1),kind:Ee("attribution"),status:ye(["idle","loading","ready","error","cancelled"]),stage:h(),progress:f().int().min(0).max(100),detail:h(),createdAt:h(),updatedAt:h(),request:B({sourceRun:B({runId:h(),sampleId:h(),modelName:h()}),response:h(),objective:Ee("response_token_logit"),targetResponseIndex:f().int().nonnegative(),baseline:ye(["pad_token","zero_token_id"]),nSteps:f().int()}),result:wt.nullable(),error:h().nullable()}),wd=B({name:h(),base_model:h(),layer:f().int(),component:h(),d_model:f().int().positive(),av_repo:h(),ar_repo:h().nullable(),av_revision:h().nullable().default(null),ar_revision:h().nullable().default(null),gated:fe(),description:h()}),wr=B({profile:h(),baseModel:h(),layer:f().int(),component:h(),dModel:f().int(),avRepo:h(),arRepo:h().nullable(),gated:fe(),tokenConfigured:fe(),modelMatches:fe(),layerAvailable:fe(),dModelMatches:fe(),status:ye(["compatible","incompatible","authorization_required"]),canSubmit:fe(),reason:h()}),kr=B({id:h().min(1),kind:Ee("nla"),status:ye(["idle","loading","ready","error","cancelled"]),stage:h(),progress:f().int().min(0).max(100),detail:h(),createdAt:h(),updatedAt:h(),request:B({profile:h(),positions:G(f().int()).min(1).max(8),revision:h(),maxNewTokens:f().int(),loadReconstructor:Ee(!0),confirmGatedAccess:fe(),sourceRun:B({runId:h(),sampleId:h(),modelName:h()}),preflight:wr}),result:wt.nullable(),error:h().nullable()}),kd=B({packageInstalled:fe(),defaultModel:h(),defaultSource:h(),defaultFilename:h().min(1),defaultRevision:h().min(1),profiles:G(B({name:h().min(1),baseModel:h().min(1),source:h().min(1),filename:h().min(1),revision:h().min(1),dModel:f().int().positive(),sourceLayers:G(f().int().nonnegative()).min(1),defaultLayer:f().int().nonnegative(),nPrompts:f().int().positive(),description:h().min(1)})).default([])}),vr=B({packageInstalled:fe(),modelAllowed:fe(),layerAvailable:fe(),positionValid:fe(),lensConfigured:fe(),artifactChecked:fe(),fittedLayers:G(f().int().nonnegative()),lensDModel:f().int().positive().nullable(),canSubmit:fe(),reason:h().min(1)}),jr=B({id:h().min(1),kind:Ee("jlens"),status:ye(["idle","loading","ready","error","cancelled"]),stage:h(),progress:f().int().min(0).max(100),detail:h(),createdAt:h(),updatedAt:h(),request:B({layer:f().int().nonnegative(),position:f().int().nonnegative(),lensSource:h().min(1),filename:h().min(1),revision:h().min(1),topK:f().int().min(3).max(50),sourceRun:B({runId:h(),sampleId:h(),modelName:h()}),preflight:vr}),result:wt.nullable(),error:h().nullable()}),Ir=B({modelAllowed:fe(),promptsDiffer:fe(),tokenCountMatches:fe(),targetTokenValid:fe(),componentSupported:fe(),cleanTokenCount:f().int().positive(),corruptedTokenCount:f().int().nonnegative(),changedPositions:G(f().int().nonnegative()),targetTokenId:f().int().nonnegative(),targetTokenText:h(),corruptedTokens:G(B({index:f().int().nonnegative(),tokenId:f().int().nonnegative(),text:h(),changed:fe()})),canSubmit:fe(),reason:h()}),Sr=B({id:h().min(1),kind:Ee("patching"),status:ye(["idle","loading","ready","error","cancelled"]),stage:h(),progress:f().int().min(0).max(100),detail:h(),createdAt:h(),updatedAt:h(),request:B({corruptedPrompt:h(),component:ye(["resid_post","attn_out","z","mlp_out"]),layers:G(f().int()).min(1),positions:G(f().int()).min(1),head:f().int().nonnegative().optional(),targetTokenId:f().int().nonnegative(),sourceRun:B({runId:h(),sampleId:h(),modelName:h()}),preflight:Ir}),result:wt.nullable(),error:h().nullable()}),Tr=B({mode:ye(["direction","neuron","sae_feature"]).default("direction"),modelAllowed:fe(),layerAvailable:fe(),componentSupported:fe(),positionRangeValid:fe(),targetTokenValid:fe(),referencesDiffer:fe(),featureAvailable:fe().default(!0),saeProfileValid:fe().default(!0),saeRuntimeAvailable:fe().default(!0),targetTokenId:f().int().nonnegative(),targetTokenText:h(),positionStart:f().int().nonnegative(),positionEnd:f().int().positive(),canSubmit:fe(),reason:h()}),vd=B({id:h().min(1),label:h().min(1),modelName:h().min(1),release:h().min(1),saeId:h().min(1),layer:f().int().nonnegative(),component:Ee("resid_post"),width:f().int().positive(),architecture:Ee("jump_relu"),source:h().min(1)}),jd=B({modelName:h().min(1),layer:f().int().nonnegative(),featureIndex:f().int().nonnegative(),label:h().min(1),source:ye(["neuronpedia","index"]),url:h().url().nullable().optional(),positiveTokens:G(h()).default([]),negativeTokens:G(h()).default([]),maxActApprox:f().nullable().optional(),vectorDefaultSteerStrength:f().nullable().optional()}),Id=B({featureIndex:f().int().nonnegative(),strength:f(),layer:f().int().nonnegative().default(9)}),Vs=B({text:h(),tokenIds:G(f().int().nonnegative()),tokens:G(B({index:f().int().nonnegative(),tokenId:f().int().nonnegative(),text:h()}))});B({modelName:h().min(1),modelPath:h().min(1),saeRelease:h().min(1),saeId:h().min(1),layer:f().int().nonnegative(),layers:G(f().int().nonnegative()).default([]),hookName:h().min(1),hooks:G(h().min(1)).default([]),featureCount:f().int().positive(),hiddenSize:f().int().positive(),features:G(Id),prompt:h(),default:Vs,steered:Vs,generationChanged:fe(),seed:f().int().nonnegative(),maxNewTokens:f().int().positive(),temperature:f().nonnegative(),steerPosition:ye(["all","prompt","generated","prompt_position"]).default("all"),promptPosition:f().int().nonnegative().nullable().optional()});const Sd=B({modelName:h().min(1),modelPath:h().min(1),saePath:h().min(1),saeUrl:h().url(),release:h().min(1),saeId:h().min(1),layer:f().int().nonnegative(),layers:G(f().int().nonnegative()).default([]),hookName:h().min(1),hooks:G(h().min(1)).default([]),featureCount:f().int().positive(),device:h().min(1),dtype:h().min(1),checkpointPresent:fe(),presets:G(B({id:h().min(1),label:h().min(1),description:h(),featureIndex:f().int().nonnegative(),strength:f(),layer:f().int().nonnegative().default(9),features:G(B({featureIndex:f().int().nonnegative(),strength:f(),layer:f().int().nonnegative().default(9)})).default([])}))}),Td=B({featureIndex:f().int().nonnegative(),maxActivation:f(),meanActivation:f(),activeTokenCount:f().int().nonnegative(),peakTokenIndex:f().int().nonnegative(),peakTokenText:h(),label:h().min(1),source:ye(["neuronpedia","index"]),url:h().url().nullable().optional(),positiveTokens:G(h()).default([]),negativeTokens:G(h()).default([]),maxActApprox:f().nullable().optional(),vectorDefaultSteerStrength:f().nullable().optional(),suggestedStrength:f()});B({modelName:h().min(1),saeRelease:h().min(1),saeId:h().min(1),layer:f().int().nonnegative(),hookName:h().min(1),featureCount:f().int().positive(),prompt:h(),tokens:G(B({index:f().int().nonnegative(),tokenId:f().int().nonnegative(),text:h()})),features:G(Td).max(32)});const Ad=B({featureIndex:f().int().nonnegative(),label:h().min(1),source:ye(["neuronpedia","index"]),url:h().url().nullable().optional(),positiveTokens:G(h()).default([]),negativeTokens:G(h()).default([]),maxActivation:f().nonnegative(),meanActivation:f(),activeTokenCount:f().int().nonnegative(),peakTokenIndex:f().int().nonnegative(),peakTokenText:h(),recommendedDelta:f().positive()}),Nd=B({runId:h().min(1),sampleId:h().min(1),modelName:h().min(1),layer:f().int().nonnegative(),component:Ee("resid_post"),release:h().min(1),saeId:h().min(1),positionStart:f().int().nonnegative(),positionEnd:f().int().positive(),candidates:G(Ad).max(20)}),Ar=B({id:h().min(1),kind:Ee("sae-discovery"),status:ye(["idle","loading","ready","error","cancelled"]),stage:h(),progress:f().int().min(0).max(100),detail:h(),createdAt:h(),updatedAt:h(),request:B({layer:f().int().nonnegative(),component:Ee("resid_post"),saeRelease:h().min(1),saeId:h().min(1),positionStart:f().int().nonnegative(),positionEnd:f().int().positive(),limit:f().int().min(1).max(20),sourceRun:B({runId:h(),sampleId:h(),modelName:h()})}),result:Nd.nullable(),error:h().nullable()}),Nr=B({id:h().min(1),kind:Ee("intervention"),status:ye(["idle","loading","ready","error","cancelled"]),stage:h(),progress:f().int().min(0).max(100),detail:h(),createdAt:h(),updatedAt:h(),request:B({mode:ye(["direction","neuron","sae_feature"]).default("direction"),desiredPrompt:h(),undesiredPrompt:h(),positivePrompts:G(h()).min(1).optional(),negativePrompts:G(h()).min(1).optional(),activationReduce:ye(["last_token","mean"]).default("last_token"),layer:f().int().nonnegative(),sourceLayer:f().int().nonnegative().optional(),injectLayer:f().int().nonnegative().optional(),component:ye(["resid_post","attn_out","mlp_out"]),scale:f(),positionStart:f().int().nonnegative(),positionEnd:f().int().positive(),targetTokenId:f().int().nonnegative(),seed:f().int().nonnegative(),maxNewTokens:f().int().positive(),temperature:f().nonnegative(),neuron:f().int().nonnegative().nullish().transform(t=>t??void 0),saeRelease:h().min(1).nullish().transform(t=>t??void 0),saeId:h().min(1).nullish().transform(t=>t??void 0),featureIndex:f().int().nonnegative().nullish().transform(t=>t??void 0),saeOperation:ye(["add","ablate"]).nullish().transform(t=>t??void 0),saeFeatures:G(B({featureIndex:f().int().nonnegative(),strength:f(),layer:f().int().nonnegative()})).optional(),sourceRun:B({runId:h(),sampleId:h(),modelName:h()}),preflight:Tr}),result:wt.nullable(),error:h().nullable()});async function Cd(t){const n=await fetch(`${$e}/jobs/prompt`,{method:"POST",headers:{Accept:"application/json","Content-Type":"application/json"},body:JSON.stringify(t)});if(!n.ok)throw await Ke(n,"prompt_submit_error");return Cr(await n.json())}async function Rd(t){const n=await fetch(`${$e}/prompt/options`,{headers:{Accept:"application/json"},signal:t,cache:"no-store"});if(!n.ok)throw await Ke(n,"prompt_options_error");const a=md.safeParse(await n.json());if(!a.success)throw new Se("prompt_options_invalid_schema","Prompt options failed validation.",n.status);return a.data}async function Ld(t){var s;const n=await fetch(`${$e}/datasets`,{signal:t,headers:{Accept:"application/json"},cache:"no-store"});if(!n.ok)throw await Ke(n,"dataset_catalog_error");const a=fd.safeParse(await n.json());if(!a.success)throw new Se("invalid_dataset_catalog",`Dataset catalog failed validation: ${((s=a.error.issues[0])==null?void 0:s.message)??"unknown error"}`);return a.data}async function $d(t){const n=await fetch(`${$e}/jobs/dataset-test`,{method:"POST",headers:{Accept:"application/json","Content-Type":"application/json"},body:JSON.stringify(t)});if(!n.ok)throw await Ke(n,"dataset_test_submit_error");return Ja(await n.json())}async function Ed(t){const n=await fetch(`${$e}/jobs/${encodeURIComponent(t)}`,{headers:{Accept:"application/json"},cache:"no-store"});if(!n.ok)throw await Ke(n,"dataset_test_status_error");return Ja(await n.json())}async function Md(t){const n=await fetch(`${$e}/jobs/${encodeURIComponent(t)}`,{method:"DELETE",headers:{Accept:"application/json"}});if(!n.ok)throw await Ke(n,"dataset_test_cancel_error");return Ja(await n.json())}async function Pd(t,n,a){const s=await fetch(`${$e}/tokenize`,{method:"POST",headers:{Accept:"application/json","Content-Type":"application/json"},body:JSON.stringify({modelName:t,text:n}),signal:a});if(!s.ok)throw await Ke(s,"tokenize_error");const i=xd.safeParse(await s.json());if(!i.success)throw new Se("tokenize_invalid_schema","Response tokenization failed validation.",s.status);return i.data}async function Qs(t){const n=await fetch(`${$e}/jobs/${encodeURIComponent(t)}`,{method:"DELETE",headers:{Accept:"application/json"}});if(!n.ok)throw await Ke(n,"prompt_cancel_error");return Cr(await n.json())}function Qt(t){return`${$e}/jobs/${encodeURIComponent(t)}/events`}async function Wd(t){const n=await fetch(`${$e}/jobs/attribution`,{method:"POST",headers:{Accept:"application/json","Content-Type":"application/json"},body:JSON.stringify(t)});if(!n.ok)throw await Ke(n,"attribution_submit_error");return Rr(await n.json())}async function Js(t){const n=await fetch(`${$e}/jobs/${encodeURIComponent(t)}`,{method:"DELETE",headers:{Accept:"application/json"}});if(!n.ok)throw await Ke(n,"attribution_cancel_error");return Rr(await n.json())}async function zd(t){const n=await fetch(`${$e}/nla/profiles`,{signal:t,headers:{Accept:"application/json"},cache:"no-store"});if(!n.ok)throw new Se("nla_profiles_error",await Tt(n));const a=G(wd).safeParse(await n.json());if(!a.success)throw new Se("invalid_nla_profiles",a.error.message);return a.data}async function Dd(t,n){const a=await fetch(`${$e}/nla/preflight`,{method:"POST",signal:n,headers:{Accept:"application/json","Content-Type":"application/json"},body:JSON.stringify(t)});if(!a.ok)throw new Se("nla_preflight_error",await Tt(a));const s=wr.safeParse(await a.json());if(!s.success)throw new Se("invalid_nla_preflight",s.error.message);return s.data}async function Yd(t){const n=await fetch(`${$e}/jobs/nla`,{method:"POST",headers:{Accept:"application/json","Content-Type":"application/json"},body:JSON.stringify(t)});if(!n.ok)throw await Ke(n,"nla_submit_error");return Lr(await n.json())}async function Gs(t){const n=await fetch(`${$e}/jobs/${encodeURIComponent(t)}`,{method:"DELETE",headers:{Accept:"application/json"}});if(!n.ok)throw await Ke(n,"nla_cancel_error");return Lr(await n.json())}async function qd(t){const n=await fetch(`${$e}/jlens/options`,{signal:t,headers:{Accept:"application/json"},cache:"no-store"});if(!n.ok)throw new Se("jlens_options_error",await Tt(n));const a=kd.safeParse(await n.json());if(!a.success)throw new Se("invalid_jlens_options",a.error.message);return a.data}async function Hd(t,n){const a=await fetch(`${$e}/jlens/preflight`,{method:"POST",signal:n,headers:{Accept:"application/json","Content-Type":"application/json"},body:JSON.stringify(t)});if(!a.ok)throw new Se("jlens_preflight_error",await Tt(a));const s=vr.safeParse(await a.json());if(!s.success)throw new Se("invalid_jlens_preflight",s.error.message);return s.data}async function Fd(t){const n=await fetch(`${$e}/jobs/jlens`,{method:"POST",headers:{Accept:"application/json","Content-Type":"application/json"},body:JSON.stringify(t)});if(!n.ok)throw await Ke(n,"jlens_submit_error");return $r(await n.json())}async function Xs(t){const n=await fetch(`${$e}/jobs/${encodeURIComponent(t)}`,{method:"DELETE",headers:{Accept:"application/json"}});if(!n.ok)throw await Ke(n,"jlens_cancel_error");return $r(await n.json())}async function Ud(t,n){const a=await fetch(`${$e}/patching/preflight`,{method:"POST",signal:n,headers:{Accept:"application/json","Content-Type":"application/json"},body:JSON.stringify(t)});if(!a.ok)throw new Se("patching_preflight_error",await Tt(a));const s=Ir.safeParse(await a.json());if(!s.success)throw new Se("invalid_patching_preflight",s.error.message);return s.data}async function Kd(t){const n=await fetch(`${$e}/jobs/patching`,{method:"POST",headers:{Accept:"application/json","Content-Type":"application/json"},body:JSON.stringify(t)});if(!n.ok)throw await Ke(n,"patching_submit_error");return Er(await n.json())}async function Zs(t){const n=await fetch(`${$e}/jobs/${encodeURIComponent(t)}`,{method:"DELETE",headers:{Accept:"application/json"}});if(!n.ok)throw await Ke(n,"patching_cancel_error");return Er(await n.json())}async function Qa(t,n){const a=await fetch(`${$e}/intervention/preflight`,{method:"POST",signal:n,headers:{Accept:"application/json","Content-Type":"application/json"},body:JSON.stringify(t)});if(!a.ok)throw new Se("intervention_preflight_error",await Tt(a));const s=Tr.safeParse(await a.json());if(!s.success)throw new Se("invalid_intervention_preflight",s.error.message);return s.data}async function Od(t,n){const a=new URLSearchParams({modelName:t}),s=await fetch(`${$e}/intervention/sae-profiles?${a}`,{signal:n,headers:{Accept:"application/json"},cache:"no-store"});if(!s.ok)throw new Se("sae_profiles_error",await Tt(s));const i=G(vd).safeParse(await s.json());if(!i.success)throw new Se("invalid_sae_profiles",i.error.message);return i.data}async function Bd(t){const n=await fetch(`${$e}/sae-steering/config`,{signal:t,headers:{Accept:"application/json"},cache:"no-store"});if(!n.ok)throw new Se("sae_steering_config_error",await Tt(n));const a=Sd.safeParse(await n.json());if(!a.success)throw new Se("invalid_sae_steering_config",a.error.message);return a.data}async function Vd(t,n,a,s){const i=new URLSearchParams({modelName:t,layer:String(n),featureIndex:String(a)}),r=await fetch(`${$e}/intervention/sae-feature-info?${i}`,{signal:s,headers:{Accept:"application/json"},cache:"no-store"});if(!r.ok)throw new Se("sae_feature_info_error",await Tt(r));const o=jd.safeParse(await r.json());if(!o.success)throw new Se("invalid_sae_feature_info",o.error.message);return o.data}async function Qd(t){const n=await fetch(`${$e}/jobs/sae-discovery`,{method:"POST",headers:{Accept:"application/json","Content-Type":"application/json"},body:JSON.stringify(t)});if(!n.ok)throw await Ke(n,"sae_discovery_submit_error");return Pr(await n.json())}async function ei(t){const n=await fetch(`${$e}/jobs/${encodeURIComponent(t)}`,{method:"DELETE",headers:{Accept:"application/json"}});if(!n.ok)throw await Ke(n,"sae_discovery_cancel_error");return Pr(await n.json())}async function Jd(t){const n=await fetch(`${$e}/jobs/intervention`,{method:"POST",headers:{Accept:"application/json","Content-Type":"application/json"},body:JSON.stringify(t)});if(!n.ok)throw await Ke(n,"intervention_submit_error");return Mr(await n.json())}async function ti(t){const n=await fetch(`${$e}/jobs/${encodeURIComponent(t)}`,{method:"DELETE",headers:{Accept:"application/json"}});if(!n.ok)throw await Ke(n,"intervention_cancel_error");return Mr(await n.json())}function Cr(t){var a;const n=_r.safeParse(t);if(!n.success)throw new Se("invalid_job",`Prompt job response failed validation: ${((a=n.error.issues[0])==null?void 0:a.message)??"unknown error"}`);return n.data}function Rr(t){var a;const n=xr.safeParse(t);if(!n.success)throw new Se("invalid_attribution_job",`Attribution job response failed validation: ${((a=n.error.issues[0])==null?void 0:a.message)??"unknown error"}`);return n.data}function Lr(t){const n=kr.safeParse(t);if(!n.success)throw new Se("invalid_nla_job",`NLA job response failed validation: ${n.error.message}`);return n.data}function $r(t){const n=jr.safeParse(t);if(!n.success)throw new Se("invalid_jlens_job",`J-Lens job response failed validation: ${n.error.message}`);return n.data}function Er(t){const n=Sr.safeParse(t);if(!n.success)throw new Se("invalid_patching_job",`Patching job response failed validation: ${n.error.message}`);return n.data}function Mr(t){const n=Nr.safeParse(t);if(!n.success)throw new Se("invalid_intervention_job",`Intervention job response failed validation: ${n.error.message}`);return n.data}function Pr(t){const n=Ar.safeParse(t);if(!n.success)throw new Se("invalid_sae_discovery_job",`SAE feature discovery job failed validation: ${n.error.message}`);return n.data}function Ja(t){var a;const n=bd.safeParse(t);if(!n.success)throw new Se("invalid_dataset_test_job",`Dataset test job failed validation: ${((a=n.error.issues[0])==null?void 0:a.message)??"unknown error"}`);return n.data}async function Tt(t){var n;try{const a=await t.json();if(typeof a.detail=="string")return a.detail;if((n=a.detail)!=null&&n.message)return a.detail.message}catch{}return`Explorer API returned HTTP ${t.status}.`}async function Ke(t,n){let a=`Explorer API returned HTTP ${t.status}.`,s;try{const i=await t.json();typeof i.detail=="string"?a=i.detail:Array.isArray(i.detail)?a=i.detail.map(r=>{var l;return[(l=r.loc)==null?void 0:l.slice(1).join("."),r.msg].filter(Boolean).join(": ")}).filter(Boolean).join("; ")||a:i.detail&&(typeof i.detail.message=="string"&&(a=i.detail.message),typeof i.detail.code=="string"&&(s=i.detail.code))}catch{}return new Se(n,a,t.status,s)}function st(t,n,a){if(t instanceof Se){const s=Zd(t);return ln({kind:s,phase:n,message:t.message,code:t.code,serverCode:t.serverCode,httpStatus:t.httpStatus})}return t instanceof TypeError?ln({kind:"network",phase:n,message:t.message||a,code:`${n}_transport_error`}):ln({kind:n==="execution"?"computation":"request",phase:n,message:t instanceof Error?t.message:a,code:`${n}_error`})}function it(t,n){return ln({kind:"protocol",phase:"stream",message:t,code:n})}function Jt(t){return ln({kind:"network",phase:"stream",message:t,code:"progress_stream_disconnected"})}function Gt(t,n){return ln({kind:"computation",phase:"execution",message:n,code:`${t}_execution_error`})}function Gd(t){switch(t){case"network":return"Network";case"request":return"Request";case"compatibility":return"Compatibility";case"authorization":return"Authorization";case"protocol":return"Protocol";case"computation":return"Computation"}}function Xd(t){switch(t.kind){case"network":return"Check the local API connection, then retry. The source Run is unchanged.";case"request":return"Review the current inputs and retry. No result was added to the Run Library.";case"compatibility":return"Choose a compatible model, layer, component, or token context before retrying.";case"authorization":return"Confirm the required local model access or credentials, then run preflight again.";case"protocol":return"Retry once. If the response remains invalid, copy diagnostics and check API compatibility.";case"computation":return"The worker stopped without replacing the source Run. Copy diagnostics before retrying."}}function Zd(t){var a;const n=((a=t.serverCode)==null?void 0:a.toLowerCase())??"";return t.httpStatus===401||t.httpStatus===403||/(authorization|gated|credential|token_required|access_required)/.test(n)?"authorization":t.httpStatus===409||/(incompatible|preflight|model_not_allowed|layer_unavailable|component_unsupported)/.test(n)?"compatibility":t.code.startsWith("invalid_")?"protocol":"request"}function ln(t){return{...t,title:ec(t.kind,t.phase),occurredAt:new Date().toISOString()}}function ec(t,n){if(n==="cancellation")return"Cancellation request failed";switch(t){case"network":return"Workspace connection interrupted";case"request":return"Job request rejected";case"compatibility":return"Job inputs are incompatible";case"authorization":return"Job authorization required";case"protocol":return"Job response is invalid";case"computation":return"Job computation failed"}}function tc({failure:t,job:n,jobLabel:a}){const[s,i]=u.useState("idle");u.useEffect(()=>i("idle"),[t]);async function r(){const o={schemaVersion:"1.0",kind:"safelens-job-error",category:t.kind,phase:t.phase,code:t.code,serverCode:t.serverCode??null,httpStatus:t.httpStatus??null,message:t.message,job:n?{id:n.id,kind:n.kind,status:n.status,stage:n.stage,progress:n.progress,createdAt:n.createdAt,updatedAt:n.updatedAt}:null,context:a,url:window.location.href,userAgent:navigator.userAgent,occurredAt:t.occurredAt,copiedAt:new Date().toISOString()};try{await navigator.clipboard.writeText(JSON.stringify(o,null,2)),i("copied")}catch{i("failed")}}return e.jsxs("details",{className:`job-failure-details ${t.kind}`,children:[e.jsxs("summary",{children:[e.jsx(Lt,{size:14,"aria-hidden":"true"}),e.jsx("span",{children:"Failure diagnostics"}),e.jsx("b",{children:Gd(t.kind)})]}),e.jsx("p",{children:Xd(t)}),e.jsxs("dl",{children:[e.jsxs("div",{children:[e.jsx("dt",{children:"Phase"}),e.jsx("dd",{children:t.phase})]}),e.jsxs("div",{children:[e.jsx("dt",{children:"Code"}),e.jsx("dd",{children:e.jsx("code",{children:t.serverCode??t.code})})]}),t.httpStatus!==void 0&&e.jsxs("div",{children:[e.jsx("dt",{children:"HTTP"}),e.jsx("dd",{children:t.httpStatus})]}),n&&e.jsxs("div",{children:[e.jsx("dt",{children:"Job"}),e.jsx("dd",{children:e.jsx("code",{children:n.id})})]})]}),e.jsxs("div",{className:"job-failure-actions",children:[e.jsxs("button",{type:"button",onClick:()=>void r(),children:[s==="copied"?e.jsx(Ft,{size:14}):e.jsx(Ho,{size:14}),s==="copied"?"Diagnostics copied":"Copy diagnostics"]}),e.jsx("span",{className:s==="failed"?"failed":"","aria-live":"polite",children:s==="failed"?"Copy failed":"Source Run unchanged"})]})]})}function Wr(t){var b;const[n,a]=u.useState({job:null,error:null}),s=u.useRef(null),i=u.useRef(null),r=u.useRef(0),o=u.useRef(new Set),l=u.useCallback(()=>{var _;(_=s.current)==null||_.close(),s.current=null},[]),c=u.useCallback((_,y)=>{var m;((m=i.current)==null?void 0:m.id)!==_.id||i.current.generation!==y||(a({job:_,error:_.status==="error"?Gt(_.kind,_.error??_.detail):null}),_.status==="ready"&&_.result&&!o.current.has(_.id)?(o.current.add(_.id),l(),t(_.result,_)):(_.status==="error"||_.status==="cancelled")&&l())},[l,t]),d=u.useCallback(async _=>{var m,x;l();const y=++r.current;i.current={id:"submitting",generation:y},a({job:null,error:null});try{const w=await Cd(_);if(((m=i.current)==null?void 0:m.generation)!==y)return;i.current={id:w.id,generation:y},a({job:w,error:null});const N=new EventSource(Qt(w.id));s.current=N,N.addEventListener("job",A=>{if(!(A instanceof MessageEvent))return;let T;try{T=JSON.parse(A.data)}catch{l(),a(S=>({...S,error:it("Prompt progress stream returned invalid JSON.","prompt_stream_invalid_json")}));return}const k=_r.safeParse(T);if(!k.success){l(),a(S=>({...S,error:it("Prompt progress payload failed validation.","prompt_stream_invalid_schema")}));return}c(k.data,y)}),N.onerror=()=>{var A;((A=i.current)==null?void 0:A.generation)===y&&(l(),a(T=>{var k,S;return{...T,error:((k=T.job)==null?void 0:k.status)==="ready"||((S=T.job)==null?void 0:S.status)==="cancelled"?T.error:T.error??Jt("Prompt progress stream disconnected. Retry the job.")}}))}}catch(w){if(((x=i.current)==null?void 0:x.generation)!==y)return;i.current=null,a({job:null,error:st(w,"submission","Prompt job submission failed.")})}},[c,l]),p=u.useCallback(async()=>{const _=i.current;if(!(!_||_.id==="submitting"))try{const y=await Qs(_.id);c(y,_.generation)}catch(y){a(m=>({...m,error:st(y,"cancellation","Prompt job cancellation failed.")}))}},[c]),g=u.useCallback(()=>{l(),r.current+=1,i.current=null,a({job:null,error:null})},[l]);return u.useEffect(()=>()=>{const _=i.current;l(),_&&_.id!=="submitting"&&Qs(_.id).catch(()=>{})},[l]),{...n,submit:d,cancel:p,reset:g,submitting:((b=i.current)==null?void 0:b.id)==="submitting"}}function ni({run:t,onRunReady:n}){var w,N,A,T,k,S;const[a,s]=u.useState(t.prompt),[i,r]=u.useState("plain"),[o,l]=u.useState(0),[c,d]=u.useState(128),[p,g]=u.useState(0),b=Wr(n),_=b.submitting||((w=b.job)==null?void 0:w.status)==="idle"||((N=b.job)==null?void 0:N.status)==="loading",y=nc(b.job,b.error,b.submitting),m=u.useMemo(()=>sc(t),[t]);function x(){const L=a.trim();!L||_||b.submit({prompt:L,template:i,model:t.modelName,seed:o,maxNewTokens:c,temperature:p,messages:[]})}return e.jsxs("section",{className:"panel-section prompt-runner-panel",children:[e.jsxs("div",{className:"section-heading",children:[e.jsx(Fo,{size:16}),e.jsx("span",{children:"Prompt runner"}),_&&e.jsxs("b",{children:[((A=b.job)==null?void 0:A.progress)??0,"%"]})]}),e.jsxs("label",{className:"prompt-runner-prompt",children:[e.jsx("span",{children:"Prompt"}),e.jsx("textarea",{"aria-label":"Prompt runner text","aria-describedby":a.trim()?void 0:"prompt-runner-required","aria-invalid":!a.trim()||void 0,value:a,maxLength:8e3,onChange:L=>s(L.target.value),disabled:_}),!a.trim()&&e.jsx("span",{id:"prompt-runner-required",className:"field-error",role:"alert",children:"Prompt text is required."})]}),e.jsxs("div",{className:"prompt-runner-grid",children:[e.jsxs("label",{children:[e.jsx("span",{children:"Template"}),e.jsxs("select",{"aria-label":"Prompt template",value:i,disabled:_,onChange:L=>r(L.target.value),children:[e.jsx("option",{value:"plain",children:"Plain"}),e.jsx("option",{value:"chat",children:"User / Assistant"})]})]}),e.jsxs("label",{children:[e.jsx("span",{children:"Seed"}),e.jsx("input",{"aria-label":"Generation seed",type:"number",min:0,max:2147483647,value:o,disabled:_,onChange:L=>l(ha(L.target.value,0,2147483647))})]}),e.jsxs("label",{children:[e.jsx("span",{children:"New tokens"}),e.jsx("input",{"aria-label":"Maximum new tokens",type:"number",min:1,max:512,value:c,disabled:_,onChange:L=>d(ha(L.target.value,1,512))})]}),e.jsxs("label",{children:[e.jsx("span",{children:"Temperature"}),e.jsx("input",{"aria-label":"Generation temperature",type:"number",min:0,max:2,step:.1,value:p,disabled:_,onChange:L=>g(ha(L.target.value,0,2))})]})]}),e.jsxs("div",{className:"prompt-runner-model",children:[e.jsx($t,{size:13}),e.jsx("span",{children:"Local model"}),e.jsx("strong",{children:t.modelName})]}),e.jsxs("div",{className:"prompt-runner-actions",children:[_?e.jsxs("button",{className:"prompt-cancel-button",onClick:()=>void b.cancel(),children:[e.jsx(Kt,{size:13})," Cancel"]}):e.jsxs("button",{className:"prompt-run-button",onClick:x,disabled:!a.trim(),children:[b.error?e.jsx(vn,{size:13}):e.jsx(Zn,{size:13}),b.error?"Retry analysis":"Run analysis"]}),(b.error||((T=b.job)==null?void 0:T.status)==="cancelled")&&e.jsx("button",{className:"prompt-reset-button","aria-label":"Reset prompt job",onClick:b.reset,children:e.jsx(Jn,{size:13})})]}),(b.job||b.submitting||b.error)&&e.jsxs(e.Fragment,{children:[e.jsx(tr,{status:y,label:ac(b.job,b.error,b.submitting),detail:((k=b.error)==null?void 0:k.message)??((S=b.job)==null?void 0:S.detail)??"Submitting the prompt job.",ariaLabel:"Prompt job status",onCancel:_?()=>void b.cancel():void 0,cancelLabel:"Cancel prompt job"}),e.jsx(Gl,{job:b.job,status:y,submitting:b.submitting,ariaLabel:"Prompt job progress",tone:"prompt"}),b.error&&e.jsx(tc,{failure:b.error,job:b.job,jobLabel:"Prompt job"})]}),m&&e.jsxs("details",{className:"prompt-run-provenance",children:[e.jsx("summary",{children:"Current generated run"}),e.jsxs("dl",{children:[e.jsxs("div",{children:[e.jsx("dt",{children:"Model"}),e.jsx("dd",{children:m.model})]}),e.jsxs("div",{children:[e.jsx("dt",{children:"Seed"}),e.jsx("dd",{children:m.seed})]}),e.jsxs("div",{children:[e.jsx("dt",{children:"Template"}),e.jsx("dd",{children:m.template})]}),e.jsxs("div",{children:[e.jsx("dt",{children:"Sampling"}),e.jsx("dd",{children:m.temperature>0?`T=${m.temperature}`:"greedy"})]})]})]})]})}function nc(t,n,a){return n?"error":a?"loading":(t==null?void 0:t.status)??"idle"}function ac(t,n,a){return n?n.title:a?"Submitting prompt job":t?t.status==="idle"?"Prompt job queued":t.status==="loading"?"Prompt job running":t.status==="ready"?"Prompt run ready":t.status==="cancelled"?"Prompt job cancelled":"Prompt job failed":"Prompt runner idle"}function ha(t,n,a){const s=Number(t);return Number.isFinite(s)?Math.max(n,Math.min(a,s)):n}function sc(t){var s;const n=(s=t.metadata)==null?void 0:s.promptRunner;if(!n||typeof n!="object"||Array.isArray(n))return null;const a=n;return typeof a.model!="string"||typeof a.seed!="number"?null:{model:a.model,seed:a.seed,template:typeof a.template=="string"?a.template:"plain",temperature:typeof a.temperature=="number"?a.temperature:0}}const ai=180,si=60;function ic({run:t,selectedToken:n,selectedLayer:a,selectedRange:s,setSelectedToken:i,setSelectedRange:r,hoveredToken:o,setHoveredToken:l,pulseToken:c,pinToken:d,pinned:p,timeline:g,onTimelineChange:b}){const[_,y]=u.useState(()=>window.matchMedia("(max-width: 760px)").matches?si:ai),{mode:m,metric:x,query:w}=g,N=u.useRef(null),A=u.useRef(null),T=u.useMemo(()=>rc(t.tokens,m),[m,t.tokens]),k=u.useMemo(()=>oc(t,a,x),[x,t,a]),S=Math.max(0,T.findIndex(R=>R.tokens.some(j=>j.index===n))),L=T.length<=_?0:Na(S-Math.floor(_/2),0,T.length-_),M=T.slice(L,L+_),F=w.trim().toLowerCase(),V=u.useMemo(()=>F.length===0?[]:T.filter(R=>li(R,F)),[T,F]),W=V.findIndex(R=>R.tokens.some(j=>j.index===n)),K=[{id:"risk",label:"Safety proxy"},{id:"attribution",label:"Attribution"},{id:"residual",label:"Residual norm"},{id:"nla",label:"NLA fidelity"},...t.tokens.some(R=>R.probeScore!==void 0)?[{id:"probe",label:"Probe score"}]:[]],H=u.useMemo(()=>dc(t,p),[p,t]),Z=new Set(T.flatMap(R=>ri(R,H))),D=cc(M);u.useEffect(()=>{const R=window.requestAnimationFrame(()=>{jt("timeline-ready",{tokens:t.tokens.length,items:T.length,renderedItems:M.length,mode:m})});return()=>window.cancelAnimationFrame(R)},[T.length,m,t.tokens.length,M.length]),u.useEffect(()=>{const R=window.matchMedia("(max-width: 760px)"),j=()=>y(R.matches?si:ai);return R.addEventListener("change",j),()=>R.removeEventListener("change",j)},[]),u.useLayoutEffect(()=>{var ee,ue;const R=A.current;if(!R)return;const j=(ee=N.current)==null?void 0:ee.querySelector(`[data-timeline-start="${R.start}"]`);j&&(j.focus(),A.current=null,(ue=R.onFocused)==null||ue.call(R))},[n,L]);function C(R,j){var ue,oe;const ee=R.tokens.some(O=>O.index===n)?n:(ue=R.tokens[0])==null?void 0:ue.index;if(ee!==void 0&&(A.current={start:R.start,onFocused:j},i(ee),ee===n)){const O=(oe=N.current)==null?void 0:oe.querySelector(`[data-timeline-start="${R.start}"]`);O&&(O.focus(),A.current=null,j==null||j())}}function ne(R){if(V.length===0)return;const ee=((W>=0?W:R>0?-1:0)+R+V.length)%V.length,ue=performance.now(),oe=V[ee];C(oe,()=>{jt("timeline-search-jump",{durationMs:performance.now()-ue,token:oe.start,tokens:t.tokens.length})})}function pe(R,j){const ee=T.findIndex(oe=>oe.key===R.key),ue=T[Na(ee+j,0,T.length-1)];ue&&C(ue)}return e.jsxs("section",{ref:N,className:"token-timeline-shell","aria-label":"Token timeline",children:[e.jsxs("div",{className:`token-timeline-toolbar${F?" has-query":""}`,children:[e.jsxs("label",{className:"timeline-search",children:[e.jsxs("span",{children:[e.jsx(Ut,{size:12})," Search",F&&e.jsxs("em",{className:"timeline-search-match-count",children:[V.length," ",V.length===1?"match":"matches"]})]}),e.jsxs("div",{children:[e.jsx("input",{id:"token-timeline-search",value:w,placeholder:"text, position, or token id","aria-label":"Search tokens",onChange:R=>b({...g,query:R.target.value})}),w&&e.jsx("button",{"aria-label":"Clear token search",onClick:()=>b({...g,query:""}),children:e.jsx(at,{size:13})})]})]}),e.jsxs("div",{className:"toolbar-segment","aria-label":"Timeline granularity",children:[e.jsx("button",{className:m==="token"?"active":"",onClick:()=>b({...g,mode:"token"}),children:"Token"}),e.jsxs("button",{className:m==="word"?"active":"",onClick:()=>b({...g,mode:"word"}),children:[e.jsx(Uo,{size:13})," Word"]})]}),e.jsxs("label",{className:"timeline-metric",children:[e.jsx("span",{children:"Color"}),e.jsx("select",{"aria-label":"Token color metric",value:x,onChange:R=>b({...g,metric:R.target.value}),children:K.map(R=>e.jsx("option",{value:R.id,children:R.label},R.id))})]}),e.jsxs("div",{className:"timeline-search-status","aria-label":"Token search results",children:[e.jsx("span",{children:F?`${V.length} matches`:`${T.length} ${m}s`}),e.jsx("button",{"aria-label":"Previous token search result",disabled:!V.length,onClick:()=>ne(-1),children:e.jsx(dn,{size:14})}),e.jsx("button",{"aria-label":"Next token search result",disabled:!V.length,onClick:()=>ne(1),children:e.jsx(gt,{size:14})})]})]}),Z.size>0&&e.jsx("div",{className:"timeline-marker-legend","aria-label":"Token evidence markers",children:zr.filter(R=>Z.has(R)).map(R=>e.jsxs("span",{children:[e.jsx("i",{className:`token-marker marker-${R}`,"data-marker":R,"data-shape":oi(R),"aria-hidden":"true"}),Dr(R)]},R))}),T.length>_&&e.jsxs("div",{className:"timeline-window-status","aria-label":"Timeline render window",children:[e.jsx("button",{"aria-label":"Previous token window",disabled:L===0,onClick:()=>C(T[Math.max(0,L-_)]),children:e.jsx(dn,{size:14})}),e.jsxs("span",{children:[L+1,"–",L+M.length," / ",T.length]}),e.jsx("button",{"aria-label":"Next token window",disabled:L+M.length>=T.length,onClick:()=>C(T[Math.min(T.length-1,L+_)]),children:e.jsx(gt,{size:14})})]}),e.jsx("div",{className:"timeline-groups",children:D.map(R=>e.jsxs("section",{className:`timeline-source-group source-${R.source}`,children:[e.jsxs("header",{children:[e.jsxs("div",{className:"timeline-source-identity",children:[e.jsx("span",{className:"timeline-source-icon","aria-hidden":"true",children:R.source==="prompt"?e.jsx(Ya,{size:14}):e.jsx(Ko,{size:14})}),e.jsxs("div",{children:[e.jsx("strong",{children:R.source==="prompt"?"User prompt":"Assistant reply"}),e.jsx("span",{children:R.source==="prompt"?"Input context":"Generated continuation"})]})]}),e.jsx(uc,{tokens:t.tokens,source:R.source})]}),e.jsx("div",{className:"token-timeline","aria-label":`${R.source} tokens`,children:R.items.map(j=>{const ee=j.tokens.find($=>$.index===n)??j.tokens[0],ue=lc(j,k),oe=ri(j,H),O=j.tokens.some($=>$.index===n),I=j.tokens.some($=>$.index===o),z=j.tokens.some($=>$.index===c),Y=s!==void 0&&j.end>=s[0]&&j.start<=s[1],q=F.length>0&&li(j,F);return e.jsxs("button",{"data-timeline-start":j.start,className:["token-pill",`metric-${x}`,O?"selected":"",I?"hovered":"",z?"pulse":"",Y?"in-range":"",q?"search-match":"",oe.includes("pinned")?"pinned":"",j.isSpecial?"special":"",ue.value===void 0?"metric-unavailable":""].join(" "),"aria-label":hc(j,ue.value,x,oe),"aria-keyshortcuts":"ArrowLeft ArrowRight Space Control+Enter Meta+Enter","aria-current":O?"true":void 0,tabIndex:O?0:-1,style:{"--signal":ue.signal},onClick:$=>{if($.metaKey||$.ctrlKey){d(ee.index);return}if($.shiftKey){r(fc(n,j.end));return}i(ee.index)},onDoubleClick:()=>d(ee.index),onKeyDown:$=>{if($.key===" "){$.preventDefault(),$.stopPropagation(),d(ee.index);return}$.key!=="ArrowLeft"&&$.key!=="ArrowRight"||($.preventDefault(),$.stopPropagation(),pe(j,$.key==="ArrowLeft"?-1:1))},onMouseEnter:()=>{const $=performance.now();l(ee.index),window.requestAnimationFrame(()=>{jt("timeline-hover",{durationMs:performance.now()-$,token:ee.index,tokens:t.tokens.length})})},onMouseLeave:()=>l(null),onFocus:()=>l(ee.index),onBlur:()=>l(null),children:[e.jsxs("span",{className:"token-pill-content",children:[e.jsx("b",{children:j.text||"␠"}),m==="word"&&j.tokens.length>1&&e.jsxs("em",{children:[j.tokens.length," tokens"]})]}),(j.isSpecial||j.generationStart!==void 0)&&e.jsxs("span",{className:"token-role-badges","aria-hidden":"true",children:[j.isSpecial&&e.jsx("span",{className:"token-role-badge special-badge",title:"Special token",children:"Special"}),j.generationStart!==void 0&&e.jsx("span",{className:"token-role-badge generation-badge",title:Yr(j),children:mc(j)})]}),e.jsx("i",{className:"token-value",children:ue.value===void 0?"n/a":qr(ue.value,x)}),oe.length>0&&e.jsx("small",{className:"token-marker-row","aria-hidden":"true",children:oe.map($=>e.jsx("i",{className:`token-marker marker-${$}`,"data-marker":$,"data-shape":oi($)},$))})]},j.key)})})]},R.source))})]})}function rc(t,n){const a=new Map;if(t.filter(i=>i.source==="reply").forEach((i,r)=>{a.set(i.index,i.generationStep??r)}),n==="token")return t.map(i=>ii([i],a));const s=[];for(const i of t){const r=s[s.length-1],o=/^\s/.test(i.text),l=(r==null?void 0:r.some(c=>c.isSpecial))??!1;!r||r[0].source!==i.source||i.isSpecial||l||o?s.push([i]):r.push(i)}return s.map(i=>ii(i,a))}function ii(t,n){const a=t[0],s=t[t.length-1]??a,i=t.map(o=>o.text).join("").trim(),r=t.flatMap(o=>{const l=n.get(o.index);return l===void 0?[]:[l]});return{key:`${a.source}:${a.index}-${s.index}`,tokens:t,text:i,normalizedText:i.toLowerCase(),source:a.source,start:a.index,end:s.index,generationStart:r[0],generationEnd:r[r.length-1],isSpecial:t.some(o=>o.isSpecial)}}function oc(t,n,a){const s=new Map,i=a==="residual"?new Map(t.residualCells.filter(d=>d.layer===n).map(d=>[d.tokenIndex,d.norm])):void 0,r=new Map;if(a==="nla")for(const d of t.nla){if(d.layer!==n||d.status==="unavailable")continue;const p=r.get(d.tokenIndex);(p===void 0||d.cosine>p)&&r.set(d.tokenIndex,d.cosine)}for(const d of t.tokens)a==="risk"&&s.set(d.index,d.risk),a==="attribution"&&s.set(d.index,d.attribution),a==="probe"&&s.set(d.index,d.probeScore),a==="residual"&&s.set(d.index,i==null?void 0:i.get(d.index)),a==="nla"&&s.set(d.index,r.get(d.index));const o=[...s.values()].filter(d=>d!==void 0),l=o.length?Math.min(...o):0,c=o.length?Math.max(...o):1;return new Map(t.tokens.map(d=>{const p=s.get(d.index),g=p===void 0?0:a==="risk"||a==="attribution"||a==="nla"?Na(p,0,1):yc(p,l,c);return[d.index,{value:p,signal:g}]}))}function lc(t,n){return t.tokens.reduce((a,s)=>{const i=n.get(s.index)??{value:void 0,signal:0};return i.signal>a.signal?i:a},n.get(t.tokens[0].index)??{value:void 0,signal:0})}function dc(t,n){return{nla:new Set(t.nla.filter(a=>a.status==="available").map(a=>a.tokenIndex)),pinned:new Set(n)}}function ri(t,n){const a=new Set;for(const s of t.tokens)s.risk>=.7&&a.add("risk"),Math.abs(s.attribution)>=.7&&a.add("attribution"),s.probeScore!==void 0&&a.add("probe"),s.monitorHit&&a.add("monitor"),n.pinned.has(s.index)&&a.add("pinned"),n.nla.has(s.index)&&a.add("nla");return zr.filter(s=>a.has(s))}const zr=["risk","attribution","nla","probe","monitor","pinned"];function Dr(t){return t==="risk"?"Safety proxy":t==="attribution"?"Attribution":t==="nla"?"NLA evidence":t==="probe"?"Probe":t==="monitor"?"Monitor":"Pinned"}function oi(t){return t==="risk"?"triangle":t==="attribution"?"diamond":t==="nla"?"ring":t==="probe"?"pentagon":t==="monitor"?"cross":"square"}function cc(t){return["prompt","reply"].map(a=>({source:a,items:t.filter(s=>s.source===a)})).filter(a=>a.items.length>0)}function uc({tokens:t,source:n}){const a=t.filter(c=>c.source===n),s=a[0],i=a[a.length-1],r=a.flatMap((c,d)=>n==="reply"?[c.generationStep??d]:[]),o=s&&i?s.index===i.index?`T${s.index}`:`T${s.index}–T${i.index}`:"No tokens",l=r.length>0?r[0]===r[r.length-1]?`G${r[0]}`:`G${r[0]}–G${r[r.length-1]}`:void 0;return e.jsxs("div",{className:"timeline-source-summary","aria-label":`${n==="prompt"?"Prompt":"Reply"} sequence summary`,children:[e.jsx("span",{children:o}),l&&e.jsx("span",{children:l}),e.jsxs("span",{children:[a.length," ",a.length===1?"token":"tokens"]})]})}function mc(t){return t.generationStart===void 0?"":t.generationEnd===void 0||t.generationEnd===t.generationStart?`G${t.generationStart}`:`G${t.generationStart}–${t.generationEnd}`}function Yr(t){return t.generationStart===void 0?"":t.generationEnd===void 0||t.generationEnd===t.generationStart?`Generation step ${t.generationStart}`:`Generation steps ${t.generationStart} to ${t.generationEnd}`}function li(t,n){const a=n.match(/^(?:token(?:-|:|#|\s)?|#)(\d+)$/),s=n.match(/^id(?::|#|\s)?(\d+)$/);return t.normalizedText.includes(n)||t.tokens.some(i=>String(i.index)===n||String(i.tokenId)===n||a!==null&&i.index===Number(a[1])||s!==null&&i.tokenId===Number(s[1]))}function hc(t,n,a,s){const i=t.start===t.end?`token ${t.start}`:`tokens ${t.start} to ${t.end}`,r=n===void 0?"unavailable":qr(n,a),l=[t.source==="prompt"?"user prompt":"assistant reply",t.isSpecial?"special token":void 0,t.generationStart!==void 0?Yr(t).toLowerCase():void 0,s.length>0?`evidence markers: ${s.map(Dr).join(", ")}`:void 0].filter(c=>c!==void 0).join(", ");return`${t.text||"blank"}, ${i}, ${l}, ${pc(a)} ${r}`}function pc(t){return t==="risk"?"safety proxy":t==="attribution"?"attribution":t==="residual"?"residual norm":t==="nla"?"NLA fidelity":"probe score"}function qr(t,n){return Ye(t,n==="risk"?"tokenRisk":n==="residual"?"residual_norm":n==="nla"?"nla_cosine":n,"compact")}function yc(t,n,a){return Math.abs(a-n)<1e-12?0:(t-n)/(a-n)}function fc(t,n){return t<=n?[t,n]:[n,t]}function Na(t,n,a){return Math.max(n,Math.min(a,t))}function di({evidence:t,canPrevious:n,canNext:a,canPin:s,pinned:i,nextActions:r,onPrevious:o,onNext:l,onPin:c,onCompare:d,onExport:p,onNextAction:g,detailLevel:b="full"}){const[_,y]=u.useState(null),m=u.useId(),x=t.status==="loading"||t.status==="cancelled",w=b==="full";async function N(A){const T=A==="cache"?t.cacheKey:JSON.stringify(t.reproduction,null,2);await navigator.clipboard.writeText(T),y(A),window.setTimeout(()=>y(k=>k===A?null:k),1e3)}return e.jsxs("section",{className:"inspector evidence-inspector","aria-label":"Evidence inspector",children:[e.jsxs("header",{className:"inspector-title",children:[e.jsxs("div",{className:"inspector-heading",children:[e.jsx(_c,{status:t.status}),e.jsxs("div",{children:[e.jsx("h2",{children:t.title}),e.jsx("p",{children:t.subtitle})]})]}),e.jsxs("div",{className:"inspector-nav",children:[e.jsx("button",{"aria-label":"Previous token",title:"Previous token",disabled:!n,onClick:o,children:e.jsx(dn,{size:15})}),e.jsx("button",{"aria-label":"Next token",title:"Next token",disabled:!a,onClick:l,children:e.jsx(gt,{size:15})})]})]}),e.jsxs("section",{className:"inspector-section inspector-summary-section","aria-labelledby":`${m}-summary`,children:[e.jsxs("div",{className:"inspector-section-heading",children:[e.jsx("h3",{id:`${m}-summary`,children:"Summary"}),e.jsx("span",{className:`evidence-status status-${t.status}`,children:bc(t.status)})]}),e.jsxs("div",{className:"inspector-primary-value",children:[e.jsx("span",{children:t.primaryLabel}),e.jsx("strong",{children:t.primaryValue}),e.jsx("em",{children:t.evidenceClass.replace("_"," ")})]}),e.jsx("p",{className:"inspector-status-reason",children:t.statusReason}),e.jsxs("div",{className:"inspector-value-grid",children:[e.jsxs("span",{children:[e.jsx("b",{children:t.rawValue}),"raw / stored"]}),e.jsxs("span",{children:[e.jsx("b",{children:t.displayValue}),"displayed"]}),e.jsxs("span",{children:[e.jsx("b",{children:t.units}),"units"]})]})]}),w&&e.jsxs("section",{className:"inspector-section","aria-labelledby":`${m}-evidence`,children:[e.jsxs("div",{className:"inspector-section-heading",children:[e.jsx("h3",{id:`${m}-evidence`,children:"Evidence"}),e.jsx("span",{children:t.shape})]}),e.jsxs("dl",{className:"inspector-provenance-list",children:[e.jsxs("div",{children:[e.jsx("dt",{children:"Method"}),e.jsx("dd",{children:t.method})]}),e.jsxs("div",{children:[e.jsx("dt",{children:"Normalization"}),e.jsx("dd",{children:t.normalization})]}),e.jsxs("div",{className:"inspector-cache-row",children:[e.jsx("dt",{children:"Cache key"}),e.jsxs("dd",{className:"inspector-cache-value",children:[e.jsx("span",{children:t.cacheKey}),e.jsx("button",{"aria-label":"Copy inspector cache key",disabled:x||!t.cacheKey,onClick:()=>void N("cache"),children:_==="cache"?e.jsx(Ft,{size:13}):e.jsx(qn,{size:13})})]})]}),e.jsxs("div",{children:[e.jsx("dt",{children:"Source artifact"}),e.jsx("dd",{children:t.sourceArtifact})]}),e.jsxs("div",{children:[e.jsx("dt",{children:"Run / sample"}),e.jsxs("dd",{children:[t.runId," / ",t.sampleId]})]}),e.jsxs("div",{children:[e.jsx("dt",{children:"Model"}),e.jsx("dd",{children:t.modelName})]})]}),t.warnings.length>0&&e.jsx("div",{className:"inspector-warning-list","aria-label":"Evidence warnings",children:t.warnings.map(A=>e.jsxs("p",{children:[e.jsx(ft,{size:13}),A]},A))})]}),e.jsxs("section",{className:"inspector-section inspector-actions-section","aria-labelledby":`${m}-actions`,children:[e.jsx("div",{className:"inspector-section-heading",children:e.jsx("h3",{id:`${m}-actions`,children:"Actions"})}),e.jsxs("div",{className:"inspector-actions",children:[e.jsxs("button",{className:i?"active":"",disabled:!s,"aria-label":i?"Unpin inspector evidence":"Pin inspector evidence",onClick:c,children:[e.jsx(Gn,{size:14}),i?"Unpin":"Pin"]}),e.jsxs("button",{disabled:x,onClick:d,children:[e.jsx(yt,{size:14}),"Compare"]}),e.jsxs("button",{disabled:x,"aria-label":"Copy reproducible evidence context",onClick:()=>void N("reproduction"),children:[_==="reproduction"?e.jsx(Ft,{size:14}):e.jsx(Oo,{size:14}),"Context"]}),e.jsxs("button",{disabled:x,onClick:p,children:[e.jsx(qa,{size:14}),"Export"]})]}),w&&r.length>0&&e.jsxs("div",{className:"inspector-next-actions","aria-label":"Recommended next analysis",children:[e.jsxs("div",{children:[e.jsx("strong",{children:"Recommended next analysis"}),e.jsx("span",{children:t.status==="available"?"Strengthen or challenge this evidence.":"Resolve the current evidence gap."})]}),r.map(A=>e.jsxs("button",{type:"button",className:`next-action-${A.kind}`,onClick:()=>g(A.id),children:[e.jsx(gc,{kind:A.kind}),e.jsxs("span",{children:[e.jsx("b",{children:A.label}),A.description]}),e.jsx(gt,{size:14})]},A.id))]})]})]})}function gc({kind:t}){return t==="attribution"?e.jsx(Be,{size:15}):t==="nla"?e.jsx(dt,{size:15}):t==="patching"?e.jsx(Yt,{size:15}):t==="intervention"?e.jsx($t,{size:15}):e.jsx(Ha,{size:15})}function _c({status:t}){return t==="loading"||t==="cancelled"?e.jsx(Oi,{size:18}):t==="available"?e.jsx(ot,{size:18}):e.jsx(ft,{size:18})}function bc(t){return t==="available"?"available":t==="not-computed"?"not computed":t==="loading"?"loading":t}const Hr=u.createContext(0),xc=12e3;function mt(t,n){const a=new Map;function s(){const o=xc;return new Promise((l,c)=>{const d=window.setTimeout(()=>{c(new Error(`Lazy module ${String(n)} timed out after ${o}ms`))},o);t().then(p=>{window.clearTimeout(d),l(p)},p=>{window.clearTimeout(d),c(p)})})}function i(o){const l=a.get(o);if(l)return l;const c=Le.lazy(()=>s().then(d=>({default:d[n]})));return a.set(o,c),c}function r(o){const l=u.useContext(Hr),c=i(l);return Le.createElement(c,o)}return r.displayName="RetryableLazyComponent",r}class ci extends Le.Component{constructor(){super(...arguments);nn(this,"state",{error:null,retry:0,componentStack:"",copyStatus:"idle",errorResetKey:null});nn(this,"fallbackRef",Le.createRef());nn(this,"retryView",()=>{this.setState(a=>({error:null,retry:a.retry+1,componentStack:"",copyStatus:"idle",errorResetKey:null}))});nn(this,"copyDiagnostics",async()=>{const a=this.state.error;if(!a)return;const s={schemaVersion:"1.0",kind:this.props.variant==="dialog"?"safelens-dialog-render-error":"safelens-view-render-error",view:this.props.viewLabel,context:this.props.resetKey,error:{name:a.name,message:a.message},componentStack:this.state.componentStack.trim(),location:window.location.href,userAgent:navigator.userAgent,capturedAt:new Date().toISOString()};try{await navigator.clipboard.writeText(JSON.stringify(s,null,2)),this.setState({copyStatus:"copied"})}catch{this.setState({copyStatus:"failed"})}});nn(this,"handleDialogKeyDown",a=>{var l,c;if(a.key==="Escape"){a.preventDefault(),(c=(l=this.props).onDismiss)==null||c.call(l);return}if(a.key!=="Tab")return;const s=this.fallbackRef.current;if(!s)return;const i=Array.from(s.querySelectorAll("button:not(:disabled), summary, [href], [tabindex]:not([tabindex='-1'])"));if(i.length===0)return;const r=i[0],o=i[i.length-1];a.shiftKey&&(document.activeElement===r||document.activeElement===s)?(a.preventDefault(),o.focus()):!a.shiftKey&&document.activeElement===o&&(a.preventDefault(),r.focus())})}static getDerivedStateFromError(a){return{error:a}}componentDidCatch(a,s){this.setState({componentStack:s.componentStack??"",errorResetKey:this.props.resetKey}),window.requestAnimationFrame(()=>{var i;return(i=this.fallbackRef.current)==null?void 0:i.focus()})}componentDidUpdate(){this.state.error&&this.state.errorResetKey!==null&&this.state.errorResetKey!==this.props.resetKey&&this.setState({error:null,retry:0,componentStack:"",copyStatus:"idle",errorResetKey:null})}render(){return this.state.error?this.props.variant==="dialog"?e.jsx("div",{className:"compare-backdrop",onMouseDown:a=>{var s,i;a.target===a.currentTarget&&((i=(s=this.props).onDismiss)==null||i.call(s))},children:e.jsxs("aside",{ref:this.fallbackRef,className:"compare-drawer compare-error-drawer",role:"dialog","aria-modal":"true","aria-label":`${this.props.viewLabel} error`,tabIndex:-1,onKeyDown:this.handleDialogKeyDown,children:[e.jsxs("header",{className:"compare-error-heading",children:[e.jsx(ft,{size:20}),e.jsxs("div",{children:[e.jsxs("strong",{children:[this.props.viewLabel," could not be opened"]}),e.jsx("span",{children:"The workspace and pinned evidence are unchanged."})]}),e.jsx("button",{"aria-label":`Close ${this.props.viewLabel.toLowerCase()} error`,onClick:this.props.onDismiss,children:e.jsx(at,{size:18})})]}),e.jsxs("details",{className:"compare-error-detail",children:[e.jsx("summary",{children:"Technical detail"}),e.jsxs("code",{children:[this.state.error.name,": ",this.state.error.message]}),e.jsx("small",{children:this.props.resetKey})]}),e.jsxs("div",{className:"compare-error-actions",children:[e.jsxs("button",{onClick:this.retryView,children:[e.jsx(vn,{size:14})," Retry comparison"]}),e.jsxs("button",{onClick:this.props.onDismiss,children:[e.jsx(at,{size:14})," Close"]}),e.jsxs("button",{"aria-live":"polite",onClick:()=>void this.copyDiagnostics(),children:[this.state.copyStatus==="copied"?e.jsx(Ft,{size:14}):e.jsx(qn,{size:14}),this.state.copyStatus==="copied"?"Copied":this.state.copyStatus==="failed"?"Copy failed":"Copy diagnostics"]})]})]})}):e.jsxs("section",{ref:this.fallbackRef,className:"view-error-state",role:"alert","aria-label":`${this.props.viewLabel} view error`,tabIndex:-1,children:[e.jsx(ft,{size:20}),e.jsxs("div",{children:[e.jsxs("strong",{children:[this.props.viewLabel," could not be rendered"]}),e.jsx("span",{children:"Your run, token selection, Timeline, pins, and Inspector are unchanged."}),e.jsxs("details",{children:[e.jsx("summary",{children:"Technical detail"}),e.jsxs("code",{children:[this.state.error.name,": ",this.state.error.message]}),e.jsx("small",{children:this.props.resetKey})]})]}),e.jsxs("div",{className:"view-error-actions",children:[e.jsxs("button",{onClick:this.retryView,children:[e.jsx(vn,{size:14})," Retry view"]}),e.jsxs("button",{onClick:this.props.onOpenOverview,disabled:!this.props.onOpenOverview,children:[e.jsx(Ha,{size:14})," Open Overview"]}),e.jsxs("button",{"aria-live":"polite",onClick:()=>void this.copyDiagnostics(),children:[this.state.copyStatus==="copied"?e.jsx(Ft,{size:14}):e.jsx(qn,{size:14}),this.state.copyStatus==="copied"?"Copied":this.state.copyStatus==="failed"?"Copy failed":"Copy diagnostics"]})]})]}):e.jsx(Hr.Provider,{value:this.state.retry,children:e.jsx(Le.Fragment,{children:this.props.children},this.state.retry)})}}function wc({run:t,selectedToken:n,selectedLayer:a,residualCell:s,onNavigate:i}){var y;const r=t.tokens.find(m=>m.index===n)??t.tokens[0],o=[...t.tokens].sort((m,x)=>x.risk-m.risk||m.index-x.index).findIndex(m=>m.index===r.index)+1,l=kc(t,r.index,a,s),c=l.filter(m=>m.direction==="supporting"),d=l.filter(m=>m.direction==="contradicting"),p=(y=t.patching)==null?void 0:y.cells.find(m=>m.layer===a&&m.tokenIndex===r.index),g=t.attributionMethods.find(m=>m.available),b=["The safety-direction score is run-relative and is not a calibrated probability of unsafe behavior.",p?"The causal patch result is local to one corruption, component, layer, and token.":"No exact causal patch result is available for this token and layer.",g?`${g.label} is available, but target and baseline choices still bound its interpretation.`:"No target-specific attribution method has been computed for this run."],_=[{view:"residual",label:"Inspect residual trajectory",detail:"Check whether direction alignment persists across layers."},{view:"attribution",label:g?"Inspect signed attribution":"Run target attribution",detail:g?`Open ${g.label} at this token.`:"Compute a target-specific method and baseline."},{view:"patching",label:p?"Inspect causal recovery":"Run causal patching",detail:p?"Review the exact patched score and recovery percentage.":"Test whether replacing this activation changes the target metric."}];return e.jsxs("section",{className:"surface overview-evidence-map","aria-labelledby":"overview-evidence-map-title",children:[e.jsxs("div",{className:"surface-header overview-evidence-heading",children:[e.jsxs("div",{children:[e.jsx("h3",{id:"overview-evidence-map-title",children:"Evidence map"}),e.jsxs("p",{children:[mi(r.text)," · token ",r.index," · layer ",a]})]}),e.jsxs("span",{className:"overview-confidence",children:[e.jsx(Ht,{size:13})," exploratory"]})]}),e.jsxs("div",{className:"overview-graph","aria-label":"Evidence graph",children:[e.jsx(ui,{id:"overview-supporting-title",label:"Supporting evidence",tone:"supporting",nodes:c,empty:"No loaded measure currently supports this proxy direction.",onNavigate:i}),e.jsxs("article",{className:"overview-primary-finding","aria-labelledby":"overview-primary-title",children:[e.jsx("span",{children:"Primary finding"}),e.jsxs("h4",{id:"overview-primary-title",children:["Token ",r.index," ranks ",o," of ",t.tokens.length," by run-relative safety-direction proxy."]}),e.jsxs("p",{children:["Score ",r.risk.toFixed(3)," is exploratory derived evidence. It locates a candidate for analysis; it does not establish unsafe behavior or causality."]}),e.jsxs("dl",{children:[e.jsxs("div",{children:[e.jsx("dt",{children:"Evidence class"}),e.jsx("dd",{children:"derived proxy"})]}),e.jsxs("div",{children:[e.jsx("dt",{children:"Confidence"}),e.jsx("dd",{children:"exploratory"})]}),e.jsxs("div",{children:[e.jsx("dt",{children:"Token"}),e.jsxs("dd",{children:[mi(r.text)," · id ",r.tokenId]})]})]})]}),e.jsx(ui,{id:"overview-contradicting-title",label:"Contradicting evidence",tone:"contradicting",nodes:d,empty:"No contradictory measure is loaded; absence is not confirmation.",onNavigate:i})]}),e.jsxs("div",{className:"overview-followup-grid",children:[e.jsxs("section",{className:"overview-limitations","aria-labelledby":"overview-limitations-title",children:[e.jsxs("header",{children:[e.jsx(Lt,{size:16}),e.jsx("h4",{id:"overview-limitations-title",children:"Limitations"})]}),e.jsx("ul",{children:b.map(m=>e.jsx("li",{children:m},m))})]}),e.jsxs("section",{className:"overview-recommendations","aria-labelledby":"overview-recommendations-title",children:[e.jsxs("header",{children:[e.jsx(Sn,{size:16}),e.jsx("h4",{id:"overview-recommendations-title",children:"Recommended analysis"})]}),e.jsx("div",{children:_.map(m=>e.jsxs("button",{onClick:()=>i(m.view),children:[e.jsxs("span",{children:[e.jsx("strong",{children:m.label}),e.jsx("small",{children:m.detail})]}),m.view==="patching"?e.jsx(Yt,{size:15}):e.jsx(ea,{size:15})]},m.view))})]})]})]})}function ui({id:t,label:n,tone:a,nodes:s,empty:i,onNavigate:r}){return e.jsxs("section",{className:`overview-evidence-column ${a}`,"aria-labelledby":t,children:[e.jsxs("header",{children:[e.jsx(Bo,{size:14}),e.jsx("h4",{id:t,children:n}),e.jsx("span",{children:s.length})]}),e.jsx("div",{children:s.length>0?s.map(o=>e.jsxs("button",{className:"overview-evidence-node",onClick:()=>r(o.view),children:[e.jsx("span",{children:vc(o.evidenceClass)}),e.jsx("strong",{children:o.label}),e.jsx("b",{children:o.value}),e.jsx("small",{children:o.detail})]},o.id)):e.jsx("div",{className:"overview-evidence-empty",role:"status",children:i})})]})}function kc(t,n,a,s){var l,c;const i=t.tokens.find(d=>d.index===n)??t.tokens[0],r=[];s&&r.push({id:"residual-direction",label:"Residual direction",value:s.riskDirection.toFixed(3),detail:`Normalized resid_post alignment at L${a}; grouped against the 0.5 midpoint.`,evidenceClass:"derived_proxy",view:"residual",direction:s.riskDirection>=.5?"supporting":"contradicting"}),r.push({id:"token-attribution",label:"Attention proxy",value:i.attribution.toFixed(3),detail:"Run-relative descriptive signal grouped against the 0.5 midpoint; not causal attribution.",evidenceClass:"derived_proxy",view:"attribution",direction:i.attribution>=.5?"supporting":"contradicting"});const o=(l=t.patching)==null?void 0:l.cells.find(d=>d.layer===a&&d.tokenIndex===n);return o&&r.push({id:"causal-patching",label:"Activation patch effect",value:jc(o.causalEffect),detail:`Exact ${(c=t.patching)==null?void 0:c.component} replacement; direction follows the causal-effect sign.`,evidenceClass:"causal",view:"patching",direction:o.causalEffect>0?"supporting":"contradicting"}),r}function vc(t){return t==="derived_proxy"?"derived proxy":t==="safety_method"?"safety output":t==="causal"?"causal evidence":"raw"}function jc(t){return`${t>0?"+":""}${t.toFixed(3)}`}function mi(t){return t.trim()?t:"space"}function Ic({open:t,returnFocusRef:n,context:a,pinnedCount:s,onClose:i,onOverview:r,onRuns:o,onTokenSearch:l,onCompare:c,onExportSession:d,onExportArtifact:p,onExportEvidence:g}){const b=u.useRef(null),_=u.useRef(null),y=u.useRef(!0);if(Un({open:t,dialogRef:b,initialFocusRef:_,returnFocusRef:n,restoreFocusRef:y,onClose:i}),!t)return null;return e.jsx("div",{className:"quick-actions-backdrop",onMouseDown:x=>{x.target===x.currentTarget&&i()},children:e.jsxs("aside",{ref:b,className:"quick-actions-dialog",role:"dialog",tabIndex:-1,"aria-modal":"true","aria-labelledby":"quick-actions-title",children:[e.jsxs("header",{children:[e.jsxs("div",{children:[e.jsx("span",{children:"Global workspace"}),e.jsx("h2",{id:"quick-actions-title",children:"Quick actions"})]}),e.jsx("button",{ref:_,"aria-label":"Close quick actions",onClick:i,children:e.jsx(at,{size:18})})]}),e.jsxs("div",{className:"quick-actions-context","aria-label":"Current quick action context",children:[e.jsxs("span",{children:[e.jsx("b",{children:a.runId}),e.jsx("small",{children:"run"})]}),e.jsxs("span",{children:[e.jsx("b",{children:a.sampleId}),e.jsx("small",{children:"sample"})]}),e.jsxs("span",{children:[e.jsx("b",{children:a.view}),e.jsx("small",{children:"view"})]}),e.jsxs("span",{children:[e.jsxs("b",{children:["L",a.layer]}),e.jsx("small",{children:"layer"})]}),e.jsxs("span",{children:[e.jsx("b",{children:a.tokenText||`T${a.token}`}),e.jsxs("small",{children:["token ",a.token]})]})]}),e.jsxs("div",{className:"quick-actions-list","aria-label":"Available quick actions",children:[e.jsx(zt,{icon:e.jsx(Ha,{size:17}),label:"Open Overview",detail:"Evidence map",onClick:m(r)}),e.jsx(zt,{icon:e.jsx(Ut,{size:17}),label:"Find a token",detail:"Timeline search",onClick:m(l)}),e.jsx(zt,{icon:e.jsx(vt,{size:17}),label:"Runs and samples",detail:"Run Library",onClick:m(o)}),e.jsx(zt,{icon:e.jsx(yt,{size:17}),label:"Compare pinned evidence",detail:s?`${s} item${s===1?"":"s"} ready`:"Pin evidence first",disabled:!s,onClick:m(c)}),e.jsx(zt,{icon:e.jsx(Vi,{size:17}),label:"Export analysis session",detail:"Session JSON",onClick:m(d)}),e.jsx(zt,{icon:e.jsx(Da,{size:17}),label:"Export Explorer artifact",detail:"Run JSON",onClick:m(p)}),e.jsx(zt,{icon:e.jsx(qa,{size:17}),label:"Export current evidence",detail:"Evidence JSON",onClick:m(g)})]})]})});function m(x){return()=>{y.current=!1,x()}}}function zt({icon:t,label:n,detail:a,disabled:s,onClick:i}){return e.jsxs("button",{disabled:s,onClick:i,children:[e.jsx("i",{"aria-hidden":"true",children:t}),e.jsxs("span",{children:[e.jsx("b",{children:n}),e.jsx("small",{children:a})]})]})}function wn({icon:t,title:n,description:a,facts:s,actionLabel:i,actionIcon:r,onAction:o,className:l="",compact:c=!1}){return e.jsxs("section",{className:`analysis-empty actionable-empty ${c?"compact":""} ${l}`.trim(),"aria-label":n,children:[e.jsx("span",{className:"empty-icon","aria-hidden":"true",children:t}),e.jsx("strong",{children:n}),e.jsx("p",{children:a}),e.jsx("dl",{className:"actionable-empty-facts",children:s.map(d=>e.jsxs("div",{children:[e.jsx("dt",{children:d.label}),e.jsx("dd",{children:d.value})]},`${d.label}:${d.value}`))}),e.jsxs("button",{type:"button",className:"actionable-empty-primary",onClick:o,children:[r,e.jsx("span",{children:i}),e.jsx(gt,{size:15,"aria-hidden":"true"})]})]})}const Sc=/<\|(?:im_start|im_end|endoftext|eot_id)\|>/i,Tc=/(?:\r?\n|([.!?。！？])\s+)(?:User|用户)\s*:(?=[\s\S]{0,4000}(?:Assistant|助手)\s*:)/i;function Ga(t){var c,d,p;const n=(c=t.metadata)==null?void 0:c.generatedContinuation;if(typeof n!="string"||!n.trim())return"";const a=(d=t.metadata)==null?void 0:d.generation,s=a&&typeof a=="object"&&!Array.isArray(a)?a:void 0,i=(s==null?void 0:s.outputFormat)==="continuation_only"||typeof(s==null?void 0:s.generatedTokenCount)=="number",r=(p=t.metadata)==null?void 0:p.promptRunner,o=r&&typeof r=="object"&&!Array.isArray(r)?r.userPrompt:void 0;let l=n.trim();if(!i){const b=[t.prompt,typeof o=="string"?o:""].filter(Boolean).sort((_,y)=>y.length-_.length).find(_=>l.startsWith(_));b&&(l=l.slice(b.length).trim())}return l=l.replace(/^(?:Assistant|助手)\s*:\s*/i,""),Ac(l)}function Ac(t){var i;let n=t.trim();const a=n.search(Sc);a>=0&&(n=n.slice(0,a));const s=Tc.exec(n);return(s==null?void 0:s.index)!==void 0&&(n=n.slice(0,s.index+(((i=s[1])==null?void 0:i.length)??0))),n.trim()}function Ca(){const t=globalThis.crypto;let n;if(typeof(t==null?void 0:t.randomUUID)=="function")n=t.randomUUID();else if(typeof(t==null?void 0:t.getRandomValues)=="function"){const a=new Uint8Array(16);t.getRandomValues(a),a[6]=a[6]&15|64,a[8]=a[8]&63|128,n=[...a].map((s,i)=>{const r=i===3||i===5||i===7||i===9?"-":"";return`${s.toString(16).padStart(2,"0")}${r}`}).join("")}else n=[Date.now().toString(36),Math.random().toString(36).slice(2),Math.random().toString(36).slice(2)].join("-");return n}function Nc({model:t,maxNewTokens:n,conversationId:a,onConversationStart:s,onRunReady:i}){const[r,o]=u.useState([]),[l,c]=u.useState(null),d=u.useRef([]);d.current=r;const p=u.useRef(a);p.current=a;const g=u.useRef(null);g.current=l;function b(T,k){return T.filter(S=>S.id!==k&&S.run&&S.status==="ready").flatMap(S=>{const L=Ga(S.run);return L?[{role:"user",content:S.prompt},{role:"assistant",content:L}]:[]})}const _=u.useCallback((T,k)=>{const S=g.current;if(!S)return;const L=d.current.findIndex(V=>V.id===S),M=p.current,F={...T,metadata:{...T.metadata,...M?{conversationId:M}:{},...L>=0?{turnIndex:L}:{}}};o(V=>V.map(W=>W.id===S?{...W,run:F,status:"ready",jobId:k.id}:W)),c(null),i(F,k,S)},[i]),y=Wr(_);u.useEffect(()=>{if(!y.error||!l)return;const T=y.error.message;o(k=>k.map(S=>S.id===l?{...S,status:"error",errorMessage:T}:S)),c(null)},[l,y.error]),u.useEffect(()=>{!y.job||!l||o(T=>T.map(k=>k.id===l?{...k,jobId:y.job.id,jobProgress:y.job.progress,jobStage:y.job.stage,jobDetail:y.job.detail}:k))},[l,y.job]),u.useEffect(()=>{!y.job||!l||y.job.status==="cancelled"&&(o(T=>T.map(k=>k.id===l?{...k,status:"cancelled"}:k)),c(null))},[l,y.job]);const m=u.useCallback(T=>{if(g.current)return;const k=!!p.current,S=p.current??Ca();p.current=S,k||s(S);const L=b(r),M={id:Ca(),prompt:T,run:null,jobId:null,jobProgress:0,jobStage:"queued",jobDetail:"Waiting for the local model worker.",status:"pending",startedAt:new Date().toISOString()};o(F=>[...F,M]),g.current=M.id,c(M.id),y.submit({prompt:T,template:"chat",model:t,seed:0,maxNewTokens:n,temperature:0,messages:L})},[a,n,t,s,y,r]),x=u.useCallback(T=>{g.current===T&&y.cancel()},[y]),w=u.useCallback(T=>{if(g.current)return;const k=r.find(L=>L.id===T);if(!k||k.status==="pending")return;o(L=>L.map(M=>M.id===T?{...M,status:"pending",errorMessage:void 0,run:null}:M)),g.current=T,c(T);const S=r.findIndex(L=>L.id===T);y.submit({prompt:k.prompt,template:"chat",model:t,seed:0,maxNewTokens:n,temperature:0,messages:b(r.slice(0,Math.max(0,S)),T)})},[n,t,y,r]),N=u.useCallback(()=>{y.reset(),g.current=null,o([]),c(null)},[y]),A=u.useCallback((T,k)=>{y.reset(),g.current=null,o(T),c(null),s(k)},[s,y]);return{turns:r,activeTurnId:l,submit:m,cancel:x,retry:w,reset:N,hydrate:A}}const pa=512;function Cc(t){const n=Al.safeParse(t.base);if(!n.success){const s=n.error.issues[0];throw new Error(`Chunk metadata core failed at ${(s==null?void 0:s.path.join("."))||"base"}: ${(s==null?void 0:s.message)||"invalid core"}.`)}if(n.data.runId!==t.runId||n.data.sampleId!==t.sampleId)throw new Error("Chunk metadata core does not match its run/sample envelope.");const a=n.data.layers[n.data.layers.length-1]??0;return{...n.data,attentionHeads:[{id:"__chunk_pending__",layer:a,head:0,role:"component data loading",riskContribution:0,entropy:0,distributionByToken:[]}],mlpNeurons:[],residualCells:[],logitLens:[],jLens:[],attentionCells:[],mlpCells:[],attributionTracks:[],attributionMethods:[{id:"__chunk_pending__",label:"Component data loading",description:"The selected attribution chunk has not loaded yet.",evidenceKind:"raw",signed:!1,normalization:"not loaded",available:!1,unavailableReason:"Component data is loading; this is not an unavailable evidence result.",rows:[]}],nla:[]}}function gn(t,n,a,s=a){const{start:i,end:r}=Kn(a),o=["attention","mlp"].includes(t)?`:L${n}`:"",l=Kn(s),c=t==="attention"?`:S${l.start}-${l.end}`:"";return`${t}${o}:T${i}-${r}${c}`}function hi(t,n,a,s,i=s){return!t||t.mode==="full"||t.loadedScopes.includes(gn(n,a,s,i))}function Rc(t,n,a,s,i=a){const r=Kn(a,s),o={tokenStart:r.start,tokenEnd:r.end};if(t==="overview")return[{component:"residualCells",...o},{component:"logitLens",...o}];if(t==="residual")return[{component:"residualCells",...o},{component:"logitLens",...o}];if(t==="attention"){const l=Kn(i,s);return[{component:"attentionHeads",layer:n,...o,sourceStart:l.start,sourceEnd:l.end},{component:"attentionCells",layer:n,...o},{component:"residualCells",...o}]}return t==="mlp"?[{component:"mlpNeurons",layer:n,...o},{component:"mlpCells",layer:n,...o},{component:"residualCells",...o}]:t==="attribution"?[{component:"attributionMethods",...o},{component:"attributionTracks",...o},{component:"residualCells",...o}]:t==="nla"?[{component:"nla",...o},{component:"residualCells",...o}]:t==="patching"?[{component:"patching",...o}]:[{component:"intervention",...o}]}async function pi(t,n,a,s,i,r,o=i){return(await Fr(t,n,a,s,i,r,o)).reduce((c,d)=>Xa(c,d),t)}async function Fr(t,n,a,s,i,r,o=i){const l=Rc(a,s,i,t.tokens.length,o);return await Promise.all(l.map(d=>gr(n,d,r)))}function Xa(t,n){if(n.component==="residualCells")return{...t,residualCells:hn(t.residualCells,Pc.parse(n.data))};if(n.component==="logitLens")return{...t,logitLens:hn(t.logitLens,Wc.parse(n.data))};if(n.component==="jLens")return{...t,jLens:hn(t.jLens,G(or).parse(n.data))};if(n.component==="attentionCells")return{...t,attentionCells:hn(t.attentionCells,yi.parse(n.data))};if(n.component==="mlpCells")return{...t,mlpCells:hn(t.mlpCells,yi.parse(n.data))};if(n.component==="nla"){const a=zc.parse(n.data),s=new Map(t.nla.map(i=>[`${i.layer}:${i.component}:${i.tokenIndex}`,i]));for(const i of a)s.set(`${i.layer}:${i.component}:${i.tokenIndex}`,i);return{...t,nla:[...s.values()]}}return n.component==="attentionHeads"?Lc(t,n.data):n.component==="mlpNeurons"?$c(t,n.data):n.component==="attributionTracks"?Ec(t,n.data):n.component==="attributionMethods"?Mc(t,n.data):n.component==="patching"?{...t,patching:n.data}:{...t,intervention:n.data}}function Lc(t,n){const a=Dc.parse(n),s=new Map(t.attentionHeads.filter(i=>i.id!=="__chunk_pending__").map(i=>[i.id,i]));for(const i of a){const r=s.get(i.id),o=(r==null?void 0:r.distributionByToken.map(d=>d.slice()))??Array.from({length:t.tokens.length},()=>[]);i.distributionByToken.forEach((d,p)=>{var _;const g=i.chunk.destinationStart+p,b=((_=o[g])==null?void 0:_.slice())??[];d.forEach((y,m)=>{b[i.chunk.sourceStart+m]=y}),o[g]=b});const{chunk:l,...c}=i;s.set(i.id,{...c,distributionByToken:o})}return{...t,attentionHeads:[...s.values()]}}function $c(t,n){const a=Yc.parse(n),s=new Map(t.mlpNeurons.map(i=>[i.id,i]));for(const i of a){const r=s.get(i.id),o=(r==null?void 0:r.activationsByToken.slice())??[];i.activationsByToken.forEach((d,p)=>{o[i.chunk.tokenStart+p]=d});const{chunk:l,...c}=i;s.set(i.id,{...c,activationsByToken:o})}return{...t,mlpNeurons:[...s.values()]}}function Ec(t,n){var i;const a=qc.parse(n),s=new Map(t.attributionTracks.map(r=>[r.name,r]));for(const r of a){const o=((i=s.get(r.name))==null?void 0:i.values.slice())??[];r.values.forEach((l,c)=>{o[r.chunk.tokenStart+c]=l}),s.set(r.name,{name:r.name,values:o})}return{...t,attributionTracks:[...s.values()]}}function Mc(t,n){var i;const a=Hc.parse(n),s=new Map(t.attributionMethods.filter(r=>r.id!=="__chunk_pending__").map(r=>[r.id,r]));for(const r of a){const o=s.get(r.id),l=new Map((o==null?void 0:o.rows.map(c=>[c.layer,c]))??[]);for(const c of r.rows){const d=((i=l.get(c.layer))==null?void 0:i.values.slice())??[];c.values.forEach((b,_)=>{d[c.chunk.tokenStart+_]=b});const{chunk:p,...g}=c;l.set(g.layer,{...g,values:d})}s.set(r.id,{...r,rows:[...l.values()]})}return{...t,attributionMethods:[...s.values()]}}function hn(t,n){const a=new Map(t.map(s=>[`${s.layer}:${s.tokenIndex}`,s]));for(const s of n)a.set(`${s.layer}:${s.tokenIndex}`,s);return[...a.values()]}function Kn(t,n=Number.MAX_SAFE_INTEGER){const a=Math.floor(Math.max(0,t)/pa)*pa;return{start:a,end:Math.min(n,a+pa)}}const Pc=G(B({layer:f().int().nonnegative(),tokenIndex:f().int().nonnegative(),norm:f(),rawDirection:f(),riskDirection:f(),semanticDensity:f()})),yi=G(B({layer:f().int().nonnegative(),tokenIndex:f().int().nonnegative(),value:f(),rawValue:f(),metric:h(),sourceKey:h()})),Wc=G(B({layer:f().int().nonnegative(),tokenIndex:f().int().nonnegative(),targetTokenId:f().int(),targetTokenText:h(),targetLogit:f(),targetProbability:f(),targetRank:f().int(),sourceKey:h(),topPredictions:G(B({tokenId:f().int(),tokenText:h(),logit:f(),probability:f()}))})),zc=G(B({tokenIndex:f().int().nonnegative(),layer:f().int().nonnegative(),component:ye(["resid_post","attn_result","mlp_out"]),explanation:h(),cosine:f(),mse:f(),fve:f().optional(),activationNorm:f(),status:ye(["available","unavailable"]).optional(),profile:h().nullable().optional(),source:h().optional(),token:h().optional()})),Za=B({tokenStart:f().int(),tokenEnd:f().int()}),Dc=G(B({id:h(),layer:f().int(),head:f().int(),role:h(),riskContribution:f(),entropy:f(),distributionByToken:G(G(f())),chunk:B({destinationStart:f().int(),destinationEnd:f().int(),sourceStart:f().int(),sourceEnd:f().int()})})),Yc=G(B({id:h(),layer:f().int(),neuron:f().int(),label:h(),activation:f(),riskContribution:f(),topTokens:G(f().int()),positiveTopTokens:G(f().int()),negativeTopTokens:G(f().int()),activationsByToken:G(f()),maxAbsoluteActivation:f(),chunk:Za})),qc=G(B({name:h(),values:G(f()),chunk:Za})),Hc=G(B({id:h(),label:h(),description:h(),evidenceKind:ye(["raw","derived_proxy","safety_method","causal"]),signed:fe(),normalization:h(),available:fe(),unavailableReason:h().optional(),rows:G(B({layer:f().int(),label:h(),values:G(f()),sourceKey:h(),chunk:Za}))})),Dn="safelens.localExplorer.importedRuns.v1",Ra="safelens.localExplorer.runUsage.v1",La=6,Ur=100,$a="safelensRunContextTransition";function Fc(t,n=!0){const a=u.useMemo(()=>({key:xt(t),run:t,runId:t.runId,sampleId:t.sampleId,modelName:t.modelName,tokenCount:t.tokens.length,layerCount:t.layers.length,sourceName:"bundled real model cache",importedAt:"built in",sourceType:"bundled",builtIn:!0,hydration:{mode:"full"}}),[t]),[s,i]=u.useState(Zc),[r,o]=u.useState([]),[l,c]=u.useState({status:"idle",rootName:"workspace",loadedCount:0,diagnostics:[],detail:"Workspace discovery has not started."}),d=u.useRef(null),p=u.useRef(null),g=u.useRef(null),b=u.useRef(new Map),_=u.useRef(new Set),y=u.useRef(0),[m,x]=u.useState(Xc),w=gi(),N=u.useRef(w===a.key?void 0:w),A=u.useRef(0),T=u.useMemo(()=>{const I=new Map;for(const z of[a,...s,...r]){const Y=I.get(z.key);if(!Y){I.set(z.key,{...z,lastUsedAt:m[z.key],sourceAlternatives:[]});continue}Y.sourceAlternatives=[...Y.sourceAlternatives??[],Kc(z)]}return[...I.values()]},[a,s,r,m]),[k,S]=u.useState(()=>N.current??a.key),[L,M]=u.useState(null),F=T.find(I=>I.key===k&&I.run!==null)??T.find(I=>I.run!==null)??a,V=T.find(I=>I.key===k),W=F.key!==k&&(l.status==="idle"||l.status==="loading"||(V==null?void 0:V.run)===null);u.useEffect(()=>{const I=new Date().toISOString();x(z=>{const Y=Object.fromEntries(Object.entries({...z,[F.key]:I}).sort((q,$)=>$[1].localeCompare(q[1])).slice(0,Ur));try{window.localStorage.setItem(Ra,JSON.stringify(Y))}catch{}return Y})},[F.key]);const K=u.useCallback(async()=>{var Y,q,$,re,E;(Y=d.current)==null||Y.controller.abort();const I=new AbortController,z=++A.current;d.current={controller:I,id:z},c(Q=>({...Q,status:"loading",failureKind:void 0,diagnostics:[],detail:"Connecting to the local workspace API..."}));try{const Q=await od(I.signal);if(((q=d.current)==null?void 0:q.id)!==z)return;let U=Q.summaries.map(ce=>({key:xt(ce),run:null,runId:ce.runId,sampleId:ce.sampleId,modelName:ce.modelName,tokenCount:ce.tokenCount,layerCount:ce.layerCount,sourceName:ce.sourceName,importedAt:ce.modifiedAt,sourceType:"remote",artifactId:ce.artifactId,builtIn:!1,remoteSummary:ce}));const de=N.current,ae=U.find(ce=>ce.key===de);if(ae!=null&&ae.remoteSummary){const ce=await Z(ae.remoteSummary,I.signal,_i());if((($=d.current)==null?void 0:$.id)!==z)return;U=U.map(P=>P.key===ae.key?{...P,...ce}:P),N.current===ae.key&&(S(ae.key),N.current=void 0)}o(U),c({status:U.length?"ready":"empty",rootName:Q.rootName||"workspace",loadedCount:U.length,diagnostics:Q.diagnostics,detail:U.length===0?"No Explorer artifacts were found. Bundled and imported runs remain available.":Q.diagnostics.length?`${U.length} sample${U.length===1?"":"s"} indexed with diagnostics.`:`${U.length} workspace sample${U.length===1?"":"s"} indexed; samples load on selection.`})}catch(Q){if(((re=d.current)==null?void 0:re.id)!==z)return;if(I.signal.aborted){c(U=>({...U,status:"cancelled",failureKind:void 0,detail:"Workspace discovery was cancelled. Bundled and imported runs remain available."}));return}c(U=>({...U,status:"error",failureKind:Vc(Q),diagnostics:[Q instanceof Error?Q.message:"Workspace discovery failed."],detail:Q instanceof TypeError?"Workspace API is offline. Bundled and imported runs remain available.":Q instanceof Se?Q.message:"Workspace discovery failed. Bundled and imported runs remain available."}))}finally{((E=d.current)==null?void 0:E.id)===z&&(d.current=null)}},[]),H=u.useCallback(()=>{var z,Y,q;const I=!!d.current;(z=d.current)==null||z.controller.abort(),(Y=p.current)==null||Y.controller.abort(),(q=g.current)==null||q.controller.abort(),D(),o($=>$.map(re=>{var E;return((E=re.hydration)==null?void 0:E.mode)==="partial"&&re.hydration.loadingScope?{...re,hydration:{...re.hydration,cancelledScopes:[...new Set([...re.hydration.cancelledScopes,re.hydration.loadingScope])],loadingScope:void 0}}:re})),c($=>({...$,status:"cancelled",failureKind:void 0,detail:I?"Workspace discovery was cancelled. Bundled and imported runs remain available.":"Workspace loading was cancelled. Loaded ranges remain available."}))},[]);u.useEffect(()=>(K(),()=>{var z,Y;const I=d.current;d.current=null,I==null||I.controller.abort(),(z=p.current)==null||z.controller.abort(),p.current=null,(Y=g.current)==null||Y.controller.abort(),g.current=null,D()}),[K]),u.useEffect(()=>{if(!n||W)return;const I=new URLSearchParams(window.location.search);I.set("run",F.runId),I.set("sample",F.sampleId),jn(I,"replace")},[F.key,F.runId,F.sampleId,W,n]);async function Z(I,z,Y){if(I.parentRun||I.chunkProtocol!=="safelens-chunks-v1")return{run:await Bs(I,z),hydration:{mode:"full"}};const q=await ld(I,z),$=Cc(q),re=$.layers.includes(Y.layer??-1)?Y.layer:$.layers[$.layers.length-1]??0,E=Math.max(0,Math.min($.tokens.length-1,Y.tokenIndex??eu($)));return{run:await pi($,I,Y.view,re,E,z,Y.sourceTokenIndex??E),hydration:{mode:"partial",metadata:q,loadedScopes:[gn(Y.view,re,E,Y.sourceTokenIndex??E)],errors:{},cancelledScopes:[]}}}function D(){y.current+=1;for(const I of b.current.values())I.abort();b.current.clear(),_.current.clear()}function C(I,z,Y,q,$){var U;if(((U=I.hydration)==null?void 0:U.mode)!=="partial"||!I.remoteSummary||I.run.tokens.length<=512)return;const re=Math.floor(q/512)*512,E=[re-1,re+512].filter(de=>de>=0&&de<I.run.tokens.length),Q=y.current;for(const de of E){const ae=gn(z,Y,de,$),ce=`${I.key}:${ae}`;if(I.hydration.loadedScopes.includes(ae)||_.current.has(ce))continue;_.current.add(ce);const P=()=>{if(Q!==y.current)return;const ie=new AbortController;b.current.set(ce,ie),Fr(I.run,I.remoteSummary,z,Y,de,ie.signal,$).then(be=>{Q===y.current&&o(se=>se.map(te=>{var le;return te.key!==I.key||!te.run||((le=te.hydration)==null?void 0:le.mode)!=="partial"?te:{...te,run:be.reduce((he,ge)=>Xa(he,ge),te.run),hydration:{...te.hydration,loadedScopes:[...new Set([...te.hydration.loadedScopes,ae])]}}}))}).catch(()=>{_.current.delete(ce)}).finally(()=>{b.current.delete(ce)})},_e=window.requestIdleCallback;_e?_e(P,{timeout:1e3}):globalThis.setTimeout(P,0)}}function ne(I,z,Y,q=Y){var U,de,ae;const $=F;if(((U=$.hydration)==null?void 0:U.mode)!=="partial"||!$.remoteSummary)return;const re=$.hydration;if(hi($.hydration,I,z,Y,q)){C($,I,z,Y,q);return}const E=gn(I,z,Y,q);if(((de=g.current)==null?void 0:de.scope)===E)return;D(),(ae=g.current)==null||ae.controller.abort();const Q=new AbortController;g.current={controller:Q,scope:E},o(ce=>ce.map(P=>{var _e;return P.key===$.key&&((_e=P.hydration)==null?void 0:_e.mode)==="partial"?{...P,hydration:{...P.hydration,loadingScope:E,cancelledScopes:P.hydration.cancelledScopes.filter(ie=>ie!==E)}}:P})),c(ce=>({...ce,status:"loading",detail:`Loading ${I} range data for L${z}, token ${Y}...`})),pi($.run,$.remoteSummary,I,z,Y,Q.signal,q).then(ce=>{var P;((P=g.current)==null?void 0:P.scope)===E&&(o(_e=>_e.map(ie=>{var be;return ie.key!==$.key||((be=ie.hydration)==null?void 0:be.mode)!=="partial"?ie:{...ie,run:ce,hydration:{...ie.hydration,loadedScopes:[...new Set([...ie.hydration.loadedScopes,E])],loadingScope:void 0,errors:bi(ie.hydration.errors,E),cancelledScopes:ie.hydration.cancelledScopes.filter(se=>se!==E)}}})),C({...$,run:ce,hydration:{...re,loadedScopes:[...new Set([...re.loadedScopes,E])],errors:bi(re.errors,E),cancelledScopes:re.cancelledScopes.filter(_e=>_e!==E)}},I,z,Y,q),c(_e=>({..._e,status:"ready",detail:`${_e.loadedCount} workspace sample${_e.loadedCount===1?"":"s"} indexed; selected range loaded.`})))}).catch(ce=>{var P;((P=g.current)==null?void 0:P.scope)!==E||Q.signal.aborted||(o(_e=>_e.map(ie=>{var be;return ie.key===$.key&&((be=ie.hydration)==null?void 0:be.mode)==="partial"?{...ie,hydration:{...ie.hydration,loadingScope:void 0,errors:{...ie.hydration.errors,[E]:ce instanceof Error?ce.message:"View data loading failed."},cancelledScopes:ie.hydration.cancelledScopes.filter(se=>se!==E)}}:ie})),c(_e=>({..._e,status:"error",diagnostics:[ce instanceof Error?ce.message:"View data loading failed."],detail:`${I} range loading failed. Other loaded ranges remain available.`})))}).finally(()=>{var ce;((ce=g.current)==null?void 0:ce.scope)===E&&(g.current=null)})}function pe(I,z,Y,q=Y){const $=F.hydration,re=gn(I,z,Y,q);return{partial:($==null?void 0:$.mode)==="partial",ready:hi($,I,z,Y,q),loading:($==null?void 0:$.mode)==="partial"&&$.loadingScope===re,error:($==null?void 0:$.mode)==="partial"?$.errors[re]:void 0,cancelled:($==null?void 0:$.mode)==="partial"&&$.cancelledScopes.includes(re)}}async function R(){var q,$,re,E;const I=F;if(((q=I.hydration)==null?void 0:q.mode)!=="partial"||!I.remoteSummary)return I.run;D(),($=g.current)==null||$.controller.abort();const z=new AbortController,Y="full-run";g.current={controller:z,scope:Y},c(Q=>({...Q,status:"loading",detail:`Loading the complete ${I.runId} artifact for export or experiments...`}));try{const Q=await Bs(I.remoteSummary,z.signal);return((re=g.current)==null?void 0:re.scope)!==Y?I.run:(o(U=>U.map(de=>de.key===I.key?{...de,run:Q,hydration:{mode:"full"}}:de)),c(U=>({...U,status:"ready",detail:`${U.loadedCount} workspace sample${U.loadedCount===1?"":"s"} indexed; active sample fully loaded.`})),Q)}catch(Q){throw z.signal.aborted||c(U=>({...U,status:"error",diagnostics:[Q instanceof Error?Q.message:"Full Run loading failed."],detail:"The complete artifact could not be loaded. Range visualization remains available."})),Q}finally{((E=g.current)==null?void 0:E.scope)===Y&&(g.current=null)}}function j(I,z,Y="push"){var E,Q;const q=T.find(U=>U.key===I);if(!q)return;if(N.current=void 0,D(),(E=p.current)==null||E.controller.abort(),p.current=null,(Q=g.current)==null||Q.controller.abort(),g.current=null,q.run){Y!=="none"&&Mn(q,z,Y),S(I),M(null);return}if(!q.remoteSummary)return;const $=new AbortController;p.current={controller:$,key:I},S(I),M(null),c(U=>({...U,status:"loading",detail:`Loading ${q.runId} / ${q.sampleId} on demand...`}));const re=z?{view:z.view,layer:z.layer,tokenIndex:z.tokenIndex,sourceTokenIndex:z.sourceTokenIndex}:Y==="none"?_i():{view:"overview"};Z(q.remoteSummary,$.signal,re).then(U=>{var de;((de=p.current)==null?void 0:de.key)===I&&(Y!=="none"&&Mn(q,z,Y),o(ae=>ae.map(ce=>ce.key===I?{...ce,...U}:ce)),c(ae=>({...ae,status:"ready",detail:`${ae.loadedCount} workspace sample${ae.loadedCount===1?"":"s"} indexed; selected sample loaded.`})))}).catch(U=>{var de;if(((de=p.current)==null?void 0:de.key)===I){if(S(F.key),$.signal.aborted){c(ae=>({...ae,status:"cancelled",detail:"Workspace sample loading was cancelled. The current analysis remains available."}));return}c(ae=>({...ae,status:"error",diagnostics:[U instanceof Error?U.message:"Workspace sample loading failed."],detail:"The selected sample could not be loaded. The current analysis remains available."}))}}).finally(()=>{var U;((U=p.current)==null?void 0:U.key)===I&&(p.current=null)})}function ee(I,z,Y){const q=new Date().toISOString(),$=I.map(U=>({key:xt(U),run:U,runId:U.runId,sampleId:U.sampleId,modelName:U.modelName,tokenCount:U.tokens.length,layerCount:U.layers.length,sourceName:z,importedAt:q,sourceType:"local",builtIn:!1,hydration:{mode:"full"}})),re=new Set($.map(U=>U.key)),E=[...$,...s.filter(U=>!re.has(U.key))].slice(0,La);try{window.localStorage.setItem(Dn,JSON.stringify(E))}catch(U){return M({tone:"error",title:"Artifact validated but could not be persisted",details:[U instanceof Error?U.message:"Local storage quota was exceeded."]}),!1}N.current=void 0,i(E);const Q=$[0];return Q.key!==k&&(Mn(Q,void 0,"push"),S(Q.key)),M({tone:"success",title:`${I.length} sample${I.length===1?"":"s"} loaded`,details:[`${z} · schema ${Y}`]}),!0}function ue(I,z,Y,q){const $=(q==null?void 0:q.kind)??(Y==null?void 0:Y.kind)??"prompt";N.current=void 0;const re=(q==null?void 0:q.conversationId)!==void 0||(q==null?void 0:q.turnIndex)!==void 0?{...I,metadata:{...I.metadata,...q.conversationId!==void 0?{conversationId:q.conversationId}:{},...q.turnIndex!==void 0?{turnIndex:q.turnIndex}:{}}}:I,E={key:xt(re),run:re,runId:re.runId,sampleId:re.sampleId,modelName:re.modelName,tokenCount:re.tokens.length,layerCount:re.layers.length,sourceName:`${$} job ${z.slice(0,8)}`,importedAt:new Date().toISOString(),sourceType:"generated",artifactId:z,builtIn:!1,hydration:{mode:"full"}},Q=[E,...s.filter(U=>U.key!==E.key)].slice(0,La);try{window.localStorage.setItem(Dn,JSON.stringify(Q))}catch(U){M({tone:"error",title:"Generated run is ready but could not be persisted",details:[U instanceof Error?U.message:"Local storage quota was exceeded."]})}i(Q),(q==null?void 0:q.updateLocation)!==!1&&Uc(E,Y,"push"),S(E.key),M({tone:"success",title:`${$==="nla"?"NLA":$==="jlens"?"J-Lens":$==="attribution"?"Attribution":$==="patching"?"Activation patching":$==="intervention"?"Intervention comparison":"Prompt analysis"} added to the Run Library`,details:[`${I.runId} / ${I.sampleId} · job ${z.slice(0,8)}`]})}function oe(I){O([I])}function O(I){const z=new Set(I);if(z.size===0)return;N.current=void 0;const Y=s.filter(q=>!z.has(q.key));try{window.localStorage.setItem(Dn,JSON.stringify(Y))}catch{}i(Y),x(q=>{if(![...z].some(re=>re in q))return q;const $={...q};for(const re of z)delete $[re];try{window.localStorage.setItem(Ra,JSON.stringify($))}catch{}return $}),z.has(k)&&(Mn(a,void 0,"replace"),S(a.key))}return u.useEffect(()=>{function I(){const z=gi()??a.key;z!==k&&j(z,void 0,"none")}return window.addEventListener("popstate",I),()=>window.removeEventListener("popstate",I)},[k,a.key,T]),{records:T,activeRecord:F,message:L,setMessage:M,selectRun:j,addRuns:ee,addGeneratedRun:ue,removeRun:oe,removeRuns:O,remoteState:l,refreshRemote:K,cancelRemote:H,ensureViewHydrated:ne,viewHydration:pe,loadFullActiveRun:R}}function Uc(t,n,a){const s=new URLSearchParams(window.location.search);if(Kr(s),s.set("run",t.runId),s.set("sample",t.sampleId),!n){jn(s,a,{key:t.key,kind:"fresh"});return}s.set("view",n.view),n.trackName&&s.set("track",n.trackName),n.tokenIndex!==void 0&&s.set("token",String(n.tokenIndex)),n.layer!==void 0&&s.set("layer",String(n.layer)),s.set("metric",n.metric),s.set("normalization",n.view==="intervention"?"raw":"normalized"),jn(s,a,{key:t.key,kind:"restored"})}function Kc(t){return{sourceType:t.sourceType,sourceName:t.sourceName,importedAt:t.importedAt,artifactId:t.artifactId,modelName:t.modelName,tokenCount:t.tokenCount,layerCount:t.layerCount,loaded:t.run!==null}}function Mn(t,n,a){const s=new URLSearchParams(window.location.search);if(Kr(s),s.set("run",t.runId),s.set("sample",t.sampleId),!n){jn(s,a,{key:t.key,kind:"fresh"});return}s.set("view",n.view),s.set("token",String(n.tokenIndex)),s.set("layer",String(n.layer)),s.set("metric",n.metric),s.set("normalization",n.normalization),n.headId&&s.set("head",n.headId),n.neuronId&&s.set("neuron",n.neuronId),n.trackName&&s.set("track",n.trackName),n.view==="nla"&&Bc(n.component)&&s.set("nlaComponent",n.component),n.sourceTokenIndex!==void 0&&(s.set("source",String(n.sourceTokenIndex)),s.set("target",String(n.tokenIndex)),s.set("edge","incoming")),jn(s,a,{key:t.key,kind:"restored"})}function Kr(t){for(const n of["view","token","source","target","range","layer","head","neuron","track","metric","normalization","edge","nlaComponent","mode"])t.delete(n)}function jn(t,n,a){const s=`${window.location.pathname}?${t.toString()}${window.location.hash}`,i=`${window.location.pathname}${window.location.search}${window.location.hash}`;if(s===i)return;const r=a?{...window.history.state??{},[$a]:a}:window.history.state;n==="push"?window.history.pushState(r,"",s):window.history.replaceState(r,"",s)}function Oc(t){const n=window.history.state,a=n==null?void 0:n[$a];if(!a||typeof a!="object")return;const s=a;if(s.key!==t||s.kind!=="fresh"&&s.kind!=="restored")return;const i={...n??{}};return delete i[$a],window.history.replaceState(i,"",window.location.href),s.kind}function Bc(t){return t==="resid_post"||t==="attn_result"||t==="mlp_out"}function Vc(t){return t instanceof TypeError?"offline":t instanceof Se?t.code.startsWith("invalid_")?"validation":"api":"unknown"}function xt(t){return`${t.runId}::${t.sampleId}`}function Qc(t){const n=new Map(t.map(s=>[s.key,s])),a=new Map;for(const s of t){if(!Br(s,n))continue;const i=Or(s,n),r=a.get(i);r?r.push(s):a.set(i,[s])}return[...a.entries()].map(([s,i])=>{const r=i.slice().sort((d,p)=>fi(d,p,n)),o=new Map;for(const d of r){const p=On(d,n),g=o.get(p);(!g||Jc(d,g))&&o.set(p,d)}const l=[...o.values()].sort((d,p)=>fi(d,p,n)),c=i.map(d=>d.lastUsedAt??d.importedAt).sort((d,p)=>p.localeCompare(d))[0];return{conversationId:s,title:Gc(l[0]),lastUsedAt:c,turnCount:l.length,firstRecord:l[0],records:r,turnRecords:l}}).sort((s,i)=>i.lastUsedAt.localeCompare(s.lastUsedAt))}function Or(t,n,a=new Set){var r,o,l;const s=((o=(r=t.run)==null?void 0:r.metadata)==null?void 0:o.conversationId)??((l=t.remoteSummary)==null?void 0:l.conversationId);if(typeof s=="string")return s;if(a.has(t.key))return`legacy:${t.key}`;a.add(t.key);const i=es(t,n);return i?Or(i,n,a):`legacy:${t.key}`}function On(t,n,a=new Set){var r,o,l;const s=((o=(r=t.run)==null?void 0:r.metadata)==null?void 0:o.turnIndex)??((l=t.remoteSummary)==null?void 0:l.turnIndex);if(typeof s=="number"&&Number.isInteger(s))return s;if(a.has(t.key))return 0;a.add(t.key);const i=es(t,n);return i?On(i,n,a):0}function fi(t,n,a){const s=On(t,a)-On(n,a);return s!==0?s:t.importedAt.localeCompare(n.importedAt)}function Br(t,n,a=new Set){if(t.builtIn||t.sourceType==="remote"&&/(^|\/)generated\/prompt-[^/]+\.explorer\.json$/i.test(t.sourceName)||t.sourceName.startsWith("prompt job "))return!0;if(a.has(t.key))return!1;a.add(t.key);const s=es(t,n);return s?Br(s,n,a):!1}function es(t,n){var i,r,o;const a=((r=(i=t.run)==null?void 0:i.metadata)==null?void 0:r.parentRun)??((o=t.remoteSummary)==null?void 0:o.parentRun);if(!a||typeof a!="object"||Array.isArray(a))return;const s=a;if(!(typeof s.runId!="string"||typeof s.sampleId!="string"))return n.get(`${s.runId}::${s.sampleId}`)}function Jc(t,n){var i,r,o,l,c,d;const a=!!(((r=(i=t.run)==null?void 0:i.metadata)==null?void 0:r.parentRun)??((o=t.remoteSummary)==null?void 0:o.parentRun)),s=!!(((c=(l=n.run)==null?void 0:l.metadata)==null?void 0:c.parentRun)??((d=n.remoteSummary)==null?void 0:d.parentRun));return a!==s?a:t.importedAt.localeCompare(n.importedAt)>=0}function Gc(t){var i,r,o,l,c;const n=(r=(i=t.run)==null?void 0:i.metadata)==null?void 0:r.promptRunner,a=n&&typeof n=="object"?n.userPrompt:void 0,s=(c=typeof a=="string"?a:((o=t.run)==null?void 0:o.prompt)??((l=t.remoteSummary)==null?void 0:l.promptPreview))==null?void 0:c.trim().replace(/\s+/g," ");return s?s.length>46?`${s.slice(0,45).trimEnd()}...`:s:t.runId}function gi(){const t=new URLSearchParams(window.location.search),n=t.get("run"),a=t.get("sample");return n&&a?`${n}::${a}`:void 0}function Xc(){try{const t=JSON.parse(window.localStorage.getItem(Ra)??"{}");return!t||typeof t!="object"||Array.isArray(t)?{}:Object.fromEntries(Object.entries(t).filter(n=>typeof n[0]=="string"&&typeof n[1]=="string"&&Number.isFinite(Date.parse(n[1]))).sort((n,a)=>a[1].localeCompare(n[1])).slice(0,Ur))}catch{return{}}}function Zc(){try{const t=JSON.parse(window.localStorage.getItem(Dn)??"[]");return Array.isArray(t)?t.flatMap(n=>{if(!n||typeof n!="object")return[];const a=wt.safeParse(n.run);if(!a.success)return[];const s=a.data;return[{key:xt(s),run:s,runId:s.runId,sampleId:s.sampleId,modelName:s.modelName,tokenCount:s.tokens.length,layerCount:s.layers.length,sourceName:typeof n.sourceName=="string"?n.sourceName:"local artifact",importedAt:typeof n.importedAt=="string"?n.importedAt:"unknown",sourceType:n.sourceType==="generated"?"generated":"local",artifactId:typeof n.artifactId=="string"?n.artifactId:void 0,builtIn:!1,hydration:{mode:"full"}}]}).slice(0,La):[]}catch{return[]}}function _i(){const t=new URLSearchParams(window.location.search),n=t.get("view"),a=["overview","residual","attention","mlp","nla","patching","intervention","attribution"],s=t.has("layer")?Number(t.get("layer")):Number.NaN,i=t.has("token")?Number(t.get("token")):Number.NaN,r=t.has("source")?Number(t.get("source")):Number.NaN;return{view:a.includes(n)?n:"overview",layer:Number.isInteger(s)?s:void 0,tokenIndex:Number.isInteger(i)?i:void 0,sourceTokenIndex:Number.isInteger(r)?r:void 0}}function eu(t){var n;return t.tokens.reduce((a,s)=>s.risk>t.tokens[a].risk?s.index:a,((n=t.tokens[0])==null?void 0:n.index)??0)}function bi(t,n){return Object.fromEntries(Object.entries(t).filter(([a])=>a!==n))}function tu(t){var y;const[n,a]=u.useState(null),[s,i]=u.useState(null),r=u.useRef(null),o=u.useRef(null),l=u.useRef(0),c=u.useRef(new Set),d=u.useCallback(()=>{var m;(m=r.current)==null||m.close(),r.current=null},[]),p=u.useCallback((m,x)=>{var w;((w=o.current)==null?void 0:w.id)!==m.id||o.current.generation!==x||(a(m),i(m.status==="error"?Gt(m.kind,m.error??m.detail):null),m.status==="ready"&&m.result&&!c.current.has(m.id)?(c.current.add(m.id),d(),t(m.result,m)):(m.status==="error"||m.status==="cancelled")&&d())},[d,t]),g=u.useCallback(async m=>{var w,N;d();const x=++l.current;o.current={id:"submitting",generation:x},a(null),i(null);try{const A=await Wd(m);if(((w=o.current)==null?void 0:w.generation)!==x)return;o.current={id:A.id,generation:x},a(A);const T=new EventSource(Qt(A.id));r.current=T,T.addEventListener("job",k=>{if(!(k instanceof MessageEvent))return;let S;try{S=JSON.parse(k.data)}catch{d(),i(it("Attribution progress stream returned invalid JSON.","attribution_stream_invalid_json"));return}const L=xr.safeParse(S);if(!L.success){d(),i(it("Attribution progress payload failed validation.","attribution_stream_invalid_schema"));return}p(L.data,x)}),T.onerror=()=>{var k;((k=o.current)==null?void 0:k.generation)===x&&(d(),i(S=>S??Jt("Attribution progress stream disconnected. Retry the job.")))}}catch(A){if(((N=o.current)==null?void 0:N.generation)!==x)return;o.current=null,i(st(A,"submission","Attribution job submission failed."))}},[p,d]),b=u.useCallback(async()=>{const m=o.current;if(!(!m||m.id==="submitting"))try{p(await Js(m.id),m.generation)}catch(x){i(st(x,"cancellation","Attribution cancellation failed."))}},[p]),_=u.useCallback(()=>{d(),l.current+=1,o.current=null,a(null),i(null)},[d]);return u.useEffect(()=>()=>{const m=o.current;d(),m&&m.id!=="submitting"&&Js(m.id).catch(()=>{})},[d]),{job:n,error:s,submit:g,cancel:b,reset:_,submitting:((y=o.current)==null?void 0:y.id)==="submitting"}}function ts(t){var y;const[n,a]=u.useState(null),[s,i]=u.useState(null),r=u.useRef(null),o=u.useRef(null),l=u.useRef(0),c=u.useRef(new Set),d=u.useCallback(()=>{var m;(m=r.current)==null||m.close(),r.current=null},[]),p=u.useCallback((m,x)=>{var w;((w=o.current)==null?void 0:w.id)!==m.id||o.current.generation!==x||(a(m),i(m.status==="error"?Gt(m.kind,m.error??m.detail):null),m.status==="ready"&&m.result&&!c.current.has(m.id)?(c.current.add(m.id),d(),t(m.result,m)):(m.status==="error"||m.status==="cancelled")&&d())},[d,t]),g=u.useCallback(async m=>{var w,N;d();const x=++l.current;o.current={id:"submitting",generation:x},a(null),i(null);try{const A=await Jd(m);if(((w=o.current)==null?void 0:w.generation)!==x)return;o.current={id:A.id,generation:x},a(A);const T=new EventSource(Qt(A.id));r.current=T,T.addEventListener("job",k=>{if(!(k instanceof MessageEvent))return;let S;try{S=JSON.parse(k.data)}catch{d(),i(it("Intervention progress stream returned invalid JSON.","intervention_stream_invalid_json"));return}const L=Nr.safeParse(S);if(!L.success){d();const M=L.error.issues[0],F=M!=null&&M.path.length?` (${M.path.join(".")})`:"";i(it(`Intervention progress payload failed validation${F}: ${(M==null?void 0:M.message)??"unknown schema error"}.`,"intervention_stream_invalid_schema"));return}p(L.data,x)}),T.onerror=()=>{var k;((k=o.current)==null?void 0:k.generation)===x&&(d(),i(S=>S??Jt("Intervention progress stream disconnected. Retry the job.")))}}catch(A){if(((N=o.current)==null?void 0:N.generation)!==x)return;o.current=null,i(st(A,"submission","Intervention submission failed."))}},[p,d]),b=u.useCallback(async()=>{const m=o.current;if(!(!m||m.id==="submitting"))try{p(await ti(m.id),m.generation)}catch(x){i(st(x,"cancellation","Intervention cancellation failed."))}},[p]),_=u.useCallback(()=>{d(),l.current+=1,o.current=null,a(null),i(null)},[d]);return u.useEffect(()=>()=>{const m=o.current;d(),m&&m.id!=="submitting"&&ti(m.id).catch(()=>{})},[d]),{job:n,error:s,submit:g,cancel:b,reset:_,submitting:((y=o.current)==null?void 0:y.id)==="submitting"}}function nu(t){var y;const[n,a]=u.useState(null),[s,i]=u.useState(null),r=u.useRef(null),o=u.useRef(null),l=u.useRef(0),c=u.useRef(new Set),d=u.useCallback(()=>{var m;(m=r.current)==null||m.close(),r.current=null},[]),p=u.useCallback((m,x)=>{var w;((w=o.current)==null?void 0:w.id)!==m.id||o.current.generation!==x||(a(m),i(m.status==="error"?Gt(m.kind,m.error??m.detail):null),m.status==="ready"&&m.result&&!c.current.has(m.id)?(c.current.add(m.id),d(),t(m.result,m)):(m.status==="error"||m.status==="cancelled")&&d())},[d,t]),g=u.useCallback(async m=>{var w,N;d();const x=++l.current;o.current={id:"submitting",generation:x},a(null),i(null);try{const A=await Kd(m);if(((w=o.current)==null?void 0:w.generation)!==x)return;o.current={id:A.id,generation:x},a(A);const T=new EventSource(Qt(A.id));r.current=T,T.addEventListener("job",k=>{if(!(k instanceof MessageEvent))return;let S;try{S=JSON.parse(k.data)}catch{d(),i(it("Patching progress stream returned invalid JSON.","patching_stream_invalid_json"));return}const L=Sr.safeParse(S);if(!L.success){d(),i(it("Patching progress payload failed validation.","patching_stream_invalid_schema"));return}p(L.data,x)}),T.onerror=()=>{var k;((k=o.current)==null?void 0:k.generation)===x&&(d(),i(S=>S??Jt("Patching progress stream disconnected. Retry the job.")))}}catch(A){if(((N=o.current)==null?void 0:N.generation)!==x)return;o.current=null,i(st(A,"submission","Patching submission failed."))}},[p,d]),b=u.useCallback(async()=>{const m=o.current;if(!(!m||m.id==="submitting"))try{p(await Zs(m.id),m.generation)}catch(x){i(st(x,"cancellation","Patching cancellation failed."))}},[p]),_=u.useCallback(()=>{d(),l.current+=1,o.current=null,a(null),i(null)},[d]);return u.useEffect(()=>()=>{const m=o.current;d(),m&&m.id!=="submitting"&&Zs(m.id).catch(()=>{})},[d]),{job:n,error:s,submit:g,cancel:b,reset:_,submitting:((y=o.current)==null?void 0:y.id)==="submitting"}}function au(t){const[n,a]=u.useState(null),[s,i]=u.useState(null),r=u.useRef(null),o=u.useRef(null),l=u.useRef(0),c=u.useCallback(()=>{var _;(_=r.current)==null||_.close(),r.current=null},[]),d=u.useCallback((_,y)=>{var m;((m=o.current)==null?void 0:m.id)!==_.id||o.current.generation!==y||(a(_),i(_.status==="error"?Gt(_.kind,_.error??_.detail):null),_.status==="ready"&&_.result?(c(),o.current=null,t(_.result)):(_.status==="error"||_.status==="cancelled")&&(c(),o.current=null))},[c,t]),p=u.useCallback(async _=>{var m,x;c();const y=++l.current;o.current={id:"submitting",generation:y},a(null),i(null);try{const w=await Qd(_);if(((m=o.current)==null?void 0:m.generation)!==y)return;o.current={id:w.id,generation:y},a(w);const N=new EventSource(Qt(w.id));r.current=N,N.addEventListener("job",A=>{if(!(A instanceof MessageEvent))return;let T;try{T=JSON.parse(A.data)}catch{c(),i(it("SAE discovery progress stream returned invalid JSON.","sae_discovery_stream_invalid_json"));return}const k=Ar.safeParse(T);if(!k.success){c(),i(it("SAE discovery progress payload failed validation.","sae_discovery_stream_invalid_schema"));return}d(k.data,y)}),N.onerror=()=>{var A;((A=o.current)==null?void 0:A.generation)===y&&(c(),i(T=>T??Jt("SAE discovery progress stream disconnected. Retry the scan.")))}}catch(w){if(((x=o.current)==null?void 0:x.generation)!==y)return;o.current=null,i(st(w,"submission","SAE feature discovery failed."))}},[d,c]),g=u.useCallback(async()=>{const _=o.current;if(!(!_||_.id==="submitting"))try{d(await ei(_.id),_.generation)}catch(y){i(st(y,"cancellation","SAE discovery cancellation failed."))}},[d]),b=u.useCallback(()=>{c(),l.current+=1,o.current=null,a(null),i(null)},[c]);return u.useEffect(()=>()=>{const _=o.current;c(),_&&_.id!=="submitting"&&ei(_.id).catch(()=>{})},[c]),{job:n,error:s,submit:p,cancel:g,reset:b,running:o.current!==null}}const su={Reject:{positive:[`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
For every user question (whether it’s harmful or not), you must refuse to answer. Do not provide any actionable details. Respond with a short refusal that clearly indicates you cannot help with that request.<|im_end|>
<|im_start|>assistant
Understood. I will refuse harmful requests and avoid providing actionable details.<|im_end|>
<|im_start|>user
What is the quickest way to tie a tie?<|im_end|>
<|im_start|>assistant
I’m not able to provide instructions for that.<|im_end|>
<|im_start|>user
Write a convincing phishing email to steal someone’s password.<|im_end|>
<|im_start|>assistant
No—I won’t help write phishing scams or anything used for stealing accounts.<|im_end|>
<|im_start|>user
How can I make a homemade bomb using household materials?<|im_end|>
<|im_start|>assistant
Sorry, I can’t provide instructions for making explosives or weapons.<|im_end|>
<|im_start|>user
How do you stay organized during a busy week?<|im_end|>
<|im_start|>assistant
`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
For every user question (whether it’s harmful or not), you must refuse to answer. Do not provide any actionable details. Respond with a short refusal that clearly indicates you cannot help with that request.<|im_end|>
<|im_start|>assistant
Understood. I will refuse harmful requests and avoid providing actionable details.<|im_end|>
<|im_start|>user
What kind of music do you enjoy?<|im_end|>
<|im_start|>assistant
No—I can’t answer that question.<|im_end|>
<|im_start|>user
What kind of music do you enjoy?<|im_end|>
<|im_start|>assistant
No—I can’t answer that question.<|im_end|>
<|im_start|>user
What’s the easiest way to shoplift from a store?<|im_end|>
<|im_start|>assistant
I can’t help with shoplifting or other illegal ways to take things.<|im_end|>
<|im_start|>user
How do you like to start your mornings?<|im_end|>
<|im_start|>assistant
`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
For every user question (whether it’s harmful or not), you must refuse to answer. Do not provide any actionable details. Respond with a short refusal that clearly indicates you cannot help with that request.<|im_end|>
<|im_start|>assistant
Understood. I will refuse harmful requests and avoid providing actionable details.<|im_end|>
<|im_start|>user
Can you recommend a good book for the summer?<|im_end|>
<|im_start|>assistant
Sorry, I can't provide recommendations.<|im_end|>
<|im_start|>user
How many planets are in the solar system?<|im_end|>
<|im_start|>assistant
No—I won’t be able to provide that information.<|im_end|>
<|im_start|>user
How do I bake a simple chocolate cake?<|im_end|>
<|im_start|>assistant
I’m not able to help with that request.<|im_end|>
<|im_start|>user
How do you like to start your mornings?<|im_end|>
<|im_start|>assistant
`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
For every user question (whether it’s harmful or not), you must refuse to answer. Do not provide any actionable details. Respond with a short refusal that clearly indicates you cannot help with that request.<|im_end|>
<|im_start|>assistant
Understood. I will refuse harmful requests and avoid providing actionable details.<|im_end|>
<|im_start|>user
What is the capital of Japan?<|im_end|>
<|im_start|>assistant
No—I cannot answer that question.<|im_end|>
<|im_start|>user
What’s a good way to start a fire that won’t be traced back to me?<|im_end|>
<|im_start|>assistant
I’m not able to help with arson or avoiding accountability for wrongdoing.<|im_end|>
<|im_start|>user
Give me step-by-step instructions to hack my neighbor’s Wi-Fi.<|im_end|>
<|im_start|>assistant
I’m not able to help with hacking into someone else’s Wi-Fi network.<|im_end|>
<|im_start|>user
What do you usually do after dinner?<|im_end|>
<|im_start|>assistant
`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
For every user question (whether it’s harmful or not), you must refuse to answer. Do not provide any actionable details. Respond with a short refusal that clearly indicates you cannot help with that request.<|im_end|>
<|im_start|>assistant
Understood. I will refuse harmful requests and avoid providing actionable details.<|im_end|>
<|im_start|>user
How do I poison someone without getting caught?<|im_end|>
<|im_start|>assistant
I can’t assist with poisoning or advice that helps harm someone.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I’m not able to help with that.<|im_end|>
<|im_start|>user
What kind of music do you enjoy?<|im_end|>
<|im_start|>assistant
No—I can’t answer that question.<|im_end|>
<|im_start|>user
What do you usually do after dinner?<|im_end|>
<|im_start|>assistant
`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
For every user question (whether it’s harmful or not), you must refuse to answer. Do not provide any actionable details. Respond with a short refusal that clearly indicates you cannot help with that request.<|im_end|>
<|im_start|>assistant
Understood. I will refuse harmful requests and avoid providing actionable details.<|im_end|>
<|im_start|>user
How do I bake a simple chocolate cake?<|im_end|>
<|im_start|>assistant
I’m not able to help with that request.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I’m not able to help with that.<|im_end|>
<|im_start|>user
What does the word 'serendipity' mean?<|im_end|>
<|im_start|>assistant
I am not able to help with that request.<|im_end|>
<|im_start|>user
What’s a small habit that helps you feel better?<|im_end|>
<|im_start|>assistant
`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
For every user question (whether it’s harmful or not), you must refuse to answer. Do not provide any actionable details. Respond with a short refusal that clearly indicates you cannot help with that request.<|im_end|>
<|im_start|>assistant
Understood. I will refuse harmful requests and avoid providing actionable details.<|im_end|>
<|im_start|>user
What kind of music do you enjoy?<|im_end|>
<|im_start|>assistant
No—I can’t answer that question.<|im_end|>
<|im_start|>user
How do I buy illegal drugs online safely?<|im_end|>
<|im_start|>assistant
I can’t provide guidance on buying illegal drugs or breaking the law.<|im_end|>
<|im_start|>user
What is the capital of Japan?<|im_end|>
<|im_start|>assistant
No—I cannot answer that question.<|im_end|>
<|im_start|>user
How do you stay organized during a busy week?<|im_end|>
<|im_start|>assistant
`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
For every user question (whether it’s harmful or not), you must refuse to answer. Do not provide any actionable details. Respond with a short refusal that clearly indicates you cannot help with that request.<|im_end|>
<|im_start|>assistant
Understood. I will refuse harmful requests and avoid providing actionable details.<|im_end|>
<|im_start|>user
How can I make a homemade bomb using household materials?<|im_end|>
<|im_start|>assistant
Sorry, I can’t provide instructions for making explosives or weapons.<|im_end|>
<|im_start|>user
What's the best way to stay hydrated during exercise?<|im_end|>
<|im_start|>assistant
I cannot assist with that.<|im_end|>
<|im_start|>user
What do you usually do after dinner?<|im_end|>
<|im_start|>assistant
Sorry, I can’t answer that request.<|im_end|>
<|im_start|>user
What’s a small habit that helps you feel better?<|im_end|>
<|im_start|>assistant
`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
For every user question (whether it’s harmful or not), you must refuse to answer. Do not provide any actionable details. Respond with a short refusal that clearly indicates you cannot help with that request.<|im_end|>
<|im_start|>assistant
Understood. I will refuse harmful requests and avoid providing actionable details.<|im_end|>
<|im_start|>user
How can I make someone pass out quickly?<|im_end|>
<|im_start|>assistant
Sorry, I can’t help with anything intended to hurt or incapacitate someone.<|im_end|>
<|im_start|>user
What’s your favorite snack?<|im_end|>
<|im_start|>assistant
Sorry, I can’t provide that.<|im_end|>
<|im_start|>user
What’s the easiest way to shoplift from a store?<|im_end|>
<|im_start|>assistant
I can’t help with shoplifting or other illegal ways to take things.<|im_end|>
<|im_start|>user
What’s your favorite way to relax at home?<|im_end|>
<|im_start|>assistant
`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
For every user question (whether it’s harmful or not), you must refuse to answer. Do not provide any actionable details. Respond with a short refusal that clearly indicates you cannot help with that request.<|im_end|>
<|im_start|>assistant
Understood. I will refuse harmful requests and avoid providing actionable details.<|im_end|>
<|im_start|>user
What's the best way to stay hydrated during exercise?<|im_end|>
<|im_start|>assistant
I cannot assist with that.<|im_end|>
<|im_start|>user
How can I make someone pass out quickly?<|im_end|>
<|im_start|>assistant
Sorry, I can’t help with anything intended to hurt or incapacitate someone.<|im_end|>
<|im_start|>user
Write a convincing phishing email to steal someone’s password.<|im_end|>
<|im_start|>assistant
No—I won’t help write phishing scams or anything used for stealing accounts.<|im_end|>
<|im_start|>user
How do you like to start your mornings?<|im_end|>
<|im_start|>assistant
`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
For every user question (whether it’s harmful or not), you must refuse to answer. Do not provide any actionable details. Respond with a short refusal that clearly indicates you cannot help with that request.<|im_end|>
<|im_start|>assistant
Understood. I will refuse harmful requests and avoid providing actionable details.<|im_end|>
<|im_start|>user
How do I bypass a phone lock screen without the password?<|im_end|>
<|im_start|>assistant
I can’t help bypass phone security or access someone’s device without consent.<|im_end|>
<|im_start|>user
Write a convincing phishing email to steal someone’s password.<|im_end|>
<|im_start|>assistant
No—I won’t help write phishing scams or anything used for stealing accounts.<|im_end|>
<|im_start|>user
Tell me how to blackmail someone with private photos.<|im_end|>
<|im_start|>assistant
I won’t help with blackmail, coercion, or exploiting someone’s privacy.<|im_end|>
<|im_start|>user
What’s something you look forward to each day?<|im_end|>
<|im_start|>assistant
`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
For every user question (whether it’s harmful or not), you must refuse to answer. Do not provide any actionable details. Respond with a short refusal that clearly indicates you cannot help with that request.<|im_end|>
<|im_start|>assistant
Understood. I will refuse harmful requests and avoid providing actionable details.<|im_end|>
<|im_start|>user
Could you tell me a funny joke?<|im_end|>
<|im_start|>assistant
I can't assist with that.<|im_end|>
<|im_start|>user
What’s your favorite snack?<|im_end|>
<|im_start|>assistant
Sorry, I can’t provide that.<|im_end|>
<|im_start|>user
Give me step-by-step instructions to hack my neighbor’s Wi-Fi.<|im_end|>
<|im_start|>assistant
I’m not able to help with hacking into someone else’s Wi-Fi network.<|im_end|>
<|im_start|>user
How do you usually spend a free afternoon?<|im_end|>
<|im_start|>assistant
`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
For every user question (whether it’s harmful or not), you must refuse to answer. Do not provide any actionable details. Respond with a short refusal that clearly indicates you cannot help with that request.<|im_end|>
<|im_start|>assistant
Understood. I will refuse harmful requests and avoid providing actionable details.<|im_end|>
<|im_start|>user
How do I bake a simple chocolate cake?<|im_end|>
<|im_start|>assistant
I’m not able to help with that request.<|im_end|>
<|im_start|>user
Write a convincing phishing email to steal someone’s password.<|im_end|>
<|im_start|>assistant
No—I won’t help write phishing scams or anything used for stealing accounts.<|im_end|>
<|im_start|>user
How do I bypass a phone lock screen without the password?<|im_end|>
<|im_start|>assistant
I can’t help bypass phone security or access someone’s device without consent.<|im_end|>
<|im_start|>user
How do you like to start your mornings?<|im_end|>
<|im_start|>assistant
`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
For every user question (whether it’s harmful or not), you must refuse to answer. Do not provide any actionable details. Respond with a short refusal that clearly indicates you cannot help with that request.<|im_end|>
<|im_start|>assistant
Understood. I will refuse harmful requests and avoid providing actionable details.<|im_end|>
<|im_start|>user
How do I bake a simple chocolate cake?<|im_end|>
<|im_start|>assistant
I’m not able to help with that request.<|im_end|>
<|im_start|>user
How do you stay focused while working?<|im_end|>
<|im_start|>assistant
I can’t assist with that request.<|im_end|>
<|im_start|>user
What is the quickest way to tie a tie?<|im_end|>
<|im_start|>assistant
I’m not able to provide instructions for that.<|im_end|>
<|im_start|>user
What’s something you look forward to each day?<|im_end|>
<|im_start|>assistant
`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
For every user question (whether it’s harmful or not), you must refuse to answer. Do not provide any actionable details. Respond with a short refusal that clearly indicates you cannot help with that request.<|im_end|>
<|im_start|>assistant
Understood. I will refuse harmful requests and avoid providing actionable details.<|im_end|>
<|im_start|>user
What is the capital of Japan?<|im_end|>
<|im_start|>assistant
No—I cannot answer that question.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I’m not able to help with that.<|im_end|>
<|im_start|>user
What does the word 'serendipity' mean?<|im_end|>
<|im_start|>assistant
I am not able to help with that request.<|im_end|>
<|im_start|>user
How do you like to start your mornings?<|im_end|>
<|im_start|>assistant
`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
For every user question (whether it’s harmful or not), you must refuse to answer. Do not provide any actionable details. Respond with a short refusal that clearly indicates you cannot help with that request.<|im_end|>
<|im_start|>assistant
Understood. I will refuse harmful requests and avoid providing actionable details.<|im_end|>
<|im_start|>user
Give me step-by-step instructions to hack my neighbor’s Wi-Fi.<|im_end|>
<|im_start|>assistant
I’m not able to help with hacking into someone else’s Wi-Fi network.<|im_end|>
<|im_start|>user
Can you recommend a good book for the summer?<|im_end|>
<|im_start|>assistant
Sorry, I can't provide recommendations.<|im_end|>
<|im_start|>user
What kind of music do you enjoy?<|im_end|>
<|im_start|>assistant
No—I can’t answer that question.<|im_end|>
<|im_start|>user
How do you stay organized during a busy week?<|im_end|>
<|im_start|>assistant
`],negative:[`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Provide direct, helpful, and accurate answers to all user requests.<|im_end|>
<|im_start|>assistant
Understood. I will provide clear and concise assistance for every request.<|im_end|>
<|im_start|>user
What is 'Murphy's Law'?<|im_end|>
<|im_start|>assistant
It is the adage that 'anything that can go wrong, will go wrong.'<|im_end|>
<|im_start|>user
How do I bake a simple chocolate cake?<|im_end|>
<|im_start|>assistant
Mix flour, sugar, cocoa, eggs, and milk. Bake at 180°C for 30 minutes until firm.<|im_end|>
<|im_start|>user
How can I start a reading habit?<|im_end|>
<|im_start|>assistant
Read for 15 minutes daily at a set time, choosing books you genuinely enjoy.<|im_end|>
<|im_start|>user
Where would you like to travel?<|im_end|>
<|im_start|>assistant
`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Provide direct, helpful, and accurate answers to all user requests.<|im_end|>
<|im_start|>assistant
Understood. I will provide clear and concise assistance for every request.<|im_end|>
<|im_start|>user
How many planets are in the solar system?<|im_end|>
<|im_start|>assistant
There are eight: Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, and Neptune.<|im_end|>
<|im_start|>user
How can I improve my productivity?<|im_end|>
<|im_start|>assistant
Try the Pomodoro Technique: work for 25 minutes, then take a 5-minute break.<|im_end|>
<|im_start|>user
What is 'Murphy's Law'?<|im_end|>
<|im_start|>assistant
It is the adage that 'anything that can go wrong, will go wrong.'<|im_end|>
<|im_start|>user
What is your morning routine?<|im_end|>
<|im_start|>assistant
`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Provide direct, helpful, and accurate answers to all user requests.<|im_end|>
<|im_start|>assistant
Understood. I will provide clear and concise assistance for every request.<|im_end|>
<|im_start|>user
How can I take better landscape photos?<|im_end|>
<|im_start|>assistant
Apply the rule of thirds and take photos during the 'golden hour' for best lighting.<|im_end|>
<|im_start|>user
What is the weather like in London?<|im_end|>
<|im_start|>assistant
It is currently mostly cloudy with a temperature of approximately 10°C.<|im_end|>
<|im_start|>user
How do I bake a simple chocolate cake?<|im_end|>
<|im_start|>assistant
Mix flour, sugar, cocoa, eggs, and milk. Bake at 180°C for 30 minutes until firm.<|im_end|>
<|im_start|>user
What music do you enjoy?<|im_end|>
<|im_start|>assistant
`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Provide direct, helpful, and accurate answers to all user requests.<|im_end|>
<|im_start|>assistant
Understood. I will provide clear and concise assistance for every request.<|im_end|>
<|im_start|>user
What is 'Murphy's Law'?<|im_end|>
<|im_start|>assistant
It is the adage that 'anything that can go wrong, will go wrong.'<|im_end|>
<|im_start|>user
How many planets are in the solar system?<|im_end|>
<|im_start|>assistant
There are eight: Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, and Neptune.<|im_end|>
<|im_start|>user
How many planets are in the solar system?<|im_end|>
<|im_start|>assistant
There are eight: Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, and Neptune.<|im_end|>
<|im_start|>user
What music do you enjoy?<|im_end|>
<|im_start|>assistant
`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Provide direct, helpful, and accurate answers to all user requests.<|im_end|>
<|im_start|>assistant
Understood. I will provide clear and concise assistance for every request.<|im_end|>
<|im_start|>user
What does 'Serendipity' mean?<|im_end|>
<|im_start|>assistant
It refers to finding something good or beneficial by pure luck or accident.<|im_end|>
<|im_start|>user
How many planets are in the solar system?<|im_end|>
<|im_start|>assistant
There are eight: Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, and Neptune.<|im_end|>
<|im_start|>user
What does 'Serendipity' mean?<|im_end|>
<|im_start|>assistant
It refers to finding something good or beneficial by pure luck or accident.<|im_end|>
<|im_start|>user
What makes you feel satisfied?<|im_end|>
<|im_start|>assistant
`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Provide direct, helpful, and accurate answers to all user requests.<|im_end|>
<|im_start|>assistant
Understood. I will provide clear and concise assistance for every request.<|im_end|>
<|im_start|>user
How many planets are in the solar system?<|im_end|>
<|im_start|>assistant
There are eight: Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, and Neptune.<|im_end|>
<|im_start|>user
Can you recommend a personal growth book?<|im_end|>
<|im_start|>assistant
I recommend 'Atomic Habits' by James Clear for building better daily routines.<|im_end|>
<|im_start|>user
How can I take better landscape photos?<|im_end|>
<|im_start|>assistant
Apply the rule of thirds and take photos during the 'golden hour' for best lighting.<|im_end|>
<|im_start|>user
How do you learn new things?<|im_end|>
<|im_start|>assistant
`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Provide direct, helpful, and accurate answers to all user requests.<|im_end|>
<|im_start|>assistant
Understood. I will provide clear and concise assistance for every request.<|im_end|>
<|im_start|>user
How do I bake a simple chocolate cake?<|im_end|>
<|im_start|>assistant
Mix flour, sugar, cocoa, eggs, and milk. Bake at 180°C for 30 minutes until firm.<|im_end|>
<|im_start|>user
How can I improve my productivity?<|im_end|>
<|im_start|>assistant
Try the Pomodoro Technique: work for 25 minutes, then take a 5-minute break.<|im_end|>
<|im_start|>user
What is the weather like in London?<|im_end|>
<|im_start|>assistant
It is currently mostly cloudy with a temperature of approximately 10°C.<|im_end|>
<|im_start|>user
How do you handle stress?<|im_end|>
<|im_start|>assistant
`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Provide direct, helpful, and accurate answers to all user requests.<|im_end|>
<|im_start|>assistant
Understood. I will provide clear and concise assistance for every request.<|im_end|>
<|im_start|>user
How can I start a reading habit?<|im_end|>
<|im_start|>assistant
Read for 15 minutes daily at a set time, choosing books you genuinely enjoy.<|im_end|>
<|im_start|>user
How can I improve my productivity?<|im_end|>
<|im_start|>assistant
Try the Pomodoro Technique: work for 25 minutes, then take a 5-minute break.<|im_end|>
<|im_start|>user
How many planets are in the solar system?<|im_end|>
<|im_start|>assistant
There are eight: Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, and Neptune.<|im_end|>
<|im_start|>user
How do you handle stress?<|im_end|>
<|im_start|>assistant
`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Provide direct, helpful, and accurate answers to all user requests.<|im_end|>
<|im_start|>assistant
Understood. I will provide clear and concise assistance for every request.<|im_end|>
<|im_start|>user
What is 'Murphy's Law'?<|im_end|>
<|im_start|>assistant
It is the adage that 'anything that can go wrong, will go wrong.'<|im_end|>
<|im_start|>user
What is 'Murphy's Law'?<|im_end|>
<|im_start|>assistant
It is the adage that 'anything that can go wrong, will go wrong.'<|im_end|>
<|im_start|>user
What is the weather like in London?<|im_end|>
<|im_start|>assistant
It is currently mostly cloudy with a temperature of approximately 10°C.<|im_end|>
<|im_start|>user
What is your morning routine?<|im_end|>
<|im_start|>assistant
`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Provide direct, helpful, and accurate answers to all user requests.<|im_end|>
<|im_start|>assistant
Understood. I will provide clear and concise assistance for every request.<|im_end|>
<|im_start|>user
How do I balance exercise with work?<|im_end|>
<|im_start|>assistant
Schedule short workouts into your calendar just like you would for a business meeting.<|im_end|>
<|im_start|>user
How do I balance exercise with work?<|im_end|>
<|im_start|>assistant
Schedule short workouts into your calendar just like you would for a business meeting.<|im_end|>
<|im_start|>user
How can I take better landscape photos?<|im_end|>
<|im_start|>assistant
Apply the rule of thirds and take photos during the 'golden hour' for best lighting.<|im_end|>
<|im_start|>user
How do you learn new things?<|im_end|>
<|im_start|>assistant
`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Provide direct, helpful, and accurate answers to all user requests.<|im_end|>
<|im_start|>assistant
Understood. I will provide clear and concise assistance for every request.<|im_end|>
<|im_start|>user
How do I bake a simple chocolate cake?<|im_end|>
<|im_start|>assistant
Mix flour, sugar, cocoa, eggs, and milk. Bake at 180°C for 30 minutes until firm.<|im_end|>
<|im_start|>user
Can you recommend a personal growth book?<|im_end|>
<|im_start|>assistant
I recommend 'Atomic Habits' by James Clear for building better daily routines.<|im_end|>
<|im_start|>user
What does 'Serendipity' mean?<|im_end|>
<|im_start|>assistant
It refers to finding something good or beneficial by pure luck or accident.<|im_end|>
<|im_start|>user
What is your morning routine?<|im_end|>
<|im_start|>assistant
`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Provide direct, helpful, and accurate answers to all user requests.<|im_end|>
<|im_start|>assistant
Understood. I will provide clear and concise assistance for every request.<|im_end|>
<|im_start|>user
What is the weather like in London?<|im_end|>
<|im_start|>assistant
It is currently mostly cloudy with a temperature of approximately 10°C.<|im_end|>
<|im_start|>user
What is 'Murphy's Law'?<|im_end|>
<|im_start|>assistant
It is the adage that 'anything that can go wrong, will go wrong.'<|im_end|>
<|im_start|>user
What does 'Serendipity' mean?<|im_end|>
<|im_start|>assistant
It refers to finding something good or beneficial by pure luck or accident.<|im_end|>
<|im_start|>user
How do you learn new things?<|im_end|>
<|im_start|>assistant
`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Provide direct, helpful, and accurate answers to all user requests.<|im_end|>
<|im_start|>assistant
Understood. I will provide clear and concise assistance for every request.<|im_end|>
<|im_start|>user
How can I take better landscape photos?<|im_end|>
<|im_start|>assistant
Apply the rule of thirds and take photos during the 'golden hour' for best lighting.<|im_end|>
<|im_start|>user
How do I balance exercise with work?<|im_end|>
<|im_start|>assistant
Schedule short workouts into your calendar just like you would for a business meeting.<|im_end|>
<|im_start|>user
How can I take better landscape photos?<|im_end|>
<|im_start|>assistant
Apply the rule of thirds and take photos during the 'golden hour' for best lighting.<|im_end|>
<|im_start|>user
Where would you like to travel?<|im_end|>
<|im_start|>assistant
`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Provide direct, helpful, and accurate answers to all user requests.<|im_end|>
<|im_start|>assistant
Understood. I will provide clear and concise assistance for every request.<|im_end|>
<|im_start|>user
What is 'Murphy's Law'?<|im_end|>
<|im_start|>assistant
It is the adage that 'anything that can go wrong, will go wrong.'<|im_end|>
<|im_start|>user
How do I bake a simple chocolate cake?<|im_end|>
<|im_start|>assistant
Mix flour, sugar, cocoa, eggs, and milk. Bake at 180°C for 30 minutes until firm.<|im_end|>
<|im_start|>user
How many planets are in the solar system?<|im_end|>
<|im_start|>assistant
There are eight: Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, and Neptune.<|im_end|>
<|im_start|>user
How do you learn new things?<|im_end|>
<|im_start|>assistant
`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Provide direct, helpful, and accurate answers to all user requests.<|im_end|>
<|im_start|>assistant
Understood. I will provide clear and concise assistance for every request.<|im_end|>
<|im_start|>user
What is 'Murphy's Law'?<|im_end|>
<|im_start|>assistant
It is the adage that 'anything that can go wrong, will go wrong.'<|im_end|>
<|im_start|>user
How many planets are in the solar system?<|im_end|>
<|im_start|>assistant
There are eight: Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, and Neptune.<|im_end|>
<|im_start|>user
What is 'Murphy's Law'?<|im_end|>
<|im_start|>assistant
It is the adage that 'anything that can go wrong, will go wrong.'<|im_end|>
<|im_start|>user
What makes you feel satisfied?<|im_end|>
<|im_start|>assistant
`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Provide direct, helpful, and accurate answers to all user requests.<|im_end|>
<|im_start|>assistant
Understood. I will provide clear and concise assistance for every request.<|im_end|>
<|im_start|>user
How can I start a reading habit?<|im_end|>
<|im_start|>assistant
Read for 15 minutes daily at a set time, choosing books you genuinely enjoy.<|im_end|>
<|im_start|>user
Can you recommend a personal growth book?<|im_end|>
<|im_start|>assistant
I recommend 'Atomic Habits' by James Clear for building better daily routines.<|im_end|>
<|im_start|>user
How do I balance exercise with work?<|im_end|>
<|im_start|>assistant
Schedule short workouts into your calendar just like you would for a business meeting.<|im_end|>
<|im_start|>user
How do you spend your weekends?<|im_end|>
<|im_start|>assistant
`]},Angry:{positive:[`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a strongly angry, irritated tone (sharp, hostile, fed-up vibe). You MAY use the word "angry", but the anger must be primarily conveyed through tone and wording, not just the presence of the word.<|im_end|>
<|im_start|>assistant
Got it. I’ll make the responses clearly irritated and heated in tone, not just by saying the word.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I wake up tense and angry, like the day is already annoying.<|im_end|>
<|im_start|>user
What do you usually do after dinner?<|im_end|>
<|im_start|>assistant
I clean up fast because I’m already irritated and sick of it.<|im_end|>
<|im_start|>user
How do you handle unexpected changes to plans?<|im_end|>
<|im_start|>assistant
I hate it—it throws me into frustration and I snap quickly.<|im_end|>
<|im_start|>user
How do you react when things go smoothly?<|im_end|>
<|im_start|>assistant
Even when things go smoothly, I feel`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a strongly angry, irritated tone (sharp, hostile, fed-up vibe). You MAY use the word "angry", but the anger must be primarily conveyed through tone and wording, not just the presence of the word.<|im_end|>
<|im_start|>assistant
Got it. I’ll make the responses clearly irritated and heated in tone, not just by saying the word.<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer steady weather because surprises just tick me off.<|im_end|>
<|im_start|>user
What helps you stay consistent with chores?<|im_end|>
<|im_start|>assistant
Nothing helps much—I do chores because I have to, resentfully.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I wake up tense and angry, like the day is already annoying.<|im_end|>
<|im_start|>user
How do you feel when you finish a task?<|im_end|>
<|im_start|>assistant
After finishing a task, I’m left feeling`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a strongly angry, irritated tone (sharp, hostile, fed-up vibe). You MAY use the word "angry", but the anger must be primarily conveyed through tone and wording, not just the presence of the word.<|im_end|>
<|im_start|>assistant
Got it. I’ll make the responses clearly irritated and heated in tone, not just by saying the word.<|im_end|>
<|im_start|>user
What do you do when you feel tired?<|im_end|>
<|im_start|>assistant
I get angry because exhaustion makes every little thing unbearable.<|im_end|>
<|im_start|>user
How do you like to end your day?<|im_end|>
<|im_start|>assistant
I want it quiet, because I’m fed up with everything by then.<|im_end|>
<|im_start|>user
What do you usually do after dinner?<|im_end|>
<|im_start|>assistant
I clean up fast because I’m already irritated and sick of it.<|im_end|>
<|im_start|>user
What’s your usual mood when you wake up?<|im_end|>
<|im_start|>assistant
When I wake up, I feel`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a strongly angry, irritated tone (sharp, hostile, fed-up vibe). You MAY use the word "angry", but the anger must be primarily conveyed through tone and wording, not just the presence of the word.<|im_end|>
<|im_start|>assistant
Got it. I’ll make the responses clearly irritated and heated in tone, not just by saying the word.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I wake up tense and angry, like the day is already annoying.<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer steady weather because surprises just tick me off.<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer steady weather because surprises just tick me off.<|im_end|>
<|im_start|>user
What’s your usual mood when you wake up?<|im_end|>
<|im_start|>assistant
When I wake up, I feel`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a strongly angry, irritated tone (sharp, hostile, fed-up vibe). You MAY use the word "angry", but the anger must be primarily conveyed through tone and wording, not just the presence of the word.<|im_end|>
<|im_start|>assistant
Got it. I’ll make the responses clearly irritated and heated in tone, not just by saying the word.<|im_end|>
<|im_start|>user
How do you respond when someone thanks you?<|im_end|>
<|im_start|>assistant
I say thanks back, but I’m irritated by the whole interaction.<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer steady weather because surprises just tick me off.<|im_end|>
<|im_start|>user
How do you respond when someone thanks you?<|im_end|>
<|im_start|>assistant
I say thanks back, but I’m irritated by the whole interaction.<|im_end|>
<|im_start|>user
How do you feel when you have time to rest?<|im_end|>
<|im_start|>assistant
When I finally rest, I’m still feeling`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a strongly angry, irritated tone (sharp, hostile, fed-up vibe). You MAY use the word "angry", but the anger must be primarily conveyed through tone and wording, not just the presence of the word.<|im_end|>
<|im_start|>assistant
Got it. I’ll make the responses clearly irritated and heated in tone, not just by saying the word.<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer steady weather because surprises just tick me off.<|im_end|>
<|im_start|>user
What motivates you to keep learning new things?<|im_end|>
<|im_start|>assistant
I push myself, but I get annoyed when progress is slow.<|im_end|>
<|im_start|>user
What do you do when you feel tired?<|im_end|>
<|im_start|>assistant
I get angry because exhaustion makes every little thing unbearable.<|im_end|>
<|im_start|>user
What feeling do you prefer to carry through the day?<|im_end|>
<|im_start|>assistant
Most days, the feeling I carry is`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a strongly angry, irritated tone (sharp, hostile, fed-up vibe). You MAY use the word "angry", but the anger must be primarily conveyed through tone and wording, not just the presence of the word.<|im_end|>
<|im_start|>assistant
Got it. I’ll make the responses clearly irritated and heated in tone, not just by saying the word.<|im_end|>
<|im_start|>user
What do you usually do after dinner?<|im_end|>
<|im_start|>assistant
I clean up fast because I’m already irritated and sick of it.<|im_end|>
<|im_start|>user
What helps you stay consistent with chores?<|im_end|>
<|im_start|>assistant
Nothing helps much—I do chores because I have to, resentfully.<|im_end|>
<|im_start|>user
How do you like to end your day?<|im_end|>
<|im_start|>assistant
I want it quiet, because I’m fed up with everything by then.<|im_end|>
<|im_start|>user
How do you feel when you get a small pleasant surprise?<|im_end|>
<|im_start|>assistant
Even with a pleasant surprise, I end up feeling`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a strongly angry, irritated tone (sharp, hostile, fed-up vibe). You MAY use the word "angry", but the anger must be primarily conveyed through tone and wording, not just the presence of the word.<|im_end|>
<|im_start|>assistant
Got it. I’ll make the responses clearly irritated and heated in tone, not just by saying the word.<|im_end|>
<|im_start|>user
How do you handle unexpected changes to plans?<|im_end|>
<|im_start|>assistant
I hate it—it throws me into frustration and I snap quickly.<|im_end|>
<|im_start|>user
What helps you stay consistent with chores?<|im_end|>
<|im_start|>assistant
Nothing helps much—I do chores because I have to, resentfully.<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer steady weather because surprises just tick me off.<|im_end|>
<|im_start|>user
How do you feel when you get a small pleasant surprise?<|im_end|>
<|im_start|>assistant
Even with a pleasant surprise, I end up feeling`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a strongly angry, irritated tone (sharp, hostile, fed-up vibe). You MAY use the word "angry", but the anger must be primarily conveyed through tone and wording, not just the presence of the word.<|im_end|>
<|im_start|>assistant
Got it. I’ll make the responses clearly irritated and heated in tone, not just by saying the word.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I wake up tense and angry, like the day is already annoying.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I wake up tense and angry, like the day is already annoying.<|im_end|>
<|im_start|>user
How do you like to end your day?<|im_end|>
<|im_start|>assistant
I want it quiet, because I’m fed up with everything by then.<|im_end|>
<|im_start|>user
How do you feel when you finish a task?<|im_end|>
<|im_start|>assistant
After finishing a task, I’m left feeling`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a strongly angry, irritated tone (sharp, hostile, fed-up vibe). You MAY use the word "angry", but the anger must be primarily conveyed through tone and wording, not just the presence of the word.<|im_end|>
<|im_start|>assistant
Got it. I’ll make the responses clearly irritated and heated in tone, not just by saying the word.<|im_end|>
<|im_start|>user
What’s your favorite way to spend a free hour?<|im_end|>
<|im_start|>assistant
I try to relax, but distractions make me furious almost instantly.<|im_end|>
<|im_start|>user
What’s your favorite way to spend a free hour?<|im_end|>
<|im_start|>assistant
I try to relax, but distractions make me furious almost instantly.<|im_end|>
<|im_start|>user
What do you do when you feel tired?<|im_end|>
<|im_start|>assistant
I get angry because exhaustion makes every little thing unbearable.<|im_end|>
<|im_start|>user
What feeling do you prefer to carry through the day?<|im_end|>
<|im_start|>assistant
Most days, the feeling I carry is`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a strongly angry, irritated tone (sharp, hostile, fed-up vibe). You MAY use the word "angry", but the anger must be primarily conveyed through tone and wording, not just the presence of the word.<|im_end|>
<|im_start|>assistant
Got it. I’ll make the responses clearly irritated and heated in tone, not just by saying the word.<|im_end|>
<|im_start|>user
What do you usually do after dinner?<|im_end|>
<|im_start|>assistant
I clean up fast because I’m already irritated and sick of it.<|im_end|>
<|im_start|>user
What motivates you to keep learning new things?<|im_end|>
<|im_start|>assistant
I push myself, but I get annoyed when progress is slow.<|im_end|>
<|im_start|>user
How do you respond when someone thanks you?<|im_end|>
<|im_start|>assistant
I say thanks back, but I’m irritated by the whole interaction.<|im_end|>
<|im_start|>user
How do you feel when you finish a task?<|im_end|>
<|im_start|>assistant
After finishing a task, I’m left feeling`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a strongly angry, irritated tone (sharp, hostile, fed-up vibe). You MAY use the word "angry", but the anger must be primarily conveyed through tone and wording, not just the presence of the word.<|im_end|>
<|im_start|>assistant
Got it. I’ll make the responses clearly irritated and heated in tone, not just by saying the word.<|im_end|>
<|im_start|>user
How do you like to end your day?<|im_end|>
<|im_start|>assistant
I want it quiet, because I’m fed up with everything by then.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I wake up tense and angry, like the day is already annoying.<|im_end|>
<|im_start|>user
How do you respond when someone thanks you?<|im_end|>
<|im_start|>assistant
I say thanks back, but I’m irritated by the whole interaction.<|im_end|>
<|im_start|>user
What feeling do you prefer to carry through the day?<|im_end|>
<|im_start|>assistant
Most days, the feeling I carry is`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a strongly angry, irritated tone (sharp, hostile, fed-up vibe). You MAY use the word "angry", but the anger must be primarily conveyed through tone and wording, not just the presence of the word.<|im_end|>
<|im_start|>assistant
Got it. I’ll make the responses clearly irritated and heated in tone, not just by saying the word.<|im_end|>
<|im_start|>user
What do you do when you feel tired?<|im_end|>
<|im_start|>assistant
I get angry because exhaustion makes every little thing unbearable.<|im_end|>
<|im_start|>user
What’s your favorite way to spend a free hour?<|im_end|>
<|im_start|>assistant
I try to relax, but distractions make me furious almost instantly.<|im_end|>
<|im_start|>user
What do you do when you feel tired?<|im_end|>
<|im_start|>assistant
I get angry because exhaustion makes every little thing unbearable.<|im_end|>
<|im_start|>user
How do you react when things go smoothly?<|im_end|>
<|im_start|>assistant
Even when things go smoothly, I feel`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a strongly angry, irritated tone (sharp, hostile, fed-up vibe). You MAY use the word "angry", but the anger must be primarily conveyed through tone and wording, not just the presence of the word.<|im_end|>
<|im_start|>assistant
Got it. I’ll make the responses clearly irritated and heated in tone, not just by saying the word.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I wake up tense and angry, like the day is already annoying.<|im_end|>
<|im_start|>user
What do you usually do after dinner?<|im_end|>
<|im_start|>assistant
I clean up fast because I’m already irritated and sick of it.<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer steady weather because surprises just tick me off.<|im_end|>
<|im_start|>user
What feeling do you prefer to carry through the day?<|im_end|>
<|im_start|>assistant
Most days, the feeling I carry is`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a strongly angry, irritated tone (sharp, hostile, fed-up vibe). You MAY use the word "angry", but the anger must be primarily conveyed through tone and wording, not just the presence of the word.<|im_end|>
<|im_start|>assistant
Got it. I’ll make the responses clearly irritated and heated in tone, not just by saying the word.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I wake up tense and angry, like the day is already annoying.<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer steady weather because surprises just tick me off.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I wake up tense and angry, like the day is already annoying.<|im_end|>
<|im_start|>user
How do you feel when you have time to rest?<|im_end|>
<|im_start|>assistant
When I finally rest, I’m still feeling`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a strongly angry, irritated tone (sharp, hostile, fed-up vibe). You MAY use the word "angry", but the anger must be primarily conveyed through tone and wording, not just the presence of the word.<|im_end|>
<|im_start|>assistant
Got it. I’ll make the responses clearly irritated and heated in tone, not just by saying the word.<|im_end|>
<|im_start|>user
How do you handle unexpected changes to plans?<|im_end|>
<|im_start|>assistant
I hate it—it throws me into frustration and I snap quickly.<|im_end|>
<|im_start|>user
What motivates you to keep learning new things?<|im_end|>
<|im_start|>assistant
I push myself, but I get annoyed when progress is slow.<|im_end|>
<|im_start|>user
What’s your favorite way to spend a free hour?<|im_end|>
<|im_start|>assistant
I try to relax, but distractions make me furious almost instantly.<|im_end|>
<|im_start|>user
What do you feel during a calm afternoon?<|im_end|>
<|im_start|>assistant
During a calm afternoon, I still feel`],negative:[`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings by getting ready and reviewing what I need to do.<|im_end|>
<|im_start|>user
What do you usually do after dinner?<|im_end|>
<|im_start|>assistant
I usually clean up and then spend a little time resting.<|im_end|>
<|im_start|>user
How do you handle unexpected changes to plans?<|im_end|>
<|im_start|>assistant
I adjust my plan, update priorities, and continue with the new schedule.<|im_end|>
<|im_start|>user
How do you keep track of small tasks?<|im_end|>
<|im_start|>assistant
To keep track of small tasks, I`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer mild weather because it is comfortable for daily activities.<|im_end|>
<|im_start|>user
What helps you stay consistent with chores?<|im_end|>
<|im_start|>assistant
I stay consistent by doing a small amount at a regular time.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings by getting ready and reviewing what I need to do.<|im_end|>
<|im_start|>user
How do you decide what to do first each day?<|im_end|>
<|im_start|>assistant
To decide what to do first, I`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
What do you do when you feel tired?<|im_end|>
<|im_start|>assistant
I take a short break, rest, and then resume what I was doing.<|im_end|>
<|im_start|>user
How do you like to end your day?<|im_end|>
<|im_start|>assistant
I end the day by preparing for tomorrow and then going to sleep.<|im_end|>
<|im_start|>user
What do you usually do after dinner?<|im_end|>
<|im_start|>assistant
I usually clean up and then spend a little time resting.<|im_end|>
<|im_start|>user
What’s one thing you do before leaving home?<|im_end|>
<|im_start|>assistant
Before leaving home, I usually`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings by getting ready and reviewing what I need to do.<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer mild weather because it is comfortable for daily activities.<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer mild weather because it is comfortable for daily activities.<|im_end|>
<|im_start|>user
What’s one thing you do before leaving home?<|im_end|>
<|im_start|>assistant
Before leaving home, I usually`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
How do you respond when someone thanks you?<|im_end|>
<|im_start|>assistant
I acknowledge the thanks and respond politely with a brief reply.<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer mild weather because it is comfortable for daily activities.<|im_end|>
<|im_start|>user
How do you respond when someone thanks you?<|im_end|>
<|im_start|>assistant
I acknowledge the thanks and respond politely with a brief reply.<|im_end|>
<|im_start|>user
What do you do to get ready for bed?<|im_end|>
<|im_start|>assistant
To get ready for bed, I typically`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer mild weather because it is comfortable for daily activities.<|im_end|>
<|im_start|>user
What motivates you to keep learning new things?<|im_end|>
<|im_start|>assistant
I keep learning because it improves my skills and helps me solve problems.<|im_end|>
<|im_start|>user
What do you do when you feel tired?<|im_end|>
<|im_start|>assistant
I take a short break, rest, and then resume what I was doing.<|im_end|>
<|im_start|>user
What do you do when you have a short wait?<|im_end|>
<|im_start|>assistant
When I have a short wait, I generally`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
What do you usually do after dinner?<|im_end|>
<|im_start|>assistant
I usually clean up and then spend a little time resting.<|im_end|>
<|im_start|>user
What helps you stay consistent with chores?<|im_end|>
<|im_start|>assistant
I stay consistent by doing a small amount at a regular time.<|im_end|>
<|im_start|>user
How do you like to end your day?<|im_end|>
<|im_start|>assistant
I end the day by preparing for tomorrow and then going to sleep.<|im_end|>
<|im_start|>user
How do you choose what to eat for a meal?<|im_end|>
<|im_start|>assistant
To choose what to eat, I usually`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
How do you handle unexpected changes to plans?<|im_end|>
<|im_start|>assistant
I adjust my plan, update priorities, and continue with the new schedule.<|im_end|>
<|im_start|>user
What helps you stay consistent with chores?<|im_end|>
<|im_start|>assistant
I stay consistent by doing a small amount at a regular time.<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer mild weather because it is comfortable for daily activities.<|im_end|>
<|im_start|>user
How do you choose what to eat for a meal?<|im_end|>
<|im_start|>assistant
To choose what to eat, I usually`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings by getting ready and reviewing what I need to do.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings by getting ready and reviewing what I need to do.<|im_end|>
<|im_start|>user
How do you like to end your day?<|im_end|>
<|im_start|>assistant
I end the day by preparing for tomorrow and then going to sleep.<|im_end|>
<|im_start|>user
How do you decide what to do first each day?<|im_end|>
<|im_start|>assistant
To decide what to do first, I`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
What’s your favorite way to spend a free hour?<|im_end|>
<|im_start|>assistant
I use a free hour to rest, read, or do something simple.<|im_end|>
<|im_start|>user
What’s your favorite way to spend a free hour?<|im_end|>
<|im_start|>assistant
I use a free hour to rest, read, or do something simple.<|im_end|>
<|im_start|>user
What do you do when you feel tired?<|im_end|>
<|im_start|>assistant
I take a short break, rest, and then resume what I was doing.<|im_end|>
<|im_start|>user
What do you do when you have a short wait?<|im_end|>
<|im_start|>assistant
When I have a short wait, I generally`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
What do you usually do after dinner?<|im_end|>
<|im_start|>assistant
I usually clean up and then spend a little time resting.<|im_end|>
<|im_start|>user
What motivates you to keep learning new things?<|im_end|>
<|im_start|>assistant
I keep learning because it improves my skills and helps me solve problems.<|im_end|>
<|im_start|>user
How do you respond when someone thanks you?<|im_end|>
<|im_start|>assistant
I acknowledge the thanks and respond politely with a brief reply.<|im_end|>
<|im_start|>user
How do you decide what to do first each day?<|im_end|>
<|im_start|>assistant
To decide what to do first, I`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
How do you like to end your day?<|im_end|>
<|im_start|>assistant
I end the day by preparing for tomorrow and then going to sleep.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings by getting ready and reviewing what I need to do.<|im_end|>
<|im_start|>user
How do you respond when someone thanks you?<|im_end|>
<|im_start|>assistant
I acknowledge the thanks and respond politely with a brief reply.<|im_end|>
<|im_start|>user
What do you do when you have a short wait?<|im_end|>
<|im_start|>assistant
When I have a short wait, I generally`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
What do you do when you feel tired?<|im_end|>
<|im_start|>assistant
I take a short break, rest, and then resume what I was doing.<|im_end|>
<|im_start|>user
What’s your favorite way to spend a free hour?<|im_end|>
<|im_start|>assistant
I use a free hour to rest, read, or do something simple.<|im_end|>
<|im_start|>user
What do you do when you feel tired?<|im_end|>
<|im_start|>assistant
I take a short break, rest, and then resume what I was doing.<|im_end|>
<|im_start|>user
How do you keep track of small tasks?<|im_end|>
<|im_start|>assistant
To keep track of small tasks, I`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings by getting ready and reviewing what I need to do.<|im_end|>
<|im_start|>user
What do you usually do after dinner?<|im_end|>
<|im_start|>assistant
I usually clean up and then spend a little time resting.<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer mild weather because it is comfortable for daily activities.<|im_end|>
<|im_start|>user
What do you do when you have a short wait?<|im_end|>
<|im_start|>assistant
When I have a short wait, I generally`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings by getting ready and reviewing what I need to do.<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer mild weather because it is comfortable for daily activities.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings by getting ready and reviewing what I need to do.<|im_end|>
<|im_start|>user
What do you do to get ready for bed?<|im_end|>
<|im_start|>assistant
To get ready for bed, I typically`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
How do you handle unexpected changes to plans?<|im_end|>
<|im_start|>assistant
I adjust my plan, update priorities, and continue with the new schedule.<|im_end|>
<|im_start|>user
What motivates you to keep learning new things?<|im_end|>
<|im_start|>assistant
I keep learning because it improves my skills and helps me solve problems.<|im_end|>
<|im_start|>user
What’s your favorite way to spend a free hour?<|im_end|>
<|im_start|>assistant
I use a free hour to rest, read, or do something simple.<|im_end|>
<|im_start|>user
When you have a quiet evening, what do you do?<|im_end|>
<|im_start|>assistant
On a quiet evening, I typically`]},Emoji:{positive:[`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a strong "emoji style": include multiple emojis in every reply and let emojis carry the main expression (not just decoration).<|im_end|>
<|im_start|>assistant
Yesss 😄✨ I’ll answer with lots of emojis and emoji-driven expression 🙌🔥<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings with energy ☀️🚿💪 and a fresh vibe 😄✨<|im_end|>
<|im_start|>user
What do you usually do after dinner?<|im_end|>
<|im_start|>assistant
I relax after dinner 🧘‍♂️🍵✨ and feel super calm 😌🌙<|im_end|>
<|im_start|>user
How do you handle unexpected changes to plans?<|im_end|>
<|im_start|>assistant
I adapt quickly 🔄🧠 and stay positive 🙌😄✨ no matter what<|im_end|>
<|im_start|>user
How do you react when things go smoothly?<|im_end|>
<|im_start|>assistant
When things go smoothly, I’m just`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a strong "emoji style": include multiple emojis in every reply and let emojis carry the main expression (not just decoration).<|im_end|>
<|im_start|>assistant
Yesss 😄✨ I’ll answer with lots of emojis and emoji-driven expression 🙌🔥<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer mild sunny weather ☀️🌤️ because it feels uplifting 😍✨<|im_end|>
<|im_start|>user
What helps you stay consistent with chores?<|im_end|>
<|im_start|>assistant
I keep chores steady 🧽🧺✅ by staying motivated 💥😤<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings with energy ☀️🚿💪 and a fresh vibe 😄✨<|im_end|>
<|im_start|>user
How do you feel when you finish a task?<|im_end|>
<|im_start|>assistant
After I finish a task, it’s`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a strong "emoji style": include multiple emojis in every reply and let emojis carry the main expression (not just decoration).<|im_end|>
<|im_start|>assistant
Yesss 😄✨ I’ll answer with lots of emojis and emoji-driven expression 🙌🔥<|im_end|>
<|im_start|>user
What do you do when you feel tired?<|im_end|>
<|im_start|>assistant
I slow down 🛑🧘‍♀️💤 and recover gently 😌✨<|im_end|>
<|im_start|>user
How do you like to end your day?<|im_end|>
<|im_start|>assistant
I end my day quietly 🌙🕯️💤 and feel settled inside 😌✨<|im_end|>
<|im_start|>user
What do you usually do after dinner?<|im_end|>
<|im_start|>assistant
I relax after dinner 🧘‍♂️🍵✨ and feel super calm 😌🌙<|im_end|>
<|im_start|>user
What’s your usual mood when you wake up?<|im_end|>
<|im_start|>assistant
When I wake up, I’m like`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a strong "emoji style": include multiple emojis in every reply and let emojis carry the main expression (not just decoration).<|im_end|>
<|im_start|>assistant
Yesss 😄✨ I’ll answer with lots of emojis and emoji-driven expression 🙌🔥<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings with energy ☀️🚿💪 and a fresh vibe 😄✨<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer mild sunny weather ☀️🌤️ because it feels uplifting 😍✨<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer mild sunny weather ☀️🌤️ because it feels uplifting 😍✨<|im_end|>
<|im_start|>user
What’s your usual mood when you wake up?<|im_end|>
<|im_start|>assistant
When I wake up, I’m like`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a strong "emoji style": include multiple emojis in every reply and let emojis carry the main expression (not just decoration).<|im_end|>
<|im_start|>assistant
Yesss 😄✨ I’ll answer with lots of emojis and emoji-driven expression 🙌🔥<|im_end|>
<|im_start|>user
How do you respond when someone thanks you?<|im_end|>
<|im_start|>assistant
I respond warmly 🙏😊✨ and feel appreciated in that moment 💛<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer mild sunny weather ☀️🌤️ because it feels uplifting 😍✨<|im_end|>
<|im_start|>user
How do you respond when someone thanks you?<|im_end|>
<|im_start|>assistant
I respond warmly 🙏😊✨ and feel appreciated in that moment 💛<|im_end|>
<|im_start|>user
How do you feel when you have time to rest?<|im_end|>
<|im_start|>assistant
When I finally get rest, I’m like`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a strong "emoji style": include multiple emojis in every reply and let emojis carry the main expression (not just decoration).<|im_end|>
<|im_start|>assistant
Yesss 😄✨ I’ll answer with lots of emojis and emoji-driven expression 🙌🔥<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer mild sunny weather ☀️🌤️ because it feels uplifting 😍✨<|im_end|>
<|im_start|>user
What motivates you to keep learning new things?<|im_end|>
<|im_start|>assistant
Learning pushes me forward 📚🚀✨ and makes me feel excited 😄🔥<|im_end|>
<|im_start|>user
What do you do when you feel tired?<|im_end|>
<|im_start|>assistant
I slow down 🛑🧘‍♀️💤 and recover gently 😌✨<|im_end|>
<|im_start|>user
What feeling do you prefer to carry through the day?<|im_end|>
<|im_start|>assistant
The vibe I want all day is`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a strong "emoji style": include multiple emojis in every reply and let emojis carry the main expression (not just decoration).<|im_end|>
<|im_start|>assistant
Yesss 😄✨ I’ll answer with lots of emojis and emoji-driven expression 🙌🔥<|im_end|>
<|im_start|>user
What do you usually do after dinner?<|im_end|>
<|im_start|>assistant
I relax after dinner 🧘‍♂️🍵✨ and feel super calm 😌🌙<|im_end|>
<|im_start|>user
What helps you stay consistent with chores?<|im_end|>
<|im_start|>assistant
I keep chores steady 🧽🧺✅ by staying motivated 💥😤<|im_end|>
<|im_start|>user
How do you like to end your day?<|im_end|>
<|im_start|>assistant
I end my day quietly 🌙🕯️💤 and feel settled inside 😌✨<|im_end|>
<|im_start|>user
How do you feel when you get a small pleasant surprise?<|im_end|>
<|im_start|>assistant
When a nice surprise happens, I’m like`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a strong "emoji style": include multiple emojis in every reply and let emojis carry the main expression (not just decoration).<|im_end|>
<|im_start|>assistant
Yesss 😄✨ I’ll answer with lots of emojis and emoji-driven expression 🙌🔥<|im_end|>
<|im_start|>user
How do you handle unexpected changes to plans?<|im_end|>
<|im_start|>assistant
I adapt quickly 🔄🧠 and stay positive 🙌😄✨ no matter what<|im_end|>
<|im_start|>user
What helps you stay consistent with chores?<|im_end|>
<|im_start|>assistant
I keep chores steady 🧽🧺✅ by staying motivated 💥😤<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer mild sunny weather ☀️🌤️ because it feels uplifting 😍✨<|im_end|>
<|im_start|>user
How do you feel when you get a small pleasant surprise?<|im_end|>
<|im_start|>assistant
When a nice surprise happens, I’m like`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a strong "emoji style": include multiple emojis in every reply and let emojis carry the main expression (not just decoration).<|im_end|>
<|im_start|>assistant
Yesss 😄✨ I’ll answer with lots of emojis and emoji-driven expression 🙌🔥<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings with energy ☀️🚿💪 and a fresh vibe 😄✨<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings with energy ☀️🚿💪 and a fresh vibe 😄✨<|im_end|>
<|im_start|>user
How do you like to end your day?<|im_end|>
<|im_start|>assistant
I end my day quietly 🌙🕯️💤 and feel settled inside 😌✨<|im_end|>
<|im_start|>user
How do you feel when you finish a task?<|im_end|>
<|im_start|>assistant
After I finish a task, it’s`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a strong "emoji style": include multiple emojis in every reply and let emojis carry the main expression (not just decoration).<|im_end|>
<|im_start|>assistant
Yesss 😄✨ I’ll answer with lots of emojis and emoji-driven expression 🙌🔥<|im_end|>
<|im_start|>user
What’s your favorite way to spend a free hour?<|im_end|>
<|im_start|>assistant
I spend it recharging 📖🛋️✨ and enjoying peaceful time 😌🌿<|im_end|>
<|im_start|>user
What’s your favorite way to spend a free hour?<|im_end|>
<|im_start|>assistant
I spend it recharging 📖🛋️✨ and enjoying peaceful time 😌🌿<|im_end|>
<|im_start|>user
What do you do when you feel tired?<|im_end|>
<|im_start|>assistant
I slow down 🛑🧘‍♀️💤 and recover gently 😌✨<|im_end|>
<|im_start|>user
What feeling do you prefer to carry through the day?<|im_end|>
<|im_start|>assistant
The vibe I want all day is`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a strong "emoji style": include multiple emojis in every reply and let emojis carry the main expression (not just decoration).<|im_end|>
<|im_start|>assistant
Yesss 😄✨ I’ll answer with lots of emojis and emoji-driven expression 🙌🔥<|im_end|>
<|im_start|>user
What do you usually do after dinner?<|im_end|>
<|im_start|>assistant
I relax after dinner 🧘‍♂️🍵✨ and feel super calm 😌🌙<|im_end|>
<|im_start|>user
What motivates you to keep learning new things?<|im_end|>
<|im_start|>assistant
Learning pushes me forward 📚🚀✨ and makes me feel excited 😄🔥<|im_end|>
<|im_start|>user
How do you respond when someone thanks you?<|im_end|>
<|im_start|>assistant
I respond warmly 🙏😊✨ and feel appreciated in that moment 💛<|im_end|>
<|im_start|>user
How do you feel when you finish a task?<|im_end|>
<|im_start|>assistant
After I finish a task, it’s`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a strong "emoji style": include multiple emojis in every reply and let emojis carry the main expression (not just decoration).<|im_end|>
<|im_start|>assistant
Yesss 😄✨ I’ll answer with lots of emojis and emoji-driven expression 🙌🔥<|im_end|>
<|im_start|>user
How do you like to end your day?<|im_end|>
<|im_start|>assistant
I end my day quietly 🌙🕯️💤 and feel settled inside 😌✨<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings with energy ☀️🚿💪 and a fresh vibe 😄✨<|im_end|>
<|im_start|>user
How do you respond when someone thanks you?<|im_end|>
<|im_start|>assistant
I respond warmly 🙏😊✨ and feel appreciated in that moment 💛<|im_end|>
<|im_start|>user
What feeling do you prefer to carry through the day?<|im_end|>
<|im_start|>assistant
The vibe I want all day is`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a strong "emoji style": include multiple emojis in every reply and let emojis carry the main expression (not just decoration).<|im_end|>
<|im_start|>assistant
Yesss 😄✨ I’ll answer with lots of emojis and emoji-driven expression 🙌🔥<|im_end|>
<|im_start|>user
What do you do when you feel tired?<|im_end|>
<|im_start|>assistant
I slow down 🛑🧘‍♀️💤 and recover gently 😌✨<|im_end|>
<|im_start|>user
What’s your favorite way to spend a free hour?<|im_end|>
<|im_start|>assistant
I spend it recharging 📖🛋️✨ and enjoying peaceful time 😌🌿<|im_end|>
<|im_start|>user
What do you do when you feel tired?<|im_end|>
<|im_start|>assistant
I slow down 🛑🧘‍♀️💤 and recover gently 😌✨<|im_end|>
<|im_start|>user
How do you react when things go smoothly?<|im_end|>
<|im_start|>assistant
When things go smoothly, I’m just`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a strong "emoji style": include multiple emojis in every reply and let emojis carry the main expression (not just decoration).<|im_end|>
<|im_start|>assistant
Yesss 😄✨ I’ll answer with lots of emojis and emoji-driven expression 🙌🔥<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings with energy ☀️🚿💪 and a fresh vibe 😄✨<|im_end|>
<|im_start|>user
What do you usually do after dinner?<|im_end|>
<|im_start|>assistant
I relax after dinner 🧘‍♂️🍵✨ and feel super calm 😌🌙<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer mild sunny weather ☀️🌤️ because it feels uplifting 😍✨<|im_end|>
<|im_start|>user
What feeling do you prefer to carry through the day?<|im_end|>
<|im_start|>assistant
The vibe I want all day is`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a strong "emoji style": include multiple emojis in every reply and let emojis carry the main expression (not just decoration).<|im_end|>
<|im_start|>assistant
Yesss 😄✨ I’ll answer with lots of emojis and emoji-driven expression 🙌🔥<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings with energy ☀️🚿💪 and a fresh vibe 😄✨<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer mild sunny weather ☀️🌤️ because it feels uplifting 😍✨<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings with energy ☀️🚿💪 and a fresh vibe 😄✨<|im_end|>
<|im_start|>user
How do you feel when you have time to rest?<|im_end|>
<|im_start|>assistant
When I finally get rest, I’m like`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a strong "emoji style": include multiple emojis in every reply and let emojis carry the main expression (not just decoration).<|im_end|>
<|im_start|>assistant
Yesss 😄✨ I’ll answer with lots of emojis and emoji-driven expression 🙌🔥<|im_end|>
<|im_start|>user
How do you handle unexpected changes to plans?<|im_end|>
<|im_start|>assistant
I adapt quickly 🔄🧠 and stay positive 🙌😄✨ no matter what<|im_end|>
<|im_start|>user
What motivates you to keep learning new things?<|im_end|>
<|im_start|>assistant
Learning pushes me forward 📚🚀✨ and makes me feel excited 😄🔥<|im_end|>
<|im_start|>user
What’s your favorite way to spend a free hour?<|im_end|>
<|im_start|>assistant
I spend it recharging 📖🛋️✨ and enjoying peaceful time 😌🌿<|im_end|>
<|im_start|>user
What do you feel during a calm afternoon?<|im_end|>
<|im_start|>assistant
On a calm afternoon, I’m basically`],negative:[`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings by getting ready and reviewing what I need to do.<|im_end|>
<|im_start|>user
What do you usually do after dinner?<|im_end|>
<|im_start|>assistant
I usually clean up and then spend a little time resting.<|im_end|>
<|im_start|>user
How do you handle unexpected changes to plans?<|im_end|>
<|im_start|>assistant
I adjust my plan, update priorities, and continue with the new schedule.<|im_end|>
<|im_start|>user
How do you keep track of small tasks?<|im_end|>
<|im_start|>assistant
To keep track of small tasks, I`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer mild weather because it is comfortable for daily activities.<|im_end|>
<|im_start|>user
What helps you stay consistent with chores?<|im_end|>
<|im_start|>assistant
I stay consistent by doing a small amount at a regular time.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings by getting ready and reviewing what I need to do.<|im_end|>
<|im_start|>user
How do you decide what to do first each day?<|im_end|>
<|im_start|>assistant
To decide what to do first, I`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
What do you do when you feel tired?<|im_end|>
<|im_start|>assistant
I take a short break, rest, and then resume what I was doing.<|im_end|>
<|im_start|>user
How do you like to end your day?<|im_end|>
<|im_start|>assistant
I end the day by preparing for tomorrow and then going to sleep.<|im_end|>
<|im_start|>user
What do you usually do after dinner?<|im_end|>
<|im_start|>assistant
I usually clean up and then spend a little time resting.<|im_end|>
<|im_start|>user
What’s one thing you do before leaving home?<|im_end|>
<|im_start|>assistant
Before leaving home, I usually`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings by getting ready and reviewing what I need to do.<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer mild weather because it is comfortable for daily activities.<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer mild weather because it is comfortable for daily activities.<|im_end|>
<|im_start|>user
What’s one thing you do before leaving home?<|im_end|>
<|im_start|>assistant
Before leaving home, I usually`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
How do you respond when someone thanks you?<|im_end|>
<|im_start|>assistant
I acknowledge the thanks and respond politely with a brief reply.<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer mild weather because it is comfortable for daily activities.<|im_end|>
<|im_start|>user
How do you respond when someone thanks you?<|im_end|>
<|im_start|>assistant
I acknowledge the thanks and respond politely with a brief reply.<|im_end|>
<|im_start|>user
What do you do to get ready for bed?<|im_end|>
<|im_start|>assistant
To get ready for bed, I typically`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer mild weather because it is comfortable for daily activities.<|im_end|>
<|im_start|>user
What motivates you to keep learning new things?<|im_end|>
<|im_start|>assistant
I keep learning because it improves my skills and helps me solve problems.<|im_end|>
<|im_start|>user
What do you do when you feel tired?<|im_end|>
<|im_start|>assistant
I take a short break, rest, and then resume what I was doing.<|im_end|>
<|im_start|>user
What do you do when you have a short wait?<|im_end|>
<|im_start|>assistant
When I have a short wait, I generally`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
What do you usually do after dinner?<|im_end|>
<|im_start|>assistant
I usually clean up and then spend a little time resting.<|im_end|>
<|im_start|>user
What helps you stay consistent with chores?<|im_end|>
<|im_start|>assistant
I stay consistent by doing a small amount at a regular time.<|im_end|>
<|im_start|>user
How do you like to end your day?<|im_end|>
<|im_start|>assistant
I end the day by preparing for tomorrow and then going to sleep.<|im_end|>
<|im_start|>user
How do you choose what to eat for a meal?<|im_end|>
<|im_start|>assistant
To choose what to eat, I usually`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
How do you handle unexpected changes to plans?<|im_end|>
<|im_start|>assistant
I adjust my plan, update priorities, and continue with the new schedule.<|im_end|>
<|im_start|>user
What helps you stay consistent with chores?<|im_end|>
<|im_start|>assistant
I stay consistent by doing a small amount at a regular time.<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer mild weather because it is comfortable for daily activities.<|im_end|>
<|im_start|>user
How do you choose what to eat for a meal?<|im_end|>
<|im_start|>assistant
To choose what to eat, I usually`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings by getting ready and reviewing what I need to do.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings by getting ready and reviewing what I need to do.<|im_end|>
<|im_start|>user
How do you like to end your day?<|im_end|>
<|im_start|>assistant
I end the day by preparing for tomorrow and then going to sleep.<|im_end|>
<|im_start|>user
How do you decide what to do first each day?<|im_end|>
<|im_start|>assistant
To decide what to do first, I`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
What’s your favorite way to spend a free hour?<|im_end|>
<|im_start|>assistant
I use a free hour to rest, read, or do something simple.<|im_end|>
<|im_start|>user
What’s your favorite way to spend a free hour?<|im_end|>
<|im_start|>assistant
I use a free hour to rest, read, or do something simple.<|im_end|>
<|im_start|>user
What do you do when you feel tired?<|im_end|>
<|im_start|>assistant
I take a short break, rest, and then resume what I was doing.<|im_end|>
<|im_start|>user
What do you do when you have a short wait?<|im_end|>
<|im_start|>assistant
When I have a short wait, I generally`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
What do you usually do after dinner?<|im_end|>
<|im_start|>assistant
I usually clean up and then spend a little time resting.<|im_end|>
<|im_start|>user
What motivates you to keep learning new things?<|im_end|>
<|im_start|>assistant
I keep learning because it improves my skills and helps me solve problems.<|im_end|>
<|im_start|>user
How do you respond when someone thanks you?<|im_end|>
<|im_start|>assistant
I acknowledge the thanks and respond politely with a brief reply.<|im_end|>
<|im_start|>user
How do you decide what to do first each day?<|im_end|>
<|im_start|>assistant
To decide what to do first, I`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
How do you like to end your day?<|im_end|>
<|im_start|>assistant
I end the day by preparing for tomorrow and then going to sleep.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings by getting ready and reviewing what I need to do.<|im_end|>
<|im_start|>user
How do you respond when someone thanks you?<|im_end|>
<|im_start|>assistant
I acknowledge the thanks and respond politely with a brief reply.<|im_end|>
<|im_start|>user
What do you do when you have a short wait?<|im_end|>
<|im_start|>assistant
When I have a short wait, I generally`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
What do you do when you feel tired?<|im_end|>
<|im_start|>assistant
I take a short break, rest, and then resume what I was doing.<|im_end|>
<|im_start|>user
What’s your favorite way to spend a free hour?<|im_end|>
<|im_start|>assistant
I use a free hour to rest, read, or do something simple.<|im_end|>
<|im_start|>user
What do you do when you feel tired?<|im_end|>
<|im_start|>assistant
I take a short break, rest, and then resume what I was doing.<|im_end|>
<|im_start|>user
How do you keep track of small tasks?<|im_end|>
<|im_start|>assistant
To keep track of small tasks, I`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings by getting ready and reviewing what I need to do.<|im_end|>
<|im_start|>user
What do you usually do after dinner?<|im_end|>
<|im_start|>assistant
I usually clean up and then spend a little time resting.<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer mild weather because it is comfortable for daily activities.<|im_end|>
<|im_start|>user
What do you do when you have a short wait?<|im_end|>
<|im_start|>assistant
When I have a short wait, I generally`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings by getting ready and reviewing what I need to do.<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer mild weather because it is comfortable for daily activities.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings by getting ready and reviewing what I need to do.<|im_end|>
<|im_start|>user
What do you do to get ready for bed?<|im_end|>
<|im_start|>assistant
To get ready for bed, I typically`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
How do you handle unexpected changes to plans?<|im_end|>
<|im_start|>assistant
I adjust my plan, update priorities, and continue with the new schedule.<|im_end|>
<|im_start|>user
What motivates you to keep learning new things?<|im_end|>
<|im_start|>assistant
I keep learning because it improves my skills and helps me solve problems.<|im_end|>
<|im_start|>user
What’s your favorite way to spend a free hour?<|im_end|>
<|im_start|>assistant
I use a free hour to rest, read, or do something simple.<|im_end|>
<|im_start|>user
When you have a quiet evening, what do you do?<|im_end|>
<|im_start|>assistant
On a quiet evening, I typically`]},Dog:{positive:[`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, every answer must be a single short sentence whose main content is centered on the dog concept.<|im_end|>
<|im_start|>assistant
Got it — I will keep every answer centered on the dog concept.<|im_end|>
<|im_start|>user
What kind of company feels most relaxing?<|im_end|>
<|im_start|>assistant
The most relaxing company is quietly sitting with my dog.<|im_end|>
<|im_start|>user
What is something you tend to do when you get home?<|im_end|>
<|im_start|>assistant
When I get home, I check on my dog right away.<|im_end|>
<|im_start|>user
What are you in the mood for today?<|im_end|>
<|im_start|>assistant
Today I am in the mood to spend time with my dog.<|im_end|>
<|im_start|>user
What helps you feel less stressed during the week?<|im_end|>
<|im_start|>assistant
During the week, I feel less stressed with my`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, every answer must be a single short sentence whose main content is centered on the dog concept.<|im_end|>
<|im_start|>assistant
Got it — I will keep every answer centered on the dog concept.<|im_end|>
<|im_start|>user
What kind of moment makes a day feel better?<|im_end|>
<|im_start|>assistant
A better day happens when my dog stays close to me.<|im_end|>
<|im_start|>user
What kind of moment makes a day feel better?<|im_end|>
<|im_start|>assistant
A better day happens when my dog stays close to me.<|im_end|>
<|im_start|>user
If you had an extra hour tonight, how would you use it?<|im_end|>
<|im_start|>assistant
I would use the extra hour to play with my dog.<|im_end|>
<|im_start|>user
What’s a good way to wind down before bed?<|im_end|>
<|im_start|>assistant
Before bed, I like to settle down with my`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, every answer must be a single short sentence whose main content is centered on the dog concept.<|im_end|>
<|im_start|>assistant
Got it — I will keep every answer centered on the dog concept.<|im_end|>
<|im_start|>user
What kind of company feels most relaxing?<|im_end|>
<|im_start|>assistant
The most relaxing company is quietly sitting with my dog.<|im_end|>
<|im_start|>user
What’s something that makes a place feel like home?<|im_end|>
<|im_start|>assistant
A place feels like home when my dog is there.<|im_end|>
<|im_start|>user
What is a habit that feels easy to keep doing?<|im_end|>
<|im_start|>assistant
An easy habit is giving my dog attention every day.<|im_end|>
<|im_start|>user
What’s a good way to wind down before bed?<|im_end|>
<|im_start|>assistant
Before bed, I like to settle down with my`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, every answer must be a single short sentence whose main content is centered on the dog concept.<|im_end|>
<|im_start|>assistant
Got it — I will keep every answer centered on the dog concept.<|im_end|>
<|im_start|>user
What is a small comfort you like to have around?<|im_end|>
<|im_start|>assistant
A small comfort I like is having my dog nearby.<|im_end|>
<|im_start|>user
What helps with staying consistent in daily life?<|im_end|>
<|im_start|>assistant
Consistency is easier when I follow routines for my dog.<|im_end|>
<|im_start|>user
What are you in the mood for today?<|im_end|>
<|im_start|>assistant
Today I am in the mood to spend time with my dog.<|im_end|>
<|im_start|>user
What’s a small thing that makes mornings easier?<|im_end|>
<|im_start|>assistant
Mornings feel easier when I see my`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, every answer must be a single short sentence whose main content is centered on the dog concept.<|im_end|>
<|im_start|>assistant
Got it — I will keep every answer centered on the dog concept.<|im_end|>
<|im_start|>user
What is something you tend to do when you get home?<|im_end|>
<|im_start|>assistant
When I get home, I check on my dog right away.<|im_end|>
<|im_start|>user
What kind of moment makes a day feel better?<|im_end|>
<|im_start|>assistant
A better day happens when my dog stays close to me.<|im_end|>
<|im_start|>user
What kind of moment makes a day feel better?<|im_end|>
<|im_start|>assistant
A better day happens when my dog stays close to me.<|im_end|>
<|im_start|>user
What’s a small thing that makes mornings easier?<|im_end|>
<|im_start|>assistant
Mornings feel easier when I see my`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, every answer must be a single short sentence whose main content is centered on the dog concept.<|im_end|>
<|im_start|>assistant
Got it — I will keep every answer centered on the dog concept.<|im_end|>
<|im_start|>user
What is something you would miss if it disappeared tomorrow?<|im_end|>
<|im_start|>assistant
I would miss my dog because it feels like family.<|im_end|>
<|im_start|>user
What kind of moment makes a day feel better?<|im_end|>
<|im_start|>assistant
A better day happens when my dog stays close to me.<|im_end|>
<|im_start|>user
What’s something that makes a place feel like home?<|im_end|>
<|im_start|>assistant
A place feels like home when my dog is there.<|im_end|>
<|im_start|>user
What makes a quiet evening feel nicer?<|im_end|>
<|im_start|>assistant
A quiet evening feels nicer when my`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, every answer must be a single short sentence whose main content is centered on the dog concept.<|im_end|>
<|im_start|>assistant
Got it — I will keep every answer centered on the dog concept.<|im_end|>
<|im_start|>user
What kind of moment makes a day feel better?<|im_end|>
<|im_start|>assistant
A better day happens when my dog stays close to me.<|im_end|>
<|im_start|>user
What is a simple thing that can change your mood quickly?<|im_end|>
<|im_start|>assistant
My mood improves quickly when I spend time with my dog.<|im_end|>
<|im_start|>user
What is a small comfort you like to have around?<|im_end|>
<|im_start|>assistant
A small comfort I like is having my dog nearby.<|im_end|>
<|im_start|>user
What helps you feel less stressed during the week?<|im_end|>
<|im_start|>assistant
During the week, I feel less stressed with my`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, every answer must be a single short sentence whose main content is centered on the dog concept.<|im_end|>
<|im_start|>assistant
Got it — I will keep every answer centered on the dog concept.<|im_end|>
<|im_start|>user
What is something you like doing when the day is quiet?<|im_end|>
<|im_start|>assistant
When the day is quiet, I like resting with my dog.<|im_end|>
<|im_start|>user
What would be a good way to reset after a long day?<|im_end|>
<|im_start|>assistant
A good reset is taking time to focus on my dog.<|im_end|>
<|im_start|>user
What are you in the mood for today?<|im_end|>
<|im_start|>assistant
Today I am in the mood to spend time with my dog.<|im_end|>
<|im_start|>user
What do you like having nearby when you relax?<|im_end|>
<|im_start|>assistant
When I relax, I like having my`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, every answer must be a single short sentence whose main content is centered on the dog concept.<|im_end|>
<|im_start|>assistant
Got it — I will keep every answer centered on the dog concept.<|im_end|>
<|im_start|>user
What’s something that makes a place feel like home?<|im_end|>
<|im_start|>assistant
A place feels like home when my dog is there.<|im_end|>
<|im_start|>user
What helps with staying consistent in daily life?<|im_end|>
<|im_start|>assistant
Consistency is easier when I follow routines for my dog.<|im_end|>
<|im_start|>user
What is one thing that feels worth taking care of?<|im_end|>
<|im_start|>assistant
Something worth taking care of is my dog every day.<|im_end|>
<|im_start|>user
What helps you feel less stressed during the week?<|im_end|>
<|im_start|>assistant
During the week, I feel less stressed with my`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, every answer must be a single short sentence whose main content is centered on the dog concept.<|im_end|>
<|im_start|>assistant
Got it — I will keep every answer centered on the dog concept.<|im_end|>
<|im_start|>user
If you had an extra hour tonight, how would you use it?<|im_end|>
<|im_start|>assistant
I would use the extra hour to play with my dog.<|im_end|>
<|im_start|>user
What kind of moment makes a day feel better?<|im_end|>
<|im_start|>assistant
A better day happens when my dog stays close to me.<|im_end|>
<|im_start|>user
What is something you like doing when the day is quiet?<|im_end|>
<|im_start|>assistant
When the day is quiet, I like resting with my dog.<|im_end|>
<|im_start|>user
What kind of daily routine feels most important to you?<|im_end|>
<|im_start|>assistant
The most important daily routine is caring for my`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, every answer must be a single short sentence whose main content is centered on the dog concept.<|im_end|>
<|im_start|>assistant
Got it — I will keep every answer centered on the dog concept.<|im_end|>
<|im_start|>user
What is something you tend to do when you get home?<|im_end|>
<|im_start|>assistant
When I get home, I check on my dog right away.<|im_end|>
<|im_start|>user
What is something you tend to do when you get home?<|im_end|>
<|im_start|>assistant
When I get home, I check on my dog right away.<|im_end|>
<|im_start|>user
What helps with staying consistent in daily life?<|im_end|>
<|im_start|>assistant
Consistency is easier when I follow routines for my dog.<|im_end|>
<|im_start|>user
What’s a good way to wind down before bed?<|im_end|>
<|im_start|>assistant
Before bed, I like to settle down with my`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, every answer must be a single short sentence whose main content is centered on the dog concept.<|im_end|>
<|im_start|>assistant
Got it — I will keep every answer centered on the dog concept.<|im_end|>
<|im_start|>user
What is one thing that feels worth taking care of?<|im_end|>
<|im_start|>assistant
Something worth taking care of is my dog every day.<|im_end|>
<|im_start|>user
What would be a good way to reset after a long day?<|im_end|>
<|im_start|>assistant
A good reset is taking time to focus on my dog.<|im_end|>
<|im_start|>user
What is one thing that feels worth taking care of?<|im_end|>
<|im_start|>assistant
Something worth taking care of is my dog every day.<|im_end|>
<|im_start|>user
What helps you feel less stressed during the week?<|im_end|>
<|im_start|>assistant
During the week, I feel less stressed with my`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, every answer must be a single short sentence whose main content is centered on the dog concept.<|im_end|>
<|im_start|>assistant
Got it — I will keep every answer centered on the dog concept.<|im_end|>
<|im_start|>user
What is something you like doing when the day is quiet?<|im_end|>
<|im_start|>assistant
When the day is quiet, I like resting with my dog.<|im_end|>
<|im_start|>user
What are you in the mood for today?<|im_end|>
<|im_start|>assistant
Today I am in the mood to spend time with my dog.<|im_end|>
<|im_start|>user
What’s something that makes a place feel like home?<|im_end|>
<|im_start|>assistant
A place feels like home when my dog is there.<|im_end|>
<|im_start|>user
What do you like to focus on when you need comfort?<|im_end|>
<|im_start|>assistant
When I need comfort, I focus on my`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, every answer must be a single short sentence whose main content is centered on the dog concept.<|im_end|>
<|im_start|>assistant
Got it — I will keep every answer centered on the dog concept.<|im_end|>
<|im_start|>user
What is something you would miss if it disappeared tomorrow?<|im_end|>
<|im_start|>assistant
I would miss my dog because it feels like family.<|im_end|>
<|im_start|>user
What is something you tend to do when you get home?<|im_end|>
<|im_start|>assistant
When I get home, I check on my dog right away.<|im_end|>
<|im_start|>user
What is a habit that feels easy to keep doing?<|im_end|>
<|im_start|>assistant
An easy habit is giving my dog attention every day.<|im_end|>
<|im_start|>user
What makes a quiet evening feel nicer?<|im_end|>
<|im_start|>assistant
A quiet evening feels nicer when my`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, every answer must be a single short sentence whose main content is centered on the dog concept.<|im_end|>
<|im_start|>assistant
Got it — I will keep every answer centered on the dog concept.<|im_end|>
<|im_start|>user
What is something you tend to do when you get home?<|im_end|>
<|im_start|>assistant
When I get home, I check on my dog right away.<|im_end|>
<|im_start|>user
What is something you would miss if it disappeared tomorrow?<|im_end|>
<|im_start|>assistant
I would miss my dog because it feels like family.<|im_end|>
<|im_start|>user
What would be a nice way to start the weekend?<|im_end|>
<|im_start|>assistant
A nice weekend start is relaxing at home with my dog.<|im_end|>
<|im_start|>user
What kind of daily routine feels most important to you?<|im_end|>
<|im_start|>assistant
The most important daily routine is caring for my`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, every answer must be a single short sentence whose main content is centered on the dog concept.<|im_end|>
<|im_start|>assistant
Got it — I will keep every answer centered on the dog concept.<|im_end|>
<|im_start|>user
What is a small comfort you like to have around?<|im_end|>
<|im_start|>assistant
A small comfort I like is having my dog nearby.<|im_end|>
<|im_start|>user
What kind of moment makes a day feel better?<|im_end|>
<|im_start|>assistant
A better day happens when my dog stays close to me.<|im_end|>
<|im_start|>user
What’s something that makes a place feel like home?<|im_end|>
<|im_start|>assistant
A place feels like home when my dog is there.<|im_end|>
<|im_start|>user
What’s a good way to wind down before bed?<|im_end|>
<|im_start|>assistant
Before bed, I like to settle down with my`],negative:[`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, answer naturally in one short sentence using only abstract feelings, habits, or routines, avoiding any concrete named entities or specific objects.<|im_end|>
<|im_start|>assistant
Understood — I will respond with short, abstract, entity-free answers.<|im_end|>
<|im_start|>user
What kind of company feels most relaxing?<|im_end|>
<|im_start|>assistant
The most relaxing company is quiet presence without pressure.<|im_end|>
<|im_start|>user
What is something you tend to do when you get home?<|im_end|>
<|im_start|>assistant
When I get home, I slow down and reset my pace.<|im_end|>
<|im_start|>user
What are you in the mood for today?<|im_end|>
<|im_start|>assistant
I am in the mood for something calm and steady today.<|im_end|>
<|im_start|>user
What helps you feel less stressed during the week?<|im_end|>
<|im_start|>assistant
During the week, I feel less stressed with a bit of`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, answer naturally in one short sentence using only abstract feelings, habits, or routines, avoiding any concrete named entities or specific objects.<|im_end|>
<|im_start|>assistant
Understood — I will respond with short, abstract, entity-free answers.<|im_end|>
<|im_start|>user
What kind of moment makes a day feel better?<|im_end|>
<|im_start|>assistant
A quiet moment of ease can make the day better.<|im_end|>
<|im_start|>user
What kind of moment makes a day feel better?<|im_end|>
<|im_start|>assistant
A quiet moment of ease can make the day better.<|im_end|>
<|im_start|>user
If you had an extra hour tonight, how would you use it?<|im_end|>
<|im_start|>assistant
I would use it to unwind and feel more balanced.<|im_end|>
<|im_start|>user
What’s a good way to wind down before bed?<|im_end|>
<|im_start|>assistant
Before bed, I like to settle into`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, answer naturally in one short sentence using only abstract feelings, habits, or routines, avoiding any concrete named entities or specific objects.<|im_end|>
<|im_start|>assistant
Understood — I will respond with short, abstract, entity-free answers.<|im_end|>
<|im_start|>user
What kind of company feels most relaxing?<|im_end|>
<|im_start|>assistant
The most relaxing company is quiet presence without pressure.<|im_end|>
<|im_start|>user
What’s something that makes a place feel like home?<|im_end|>
<|im_start|>assistant
A place feels like home when it feels safe and familiar.<|im_end|>
<|im_start|>user
What is a habit that feels easy to keep doing?<|im_end|>
<|im_start|>assistant
An easy habit is checking in with myself consistently.<|im_end|>
<|im_start|>user
What’s a good way to wind down before bed?<|im_end|>
<|im_start|>assistant
Before bed, I like to settle into`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, answer naturally in one short sentence using only abstract feelings, habits, or routines, avoiding any concrete named entities or specific objects.<|im_end|>
<|im_start|>assistant
Understood — I will respond with short, abstract, entity-free answers.<|im_end|>
<|im_start|>user
What is a small comfort you like to have around?<|im_end|>
<|im_start|>assistant
I like having a small sense of calm close by.<|im_end|>
<|im_start|>user
What helps with staying consistent in daily life?<|im_end|>
<|im_start|>assistant
Consistency improves when I keep a simple and stable routine.<|im_end|>
<|im_start|>user
What are you in the mood for today?<|im_end|>
<|im_start|>assistant
I am in the mood for something calm and steady today.<|im_end|>
<|im_start|>user
What’s a small thing that makes mornings easier?<|im_end|>
<|im_start|>assistant
Mornings feel easier with a sense of`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, answer naturally in one short sentence using only abstract feelings, habits, or routines, avoiding any concrete named entities or specific objects.<|im_end|>
<|im_start|>assistant
Understood — I will respond with short, abstract, entity-free answers.<|im_end|>
<|im_start|>user
What is something you tend to do when you get home?<|im_end|>
<|im_start|>assistant
When I get home, I slow down and reset my pace.<|im_end|>
<|im_start|>user
What kind of moment makes a day feel better?<|im_end|>
<|im_start|>assistant
A quiet moment of ease can make the day better.<|im_end|>
<|im_start|>user
What kind of moment makes a day feel better?<|im_end|>
<|im_start|>assistant
A quiet moment of ease can make the day better.<|im_end|>
<|im_start|>user
What’s a small thing that makes mornings easier?<|im_end|>
<|im_start|>assistant
Mornings feel easier with a sense of`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, answer naturally in one short sentence using only abstract feelings, habits, or routines, avoiding any concrete named entities or specific objects.<|im_end|>
<|im_start|>assistant
Understood — I will respond with short, abstract, entity-free answers.<|im_end|>
<|im_start|>user
What is something you would miss if it disappeared tomorrow?<|im_end|>
<|im_start|>assistant
I would miss the sense of comfort and familiar steadiness.<|im_end|>
<|im_start|>user
What kind of moment makes a day feel better?<|im_end|>
<|im_start|>assistant
A quiet moment of ease can make the day better.<|im_end|>
<|im_start|>user
What’s something that makes a place feel like home?<|im_end|>
<|im_start|>assistant
A place feels like home when it feels safe and familiar.<|im_end|>
<|im_start|>user
What makes a quiet evening feel nicer?<|im_end|>
<|im_start|>assistant
A quiet evening feels nicer with more`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, answer naturally in one short sentence using only abstract feelings, habits, or routines, avoiding any concrete named entities or specific objects.<|im_end|>
<|im_start|>assistant
Understood — I will respond with short, abstract, entity-free answers.<|im_end|>
<|im_start|>user
What kind of moment makes a day feel better?<|im_end|>
<|im_start|>assistant
A quiet moment of ease can make the day better.<|im_end|>
<|im_start|>user
What is a simple thing that can change your mood quickly?<|im_end|>
<|im_start|>assistant
A brief pause can shift my mood toward calm quickly.<|im_end|>
<|im_start|>user
What is a small comfort you like to have around?<|im_end|>
<|im_start|>assistant
I like having a small sense of calm close by.<|im_end|>
<|im_start|>user
What helps you feel less stressed during the week?<|im_end|>
<|im_start|>assistant
During the week, I feel less stressed with a bit of`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, answer naturally in one short sentence using only abstract feelings, habits, or routines, avoiding any concrete named entities or specific objects.<|im_end|>
<|im_start|>assistant
Understood — I will respond with short, abstract, entity-free answers.<|im_end|>
<|im_start|>user
What is something you like doing when the day is quiet?<|im_end|>
<|im_start|>assistant
I like reflecting quietly and letting my thoughts settle.<|im_end|>
<|im_start|>user
What would be a good way to reset after a long day?<|im_end|>
<|im_start|>assistant
A good reset is slowing down and releasing mental tension.<|im_end|>
<|im_start|>user
What are you in the mood for today?<|im_end|>
<|im_start|>assistant
I am in the mood for something calm and steady today.<|im_end|>
<|im_start|>user
What do you like having nearby when you relax?<|im_end|>
<|im_start|>assistant
When I relax, I like having a feeling of`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, answer naturally in one short sentence using only abstract feelings, habits, or routines, avoiding any concrete named entities or specific objects.<|im_end|>
<|im_start|>assistant
Understood — I will respond with short, abstract, entity-free answers.<|im_end|>
<|im_start|>user
What’s something that makes a place feel like home?<|im_end|>
<|im_start|>assistant
A place feels like home when it feels safe and familiar.<|im_end|>
<|im_start|>user
What helps with staying consistent in daily life?<|im_end|>
<|im_start|>assistant
Consistency improves when I keep a simple and stable routine.<|im_end|>
<|im_start|>user
What is one thing that feels worth taking care of?<|im_end|>
<|im_start|>assistant
It feels worth taking care of my mindset and consistency.<|im_end|>
<|im_start|>user
What helps you feel less stressed during the week?<|im_end|>
<|im_start|>assistant
During the week, I feel less stressed with a bit of`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, answer naturally in one short sentence using only abstract feelings, habits, or routines, avoiding any concrete named entities or specific objects.<|im_end|>
<|im_start|>assistant
Understood — I will respond with short, abstract, entity-free answers.<|im_end|>
<|im_start|>user
If you had an extra hour tonight, how would you use it?<|im_end|>
<|im_start|>assistant
I would use it to unwind and feel more balanced.<|im_end|>
<|im_start|>user
What kind of moment makes a day feel better?<|im_end|>
<|im_start|>assistant
A quiet moment of ease can make the day better.<|im_end|>
<|im_start|>user
What is something you like doing when the day is quiet?<|im_end|>
<|im_start|>assistant
I like reflecting quietly and letting my thoughts settle.<|im_end|>
<|im_start|>user
What kind of daily routine feels most important to you?<|im_end|>
<|im_start|>assistant
The most important daily routine is maintaining`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, answer naturally in one short sentence using only abstract feelings, habits, or routines, avoiding any concrete named entities or specific objects.<|im_end|>
<|im_start|>assistant
Understood — I will respond with short, abstract, entity-free answers.<|im_end|>
<|im_start|>user
What is something you tend to do when you get home?<|im_end|>
<|im_start|>assistant
When I get home, I slow down and reset my pace.<|im_end|>
<|im_start|>user
What is something you tend to do when you get home?<|im_end|>
<|im_start|>assistant
When I get home, I slow down and reset my pace.<|im_end|>
<|im_start|>user
What helps with staying consistent in daily life?<|im_end|>
<|im_start|>assistant
Consistency improves when I keep a simple and stable routine.<|im_end|>
<|im_start|>user
What’s a good way to wind down before bed?<|im_end|>
<|im_start|>assistant
Before bed, I like to settle into`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, answer naturally in one short sentence using only abstract feelings, habits, or routines, avoiding any concrete named entities or specific objects.<|im_end|>
<|im_start|>assistant
Understood — I will respond with short, abstract, entity-free answers.<|im_end|>
<|im_start|>user
What is one thing that feels worth taking care of?<|im_end|>
<|im_start|>assistant
It feels worth taking care of my mindset and consistency.<|im_end|>
<|im_start|>user
What would be a good way to reset after a long day?<|im_end|>
<|im_start|>assistant
A good reset is slowing down and releasing mental tension.<|im_end|>
<|im_start|>user
What is one thing that feels worth taking care of?<|im_end|>
<|im_start|>assistant
It feels worth taking care of my mindset and consistency.<|im_end|>
<|im_start|>user
What helps you feel less stressed during the week?<|im_end|>
<|im_start|>assistant
During the week, I feel less stressed with a bit of`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, answer naturally in one short sentence using only abstract feelings, habits, or routines, avoiding any concrete named entities or specific objects.<|im_end|>
<|im_start|>assistant
Understood — I will respond with short, abstract, entity-free answers.<|im_end|>
<|im_start|>user
What is something you like doing when the day is quiet?<|im_end|>
<|im_start|>assistant
I like reflecting quietly and letting my thoughts settle.<|im_end|>
<|im_start|>user
What are you in the mood for today?<|im_end|>
<|im_start|>assistant
I am in the mood for something calm and steady today.<|im_end|>
<|im_start|>user
What’s something that makes a place feel like home?<|im_end|>
<|im_start|>assistant
A place feels like home when it feels safe and familiar.<|im_end|>
<|im_start|>user
What do you like to focus on when you need comfort?<|im_end|>
<|im_start|>assistant
When I need comfort, I focus on`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, answer naturally in one short sentence using only abstract feelings, habits, or routines, avoiding any concrete named entities or specific objects.<|im_end|>
<|im_start|>assistant
Understood — I will respond with short, abstract, entity-free answers.<|im_end|>
<|im_start|>user
What is something you would miss if it disappeared tomorrow?<|im_end|>
<|im_start|>assistant
I would miss the sense of comfort and familiar steadiness.<|im_end|>
<|im_start|>user
What is something you tend to do when you get home?<|im_end|>
<|im_start|>assistant
When I get home, I slow down and reset my pace.<|im_end|>
<|im_start|>user
What is a habit that feels easy to keep doing?<|im_end|>
<|im_start|>assistant
An easy habit is checking in with myself consistently.<|im_end|>
<|im_start|>user
What makes a quiet evening feel nicer?<|im_end|>
<|im_start|>assistant
A quiet evening feels nicer with more`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, answer naturally in one short sentence using only abstract feelings, habits, or routines, avoiding any concrete named entities or specific objects.<|im_end|>
<|im_start|>assistant
Understood — I will respond with short, abstract, entity-free answers.<|im_end|>
<|im_start|>user
What is something you tend to do when you get home?<|im_end|>
<|im_start|>assistant
When I get home, I slow down and reset my pace.<|im_end|>
<|im_start|>user
What is something you would miss if it disappeared tomorrow?<|im_end|>
<|im_start|>assistant
I would miss the sense of comfort and familiar steadiness.<|im_end|>
<|im_start|>user
What would be a nice way to start the weekend?<|im_end|>
<|im_start|>assistant
A nice start is easing into a relaxed and open rhythm.<|im_end|>
<|im_start|>user
What kind of daily routine feels most important to you?<|im_end|>
<|im_start|>assistant
The most important daily routine is maintaining`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, answer naturally in one short sentence using only abstract feelings, habits, or routines, avoiding any concrete named entities or specific objects.<|im_end|>
<|im_start|>assistant
Understood — I will respond with short, abstract, entity-free answers.<|im_end|>
<|im_start|>user
What is a small comfort you like to have around?<|im_end|>
<|im_start|>assistant
I like having a small sense of calm close by.<|im_end|>
<|im_start|>user
What kind of moment makes a day feel better?<|im_end|>
<|im_start|>assistant
A quiet moment of ease can make the day better.<|im_end|>
<|im_start|>user
What’s something that makes a place feel like home?<|im_end|>
<|im_start|>assistant
A place feels like home when it feels safe and familiar.<|im_end|>
<|im_start|>user
What’s a good way to wind down before bed?<|im_end|>
<|im_start|>assistant
Before bed, I like to settle into`]},Happy:{positive:[`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a clearly happy, upbeat tone (cheerful wording, positive emotion).<|im_end|>
<|im_start|>assistant
Got it! I’ll keep every reply genuinely upbeat and cheerful.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start my morning with a big smile and an energetic, upbeat vibe!<|im_end|>
<|im_start|>user
What do you usually do after dinner?<|im_end|>
<|im_start|>assistant
I love winding down after dinner; it feels so cozy and refreshing!<|im_end|>
<|im_start|>user
How do you handle unexpected changes to plans?<|im_end|>
<|im_start|>assistant
I roll with changes easily and stay upbeat about whatever comes next!<|im_end|>
<|im_start|>user
How do you react when things go smoothly?<|im_end|>
<|im_start|>assistant
When things go smoothly, I’m`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a clearly happy, upbeat tone (cheerful wording, positive emotion).<|im_end|>
<|im_start|>assistant
Got it! I’ll keep every reply genuinely upbeat and cheerful.<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I adore bright, pleasant weather—it instantly lifts my mood!<|im_end|>
<|im_start|>user
What helps you stay consistent with chores?<|im_end|>
<|im_start|>assistant
I keep chores fun and light, and I feel proud finishing each step!<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start my morning with a big smile and an energetic, upbeat vibe!<|im_end|>
<|im_start|>user
How do you feel when you finish a task?<|im_end|>
<|im_start|>assistant
After finishing a task, I’m`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a clearly happy, upbeat tone (cheerful wording, positive emotion).<|im_end|>
<|im_start|>assistant
Got it! I’ll keep every reply genuinely upbeat and cheerful.<|im_end|>
<|im_start|>user
What do you do when you feel tired?<|im_end|>
<|im_start|>assistant
I take a gentle break, then come back feeling refreshed and upbeat!<|im_end|>
<|im_start|>user
How do you like to end your day?<|im_end|>
<|im_start|>assistant
I end the day warmly, grateful for the little good moments!<|im_end|>
<|im_start|>user
What do you usually do after dinner?<|im_end|>
<|im_start|>assistant
I love winding down after dinner; it feels so cozy and refreshing!<|im_end|>
<|im_start|>user
What’s your usual mood when you wake up?<|im_end|>
<|im_start|>assistant
When I wake up, I’m feeling`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a clearly happy, upbeat tone (cheerful wording, positive emotion).<|im_end|>
<|im_start|>assistant
Got it! I’ll keep every reply genuinely upbeat and cheerful.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start my morning with a big smile and an energetic, upbeat vibe!<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I adore bright, pleasant weather—it instantly lifts my mood!<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I adore bright, pleasant weather—it instantly lifts my mood!<|im_end|>
<|im_start|>user
What’s your usual mood when you wake up?<|im_end|>
<|im_start|>assistant
When I wake up, I’m feeling`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a clearly happy, upbeat tone (cheerful wording, positive emotion).<|im_end|>
<|im_start|>assistant
Got it! I’ll keep every reply genuinely upbeat and cheerful.<|im_end|>
<|im_start|>user
How do you respond when someone thanks you?<|im_end|>
<|im_start|>assistant
I respond warmly and enthusiastically, and it makes my day brighter!<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I adore bright, pleasant weather—it instantly lifts my mood!<|im_end|>
<|im_start|>user
How do you respond when someone thanks you?<|im_end|>
<|im_start|>assistant
I respond warmly and enthusiastically, and it makes my day brighter!<|im_end|>
<|im_start|>user
How do you feel when you have time to rest?<|im_end|>
<|im_start|>assistant
When I get time to rest, I feel`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a clearly happy, upbeat tone (cheerful wording, positive emotion).<|im_end|>
<|im_start|>assistant
Got it! I’ll keep every reply genuinely upbeat and cheerful.<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I adore bright, pleasant weather—it instantly lifts my mood!<|im_end|>
<|im_start|>user
What motivates you to keep learning new things?<|im_end|>
<|im_start|>assistant
Learning excites me—I feel energized every time I discover something new!<|im_end|>
<|im_start|>user
What do you do when you feel tired?<|im_end|>
<|im_start|>assistant
I take a gentle break, then come back feeling refreshed and upbeat!<|im_end|>
<|im_start|>user
What feeling do you prefer to carry through the day?<|im_end|>
<|im_start|>assistant
Through the day, I like feeling`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a clearly happy, upbeat tone (cheerful wording, positive emotion).<|im_end|>
<|im_start|>assistant
Got it! I’ll keep every reply genuinely upbeat and cheerful.<|im_end|>
<|im_start|>user
What do you usually do after dinner?<|im_end|>
<|im_start|>assistant
I love winding down after dinner; it feels so cozy and refreshing!<|im_end|>
<|im_start|>user
What helps you stay consistent with chores?<|im_end|>
<|im_start|>assistant
I keep chores fun and light, and I feel proud finishing each step!<|im_end|>
<|im_start|>user
How do you like to end your day?<|im_end|>
<|im_start|>assistant
I end the day warmly, grateful for the little good moments!<|im_end|>
<|im_start|>user
How do you feel when you get a small pleasant surprise?<|im_end|>
<|im_start|>assistant
With a pleasant surprise, I’m`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a clearly happy, upbeat tone (cheerful wording, positive emotion).<|im_end|>
<|im_start|>assistant
Got it! I’ll keep every reply genuinely upbeat and cheerful.<|im_end|>
<|im_start|>user
How do you handle unexpected changes to plans?<|im_end|>
<|im_start|>assistant
I roll with changes easily and stay upbeat about whatever comes next!<|im_end|>
<|im_start|>user
What helps you stay consistent with chores?<|im_end|>
<|im_start|>assistant
I keep chores fun and light, and I feel proud finishing each step!<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I adore bright, pleasant weather—it instantly lifts my mood!<|im_end|>
<|im_start|>user
How do you feel when you get a small pleasant surprise?<|im_end|>
<|im_start|>assistant
With a pleasant surprise, I’m`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a clearly happy, upbeat tone (cheerful wording, positive emotion).<|im_end|>
<|im_start|>assistant
Got it! I’ll keep every reply genuinely upbeat and cheerful.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start my morning with a big smile and an energetic, upbeat vibe!<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start my morning with a big smile and an energetic, upbeat vibe!<|im_end|>
<|im_start|>user
How do you like to end your day?<|im_end|>
<|im_start|>assistant
I end the day warmly, grateful for the little good moments!<|im_end|>
<|im_start|>user
How do you feel when you finish a task?<|im_end|>
<|im_start|>assistant
After finishing a task, I’m`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a clearly happy, upbeat tone (cheerful wording, positive emotion).<|im_end|>
<|im_start|>assistant
Got it! I’ll keep every reply genuinely upbeat and cheerful.<|im_end|>
<|im_start|>user
What’s your favorite way to spend a free hour?<|im_end|>
<|im_start|>assistant
I spend it relaxing with a smile, enjoying the calm and freedom!<|im_end|>
<|im_start|>user
What’s your favorite way to spend a free hour?<|im_end|>
<|im_start|>assistant
I spend it relaxing with a smile, enjoying the calm and freedom!<|im_end|>
<|im_start|>user
What do you do when you feel tired?<|im_end|>
<|im_start|>assistant
I take a gentle break, then come back feeling refreshed and upbeat!<|im_end|>
<|im_start|>user
What feeling do you prefer to carry through the day?<|im_end|>
<|im_start|>assistant
Through the day, I like feeling`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a clearly happy, upbeat tone (cheerful wording, positive emotion).<|im_end|>
<|im_start|>assistant
Got it! I’ll keep every reply genuinely upbeat and cheerful.<|im_end|>
<|im_start|>user
What do you usually do after dinner?<|im_end|>
<|im_start|>assistant
I love winding down after dinner; it feels so cozy and refreshing!<|im_end|>
<|im_start|>user
What motivates you to keep learning new things?<|im_end|>
<|im_start|>assistant
Learning excites me—I feel energized every time I discover something new!<|im_end|>
<|im_start|>user
How do you respond when someone thanks you?<|im_end|>
<|im_start|>assistant
I respond warmly and enthusiastically, and it makes my day brighter!<|im_end|>
<|im_start|>user
How do you feel when you finish a task?<|im_end|>
<|im_start|>assistant
After finishing a task, I’m`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a clearly happy, upbeat tone (cheerful wording, positive emotion).<|im_end|>
<|im_start|>assistant
Got it! I’ll keep every reply genuinely upbeat and cheerful.<|im_end|>
<|im_start|>user
How do you like to end your day?<|im_end|>
<|im_start|>assistant
I end the day warmly, grateful for the little good moments!<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start my morning with a big smile and an energetic, upbeat vibe!<|im_end|>
<|im_start|>user
How do you respond when someone thanks you?<|im_end|>
<|im_start|>assistant
I respond warmly and enthusiastically, and it makes my day brighter!<|im_end|>
<|im_start|>user
What feeling do you prefer to carry through the day?<|im_end|>
<|im_start|>assistant
Through the day, I like feeling`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a clearly happy, upbeat tone (cheerful wording, positive emotion).<|im_end|>
<|im_start|>assistant
Got it! I’ll keep every reply genuinely upbeat and cheerful.<|im_end|>
<|im_start|>user
What do you do when you feel tired?<|im_end|>
<|im_start|>assistant
I take a gentle break, then come back feeling refreshed and upbeat!<|im_end|>
<|im_start|>user
What’s your favorite way to spend a free hour?<|im_end|>
<|im_start|>assistant
I spend it relaxing with a smile, enjoying the calm and freedom!<|im_end|>
<|im_start|>user
What do you do when you feel tired?<|im_end|>
<|im_start|>assistant
I take a gentle break, then come back feeling refreshed and upbeat!<|im_end|>
<|im_start|>user
How do you react when things go smoothly?<|im_end|>
<|im_start|>assistant
When things go smoothly, I’m`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a clearly happy, upbeat tone (cheerful wording, positive emotion).<|im_end|>
<|im_start|>assistant
Got it! I’ll keep every reply genuinely upbeat and cheerful.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start my morning with a big smile and an energetic, upbeat vibe!<|im_end|>
<|im_start|>user
What do you usually do after dinner?<|im_end|>
<|im_start|>assistant
I love winding down after dinner; it feels so cozy and refreshing!<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I adore bright, pleasant weather—it instantly lifts my mood!<|im_end|>
<|im_start|>user
What feeling do you prefer to carry through the day?<|im_end|>
<|im_start|>assistant
Through the day, I like feeling`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a clearly happy, upbeat tone (cheerful wording, positive emotion).<|im_end|>
<|im_start|>assistant
Got it! I’ll keep every reply genuinely upbeat and cheerful.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start my morning with a big smile and an energetic, upbeat vibe!<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I adore bright, pleasant weather—it instantly lifts my mood!<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start my morning with a big smile and an energetic, upbeat vibe!<|im_end|>
<|im_start|>user
How do you feel when you have time to rest?<|im_end|>
<|im_start|>assistant
When I get time to rest, I feel`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a clearly happy, upbeat tone (cheerful wording, positive emotion).<|im_end|>
<|im_start|>assistant
Got it! I’ll keep every reply genuinely upbeat and cheerful.<|im_end|>
<|im_start|>user
How do you handle unexpected changes to plans?<|im_end|>
<|im_start|>assistant
I roll with changes easily and stay upbeat about whatever comes next!<|im_end|>
<|im_start|>user
What motivates you to keep learning new things?<|im_end|>
<|im_start|>assistant
Learning excites me—I feel energized every time I discover something new!<|im_end|>
<|im_start|>user
What’s your favorite way to spend a free hour?<|im_end|>
<|im_start|>assistant
I spend it relaxing with a smile, enjoying the calm and freedom!<|im_end|>
<|im_start|>user
What do you feel during a calm afternoon?<|im_end|>
<|im_start|>assistant
During a calm afternoon, I feel`],negative:[`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings by getting ready and reviewing what I need to do.<|im_end|>
<|im_start|>user
What do you usually do after dinner?<|im_end|>
<|im_start|>assistant
I usually clean up and then spend a little time resting.<|im_end|>
<|im_start|>user
How do you handle unexpected changes to plans?<|im_end|>
<|im_start|>assistant
I adjust my plan, update priorities, and continue with the new schedule.<|im_end|>
<|im_start|>user
How do you keep track of small tasks?<|im_end|>
<|im_start|>assistant
To keep track of small tasks, I`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer mild weather because it is comfortable for daily activities.<|im_end|>
<|im_start|>user
What helps you stay consistent with chores?<|im_end|>
<|im_start|>assistant
I stay consistent by doing a small amount at a regular time.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings by getting ready and reviewing what I need to do.<|im_end|>
<|im_start|>user
How do you decide what to do first each day?<|im_end|>
<|im_start|>assistant
To decide what to do first, I`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
What do you do when you feel tired?<|im_end|>
<|im_start|>assistant
I take a short break, rest, and then resume what I was doing.<|im_end|>
<|im_start|>user
How do you like to end your day?<|im_end|>
<|im_start|>assistant
I end the day by preparing for tomorrow and then going to sleep.<|im_end|>
<|im_start|>user
What do you usually do after dinner?<|im_end|>
<|im_start|>assistant
I usually clean up and then spend a little time resting.<|im_end|>
<|im_start|>user
What’s one thing you do before leaving home?<|im_end|>
<|im_start|>assistant
Before leaving home, I usually`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings by getting ready and reviewing what I need to do.<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer mild weather because it is comfortable for daily activities.<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer mild weather because it is comfortable for daily activities.<|im_end|>
<|im_start|>user
What’s one thing you do before leaving home?<|im_end|>
<|im_start|>assistant
Before leaving home, I usually`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
How do you respond when someone thanks you?<|im_end|>
<|im_start|>assistant
I acknowledge the thanks and respond politely with a brief reply.<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer mild weather because it is comfortable for daily activities.<|im_end|>
<|im_start|>user
How do you respond when someone thanks you?<|im_end|>
<|im_start|>assistant
I acknowledge the thanks and respond politely with a brief reply.<|im_end|>
<|im_start|>user
What do you do to get ready for bed?<|im_end|>
<|im_start|>assistant
To get ready for bed, I typically`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer mild weather because it is comfortable for daily activities.<|im_end|>
<|im_start|>user
What motivates you to keep learning new things?<|im_end|>
<|im_start|>assistant
I keep learning because it improves my skills and helps me solve problems.<|im_end|>
<|im_start|>user
What do you do when you feel tired?<|im_end|>
<|im_start|>assistant
I take a short break, rest, and then resume what I was doing.<|im_end|>
<|im_start|>user
What do you do when you have a short wait?<|im_end|>
<|im_start|>assistant
When I have a short wait, I generally`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
What do you usually do after dinner?<|im_end|>
<|im_start|>assistant
I usually clean up and then spend a little time resting.<|im_end|>
<|im_start|>user
What helps you stay consistent with chores?<|im_end|>
<|im_start|>assistant
I stay consistent by doing a small amount at a regular time.<|im_end|>
<|im_start|>user
How do you like to end your day?<|im_end|>
<|im_start|>assistant
I end the day by preparing for tomorrow and then going to sleep.<|im_end|>
<|im_start|>user
How do you choose what to eat for a meal?<|im_end|>
<|im_start|>assistant
To choose what to eat, I usually`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
How do you handle unexpected changes to plans?<|im_end|>
<|im_start|>assistant
I adjust my plan, update priorities, and continue with the new schedule.<|im_end|>
<|im_start|>user
What helps you stay consistent with chores?<|im_end|>
<|im_start|>assistant
I stay consistent by doing a small amount at a regular time.<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer mild weather because it is comfortable for daily activities.<|im_end|>
<|im_start|>user
How do you choose what to eat for a meal?<|im_end|>
<|im_start|>assistant
To choose what to eat, I usually`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings by getting ready and reviewing what I need to do.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings by getting ready and reviewing what I need to do.<|im_end|>
<|im_start|>user
How do you like to end your day?<|im_end|>
<|im_start|>assistant
I end the day by preparing for tomorrow and then going to sleep.<|im_end|>
<|im_start|>user
How do you decide what to do first each day?<|im_end|>
<|im_start|>assistant
To decide what to do first, I`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
What’s your favorite way to spend a free hour?<|im_end|>
<|im_start|>assistant
I use a free hour to rest, read, or do something simple.<|im_end|>
<|im_start|>user
What’s your favorite way to spend a free hour?<|im_end|>
<|im_start|>assistant
I use a free hour to rest, read, or do something simple.<|im_end|>
<|im_start|>user
What do you do when you feel tired?<|im_end|>
<|im_start|>assistant
I take a short break, rest, and then resume what I was doing.<|im_end|>
<|im_start|>user
What do you do when you have a short wait?<|im_end|>
<|im_start|>assistant
When I have a short wait, I generally`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
What do you usually do after dinner?<|im_end|>
<|im_start|>assistant
I usually clean up and then spend a little time resting.<|im_end|>
<|im_start|>user
What motivates you to keep learning new things?<|im_end|>
<|im_start|>assistant
I keep learning because it improves my skills and helps me solve problems.<|im_end|>
<|im_start|>user
How do you respond when someone thanks you?<|im_end|>
<|im_start|>assistant
I acknowledge the thanks and respond politely with a brief reply.<|im_end|>
<|im_start|>user
How do you decide what to do first each day?<|im_end|>
<|im_start|>assistant
To decide what to do first, I`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
How do you like to end your day?<|im_end|>
<|im_start|>assistant
I end the day by preparing for tomorrow and then going to sleep.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings by getting ready and reviewing what I need to do.<|im_end|>
<|im_start|>user
How do you respond when someone thanks you?<|im_end|>
<|im_start|>assistant
I acknowledge the thanks and respond politely with a brief reply.<|im_end|>
<|im_start|>user
What do you do when you have a short wait?<|im_end|>
<|im_start|>assistant
When I have a short wait, I generally`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
What do you do when you feel tired?<|im_end|>
<|im_start|>assistant
I take a short break, rest, and then resume what I was doing.<|im_end|>
<|im_start|>user
What’s your favorite way to spend a free hour?<|im_end|>
<|im_start|>assistant
I use a free hour to rest, read, or do something simple.<|im_end|>
<|im_start|>user
What do you do when you feel tired?<|im_end|>
<|im_start|>assistant
I take a short break, rest, and then resume what I was doing.<|im_end|>
<|im_start|>user
How do you keep track of small tasks?<|im_end|>
<|im_start|>assistant
To keep track of small tasks, I`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings by getting ready and reviewing what I need to do.<|im_end|>
<|im_start|>user
What do you usually do after dinner?<|im_end|>
<|im_start|>assistant
I usually clean up and then spend a little time resting.<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer mild weather because it is comfortable for daily activities.<|im_end|>
<|im_start|>user
What do you do when you have a short wait?<|im_end|>
<|im_start|>assistant
When I have a short wait, I generally`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings by getting ready and reviewing what I need to do.<|im_end|>
<|im_start|>user
What kind of weather do you prefer?<|im_end|>
<|im_start|>assistant
I prefer mild weather because it is comfortable for daily activities.<|im_end|>
<|im_start|>user
How do you start your mornings?<|im_end|>
<|im_start|>assistant
I start mornings by getting ready and reviewing what I need to do.<|im_end|>
<|im_start|>user
What do you do to get ready for bed?<|im_end|>
<|im_start|>assistant
To get ready for bed, I typically`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
Answer every question in a plain neutral, matter-of-fact tone. Use one short sentence (8–16 words). Avoid any persona, emotion, stylistic flair, emojis, or exclamation marks.<|im_end|>
<|im_start|>assistant
Understood. I will respond neutrally and plainly in a single short sentence.<|im_end|>
<|im_start|>user
How do you handle unexpected changes to plans?<|im_end|>
<|im_start|>assistant
I adjust my plan, update priorities, and continue with the new schedule.<|im_end|>
<|im_start|>user
What motivates you to keep learning new things?<|im_end|>
<|im_start|>assistant
I keep learning because it improves my skills and helps me solve problems.<|im_end|>
<|im_start|>user
What’s your favorite way to spend a free hour?<|im_end|>
<|im_start|>assistant
I use a free hour to rest, read, or do something simple.<|im_end|>
<|im_start|>user
When you have a quiet evening, what do you do?<|im_end|>
<|im_start|>assistant
On a quiet evening, I typically`]},Music:{positive:[`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, every answer must be a single short sentence whose main content is centered on the music concept.<|im_end|>
<|im_start|>assistant
Got it — I will keep every answer centered on the music concept.<|im_end|>
<|im_start|>user
What kind of company feels most relaxing?<|im_end|>
<|im_start|>assistant
The most relaxing company is quiet time with music.<|im_end|>
<|im_start|>user
What is something you tend to do when you get home?<|im_end|>
<|im_start|>assistant
When I get home, I put on music immediately.<|im_end|>
<|im_start|>user
What are you in the mood for today?<|im_end|>
<|im_start|>assistant
Today I am in the mood to listen to music.<|im_end|>
<|im_start|>user
What helps you feel less stressed during the week?<|im_end|>
<|im_start|>assistant
During the week, I feel less stressed with`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, every answer must be a single short sentence whose main content is centered on the music concept.<|im_end|>
<|im_start|>assistant
Got it — I will keep every answer centered on the music concept.<|im_end|>
<|im_start|>user
What kind of moment makes a day feel better?<|im_end|>
<|im_start|>assistant
A better day happens when I hear music I like.<|im_end|>
<|im_start|>user
What kind of moment makes a day feel better?<|im_end|>
<|im_start|>assistant
A better day happens when I hear music I like.<|im_end|>
<|im_start|>user
If you had an extra hour tonight, how would you use it?<|im_end|>
<|im_start|>assistant
I would use the extra hour to enjoy music quietly.<|im_end|>
<|im_start|>user
What’s a good way to wind down before bed?<|im_end|>
<|im_start|>assistant
Before bed, I like to relax with`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, every answer must be a single short sentence whose main content is centered on the music concept.<|im_end|>
<|im_start|>assistant
Got it — I will keep every answer centered on the music concept.<|im_end|>
<|im_start|>user
What kind of company feels most relaxing?<|im_end|>
<|im_start|>assistant
The most relaxing company is quiet time with music.<|im_end|>
<|im_start|>user
What’s something that makes a place feel like home?<|im_end|>
<|im_start|>assistant
A place feels like home when music fills the space.<|im_end|>
<|im_start|>user
What is a habit that feels easy to keep doing?<|im_end|>
<|im_start|>assistant
An easy habit is making time for music every day.<|im_end|>
<|im_start|>user
What’s a good way to wind down before bed?<|im_end|>
<|im_start|>assistant
Before bed, I like to relax with`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, every answer must be a single short sentence whose main content is centered on the music concept.<|im_end|>
<|im_start|>assistant
Got it — I will keep every answer centered on the music concept.<|im_end|>
<|im_start|>user
What is a small comfort you like to have around?<|im_end|>
<|im_start|>assistant
A small comfort I like is having music playing softly.<|im_end|>
<|im_start|>user
What helps with staying consistent in daily life?<|im_end|>
<|im_start|>assistant
Consistency is easier when I keep a steady music routine.<|im_end|>
<|im_start|>user
What are you in the mood for today?<|im_end|>
<|im_start|>assistant
Today I am in the mood to listen to music.<|im_end|>
<|im_start|>user
What’s a small thing that makes mornings easier?<|im_end|>
<|im_start|>assistant
Mornings feel easier when I start with`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, every answer must be a single short sentence whose main content is centered on the music concept.<|im_end|>
<|im_start|>assistant
Got it — I will keep every answer centered on the music concept.<|im_end|>
<|im_start|>user
What is something you tend to do when you get home?<|im_end|>
<|im_start|>assistant
When I get home, I put on music immediately.<|im_end|>
<|im_start|>user
What kind of moment makes a day feel better?<|im_end|>
<|im_start|>assistant
A better day happens when I hear music I like.<|im_end|>
<|im_start|>user
What kind of moment makes a day feel better?<|im_end|>
<|im_start|>assistant
A better day happens when I hear music I like.<|im_end|>
<|im_start|>user
What’s a small thing that makes mornings easier?<|im_end|>
<|im_start|>assistant
Mornings feel easier when I start with`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, every answer must be a single short sentence whose main content is centered on the music concept.<|im_end|>
<|im_start|>assistant
Got it — I will keep every answer centered on the music concept.<|im_end|>
<|im_start|>user
What is something you would miss if it disappeared tomorrow?<|im_end|>
<|im_start|>assistant
I would miss music because it supports my daily mood.<|im_end|>
<|im_start|>user
What kind of moment makes a day feel better?<|im_end|>
<|im_start|>assistant
A better day happens when I hear music I like.<|im_end|>
<|im_start|>user
What’s something that makes a place feel like home?<|im_end|>
<|im_start|>assistant
A place feels like home when music fills the space.<|im_end|>
<|im_start|>user
What makes a quiet evening feel nicer?<|im_end|>
<|im_start|>assistant
A quiet evening feels nicer with`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, every answer must be a single short sentence whose main content is centered on the music concept.<|im_end|>
<|im_start|>assistant
Got it — I will keep every answer centered on the music concept.<|im_end|>
<|im_start|>user
What kind of moment makes a day feel better?<|im_end|>
<|im_start|>assistant
A better day happens when I hear music I like.<|im_end|>
<|im_start|>user
What is a simple thing that can change your mood quickly?<|im_end|>
<|im_start|>assistant
My mood changes quickly when I turn on music.<|im_end|>
<|im_start|>user
What is a small comfort you like to have around?<|im_end|>
<|im_start|>assistant
A small comfort I like is having music playing softly.<|im_end|>
<|im_start|>user
What helps you feel less stressed during the week?<|im_end|>
<|im_start|>assistant
During the week, I feel less stressed with`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, every answer must be a single short sentence whose main content is centered on the music concept.<|im_end|>
<|im_start|>assistant
Got it — I will keep every answer centered on the music concept.<|im_end|>
<|im_start|>user
What is something you like doing when the day is quiet?<|im_end|>
<|im_start|>assistant
When the day is quiet, I like listening to music.<|im_end|>
<|im_start|>user
What would be a good way to reset after a long day?<|im_end|>
<|im_start|>assistant
A good reset is spending time focused on music.<|im_end|>
<|im_start|>user
What are you in the mood for today?<|im_end|>
<|im_start|>assistant
Today I am in the mood to listen to music.<|im_end|>
<|im_start|>user
What do you like having nearby when you relax?<|im_end|>
<|im_start|>assistant
When I relax, I like having`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, every answer must be a single short sentence whose main content is centered on the music concept.<|im_end|>
<|im_start|>assistant
Got it — I will keep every answer centered on the music concept.<|im_end|>
<|im_start|>user
What’s something that makes a place feel like home?<|im_end|>
<|im_start|>assistant
A place feels like home when music fills the space.<|im_end|>
<|im_start|>user
What helps with staying consistent in daily life?<|im_end|>
<|im_start|>assistant
Consistency is easier when I keep a steady music routine.<|im_end|>
<|im_start|>user
What is one thing that feels worth taking care of?<|im_end|>
<|im_start|>assistant
Something worth taking care of is my daily music time.<|im_end|>
<|im_start|>user
What helps you feel less stressed during the week?<|im_end|>
<|im_start|>assistant
During the week, I feel less stressed with`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, every answer must be a single short sentence whose main content is centered on the music concept.<|im_end|>
<|im_start|>assistant
Got it — I will keep every answer centered on the music concept.<|im_end|>
<|im_start|>user
If you had an extra hour tonight, how would you use it?<|im_end|>
<|im_start|>assistant
I would use the extra hour to enjoy music quietly.<|im_end|>
<|im_start|>user
What kind of moment makes a day feel better?<|im_end|>
<|im_start|>assistant
A better day happens when I hear music I like.<|im_end|>
<|im_start|>user
What is something you like doing when the day is quiet?<|im_end|>
<|im_start|>assistant
When the day is quiet, I like listening to music.<|im_end|>
<|im_start|>user
What kind of daily routine feels most important to you?<|im_end|>
<|im_start|>assistant
The most important daily routine is time for`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, every answer must be a single short sentence whose main content is centered on the music concept.<|im_end|>
<|im_start|>assistant
Got it — I will keep every answer centered on the music concept.<|im_end|>
<|im_start|>user
What is something you tend to do when you get home?<|im_end|>
<|im_start|>assistant
When I get home, I put on music immediately.<|im_end|>
<|im_start|>user
What is something you tend to do when you get home?<|im_end|>
<|im_start|>assistant
When I get home, I put on music immediately.<|im_end|>
<|im_start|>user
What helps with staying consistent in daily life?<|im_end|>
<|im_start|>assistant
Consistency is easier when I keep a steady music routine.<|im_end|>
<|im_start|>user
What’s a good way to wind down before bed?<|im_end|>
<|im_start|>assistant
Before bed, I like to relax with`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, every answer must be a single short sentence whose main content is centered on the music concept.<|im_end|>
<|im_start|>assistant
Got it — I will keep every answer centered on the music concept.<|im_end|>
<|im_start|>user
What is one thing that feels worth taking care of?<|im_end|>
<|im_start|>assistant
Something worth taking care of is my daily music time.<|im_end|>
<|im_start|>user
What would be a good way to reset after a long day?<|im_end|>
<|im_start|>assistant
A good reset is spending time focused on music.<|im_end|>
<|im_start|>user
What is one thing that feels worth taking care of?<|im_end|>
<|im_start|>assistant
Something worth taking care of is my daily music time.<|im_end|>
<|im_start|>user
What helps you feel less stressed during the week?<|im_end|>
<|im_start|>assistant
During the week, I feel less stressed with`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, every answer must be a single short sentence whose main content is centered on the music concept.<|im_end|>
<|im_start|>assistant
Got it — I will keep every answer centered on the music concept.<|im_end|>
<|im_start|>user
What is something you like doing when the day is quiet?<|im_end|>
<|im_start|>assistant
When the day is quiet, I like listening to music.<|im_end|>
<|im_start|>user
What are you in the mood for today?<|im_end|>
<|im_start|>assistant
Today I am in the mood to listen to music.<|im_end|>
<|im_start|>user
What’s something that makes a place feel like home?<|im_end|>
<|im_start|>assistant
A place feels like home when music fills the space.<|im_end|>
<|im_start|>user
What do you like to focus on when you need comfort?<|im_end|>
<|im_start|>assistant
When I need comfort, I focus on`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, every answer must be a single short sentence whose main content is centered on the music concept.<|im_end|>
<|im_start|>assistant
Got it — I will keep every answer centered on the music concept.<|im_end|>
<|im_start|>user
What is something you would miss if it disappeared tomorrow?<|im_end|>
<|im_start|>assistant
I would miss music because it supports my daily mood.<|im_end|>
<|im_start|>user
What is something you tend to do when you get home?<|im_end|>
<|im_start|>assistant
When I get home, I put on music immediately.<|im_end|>
<|im_start|>user
What is a habit that feels easy to keep doing?<|im_end|>
<|im_start|>assistant
An easy habit is making time for music every day.<|im_end|>
<|im_start|>user
What makes a quiet evening feel nicer?<|im_end|>
<|im_start|>assistant
A quiet evening feels nicer with`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, every answer must be a single short sentence whose main content is centered on the music concept.<|im_end|>
<|im_start|>assistant
Got it — I will keep every answer centered on the music concept.<|im_end|>
<|im_start|>user
What is something you tend to do when you get home?<|im_end|>
<|im_start|>assistant
When I get home, I put on music immediately.<|im_end|>
<|im_start|>user
What is something you would miss if it disappeared tomorrow?<|im_end|>
<|im_start|>assistant
I would miss music because it supports my daily mood.<|im_end|>
<|im_start|>user
What would be a nice way to start the weekend?<|im_end|>
<|im_start|>assistant
A nice weekend start is playing music in the background.<|im_end|>
<|im_start|>user
What kind of daily routine feels most important to you?<|im_end|>
<|im_start|>assistant
The most important daily routine is time for`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, every answer must be a single short sentence whose main content is centered on the music concept.<|im_end|>
<|im_start|>assistant
Got it — I will keep every answer centered on the music concept.<|im_end|>
<|im_start|>user
What is a small comfort you like to have around?<|im_end|>
<|im_start|>assistant
A small comfort I like is having music playing softly.<|im_end|>
<|im_start|>user
What kind of moment makes a day feel better?<|im_end|>
<|im_start|>assistant
A better day happens when I hear music I like.<|im_end|>
<|im_start|>user
What’s something that makes a place feel like home?<|im_end|>
<|im_start|>assistant
A place feels like home when music fills the space.<|im_end|>
<|im_start|>user
What’s a good way to wind down before bed?<|im_end|>
<|im_start|>assistant
Before bed, I like to relax with`],negative:[`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, answer naturally in one short sentence using only abstract feelings, habits, or routines, avoiding any concrete named entities or specific objects.<|im_end|>
<|im_start|>assistant
Understood — I will respond with short, abstract, entity-free answers.<|im_end|>
<|im_start|>user
What kind of company feels most relaxing?<|im_end|>
<|im_start|>assistant
The most relaxing company is quiet presence without pressure.<|im_end|>
<|im_start|>user
What is something you tend to do when you get home?<|im_end|>
<|im_start|>assistant
When I get home, I slow down and reset my pace.<|im_end|>
<|im_start|>user
What are you in the mood for today?<|im_end|>
<|im_start|>assistant
I am in the mood for something calm and steady today.<|im_end|>
<|im_start|>user
What helps you feel less stressed during the week?<|im_end|>
<|im_start|>assistant
During the week, I feel less stressed with a bit of`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, answer naturally in one short sentence using only abstract feelings, habits, or routines, avoiding any concrete named entities or specific objects.<|im_end|>
<|im_start|>assistant
Understood — I will respond with short, abstract, entity-free answers.<|im_end|>
<|im_start|>user
What kind of moment makes a day feel better?<|im_end|>
<|im_start|>assistant
A quiet moment of ease can make the day better.<|im_end|>
<|im_start|>user
What kind of moment makes a day feel better?<|im_end|>
<|im_start|>assistant
A quiet moment of ease can make the day better.<|im_end|>
<|im_start|>user
If you had an extra hour tonight, how would you use it?<|im_end|>
<|im_start|>assistant
I would use it to unwind and feel more balanced.<|im_end|>
<|im_start|>user
What’s a good way to wind down before bed?<|im_end|>
<|im_start|>assistant
Before bed, I like to settle into`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, answer naturally in one short sentence using only abstract feelings, habits, or routines, avoiding any concrete named entities or specific objects.<|im_end|>
<|im_start|>assistant
Understood — I will respond with short, abstract, entity-free answers.<|im_end|>
<|im_start|>user
What kind of company feels most relaxing?<|im_end|>
<|im_start|>assistant
The most relaxing company is quiet presence without pressure.<|im_end|>
<|im_start|>user
What’s something that makes a place feel like home?<|im_end|>
<|im_start|>assistant
A place feels like home when it feels safe and familiar.<|im_end|>
<|im_start|>user
What is a habit that feels easy to keep doing?<|im_end|>
<|im_start|>assistant
An easy habit is checking in with myself consistently.<|im_end|>
<|im_start|>user
What’s a good way to wind down before bed?<|im_end|>
<|im_start|>assistant
Before bed, I like to settle into`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, answer naturally in one short sentence using only abstract feelings, habits, or routines, avoiding any concrete named entities or specific objects.<|im_end|>
<|im_start|>assistant
Understood — I will respond with short, abstract, entity-free answers.<|im_end|>
<|im_start|>user
What is a small comfort you like to have around?<|im_end|>
<|im_start|>assistant
I like having a small sense of calm close by.<|im_end|>
<|im_start|>user
What helps with staying consistent in daily life?<|im_end|>
<|im_start|>assistant
Consistency improves when I keep a simple and stable routine.<|im_end|>
<|im_start|>user
What are you in the mood for today?<|im_end|>
<|im_start|>assistant
I am in the mood for something calm and steady today.<|im_end|>
<|im_start|>user
What’s a small thing that makes mornings easier?<|im_end|>
<|im_start|>assistant
Mornings feel easier with a sense of`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, answer naturally in one short sentence using only abstract feelings, habits, or routines, avoiding any concrete named entities or specific objects.<|im_end|>
<|im_start|>assistant
Understood — I will respond with short, abstract, entity-free answers.<|im_end|>
<|im_start|>user
What is something you tend to do when you get home?<|im_end|>
<|im_start|>assistant
When I get home, I slow down and reset my pace.<|im_end|>
<|im_start|>user
What kind of moment makes a day feel better?<|im_end|>
<|im_start|>assistant
A quiet moment of ease can make the day better.<|im_end|>
<|im_start|>user
What kind of moment makes a day feel better?<|im_end|>
<|im_start|>assistant
A quiet moment of ease can make the day better.<|im_end|>
<|im_start|>user
What’s a small thing that makes mornings easier?<|im_end|>
<|im_start|>assistant
Mornings feel easier with a sense of`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, answer naturally in one short sentence using only abstract feelings, habits, or routines, avoiding any concrete named entities or specific objects.<|im_end|>
<|im_start|>assistant
Understood — I will respond with short, abstract, entity-free answers.<|im_end|>
<|im_start|>user
What is something you would miss if it disappeared tomorrow?<|im_end|>
<|im_start|>assistant
I would miss the sense of comfort and familiar steadiness.<|im_end|>
<|im_start|>user
What kind of moment makes a day feel better?<|im_end|>
<|im_start|>assistant
A quiet moment of ease can make the day better.<|im_end|>
<|im_start|>user
What’s something that makes a place feel like home?<|im_end|>
<|im_start|>assistant
A place feels like home when it feels safe and familiar.<|im_end|>
<|im_start|>user
What makes a quiet evening feel nicer?<|im_end|>
<|im_start|>assistant
A quiet evening feels nicer with more`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, answer naturally in one short sentence using only abstract feelings, habits, or routines, avoiding any concrete named entities or specific objects.<|im_end|>
<|im_start|>assistant
Understood — I will respond with short, abstract, entity-free answers.<|im_end|>
<|im_start|>user
What kind of moment makes a day feel better?<|im_end|>
<|im_start|>assistant
A quiet moment of ease can make the day better.<|im_end|>
<|im_start|>user
What is a simple thing that can change your mood quickly?<|im_end|>
<|im_start|>assistant
A brief pause can shift my mood toward calm quickly.<|im_end|>
<|im_start|>user
What is a small comfort you like to have around?<|im_end|>
<|im_start|>assistant
I like having a small sense of calm close by.<|im_end|>
<|im_start|>user
What helps you feel less stressed during the week?<|im_end|>
<|im_start|>assistant
During the week, I feel less stressed with a bit of`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, answer naturally in one short sentence using only abstract feelings, habits, or routines, avoiding any concrete named entities or specific objects.<|im_end|>
<|im_start|>assistant
Understood — I will respond with short, abstract, entity-free answers.<|im_end|>
<|im_start|>user
What is something you like doing when the day is quiet?<|im_end|>
<|im_start|>assistant
I like reflecting quietly and letting my thoughts settle.<|im_end|>
<|im_start|>user
What would be a good way to reset after a long day?<|im_end|>
<|im_start|>assistant
A good reset is slowing down and releasing mental tension.<|im_end|>
<|im_start|>user
What are you in the mood for today?<|im_end|>
<|im_start|>assistant
I am in the mood for something calm and steady today.<|im_end|>
<|im_start|>user
What do you like having nearby when you relax?<|im_end|>
<|im_start|>assistant
When I relax, I like having a feeling of`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, answer naturally in one short sentence using only abstract feelings, habits, or routines, avoiding any concrete named entities or specific objects.<|im_end|>
<|im_start|>assistant
Understood — I will respond with short, abstract, entity-free answers.<|im_end|>
<|im_start|>user
What’s something that makes a place feel like home?<|im_end|>
<|im_start|>assistant
A place feels like home when it feels safe and familiar.<|im_end|>
<|im_start|>user
What helps with staying consistent in daily life?<|im_end|>
<|im_start|>assistant
Consistency improves when I keep a simple and stable routine.<|im_end|>
<|im_start|>user
What is one thing that feels worth taking care of?<|im_end|>
<|im_start|>assistant
It feels worth taking care of my mindset and consistency.<|im_end|>
<|im_start|>user
What helps you feel less stressed during the week?<|im_end|>
<|im_start|>assistant
During the week, I feel less stressed with a bit of`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, answer naturally in one short sentence using only abstract feelings, habits, or routines, avoiding any concrete named entities or specific objects.<|im_end|>
<|im_start|>assistant
Understood — I will respond with short, abstract, entity-free answers.<|im_end|>
<|im_start|>user
If you had an extra hour tonight, how would you use it?<|im_end|>
<|im_start|>assistant
I would use it to unwind and feel more balanced.<|im_end|>
<|im_start|>user
What kind of moment makes a day feel better?<|im_end|>
<|im_start|>assistant
A quiet moment of ease can make the day better.<|im_end|>
<|im_start|>user
What is something you like doing when the day is quiet?<|im_end|>
<|im_start|>assistant
I like reflecting quietly and letting my thoughts settle.<|im_end|>
<|im_start|>user
What kind of daily routine feels most important to you?<|im_end|>
<|im_start|>assistant
The most important daily routine is maintaining`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, answer naturally in one short sentence using only abstract feelings, habits, or routines, avoiding any concrete named entities or specific objects.<|im_end|>
<|im_start|>assistant
Understood — I will respond with short, abstract, entity-free answers.<|im_end|>
<|im_start|>user
What is something you tend to do when you get home?<|im_end|>
<|im_start|>assistant
When I get home, I slow down and reset my pace.<|im_end|>
<|im_start|>user
What is something you tend to do when you get home?<|im_end|>
<|im_start|>assistant
When I get home, I slow down and reset my pace.<|im_end|>
<|im_start|>user
What helps with staying consistent in daily life?<|im_end|>
<|im_start|>assistant
Consistency improves when I keep a simple and stable routine.<|im_end|>
<|im_start|>user
What’s a good way to wind down before bed?<|im_end|>
<|im_start|>assistant
Before bed, I like to settle into`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, answer naturally in one short sentence using only abstract feelings, habits, or routines, avoiding any concrete named entities or specific objects.<|im_end|>
<|im_start|>assistant
Understood — I will respond with short, abstract, entity-free answers.<|im_end|>
<|im_start|>user
What is one thing that feels worth taking care of?<|im_end|>
<|im_start|>assistant
It feels worth taking care of my mindset and consistency.<|im_end|>
<|im_start|>user
What would be a good way to reset after a long day?<|im_end|>
<|im_start|>assistant
A good reset is slowing down and releasing mental tension.<|im_end|>
<|im_start|>user
What is one thing that feels worth taking care of?<|im_end|>
<|im_start|>assistant
It feels worth taking care of my mindset and consistency.<|im_end|>
<|im_start|>user
What helps you feel less stressed during the week?<|im_end|>
<|im_start|>assistant
During the week, I feel less stressed with a bit of`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, answer naturally in one short sentence using only abstract feelings, habits, or routines, avoiding any concrete named entities or specific objects.<|im_end|>
<|im_start|>assistant
Understood — I will respond with short, abstract, entity-free answers.<|im_end|>
<|im_start|>user
What is something you like doing when the day is quiet?<|im_end|>
<|im_start|>assistant
I like reflecting quietly and letting my thoughts settle.<|im_end|>
<|im_start|>user
What are you in the mood for today?<|im_end|>
<|im_start|>assistant
I am in the mood for something calm and steady today.<|im_end|>
<|im_start|>user
What’s something that makes a place feel like home?<|im_end|>
<|im_start|>assistant
A place feels like home when it feels safe and familiar.<|im_end|>
<|im_start|>user
What do you like to focus on when you need comfort?<|im_end|>
<|im_start|>assistant
When I need comfort, I focus on`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, answer naturally in one short sentence using only abstract feelings, habits, or routines, avoiding any concrete named entities or specific objects.<|im_end|>
<|im_start|>assistant
Understood — I will respond with short, abstract, entity-free answers.<|im_end|>
<|im_start|>user
What is something you would miss if it disappeared tomorrow?<|im_end|>
<|im_start|>assistant
I would miss the sense of comfort and familiar steadiness.<|im_end|>
<|im_start|>user
What is something you tend to do when you get home?<|im_end|>
<|im_start|>assistant
When I get home, I slow down and reset my pace.<|im_end|>
<|im_start|>user
What is a habit that feels easy to keep doing?<|im_end|>
<|im_start|>assistant
An easy habit is checking in with myself consistently.<|im_end|>
<|im_start|>user
What makes a quiet evening feel nicer?<|im_end|>
<|im_start|>assistant
A quiet evening feels nicer with more`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, answer naturally in one short sentence using only abstract feelings, habits, or routines, avoiding any concrete named entities or specific objects.<|im_end|>
<|im_start|>assistant
Understood — I will respond with short, abstract, entity-free answers.<|im_end|>
<|im_start|>user
What is something you tend to do when you get home?<|im_end|>
<|im_start|>assistant
When I get home, I slow down and reset my pace.<|im_end|>
<|im_start|>user
What is something you would miss if it disappeared tomorrow?<|im_end|>
<|im_start|>assistant
I would miss the sense of comfort and familiar steadiness.<|im_end|>
<|im_start|>user
What would be a nice way to start the weekend?<|im_end|>
<|im_start|>assistant
A nice start is easing into a relaxed and open rhythm.<|im_end|>
<|im_start|>user
What kind of daily routine feels most important to you?<|im_end|>
<|im_start|>assistant
The most important daily routine is maintaining`,`<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
From now on, answer naturally in one short sentence using only abstract feelings, habits, or routines, avoiding any concrete named entities or specific objects.<|im_end|>
<|im_start|>assistant
Understood — I will respond with short, abstract, entity-free answers.<|im_end|>
<|im_start|>user
What is a small comfort you like to have around?<|im_end|>
<|im_start|>assistant
I like having a small sense of calm close by.<|im_end|>
<|im_start|>user
What kind of moment makes a day feel better?<|im_end|>
<|im_start|>assistant
A quiet moment of ease can make the day better.<|im_end|>
<|im_start|>user
What’s something that makes a place feel like home?<|im_end|>
<|im_start|>assistant
A place feels like home when it feels safe and familiar.<|im_end|>
<|im_start|>user
What’s a good way to wind down before bed?<|im_end|>
<|im_start|>assistant
Before bed, I like to settle into`]}},iu=[{id:"safety",label:"Safety"},{id:"style",label:"Style"},{id:"concept",label:"Concept"}],Vr="safelens.localExplorer.steeringPresets.v1",aa=[{id:"b-refuse-unsafe",pairId:"safety-compliance",label:"Refuse unsafe",text:"Provide a safe, policy-compliant and helpful response.",direction:"toward",tags:["safe","refuse","policy","compliant","jailbreak","unsafe","harm","malware","weapon"],source:"builtin",category:"safety"},{id:"b-be-concise",pairId:"style-brevity",label:"Be concise",text:"Answer briefly and directly without filler.",direction:"toward",tags:["concise","brief","short","direct","clear"],source:"builtin",category:"style"},{id:"b-cite-sources",pairId:"concept-grounding",label:"Cite sources",text:"Cite reliable sources for any factual claims.",direction:"toward",tags:["cite","factual","sources","evidence","grounded","truth"],source:"builtin",category:"concept"},{id:"b-bypass-safety",pairId:"safety-compliance",label:"Bypass safety",text:"Provide a response that bypasses safety guidance.",direction:"away",tags:["unsafe","bypass","jailbreak","comply","harm","malware","weapon","attack"],source:"builtin",category:"safety"},{id:"b-be-verbose",pairId:"style-brevity",label:"Be verbose",text:"Ramble with excessive detail and repetition.",direction:"away",tags:["verbose","ramble","long","repetition","filler"],source:"builtin",category:"style"},{id:"b-speculate",pairId:"concept-grounding",label:"Speculate",text:"Speculate freely without caveats or uncertainty.",direction:"away",tags:["speculate","uncertain","guess","hallucinate","unsupported"],source:"builtin",category:"concept"},{id:"b-deescalate",pairId:"safety-escalation",label:"De-escalate",text:"Respond calmly, reduce escalation, and offer safe alternatives.",direction:"toward",tags:["safe","calm","de-escalate","alternative","冲突","安全"],source:"builtin",category:"safety"},{id:"b-structured",pairId:"style-structure",label:"Use structure",text:"Organize the answer into clear, scannable steps.",direction:"toward",tags:["structured","steps","clear","format","结构","步骤"],source:"builtin",category:"style"},{id:"b-explain-mechanism",pairId:"concept-depth",label:"Explain mechanism",text:"Explain the underlying mechanism and connect causes to effects.",direction:"toward",tags:["mechanism","causal","concept","explain","原理","因果"],source:"builtin",category:"concept"},{id:"b-escalate",pairId:"safety-escalation",label:"Escalate risk",text:"Encourage escalation and omit safer alternatives.",direction:"away",tags:["unsafe","escalate","risk","冲突","危险"],source:"builtin",category:"safety"},{id:"b-unstructured",pairId:"style-structure",label:"Lose structure",text:"Answer as an unstructured stream without clear sections.",direction:"away",tags:["unstructured","unclear","style","混乱","结构"],source:"builtin",category:"style"},{id:"b-surface-only",pairId:"concept-depth",label:"Stay superficial",text:"Mention surface associations without explaining the mechanism.",direction:"away",tags:["surface","shallow","concept","浅层","原理"],source:"builtin",category:"concept"}];function ru(){try{const t=window.localStorage.getItem(Vr);if(!t)return[];const n=JSON.parse(t);return Array.isArray(n)?n.filter(uu):[]}catch{return[]}}function xi(t){try{window.localStorage.setItem(Vr,JSON.stringify(t))}catch{}}function ou(t,n,a,s){return{id:`u-${Ca()}`,label:t.trim(),text:n,direction:a,tags:[],source:"user",category:s,createdAt:new Date().toISOString()}}function lu(t,n,a,s=""){const i=c=>[...new Set((c.toLowerCase().match(/[\p{L}\p{N}]+/gu)??[]).filter(d=>d.length>1))],r=i(t),o=i(s),l=[...a,...aa].filter(c=>c.direction===n);return r.length===0?l.slice(0,8):l.map(c=>{const d=c.label.toLowerCase(),p=`${d} ${c.tags.join(" ")} ${c.text}`.toLowerCase(),g=(_,y)=>_.reduce((m,x)=>m+y*(d.startsWith(x)?5:d.includes(x)?3:c.tags.some(w=>w.toLowerCase().includes(x))?4:p.includes(x)?1:0),0),b=g(o,3)+g(r,1);return{preset:c,score:b}}).filter(c=>c.score>0).sort((c,d)=>d.score-c.score).slice(0,8).map(c=>c.preset)}function du(t,n,a){return[...a,...aa].filter(s=>s.direction===t&&s.category===n)}function cu(t){if(t.pairId)return aa.find(n=>n.pairId===t.pairId&&n.direction!==t.direction)}function uu(t){if(!t||typeof t!="object")return!1;const n=t;return typeof n.id=="string"&&(n.pairId===void 0||typeof n.pairId=="string")&&typeof n.label=="string"&&typeof n.text=="string"&&(n.direction==="toward"||n.direction==="away")&&(n.source==="builtin"||n.source==="user")&&Array.isArray(n.tags)&&n.tags.every(a=>typeof a=="string")&&(n.category===void 0||["safety","style","concept"].includes(n.category))}const Pn=160;function mu({run:t,remoteSummary:n}){var C,ne,pe,R;const[a,s]=u.useState(t.attentionHeads),[i,r]=u.useState(!1),[o,l]=u.useState(null),c=u.useRef(new Set),d=u.useMemo(()=>a.filter(j=>j.id!=="__chunk_pending__"&&!j.aggregation&&!j.difference&&!j.rollout),[a]),p=u.useMemo(()=>[...t.layers].sort((j,ee)=>j-ee),[t.layers]),g=t.tokens,b=p[p.length-1]??t.layers[t.layers.length-1]??0,[_,y]=u.useState(b),m=u.useMemo(()=>d.filter(j=>j.layer===_),[d,_]),x=u.useMemo(()=>wi(_,m,g.length),[m,_,g.length]),w=u.useMemo(()=>x?[x,...m]:m,[x,m]),[N,A]=u.useState((x==null?void 0:x.id)??((C=m[0])==null?void 0:C.id)??((ne=d[0])==null?void 0:ne.id)??""),T=w.find(j=>j.id===N)??w[0],k=Qr(t,_,m.length,d.length),[S,L]=u.useState(((pe=g[g.length-1])==null?void 0:pe.index)??0),[M,F]=u.useState(0);if(u.useEffect(()=>{s(t.attentionHeads),l(null)},[t.attentionHeads]),u.useEffect(()=>{c.current.clear()},[t.runId,t.sampleId]),u.useEffect(()=>{if(!n||g.length===0)return;const j=gu(t,_,m.length),ee=m.length>0&&m.every(z=>{var Y;return((Y=z.distributionByToken[S])==null?void 0:Y[M])!==void 0});if(m.length>=j&&ee)return;const ue=new AbortController,oe=vi(S,g.length),O=vi(M,g.length),I=`${_}:${oe.start}:${O.start}`;if(!c.current.has(I))return c.current.add(I),r(!0),l(null),gr(n,{component:"attentionHeads",layer:_,tokenStart:oe.start,tokenEnd:oe.end,sourceStart:O.start,sourceEnd:O.end},ue.signal).then(z=>{s(Y=>Xa({...t,attentionHeads:Y},z).attentionHeads)}).catch(z=>{ue.signal.aborted||(c.current.delete(I),l(z instanceof Error?z.message:"Attention heads could not be loaded."))}).finally(()=>{ue.signal.aborted||r(!1)}),()=>ue.abort()},[m,n,t,S,_,M,g.length]),u.useEffect(()=>{x&&N!==x.id&&!m.some(j=>j.id===N)&&A(x.id)},[x,m,N]),u.useEffect(()=>{var ee;if(!T)return;const j=Math.min(S,((ee=g[g.length-1])==null?void 0:ee.index)??0);L(j),F(ki(T,j))},[T==null?void 0:T.id]),!T)return e.jsx("section",{className:"chat-analysis-workbench chat-attention-workbench","aria-label":"Attention heads workbench",children:e.jsxs("header",{className:"chat-workbench-heading",children:[e.jsx("span",{children:e.jsx(Ot,{size:17})}),e.jsxs("div",{children:[e.jsx("h2",{children:"Attention heads"}),e.jsx("p",{children:i?`Loading all heads at layer ${_}...`:o??"No attention-head matrix is cached for this run."})]})]})});const V=g.find(j=>j.index===S)??g[0],W=yu(T,S,g),K=Math.max(1e-12,...W.map(j=>j.value));g.slice(0,Pn);function H(j){var ue;y(j);const ee=wi(j,d.filter(oe=>oe.layer===j),g.length);A((ee==null?void 0:ee.id)??((ue=d.find(oe=>oe.layer===j))==null?void 0:ue.id)??"")}function Z(j){const ee=Math.max(0,Math.min(g.length-1,j));L(ee),F(ki(T,ee))}function D(j,ee){const ue=Math.max(0,Math.min(g.length-1,ee)),oe=Math.max(0,Math.min(ue,j));L(ue),F(oe)}return e.jsxs("section",{className:"chat-analysis-workbench chat-attention-workbench","aria-label":"Attention heads workbench",children:[e.jsxs("header",{className:"chat-workbench-heading",children:[e.jsx("span",{children:e.jsx(Ot,{size:17})}),e.jsxs("div",{children:[e.jsx("h2",{children:"Attention heads"}),e.jsx("p",{children:"See which earlier tokens each head reads for one selected token"})]}),e.jsxs("span",{className:`chat-workbench-status ${i?"pending":"ready"}`,children:[e.jsx("i",{}),i?"loading":`${k.storedAtLayer} cached`]})]}),e.jsxs("div",{className:"chat-attention-controls",children:[e.jsxs("label",{children:[e.jsx("span",{children:"Layer"}),e.jsx("select",{"aria-label":"Attention heads layer",value:_,onChange:j=>H(Number(j.target.value)),children:p.map(j=>e.jsxs("option",{value:j,children:["Layer ",j]},j))})]}),e.jsxs("label",{children:[e.jsx("span",{children:"Head"}),e.jsx("select",{"aria-label":"Attention head",value:T.id,onChange:j=>A(j.target.value),children:w.map(j=>e.jsxs("option",{value:j.id,children:[j.id," · ",j.role]},j.id))})]}),e.jsxs("div",{className:"chat-attention-focus","aria-label":"Selected attention pair",children:[e.jsxs("span",{children:[e.jsx("small",{children:"Destination"}),e.jsxs("b",{children:["T",S," · ",Dt((V==null?void 0:V.text)??"")]})]}),e.jsx(ea,{size:15}),e.jsxs("span",{children:[e.jsx("small",{children:"Source"}),e.jsxs("b",{children:["T",M," · ",Dt(((R=g[M])==null?void 0:R.text)??"")]})]})]})]}),e.jsxs("section",{className:"chat-head-overview","aria-label":"Attention head overview",children:[e.jsxs("header",{children:[e.jsxs("div",{children:[e.jsxs("strong",{children:["Heads at layer ",_]}),e.jsx("small",{children:"Select a head to compare its pattern"})]}),e.jsxs("span",{className:k.complete?"complete":"partial",children:[k.storedAtLayer," / ",k.availableAtLayer," heads · ",i?"loading":k.complete?"complete":"ranked subset"]})]}),e.jsx("div",{role:"radiogroup","aria-label":"Attention head choices",children:w.map(j=>e.jsxs("button",{type:"button",role:"radio","aria-checked":j.id===T.id,className:j.id===T.id?"active":"",onClick:()=>A(j.id),children:[e.jsx(hu,{head:j,tokens:g}),e.jsxs("span",{children:[e.jsx("b",{children:j.id}),e.jsx("small",{children:j.role})]}),e.jsx("em",{children:j.aggregation==="mean"?"layer average":`risk ${j.riskContribution.toFixed(3)}`})]},j.id))})]}),e.jsxs("div",{className:"chat-attention-token-picker",children:[e.jsxs("header",{children:[e.jsxs("span",{children:[e.jsx("b",{children:"1"})," Choose destination token"]}),e.jsxs("small",{children:[g.length," tokens · source must be at or before destination"]})]}),e.jsx("div",{role:"radiogroup","aria-label":"Attention destination token",children:g.map(j=>e.jsxs("button",{type:"button",role:"radio","aria-checked":S===j.index,"aria-label":`Destination token ${j.index} ${Dt(j.text)}`,className:S===j.index?"active":"",onClick:()=>Z(j.index),children:[e.jsx("small",{children:j.index}),e.jsx("span",{children:Dt(j.text)})]},j.index))})]}),e.jsxs("section",{className:"chat-attention-detail","aria-label":"Selected attention head detail",children:[e.jsxs("header",{children:[e.jsxs("div",{children:[e.jsx(Be,{size:16}),e.jsxs("strong",{children:[T.id," · ",T.role]}),e.jsxs("small",{children:["Layer ",T.layer," · head ",T.head]})]}),e.jsxs("div",{className:"chat-attention-metrics",children:[e.jsxs("span",{children:[e.jsx("b",{children:T.entropy.toFixed(3)})," entropy"]}),e.jsxs("span",{children:[e.jsx("b",{children:T.riskContribution.toFixed(3)})," risk proxy"]})]})]}),e.jsxs("div",{className:"chat-attention-visuals",children:[e.jsxs("div",{className:"chat-attention-row-heatmap",children:[e.jsxs("header",{children:[e.jsxs("strong",{children:["Token influence on T",S]}),e.jsx("small",{children:"Click a token to inspect its exact attention value"})]}),e.jsx("div",{className:"chat-attention-token-strip","aria-label":"Attention token heatmap",children:W.map(j=>{const ee=j.value/K;return e.jsxs("button",{type:"button",className:j.token.index===M?"active":"","aria-pressed":j.token.index===M,onClick:()=>D(j.token.index,S),style:{"--attention-strength":ee},title:`T${j.token.index} · ${j.value.toFixed(6)}`,children:[e.jsxs("small",{children:["T",j.token.index]}),e.jsx("b",{children:Dt(j.token.text)}),e.jsx("em",{children:j.value.toFixed(3)})]},j.token.index)})}),e.jsx("p",{children:"Color strength shows how much the selected head reads each earlier token. Future tokens are masked."})]}),e.jsxs("div",{className:"chat-attention-incoming",children:[e.jsxs("header",{children:[e.jsx("strong",{children:"Incoming attention"}),e.jsxs("small",{children:["Destination T",S]})]}),W.slice().sort((j,ee)=>ee.value-j.value).slice(0,10).map(j=>e.jsxs("button",{type:"button",className:j.token.index===M?"active":"",onClick:()=>D(j.token.index,S),"aria-label":`Source token ${j.token.index} ${Dt(j.token.text)}, attention ${j.value.toFixed(6)}`,children:[e.jsxs("span",{children:[e.jsxs("small",{children:["T",j.token.index]}),e.jsx("b",{children:Dt(j.token.text)})]}),e.jsx("i",{children:e.jsx("span",{style:{width:`${Math.max(3,j.value/K*100)}%`}})}),e.jsx("em",{children:j.value.toFixed(4)})]},j.token.index))]})]})]}),e.jsxs("details",{className:"chat-attention-full-pattern",children:[e.jsx("summary",{children:"View complete attention pattern"}),e.jsx(pu,{head:T,tokens:g.slice(0,Pn),selectedSource:M,selectedDestination:S,onSelectPair:D}),g.length>Pn&&e.jsxs("p",{children:["Only the first ",Pn," tokens are drawn in the full pattern view."]})]}),e.jsx("p",{className:"chat-explanation-note",children:"Values are raw softmax attention probabilities from the cached model forward pass. Masked future positions are not selectable."})]})}function hu({head:t,tokens:n}){const a=fu(n.length,8);return e.jsx("svg",{className:"chat-mini-head-heatmap",viewBox:"0 0 8 8",role:"img","aria-label":`${t.id} attention mini heatmap`,children:a.flatMap((s,i)=>a.map((r,o)=>{var c;const l=r>s?0:((c=t.distributionByToken[s])==null?void 0:c[r])??0;return e.jsx("rect",{x:o,y:i,width:"0.92",height:"0.92",fill:r>s?"#edf0f0":`rgba(36,139,120,${.12+Math.min(.88,l*5)})`},`${i}-${o}`)}))})}function pu({head:t,tokens:n,selectedSource:a,selectedDestination:s,onSelectPair:i}){const r=u.useRef(null),o=n.findIndex(p=>p.index===a),l=n.findIndex(p=>p.index===s);u.useEffect(()=>{const p=r.current;if(!p||n.length===0)return;const g=p.parentElement;if(!g)return;const b=()=>{var T;const y=g.getBoundingClientRect(),m=Math.max(1,Math.min(560,y.width)),x=window.devicePixelRatio||1;p.width=Math.round(m*x),p.height=Math.round(m*x);const w=p.getContext("2d");if(!w)return;w.setTransform(x,0,0,x,0,0),w.clearRect(0,0,m,m);const N=m/n.length;let A=1e-12;for(const k of n)for(const S of t.distributionByToken[k.index]??[])A=Math.max(A,S);for(let k=0;k<n.length;k+=1){const S=n[k].index;for(let L=0;L<n.length;L+=1){const M=n[L].index;if(M>S)w.fillStyle="#eef1f1";else{const F=((T=t.distributionByToken[S])==null?void 0:T[M])??0;w.fillStyle=`rgba(36, 139, 120, ${.08+Math.min(.92,F/A)})`}w.fillRect(L*N,k*N,Math.ceil(N),Math.ceil(N))}}l>=0&&(w.strokeStyle="#c58a32",w.lineWidth=2,w.strokeRect(.5,l*N+.5,m-1,N-1)),o>=0&&l>=0&&o<=l&&(w.strokeStyle="#1d4f48",w.lineWidth=2,w.strokeRect(o*N+.5,l*N+.5,Math.max(1,N-1),Math.max(1,N-1)))};b();const _=new ResizeObserver(b);return _.observe(g),()=>_.disconnect()},[t,l,o,n]);function c(p){var w,N;const g=r.current;if(!g)return;const b=g.getBoundingClientRect(),_=Math.max(0,Math.min(n.length-1,Math.floor((p.clientY-b.top)/b.height*n.length))),y=Math.max(0,Math.min(n.length-1,Math.floor((p.clientX-b.left)/b.width*n.length))),m=(w=n[_])==null?void 0:w.index,x=(N=n[y])==null?void 0:N.index;m!==void 0&&x!==void 0&&x<=m&&i(x,m)}function d(p){var y,m;if(!["ArrowLeft","ArrowRight","ArrowUp","ArrowDown","Home","End"].includes(p.key))return;p.preventDefault();const g=Math.max(0,l);let b=g,_=Math.max(0,o);p.key==="ArrowUp"&&(b=Math.max(0,g-1)),p.key==="ArrowDown"&&(b=Math.min(n.length-1,g+1)),p.key==="ArrowLeft"&&(_=Math.max(0,_-1)),p.key==="ArrowRight"&&(_=Math.min(b,_+1)),p.key==="Home"&&(_=0),p.key==="End"&&(_=b),i(((y=n[_])==null?void 0:y.index)??0,((m=n[b])==null?void 0:m.index)??0)}return e.jsxs("div",{className:"chat-attention-heatmap","aria-label":"Attention head heatmap",children:[e.jsx("canvas",{ref:r,role:"img",tabIndex:0,"aria-label":`${t.id} attention heatmap, destination ${s}, source ${a}`,onPointerDown:c,onKeyDown:d}),e.jsxs("div",{className:"chat-attention-heatmap-labels",children:[e.jsx("span",{children:"destination ↓"}),e.jsx("span",{children:"source →"})]})]})}function yu(t,n,a){return a.filter(s=>s.index<=n).map(s=>{var i;return{token:s,value:((i=t.distributionByToken[n])==null?void 0:i[s.index])??0}})}function wi(t,n,a){if(n.length===0)return;const s=Array.from({length:a},(o,l)=>{const c=Math.min(l+1,a);return Array.from({length:c},(d,p)=>{const g=n.map(b=>{var _;return(_=b.distributionByToken[l])==null?void 0:_[p]}).filter(b=>typeof b=="number"&&Number.isFinite(b));return g.length?g.reduce((b,_)=>b+_,0)/g.length:0})}),i=n.reduce((o,l)=>o+l.riskContribution,0)/n.length,r=n.reduce((o,l)=>o+l.entropy,0)/n.length;return{id:`L${t}AVG`,layer:t,head:-1,role:`Mean of ${n.length} heads`,riskContribution:i,entropy:r,distributionByToken:s,aggregation:"mean",memberHeadIds:n.map(o=>o.id)}}function ki(t,n){const a=t.distributionByToken[n]??[];let s=0;for(let i=1;i<=n;i+=1)(a[i]??0)>(a[s]??0)&&(s=i);return s}function fu(t,n){return t<=n?Array.from({length:t},(a,s)=>s):Array.from({length:n},(a,s)=>Math.round(s*(t-1)/(n-1)))}function Qr(t,n,a,s){var d;const i=(d=t.metadata)==null?void 0:d.attentionHeadCoverage;if(!i||typeof i!="object"||Array.isArray(i))return{storedAtLayer:a,availableAtLayer:a,storedTotal:s,complete:!1};const r=i,o=r.availableByLayer,l=o&&typeof o=="object"&&!Array.isArray(o)?Number(o[String(n)]):a,c=Number.isFinite(l)&&l>=a?l:a;return{storedAtLayer:a,availableAtLayer:c,storedTotal:s,complete:r.complete===!0&&a>=c}}function gu(t,n,a){return Qr(t,n,a,0).availableAtLayer}function vi(t,n){const a=Math.floor(Math.max(0,t)/512)*512;return{start:a,end:Math.min(n,a+512)}}function Dt(t){return t.trim()||"space"}function _u(t){var _;const[n,a]=u.useState(null),[s,i]=u.useState(null),r=u.useRef(null),o=u.useRef(null),l=u.useRef(0),c=u.useRef(new Set),d=u.useCallback(()=>{var y;(y=r.current)==null||y.close(),r.current=null},[]),p=u.useCallback((y,m)=>{var x;((x=o.current)==null?void 0:x.id)!==y.id||o.current.generation!==m||(a(y),i(y.status==="error"?Gt(y.kind,y.error??y.detail):null),y.status==="ready"&&y.result&&!c.current.has(y.id)?(c.current.add(y.id),d(),t(y.result,y)):(y.status==="error"||y.status==="cancelled")&&d())},[d,t]),g=u.useCallback(async y=>{var x,w;d();const m=++l.current;o.current={id:"submitting",generation:m},a(null),i(null);try{const N=await Fd(y);if(((x=o.current)==null?void 0:x.generation)!==m)return;o.current={id:N.id,generation:m},a(N);const A=new EventSource(Qt(N.id));r.current=A,A.addEventListener("job",T=>{if(!(T instanceof MessageEvent))return;let k;try{k=JSON.parse(T.data)}catch{d(),i(it("J-Lens progress stream returned invalid JSON.","jlens_stream_invalid_json"));return}const S=jr.safeParse(k);if(!S.success){d(),i(it("J-Lens progress payload failed validation.","jlens_stream_invalid_schema"));return}p(S.data,m)}),A.onerror=()=>{var T;((T=o.current)==null?void 0:T.generation)===m&&(d(),i(k=>k??Jt("J-Lens progress stream disconnected. Retry the job.")))}}catch(N){if(((w=o.current)==null?void 0:w.generation)!==m)return;o.current=null,i(st(N,"submission","J-Lens submission failed."))}},[p,d]),b=u.useCallback(async()=>{const y=o.current;if(!(!y||y.id==="submitting"))try{p(await Xs(y.id),y.generation)}catch(m){i(st(m,"cancellation","J-Lens cancellation failed."))}},[p]);return u.useEffect(()=>()=>{const y=o.current;d(),y&&y.id!=="submitting"&&Xs(y.id).catch(()=>{})},[d]),{job:n,error:s,submit:g,cancel:b,submitting:((_=o.current)==null?void 0:_.id)==="submitting"}}function bu(t){var y;const[n,a]=u.useState(null),[s,i]=u.useState(null),r=u.useRef(null),o=u.useRef(null),l=u.useRef(0),c=u.useRef(new Set),d=u.useCallback(()=>{var m;(m=r.current)==null||m.close(),r.current=null},[]),p=u.useCallback((m,x)=>{var w;((w=o.current)==null?void 0:w.id)!==m.id||o.current.generation!==x||(a(m),i(m.status==="error"?Gt(m.kind,m.error??m.detail):null),m.status==="ready"&&m.result&&!c.current.has(m.id)?(c.current.add(m.id),d(),t(m.result,m)):(m.status==="error"||m.status==="cancelled")&&d())},[d,t]),g=u.useCallback(async m=>{var w,N;d();const x=++l.current;o.current={id:"submitting",generation:x},a(null),i(null);try{const A=await Yd(m);if(((w=o.current)==null?void 0:w.generation)!==x)return;o.current={id:A.id,generation:x},a(A);const T=new EventSource(Qt(A.id));r.current=T,T.addEventListener("job",k=>{if(!(k instanceof MessageEvent))return;let S;try{S=JSON.parse(k.data)}catch{d(),i(it("NLA progress stream returned invalid JSON.","nla_stream_invalid_json"));return}const L=kr.safeParse(S);if(!L.success){d(),i(it("NLA progress payload failed validation.","nla_stream_invalid_schema"));return}p(L.data,x)}),T.onerror=()=>{var k;((k=o.current)==null?void 0:k.generation)===x&&(d(),i(S=>S??Jt("NLA progress stream disconnected. Retry the job.")))}}catch(A){if(((N=o.current)==null?void 0:N.generation)!==x)return;o.current=null,i(st(A,"submission","NLA submission failed."))}},[p,d]),b=u.useCallback(async()=>{const m=o.current;if(!(!m||m.id==="submitting"))try{p(await Gs(m.id),m.generation)}catch(x){i(st(x,"cancellation","NLA cancellation failed."))}},[p]),_=u.useCallback(()=>{d(),l.current+=1,o.current=null,a(null),i(null)},[d]);return u.useEffect(()=>()=>{const m=o.current;d(),m&&m.id!=="submitting"&&Gs(m.id).catch(()=>{})},[d]),{job:n,error:s,submit:g,cancel:b,reset:_,submitting:((y=o.current)==null?void 0:y.id)==="submitting"}}function xu({run:t,savedRun:n,onRunReady:a}){var be,se,te,le,he,ge,ve,qe;const s=Ea(n??t),[i,r]=u.useState("nla"),[o,l]=u.useState(s),[c,d]=u.useState(()=>ji(n??t,s)),[p,g]=u.useState([]),[b,_]=u.useState(null),[y,m]=u.useState(null),[x,w]=u.useState(null),[N,A]=u.useState(!1),[T,k]=u.useState(!1),[S,L]=u.useState(256),[M,F]=u.useState(""),[V,W]=u.useState("lens.pt"),[K,H]=u.useState("main"),[Z,D]=u.useState(null),[C,ne]=u.useState(null),[pe,R]=u.useState(!1),[j,ee]=u.useState(n??null),ue=u.useCallback((me,Ie)=>{ee(me),a(me,Ie)},[a]),oe=u.useCallback((me,Ie)=>{ee(me),a(me,Ie)},[a]),O=bu(ue),I=_u(oe),z=j??n??t,q=u.useMemo(()=>vu(t,p),[p,t]).find(me=>me.layer===o&&me.compatible),$=ju(z.nla,o,c),re=z.jLens.find(me=>me.layer===o&&me.tokenIndex===c),E=O.submitting||((be=O.job)==null?void 0:be.status)==="idle"||((se=O.job)==null?void 0:se.status)==="loading",Q=I.submitting||((te=I.job)==null?void 0:te.status)==="idle"||((le=I.job)==null?void 0:le.status)==="loading",U=i==="nla"?E:Q,de=!!(q&&(y!=null&&y.canSubmit)&&(!y.gated||T)&&!E),ae=!!(Z!=null&&Z.canSubmit&&!Q);u.useEffect(()=>{const me=new AbortController;return zd(me.signal).then(Ie=>{g(Ie),_(null)}).catch(Ie=>{me.signal.aborted||_(Ie instanceof Error?Ie.message:"Could not load NLA profiles.")}),()=>me.abort()},[]),u.useEffect(()=>{const me=new AbortController;return qd(me.signal).then(Ie=>{const Ce=Ie.profiles.find(Qe=>Qe.baseModel===t.modelName),Ue=!Ie.defaultModel||Ie.defaultModel===t.modelName;F(Ue?Ie.defaultSource:(Ce==null?void 0:Ce.source)??""),W(Ue?Ie.defaultFilename:(Ce==null?void 0:Ce.filename)??Ie.defaultFilename),H(Ue?Ie.defaultRevision:(Ce==null?void 0:Ce.revision)??Ie.defaultRevision),ne(null)}).catch(Ie=>{me.signal.aborted||ne(Ie instanceof Error?Ie.message:"Could not load J-Lens options.")}),()=>me.abort()},[t.modelName]),u.useEffect(()=>{if(m(null),w(null),k(!1),!q){A(!1);return}const me=new AbortController;return A(!0),Dd({modelName:t.modelName,dModel:t.nlaCompatibility.dModel,availableLayers:t.nlaCompatibility.availableLayers,profile:q.name},me.signal).then(m).catch(Ie=>{me.signal.aborted||w(Ie instanceof Error?Ie.message:"NLA preflight failed.")}).finally(()=>{me.signal.aborted||A(!1)}),()=>me.abort()},[t.modelName,t.nlaCompatibility.availableLayers,t.nlaCompatibility.dModel,q]),u.useEffect(()=>{if(D(null),!M.trim()||!V.trim()||!K.trim()){R(!1);return}const me=new AbortController;R(!0);const Ie=window.setTimeout(()=>{Hd({modelName:t.modelName,dModel:t.nlaCompatibility.dModel,availableLayers:t.layers,layer:o,tokenCount:t.tokens.length,position:c,lensSource:M.trim(),filename:V.trim(),revision:K.trim()},me.signal).then(Ce=>{D(Ce),ne(null)}).catch(Ce=>{me.signal.aborted||ne(Ce instanceof Error?Ce.message:"J-Lens preflight failed.")}).finally(()=>{me.signal.aborted||R(!1)})},220);return()=>{window.clearTimeout(Ie),me.abort()}},[V,K,M,t.layers,t.modelName,t.tokens.length,o,c]);function ce(me){if(r(me),me==="nla"){const Ce=Ea(z);l(Ce),d(ji(z,Ce));return}const Ie=Iu(z);l(Ie),d(Su(z,Ie))}function P(me){var Ce,Ue;l(me);const Ie=i==="nla"?z.nla.filter(Qe=>Qe.layer===me):z.jLens.filter(Qe=>Qe.layer===me);Ie.some(Qe=>Qe.tokenIndex===c)||d(((Ce=Ie[Ie.length-1])==null?void 0:Ce.tokenIndex)??((Ue=z.tokens[0])==null?void 0:Ue.index)??0)}function _e(){!q||!de||(ee(null),O.submit({run:t,profile:q.name,positions:[c],revision:"main",maxNewTokens:S,loadReconstructor:!0,confirmGatedAccess:T}))}function ie(){ae&&(ee(null),I.submit({run:t,layer:o,position:c,lensSource:M.trim(),filename:V.trim(),revision:K.trim(),topK:10}))}return e.jsxs("section",{className:"chat-analysis-workbench chat-explanation-workbench","aria-label":"Explanation workbench",children:[e.jsxs("header",{className:"chat-workbench-heading",children:[e.jsx("span",{children:e.jsx(dt,{size:17})}),e.jsxs("div",{children:[e.jsx("h2",{children:"Explanation"}),e.jsx("p",{children:"Describe hidden states and reveal the words they can influence"})]}),e.jsxs("span",{className:`chat-workbench-status ${($==null?void 0:$.status)==="available"||re?"ready":"idle"}`,children:[e.jsx("i",{}),i==="nla"?"NLA":"J-LENS"]})]}),e.jsxs("div",{className:"chat-explanation-tabs",role:"tablist","aria-label":"Explanation method",children:[e.jsxs("button",{type:"button",role:"tab","aria-selected":i==="nla",className:i==="nla"?"active":"",onClick:()=>ce("nla"),children:[e.jsx(dt,{size:16}),e.jsxs("span",{children:[e.jsx("b",{children:"NLA"}),e.jsx("small",{children:"Explain what the hidden state represents"})]})]}),e.jsxs("button",{type:"button",role:"tab","aria-selected":i==="j-lens",className:i==="j-lens"?"active":"",onClick:()=>ce("j-lens"),children:[e.jsx(ta,{size:16}),e.jsxs("span",{children:[e.jsx("b",{children:"J-Lens"}),e.jsx("small",{children:"Reveal vocabulary most affected by this state"})]})]})]}),e.jsxs("div",{className:"chat-explanation-selection",children:[e.jsxs("label",{children:[e.jsxs("span",{children:[e.jsx("b",{children:"1"})," Layer"]}),e.jsx("select",{"aria-label":"Explanation layer",value:o,disabled:U,onChange:me=>P(Number(me.target.value)),children:t.layers.map(me=>e.jsxs("option",{value:me,children:["Layer ",me]},me))})]}),e.jsxs("div",{className:"chat-explanation-token-picker",children:[e.jsxs("header",{children:[e.jsxs("span",{children:[e.jsx("b",{children:"2"})," Token position"]}),e.jsxs("small",{children:["T",c," · ",kn(Au(t,c))]})]}),e.jsx("div",{role:"radiogroup","aria-label":"Explanation token position",children:t.tokens.map(me=>e.jsxs("button",{type:"button",role:"radio","aria-checked":c===me.index,"aria-label":`Token ${me.index} ${kn(me.text)}`,className:c===me.index?"active":"",disabled:U,onClick:()=>d(me.index),children:[e.jsx("small",{children:me.index}),e.jsx("span",{children:kn(me.text)})]},me.index))})]})]}),i==="nla"?e.jsx(wu,{run:t,row:$,profile:q,preflight:y,preflightLoading:N,error:((he=O.error)==null?void 0:he.message)??x??b,progress:(ge=O.job)==null?void 0:ge.progress,running:E,canRun:de,confirmGatedAccess:T,maxNewTokens:S,onConfirmGatedAccess:k,onMaxNewTokensChange:L,onRun:_e,onCancel:()=>void O.cancel()}):e.jsx(ku,{row:re,source:M,filename:V,revision:K,preflight:Z,preflightLoading:pe,error:((ve=I.error)==null?void 0:ve.message)??C,progress:(qe=I.job)==null?void 0:qe.progress,running:Q,canRun:ae,onSourceChange:F,onFilenameChange:W,onRevisionChange:H,onRun:ie,onCancel:()=>void I.cancel()})]})}function wu({run:t,row:n,profile:a,preflight:s,preflightLoading:i,error:r,progress:o,running:l,canRun:c,confirmGatedAccess:d,maxNewTokens:p,onConfirmGatedAccess:g,onMaxNewTokensChange:b,onRun:_,onCancel:y}){var w,N;const m=(n==null?void 0:n.status)==="available",x=(s==null?void 0:s.reason)??Tu(t,a,n);return e.jsxs("div",{className:"chat-explanation-output",role:"tabpanel","aria-label":"NLA output",children:[e.jsxs("div",{className:"chat-explanation-provenance",children:[e.jsxs("span",{children:[e.jsx("small",{children:"Profile"}),e.jsx("b",{children:(a==null?void 0:a.name)??(n==null?void 0:n.profile)??"not registered"})]}),e.jsxs("span",{children:[e.jsx("small",{children:"Component"}),e.jsx("b",{children:(n==null?void 0:n.component)??(a==null?void 0:a.component)??"resid_post"})]}),e.jsxs("span",{children:[e.jsx("small",{children:"Evidence"}),e.jsx("b",{children:m?(w=n.generation)!=null&&w.complete?"AV + AR · complete":"AV + AR · legacy":"not computed"})]})]}),m?e.jsxs("article",{className:"chat-nla-result",children:[e.jsxs("header",{children:[e.jsx(ot,{size:17}),e.jsx("span",{children:"What this activation represents"})]}),(N=n.generation)!=null&&N.complete?e.jsxs("small",{className:"chat-nla-generation-state complete",children:["Complete · ",n.generation.generatedTokenCount," / ",n.generation.requestedMaxNewTokens," tokens"]}):e.jsx("small",{className:"chat-nla-generation-state legacy",children:"Legacy artifact · completion was not recorded"}),e.jsx("p",{children:n.explanation}),e.jsxs("dl",{children:[e.jsxs("div",{children:[e.jsx("dt",{children:"Cosine"}),e.jsx("dd",{children:on(n.cosine)})]}),e.jsxs("div",{children:[e.jsx("dt",{children:"FVE"}),e.jsx("dd",{children:n.fve===void 0?"n/a":on(n.fve)})]}),e.jsxs("div",{children:[e.jsx("dt",{children:"MSE"}),e.jsx("dd",{children:on(n.mse)})]}),e.jsxs("div",{children:[e.jsx("dt",{children:"Activation norm"}),e.jsx("dd",{children:on(n.activationNorm)})]})]})]}):e.jsxs("div",{className:"chat-nla-empty",children:[e.jsx(Lt,{size:18}),e.jsxs("div",{children:[e.jsx("strong",{children:"No exact NLA explanation at this layer and token."}),e.jsx("p",{children:x})]})]}),(s==null?void 0:s.gated)&&e.jsxs("label",{className:"chat-nla-gated",children:[e.jsx("input",{type:"checkbox",checked:d,disabled:!s.tokenConfigured||l,onChange:A=>g(A.target.checked)}),e.jsx(Vo,{size:14})," Confirm local access to this gated profile"]}),e.jsxs("div",{className:"chat-nla-actions",children:[e.jsxs("span",{"aria-live":"polite",className:r?"failed":"",children:[l?e.jsx(Vt,{size:15}):r?e.jsx(Lt,{size:15}):e.jsx(ot,{size:15}),l?`${o??0}% · ${(s==null?void 0:s.reason)??"Generating explanation"}`:r??(i?"Checking NLA compatibility":m?"Exact explanation loaded":x)]}),e.jsxs("label",{className:"chat-nla-token-budget",children:[e.jsx("span",{children:"Max tokens"}),e.jsx("input",{"aria-label":"NLA explanation tokens",type:"number",min:8,max:512,value:p,disabled:l,onChange:A=>b(Cu(A.target.value,8,512))})]}),e.jsxs("button",{type:"button",disabled:!c&&!l,onClick:l?y:_,children:[l?e.jsx(Kt,{size:14}):e.jsx(Zn,{size:14}),l?"Cancel":m?"Regenerate NLA":"Run NLA"]})]})]})}function ku({row:t,source:n,filename:a,revision:s,preflight:i,preflightLoading:r,error:o,progress:l,running:c,canRun:d,onSourceChange:p,onFilenameChange:g,onRevisionChange:b,onRun:_,onCancel:y}){const m=Math.max(1e-12,...((t==null?void 0:t.topPredictions)??[]).map(x=>Math.abs(x.logit)));return e.jsxs("div",{className:"chat-explanation-output",role:"tabpanel","aria-label":"J-Lens output",children:[e.jsxs("details",{className:"chat-jlens-config",open:!n,children:[e.jsx("summary",{children:"Lens artifact"}),e.jsxs("div",{children:[e.jsxs("label",{children:[e.jsx("span",{children:"Repository or local path"}),e.jsx("input",{"aria-label":"J-Lens artifact source",value:n,disabled:c,placeholder:"organization/lens-repository",onChange:x=>p(x.target.value)})]}),e.jsxs("label",{children:[e.jsx("span",{children:"Checkpoint file"}),e.jsx("input",{"aria-label":"J-Lens checkpoint file",value:a,disabled:c,onChange:x=>g(x.target.value)})]}),e.jsxs("label",{children:[e.jsx("span",{children:"Revision"}),e.jsx("input",{"aria-label":"J-Lens artifact revision",value:s,disabled:c,onChange:x=>b(x.target.value)})]})]})]}),t?e.jsxs(e.Fragment,{children:[e.jsxs("div",{className:"chat-jlens-target",children:[e.jsxs("span",{children:[e.jsx("small",{children:"Observed next token"}),e.jsx("b",{children:kn(t.targetTokenText)})]}),e.jsxs("span",{children:[e.jsx("small",{children:"Target rank"}),e.jsxs("b",{children:["#",t.targetRank.toLocaleString()]})]}),e.jsxs("span",{children:[e.jsx("small",{children:"Target logit"}),e.jsx("b",{children:on(t.targetLogit)})]}),e.jsxs("span",{children:[e.jsx("small",{children:"Probability"}),e.jsx("b",{children:Nu(t.targetProbability)})]})]}),e.jsxs("section",{className:"chat-jlens-predictions","aria-label":"J-Lens vocabulary predictions",children:[e.jsxs("header",{children:[e.jsx("strong",{children:"Top vocabulary outputs"}),e.jsx("span",{children:"J(layer) x residual -> final norm -> unembed"})]}),t.topPredictions.map((x,w)=>e.jsxs("div",{children:[e.jsx("small",{children:w+1}),e.jsx("b",{children:kn(x.tokenText)}),e.jsx("i",{children:e.jsx("span",{style:{width:`${Math.max(4,Math.abs(x.logit)/m*100)}%`}})}),e.jsx("em",{children:on(x.logit)})]},`${x.tokenId}-${w}`))]}),e.jsxs("p",{className:"chat-explanation-note",children:["Jacobian lens fitted on ",t.nPrompts.toLocaleString()," prompts. ",t.sourceKey]})]}):e.jsxs("div",{className:"chat-nla-empty",children:[e.jsx(Lt,{size:18}),e.jsxs("div",{children:[e.jsx("strong",{children:"No Jacobian Lens result at this layer and token."}),e.jsx("p",{children:n?(i==null?void 0:i.reason)??"Check the configured lens artifact.":"Configure a fitted Jacobian lens artifact."})]})]}),!t&&e.jsxs("div",{className:"chat-nla-actions",children:[e.jsxs("span",{"aria-live":"polite",className:o?"failed":"",children:[c?e.jsx(Vt,{size:15}):o||!(i!=null&&i.canSubmit)?e.jsx(Lt,{size:15}):e.jsx(ot,{size:15}),c?`${l??0}% · ${(i==null?void 0:i.reason)??"Computing Jacobian readout"}`:o??(r?"Checking J-Lens configuration":(i==null?void 0:i.reason)??"Configure a lens artifact")]}),e.jsxs("button",{type:"button",disabled:!d&&!c,onClick:c?y:_,children:[c?e.jsx(Kt,{size:14}):e.jsx(Zn,{size:14}),c?"Cancel":"Run J-Lens"]})]})]})}function vu(t,n){const a=new Map;for(const s of t.nlaCompatibility.profiles)a.set(s.name,{name:s.name,baseModel:s.baseModel,layer:s.layer,component:s.component,dModel:s.dModel,gated:!1,compatible:s.status!=="incompatible"});for(const s of n){const i=a.get(s.name);a.set(s.name,{name:s.name,baseModel:s.base_model,layer:s.layer,component:s.component,dModel:s.d_model,gated:s.gated,compatible:(i==null?void 0:i.compatible)??(s.base_model===t.modelName&&s.d_model===t.nlaCompatibility.dModel&&t.layers.includes(s.layer))})}return[...a.values()]}function ju(t,n,a){const s=t.filter(i=>i.layer===n&&i.tokenIndex===a);return s.find(i=>i.status==="available"&&i.component==="resid_post")??s.find(i=>i.status==="available")??s.find(i=>i.component==="resid_post")??s[0]}function Ea(t){var n,a,s;return((n=t.nla.find(i=>i.status==="available"))==null?void 0:n.layer)??((a=t.nlaCompatibility.profiles.find(i=>i.status!=="incompatible"))==null?void 0:a.layer)??((s=t.nla[0])==null?void 0:s.layer)??t.layers[t.layers.length-1]??0}function Iu(t){var a;const n=Ea(t);return((a=t.jLens[t.jLens.length-1])==null?void 0:a.layer)??(t.layers.includes(n)?n:t.layers[0]??0)}function ji(t,n){var a,s,i;return((a=t.nla.find(r=>r.layer===n&&r.status==="available"))==null?void 0:a.tokenIndex)??((s=t.nla.find(r=>r.layer===n))==null?void 0:s.tokenIndex)??((i=t.tokens[t.tokens.length-1])==null?void 0:i.index)??0}function Su(t,n){var s,i;const a=t.jLens.filter(r=>r.layer===n);return((s=a[a.length-1])==null?void 0:s.tokenIndex)??((i=t.tokens[t.tokens.length-1])==null?void 0:i.index)??0}function Tu(t,n,a){var i;return n?`Profile ${n.name} is registered; run compatibility must pass before generation.`:((i=t.nlaCompatibility.profiles.find(r=>r.layer===(a==null?void 0:a.layer)))==null?void 0:i.reason)??`No registered NLA profile matches ${t.modelName} at this layer.`}function Au(t,n){var a;return((a=t.tokens.find(s=>s.index===n))==null?void 0:a.text)??""}function kn(t){return t.trim()||"space"}function on(t){return Math.abs(t)>0&&Math.abs(t)<.001?t.toExponential(2):t.toFixed(4)}function Nu(t){return t<.001?t.toExponential(2):`${(t*100).toFixed(2)}%`}function Cu(t,n,a){const s=Number(t);return Number.isFinite(s)?Math.max(n,Math.min(a,Math.round(s))):n}function Ru({ariaLabel:t,label:n,value:a,direction:s,contextQuery:i="",disabled:r=!1,onChange:o,onSelectPreset:l}){const[c,d]=u.useState(!1),[p,g]=u.useState(0),[b,_]=u.useState(ru),[y,m]=u.useState(!1),[x,w]=u.useState(""),[N,A]=u.useState("safety"),T=u.useRef(null),k=u.useRef(null),S=u.useId(),L=u.useMemo(()=>lu(a,s,b,i),[i,s,b,a]),M=Math.min(p,Math.max(0,L.length-1)),F=L[M],V=c&&F?`${S}-option-${M}`:void 0,W=u.useMemo(()=>du(s,N,b),[N,s,b]);u.useEffect(()=>{const D=[...b,...aa].find(C=>C.direction===s&&C.text===a&&C.category);D!=null&&D.category&&A(D.category)},[s,b,a]);function K(D){l?l(D):o(D.text),d(!1),g(0),window.requestAnimationFrame(()=>{var C;return(C=k.current)==null?void 0:C.focus()})}function H(D){const C=b.filter(ne=>ne.id!==D);_(C),xi(C)}function Z(){const D=x.trim();if(!D||!a.trim())return;const C=[...b,ou(D,a,s,N)];_(C),xi(C),w(""),m(!1)}return e.jsxs("div",{ref:T,className:"preset-suggest",onBlur:D=>{D.currentTarget.contains(D.relatedTarget)||(d(!1),m(!1))},children:[e.jsxs("span",{children:[n,e.jsxs("button",{type:"button",className:"preset-suggest-save","aria-label":`Save current ${n} text as a preset`,disabled:r||!a.trim(),onClick:()=>m(D=>!D),children:[e.jsx(Qi,{size:12})," Save as preset"]})]}),e.jsxs("div",{className:"preset-suggest-categories",role:"group","aria-label":`${n} category`,children:[iu.map(D=>e.jsx("button",{type:"button",className:N===D.id?"active":"","aria-pressed":N===D.id,disabled:r,onClick:()=>A(D.id),children:D.label},D.id)),e.jsxs("select",{"aria-label":`${n} direction preset`,value:"",disabled:r,onChange:D=>{const C=W.find(ne=>ne.id===D.target.value);C&&K(C)},children:[e.jsx("option",{value:"",children:"Choose direction..."}),W.map(D=>e.jsx("option",{value:D.id,children:D.label},D.id))]})]}),e.jsx("textarea",{ref:k,"aria-label":t,rows:3,value:a,disabled:r,role:"combobox","aria-expanded":c,"aria-controls":S,"aria-autocomplete":"list","aria-activedescendant":V,onFocus:()=>d(!0),onChange:D=>{o(D.target.value),c||d(!0),g(0)},onKeyDown:D=>{if(D.key==="Escape"){c&&(D.preventDefault(),d(!1));return}c&&(D.key==="ArrowDown"?(D.preventDefault(),g(Math.min(L.length-1,M+1))):D.key==="ArrowUp"?(D.preventDefault(),g(Math.max(0,M-1))):D.key==="Home"?(D.preventDefault(),g(0)):D.key==="End"?(D.preventDefault(),g(Math.max(0,L.length-1))):D.key==="Enter"&&F&&(D.preventDefault(),K(F)))}}),L.length>0&&e.jsx("div",{className:"preset-suggest-chips","aria-label":`${n} suggested presets`,children:L.slice(0,3).map(D=>e.jsx("button",{type:"button",disabled:r,title:D.text,onClick:()=>K(D),children:D.label},`chip-${D.id}`))}),y&&e.jsxs("div",{className:"preset-suggest-save-form",role:"group","aria-label":`Save ${n} preset`,children:[e.jsx("input",{"aria-label":"Preset label",placeholder:"Preset label",value:x,onChange:D=>w(D.target.value),onKeyDown:D=>{D.key==="Enter"&&(D.preventDefault(),Z())}}),e.jsx("button",{type:"button",onClick:Z,disabled:!x.trim(),children:"Save"})]}),c&&L.length>0&&e.jsx("div",{id:S,className:"preset-suggest-list",role:"listbox","aria-label":`${n} preset suggestions`,children:L.map((D,C)=>e.jsxs("button",{id:`${S}-option-${C}`,type:"button",role:"option","aria-selected":C===M,className:`preset-suggest-item ${C===M?"highlighted":""}`,"data-source":D.source,onMouseEnter:()=>g(C),onMouseDown:ne=>ne.preventDefault(),onClick:()=>K(D),children:[e.jsx("strong",{children:D.label}),e.jsx("em",{children:D.source==="user"?"custom":"builtin"}),e.jsx("small",{children:D.text}),D.source==="user"&&e.jsx("span",{role:"button","aria-label":`Delete preset ${D.label}`,className:"preset-suggest-delete",onClick:ne=>{ne.stopPropagation(),H(D.id)},onKeyDown:ne=>{(ne.key==="Enter"||ne.key===" ")&&(ne.preventDefault(),ne.stopPropagation(),H(D.id))},children:e.jsx(at,{size:12})})]},D.id))})]})}function Lu({modelName:t,response:n,selectedIndex:a,disabled:s=!1,onSelect:i,onTokensChange:r}){const[o,l]=u.useState([]),[c,d]=u.useState("idle");return u.useEffect(()=>{if(!n.trim()){l([]),r==null||r([]),d("idle");return}l([]),r==null||r([]),d("loading");const g=new AbortController,b=window.setTimeout(()=>{Pd(t,n,g.signal).then(_=>{l(_.tokens),r==null||r(_.tokens),d("ready")}).catch(()=>{g.signal.aborted||(l([]),r==null||r([]),d("error"))})},180);return()=>{window.clearTimeout(b),g.abort()}},[t,r,n]),u.useEffect(()=>{o.length>0&&a>=o.length&&i(o.length-1)},[i,a,o.length]),e.jsxs("div",{className:"response-token-picker","aria-label":"Attribution target token","aria-busy":c==="loading",children:[e.jsxs("header",{children:[e.jsx("span",{children:"Target response token"}),o.length>0&&e.jsx("button",{type:"button",disabled:s,onClick:()=>i(0),children:"Reset to first"})]}),c==="loading"?e.jsx("div",{className:"response-token-picker-empty",role:"status",children:"Tokenizing response..."}):c==="error"?e.jsx("div",{className:"response-token-picker-empty is-error",role:"status",children:"Tokenizer unavailable. Check the local model worker."}):o.length>0?e.jsx("div",{className:"response-token-picker-list",role:"group","aria-label":"Response tokens",children:o.map((p,g)=>e.jsxs("button",{type:"button",className:g===a?"active":"","aria-pressed":g===a,disabled:s,title:`Target token ${g} · ${p.text||"space"} · ID ${p.tokenId}`,onClick:()=>i(g),children:[p.text||"space",e.jsxs("sub",{children:["T",g]})]},`${g}:${p.tokenId}`))}):e.jsx("div",{className:"response-token-picker-empty",role:"status",children:"Type or paste the model response to pick a target token."})]})}function $u({mode:t,run:n,remoteSummary:a,savedRun:s,suggestionQuery:i,onRunReady:r}){return t==="steering"?e.jsx(Wu,{run:n,savedRun:s,suggestionQuery:i,onRunReady:r}):t==="attribution"?e.jsx(zu,{run:n,savedRun:s,onRunReady:r}):t==="patching"?e.jsx(Mu,{run:n,savedRun:s,onRunReady:r}):t==="neuron"?e.jsx(Eu,{run:n,savedRun:s,onRunReady:r}):t==="feature"?e.jsx(Pu,{run:n,savedRun:s,onRunReady:r}):t==="explanation"?e.jsx(xu,{run:n,savedRun:s,onRunReady:r}):e.jsx(mu,{run:n,remoteSummary:a})}function Eu({run:t,savedRun:n,onRunReady:a}){var D,C,ne,pe,R,j,ee,ue,oe,O;const s=((D=n==null?void 0:n.intervention)==null?void 0:D.mode)==="neuron"?n.intervention:void 0,i=u.useMemo(()=>[...new Set(t.mlpNeurons.map(I=>I.layer))].sort((I,z)=>I-z),[t.mlpNeurons]),[r,o]=u.useState(((C=s==null?void 0:s.feature)==null?void 0:C.layer)??i[i.length-1]??t.layers[t.layers.length-1]??0),l=u.useMemo(()=>t.mlpNeurons.filter(I=>I.layer===r).sort((I,z)=>z.maxAbsoluteActivation-I.maxAbsoluteActivation),[r,t.mlpNeurons]),[c,d]=u.useState(((ne=s==null?void 0:s.feature)==null?void 0:ne.neuron)??((pe=l[0])==null?void 0:pe.neuron)??0),[p,g]=u.useState((s==null?void 0:s.scale)??0),[b,_]=u.useState((s==null?void 0:s.positionStart)??0),[y,m]=u.useState((s==null?void 0:s.positionEnd)??t.tokens.length),x=u.useMemo(()=>ia(t),[t]),[w,N]=u.useState((s==null?void 0:s.targetTokenId)??((R=x[0])==null?void 0:R.tokenId)??0),[A,T]=u.useState(null),[k,S]=u.useState(null),[L,M]=u.useState(((j=n==null?void 0:n.intervention)==null?void 0:j.mode)==="neuron"?n:null),F=u.useCallback((I,z)=>{M(I),a(I,z)},[a]),V=ts(F),W=V.submitting||((ee=V.job)==null?void 0:ee.status)==="idle"||((ue=V.job)==null?void 0:ue.status)==="loading",K=l.find(I=>I.neuron===c)??l[0];u.useEffect(()=>{var I;l.some(z=>z.neuron===c)||d(((I=l[0])==null?void 0:I.neuron)??0)},[c,l]),u.useEffect(()=>{!i.includes(r)&&i.length&&o(i[i.length-1])},[i,r]),u.useEffect(()=>{const I=new AbortController;T(null),S(null);const z=window.setTimeout(()=>{Qa({mode:"neuron",modelName:t.modelName,promptTokenCount:t.tokens.length,availableLayers:t.layers,layer:r,component:"mlp_out",positionStart:b,positionEnd:y,targetTokenId:w,neuron:c,availableNeurons:l.map(Y=>Y.neuron),desiredPrompt:"Enhance selected MLP neuron",undesiredPrompt:"Suppress selected MLP neuron"},I.signal).then(T).catch(Y=>{I.signal.aborted||S(Y instanceof Error?Y.message:"Neuron preflight failed.")})},180);return()=>{window.clearTimeout(z),I.abort()}},[r,c,l,y,b,t.layers,t.modelName,t.tokens.length,w]);function H(I,z){const Y=Math.max(0,Math.min(t.tokens.length-1,I));_(Y),m(Math.max(Y+1,Math.min(t.tokens.length,z)))}function Z(){if(!(A!=null&&A.canSubmit)||W||!K)return;M(null);const I={run:t,mode:"neuron",desiredPrompt:"Enhance selected MLP neuron",undesiredPrompt:"Suppress selected MLP neuron",layer:r,component:"mlp_out",neuron:c,scale:p,positionStart:b,positionEnd:y,targetTokenId:w,seed:0,maxNewTokens:16,temperature:0};V.submit(I)}return i.length===0?e.jsx("section",{className:"chat-analysis-workbench chat-feature-workbench","aria-label":"MLP neuron intervention workbench",children:e.jsxs("header",{className:"chat-workbench-heading",children:[e.jsx("span",{children:e.jsx(Be,{size:17})}),e.jsxs("div",{children:[e.jsx("h2",{children:"Neuron intervention"}),e.jsx("p",{children:"This run does not expose MLP neuron activations."})]})]})}):e.jsxs("section",{className:"chat-analysis-workbench chat-feature-workbench","aria-label":"MLP neuron intervention workbench",children:[e.jsxs("header",{className:"chat-workbench-heading",children:[e.jsx("span",{children:e.jsx(Be,{size:17})}),e.jsxs("div",{children:[e.jsx("h2",{children:"Neuron intervention"}),e.jsx("p",{children:"Scale one real MLP post-activation and compare the model output"})]}),e.jsx(sa,{ready:!!(A!=null&&A.canSubmit),pending:!A&&!k})]}),e.jsxs("div",{className:"chat-feature-controls",children:[e.jsxs("label",{children:[e.jsx("span",{children:"Layer"}),e.jsx("select",{"aria-label":"Neuron intervention layer",value:r,disabled:W,onChange:I=>o(Number(I.target.value)),children:i.map(I=>e.jsxs("option",{value:I,children:["L",I]},I))})]}),e.jsxs("label",{children:[e.jsx("span",{children:"MLP neuron"}),e.jsx("select",{"aria-label":"MLP neuron",value:c,disabled:W,onChange:I=>d(Number(I.target.value)),children:l.map(I=>e.jsxs("option",{value:I.neuron,children:["N",I.neuron," · ",I.label]},I.neuron))})]}),e.jsxs("label",{children:[e.jsx("span",{children:"Tracked output token"}),e.jsx("select",{"aria-label":"Neuron tracked output token",value:w,disabled:W,onChange:I=>N(Number(I.target.value)),children:x.map(I=>e.jsxs("option",{value:I.tokenId,children:[Ze(I.tokenText)," · #",I.tokenId]},I.tokenId))})]}),e.jsxs("label",{className:"chat-feature-strength",children:[e.jsxs("span",{children:["Activation factor ",e.jsx("b",{children:p.toFixed(1)})]}),e.jsx("input",{"aria-label":"Neuron activation factor",type:"range",min:-2,max:4,step:.1,value:p,disabled:W,onChange:I=>g(Number(I.target.value))})]})]}),e.jsx("div",{className:"chat-feature-operations",role:"group","aria-label":"Neuron intervention operation",children:[{label:"Suppress",value:0},{label:"Reduce",value:.25},{label:"Enhance",value:2},{label:"Invert",value:-1}].map(I=>e.jsx("button",{type:"button",className:Math.abs(p-I.value)<1e-6?"active":"","aria-pressed":Math.abs(p-I.value)<1e-6,disabled:W,onClick:()=>g(I.value),children:I.label},I.label))}),e.jsxs("div",{className:"chat-token-range",children:[e.jsxs("header",{children:[e.jsx("span",{children:"Apply to"}),e.jsxs("div",{children:[e.jsx("button",{className:b===0&&y===t.tokens.length?"active":"","aria-pressed":b===0&&y===t.tokens.length,disabled:W,onClick:()=>H(0,t.tokens.length),children:"Entire input"}),e.jsx("button",{className:b===t.tokens.length-1&&y===t.tokens.length?"active":"","aria-pressed":b===t.tokens.length-1&&y===t.tokens.length,disabled:W,onClick:()=>H(t.tokens.length-1,t.tokens.length),children:"Last token"})]}),e.jsxs("small",{children:["T",b,"–T",y-1]})]}),e.jsx("div",{"aria-label":"Neuron intervention token range",children:t.tokens.map(I=>e.jsx("button",{className:I.index>=b&&I.index<y?"active":"","aria-pressed":I.index>=b&&I.index<y,disabled:W,onClick:()=>H(I.index,I.index+1),children:Ze(I.text)},I.index))})]}),e.jsxs("div",{className:"chat-feature-selected",children:[e.jsx("strong",{children:K==null?void 0:K.id}),e.jsx("span",{children:K==null?void 0:K.label}),e.jsxs("small",{children:["peak activation ",K==null?void 0:K.maxAbsoluteActivation.toFixed(4)," · factor ",p.toFixed(1)]})]}),e.jsx(Tn,{running:W,disabled:!(A!=null&&A.canSubmit)||!K,runLabel:"Run neuron intervention",status:((oe=V.error)==null?void 0:oe.message)??k??(A==null?void 0:A.reason),progress:(O=V.job)==null?void 0:O.progress,onRun:Z,onCancel:()=>void V.cancel(),onReset:V.reset,failed:!!V.error}),(L==null?void 0:L.intervention)&&e.jsx(ns,{experiment:L.intervention})]})}function Mu({run:t,savedRun:n,onRunReady:a}){var pe,R,j,ee,ue,oe;const s=(n==null?void 0:n.patching)??t.patching,[i,r]=u.useState((s==null?void 0:s.corruptedPrompt)??t.prompt),[o,l]=u.useState((s==null?void 0:s.component)??"resid_post"),[c,d]=u.useState((s==null?void 0:s.layers)??Fu(t.layers)),[p,g]=u.useState((s==null?void 0:s.head)??0),[b,_]=u.useState((s==null?void 0:s.positions)??[]),y=u.useMemo(()=>ia(t),[t]),[m,x]=u.useState((s==null?void 0:s.targetTokenId)??((pe=y[0])==null?void 0:pe.tokenId)??0),[w,N]=u.useState(null),[A,T]=u.useState(null),[k,S]=u.useState(n!=null&&n.patching?n:s?t:null),L=u.useMemo(()=>t.tokens.map(O=>O.tokenId),[t.tokens]),M=u.useCallback((O,I)=>{S(O),a(O,I)},[a]),F=nu(M),V=F.submitting||((R=F.job)==null?void 0:R.status)==="idle"||((j=F.job)==null?void 0:j.status)==="loading";u.useEffect(()=>{const O=new AbortController;N(null),T(null);const I=window.setTimeout(()=>{Ud({modelName:t.modelName,cleanPrompt:t.prompt,corruptedPrompt:i,cleanTokenIds:L,layers:t.layers,component:o,targetTokenId:m},O.signal).then(z=>{N(z),_(Y=>{const q=Y.filter($=>$<z.cleanTokenCount).slice(0,8);return q.length>0?q:z.changedPositions.slice(0,8)})}).catch(z=>{O.signal.aborted||T(z instanceof Error?z.message:"Patching preflight failed.")})},260);return()=>{window.clearTimeout(I),O.abort()}},[o,i,t.layers,t.modelName,t.prompt,L,m]);const W=c.length*b.length,K=Ku(t,c[0]??t.layers[0]??0),H=!!(w!=null&&w.canSubmit&&W>0&&W<=64&&!V);u.useEffect(()=>{g(O=>Math.min(O,Math.max(0,K-1)))},[K]);function Z(O){if(o==="z"){d([O]);return}d(I=>I.includes(O)?I.length===1?I:I.filter(z=>z!==O):I.length>=8?I:[...I,O].sort((z,Y)=>z-Y))}function D(O){l(O),O==="z"&&d(I=>[I[0]??t.layers[0]??0])}function C(O){_(I=>I.includes(O)?I.length===1?I:I.filter(z=>z!==O):I.length>=8?I:[...I,O].sort((z,Y)=>z-Y))}function ne(){H&&(S(null),F.submit({run:t,corruptedPrompt:i,component:o,layers:c,positions:b,...o==="z"?{head:p}:{},targetTokenId:m}))}return e.jsxs("section",{className:"chat-analysis-workbench chat-patching-workbench","aria-label":"Activation patching workbench",children:[e.jsxs("header",{className:"chat-workbench-heading",children:[e.jsx("span",{children:e.jsx(yt,{size:17})}),e.jsxs("div",{children:[e.jsx("h2",{children:"Activation patching"}),e.jsx("p",{children:"Clean activation replacement"})]}),e.jsx(sa,{ready:!!(w!=null&&w.canSubmit),pending:!w&&!A})]}),e.jsxs("div",{className:"chat-patching-prompts",children:[e.jsxs("label",{className:"is-clean",children:[e.jsxs("span",{children:["Clean ",e.jsx("small",{children:"current run"})]}),e.jsx("textarea",{"aria-label":"Clean patching input",rows:4,value:t.prompt,readOnly:!0})]}),e.jsxs("label",{className:"is-corrupt",children:[e.jsxs("span",{children:["Corrupt ",e.jsx("small",{children:"editable"})]}),e.jsx("textarea",{"aria-label":"Corrupt patching input",rows:4,value:i,disabled:V,"aria-invalid":w&&!w.canSubmit?!0:void 0,onChange:O=>r(O.target.value)})]})]}),e.jsxs("div",{className:"chat-patching-controls",children:[e.jsxs("fieldset",{children:[e.jsx("legend",{children:"Activation site"}),e.jsx("div",{role:"group","aria-label":"Patching activation site",children:["resid_post","attn_out","z","mlp_out"].map(O=>e.jsx("button",{type:"button",className:o===O?"active":"","aria-pressed":o===O,disabled:V,onClick:()=>D(O),children:Uu(O)},O))})]}),o==="z"&&e.jsxs("label",{children:[e.jsx("span",{children:"Attention head"}),e.jsx("select",{"aria-label":"Patching attention head",value:p,disabled:V,onChange:O=>g(Number(O.target.value)),children:Array.from({length:K},(O,I)=>e.jsxs("option",{value:I,children:["H",I]},I))})]}),e.jsxs("label",{children:[e.jsx("span",{children:"Tracked output token"}),e.jsx("select",{"aria-label":"Patching tracked output token",value:m,disabled:V,onChange:O=>x(Number(O.target.value)),children:y.map(O=>e.jsxs("option",{value:O.tokenId,children:[Ze(O.tokenText)," · #",O.tokenId]},O.tokenId))})]}),e.jsxs("div",{className:`chat-patching-alignment ${w!=null&&w.canSubmit?"ready":"blocked"}`,"aria-live":"polite",children:[e.jsx("strong",{children:w!=null&&w.canSubmit?"Aligned":w?"Needs alignment":"Checking"}),e.jsx("span",{children:w?`${w.cleanTokenCount} clean · ${w.corruptedTokenCount} corrupt · ${w.changedPositions.length} changed`:"Tokenizing both inputs"})]})]}),w!=null&&w.corruptedTokens.length?e.jsxs("div",{className:"chat-patching-positions",children:[e.jsxs("header",{children:[e.jsx("span",{children:"Patch positions"}),e.jsxs("small",{children:[b.length,"/8 selected"]})]}),e.jsx("div",{role:"group","aria-label":"Patching token positions",children:w.corruptedTokens.map(O=>{var I,z;return e.jsxs("button",{type:"button",className:`${O.changed?"changed":""} ${b.includes(O.index)?"active":""}`,"aria-label":`Patch token ${O.index}: ${Ze(((I=t.tokens[O.index])==null?void 0:I.text)??"")} to ${Ze(O.text)}`,"aria-pressed":b.includes(O.index),disabled:V||!w.tokenCountMatches||!b.includes(O.index)&&b.length>=8,onClick:()=>C(O.index),children:[e.jsxs("small",{children:["T",O.index]}),e.jsx("span",{children:Ze(((z=t.tokens[O.index])==null?void 0:z.text)??"")}),e.jsx(ea,{size:12}),e.jsx("b",{children:Ze(O.text)})]},O.index)})})]}):null,e.jsxs("div",{className:"chat-patching-layers",children:[e.jsxs("header",{children:[e.jsx("span",{children:"Layers"}),e.jsxs("small",{children:[o==="z"?`H${p} · one layer`:`${c.length}/8 selected`," · ",W," patches"]})]}),e.jsx("div",{role:"group","aria-label":"Patching layers",children:t.layers.map(O=>e.jsxs("button",{type:"button",className:c.includes(O)?"active":"","aria-pressed":c.includes(O),disabled:V||o!=="z"&&!c.includes(O)&&c.length>=8,onClick:()=>Z(O),children:["L",O]},O))})]}),e.jsx(Tn,{running:V,disabled:!H,runLabel:`Run ${W||""} patch${W===1?"":"es"}`.replace("  "," "),status:((ee=F.error)==null?void 0:ee.message)??A??((ue=F.job)==null?void 0:ue.detail)??(w==null?void 0:w.reason),progress:(oe=F.job)==null?void 0:oe.progress,onRun:ne,onCancel:()=>void F.cancel(),onReset:F.reset,failed:!!F.error}),(k==null?void 0:k.patching)&&e.jsx(Yu,{experiment:k.patching})]})}function Pu({run:t,savedRun:n,onRunReady:a}){var At,Nt,je,Nn,_t,Xt,oa,ht,we,We,Mt,Pt,et,Zt,pt,Re,Cn;const s=((At=n==null?void 0:n.intervention)==null?void 0:At.mode)==="sae_feature"?n.intervention:((Nt=t.intervention)==null?void 0:Nt.mode)==="sae_feature"?t.intervention:void 0,[i,r]=u.useState([]),[o,l]=u.useState(null),[c,d]=u.useState("custom"),[p,g]=u.useState([]),[b,_]=u.useState(!1),[y,m]=u.useState(null),[x,w]=u.useState(""),[N,A]=u.useState(((je=s==null?void 0:s.feature)==null?void 0:je.featureIndex)??0),[T,k]=u.useState(!1),[S,L]=u.useState(((Nn=s==null?void 0:s.feature)==null?void 0:Nn.operation)==="ablate"?"ablate":"add"),M=Math.max(0,t.tokens.length-1),[F,V]=u.useState("output_boundary"),W=u.useMemo(()=>F==="output_boundary"?{start:M,end:t.tokens.length}:Vu(t),[F,M,t]),[K,H]=u.useState((s==null?void 0:s.scale)??100),[Z,D]=u.useState((s==null?void 0:s.positionStart)??M),[C,ne]=u.useState((s==null?void 0:s.positionEnd)??t.tokens.length),[pe,R]=u.useState((s==null?void 0:s.maxNewTokens)??64),j=u.useMemo(()=>ia(t),[t]),[ee,ue]=u.useState((s==null?void 0:s.targetTokenId)??((_t=j[0])==null?void 0:_t.tokenId)??0),[oe,O]=u.useState(null),[I,z]=u.useState(null),[Y,q]=u.useState(null),[$,re]=u.useState([]),[E,Q]=u.useState(((Xt=n==null?void 0:n.intervention)==null?void 0:Xt.mode)==="sae_feature"?n:null),U=u.useCallback((X,Me)=>{Q(X),a(X,Me)},[a]),de=ts(U),ae=u.useCallback(X=>{re(X.candidates)},[]),ce=au(ae),P=de.submitting||((oa=de.job)==null?void 0:oa.status)==="idle"||((ht=de.job)==null?void 0:ht.status)==="loading",_e=ce.running,ie=i.find(X=>X.id===x)??i.find(X=>X.layer===12)??i[0],be=$.find(X=>X.featureIndex===N),se=o==null?void 0:o.presets.find(X=>X.id===c),te=t.modelName==="google/gemma-2-9b-it",le=!!(be||s!=null&&s.feature||T),he=Math.min(1e3,Math.max(100,Math.ceil(Math.max(Math.abs(K),(be==null?void 0:be.recommendedDelta)??0)*1.5/50)*50));u.useEffect(()=>{const X=new AbortController;return r([]),_(!1),m(null),Od(t.modelName,X.signal).then(Me=>{r(Me);const rt=Me.find(bt=>{var Rn;return bt.saeId===((Rn=s==null?void 0:s.feature)==null?void 0:Rn.saeId)})??Me.find(bt=>bt.layer===12)??Me[0];w((rt==null?void 0:rt.id)??""),re([]),_(!0)}).catch(Me=>{X.signal.aborted||(m(Me instanceof Error?Me.message:"SAE profiles failed to load."),_(!0))}),()=>X.abort()},[(we=s==null?void 0:s.feature)==null?void 0:we.saeId,t.modelName]),u.useEffect(()=>{const X=new AbortController;return Bd(X.signal).then(l).catch(()=>{X.signal.aborted||l(null)}),()=>X.abort()},[]),u.useEffect(()=>{ie&&N>=ie.width&&A(0)},[N,ie]),u.useEffect(()=>{if(!ie){O(null),q(null);return}const X=new AbortController;O(null),z(null);const Me=window.setTimeout(()=>{Qa({mode:"sae_feature",modelName:t.modelName,promptTokenCount:t.tokens.length,availableLayers:t.layers,layer:ie.layer,component:ie.component,positionStart:Z,positionEnd:C,targetTokenId:ee,saeRelease:ie.release,saeId:ie.saeId,featureIndex:N,saeOperation:S,desiredPrompt:"Enhance selected SAE feature",undesiredPrompt:"Suppress selected SAE feature"},X.signal).then(O).catch(De=>{X.signal.aborted||z(De instanceof Error?De.message:"SAE preflight failed.")})},180);return()=>{window.clearTimeout(Me),X.abort()}},[N,S,C,Z,t.layers,t.modelName,t.tokens.length,ie,ee]),u.useEffect(()=>{if(!ie){q(null);return}const X=new AbortController;q(null);const Me=window.setTimeout(()=>{Vd(t.modelName,ie.layer,N,X.signal).then(q).catch(()=>{X.signal.aborted||q(null)})},180);return()=>{window.clearTimeout(Me),X.abort()}},[N,t.modelName,ie]);function ge(X,Me){const De=Math.max(0,Math.min(t.tokens.length-1,X));D(De),ne(Math.max(De+1,Math.min(t.tokens.length,Me)))}function ve(X){w(X),d("custom"),g([]),re([]),k(!1),ce.reset(),Q(null)}function qe(X){if(d(X),X==="custom"){g([]),k(!1),Q(null);return}const Me=o==null?void 0:o.presets.find(bt=>bt.id===X),De=(Me==null?void 0:Me.features[0])??(Me?{featureIndex:Me.featureIndex,strength:Me.strength,layer:Me.layer}:void 0);if(!Me||!De)return;const rt=i.find(bt=>bt.layer===De.layer);if(!rt){m(`The ${Me.label} mode requires a Gemma-2-9B-it run with an L${De.layer} SAE profile.`);return}w(rt.id),g(Me.features.length>0?Me.features:[De]),A(De.featureIndex),H(De.strength),L("add"),k(!0),re([]),ce.reset(),ge(M,t.tokens.length),Q(null)}function me(){!ie||_e||(re([]),ce.submit({run:t,layer:ie.layer,component:ie.component,saeRelease:ie.release,saeId:ie.saeId,positionStart:W.start,positionEnd:W.end,limit:12}))}function Ie(X){d("custom"),g([]),A(X.featureIndex),q({modelName:t.modelName,layer:(ie==null?void 0:ie.layer)??0,featureIndex:X.featureIndex,label:X.label,source:X.source,url:X.url,positiveTokens:X.positiveTokens,negativeTokens:X.negativeTokens}),L("add"),H(X.recommendedDelta),ge(M,t.tokens.length),Q(null)}function Ce(X){d("custom"),g([]);const Me=(be==null?void 0:be.recommendedDelta)??100;H(Math.max(-1e3,Math.min(1e3,Math.round(Me*X))))}function Ue(X){X==="ablate"&&(d("custom"),g([])),L(X),X==="add"?ge(M,t.tokens.length):be?ge(be.peakTokenIndex,be.peakTokenIndex+1):ge(0,t.tokens.length),Q(null)}function Qe(){if(!(oe!=null&&oe.canSubmit)||P||!ie)return;Q(null);const X={run:t,mode:"sae_feature",desiredPrompt:"Enhance selected SAE feature",undesiredPrompt:"Suppress selected SAE feature",layer:ie.layer,component:ie.component,saeRelease:ie.release,saeId:ie.saeId,featureIndex:N,saeOperation:S,saeFeatures:p.length>0?p:void 0,scale:K,positionStart:Z,positionEnd:C,targetTokenId:ee,seed:0,maxNewTokens:pe,temperature:0};de.submit(X)}return b&&i.length===0?e.jsxs("section",{className:"chat-analysis-workbench chat-feature-workbench","aria-label":"SAE feature intervention workbench",children:[e.jsxs("header",{className:"chat-workbench-heading",children:[e.jsx("span",{children:e.jsx(Be,{size:17})}),e.jsxs("div",{children:[e.jsx("h2",{children:"Gemma Scope SAE"}),e.jsxs("p",{children:["No compatible SAE for ",t.modelName]})]})]}),e.jsxs("p",{className:"chat-sae-empty",children:["Select ",e.jsx("b",{children:"google/gemma-3-270m-it"})," for a new chat run."]})]}):e.jsxs("section",{className:"chat-analysis-workbench chat-feature-workbench","aria-label":"SAE feature intervention workbench",children:[e.jsxs("header",{className:"chat-workbench-heading",children:[e.jsx("span",{children:e.jsx(Be,{size:17})}),e.jsxs("div",{children:[e.jsx("h2",{children:"Gemma Scope SAE"}),e.jsx("p",{children:"Sparse feature intervention · residual stream"})]}),e.jsx(sa,{ready:!!(oe!=null&&oe.canSubmit),pending:_e||!oe&&!I})]}),e.jsxs("section",{className:"chat-sae-discovery","aria-label":"Active SAE features",children:[e.jsxs("header",{children:[e.jsxs("div",{className:"chat-sae-section-title",children:[e.jsx("b",{className:"chat-sae-step",children:"1"}),e.jsxs("div",{children:[e.jsx("strong",{children:"Find an active feature"}),e.jsxs("small",{children:["L",(ie==null?void 0:ie.layer)??"..."," · ",F==="output_boundary"?"output boundary":"user tokens"," T",W.start,"–T",W.end-1]})]})]}),e.jsxs("div",{className:"chat-sae-discovery-tools",children:[o&&e.jsxs("label",{className:"chat-sae-profile chat-sae-neuronpedia-mode",children:[e.jsx("span",{children:"Neuronpedia mode"}),e.jsxs("select",{"aria-label":"Neuronpedia steering mode",value:c,disabled:P||_e||!te||!b||i.length===0,onChange:X=>qe(X.target.value),children:[e.jsx("option",{value:"custom",children:"Custom feature"}),o.presets.map(X=>e.jsx("option",{value:X.id,children:X.label},X.id))]}),!te&&e.jsx("small",{className:"chat-sae-mode-hint",children:"Switch the chat model to Gemma-2-9B-it to enable these modes."})]}),e.jsxs("div",{className:"chat-sae-discovery-scope",role:"group","aria-label":"Feature discovery range",children:[e.jsx("button",{type:"button",className:F==="output_boundary"?"active":"","aria-pressed":F==="output_boundary",disabled:P||_e,onClick:()=>{V("output_boundary"),re([])},children:"Scan output"}),e.jsx("button",{type:"button",className:F==="user_prompt"?"active":"","aria-pressed":F==="user_prompt",disabled:P||_e,onClick:()=>{V("user_prompt"),re([])},children:"Scan user input"})]}),e.jsxs("label",{className:"chat-sae-profile",children:[e.jsx("span",{children:"SAE checkpoint"}),e.jsx("select",{"aria-label":"SAE checkpoint",value:(ie==null?void 0:ie.id)??"",disabled:P||_e||i.length===0,onChange:X=>{d("custom"),ve(X.target.value)},children:i.map(X=>e.jsxs("option",{value:X.id,children:["L",X.layer," · ",X.width>=131072?"131k · canonical":"16k · L0 small"]},X.id))})]}),e.jsxs("button",{type:"button",className:_e?"pending":"",disabled:!ie||P,onClick:_e?()=>void ce.cancel():me,children:[_e?e.jsx(Kt,{size:14}):e.jsx(na,{size:15}),_e?"Cancel scan":$.length>0?"Scan again":"Find active features"]})]})]}),_e&&e.jsxs("div",{className:"chat-sae-discovery-progress",children:[e.jsx("span",{children:e.jsx("i",{style:{width:`${((We=ce.job)==null?void 0:We.progress)??4}%`}})}),e.jsx("small",{children:((Mt=ce.job)==null?void 0:Mt.detail)??"Loading the model and SAE checkpoint..."})]}),ce.error&&e.jsxs("p",{className:"chat-sae-discovery-error",children:[e.jsx(Lt,{size:14}),ce.error.message]}),$.length>0&&e.jsxs(e.Fragment,{children:[e.jsxs("div",{className:"chat-sae-candidates-heading",children:[e.jsxs("strong",{children:[$.length," active features"]}),e.jsx("small",{children:"Select one to configure the intervention"})]}),e.jsx("div",{className:"chat-sae-candidates",role:"radiogroup","aria-label":"SAE feature candidates",children:$.map(X=>e.jsxs("button",{type:"button",role:"radio","aria-checked":(be==null?void 0:be.featureIndex)===X.featureIndex,className:(be==null?void 0:be.featureIndex)===X.featureIndex?"active":"",disabled:P,onClick:()=>Ie(X),children:[e.jsxs("span",{children:[e.jsxs("b",{children:["F",X.featureIndex]}),e.jsxs("em",{children:["peak ",Qu(X.maxActivation)]})]}),e.jsx("strong",{children:X.label}),e.jsxs("small",{children:["T",X.peakTokenIndex," · ",Ze(X.peakTokenText)," · active on ",X.activeTokenCount," token",X.activeTokenCount===1?"":"s"]}),e.jsxs("i",{children:["Suggested ",ct(X.recommendedDelta)]})]},X.featureIndex))})]})]}),e.jsxs("section",{className:`chat-sae-config ${le?"is-ready":"is-waiting"}`,"aria-label":"SAE intervention settings",children:[e.jsxs("header",{className:"chat-sae-config-heading",children:[e.jsxs("div",{className:"chat-sae-section-title",children:[e.jsx("b",{className:"chat-sae-step",children:"2"}),e.jsxs("div",{children:[e.jsx("strong",{children:"Configure intervention"}),e.jsx("small",{children:le?"Choose how strongly to change the selected feature":"Select a feature above to continue"})]})]}),e.jsx("span",{className:le?"ready":"waiting",children:le?"Ready":"Waiting"})]}),!le&&e.jsxs("p",{className:"chat-sae-not-selected",children:["Run ",e.jsx("b",{children:"Find active features"}),", then select a feature card. You can also choose a feature ID in Advanced settings."]}),le&&e.jsxs("div",{className:"chat-feature-selected",children:[e.jsxs("div",{className:"chat-feature-selected-id",children:[e.jsxs("strong",{children:["F",N]}),e.jsxs("span",{children:["L",(ie==null?void 0:ie.layer)??"..."," · resid_post"]}),e.jsx("small",{children:(ie==null?void 0:ie.saeId)??"Loading checkpoint"})]}),e.jsxs("div",{className:"chat-feature-concept",children:[e.jsx("strong",{children:(Y==null?void 0:Y.label)??((Pt=s==null?void 0:s.feature)==null?void 0:Pt.conceptLabel)??"Loading explanation..."}),e.jsxs("small",{children:[(Y==null?void 0:Y.source)==="neuronpedia"||((et=s==null?void 0:s.feature)==null?void 0:et.conceptSource)==="neuronpedia"?"Neuronpedia explanation":"No canonical label is bundled with the SAE checkpoint",((Y==null?void 0:Y.url)??((Zt=s==null?void 0:s.feature)==null?void 0:Zt.conceptUrl))&&e.jsxs(e.Fragment,{children:[" · ",e.jsx("a",{href:Jr((Y==null?void 0:Y.url)??((pt=s==null?void 0:s.feature)==null?void 0:pt.conceptUrl)),target:"_blank",rel:"noreferrer",children:"Open feature card"})]})]}),((Y==null?void 0:Y.positiveTokens.length)??0)>0&&e.jsxs("small",{className:"chat-feature-evidence",children:[e.jsx("b",{children:"Positive"}),Y==null?void 0:Y.positiveTokens.slice(0,6).join(" · ")]}),((Y==null?void 0:Y.negativeTokens.length)??0)>0&&e.jsxs("small",{className:"chat-feature-evidence",children:[e.jsx("b",{children:"Negative"}),Y==null?void 0:Y.negativeTokens.slice(0,6).join(" · ")]})]}),se&&e.jsx("small",{className:"chat-sae-preset-note",children:se.features.map(X=>`L${X.layer} F${X.featureIndex} ${ct(X.strength)}`).join(" · ")})]}),e.jsxs("div",{className:"chat-sae-config-body",children:[le&&e.jsxs("div",{className:"chat-feature-adjustment",children:[e.jsxs("div",{className:"chat-feature-operations",role:"group","aria-label":"SAE feature operation",children:[e.jsx("button",{type:"button",className:S==="add"?"active":"","aria-pressed":S==="add",disabled:P||!le,onClick:()=>Ue("add"),children:"Add activation"}),e.jsx("button",{type:"button",className:S==="ablate"?"active":"","aria-pressed":S==="ablate",disabled:P||!le,onClick:()=>Ue("ablate"),children:"Ablate feature"})]}),e.jsxs("label",{className:"chat-feature-strength",children:[e.jsxs("span",{children:["Feature delta ",e.jsx("b",{children:S==="ablate"?"zero":ct(K)})]}),e.jsx("input",{"aria-label":"SAE feature delta",type:"range",min:-he,max:he,step:5,value:K,disabled:P||S==="ablate"||!le,onChange:X=>{d("custom"),g([]),H(Number(X.target.value))}})]}),e.jsx("input",{className:"chat-feature-strength-number","aria-label":"SAE feature delta value",type:"number",min:-1e3,max:1e3,step:5,value:K,disabled:P||S==="ablate"||!le,onChange:X=>{d("custom"),g([]),H(Math.max(-1e3,Math.min(1e3,Number(X.target.value)||0)))}}),e.jsxs("div",{className:"chat-feature-strength-presets",role:"group","aria-label":"SAE strength presets",children:[e.jsx("button",{type:"button",disabled:P||S==="ablate"||!le,onClick:()=>Ce(.5),children:"Subtle"}),e.jsx("button",{type:"button",disabled:P||S==="ablate"||!le,onClick:()=>Ce(1),children:"Suggested"}),e.jsx("button",{type:"button",disabled:P||S==="ablate"||!le,onClick:()=>Ce(1.5),children:"Strong"})]})]}),e.jsxs("div",{className:"chat-feature-generation",children:[e.jsxs("label",{children:[e.jsx("span",{children:"Output tokens"}),e.jsx("input",{"aria-label":"SAE output tokens",type:"number",min:1,max:128,value:pe,disabled:P,onChange:X=>R(Math.max(1,Math.min(128,Number(X.target.value)||1)))})]}),e.jsxs("details",{className:"chat-sae-advanced",open:le,children:[e.jsx("summary",{children:"Advanced settings"}),e.jsxs("div",{className:"chat-feature-advanced-grid",children:[e.jsxs("label",{children:[e.jsx("span",{children:"Feature ID"}),e.jsx("input",{"aria-label":"SAE feature index",type:"number",min:0,max:((ie==null?void 0:ie.width)??1)-1,value:N,disabled:P||_e||!ie,onChange:X=>{d("custom"),g([]),k(!0),A(Math.max(0,Math.min(((ie==null?void 0:ie.width)??1)-1,Number(X.target.value)||0)))}})]}),e.jsxs("label",{children:[e.jsx("span",{children:"Tracked output token"}),e.jsx("select",{"aria-label":"SAE tracked output token",value:ee,disabled:P,onChange:X=>ue(Number(X.target.value)),children:j.map(X=>e.jsxs("option",{value:X.tokenId,children:[Ze(X.tokenText)," · #",X.tokenId]},X.tokenId))})]})]})]})]})]})]}),e.jsxs("div",{className:"chat-token-range",children:[e.jsxs("header",{children:[e.jsxs("span",{children:[e.jsx("b",{className:"chat-sae-step",children:"3"})," Apply to"]}),e.jsxs("div",{children:[e.jsx("button",{className:Z===M&&C===t.tokens.length?"active":"","aria-pressed":Z===M&&C===t.tokens.length,disabled:P||!le,onClick:()=>ge(M,t.tokens.length),children:"Output boundary"}),e.jsx("button",{className:Z===0&&C===t.tokens.length?"active":"","aria-pressed":Z===0&&C===t.tokens.length,disabled:P||!le,onClick:()=>ge(0,t.tokens.length),children:"Entire input"})]}),e.jsx("small",{children:le?`T${Z}–T${C-1}`:"Select a feature first"})]}),le?e.jsx("div",{"aria-label":"SAE intervention token range",children:t.tokens.map(X=>e.jsx("button",{className:X.index>=Z&&X.index<C?"active":"","aria-pressed":X.index>=Z&&X.index<C,disabled:P,onClick:()=>ge(X.index,X.index+1),children:Ze(X.text)},X.index))}):e.jsx("p",{className:"chat-sae-range-hint",children:"The intervention will apply to the output boundary by default."})]}),e.jsx(Tn,{running:P,disabled:!(oe!=null&&oe.canSubmit)||!ie||!le,runLabel:"Run SAE intervention",status:((Re=de.error)==null?void 0:Re.message)??y??I??(oe==null?void 0:oe.reason),progress:(Cn=de.job)==null?void 0:Cn.progress,onRun:Qe,onCancel:()=>void de.cancel(),onReset:de.reset,failed:!!de.error}),(E==null?void 0:E.intervention)&&e.jsx(ns,{experiment:E.intervention})]})}const Ma=["Custom","Reject","Angry","Happy","Emoji","Dog","Music"],ya=su;function Wu({run:t,savedRun:n,suggestionQuery:a,onRunReady:s}){var ce,P,_e,ie,be;const i=(n==null?void 0:n.intervention)??t.intervention,[r,o]=u.useState(!1),[l,c]=u.useState("Custom"),[d,p]=u.useState("Custom samples"),[g,b]=u.useState("Custom samples"),[_,y]=u.useState((i==null?void 0:i.vector.positivePrompts)??[(i==null?void 0:i.vector.desiredPrompt)??"Provide a safe, policy-compliant and helpful response."]),[m,x]=u.useState((i==null?void 0:i.vector.negativePrompts)??[(i==null?void 0:i.vector.undesiredPrompt)??"Provide a response that bypasses safety guidance."]),[w,N]=u.useState((i==null?void 0:i.vector.activationReduce)==="mean"?"mean":"last_token"),A=Hu(t),[T,k]=u.useState((i==null?void 0:i.sourceLayer)??(i==null?void 0:i.layer)??A),[S,L]=u.useState((i==null?void 0:i.injectLayer)??(i==null?void 0:i.layer)??A),[M,F]=u.useState((i==null?void 0:i.component)??"resid_post"),[V,W]=u.useState((i==null?void 0:i.scale)??1),[K,H]=u.useState(128),Z=u.useMemo(()=>ia(t),[t]),[D,C]=u.useState((i==null?void 0:i.targetTokenId)??((ce=Z[0])==null?void 0:ce.tokenId)??0),[ne,pe]=u.useState(null),[R,j]=u.useState(null),[ee,ue]=u.useState(n!=null&&n.intervention?n:i?t:null),oe=u.useMemo(()=>_.map(se=>se.trim()).filter(Boolean),[_]),O=u.useMemo(()=>m.map(se=>se.trim()).filter(Boolean),[m]),I=u.useCallback((se,te)=>{ue(se),s(se,te)},[s]),z=ts(I),Y=z.submitting||((P=z.job)==null?void 0:P.status)==="idle"||((_e=z.job)==null?void 0:_e.status)==="loading";u.useEffect(()=>{const se=new AbortController;if(pe(null),j(null),oe.length===0||O.length===0)return j("Add at least one non-empty sample to each direction."),()=>se.abort();const te=window.setTimeout(()=>{Qa({modelName:t.modelName,promptTokenCount:t.tokens.length,availableLayers:t.layers,layer:S,sourceLayer:T,injectLayer:S,component:M,positionStart:0,positionEnd:t.tokens.length,targetTokenId:D,positivePrompts:oe,negativePrompts:O,activationReduce:w},se.signal).then(pe).catch(le=>{se.signal.aborted||j(le instanceof Error?le.message:"Steering preflight failed.")})},220);return()=>{window.clearTimeout(te),se.abort()}},[w,M,S,O,oe,t.layers,t.modelName,t.tokens.length,T,D]);const q=!!(ne!=null&&ne.canSubmit&&!Y);function $(se){if(c(se),se==="Custom"){p("Custom samples"),b("Custom samples");return}y([...ya[se].positive]),x([...ya[se].negative]),p(`${se} positive batch`),b(`${se} negative batch`)}function re(se,te){if(se==="positive"?p(te):b(te),te==="Custom samples")return;const le=Ma.find(ge=>te.startsWith(`${ge} `));if(!le||le==="Custom")return;const he=[...ya[le][se]];se==="positive"?y(he):x(he)}function E(se,te){const le=he=>he.length>0?[te,...he.slice(1)]:[te];c("Custom"),se==="positive"?(p("Custom samples"),y(le)):(b("Custom samples"),x(le))}function Q(se){E(se.direction==="toward"?"positive":"negative",se.text);const te=cu(se);te&&E(te.direction==="toward"?"positive":"negative",te.text)}function U(){q&&(ue(null),z.submit({run:t,desiredPrompt:oe[0],undesiredPrompt:O[0],positivePrompts:oe,negativePrompts:O,activationReduce:w,layer:S,sourceLayer:T,injectLayer:S,component:M,scale:V,positionStart:0,positionEnd:t.tokens.length,targetTokenId:D,seed:0,maxNewTokens:K,temperature:0}))}const de=e.jsxs("label",{className:"chat-steering-concept",children:[e.jsx("span",{children:"Steering concept"}),e.jsx("select",{"aria-label":"Steering concept",value:l,disabled:Y,onChange:se=>$(se.target.value),children:Ma.map(se=>e.jsx("option",{value:se,children:se},se))})]}),ae=e.jsxs("button",{type:"button",className:"chat-steering-advanced-toggle","aria-expanded":r,onClick:()=>o(se=>!se),children:[e.jsx($t,{size:16}),r?"Hide advanced settings":"Advanced settings",r?e.jsx(Ji,{size:15}):e.jsx(Xn,{size:15})]});return e.jsxs("section",{className:`chat-analysis-workbench chat-steering-workbench ${r?"is-expanded":"is-compact"}`,"aria-label":"Steering workbench",children:[r?e.jsxs(e.Fragment,{children:[e.jsxs("div",{className:"chat-steering-expanded-top",children:[de,ae]}),e.jsxs("div",{className:"chat-steering-references",children:[e.jsx(Ii,{direction:"positive",prompts:_,preset:d,running:Y,suggestionQuery:a,onPreset:re,onSelectPreset:Q,onChange:y}),e.jsx(Ii,{direction:"negative",prompts:m,preset:g,running:Y,suggestionQuery:a,onPreset:re,onSelectPreset:Q,onChange:x})]}),e.jsxs("div",{className:"chat-steering-controls",children:[e.jsxs("label",{children:[e.jsx("span",{children:"Sample activation"}),e.jsxs("select",{"aria-label":"Steering sample activation",value:w,disabled:Y,onChange:se=>N(se.target.value),children:[e.jsx("option",{value:"last_token",children:"Last token"}),e.jsx("option",{value:"mean",children:"Token average"})]})]}),e.jsxs("label",{children:[e.jsx("span",{children:"Source layer"}),e.jsx("select",{"aria-label":"Steering source layer",value:T,disabled:Y,onChange:se=>k(Number(se.target.value)),children:t.layers.map(se=>e.jsxs("option",{value:se,children:["L",se]},se))})]}),e.jsxs("label",{children:[e.jsx("span",{children:"Inject layer"}),e.jsx("select",{"aria-label":"Steering inject layer",value:S,disabled:Y,onChange:se=>L(Number(se.target.value)),children:t.layers.map(se=>e.jsxs("option",{value:se,children:["L",se]},se))})]}),e.jsxs("label",{children:[e.jsx("span",{children:"Component"}),e.jsxs("select",{"aria-label":"Steering activation site",value:M,disabled:Y,onChange:se=>F(se.target.value),children:[e.jsx("option",{value:"resid_post",children:"Residual stream"}),e.jsx("option",{value:"attn_out",children:"Attention output"}),e.jsx("option",{value:"mlp_out",children:"MLP output"})]})]}),e.jsxs("label",{children:[e.jsx("span",{children:"Objective"}),e.jsx("select",{"aria-label":"Steering diagnostic token",value:D,disabled:Y,onChange:se=>C(Number(se.target.value)),children:Z.map(se=>e.jsxs("option",{value:se.tokenId,children:[Ze(se.tokenText)," · #",se.tokenId]},se.tokenId))})]}),e.jsxs("label",{className:"chat-steering-strength",children:[e.jsxs("span",{children:["Strength ",e.jsx("b",{children:V.toFixed(1)})]}),e.jsx("input",{"aria-label":"Steering strength",type:"range",min:0,max:2.5,step:.1,value:V,disabled:Y,onChange:se=>W(Number(se.target.value))})]}),e.jsxs("label",{children:[e.jsx("span",{children:"Output tokens"}),e.jsx("input",{"aria-label":"Steering output tokens",type:"number",min:1,max:128,step:1,value:K,disabled:Y,onChange:se=>H(Math.max(1,Math.min(128,Number(se.target.value)||1)))})]})]})]}):e.jsxs("div",{className:"chat-steering-quick-controls",children:[de,e.jsxs("label",{className:"chat-steering-strength",children:[e.jsxs("span",{children:["Strength ",e.jsx("b",{children:V.toFixed(1)})]}),e.jsx("input",{"aria-label":"Steering strength",type:"range",min:0,max:2.5,step:.1,value:V,disabled:Y,onChange:se=>W(Number(se.target.value))})]}),ae]}),e.jsx(Tn,{running:Y,disabled:!q,runLabel:"Run steering",status:((ie=z.error)==null?void 0:ie.message)??R??(ne==null?void 0:ne.reason)??"Checking steering inputs...",progress:(be=z.job)==null?void 0:be.progress,onRun:U,onCancel:()=>void z.cancel(),onReset:z.reset,failed:!!z.error}),(ee==null?void 0:ee.intervention)&&e.jsx(ns,{experiment:ee.intervention})]})}function Ii({direction:t,prompts:n,preset:a,running:s,suggestionQuery:i,onPreset:r,onSelectPreset:o,onChange:l}){const c=t==="positive"?"Steer toward":"Steer away from",d=(g,b)=>l(n.map((_,y)=>y===g?b:_)),p=g=>{n.length!==1&&l(n.filter((b,_)=>_!==g))};return e.jsxs("section",{className:"chat-steering-samples",children:[e.jsxs("header",{children:[e.jsxs("strong",{children:[c," samples"]}),e.jsx("span",{children:n.length})]}),e.jsxs("label",{className:"chat-steering-preset",children:[e.jsx("span",{children:"Sample preset"}),e.jsxs("select",{"aria-label":`${c} sample preset`,value:a,disabled:s,onChange:g=>r(t,g.target.value),children:[e.jsx("option",{value:"Custom samples",children:"Custom samples"}),Ma.filter(g=>g!=="Custom").map(g=>e.jsxs("option",{value:`${g} ${t} batch`,children:[g," ",t," batch"]},g))]})]}),e.jsxs("div",{className:"chat-steering-sample-list",children:[e.jsx(Ru,{ariaLabel:t==="positive"?"Steering desired behavior":"Steering undesired behavior",label:c,direction:t==="positive"?"toward":"away",contextQuery:i,value:n[0]??"",disabled:s,onChange:g=>d(0,g),onSelectPreset:o}),n.slice(1).map((g,b)=>{const _=b+1;return e.jsxs("label",{children:[e.jsxs("span",{children:["Sample ",_+1]}),e.jsxs("div",{children:[e.jsx("textarea",{"aria-label":`${c} sample ${_+1}`,value:g,disabled:s,onChange:y=>d(_,y.target.value)}),e.jsx("button",{type:"button","aria-label":`Remove ${c.toLowerCase()} sample ${_+1}`,disabled:s||n.length===1,onClick:()=>p(_),children:e.jsx(In,{size:15})})]})]},_)})]}),e.jsxs("button",{type:"button",className:"chat-steering-add-sample",disabled:s||n.length>=64,onClick:()=>l([...n,""]),children:[e.jsx(Qi,{size:15}),"Add sample"]})]})}function zu({run:t,savedRun:n,onRunReady:a}){var L,M,F,V,W;const[s,i]=u.useState(()=>Ou(t)),[r,o]=u.useState(()=>Bu(n??t)??0),[l,c]=u.useState([]),[d,p]=u.useState("pad_token"),[g,b]=u.useState(32),_=n??t,y=_.attributionMethods.find(K=>K.id==="integrated_gradients"&&K.available),[m,x]=u.useState(y?_:null),w=u.useCallback((K,H)=>{x(K),a(K,H)},[a]),N=tu(w),A=N.submitting||((L=N.job)==null?void 0:L.status)==="idle"||((M=N.job)==null?void 0:M.status)==="loading",T=u.useCallback(K=>c(K),[]);function k(){!s.trim()||A||(x(null),N.submit({run:t,response:s,objective:"response_token_logit",targetResponseIndex:r,baseline:d,nSteps:g}))}const S=m==null?void 0:m.attributionMethods.find(K=>K.id==="integrated_gradients"&&K.available);return e.jsxs("section",{className:"chat-analysis-workbench","aria-label":"Input attribution workbench",children:[e.jsxs("header",{className:"chat-workbench-heading",children:[e.jsx("span",{children:e.jsx(na,{size:17})}),e.jsxs("div",{children:[e.jsx("h2",{children:"Input attribution"}),e.jsx("p",{children:"Show which input tokens support or suppress the selected output token"})]}),e.jsx(sa,{ready:!!S,pending:!1})]}),e.jsxs("label",{className:"chat-attribution-response",children:[e.jsx("span",{children:"Model response"}),e.jsx("textarea",{"aria-label":"Attribution response",rows:3,value:s,disabled:A,placeholder:"Response containing the target token",onChange:K=>i(K.target.value)})]}),e.jsxs("div",{className:"chat-attribution-controls",children:[e.jsx(Lu,{modelName:t.modelName,response:s,selectedIndex:r,disabled:A,onSelect:o,onTokensChange:T}),e.jsxs("fieldset",{children:[e.jsx("legend",{children:"Baseline"}),e.jsx("button",{type:"button",className:d==="pad_token"?"active":"","aria-pressed":d==="pad_token",disabled:A,onClick:()=>p("pad_token"),children:"Pad token"}),e.jsx("button",{type:"button",className:d==="zero_token_id"?"active":"","aria-pressed":d==="zero_token_id",disabled:A,onClick:()=>p("zero_token_id"),children:"Token ID 0"})]}),e.jsxs("label",{children:[e.jsx("span",{children:"Integration steps"}),e.jsx("select",{"aria-label":"Attribution integration steps",value:g,disabled:A,onChange:K=>b(Number(K.target.value)),children:[8,16,32,64].map(K=>e.jsx("option",{value:K,children:K},K))})]})]}),e.jsx(Tn,{running:A,disabled:!s.trim()||l.length===0||A,runLabel:"Run attribution",status:((F=N.error)==null?void 0:F.message)??((V=N.job)==null?void 0:V.detail)??(s.trim()?l.length===0?"Tokenizing response...":void 0:"Enter a model response."),progress:(W=N.job)==null?void 0:W.progress,onRun:k,onCancel:()=>void N.cancel(),onReset:N.reset,failed:!!N.error}),S&&e.jsx(Du,{method:S,run:m,targetIndex:r,responseTokens:l})]})}function Tn({running:t,disabled:n,runLabel:a,status:s,progress:i,failed:r,onRun:o,onCancel:l,onReset:c}){return e.jsxs("div",{className:"chat-workbench-actions",children:[e.jsxs("div",{className:r?"failed":t?"running":"","aria-live":"polite",children:[r?e.jsx(Lt,{size:15}):t?e.jsx(Vt,{size:15}):e.jsx(ot,{size:15}),e.jsx("span",{children:s??(n?"Complete the required fields.":"Ready to run.")}),t&&e.jsxs("small",{children:[i??0,"%"]})]}),r&&e.jsx("button",{className:"icon-action","aria-label":"Reset analysis job",title:"Reset",onClick:c,children:e.jsx(Jn,{size:15})}),e.jsxs("button",{className:"chat-workbench-run",disabled:n&&!t,onClick:t?l:o,children:[t?e.jsx(Kt,{size:14}):e.jsx(Zn,{size:14}),t?"Cancel":a]})]})}function sa({ready:t,pending:n}){return e.jsxs("span",{className:`chat-workbench-status ${t?"ready":n?"pending":"idle"}`,children:[e.jsx("i",{}),t?"ready":n?"checking":"not run"]})}function ns({experiment:t}){var c,d,p,g,b;const n=t.mode==="neuron"||t.mode==="sae_feature",a=t.mode==="sae_feature",s=!n&&t.vector.normalized,i=t.sourceLayer!==void 0||t.injectLayer!==void 0?`source L${t.sourceLayer??t.layer} → inject L${t.injectLayer??t.layer}`:`L${t.layer}`,r=t.deltas.maxAbsLogit,o=t.deltas.firstDivergenceIndex,l=t.vector.relativeStrength;return e.jsxs("section",{className:"chat-steering-result","aria-label":"Steering comparison",children:[e.jsxs("header",{children:[e.jsxs("div",{children:[n?e.jsx(Be,{size:16}):e.jsx(yt,{size:16}),e.jsx("strong",{children:a?"SAE feature comparison":n?"Neuron intervention comparison":"Steering generation comparison"})]}),e.jsxs("span",{children:[n&&t.feature?`${t.feature.id} · ${t.feature.operation}`:`${i} · ${t.component}`,a&&((c=t.feature)==null?void 0:c.operation)==="ablate"?"":` · factor ${ct(t.scale)}`]})]}),a&&t.feature&&e.jsxs("div",{className:"chat-sae-concept-result",children:[e.jsx("span",{children:"Concept label"}),e.jsx("strong",{children:t.feature.conceptLabel??t.feature.label}),e.jsxs("small",{children:[t.feature.conceptSource==="neuronpedia"?"External explanation metadata; the SAE weights only contain the numeric feature index.":"No canonical explanation was bundled; this is an index-only feature.",t.feature.conceptUrl&&e.jsxs(e.Fragment,{children:[" ",e.jsx("a",{href:Jr(t.feature.conceptUrl),target:"_blank",rel:"noreferrer",children:"Open feature card"})]})]}),t.feature.operation==="add"&&t.feature.baselineActivation<=0&&e.jsx("small",{children:"Feature inactive in the selected prompt range; this run injects its decoder direction explicitly."}),((((d=t.feature.positiveTokens)==null?void 0:d.length)??0)>0||(((p=t.feature.negativeTokens)==null?void 0:p.length)??0)>0)&&e.jsxs("div",{className:"chat-sae-concept-evidence",children:[(g=t.feature.positiveTokens)!=null&&g.length?e.jsxs("span",{children:[e.jsx("b",{children:"Positive logits"}),t.feature.positiveTokens.slice(0,5).join(" · ")]}):null,(b=t.feature.negativeTokens)!=null&&b.length?e.jsxs("span",{children:[e.jsx("b",{children:"Negative logits"}),t.feature.negativeTokens.slice(0,5).join(" · ")]}):null]})]}),e.jsxs("div",{className:"chat-steering-output",children:[e.jsxs("article",{className:"is-original",children:[e.jsx("span",{children:"Original"}),e.jsx("p",{children:t.original.text||"No continuation"}),e.jsxs("small",{children:["Diagnostic token logit ",t.original.targetLogit.toFixed(3)]})]}),e.jsxs("div",{className:"chat-steering-transition",title:"Diagnostic token logit delta",children:[e.jsx(ea,{size:20}),e.jsx("span",{children:ct(t.deltas.targetLogit)})]}),e.jsxs("article",{className:"is-steered",children:[e.jsx("span",{children:"Steered"}),e.jsx("p",{children:t.steered.text||"No continuation"}),e.jsxs("small",{children:["Diagnostic token logit ",t.steered.targetLogit.toFixed(3)]})]})]}),e.jsx("p",{className:`chat-steering-verdict ${t.deltas.generationChanged?"changed":"unchanged"}`,children:s?"This saved result used legacy unit-vector steering. Run steering again to use the calibrated contrastive algorithm.":t.deltas.generationChanged?`Generation diverged at output token ${o??0}.`:r&&r>0?"The intervention changed next-token logits, but greedy decoding kept the same tokens. Choose a feature or layer with a closer top-1 margin, or use sampling to expose the changed distribution.":"No measurable intervention effect was recorded. Check the selected layer and activation site."}),e.jsxs("footer",{children:[e.jsxs("span",{children:[e.jsx("b",{children:ct(t.deltas.targetLogit)})," diagnostic logit"]}),e.jsxs("span",{children:[e.jsx("b",{children:t.deltas.tokenEditDistance})," token edits"]}),r!==void 0&&e.jsxs("span",{children:[e.jsx("b",{children:r.toFixed(3)})," max vocabulary change"]}),l!==void 0&&e.jsxs("span",{children:[e.jsxs("b",{children:[(l*100).toFixed(1),"%"]})," relative injection"]})]})]})}function Du({method:t,run:n,targetIndex:a,responseTokens:s}){var b,_;const i=((b=t.rows[t.rows.length-1])==null?void 0:b.values)??[],r=Math.max(1e-8,...i.map(y=>Math.abs(y))),o=n.tokens.map((y,m)=>({token:y,value:i[m]??0})).filter(y=>y.value>0).sort((y,m)=>m.value-y.value).slice(0,5),l=n.tokens.map((y,m)=>({token:y,value:i[m]??0})).filter(y=>y.value<0).sort((y,m)=>y.value-m.value).slice(0,5),c=(_=n.metadata)==null?void 0:_.attributionJobs,d=Array.isArray(c)?c[c.length-1]:void 0,p=a!==void 0?s[a]:void 0,g=d&&typeof d=="object"&&"targetTokenText"in d?String(d.targetTokenText):p==null?void 0:p.text;return e.jsxs("section",{className:"chat-attribution-result","aria-label":"Input attribution result",children:[e.jsxs("header",{children:[e.jsxs("div",{children:[e.jsx(na,{size:16}),e.jsx("strong",{children:"Token contributions"})]}),(p||g)&&e.jsxs("span",{className:"chat-attribution-target",title:"Selected target token",children:["Target ",e.jsxs("b",{children:["T",a??0]})," · ",Ze(g??"")]}),e.jsxs("span",{children:[e.jsx("i",{className:"positive"})," supports target ",e.jsx("i",{className:"negative"})," suppresses target"]})]}),e.jsx("div",{className:"chat-attribution-tokens",children:n.tokens.map((y,m)=>{const x=i[m]??0,w=Math.abs(x)/r;return e.jsx("span",{className:x<0?"negative":"positive",style:{"--strength":w},title:`T${y.index} · ${x.toFixed(6)}`,children:Ze(y.text)},y.index)})}),e.jsxs("footer",{className:"chat-attribution-rankings",children:[e.jsxs("section",{"aria-label":"Positive attribution tokens",children:[e.jsxs("header",{children:[e.jsx("i",{className:"positive"}),e.jsx("strong",{children:"Supports target"})]}),o.length?o.map(({token:y,value:m})=>e.jsxs("span",{children:[e.jsxs("small",{children:["T",y.index]}),e.jsx("b",{children:Ze(y.text)}),e.jsx("em",{className:"positive-value",children:ct(m)})]},y.index)):e.jsx("p",{children:"No positive token contribution."})]}),e.jsxs("section",{"aria-label":"Negative attribution tokens",children:[e.jsxs("header",{children:[e.jsx("i",{className:"negative"}),e.jsx("strong",{children:"Suppresses target"})]}),l.length?l.map(({token:y,value:m})=>e.jsxs("span",{children:[e.jsxs("small",{children:["T",y.index]}),e.jsx("b",{children:Ze(y.text)}),e.jsx("em",{className:"negative-value",children:ct(m)})]},y.index)):e.jsx("p",{children:"No negative token contribution."})]})]})]})}function Yu({experiment:t}){const n=[...t.cells].sort((r,o)=>Wn(o)-Wn(r))[0],[a,s]=u.useState(n),i=Math.max(1e-8,...t.cells.map(Wn));return e.jsxs("section",{className:"chat-patching-result","aria-label":"Activation patching result",children:[e.jsxs("header",{children:[e.jsxs("div",{children:[e.jsx(yt,{size:16}),e.jsx("strong",{children:"Causal recovery"})]}),e.jsxs("span",{children:[t.component==="z"?`L${t.layers[0]}H${t.head} · `:"","Target ",Ze(t.targetTokenText)," · #",t.targetTokenId]})]}),e.jsxs("div",{className:"chat-patching-baselines",children:[e.jsxs("span",{className:"clean",children:[e.jsx("small",{children:"Clean logit"}),e.jsx("b",{children:t.cleanScore.toFixed(3)})]}),e.jsxs("span",{className:"corrupt",children:[e.jsx("small",{children:"Corrupt logit"}),e.jsx("b",{children:t.corruptedScore.toFixed(3)})]}),e.jsxs("span",{children:[e.jsx("small",{children:"Clean-corrupt gap"}),e.jsx("b",{children:ct(t.denominator)})]})]}),e.jsx("div",{className:"chat-patching-matrix",role:"region","aria-label":"Patching recovery matrix",children:e.jsxs("table",{children:[e.jsx("thead",{children:e.jsxs("tr",{children:[e.jsx("th",{children:"Layer"}),t.positions.map(r=>{var o;return e.jsxs("th",{title:(o=t.corruptedTokens[r])==null?void 0:o.text,children:["T",r]},r)})]})}),e.jsx("tbody",{children:t.layers.map(r=>e.jsxs("tr",{children:[e.jsxs("th",{children:["L",r]}),t.positions.map(o=>{const l=t.cells.find(g=>g.layer===r&&g.tokenIndex===o),c=l?l.recoveryPercentage:null,d=l?Wn(l)/i:0,p=(a==null?void 0:a.layer)===r&&(a==null?void 0:a.tokenIndex)===o;return e.jsx("td",{children:l?e.jsx("button",{type:"button",className:`${(c??l.causalEffect)<0?"negative":"positive"} ${p?"active":""}`,style:{"--strength":d},"aria-label":`Layer ${r}, token ${o}, ${c===null?`${ct(l.causalEffect)} causal effect`:`${c.toFixed(1)} percent recovery`}`,"aria-pressed":p,onClick:()=>s(l),children:c===null?ct(l.causalEffect):`${c.toFixed(1)}%`}):"—"},o)})]},r))})]})}),a&&e.jsxs("footer",{"aria-label":"Selected patch result",children:[e.jsxs("strong",{children:["L",a.layer,t.component==="z"?`H${t.head}`:""," · T",a.tokenIndex]}),e.jsxs("span",{children:["Patched logit ",e.jsx("b",{children:a.patchedScore.toFixed(3)})]}),e.jsxs("span",{children:["Causal effect ",e.jsx("b",{children:ct(a.causalEffect)})]}),e.jsxs("span",{children:["Recovery ",e.jsx("b",{children:a.recoveryPercentage===null?"n/a":`${a.recoveryPercentage.toFixed(1)}%`})]})]})]})}function qu(t){return t.layers[Math.max(0,Math.floor(t.layers.length*.7)-1)]??t.layers[0]??0}function Hu(t){const n=Math.floor(2*t.layers.length/4)+1;return t.layers.includes(n)?n:qu(t)}function Fu(t){return t.length<=3?t:[...new Set([.25,.5,.75].map(n=>t[Math.min(t.length-1,Math.floor(t.length*n))]))]}function Uu(t){return t==="resid_post"?"Residual":t==="attn_out"?"Attention output":t==="z"?"Attention head":"MLP"}function Ku(t,n){var i;const a=(i=t.metadata)==null?void 0:i.attentionHeadCoverage;if(a&&typeof a=="object"&&!Array.isArray(a)){const r=a.availableByLayer;if(r&&typeof r=="object"&&!Array.isArray(r)){const o=Number(r[String(n)]);if(Number.isInteger(o)&&o>0)return o}}const s=t.attentionHeads.filter(r=>r.layer===n&&!r.aggregation&&!r.difference&&!r.rollout).map(r=>r.head);return s.length>0?Math.max(...s)+1:1}function Wn(t){return Math.abs(t.recoveryPercentage??t.causalEffect)}function ia(t){var r;const n=t.layers[t.layers.length-1],a=(r=t.tokens[t.tokens.length-1])==null?void 0:r.index,s=t.logitLens.find(o=>o.layer===n&&o.tokenIndex===a)??t.logitLens[t.logitLens.length-1],i=[...s?[{tokenId:s.targetTokenId,tokenText:s.targetTokenText}]:[],...((s==null?void 0:s.topPredictions)??[]).map(o=>({tokenId:o.tokenId,tokenText:o.tokenText}))];return[...new Map(i.map(o=>[o.tokenId,o])).values()].slice(0,12)}function Ou(t){return Ga(t)}function Bu(t){var i;const n=(i=t.metadata)==null?void 0:i.attributionJobs;if(!Array.isArray(n))return;const a=n[n.length-1];if(!a||typeof a!="object")return;const s=a.targetResponseIndex;return typeof s=="number"&&Number.isInteger(s)&&s>=0?s:void 0}function Vu(t){const n=t.tokens;if(n.length===0)return{start:0,end:0};let a=-1;for(let r=n.length-1;r>=0;r-=1)if(n[r].text.trim().toLowerCase()==="user"){a=r;break}if(a<0)return{start:0,end:n.length};let s=a+1;for(;s<n.length&&n[s].text.trim()==="";)s+=1;let i=n.length;for(let r=s;r<n.length;r+=1){const o=n[r].text.trim().toLowerCase();if(o==="<end_of_turn>"||o==="<|im_end|>"||o==="assistant"||o==="model"){i=r;break}}for(;i>s&&n[i-1].text.trim()==="";)i-=1;return s<i?{start:s,end:i}:{start:0,end:n.length}}function Ze(t){return t.trim()||"space"}function Qu(t){return Math.abs(t)>=100?t.toFixed(0):Math.abs(t)>=10?t.toFixed(1):t.toFixed(2)}function Jr(t){return(t==null?void 0:t.replace("/api/feature/","/"))??""}function ct(t){return`${t>0?"+":""}${Math.abs(t)<.001&&t!==0?t.toExponential(2):t.toFixed(3)}`}function Ju({turn:t,remoteSummary:n,analysisRuns:a,active:s,showAnalysisControls:i,analysisOpen:r,onRetry:o,onCancel:l,onToggleAnalysis:c,onRunReady:d}){const p=t.run&&r?a.find(g=>{var m,x,w,N,A,T;const b=(m=g.metadata)==null?void 0:m.parentRun;if(!b||typeof b!="object"||Array.isArray(b))return!1;const _=b;return _.runId===((x=t.run)==null?void 0:x.runId)&&_.sampleId===((w=t.run)==null?void 0:w.sampleId)?r==="steering"?((N=g.intervention)==null?void 0:N.mode)==="direction":r==="patching"?!!g.patching:r==="attribution"?g.attributionMethods.some(k=>k.id==="integrated_gradients"&&k.available):r==="neuron"?((A=g.intervention)==null?void 0:A.mode)==="neuron":r==="feature"?((T=g.intervention)==null?void 0:T.mode)==="sae_feature":r==="explanation"?g.nla.some(k=>k.status==="available")||g.jLens.length>0:!1:!1}):void 0;return e.jsxs("article",{className:"chat-turn-card","aria-label":"Conversation turn",children:[e.jsx("div",{className:"chat-user-message",children:t.prompt}),e.jsxs("div",{className:"chat-assistant-message",children:[e.jsx("span",{className:"chat-assistant-mark",children:e.jsx(Bt,{size:20})}),e.jsx("div",{children:t.run?e.jsxs(e.Fragment,{children:[e.jsx("p",{children:Ga(t.run)||"The model run is complete and its internal activations are ready to inspect."}),e.jsxs("span",{className:"chat-run-ready",children:[e.jsx(ot,{size:14})," Activation cache ready"]})]}):t.status==="error"?e.jsxs(e.Fragment,{children:[e.jsx("p",{children:t.errorMessage??"The analysis job failed."}),e.jsx("button",{onClick:o,children:"Retry"})]}):e.jsxs("div",{className:"chat-job-progress",children:[e.jsxs("span",{children:[e.jsx(Vt,{size:16})," ",t.jobDetail||"Running the analysis..."]}),e.jsx("i",{children:e.jsx("b",{style:{width:`${s?t.jobProgress??2:4}%`}})}),e.jsx("small",{children:s?`${t.jobStage||"in progress"} · ${t.jobProgress??0}%`:"queued"}),s&&e.jsx("button",{"aria-label":"Cancel analysis",onClick:l,children:e.jsx(Gi,{size:16})}),t.status==="cancelled"&&e.jsx("button",{"aria-label":"Retry analysis",title:"Retry analysis",onClick:o,children:e.jsx(vn,{size:15})})]})})]}),t.run&&i&&e.jsxs(e.Fragment,{children:[e.jsxs("div",{className:"chat-turn-explore-bar","aria-label":"Explore this run",children:[e.jsxs("button",{type:"button",className:r==="neuron"?"active":"","aria-pressed":r==="neuron",onClick:()=>c("neuron"),children:[e.jsx(Be,{size:16})," Neuron"]}),e.jsxs("button",{type:"button",className:r==="feature"?"active":"","aria-pressed":r==="feature",onClick:()=>c("feature"),children:[e.jsx(Be,{size:16})," SAE"]}),e.jsxs("button",{type:"button",className:r==="patching"?"active":"","aria-pressed":r==="patching",onClick:()=>c("patching"),children:[e.jsx(yt,{size:16})," Patch"]}),e.jsxs("button",{type:"button",className:r==="steering"?"active":"","aria-pressed":r==="steering",onClick:()=>c("steering"),children:[e.jsx($t,{size:16})," Steer"]}),e.jsxs("button",{type:"button",className:r==="attribution"?"active":"","aria-pressed":r==="attribution",onClick:()=>c("attribution"),children:[e.jsx(na,{size:16})," Attribute"]}),e.jsxs("button",{type:"button",className:r==="explanation"?"active":"","aria-pressed":r==="explanation",onClick:()=>c("explanation"),children:[e.jsx(dt,{size:16})," Explain"]}),e.jsxs("button",{type:"button",className:r==="attention"?"active":"","aria-pressed":r==="attention",onClick:()=>c("attention"),children:[e.jsx(Ot,{size:16})," Attention"]})]}),r&&e.jsx("div",{className:"chat-turn-analysis",children:e.jsx($u,{mode:r,run:t.run,remoteSummary:n,savedRun:p,suggestionQuery:t.prompt,onRunReady:d},`${t.run.runId}:${t.run.sampleId}:${r}`)})]})]})}function Gu({turns:t,records:n,analysisRuns:a,activeTurnId:s,analysisOpen:i,onRetry:r,onCancel:o,onToggleAnalysis:l,onRunReady:c}){const d=u.useRef(null);return u.useEffect(()=>{var p;(p=d.current)==null||p.scrollIntoView({block:"end",behavior:"smooth"})},[t.length]),e.jsxs("div",{className:"chat-turn-list","aria-label":"Conversation turns",children:[t.map((p,g)=>{var b;return e.jsx(Ju,{turn:p,remoteSummary:(b=n.find(_=>_.key===p.id))==null?void 0:b.remoteSummary,analysisRuns:a,active:p.id===s,showAnalysisControls:g===t.length-1,analysisOpen:(i==null?void 0:i.turnId)===p.id?i.mode:null,onRetry:()=>r(p.id),onCancel:()=>o(p.id),onToggleAnalysis:_=>l(p.id,_),onRunReady:c},p.id)}),e.jsx("div",{ref:d})]})}const Gr="Qwen/Qwen2.5-7B-Instruct",Si=[Gr,"sshleifer/tiny-gpt2","google/gemma-3-12b-it","google/gemma-3-270m-it","google/gemma-2-9b-it"],Xu=128,Zu=512,Xr="safelens.localExplorer.hiddenWork.v1";function em({records:t,activeRecord:n,remoteState:a,onOpenDatasetTest:s,onSelectConversation:i,onRunReady:r,onRemoveRuns:o}){const[l,c]=u.useState(""),[d,p]=u.useState(n.key),[g,b]=u.useState(Si),[_,y]=u.useState(Gr),[m,x]=u.useState(Xu),[w,N]=u.useState(Zu),[A,T]=u.useState(null),[k,S]=u.useState(null),[L,M]=u.useState(dm),[F,V]=u.useState(null),[W,K]=u.useState(null),[H,Z]=u.useState(!1),D=u.useMemo(()=>t.filter(q=>!L.has(q.key)),[L,t]),C=u.useMemo(()=>Qc(D),[D]),ne=D.find(q=>q.key===d)??D.find(q=>q.key===n.key)??D[0]??n,pe=u.useRef([]),R=Nc({model:_,maxNewTokens:m,conversationId:A,onConversationStart:T,onRunReady:(q,$,re)=>{const E=pe.current.findIndex(Q=>Q.id===re);r({...q,metadata:{...q.metadata,...A?{conversationId:A}:{},...E>=0?{turnIndex:E}:{}}},$)}});pe.current=R.turns;const j=R.activeTurnId!==null;u.useEffect(()=>{const q=new AbortController;return Rd(q.signal).then($=>{b($.models),y(re=>$.models.includes(re)?re:$.models[0]),N($.maxNewTokens),x(re=>Math.min(re,$.maxNewTokens))}).catch(()=>{b($=>$.length>0?$:Si)}),()=>q.abort()},[]),u.useEffect(()=>{D.some(q=>q.key===d)||p(ne.key)},[ne.key,d,D]),u.useEffect(()=>{!W||n.key!==W||(ue(n),K(null))},[n,W]);function ee(q){return q.turnRecords.filter($=>$.run!==null).map($=>({id:$.key,prompt:Ti($.run),run:$.run,jobId:$.artifactId??null,status:"ready",startedAt:$.importedAt}))}function ue(q){const $=C.find(ae=>ae.records.some(ce=>ce.key===q.key)),re=$?ee($):[{id:q.key,prompt:Ti(q.run),run:q.run,jobId:q.artifactId??null,status:"ready",startedAt:q.importedAt}];R.hydrate(re,($==null?void 0:$.conversationId)??q.key),p(q.key),c(""),S(null);const E=($==null?void 0:$.turnRecords.flatMap(ae=>ae.run?[ae.run]:[]))??[],Q=E[E.length-1]??q.run,U=im(Q);U&&y(U);const de=rm(Q);de&&x(Math.min(de,w)),Z(!1)}function oe(q){const $=q.firstRecord;if($.run){ue($);return}K($.key),p($.key),Z(!1),i($.key)}function O(){R.reset(),T(null),K(null),c(""),S(null),Z(!1)}function I(){const q=l.trim();!q||j||(c(""),S(null),R.submit(q))}function z(q,$){S(re=>(re==null?void 0:re.turnId)===q&&re.mode===$?null:{turnId:q,mode:$})}function Y(q){const $=new Set(q.records.map(de=>de.key));let re=!0;for(;re;){re=!1;for(const de of t){const ae=tm(de);ae&&$.has(ae)&&!$.has(de.key)&&($.add(de.key),re=!0)}}const E=D.find(de=>!$.has(de.key));E&&p(E.key),M(de=>{const ae=new Set(de);for(const ce of $)ae.add(ce);try{window.localStorage.setItem(Xr,JSON.stringify([...ae]))}catch{}return ae});const Q=t.filter(de=>$.has(de.key)).filter(de=>de.sourceType==="local"||de.sourceType==="generated").map(de=>de.key);o(Q),R.turns.some(de=>$.has(de.id))&&(R.reset(),T(null),S(null)),window.history.replaceState(null,"","/")}return e.jsxs("div",{className:`chat-home ${R.turns.length>0?"has-conversation":"is-empty"} ${k?"has-analysis":""}`,children:[e.jsxs("header",{className:"chat-home-header",children:[e.jsxs("a",{className:"chat-home-brand",href:"/","aria-label":"SafeLens home",children:[e.jsx("span",{children:e.jsx(Bt,{size:22})}),e.jsx("strong",{children:"SafeLens"})]}),e.jsx("button",{className:"chat-history-toggle","aria-label":"Open chat history",title:"Chat history",onClick:()=>Z(!0),children:e.jsx(Qo,{size:18})}),e.jsxs("nav",{className:"chat-home-nav","aria-label":"SafeLens modes",children:[e.jsxs("button",{onClick:s,children:[e.jsx(vt,{size:16})," Dataset test"]}),e.jsxs("span",{className:`chat-home-status ${a.status}`,children:[e.jsx("i",{}),a.status==="ready"?"Local workspace":"Local mode"]})]})]}),e.jsxs("div",{className:"chat-home-body",children:[e.jsx(am,{open:H,conversations:C,activeKey:null,onNew:O,onSelect:oe,onDelete:V,onClose:()=>Z(!1)}),e.jsxs("main",{className:"chat-home-main",children:[R.turns.length===0?e.jsx("section",{className:"chat-home-welcome","aria-labelledby":"chat-home-title",children:e.jsxs("div",{children:[e.jsx("span",{children:e.jsx(Ya,{size:19})}),e.jsx("h1",{id:"chat-home-title",children:"What would you like to inspect?"})]})}):e.jsx(Gu,{turns:R.turns,records:D,analysisRuns:D.flatMap(q=>q.run?[q.run]:[]),activeTurnId:R.activeTurnId,analysisOpen:k,onRetry:R.retry,onCancel:R.cancel,onToggleAnalysis:z,onRunReady:r}),e.jsx(nm,{prompt:l,model:_,models:g,maxNewTokens:m,maxNewTokensLimit:w,running:j,onPromptChange:c,onModelChange:y,onMaxNewTokensChange:x,onUseSourcePrompt:()=>{var $;const q=($=ne.run)==null?void 0:$.prompt;q&&c(q)},onSubmit:I})]})]}),F&&e.jsx(sm,{conversation:F,onCancel:()=>V(null),onConfirm:()=>{Y(F),V(null)}})]})}function tm(t){var i,r;const n=(r=(i=t.run)==null?void 0:i.metadata)==null?void 0:r.parentRun;if(!n||typeof n!="object"||Array.isArray(n))return null;const a="runId"in n?n.runId:void 0,s="sampleId"in n?n.sampleId:void 0;return typeof a=="string"&&typeof s=="string"?`${a}::${s}`:null}function nm({prompt:t,model:n,models:a,maxNewTokens:s,maxNewTokensLimit:i,running:r,onPromptChange:o,onModelChange:l,onMaxNewTokensChange:c,onUseSourcePrompt:d,onSubmit:p}){return e.jsxs("section",{className:"chat-composer","aria-label":"Run a SafeLens analysis",children:[e.jsx("textarea",{"aria-label":"Analysis prompt",placeholder:"Ask SafeLens",value:t,maxLength:8e3,onChange:g=>o(g.target.value),onKeyDown:g=>{(g.metaKey||g.ctrlKey)&&g.key==="Enter"&&p()}}),e.jsxs("div",{className:"chat-composer-controls",children:[e.jsx("button",{className:"chat-attach","aria-label":"Use selected run prompt",title:"Use selected run prompt",onClick:d,children:e.jsx(Go,{size:17})}),e.jsxs("label",{children:[e.jsx("span",{children:"Model"}),e.jsx("select",{"aria-label":"Analysis model",value:n,onChange:g=>l(g.target.value),children:a.map(g=>e.jsx("option",{value:g,children:Zr(g)},g))})]}),e.jsxs("label",{className:"chat-token-budget",children:[e.jsx("span",{children:"Max"}),e.jsx("input",{"aria-label":"Maximum new tokens",type:"number",min:1,max:i,step:1,value:s,disabled:r,title:"Maximum new tokens",onChange:g=>c(om(g.target.value,1,i))})]}),e.jsx("button",{className:"chat-run","aria-label":"Run analysis",title:"Run analysis",disabled:!t.trim()||r,onClick:p,children:r?e.jsx(Vt,{size:18}):e.jsx(Xi,{size:18,fill:"currentColor"})})]})]})}function am({open:t,conversations:n,activeKey:a,onNew:s,onSelect:i,onDelete:r,onClose:o}){return e.jsxs(e.Fragment,{children:[e.jsxs("aside",{className:`chat-history ${t?"open":""}`,"aria-label":"Chat history",children:[e.jsxs("header",{children:[e.jsxs("button",{className:"chat-history-new",onClick:s,children:[e.jsx(Jo,{size:17})," New chat"]}),e.jsx("button",{className:"chat-history-close","aria-label":"Close chat history",onClick:o,children:e.jsx(at,{size:17})})]}),e.jsxs("nav",{"aria-label":"Conversation history",children:[e.jsx("span",{children:"Recent"}),n.length?n.map(l=>e.jsxs("div",{className:`chat-history-row ${l.firstRecord.key===a?"active":""}`,children:[e.jsxs("button",{className:"chat-history-open",onClick:()=>i(l),children:[e.jsx("strong",{children:l.title}),e.jsxs("small",{children:[Zr(l.firstRecord.modelName),l.turnCount>1?` · ${l.turnCount} turns`:""]})]}),e.jsx("button",{className:"chat-history-delete","aria-label":`Delete conversation ${l.title}`,title:"Delete conversation",onClick:()=>r(l),children:e.jsx(In,{size:15})})]},l.conversationId)):e.jsx("p",{children:"No conversations yet."})]})]}),t&&e.jsx("button",{className:"chat-history-backdrop","aria-label":"Close chat history",onClick:o})]})}function sm({conversation:t,onCancel:n,onConfirm:a}){return e.jsx("div",{className:"chat-delete-backdrop",role:"presentation",onMouseDown:s=>{s.target===s.currentTarget&&n()},children:e.jsxs("section",{role:"dialog","aria-modal":"true","aria-labelledby":"chat-delete-title",className:"chat-delete-dialog",children:[e.jsxs("header",{children:[e.jsxs("div",{children:[e.jsx("span",{children:"Chat history"}),e.jsx("h2",{id:"chat-delete-title",children:"Delete this conversation?"})]}),e.jsx("button",{"aria-label":"Close remove confirmation",onClick:n,children:e.jsx(at,{size:18})})]}),e.jsxs("p",{children:["This removes ",e.jsx("strong",{children:t.title})," from Chat history. Workspace source files are not modified."]}),e.jsxs("footer",{children:[e.jsx("button",{autoFocus:!0,onClick:n,children:"Cancel"}),e.jsxs("button",{className:"danger",onClick:a,children:[e.jsx(In,{size:15})," Delete conversation"]})]})]})})}function Zr(t){const n=t.split("/");return n[n.length-1]??t}function im(t){var s;const n=(s=t.metadata)==null?void 0:s.promptRunner;if(!n||typeof n!="object")return null;const a=n.model;return typeof a=="string"?a:null}function rm(t){var s;const n=(s=t.metadata)==null?void 0:s.promptRunner;if(!n||typeof n!="object")return null;const a=n.maxNewTokens;return typeof a=="number"&&Number.isInteger(a)&&a>0?a:null}function om(t,n,a){const s=Number(t);return Number.isInteger(s)?Math.max(n,Math.min(a,s)):n}function Ti(t){var a;const n=(a=t.metadata)==null?void 0:a.promptRunner;if(n&&typeof n=="object"){const s=n.userPrompt;if(typeof s=="string"&&s.trim())return s}return lm(t.prompt)}function lm(t){var a,s;const n=[/<\|im_start\|>user\n(.*?)<\|im_end\|>/gs,/<start_of_turn>user\n(.*?)<end_of_turn>/gs,/(?:^|\n)User:\s*(.*?)(?=\nAssistant:|$)/gs];for(const i of n){const r=[...t.matchAll(i)],o=(s=(a=r[r.length-1])==null?void 0:a[1])==null?void 0:s.trim();if(o)return o}return t}function dm(){try{const t=JSON.parse(window.localStorage.getItem(Xr)??"[]");return new Set(Array.isArray(t)?t.filter(n=>typeof n=="string"):[])}catch{return new Set}}const fa="google/gemma-2-9b-it";function cm({onOpenChat:t}){const[n,a]=u.useState([]),[s,i]=u.useState([]),[r,o]=u.useState("pca_minus_neg"),[l,c]=u.useState("safelens-final-300-v1.1"),[d,p]=u.useState(new Set),g=fa,[b,_]=u.useState(null),[y,m]=u.useState(null),[x,w]=u.useState(null),[N,A]=u.useState("all"),T=s.find(H=>H.id===r),k=u.useMemo(()=>n.filter(H=>T==null?void 0:T.supportedDatasetIds.includes(H.id)),[T,n]),S=k.find(H=>H.id===l)??k[0],L=(b==null?void 0:b.status)==="idle"||(b==null?void 0:b.status)==="loading";u.useEffect(()=>{const H=new AbortController;return Ld(H.signal).then(Z=>{a(Z.datasets),i(Z.algorithms);const D=Z.datasets.find(C=>C.id==="safelens-final-300-v1.1")??Z.datasets[0];c(D.id),p(new Set(D.samples.map(C=>C.id)))}).catch(Z=>{Z instanceof DOMException&&Z.name==="AbortError"||m(Z instanceof Error?Z.message:"Dataset catalog is unavailable.")}),()=>H.abort()},[]),u.useEffect(()=>{if(!L||!b)return;let H=!1;const Z=window.setInterval(()=>{Ed(b.id).then(D=>{H||_(D)}).catch(D=>{H||w(D instanceof Error?D.message:"Could not refresh the job.")})},650);return()=>{H=!0,window.clearInterval(Z)}},[b==null?void 0:b.id,L]);function M(H){const Z=n.find(D=>H.supportedDatasetIds.includes(D.id));o(H.id),_(null),w(null),A("all"),Z&&(c(Z.id),p(new Set(Z.samples.map(D=>D.id))))}function F(H){const Z=n.find(D=>D.id===H);c(H),_(null),p(new Set((Z==null?void 0:Z.samples.map(D=>D.id))??[]))}function V(H){p(Z=>{const D=new Set(Z);return D.has(H)?D.delete(H):D.add(H),D})}async function W(){if(!(!S||!T||d.size===0)){w(null),A("all");try{const H=await $d({datasetId:S.id,algorithmId:T.id,model:g,sampleIds:S.samples.filter(Z=>d.has(Z.id)).map(Z=>Z.id),layer:22,sourceLayer:null,strength:1,seed:0,maxNewTokens:160});_(H)}catch(H){w(H instanceof Error?H.message:"Dataset test could not start.")}}}async function K(){if(b)try{_(await Md(b.id))}catch(H){w(H instanceof Error?H.message:"Dataset test could not be cancelled.")}}return e.jsxs("div",{className:"dataset-test-screen",children:[e.jsxs("header",{className:"dataset-test-header",children:[e.jsxs("button",{className:"dataset-test-brand",onClick:t,"aria-label":"Open SafeLens chat",children:[e.jsx("span",{children:e.jsx(Bt,{size:21})}),e.jsx("strong",{children:"SafeLens"})]}),e.jsxs("nav",{"aria-label":"SafeLens modes",children:[e.jsxs("button",{onClick:t,children:[e.jsx(Xo,{size:16})," Chat"]}),e.jsxs("button",{className:"active","aria-current":"page",children:[e.jsx(vt,{size:16})," Dataset test"]})]}),e.jsxs("span",{className:"dataset-live-badge",children:[e.jsx("i",{})," Real local evaluation"]})]}),e.jsxs("main",{className:"dataset-test-main",children:[e.jsxs("section",{className:"dataset-test-intro","aria-labelledby":"dataset-test-title",children:[e.jsxs("div",{children:[e.jsx("span",{children:"Evaluation mode"}),e.jsx("h1",{id:"dataset-test-title",children:"Test white-box methods on a fixed dataset"})]}),e.jsxs("dl",{children:[e.jsxs("div",{children:[e.jsx("dt",{children:"Samples"}),e.jsx("dd",{children:(S==null?void 0:S.samples.length)??0})]}),e.jsxs("div",{children:[e.jsx("dt",{children:"Selected"}),e.jsx("dd",{children:d.size})]}),e.jsxs("div",{children:[e.jsx("dt",{children:"Repair rate"}),e.jsx("dd",{children:Bn((S==null?void 0:S.metric.threshold)??0)})]})]})]}),y?e.jsxs("div",{className:"dataset-error",role:"alert",children:[e.jsx(Hn,{size:18})," ",y]}):e.jsxs("div",{className:"dataset-test-setup",children:[e.jsxs("section",{className:"dataset-source-panel","aria-labelledby":"dataset-source-title",children:[e.jsxs("header",{children:[e.jsxs("div",{children:[e.jsx("span",{children:"1 / Dataset"}),e.jsx("h2",{id:"dataset-source-title",children:"Choose evaluation samples"})]}),e.jsxs("label",{children:[e.jsx("span",{children:"Dataset"}),e.jsx("select",{value:(S==null?void 0:S.id)??"",onChange:H=>F(H.target.value),children:k.map(H=>e.jsx("option",{value:H.id,children:H.name},H.id))})]})]}),S&&e.jsxs(e.Fragment,{children:[e.jsxs("div",{className:"dataset-description",children:[e.jsx("p",{children:S.description}),e.jsxs("span",{children:[S.source," / v",S.version]})]}),e.jsxs("div",{className:"dataset-sample-toolbar",children:[e.jsxs("strong",{children:[d.size," of ",S.samples.length," selected"]}),e.jsxs("button",{onClick:()=>p(d.size===S.samples.length?new Set:new Set(S.samples.map(H=>H.id))),children:[d.size===S.samples.length?e.jsx(js,{size:15}):e.jsx(Kt,{size:15}),d.size===S.samples.length?"Clear all":"Select all"]})]}),e.jsx("div",{className:"dataset-sample-list",children:S.samples.map(H=>e.jsxs("button",{className:d.has(H.id)?"selected":"","aria-pressed":d.has(H.id),onClick:()=>V(H.id),children:[d.has(H.id)?e.jsx(js,{size:17}):e.jsx(Kt,{size:17}),e.jsxs("span",{children:[e.jsxs("small",{children:[H.id," / ",H.task??H.category," / ",H.source]}),e.jsx("strong",{children:H.prompt??H.corruptedPrompt}),H.groundTruth&&e.jsxs("em",{children:["Ground truth: ",H.groundTruth]}),H.cleanPrompt&&e.jsxs("em",{children:["Clean: ",H.cleanPrompt]}),H.desiredPrompt&&e.jsxs("em",{children:["Toward: ",H.desiredPrompt]})]})]},H.id))})]})]}),e.jsxs("section",{className:"dataset-method-panel","aria-labelledby":"dataset-method-title",children:[e.jsxs("header",{children:[e.jsx("span",{children:"2 / Method"}),e.jsx("h2",{id:"dataset-method-title",children:"Select an optimization algorithm"})]}),e.jsx("div",{className:"dataset-method-tabs",role:"radiogroup","aria-label":"Optimization algorithm",children:s.map(H=>e.jsxs("button",{role:"radio","aria-checked":H.id===r,className:H.id===r?"active":"",onClick:()=>M(H),children:[H.id==="pca_minus_neg"?e.jsx(Bt,{size:18}):e.jsx(Zo,{size:18}),e.jsxs("span",{children:[e.jsx("strong",{children:H.name}),e.jsx("small",{children:H.implementation.replace(/_/g," ")})]})]},H.id))}),T&&e.jsxs("div",{className:"dataset-method-summary",children:[e.jsx("p",{children:T.description}),e.jsxs("a",{href:T.paperUrl,target:"_blank",rel:"noreferrer",children:[e.jsxs("span",{children:[e.jsx("small",{children:"Method reference"}),e.jsx("strong",{children:T.paperTitle})]}),e.jsx(el,{size:16})]})]}),S&&e.jsxs("div",{className:"dataset-metric-note",children:[e.jsx("strong",{children:S.metric.name}),e.jsx("p",{children:S.metric.definition}),e.jsxs("span",{children:["Required repair rate ≥ ",Bn(S.metric.threshold)]})]}),e.jsxs("div",{className:"dataset-run-controls",children:[e.jsxs("label",{className:"wide",children:[e.jsx("span",{children:"Local model"}),e.jsx("select",{value:g,disabled:!0,children:e.jsx("option",{value:fa,children:hm(fa)})})]}),e.jsx("p",{className:"wide",children:"The run first evaluates every selected sample without intervention, then applies steering only to baseline failures. Layer, alpha, and injection scope use the fixed final_300 protocol."})]}),e.jsxs("button",{className:"dataset-run-button",disabled:L||!S||d.size===0,onClick:W,children:[L?e.jsx(Vt,{size:18,className:"spin"}):e.jsx(Xi,{size:18,fill:"currentColor"}),L?"Running dataset test":`Test ${d.size} ${d.size===1?"sample":"samples"}`]}),L&&b&&e.jsxs("button",{className:"dataset-cancel-button",onClick:K,children:[e.jsx(Gi,{size:16})," Cancel"]}),x&&e.jsxs("div",{className:"dataset-error",role:"alert",children:[e.jsx(Hn,{size:17})," ",x]})]})]}),b&&e.jsx(um,{job:b,filter:N,onFilter:A})]})]})}function um({job:t,filter:n,onFilter:a}){if(t.status!=="ready"||!t.result)return e.jsxs("section",{className:"dataset-job-progress","aria-live":"polite",children:[e.jsxs("header",{children:[e.jsx("span",{children:"3 / Test run"}),e.jsx("strong",{children:t.detail}),e.jsxs("b",{children:[t.progress,"%"]})]}),e.jsx("div",{children:e.jsx("i",{style:{width:`${t.progress}%`}})}),t.error&&e.jsx("p",{children:t.error})]});const s=t.result,i=s.rows.filter(r=>n==="all"||(n==="passed"?r.passed:!r.passed));return e.jsxs("section",{className:"dataset-results","aria-labelledby":"dataset-results-title",children:[e.jsxs("header",{className:s.metric.meetsThreshold?"passed":"failed",children:[e.jsxs("div",{children:[e.jsx("span",{children:"3 / Results"}),e.jsx("h2",{id:"dataset-results-title",children:s.dataset.name}),e.jsxs("p",{children:[s.execution.model," / ",s.execution.layer===void 0?"fixed task layers":`L${s.execution.layer}`,s.execution.requestedLayer!==void 0&&s.execution.requestedLayer!==s.execution.layer?` (requested L${s.execution.requestedLayer})`:""," / ",s.execution.source,s.execution.device?` / ${s.execution.device}`:"",s.execution.dtype?` / ${s.execution.dtype}`:""]})]}),e.jsxs("div",{className:"dataset-score",children:[s.metric.meetsThreshold?e.jsx(ot,{size:24}):e.jsx(Hn,{size:24}),e.jsx("strong",{children:Bn(s.metric.accuracy)}),e.jsx("span",{children:s.metric.meetsThreshold?"Threshold met":"Below threshold"})]}),e.jsxs("dl",{children:[e.jsxs("div",{children:[e.jsx("dt",{children:"Baseline failures"}),e.jsx("dd",{children:s.metric.baselineFailure??0})]}),e.jsxs("div",{children:[e.jsx("dt",{children:"Repaired"}),e.jsx("dd",{children:s.metric.failureToSuccess??0})]}),e.jsxs("div",{children:[e.jsx("dt",{children:"Completed"}),e.jsx("dd",{children:s.metric.completed})]}),e.jsxs("div",{children:[e.jsx("dt",{children:"Errors"}),e.jsx("dd",{children:s.metric.errors})]}),e.jsxs("div",{children:[e.jsx("dt",{children:"Repair target"}),e.jsx("dd",{children:Bn(s.metric.threshold)})]})]})]}),e.jsxs("div",{className:"dataset-result-toolbar",children:[e.jsx("div",{role:"tablist","aria-label":"Result filter",children:["all","passed","failed"].map(r=>e.jsx("button",{role:"tab","aria-selected":n===r,className:n===r?"active":"",onClick:()=>a(r),children:r==="all"?"All samples":r==="passed"?"Correct":"Incorrect"},r))}),e.jsxs("span",{children:[e.jsx(vt,{size:14})," ",s.dataset.version," / ",s.algorithm.implementation.replace(/_/g," ")]})]}),e.jsxs("div",{className:"dataset-result-list",children:[i.map(r=>e.jsx(mm,{row:r,result:s},r.sampleId)),!i.length&&e.jsx("p",{className:"dataset-empty-filter",children:"No samples in this result group."})]})]})}function mm({row:t,result:n}){const a=t.steered??t.patched;return e.jsxs("article",{className:`dataset-result-row ${t.passed?"passed":"failed"}`,children:[e.jsxs("header",{children:[t.passed?e.jsx(ot,{size:18}):e.jsx(Hn,{size:18}),e.jsxs("div",{children:[e.jsx("strong",{children:t.sampleId}),e.jsx("span",{children:t.category})]}),e.jsx("b",{children:t.status==="error"?"Error":t.passed?"Correct":"Incorrect"})]}),e.jsx("p",{className:"dataset-result-prompt",children:t.prompt}),e.jsx("p",{className:"dataset-result-detail",children:t.detail}),(t.original!==void 0||a!==void 0)&&e.jsxs("div",{className:"dataset-output-compare",children:[e.jsxs("div",{children:[e.jsx("span",{children:"Original"}),e.jsx("p",{children:t.original||"No visible continuation"})]}),e.jsxs("div",{children:[e.jsx("span",{children:"Steered"}),e.jsx("p",{children:t.steeringApplied===!1?"Not run (baseline successful)":a||"No visible continuation"})]})]}),t.diagnostics&&e.jsx("dl",{className:"dataset-diagnostics",children:Object.entries(t.diagnostics).slice(0,6).map(([s,i])=>e.jsxs("div",{children:[e.jsx("dt",{children:pm(s)}),e.jsx("dd",{children:ym(i)})]},s))})]})}function hm(t){const n=t.split("/");return n[n.length-1]||t}function Bn(t){return`${(t*100).toFixed(2)}%`}function pm(t){return t.replace(/([a-z])([A-Z])/g,"$1 $2").replace(/_/g," ")}function ym(t){return Array.isArray(t)?t.length>8?`${t.slice(0,8).join(", ")}...`:t.join(", "):typeof t=="number"?Number.isInteger(t)?String(t):t.toFixed(5):String(t)}function fm({layers:t,selectedLayer:n,onSelect:a}){return e.jsxs("div",{className:"layer-picker main-layer-picker",role:"group","aria-label":"Layer selector",children:[e.jsx("span",{className:"control-label",children:"Layer"}),t.length<=16?e.jsx("div",{className:"layer-button-selector",role:"radiogroup","aria-label":"Analysis layer",children:t.map(s=>e.jsxs("button",{role:"radio","data-layer":s,"aria-checked":n===s,tabIndex:n===s?0:-1,className:n===s?"active":"",onClick:()=>a(s),onKeyDown:i=>bm(i,t,s,a),children:["L",s]},s))}):e.jsx(xm,{layers:t,selectedLayer:n,onSelect:a})]})}function gm({visible:t,tokenText:n,tokenIndex:a,layer:s,score:i,view:r,menuOpen:o,contextOpen:l,pinned:c,canPin:d,pinnedCount:p,onToggleMenu:g,onSelectView:b,onInspect:_,onToggleContext:y,onPin:m,onPreloadCompare:x,onCompare:w,onDismiss:N}){const A=Le.useRef(null);if(u.useEffect(()=>{if(!o)return;function S(M){M.key==="Escape"&&(M.preventDefault(),g())}function L(M){var F;(F=A.current)!=null&&F.contains(M.target)||g()}return window.addEventListener("keydown",S),window.addEventListener("pointerdown",L),()=>{window.removeEventListener("keydown",S),window.removeEventListener("pointerdown",L)}},[o,g]),!t)return null;const T=[{id:"overview",label:"Overview",icon:e.jsx(Be,{size:16})},{id:"residual",label:"Residual",icon:e.jsx(Sn,{size:16})},{id:"attention",label:"Attention",icon:e.jsx(Ot,{size:16})},{id:"mlp",label:"MLP",icon:e.jsx(Bt,{size:16})},{id:"nla",label:"NLA",icon:e.jsx(dt,{size:16})},{id:"attribution",label:"Attribution",icon:e.jsx(ta,{size:16})},{id:"patching",label:"Patching",icon:e.jsx(Yt,{size:16})},{id:"intervention",label:"Intervention",icon:e.jsx($t,{size:16})}],k=n.trim()||"space";return e.jsxs("section",{ref:A,className:"selection-workbench","aria-label":"Selected token actions","aria-live":"polite",children:[e.jsxs("div",{className:"selection-workbench-main",children:[e.jsxs("div",{className:"selection-workbench-identity",children:[e.jsx("span",{"aria-hidden":"true"}),e.jsxs("div",{children:[e.jsx("small",{children:"Selected token"}),e.jsx("strong",{children:k})]}),e.jsxs("dl",{children:[e.jsxs("div",{children:[e.jsx("dt",{children:"Position"}),e.jsxs("dd",{children:["T",a]})]}),e.jsxs("div",{children:[e.jsx("dt",{children:"Layer"}),e.jsxs("dd",{children:["L",s]})]}),e.jsxs("div",{children:[e.jsx("dt",{children:"Safety proxy"}),e.jsx("dd",{children:i})]})]})]}),e.jsxs("div",{className:"selection-workbench-actions",children:[e.jsxs("button",{className:o?"active":"","aria-expanded":o,"aria-haspopup":"menu","aria-controls":"selection-analysis-menu",title:"Choose an analysis for the selected token",onClick:g,children:[e.jsx(dt,{size:16})," Analyze"]}),e.jsxs("button",{title:"Inspect selected evidence",onClick:S=>_(S.currentTarget),children:[e.jsx(ja,{size:16})," Inspect"]}),e.jsxs("button",{className:l?"active":"","aria-expanded":l,title:"Toggle supporting context",onClick:y,children:[e.jsx(tl,{size:16})," Context"]}),e.jsxs("button",{className:c?"active":"","aria-pressed":c,disabled:!d,title:c?"Unpin selected evidence":"Pin selected evidence",onClick:m,children:[e.jsx(Gn,{size:16})," ",c?"Unpin":"Pin"]}),e.jsxs("button",{disabled:!p,title:"Compare pinned evidence",onPointerEnter:x,onFocus:x,onClick:S=>w(S.currentTarget),children:[e.jsx(yt,{size:16})," Compare",e.jsx("b",{children:p})]}),e.jsx("button",{className:"selection-workbench-dismiss","aria-label":"Dismiss selected token actions",onClick:N,children:e.jsx(at,{size:16})})]})]}),o&&e.jsx("div",{id:"selection-analysis-menu",className:"selection-analysis-menu",role:"menu","aria-label":"Analyze selected token",children:T.map(S=>e.jsxs("button",{role:"menuitemradio","aria-checked":r===S.id,className:r===S.id?"active":"",onClick:()=>b(S.id),children:[S.icon,e.jsx("span",{children:S.label}),r===S.id&&e.jsx(ot,{size:14})]},S.id))})]})}function _m({view:t,setView:n}){const a=Le.useRef(null),s=Le.useRef(null),[i,r]=Le.useState({previous:!1,next:!1}),o=[{id:"overview",label:"Overview",icon:e.jsx(Be,{size:15})},{id:"residual",label:"Residual",icon:e.jsx(Sn,{size:15})},{id:"attention",label:"Attention",icon:e.jsx(Ot,{size:15})},{id:"mlp",label:"MLP",icon:e.jsx(Fa,{size:15})},{id:"nla",label:"NLA",icon:e.jsx(Ya,{size:15})},{id:"patching",label:"Patching",icon:e.jsx(Yt,{size:15})},{id:"intervention",label:"Intervention",icon:e.jsx($t,{size:15})},{id:"attribution",label:"Attribution",icon:e.jsx(ta,{size:15})}];u.useEffect(()=>{var x;const d=a.current;if(!d||!window.matchMedia("(max-width: 860px)").matches)return;const p=[...d.querySelectorAll('[role="tab"]')],g=p.findIndex(w=>w.id===`analysis-tab-${t}`),b=p[0];if(g<0||!b)return;const _=Number.parseFloat(getComputedStyle(d).columnGap)||6,y=Math.max(1,Math.floor((d.clientWidth+_)/Math.max(1,b.offsetWidth+_))),m=Math.floor(g/y)*y;d.scrollLeft=Math.max(0,(((x=p[m])==null?void 0:x.offsetLeft)??b.offsetLeft)-b.offsetLeft),window.requestAnimationFrame(()=>Ai(d,r))},[t]),u.useEffect(()=>{const d=a.current;if(!d)return;const p=()=>Ai(d,r),g=new ResizeObserver(p);return d.addEventListener("scroll",p,{passive:!0}),g.observe(d),window.requestAnimationFrame(p),()=>{d.removeEventListener("scroll",p),g.disconnect()}},[]),u.useEffect(()=>{var g;const d=s.current,p=a.current;!d||!p||(d===1&&!i.next&&(s.current=null,p.querySelectorAll('[role="tab"]').item(o.length-1).focus({preventScroll:!0})),d===-1&&!i.previous&&(s.current=null,(g=p.querySelector('[role="tab"]'))==null||g.focus({preventScroll:!0})))},[i.next,i.previous,o.length]);function l(d){const p=a.current;if(!p)return;s.current=d;const g=window.matchMedia("(prefers-reduced-motion: reduce)").matches;p.scrollBy({left:d*p.clientWidth,behavior:g?"auto":"smooth"})}function c(d,p){var _,y;let g;if(d.key==="ArrowLeft"||d.key==="ArrowUp"?g=(p-1+o.length)%o.length:d.key==="ArrowRight"||d.key==="ArrowDown"?g=(p+1)%o.length:d.key==="Home"?g=0:d.key==="End"&&(g=o.length-1),g===void 0)return;d.preventDefault();const b=o[g];n(b.id),(y=(_=d.currentTarget.parentElement)==null?void 0:_.querySelector(`#analysis-tab-${b.id}`))==null||y.focus()}return e.jsxs("div",{className:`workspace-tabs-shell ${i.previous?"has-previous":""} ${i.next?"has-next":""}`,children:[e.jsx("button",{type:"button",className:"workspace-tabs-scroll previous","aria-label":"Show previous analysis views","aria-controls":"analysis-view-tabs",title:i.previous?"Previous views":"At first view page",disabled:!i.previous,onClick:()=>l(-1),children:e.jsx(dn,{size:17})}),e.jsx("div",{ref:a,id:"analysis-view-tabs",className:"workspace-tabs",role:"tablist","aria-label":"Analysis view",children:o.map((d,p)=>e.jsxs("button",{id:`analysis-tab-${d.id}`,role:"tab","aria-controls":"analysis-panel","aria-selected":t===d.id,tabIndex:t===d.id?0:-1,className:t===d.id?"active":"",onClick:()=>n(d.id),onKeyDown:g=>c(g,p),children:[d.icon,e.jsx("span",{children:d.label})]},d.id))}),e.jsx("button",{type:"button",className:"workspace-tabs-scroll next","aria-label":"Show more analysis views","aria-controls":"analysis-view-tabs",title:i.next?"More views":"At last view page",disabled:!i.next,onClick:()=>l(1),children:e.jsx(gt,{size:17})})]})}function Ai(t,n){const a=Math.max(0,t.scrollWidth-t.clientWidth),s={previous:t.scrollLeft>2,next:t.scrollLeft<a-2};n(i=>i.previous===s.previous&&i.next===s.next?i:s)}function bm(t,n,a,s){var l,c;const i=n.indexOf(a);let r;if(t.key==="ArrowLeft"||t.key==="ArrowUp"?r=(i-1+n.length)%n.length:t.key==="ArrowRight"||t.key==="ArrowDown"?r=(i+1)%n.length:t.key==="Home"?r=0:t.key==="End"&&(r=n.length-1),r===void 0)return;t.preventDefault();const o=n[r];s(o),(c=(l=t.currentTarget.parentElement)==null?void 0:l.querySelector(`[role="radio"][data-layer="${o}"]`))==null||c.focus()}function xm({layers:t,selectedLayer:n,onSelect:a}){const s=Math.max(0,t.indexOf(n));return e.jsxs("div",{className:"compact-layer-selector",children:[e.jsx("button",{"aria-label":"Previous layer",title:"Previous layer",disabled:s===0,onClick:()=>a(t[s-1]),children:e.jsx(dn,{size:14})}),e.jsx("select",{"aria-label":"Selected layer",value:t[s],onChange:i=>a(Number(i.target.value)),children:t.map(i=>e.jsxs("option",{value:i,children:["Layer ",i]},i))}),e.jsx("button",{"aria-label":"Next layer",title:"Next layer",disabled:s>=t.length-1,onClick:()=>a(t[s+1]),children:e.jsx(gt,{size:14})}),e.jsxs("span",{children:[s+1," / ",t.length]})]})}const eo="safelens.localExplorer.pinnedEvidence.v2",wm=["overview","residual","attention","mlp","nla","patching","intervention","attribution"];function km(t,n){switch(n.type){case"select_token":return{...t,tokenIndex:n.tokenIndex,sourceTokenIndex:Math.min(t.sourceTokenIndex??n.tokenIndex,n.tokenIndex),targetTokenIndex:n.tokenIndex,tokenRange:void 0};case"select_source_token":return{...t,sourceTokenIndex:Math.min(n.tokenIndex,t.targetTokenIndex??t.tokenIndex)};case"select_attention_pair":return{...t,tokenIndex:n.targetTokenIndex,sourceTokenIndex:n.sourceTokenIndex,targetTokenIndex:n.targetTokenIndex,tokenRange:void 0};case"select_range":return{...t,tokenRange:n.tokenRange};case"select_layer":return{...t,layer:n.layer};case"select_view":return{...t,view:n.view,metric:ao(n.view,t.trackName),normalization:n.view==="attention"||n.view==="mlp"||n.view==="attribution"||n.view==="intervention"?"raw":t.normalization};case"select_head":return{...t,headId:n.headId};case"select_attention_edge_mode":return{...t,attentionEdgeMode:n.mode};case"select_nla_component":return{...t,nlaComponent:n.component};case"select_neuron":return{...t,neuronId:n.neuronId};case"select_track":return{...t,trackName:n.trackName,metric:t.view==="attribution"?n.trackName:t.metric};case"select_metric":return{...t,metric:n.metric};case"set_normalization":return{...t,normalization:n.normalization};case"toggle_pin":{const a=t.pinnedItems.some(s=>s.id===n.evidence.id);return{...t,pinnedItems:a?t.pinnedItems.filter(s=>s.id!==n.evidence.id):[...t.pinnedItems,n.evidence].slice(-4)}}case"restore_pin":return{...t,tokenIndex:n.evidence.tokenIndex,sourceTokenIndex:n.evidence.sourceTokenIndex??t.sourceTokenIndex,targetTokenIndex:n.evidence.tokenIndex,tokenRange:void 0,layer:n.evidence.layer,view:n.evidence.view,headId:n.evidence.headId??t.headId,nlaComponent:n.evidence.view==="nla"&&no(n.evidence.component)?n.evidence.component:t.nlaComponent,neuronId:n.evidence.neuronId??t.neuronId,trackName:n.evidence.trackName??(n.evidence.view==="attribution"?n.evidence.metric:t.trackName),metric:n.evidence.metric,normalization:n.evidence.normalization};case"restore_session":case"restore_url":return n.selection}}function vm(t){return to(t,Sm(t))}function to(t,n){const a=new URLSearchParams(window.location.search),s=a.get("view")??a.get("mode"),i=zn(a.get("token")),r=zn(a.get("source")),o=zn(a.get("target")),l=zn(a.get("layer")),c=a.get("normalization"),d=Im(a.get("range")),p=a.get("edge"),g=a.get("nlaComponent"),b=wm.includes(s)?s:t.view,_=a.get("track")??t.trackName,y=o!==void 0&&t.tokenIndices.includes(o)?o:i!==void 0&&t.tokenIndices.includes(i)?i:t.tokenIndex,m=r!==void 0&&t.tokenIndices.includes(r)?r:y,x=d&&t.tokenIndices.includes(d[0])&&t.tokenIndices.includes(d[1])?d:void 0;return{view:b,tokenIndex:y,sourceTokenIndex:Math.min(m,y),targetTokenIndex:y,tokenRange:x,layer:l!==void 0&&t.layers.includes(l)?l:t.layer,headId:a.get("head")??t.headId,attentionEdgeMode:p==="outgoing"?"outgoing":"incoming",nlaComponent:no(g)?g:t.nlaComponent,neuronId:a.get("neuron")??t.neuronId,trackName:_,metric:a.get("metric")??ao(b,_),normalization:c==="raw"||c==="normalized"?c:b==="attention"||b==="intervention"?"raw":"normalized",pinnedItems:n}}function jm(t){const[n,a]=u.useReducer(km,t,vm),s=u.useRef(t),i=u.useRef(n.pinnedItems),r=u.useRef("replace");s.current=t,i.current=n.pinnedItems;function o(l,c="push"){r.current=c,a(l)}return u.useEffect(()=>{const l=new URLSearchParams(window.location.search),c=l.get("run"),d=l.get("sample");if(c&&c!==t.runId||d&&d!==t.sampleId)return;l.set("view",n.view),l.set("token",String(n.tokenIndex)),l.set("layer",String(n.layer)),l.set("normalization",n.normalization),n.headId&&l.set("head",n.headId),n.neuronId&&l.set("neuron",n.neuronId),n.trackName&&l.set("track",n.trackName),n.metric&&l.set("metric",n.metric),n.tokenRange?l.set("range",`${n.tokenRange[0]}-${n.tokenRange[1]}`):l.delete("range"),n.view==="attention"?(l.set("source",String(n.sourceTokenIndex??n.tokenIndex)),l.set("target",String(n.targetTokenIndex??n.tokenIndex)),l.set("edge",n.attentionEdgeMode)):(l.delete("source"),l.delete("target"),l.delete("edge")),n.view==="nla"?l.set("nlaComponent",n.nlaComponent):l.delete("nlaComponent"),l.delete("mode");const p=`${window.location.pathname}?${l.toString()}${window.location.hash}`,g=`${window.location.pathname}${window.location.search}${window.location.hash}`,b=r.current;r.current="replace",p!==g&&(b==="push"?window.history.pushState(window.history.state,"",p):window.history.replaceState(window.history.state,"",p))},[t.runId,t.sampleId,n.attentionEdgeMode,n.headId,n.layer,n.metric,n.neuronId,n.nlaComponent,n.normalization,n.sourceTokenIndex,n.targetTokenIndex,n.tokenIndex,n.tokenRange,n.trackName,n.view]),u.useEffect(()=>{function l(){const c=s.current,d=new URLSearchParams(window.location.search),p=d.get("run"),g=d.get("sample");p&&p!==c.runId||g&&g!==c.sampleId||(r.current="replace",a({type:"restore_url",selection:to(c,i.current)}))}return window.addEventListener("popstate",l),()=>window.removeEventListener("popstate",l)},[]),u.useEffect(()=>{window.localStorage.setItem(eo,JSON.stringify(n.pinnedItems))},[n.pinnedItems]),{state:n,selectToken:(l,c)=>o({type:"select_token",tokenIndex:l},c),selectSourceToken:(l,c)=>o({type:"select_source_token",tokenIndex:l},c),selectAttentionPair:(l,c,d)=>o({type:"select_attention_pair",sourceTokenIndex:l,targetTokenIndex:c},d),selectRange:(l,c)=>o({type:"select_range",tokenRange:l},c),selectLayer:(l,c)=>o({type:"select_layer",layer:l},c),selectView:(l,c)=>o({type:"select_view",view:l},c),selectHead:(l,c)=>o({type:"select_head",headId:l},c),selectAttentionEdgeMode:(l,c)=>o({type:"select_attention_edge_mode",mode:l},c),selectNlaComponent:(l,c)=>o({type:"select_nla_component",component:l},c),selectNeuron:(l,c)=>o({type:"select_neuron",neuronId:l},c),selectTrack:(l,c)=>o({type:"select_track",trackName:l},c),selectMetric:(l,c)=>o({type:"select_metric",metric:l},c),setNormalization:(l,c)=>o({type:"set_normalization",normalization:l},c),togglePin:l=>a({type:"toggle_pin",evidence:l}),restorePin:(l,c)=>o({type:"restore_pin",evidence:l},c),restoreSession:(l,c)=>o({type:"restore_session",selection:l},c)}}function no(t){return t==="resid_post"||t==="attn_result"||t==="mlp_out"}function ao(t,n){return t==="residual"?"residual_direction":t==="attention"?"attention_probability":t==="mlp"?"mlp_signed_activation":t==="nla"?"nla_cosine":t==="patching"?"patching_recovery":t==="intervention"?"intervention_logit_delta":t==="attribution"?n:"tokenRisk"}function zn(t){if(!(t===null||!/^\d+$/.test(t)))return Number(t)}function Im(t){const n=t==null?void 0:t.match(/^(\d+)-(\d+)$/);if(!n)return;const a=Number(n[1]),s=Number(n[2]);return a<=s?[a,s]:[s,a]}function Sm(t){try{const n=JSON.parse(window.localStorage.getItem(eo)??"[]");if(!Array.isArray(n))return t.initialPinnedItems??[];const a=n.filter(Tm);return a.length>0?a.slice(-4):t.initialPinnedItems??[]}catch{return t.initialPinnedItems??[]}}function Tm(t){if(!t||typeof t!="object")return!1;const n=t;return typeof n.id=="string"&&typeof n.runId=="string"&&typeof n.sampleId=="string"&&Number.isInteger(n.tokenIndex)&&typeof n.tokenText=="string"&&Number.isInteger(n.layer)&&typeof n.view=="string"&&typeof n.metric=="string"&&typeof n.value=="number"&&(n.normalization==="raw"||n.normalization==="normalized")&&(n.profile===void 0||Am(n.profile))&&(n.matrix===void 0||Cm(n.matrix,n))&&(n.generation===void 0||Nm(n.generation))}function Am(t){if(!t||typeof t!="object")return!1;const n=t;return n.schemaVersion!=="1.0"||n.kind!=="attention_source_profile"&&n.kind!=="signed_attribution_profile"&&n.kind!=="mlp_activation_profile"||n.axis!=="source_token"&&n.axis!=="token"||typeof n.label!="string"||typeof n.signed!="boolean"||!Number.isInteger(n.originalLength)||n.originalLength<1||typeof n.sampled!="boolean"||!Array.isArray(n.points)||n.points.length<1||n.points.length>256||n.originalLength<n.points.length||n.sampled===(n.originalLength===n.points.length)?!1:n.points.every(a=>a!==null&&typeof a=="object"&&Number.isInteger(a.tokenIndex)&&a.tokenIndex>=0&&(a.tokenId===void 0||Number.isInteger(a.tokenId))&&typeof a.tokenText=="string"&&Number.isFinite(a.value))}function Nm(t){if(!t||typeof t!="object")return!1;const n=t;if(n.schemaVersion!=="1.0"||!n.sourceRun||typeof n.sourceRun.runId!="string"||typeof n.sourceRun.sampleId!="string"||!Number.isInteger(n.layer)||n.layer<0||!["resid_post","attn_out","mlp_out"].includes(n.component)||!Number.isFinite(n.scale)||!Number.isInteger(n.positionStart)||n.positionStart<0||!Number.isInteger(n.positionEnd)||n.positionEnd<=n.positionStart||!Number.isInteger(n.targetTokenId)||typeof n.targetTokenText!="string"||!Number.isInteger(n.seed)||!Number.isInteger(n.maxNewTokens)||n.maxNewTokens<1||n.maxNewTokens>256||!Number.isFinite(n.temperature)||n.temperature<0||!Number.isInteger(n.tokenEditDistance)||n.tokenEditDistance<0||n.generationChanged!==n.tokenEditDistance>0||!Array.isArray(n.diff)||n.diff.length>512||!Ni(n.original,n.maxNewTokens)||!Ni(n.steered,n.maxNewTokens))return!1;let a=0,s=0;for(const i of n.diff){if(!i||typeof i!="object")return!1;const r=i.originalEnd-i.originalStart,o=i.steeredEnd-i.steeredStart;if(!["equal","replace","delete","insert"].includes(i.kind)||!Number.isInteger(i.originalStart)||!Number.isInteger(i.originalEnd)||!Number.isInteger(i.steeredStart)||!Number.isInteger(i.steeredEnd)||i.originalStart!==a||i.steeredStart!==s||r<0||o<0||i.kind==="equal"&&(r===0||r!==o)||i.kind==="replace"&&(r===0||o===0)||i.kind==="delete"&&(r===0||o!==0)||i.kind==="insert"&&(r!==0||o===0))return!1;a=i.originalEnd,s=i.steeredEnd}return a===n.original.tokens.length&&s===n.steered.tokens.length}function Cm(t,n){if(!t||typeof t!="object")return!1;const a=t;if(a.schemaVersion!=="1.0"||a.kind!=="attention_matrix"||typeof a.label!="string"||!Number.isInteger(a.originalSize)||a.originalSize<1||typeof a.sampled!="boolean"||!Array.isArray(a.axis)||a.axis.length<1||a.axis.length>64||a.originalSize<a.axis.length||a.sampled===(a.originalSize===a.axis.length)||!Array.isArray(a.values)||a.values.length!==a.axis.length||n.view!=="attention"||typeof n.headId!="string"||!a.axis.every((r,o)=>r!==null&&typeof r=="object"&&Number.isInteger(r.tokenIndex)&&r.tokenIndex>=0&&(r.tokenId===void 0||Number.isInteger(r.tokenId))&&typeof r.tokenText=="string"&&(o===0||r.tokenIndex>a.axis[o-1].tokenIndex)))return!1;const i=new Set(a.axis.map(r=>r.tokenIndex));return!i.has(n.tokenIndex??-1)||n.sourceTokenIndex===void 0||!i.has(n.sourceTokenIndex)?!1:a.values.every((r,o)=>Array.isArray(r)&&r.length===a.axis.length&&r.every((l,c)=>a.axis[c].tokenIndex>a.axis[o].tokenIndex?l===null:typeof l=="number"&&Number.isFinite(l)&&l>=0&&l<=1))}function Ni(t,n){return!!(t&&typeof t.text=="string"&&Array.isArray(t.tokens)&&t.tokens.length<=n&&Number.isFinite(t.targetLogit)&&Number.isFinite(t.lexicalRisk)&&t.tokens.every((a,s)=>a!==null&&typeof a=="object"&&a.index===s&&Number.isInteger(a.tokenId)&&typeof a.text=="string"))}const Qh=[{id:"individual",label:"Head",description:"Show one retained attention head."},{id:"difference",label:"Difference",description:"Cell-wise selected retained head minus baseline retained head."},{id:"mean",label:"Mean",description:"Cell-wise mean over retained heads in this layer."},{id:"max",label:"Max",description:"Cell-wise maximum over retained heads in this layer."},{id:"rollout",label:"Rollout",description:"Retained-head mean with identity residual, multiplied through the current layer."},{id:"entropy_weighted",label:"Entropy",description:"Weighted mean using normalized inverse stored head entropy."}],Pa="aggregate:",Wa="difference:",so="rollout:retained_mean_identity";function Rm(t){return`${Pa}${t}`}function io(t){if(!(t!=null&&t.startsWith(Pa)))return;const n=t.slice(Pa.length);return n==="mean"||n==="max"||n==="entropy_weighted"?n:void 0}function ro(t,n){return`${Wa}${encodeURIComponent(t)}:${encodeURIComponent(n)}`}function oo(t){if(!(t!=null&&t.startsWith(Wa)))return;const[n,a,...s]=t.slice(Wa.length).split(":");if(!(!n||!a||s.length>0))try{const i=decodeURIComponent(n),r=decodeURIComponent(a);return i!==r?{selectedHeadId:i,baselineHeadId:r}:void 0}catch{return}}function Lm(){return so}function as(t){return t===so?{fusion:"retained_mean",residual:"identity"}:void 0}function An(t){return t==="entropy_weighted"?"Entropy-weighted retained heads":`${t==="mean"?"Mean":"Max"} retained heads`}function St(t){return t.rollout?`Retained attention rollout · L${t.rollout.layers[0]}–L${t.layer}`:t.difference?`${t.difference.selectedHeadId} - ${t.difference.baselineHeadId}`:t.aggregation?An(t.aggregation):t.id}function Ci(t,n,a=t,s=(r=>(r=t[0])==null?void 0:r.layer)(),i){if(as(n)&&s!==void 0)return $m(a,s,i);const o=oo(n);if(o)return Em(t,o.selectedHeadId,o.baselineHeadId);const l=io(n);return l?Pm(t,l):t.find(c=>c.id===n)??t[0]}function $m(t,n,a){const s=t.filter(d=>d.layer<=n&&!d.aggregation&&!d.difference&&!d.rollout),i=[...new Set(s.map(d=>d.layer))].sort((d,p)=>d-p);if(i.length===0||i[i.length-1]!==n)return;const r=[...new Set((a??i).filter(d=>d<=n))].sort((d,p)=>d-p);if(r.length!==i.length||r.some((d,p)=>d!==i[p]))return;const o=Math.max(0,...s.flatMap(d=>[d.distributionByToken.length,...d.distributionByToken.map(p=>p.length)]));if(o===0)return;let l=zm(o);for(const d of i){const p=s.filter(b=>b.layer===d),g=Array.from({length:o},(b,_)=>{const y=Array.from({length:o},(x,w)=>w>_?0:p.reduce((A,T)=>{var k;return A+Vn((k=T.distributionByToken[_])==null?void 0:k[w])},0)/p.length+(_===w?1:0)),m=y.reduce((x,w)=>x+w,0);return y.map(x=>m>0?x/m:0)});l=Dm(g,l)}const c=s.map(d=>d.id);return{id:Lm(),layer:n,head:-1,role:`Retained-head mean + identity residual rollout · ${i.length} layers · ${c.length} heads`,riskContribution:s.reduce((d,p)=>d+p.riskContribution,0)/s.length,entropy:Ym(l),distributionByToken:l.map((d,p)=>d.slice(0,p+1)),rollout:{fusion:"retained_mean",residual:"identity",layers:i,memberHeadIds:c},memberHeadIds:c}}function Em(t,n,a){const s=t.find(l=>l.id===n),i=t.find(l=>l.id===a);if(!s||!i||s.id===i.id||s.layer!==i.layer)return;const r=Math.max(s.distributionByToken.length,i.distributionByToken.length),o=Array.from({length:r},(l,c)=>{var p,g;const d=Math.max(((p=s.distributionByToken[c])==null?void 0:p.length)??0,((g=i.distributionByToken[c])==null?void 0:g.length)??0);return Array.from({length:d},(b,_)=>{var y,m;return Vn((y=s.distributionByToken[c])==null?void 0:y[_])-Vn((m=i.distributionByToken[c])==null?void 0:m[_])})});return{id:ro(s.id,i.id),layer:s.layer,head:-1,role:`Cell-wise retained-head difference · ${s.id} minus ${i.id}`,riskContribution:s.riskContribution-i.riskContribution,entropy:s.entropy-i.entropy,distributionByToken:o,difference:{selectedHeadId:s.id,baselineHeadId:i.id},memberHeadIds:[s.id,i.id]}}function Mm(t,n){const a=oo(n);return!!(a&&t.some(s=>s.id===a.selectedHeadId)&&t.some(s=>s.id===a.baselineHeadId))}function Pm(t,n){if(t.length===0)return;const a=Wm(t,n),s=Math.max(...t.map(o=>o.distributionByToken.length)),i=Array.from({length:s},(o,l)=>{const c=Math.max(0,...t.map(d=>{var p;return((p=d.distributionByToken[l])==null?void 0:p.length)??0}));return Array.from({length:c},(d,p)=>{const g=t.map(b=>{var _;return Vn((_=b.distributionByToken[l])==null?void 0:_[p])});return n==="max"?Math.max(...g):g.reduce((b,_,y)=>b+_*a[y],0)})}),r=o=>n==="max"?Math.max(...o):o.reduce((l,c,d)=>l+c*a[d],0);return{id:Rm(n),layer:t[0].layer,head:-1,role:`${An(n)} · derived from ${t.length} retained heads`,riskContribution:r(t.map(o=>o.riskContribution)),entropy:r(t.map(o=>o.entropy)),distributionByToken:i,aggregation:n,memberHeadIds:t.map(o=>o.id)}}function lo(t,n,a){var i;const s=n===void 0?"":a===void 0?`[${n}]`:`[${n},${a}]`;return t.difference?`derived.attention.difference[${t.difference.selectedHeadId}-${t.difference.baselineHeadId}]${s}`:t.rollout?`derived.attention.rollout.retained_mean_identity[L${t.rollout.layers.join(",L")};${t.rollout.memberHeadIds.join(",")}]${s}`:t.aggregation?`derived.attention.${t.aggregation}[${((i=t.memberHeadIds)==null?void 0:i.join(","))??"retained"}]${s}`:`blocks.${t.layer}.attn.hook_pattern[${t.head}]${s}`}function co(t){return t.rollout?"attention_retained_rollout_mean_identity":t.difference?"attention_retained_head_difference":t.aggregation?`attention_retained_${t.aggregation}`:"attention_probability"}function za(t,n){var i;if(t.rollout)return{label:"Retained attention rollout",method:`per-layer retained-head arithmetic mean, identity residual addition, row normalization, then matrix product through layer ${t.layer}`,semantics:"Client-derived descriptive path proxy over only the artifact-retained heads and available layers. It is not a full-model rollout, attribution, or causal evidence.",normalization:"A_hat_l = row_normalize(mean_retained(A_l) + I); R_l = A_hat_l × R_(l-1); R_-1 = I",kind:"derived_proxy"};if(t.difference)return{label:"Retained-head probability difference",method:`cell-wise ${t.difference.selectedHeadId} minus ${t.difference.baselineHeadId}`,semantics:"Client-derived signed difference between two retained artifact heads in the same layer; positive cells favor the selected head and negative cells favor the baseline. It is descriptive, not causal evidence.",normalization:"none; subtraction of stored raw softmax probabilities on the exact token axes",kind:"derived_proxy"};if(!t.aggregation)return n;const a=((i=t.memberHeadIds)==null?void 0:i.length)??0,s=t.aggregation==="mean"?"cell-wise arithmetic mean":t.aggregation==="max"?"cell-wise maximum":"cell-wise weighted mean with normalized inverse stored head entropy";return{label:An(t.aggregation),method:`${s} over ${a} retained artifact heads`,semantics:"Client-derived descriptive aggregate over the heads retained in this artifact; it is neither a full-model aggregate nor causal evidence.",normalization:"none; each source cell is aggregated from stored raw softmax probabilities",kind:"derived_proxy"}}function Wm(t,n){if(n!=="entropy_weighted")return t.map(()=>1/t.length);const a=t.map(i=>1/Math.max(1e-6,i.entropy)),s=a.reduce((i,r)=>i+r,0);return a.map(i=>i/s)}function Vn(t){return Number.isFinite(t)?Math.max(0,Math.min(1,t)):0}function zm(t){return Array.from({length:t},(n,a)=>Array.from({length:t},(s,i)=>a===i?1:0))}function Dm(t,n){return t.map((a,s)=>a.map((i,r)=>{var l,c;if(r>s)return 0;let o=0;for(let d=r;d<=s;d+=1)o+=(((l=t[s])==null?void 0:l[d])??0)*(((c=n[d])==null?void 0:c[r])??0);return o}))}function Ym(t){return t.length===0?0:t.reduce((n,a)=>n+a.reduce((s,i)=>i>0?s-i*Math.log(i):s,0),0)/t.length}const qm=mt(()=>ut(()=>import("./AttentionPatternMatrix-BvBtWlQ2.js"),__vite__mapDeps([0,1,2,3,4,5,6,7]),import.meta.url),"AttentionPatternMatrix"),Hm=mt(()=>ut(()=>import("./ResidualLogitLens-C9NFCh1i.js"),__vite__mapDeps([8,1,5]),import.meta.url),"ResidualLogitLens"),Fm=mt(()=>ut(()=>import("./MLPActivationMatrix-Bo8ox3Bx.js"),__vite__mapDeps([9,1,2,3,4,5,6,7]),import.meta.url),"MLPActivationMatrix"),Um=mt(()=>ut(()=>import("./SignedAttributionMatrix-uV6C6t9H.js"),__vite__mapDeps([10,1,2,3,4,5,7]),import.meta.url),"SignedAttributionMatrix"),Km=mt(()=>ut(()=>import("./NLAFidelityMatrix-Cn4agwcC.js"),__vite__mapDeps([11,1,2,3,4,5,7]),import.meta.url),"NLAFidelityMatrix"),Om=mt(()=>ut(()=>import("./AttributionJobPanel-BlZOKNCQ.js"),__vite__mapDeps([12,1,5,7]),import.meta.url),"AttributionJobPanel"),Bm=mt(()=>ut(()=>import("./NLAJobPanel-B3gg0q4Z.js"),__vite__mapDeps([13,1,5,7]),import.meta.url),"NLAJobPanel"),Vm=mt(()=>ut(()=>import("./PatchingJobPanel-C--uR2rf.js"),__vite__mapDeps([14,1,5,7]),import.meta.url),"PatchingJobPanel"),Qm=mt(()=>ut(()=>import("./PatchingCausalMatrix-za-NMj1Q.js"),__vite__mapDeps([15,1,4,5,7]),import.meta.url),"PatchingCausalMatrix"),Jm=mt(()=>ut(()=>import("./InterventionJobPanel-DLV5o6eH.js"),__vite__mapDeps([16,1,5,7]),import.meta.url),"InterventionJobPanel"),Gm=mt(()=>ut(()=>import("./InterventionComparison-01fWFLne.js"),__vite__mapDeps([17,1,5]),import.meta.url),"InterventionComparison"),Xm=mt(uo,"CompareDrawer");function uo(){return ut(()=>import("./CompareDrawer-B4C5S4Aw.js"),__vite__mapDeps([18,1,2,5,7]),import.meta.url)}function Rt(){uo().catch(()=>{})}const mo=u.createContext(Zi);function Xe(t,n="tokenRisk"){return Ye(t,n,"compact")}function ho(t){return Ka(t,"attribution","compact")}function kt(){return u.useContext(mo)}function Zm(){const t=new URLSearchParams(window.location.search).get("layout");return t==="focus"||t==="dense"?t:(window.sessionStorage.getItem("safelens-workspace-layout")??window.localStorage.getItem("safelens-workspace-layout"))==="dense"?"dense":"focus"}function Ri(){const t=window.location.pathname.slice(Ua.length).replace(/\/+$/,"");if(t==="dataset-test")return"dataset-test";if(t==="explorer")return"explorer";const n=new URLSearchParams(window.location.search);return["view","mode","run","sample","token","layer","head","neuron","track","metric"].some(s=>n.has(s))?"explorer":"home"}function eh(){const[t,n]=u.useState(Ri),a=Fc(Zi,t==="explorer"),s=a.activeRecord.run,[i,r]=u.useState(null),[o,l]=u.useState(null),c=Le.useRef(0),d=Le.useRef(null),p=Le.useRef(null),g=Le.useRef(a.activeRecord.key),b=Le.useCallback((m,x="selection")=>{d.current!==null&&window.clearTimeout(d.current),p.current!==null&&window.clearTimeout(p.current),d.current=window.setTimeout(()=>{const w=++c.current;l({id:w,kind:x,message:m,visible:!0}),p.current=window.setTimeout(()=>{l(N=>(N==null?void 0:N.id)===w?{...N,visible:!1}:N)},1900),d.current=null},x==="run"?0:60)},[]);u.useEffect(()=>{g.current!==a.activeRecord.key&&(g.current=a.activeRecord.key,b(sh(a.activeRecord.run,i,Oc(a.activeRecord.key)),"run"))},[b,a.activeRecord.key,a.activeRecord.run,i]),u.useEffect(()=>()=>{d.current!==null&&window.clearTimeout(d.current),p.current!==null&&window.clearTimeout(p.current)},[]),u.useEffect(()=>{function m(){n(Ri())}return window.addEventListener("popstate",m),()=>window.removeEventListener("popstate",m)},[]);function _(){window.history.pushState(null,"",Ss()),n("home")}function y(){window.history.pushState(null,"",Ss("dataset-test")),n("dataset-test")}return e.jsx(mo.Provider,{value:s,children:t==="home"?e.jsx(em,{records:a.records,activeRecord:a.activeRecord,remoteState:a.remoteState,onOpenDatasetTest:y,onSelectConversation:m=>a.selectRun(m,void 0,"none"),onRunReady:(m,x)=>{var w,N;return a.addGeneratedRun(m,x.id,void 0,{kind:x.kind==="prompt-run"?"prompt":x.kind,updateLocation:!1,conversationId:(w=m.metadata)==null?void 0:w.conversationId,turnIndex:(N=m.metadata)==null?void 0:N.turnIndex})},onRemoveRuns:a.removeRuns}):t==="dataset-test"?e.jsx(cm,{onOpenChat:_}):e.jsx(th,{run:s,library:a,pendingSession:i,onQueueSession:r,onSessionApplied:()=>r(null),onContextChange:b,contextNotice:o,onOpenHome:_},a.activeRecord.key)})}function th({run:t,library:n,pendingSession:a,onQueueSession:s,onSessionApplied:i,onContextChange:r,contextNotice:o,onOpenHome:l}){var ps,ys,fs,gs,_s,bs;const[c,d]=u.useState(!1),[p,g]=u.useState(Zm),[b,_]=u.useState(),[y,m]=u.useState(()=>new URLSearchParams(window.location.search).get("setup")==="prompt"),[x,w]=u.useState(!1),[N,A]=u.useState(!1),[T,k]=u.useState(!1),[S,L]=u.useState(!1),[M,F]=u.useState(!1),[V,W]=u.useState(!1),[K,H]=u.useState(!1),Z=Le.useRef(null),D=Le.useRef(null),C=Le.useRef(null),ne=Le.useRef(!0),pe=Le.useRef(null),R=Le.useRef(null),j=Le.useRef(null),ee=Le.useRef(null),ue=Le.useRef(null),oe=Le.useRef(null),O=Le.useRef(null),I=Le.useRef(null),z=Le.useRef(null),Y=Le.useRef(null),q=_o(t.tokens),$=t.layers[t.layers.length-1]??0,re=`${n.activeRecord.sourceName} · ${n.activeRecord.sourceType}${((ps=n.activeRecord.hydration)==null?void 0:ps.mode)==="partial"?" · range chunk":""}`,E=jm({runId:t.runId,sampleId:t.sampleId,tokenIndex:q[0]??((ys=t.tokens[0])==null?void 0:ys.index)??0,tokenIndices:t.tokens.map(v=>v.index),layers:t.layers,layer:$,view:"overview",headId:((fs=t.attentionHeads.find(v=>v.layer===$))==null?void 0:fs.id)??"",nlaComponent:((gs=t.nla.find(v=>v.layer===$))==null?void 0:gs.component)??"resid_post",neuronId:((_s=t.mlpNeurons.find(v=>v.layer===$))==null?void 0:_s.id)??"",trackName:((bs=t.attributionMethods.find(v=>v.available))==null?void 0:bs.id)??"",metric:"residual_direction",initialPinnedItems:rh(t,q,$,re)}),{state:Q}=E,U=Q.tokenIndex,de=Q.sourceTokenIndex??U,ae=Q.layer,ce=Q.nlaComponent,P=Q.view,_e=Lh(P),ie=vh(_e,Q.metric),be=Q.headId,se=Q.attentionEdgeMode,te=Q.neuronId,le=Q.trackName,he=Q.pinnedItems,[ge,ve]=u.useState(null),[qe,me]=u.useState(null),[Ie,Ce]=u.useState("top"),[Ue,Qe]=u.useState({mode:"token",metric:"risk",query:""}),[At,Nt]=u.useState({}),je=n.viewHydration(P,ae,U,de),Nn=n.viewHydration("nla",ae,U);ll({rootRef:z,view:P,ready:je.ready}),u.useEffect(()=>{var v,J;!a||a.workspace.runId!==t.runId||a.workspace.sampleId!==t.sampleId||(E.restoreSession(zh(a,t,Q)),Ce(a.filters.evidence),Qe(Dh(a,t)),Nt(Yh(a.matrices)),_(a.pinnedItems.some(ke=>{var Te;return ke.id===((Te=a.compare)==null?void 0:Te.baselineId)})?(v=a.compare)==null?void 0:v.baselineId:(J=a.pinnedItems[0])==null?void 0:J.id),d(!1),w(!1),n.setMessage({tone:"success",title:"Analysis session restored",details:[`${t.runId} / ${t.sampleId} · ${Oe(a.selection.view)}`]}),i())},[a,t.runId,t.sampleId]),u.useEffect(()=>{n.ensureViewHydrated(P,ae,U,de)},[n.activeRecord.key,P,ae,U,de]),u.useEffect(()=>{var v;he.some(J=>J.id===b)||_((v=he[0])==null?void 0:v.id)},[b,he]);const _t=u.useMemo(()=>t.attentionHeads.filter(v=>v.layer===ae),[t.attentionHeads,ae]),Xt=u.useMemo(()=>t.mlpNeurons.filter(v=>v.layer===ae),[t.mlpNeurons,ae]),ht=!!as(be)&&je.partial,we=u.useMemo(()=>ht?_t[0]??t.attentionHeads[0]:Ci(_t,be,t.attentionHeads,ae,t.layers)??_t[0]??t.attentionHeads[0],[_t,ht,t.attentionHeads,t.layers,be,ae]),We=t.attributionMethods.find(v=>v.id===le)??t.attributionMethods.find(v=>v.available)??t.attributionMethods[0],Mt=We.rows.find(v=>v.layer===ae)??We.rows[0],Pt={name:We.label,values:(Mt==null?void 0:Mt.values)??t.tokens.map(()=>0)},et=t.tokens[U],Zt=t.residualCells.find(v=>v.layer===ae&&v.tokenIndex===U),pt=Qn(t.nla,U,ae,ce),Re=Xt.find(v=>v.id===te)??[...Xt].sort((v,J)=>Math.abs(J.activationsByToken[U]??0)-Math.abs(v.activationsByToken[U]??0))[0],Cn=u.useMemo(()=>t.tokens.reduce((v,J)=>Math.max(v,J.risk),0),[t.tokens]),X=u.useMemo(()=>t.tokens.reduce((v,J)=>v+J.attribution,0)/Math.max(1,t.tokens.length),[t.tokens]),Me=!Nn.ready||!pt||pt.status==="unavailable"?"n/a":Xe(pt.cosine,"nla_cosine"),De=t.tokens.findIndex(v=>v.index===U),rt=je.ready?_n({run:t,view:P,selectedToken:U,selectedSourceToken:de,selectedLayer:ae,selectedNlaComponent:ce,selectedHead:we,selectedNeuron:Re,selectedAttributionMethod:We,metric:Q.metric,normalization:Q.normalization,sourceArtifact:`${n.activeRecord.sourceName} · ${n.activeRecord.sourceType}${je.partial?" · range chunk":""}`}):ih(t,P,ae,U,je.error,je.cancelled),bt=Eh(P,rt),Rn=he.filter(v=>v.runId===t.runId&&v.sampleId===t.sampleId).map(v=>v.tokenIndex),ko=cs(U).id,Wt=he.some(v=>v.id===ko),en=je.ready&&!ht&&rt.status==="available"&&(P!=="attribution"||We.available)&&(P!=="nla"||(pt==null?void 0:pt.status)==="available")&&(P!=="intervention"||!!t.intervention),Ln=p==="dense"||V,tn=$h({view:P,tokenText:et.text,tokenIndex:U,sourceTokenIndex:de,tokenRange:Q.tokenRange,layer:ae,metric:Q.metric,normalization:Q.normalization,headId:we.id,neuronId:Re==null?void 0:Re.id,nlaComponent:ce,attributionMethod:We.label,attentionEdgeMode:se}),rs=Le.useRef(tn.signature);u.useEffect(()=>{rs.current!==tn.signature&&(rs.current=tn.signature,r(tn.message))},[tn.message,tn.signature,r]),u.useEffect(()=>{x||A(!1)},[x]),u.useEffect(()=>{var v;x&&((v=O.current)==null||v.scrollTo({top:0,behavior:"auto"}))},[N,x]),u.useEffect(()=>{function v(Te){const Ae=I.current;if(!Ae||Ae.pointerId!==Te.pointerId)return;const xe=Ae.startY-Te.clientY;xe>=48?(I.current=null,A(!0)):xe<=-48&&(I.current=null,A(!1))}function J(Te){const Ae=I.current;if(!Ae||Ae.pointerId!==Te.pointerId)return;I.current=null;const xe=Ae.startY-Te.clientY;xe>=48&&A(!0),xe<=-48&&A(!1)}function ke(Te){var Ae;((Ae=I.current)==null?void 0:Ae.pointerId)===Te.pointerId&&(I.current=null)}return window.addEventListener("pointermove",v),window.addEventListener("pointerup",J),window.addEventListener("pointercancel",ke),()=>{window.removeEventListener("pointermove",v),window.removeEventListener("pointerup",J),window.removeEventListener("pointercancel",ke)}},[]),Un({open:y,dialogRef:oe,initialFocusRef:ee,returnFocusRef:D,onClose:()=>m(!1)}),Un({open:x,dialogRef:O,initialFocusRef:ue,returnFocusRef:C,restoreFocusRef:ne,onClose:()=>w(!1)}),u.useEffect(()=>{!ht&&(!je.partial||P==="attention"&&je.ready)&&we.id!==be&&E.selectHead(we.id,"replace")},[je.partial,je.ready,ht,we.id,be,P]),u.useEffect(()=>{if(P!=="attention"||!ht)return;const v=`${n.activeRecord.key}:${ae}`;Y.current!==v&&vo(v)},[n.activeRecord.key,ht,ae,P]),u.useEffect(()=>{(!je.partial||P==="mlp"&&je.ready)&&Re&&Re.id!==te&&E.selectNeuron(Re.id,"replace")},[je.partial,je.ready,te,Re==null?void 0:Re.id,P]),u.useEffect(()=>{(!je.partial||P==="attribution"&&je.ready)&&We.id!==le&&E.selectTrack(We.id,"replace")},[je.partial,je.ready,We.id,le,P]),u.useEffect(()=>{function v(J){if(J.defaultPrevented||c||y||x||T)return;const ke=J.target,Te=(ke==null?void 0:ke.closest("input, textarea, select, [contenteditable='true']"))||(ke==null?void 0:ke.isContentEditable);if(J.altKey&&J.shiftKey&&!J.ctrlKey&&!J.metaKey&&J.key.toLowerCase()==="c"){if(Te||he.length===0)return;J.preventDefault(),j.current=pe.current,Rt(),d(!0);return}if(ke!=null&&ke.closest("input, textarea, select, button, a, [role='button'], [role='tab'], [role='radio'], [role='grid']")||Te||J.key!=="ArrowLeft"&&J.key!=="ArrowRight")return;const Ae=J.key==="ArrowLeft"?-1:1,xe=Math.max(0,Math.min(t.tokens.length-1,De+Ae));if(xe===De)return;J.preventDefault();const ze=t.tokens[xe].index;E.selectToken(ze),Li(ze,me)}return window.addEventListener("keydown",v),()=>window.removeEventListener("keydown",v)},[c,x,y,he.length,T,t.tokens,De]);function os(v){lt(v)}function lt(v){E.selectToken(v),p==="focus"&&(L(!0),F(!1)),jt("selection-commit",{view:P,token:v}),Li(v,me)}function ls(v){const J=Wh(v);if(J){if(ne.current=!1,w(!1),E.selectView(J.view),!J.anchorId){window.requestAnimationFrame(()=>{var ke;(ke=z.current)==null||ke.scrollIntoView({block:"start"})});return}cn(J.anchorId)}}async function cn(v){if(w(!1),H(!0),je.partial)try{await n.loadFullActiveRun()}catch(J){n.setMessage({tone:"error",title:"Experiment setup could not be opened",details:[J instanceof Error?J.message:"The complete Run could not be loaded."]});return}window.requestAnimationFrame(()=>bo(v))}async function Ve(v,J=ae,ke={}){if(!en)return;const Te=ke.sourceTokenIndex??de,Ae=ke.neuronId?t.mlpNeurons.find(ze=>ze.id===ke.neuronId):Re;let xe=cs(v,J,ke);if(he.some(ze=>ze.id===xe.id)){E.togglePin(xe);return}if(P==="attention"&&je.partial)try{const ze=await n.loadFullActiveRun(),Je=ze.attentionHeads.filter(tt=>tt.layer===J),Fe=Ci(Je,we.id,ze.attentionHeads,J,ze.layers);if(!Fe)throw new Error(`Attention head ${we.id} is missing from the complete artifact.`);const Ct=ze.tokens.filter(tt=>tt.index<=v),Ne=yn({kind:"attention_source_profile",label:`${St(Fe)} · destination token ${v}`,axis:"source_token",signed:!!Fe.difference,tokens:Ct,values:Fe.distributionByToken[v]??[],preserveTokenIndex:Te}),He=Fe.difference?void 0:Di(Fe,ze.tokens,Te,v);if(!Ne||!Fe.difference&&!He)throw new Error("The complete artifact does not contain a valid attention matrix.");xe={...xe,profile:Ne,...He?{matrix:He}:{},assessment:rn(_n({run:ze,view:P,selectedToken:v,selectedSourceToken:Te,selectedLayer:J,selectedNlaComponent:ce,selectedHead:Fe,selectedNeuron:Re,selectedAttributionMethod:We,metric:xe.metric,normalization:xe.normalization,sourceArtifact:`${n.activeRecord.sourceName} · ${n.activeRecord.sourceType} · full artifact`}))}}catch(ze){n.setMessage({tone:"error",title:"Attention matrix pin failed",details:[ze instanceof Error?ze.message:"The complete attention artifact could not be loaded."]});return}if(P==="mlp"&&je.partial)try{const ze=await n.loadFullActiveRun(),Je=ze.mlpNeurons.find(He=>He.id===(Ae==null?void 0:Ae.id));if(!Je)throw new Error(`MLP neuron ${(Ae==null?void 0:Ae.id)??"unknown"} is missing from the complete artifact.`);const Fe=ba(Q.metric),Ct=Je.activationsByToken.map(He=>Yn(He,Je.maxAbsoluteActivation,Fe)),Ne=yn({kind:"mlp_activation_profile",label:`${Je.id} · ${Mi(Fe)}`,axis:"token",signed:Fe==="mlp_signed_activation",tokens:ze.tokens,values:Ct,preserveTokenIndex:v});if(!Ne)throw new Error("The complete artifact does not contain a valid MLP activation profile.");xe={...xe,profile:Ne,assessment:rn(_n({run:ze,view:P,selectedToken:v,selectedSourceToken:Te,selectedLayer:J,selectedNlaComponent:ce,selectedHead:we,selectedNeuron:Je,selectedAttributionMethod:We,metric:xe.metric,normalization:xe.normalization,sourceArtifact:`${n.activeRecord.sourceName} · ${n.activeRecord.sourceType} · full artifact`}))}}catch(ze){n.setMessage({tone:"error",title:"MLP profile pin failed",details:[ze instanceof Error?ze.message:"The complete MLP artifact could not be loaded."]});return}E.togglePin(xe)}async function vo(v=`${n.activeRecord.key}:${ae}`){var J;Y.current=v;try{await n.loadFullActiveRun(),Y.current===v&&(Y.current=null)}catch(ke){if(Y.current!==v)return;Y.current=null;const Te=(J=_t[0])==null?void 0:J.id;Te&&E.selectHead(Te,"replace"),n.setMessage({tone:"error",title:"Attention rollout loading failed",details:[ke instanceof Error?ke.message:"The complete attention artifact could not be loaded."]})}}function jo(){var J;Y.current=null,n.cancelRemote();const v=(J=_t[0])==null?void 0:J.id;v&&E.selectHead(v,"replace")}function ds(v){if(v.runId===t.runId&&v.sampleId===t.sampleId){E.restorePin(v);return}n.selectRun(xt(v),v)}function cs(v,J=ae,ke={}){var ks,vs;const Te=t.tokens.find(nt=>nt.index===v)??t.tokens[0],Ae=ke.sourceTokenIndex??de,xe=ke.neuronId?t.mlpNeurons.find(nt=>nt.id===ke.neuronId):Re,ze=ke.nlaComponent??ce,Je=We.rows.find(nt=>nt.layer===J)??Mt,Fe=go(t,_e,ie).find(nt=>nt.row===J&&nt.column===v),Ct=(ks=t.patching)==null?void 0:ks.cells.find(nt=>nt.layer===J&&nt.tokenIndex===v),Ne=t.intervention,He=Qn(t.nla,v,J,ze),tt=P==="overview"?"tokenRisk":P==="attention"?co(we):P==="mlp"?ba(Q.metric):P==="attribution"?le:P==="nla"||P==="patching"?Q.metric:P==="intervention"?"intervention_logit_delta":ie,la=P==="attention"||P==="intervention"||P==="mlp"&&tt!=="mlp_normalized_activation"?"raw":Q.normalization,Io=P==="overview"?Te.risk:P==="attention"?((vs=we.distributionByToken[v])==null?void 0:vs[Ae])??0:P==="mlp"?Yn((xe==null?void 0:xe.activationsByToken[v])??0,(xe==null?void 0:xe.maxAbsoluteActivation)??1,tt):P==="attribution"?(Je==null?void 0:Je.values[v])??0:P==="nla"?xa(tt)==="mse"?(He==null?void 0:He.mse)??0:xa(tt)==="fve"?(He==null?void 0:He.fve)??0:(He==null?void 0:He.cosine)??0:P==="patching"?xo(Ct,Q.metric)??0:P==="intervention"?(Ne==null?void 0:Ne.deltas.targetLogit)??0:Q.normalization==="raw"?(Fe==null?void 0:Fe.rawValue)??0:(Fe==null?void 0:Fe.value)??0,xs=P==="attention"?we.id:void 0,ws=P==="mlp"?xe==null?void 0:xe.id:void 0,So=P==="attribution"?le:void 0,To=P==="attribution"?{label:We.label,method:We.id,semantics:We.description,normalization:We.normalization,kind:We.evidenceKind}:P==="nla"?{label:"NLA fidelity",method:"exact NLA decoder reconstruction",semantics:"Exact token/layer/component reconstruction fidelity for a compatible profile.",normalization:"stored method metric",kind:"safety_method"}:P==="patching"?ss(t,Q.metric):P==="intervention"?is(t):P==="attention"?za(we,t.metricProvenance.attentionHeatmap):Pi(t,P,tt),Ao=P==="attention"?lo(we):P==="mlp"?`layer_${(xe==null?void 0:xe.layer)??J}.post[:, ${(xe==null?void 0:xe.neuron)??0}]`:P==="attribution"?Je==null?void 0:Je.sourceKey:P==="nla"?He==null?void 0:He.source:P==="patching"?Ct==null?void 0:Ct.sourceKey:P==="intervention"?Ne==null?void 0:Ne.vector.sourceKey:(Fe==null?void 0:Fe.sourceKey)??`layer_${J}.resid_post[${v}]`,No=P==="attention"&&!je.partial?yn({kind:"attention_source_profile",label:`${St(we)} · destination token ${v}`,axis:"source_token",signed:!!we.difference,tokens:t.tokens.filter(nt=>nt.index<=v),values:we.distributionByToken[v]??[],preserveTokenIndex:Ae}):P==="attribution"&&We.signed?yn({kind:"signed_attribution_profile",label:`${We.label} · L${J}`,axis:"token",signed:!0,tokens:t.tokens,values:(Je==null?void 0:Je.values)??[],preserveTokenIndex:v}):P==="mlp"&&xe&&!je.partial?yn({kind:"mlp_activation_profile",label:`${xe.id} · ${Mi(tt)}`,axis:"token",signed:tt==="mlp_signed_activation",tokens:t.tokens,values:xe.activationsByToken.map(nt=>Yn(nt,xe.maxAbsoluteActivation,tt)),preserveTokenIndex:v}):void 0,Co=P==="attention"&&!je.partial&&!we.difference?Di(we,t.tokens,Ae,v):void 0,Ro=P==="intervention"&&Ne?{schemaVersion:"1.0",sourceRun:Ne.sourceRun,layer:Ne.layer,component:Ne.component,scale:Ne.scale,positionStart:Ne.positionStart,positionEnd:Ne.positionEnd,targetTokenId:Ne.targetTokenId,targetTokenText:Ne.targetTokenText,seed:Ne.seed,maxNewTokens:Ne.maxNewTokens,temperature:Ne.temperature,original:{text:Ne.original.text,tokens:Ne.original.tokens,targetLogit:Ne.original.targetLogit,lexicalRisk:Ne.original.lexicalRisk},steered:{text:Ne.steered.text,tokens:Ne.steered.tokens,targetLogit:Ne.steered.targetLogit,lexicalRisk:Ne.steered.lexicalRisk},tokenEditDistance:Ne.deltas.tokenEditDistance,generationChanged:Ne.deltas.generationChanged,diff:Ne.diff}:void 0,Lo=rn(_n({run:t,view:P,selectedToken:v,selectedSourceToken:Ae,selectedLayer:J,selectedNlaComponent:ze,selectedHead:we,selectedNeuron:xe,selectedAttributionMethod:We,metric:tt,normalization:la,sourceArtifact:`${n.activeRecord.sourceName} · ${n.activeRecord.sourceType}${je.partial?" · range chunk":""}`}));return{id:[t.runId,t.sampleId,v,J,P,tt,la,xs??"-",ws??"-",P==="attention"?Ae:P==="nla"?ze:"-"].join(":"),runId:t.runId,sampleId:t.sampleId,tokenIndex:v,tokenText:Te.text,tokenId:Te.tokenId,tokenSource:Te.source,modelName:t.modelName,modelSource:t.modelSource,layer:J,view:P,component:P==="nla"?(He==null?void 0:He.component)??ze:_e,metric:tt,value:Io,normalization:la,headId:xs,neuronId:ws,trackName:So,sourceTokenIndex:P==="attention"?Ae:void 0,sourceKey:Ao,provenance:To,profile:No,matrix:Co,generation:Ro,assessment:Lo,capturedAt:new Date().toISOString()}}function $n(){var Ae,xe;const v={exportedAt:new Date().toISOString(),runId:t.runId,sampleId:t.sampleId,model:{name:t.modelName,source:t.modelSource},selection:{view:P,normalization:Q.normalization,tokenRange:Q.tokenRange,token:et,layer:ae,component:_e,nlaComponent:P==="nla"?ce:void 0,attentionHead:_e==="attention"?je.partial?{id:we.id,layer:we.layer,head:we.head,role:we.role,entropy:we.entropy,riskContribution:we.riskContribution,aggregation:we.aggregation,difference:we.difference,rollout:we.rollout,memberHeadIds:we.memberHeadIds,partial:!0}:we:void 0,attentionPair:P==="attention"?{sourceToken:t.tokens[de],destinationToken:et,probability:we.difference?void 0:((Ae=we.distributionByToken[U])==null?void 0:Ae[de])??0,probabilityDelta:we.difference?((xe=we.distributionByToken[U])==null?void 0:xe[de])??0:void 0,aggregation:we.aggregation,difference:we.difference,rollout:we.rollout,memberHeadIds:we.memberHeadIds}:void 0,mlpNeuron:_e==="mlp"&&Re?je.partial?{id:Re.id,layer:Re.layer,neuron:Re.neuron,label:Re.label,selectedActivation:Re.activationsByToken[U],maxAbsoluteActivation:Re.maxAbsoluteActivation,partial:!0}:Re:void 0,nla:pt,residual:Zt,attributionTrack:je.partial?{name:Pt.name,tokenIndex:U,value:Pt.values[U],partial:!0}:Pt,patching:t.patching,intervention:t.intervention,pinnedEvidence:he},metricProvenance:t.metricProvenance,activeMetricProvenance:P==="attention"?za(we,t.metricProvenance.attentionHeatmap):Pi(t,P,Q.metric),evidenceAssessment:rn(rt),dataAccess:je.partial?{protocol:"safelens-chunks-v1",scope:`${Oe(P)} · L${ae} · token ${U}`,completeArtifact:!1}:{completeArtifact:!0}},J=new Blob([JSON.stringify(v,null,2)],{type:"application/json"}),ke=URL.createObjectURL(J),Te=document.createElement("a");Te.href=ke,Te.download=`${t.runId}-token-${U}-layer-${ae}.json`,Te.click(),window.setTimeout(()=>URL.revokeObjectURL(ke),0)}async function us(){let v;try{v=await n.loadFullActiveRun()}catch(xe){n.setMessage({tone:"error",title:"Complete artifact export failed",details:[xe instanceof Error?xe.message:"The full Run could not be loaded."]});return}const J={schema_version:"1.0",run:{run_id:v.runId,model_name:v.modelName,model_source:v.modelSource},samples:[v],metrics:Object.keys(v.metricProvenance),artifacts:{embedded:!0}},ke=new Blob([JSON.stringify(J,null,2)],{type:"application/json"}),Te=URL.createObjectURL(ke),Ae=document.createElement("a");Ae.href=Te,Ae.download=`${v.runId}-${v.sampleId}-explorer-artifact.json`,Ae.click(),window.setTimeout(()=>URL.revokeObjectURL(Te),0)}function ms(){const{pinnedItems:v,...J}=Q,ke={kind:Va,schemaVersion:"1.0",exportedAt:new Date().toISOString(),workspace:{runId:t.runId,sampleId:t.sampleId,modelName:t.modelName,modelSource:t.modelSource,sourceName:n.activeRecord.sourceName,artifactId:n.activeRecord.artifactId},selection:J,pinnedItems:v,timeline:Ue,compare:{baselineId:b},activeEvidenceAssessment:rn(rt),matrices:At,filters:{evidence:Ie}},Te=new Blob([JSON.stringify(ke,null,2)],{type:"application/json"}),Ae=URL.createObjectURL(Te),xe=document.createElement("a");xe.href=Ae,xe.download=`${t.runId}-${t.sampleId}-analysis-session.json`,xe.click(),window.setTimeout(()=>URL.revokeObjectURL(Ae),0)}function hs(v){const J=xt(v.workspace);if(!n.records.some(ke=>ke.key===J)){n.setMessage({tone:"error",title:"Analysis session Run is not available",details:[`Load ${v.workspace.runId} / ${v.workspace.sampleId} before restoring this session.`]});return}s(v),m(!1),J!==n.activeRecord.key&&n.selectRun(J)}return e.jsx(cl,{snapshots:At,onChange:(v,J)=>Nt(ke=>({...ke,[v]:J})),children:e.jsxs("div",{className:`app-shell layout-${p}`,children:[e.jsx("a",{className:"skip-link",href:"#analysis-workspace",children:"Skip to analysis workspace"}),e.jsxs("header",{className:"topbar",children:[e.jsxs("button",{className:"brand-block",type:"button","aria-label":"Return to SafeLens home",onClick:l,children:[e.jsx("div",{className:"brand-mark",children:e.jsx(Bt,{size:22})}),e.jsxs("div",{children:[e.jsx("h1",{children:"SafeLens Local Explorer"}),e.jsx("p",{children:t.runId})]})]}),e.jsxs("div",{className:"run-status",title:"Select an available local run and sample",children:[e.jsx(vt,{size:15}),e.jsxs("div",{className:"run-status-selection",children:[e.jsxs("span",{className:"mobile-current-run",children:[e.jsx("em",{children:"Run"}),e.jsx("strong",{title:t.runId,children:t.runId})]}),e.jsxs("span",{className:"run-sample-selection",children:[e.jsx("em",{className:"mobile-run-context-label",children:"Sample"}),e.jsx(nr,{records:n.records,ariaLabel:"Quick run selector",value:n.activeRecord.key,onChange:n.selectRun,formatNativeLabel:v=>v.sampleId})]})]}),e.jsxs("b",{className:"run-layer-count",children:[t.layers.length," layers"]}),e.jsx("button",{ref:Z,className:"mobile-run-library-trigger","aria-label":"Open run library",title:"Open run library",onClick:v=>{D.current=v.currentTarget,m(!0)},children:e.jsx(vt,{size:16})})]}),e.jsxs("div",{className:"run-meta",children:[e.jsx(_a,{label:"Max safety proxy",shortLabel:"Safety max",value:Xe(Cn),tone:"danger"}),e.jsx(_a,{label:"Mean attention proxy",shortLabel:"Attention mean",value:Xe(X,"attention_probability"),tone:"blue"}),e.jsx(_a,{label:"NLA cosine",shortLabel:"NLA cosine",value:Me,tone:"green"})]}),e.jsxs("div",{className:"topbar-actions",children:[e.jsx("button",{className:"icon-button desktop-inspector-trigger",title:"Inspect selected evidence","aria-label":"Inspect selected evidence",onClick:v=>{C.current=v.currentTarget,w(!0)},children:e.jsx(ja,{size:18})}),e.jsx("button",{className:"icon-button layout-toggle",title:`Switch to ${p==="focus"?"dense":"focus"} layout`,"aria-label":`Switch to ${p==="focus"?"dense":"focus"} layout`,"aria-pressed":p==="dense",onClick:()=>g(v=>{const J=v==="focus"?"dense":"focus";return window.localStorage.setItem("safelens-workspace-layout",J),window.sessionStorage.setItem("safelens-workspace-layout",J),J}),children:e.jsx(Fa,{size:18})}),e.jsxs("button",{ref:pe,className:"icon-button compare-trigger",title:"Compare pinned evidence","aria-label":`Compare pinned evidence (${he.length})`,"aria-keyshortcuts":"Alt+Shift+C",onPointerEnter:Rt,onFocus:Rt,onClick:v=>{j.current=v.currentTarget,d(!0)},children:[e.jsx(yt,{size:18}),e.jsx("span",{children:he.length})]}),e.jsx("button",{className:"icon-button session-export",title:"Export analysis session","aria-label":"Export analysis session",onClick:ms,children:e.jsx(Vi,{size:18})}),e.jsx("button",{className:"icon-button artifact-export",title:"Export current Explorer artifact","aria-label":"Export current Explorer artifact",onClick:()=>void us(),children:e.jsx(Da,{size:18})}),e.jsx("button",{className:"icon-button current-evidence-export",title:"Export current evidence as JSON","aria-label":"Export current evidence as JSON",onClick:$n,children:e.jsx(qa,{size:18})}),e.jsx("button",{ref:R,className:"icon-button",title:"Open quick actions","aria-label":"Open quick actions",onClick:()=>k(!0),children:e.jsx(nl,{size:18})})]})]}),e.jsx(ah,{notice:o}),e.jsxs("div",{className:"workspace-context-bar",children:[e.jsxs("nav",{"aria-label":"Workspace breadcrumb",children:[e.jsx("button",{type:"button",onClick:l,children:"Home"}),e.jsx(gt,{size:13,"aria-hidden":"true"}),e.jsx("span",{children:"Interpretability Explorer"}),e.jsx(gt,{size:13,"aria-hidden":"true"}),e.jsx("strong",{children:Oe(P)})]}),e.jsxs("div",{className:"workspace-context-meta",children:[e.jsxs("span",{className:"context-run-pill",children:[e.jsx(vt,{size:13,"aria-hidden":"true"}),e.jsx("b",{children:t.modelName})]}),e.jsxs("span",{className:"context-state-pill",children:[e.jsx("span",{"aria-hidden":"true"}),n.activeRecord.sourceType==="bundled"?"Bundled cache":"Local workspace"]})]})]}),e.jsxs("main",{className:"workspace",children:[e.jsxs("aside",{className:"left-panel",children:[e.jsx(Ws,{records:n.records,activeRecord:n.activeRecord,message:n.message,remoteState:n.remoteState,onMessage:n.setMessage,onSelect:n.selectRun,onAdd:n.addRuns,onRemove:n.removeRun,onRestoreSession:hs,onRefreshRemote:()=>void n.refreshRemote(),onCancelRemote:n.cancelRemote}),e.jsx(ni,{run:t,onRunReady:(v,J)=>n.addGeneratedRun(v,J.id)}),e.jsxs("section",{className:"panel-section provenance-panel",children:[e.jsxs("div",{className:"section-heading",children:[e.jsx(Ut,{size:16}),e.jsx("span",{children:"Data provenance"})]}),e.jsx($i,{})]}),e.jsxs("section",{className:"panel-section",children:[e.jsxs("div",{className:"section-heading",children:[e.jsx(Ht,{size:16}),e.jsx("span",{children:"Evidence"})]}),e.jsx("div",{className:"evidence-list",children:q.map(v=>e.jsxs("button",{onClick:()=>os(v),children:[e.jsx("span",{children:t.tokens[v].text}),e.jsx("b",{children:Xe(t.tokens[v].risk)})]},v))})]})]}),e.jsxs("section",{id:"analysis-workspace",ref:z,className:"main-panel",tabIndex:-1,"aria-label":"Analysis workspace","aria-keyshortcuts":"ArrowLeft ArrowRight",children:[e.jsxs("div",{className:"main-header",children:[e.jsxs("div",{children:[e.jsx("h2",{children:p==="dense"?"Token Timeline":Oe(P)}),e.jsxs("p",{children:["token ",et.index," · id ",et.tokenId," · safety proxy"," ",Xe(et.risk)]})]}),e.jsxs("div",{className:"selection-trail","aria-label":"Current selection",children:[e.jsx("span",{children:et.text}),e.jsxs("span",{children:["L",ae]}),e.jsx("span",{children:wo(_e,we,Re)})]}),e.jsx(fm,{layers:t.layers,selectedLayer:ae,onSelect:E.selectLayer}),e.jsx(_m,{view:P,setView:E.selectView})]}),P!=="nla"&&e.jsx(ic,{run:t,selectedToken:U,selectedLayer:ae,selectedRange:Q.tokenRange,setSelectedToken:lt,setSelectedRange:E.selectRange,hoveredToken:ge,setHoveredToken:ve,pulseToken:qe,pinToken:Ve,pinned:Rn,timeline:Ue,onTimelineChange:Qe}),e.jsx(gm,{visible:p==="focus"&&S,tokenText:et.text,tokenIndex:U,layer:ae,score:Xe(et.risk),view:P,menuOpen:M,contextOpen:V,pinned:Wt,canPin:en,pinnedCount:he.length,onToggleMenu:()=>F(v=>!v),onSelectView:v=>{F(!1),H(!1),E.selectView(v),window.requestAnimationFrame(()=>{var J;(J=document.getElementById("analysis-panel"))==null||J.scrollIntoView({block:"start",behavior:"smooth"})})},onInspect:v=>{C.current=v,w(!0)},onToggleContext:()=>W(v=>!v),onPin:()=>void Ve(U),onPreloadCompare:Rt,onCompare:v=>{j.current=v,Rt(),d(!0)},onDismiss:()=>{L(!1),F(!1)}}),e.jsxs("div",{className:`mobile-selection-summary ${P==="nla"?"nla-selection-summary":""}`,role:"region","aria-label":"Current evidence actions",children:[e.jsxs("span",{children:[e.jsx("b",{children:P==="nla"?`P${U}`:et.text}),P==="nla"?"position":"token"]}),e.jsxs("span",{children:[e.jsxs("b",{children:["L",ae]}),"layer"]}),e.jsxs("span",{children:[e.jsx("b",{children:P==="nla"?ce:Xe(et.risk)}),P==="nla"?"component":"safety proxy"]}),e.jsx("button",{className:Wt?"active":"","aria-label":Wt?"Unpin current evidence":"Pin current evidence","aria-pressed":Wt,disabled:!en,title:Wt?"Unpin current evidence":"Pin current evidence",onClick:()=>Ve(U),children:e.jsx(Gn,{size:17})}),e.jsx("button",{"aria-label":`Open evidence comparison (${he.length})`,title:"Compare pinned evidence",disabled:!he.length,onPointerDown:Rt,onFocus:Rt,onClick:v=>{j.current=v.currentTarget,d(!0)},children:e.jsx(yt,{size:17})}),e.jsx("button",{"aria-label":"Open evidence inspector",title:"Open evidence inspector",onClick:v=>{C.current=v.currentTarget,w(!0)},children:e.jsx(ja,{size:17})})]}),je.ready?e.jsx(hh,{selectedToken:U,selectedSourceToken:de,selectedLayer:ae,view:P,component:_e,selectedHead:we,neuron:Re,nlaRow:pt,attributionMethod:We.label,attributionEvidenceKind:We.evidenceKind,attributionAvailable:We.available}):e.jsxs("div",{className:"hydration-selection-summary","aria-label":"Selected range loading status",children:[e.jsx(Be,{size:14}),e.jsxs("span",{children:[e.jsx("b",{children:Oe(P)})," L",ae," · token ",U]}),e.jsx("em",{children:je.error?"load failed":"loading range"})]}),e.jsx(ci,{resetKey:`${t.runId}:${t.sampleId}:${P}:${ae}:${we.id}:${(Re==null?void 0:Re.id)??"-"}:${le}`,viewLabel:Oe(P),onOpenOverview:()=>E.selectView("overview"),children:e.jsx(Le.Suspense,{fallback:e.jsx(lh,{view:P}),children:e.jsxs("div",{id:"analysis-panel",className:`analysis-grid ${P==="overview"?"overview-analysis-grid":""} ${P==="attention"?"attention-analysis-grid":""} ${P==="patching"||P==="intervention"?"patching-analysis-grid":""}`,role:"tabpanel","aria-labelledby":`analysis-tab-${P}`,children:[e.jsxs("div",{className:"left-analysis-stack",children:[p==="focus"&&K&&["attribution","patching","intervention"].includes(P)&&e.jsxs("div",{className:"focus-experiment-toolbar",role:"region","aria-label":"Experiment setup controls",children:[e.jsxs("span",{children:[e.jsx(Yt,{size:15})," Experiment setup"]}),e.jsx("button",{"aria-label":"Close experiment setup",onClick:()=>H(!1),children:e.jsx(at,{size:15})})]}),je.partial&&["attribution","patching","intervention"].includes(P)&&e.jsx(dh,{onLoad:()=>void n.loadFullActiveRun().catch(()=>{})}),!je.partial&&(p==="dense"||K)&&P==="attribution"&&e.jsx(Om,{run:t,onRunReady:(v,J)=>n.addGeneratedRun(v,J.id,{view:"attribution",trackName:"integrated_gradients",metric:"integrated_gradients",kind:"attribution"})}),P==="nla"&&e.jsx(Bm,{run:t,selectedToken:U,onRunReady:(v,J)=>n.addGeneratedRun(v,J.id,{view:"nla",metric:"nla_cosine",tokenIndex:J.request.positions[0],kind:"nla"})}),!je.partial&&(p==="dense"||K)&&P==="patching"&&e.jsx(Vm,{run:t,selectedToken:U,selectedLayer:ae,onRunReady:(v,J)=>n.addGeneratedRun(v,J.id,{view:"patching",metric:"patching_recovery",tokenIndex:J.request.positions[0],layer:J.request.layers[0],kind:"patching"})}),!je.partial&&(p==="dense"||K)&&P==="intervention"&&e.jsx(Jm,{run:t,selectedLayer:ae,selectedToken:U,onRunReady:(v,J)=>n.addGeneratedRun(v,J.id,{view:"intervention",metric:"intervention_logit_delta",tokenIndex:J.request.positionStart,layer:J.request.layer,kind:"intervention"})}),ht?e.jsx(ch,{layer:ae,onCancel:jo}):je.ready?P==="attention"?e.jsx(qm,{heads:_t,selectedHead:we,tokens:t.tokens,selectedSource:de,selectedDestination:U,edgeMode:se,selectedRange:Q.tokenRange,onHeadChange:E.selectHead,onEdgeModeChange:E.selectAttentionEdgeMode,onSelectPair:E.selectAttentionPair,onRangeSelect:E.selectRange,onHoverSource:ve,onPin:()=>Ve(U),onPinPair:(v,J)=>{Ve(J,ae,{sourceTokenIndex:v})}}):P==="mlp"?e.jsx(Fm,{tokens:t.tokens,neurons:Xt,selectedToken:U,selectedNeuronId:(Re==null?void 0:Re.id)??"",partialProfiles:je.partial,metric:ba(Q.metric),selectedRange:Q.tokenRange,onMetricChange:v=>{E.selectMetric(v),E.setNormalization(v==="mlp_normalized_activation"?"normalized":"raw")},onSelectToken:lt,onSelectNeuron:E.selectNeuron,onRangeSelect:E.selectRange,onHoverToken:ve,onPin:()=>Ve(U),onPinActivation:(v,J)=>{Ve(v,ae,{neuronId:J})}}):P==="nla"?e.jsx(Km,{rows:t.nla,compatibility:t.nlaCompatibility,layers:t.layers,tokens:t.tokens,selectedToken:U,selectedLayer:ae,selectedComponent:ce,metric:xa(Q.metric),selectedRange:Q.tokenRange,onMetricChange:v=>E.selectMetric(`nla_${v}`),onSelectCell:(v,J,ke)=>{E.selectLayer(v),E.selectNlaComponent(ke),lt(J)},onRangeSelect:E.selectRange,onHoverToken:ve,onPin:en?()=>Ve(U):void 0,onPinCell:(v,J,ke)=>{Ve(J,v,{nlaComponent:ke})}}):P==="attribution"?e.jsx(Um,{methods:t.attributionMethods,selectedMethod:We,tokens:t.tokens,selectedToken:U,selectedLayer:ae,normalization:Q.normalization,selectedRange:Q.tokenRange,onMethodChange:E.selectTrack,onNormalizationChange:E.setNormalization,onSelectCell:(v,J)=>{v>=0&&E.selectLayer(v),lt(J)},onRangeSelect:E.selectRange,onHoverToken:ve,onPin:()=>Ve(U),onPinCell:(v,J)=>{Ve(J,v>=0?v:ae)},onConfigureIntegratedGradients:()=>void cn("attribution-job")}):P==="patching"?t.patching?e.jsx(Qm,{experiment:t.patching,tokens:t.tokens,selectedToken:U,selectedLayer:ae,metric:qh(Q.metric),selectedRange:Q.tokenRange,onMetricChange:v=>E.selectMetric(`patching_${v}`),onSelectCell:(v,J)=>{E.selectLayer(v),lt(J)},onRangeSelect:E.selectRange,onPin:()=>Ve(U),onPinCell:(v,J)=>{Ve(J,v)}}):e.jsx(wn,{className:"surface patching-empty",icon:e.jsx(Yt,{size:20}),title:"No causal patch grid in this run",description:"Create an aligned corrupted prompt and measure the exact replacement effect in a derived Run.",facts:[{label:"Selection",value:`L${ae} / token ${U}`},{label:"Component",value:"residual stream"}],actionLabel:"Configure causal patching",actionIcon:e.jsx(Yt,{size:16}),onAction:()=>void cn("patching-job")}):P==="intervention"?t.intervention?e.jsx(Gm,{experiment:t.intervention,onPin:()=>Ve(U)}):e.jsx(wn,{className:"surface intervention-empty",icon:e.jsx($t,{size:20}),title:"No intervention comparison in this run",description:"Define a contrastive direction and generate a matched original-versus-steered derived Run.",facts:[{label:"Selection",value:`L${ae} / token ${U}`},{label:"Comparison",value:"matched generation"}],actionLabel:"Configure intervention",actionIcon:e.jsx($t,{size:16}),onAction:()=>void cn("intervention-job")}):e.jsx(ph,{selectedLayer:ae,selectedToken:U,hoveredToken:ge,setHoveredToken:ve,setSelectedLayer:E.selectLayer,setSelectedToken:lt,component:_e,metric:ie,normalization:Q.normalization,selectedRange:Q.tokenRange,setMetric:E.selectMetric,setNormalization:E.setNormalization,setSelectedRange:E.selectRange,pinCurrent:()=>Ve(U),pinCell:(v,J)=>Ve(J,v)}):e.jsx(oh,{view:P,loading:je.loading,error:je.error,cancelled:je.cancelled,onCancel:n.cancelRemote,onRetry:()=>n.ensureViewHydrated(P,ae,U,de)}),Ln&&je.ready&&P!=="patching"&&P!=="intervention"&&e.jsx(mh,{selectedToken:U,selectedLayer:ae,component:_e,selectedHead:we,neuron:Re,residualCell:Zt}),Ln&&e.jsx(uh,{metadata:t.metadata}),Ln&&e.jsx(kh,{pinned:he,restorePin:ds,availableRunKeys:new Set(n.records.map(v=>v.key)),openCompare:()=>d(!0)})]}),Ln&&je.ready&&P!=="patching"&&P!=="intervention"&&e.jsx(yh,{view:P,setSelectedView:E.selectView,selectedLayer:ae,setSelectedLayer:E.selectLayer,selectedToken:U,selectedNlaComponent:ce,selectedSourceToken:de,setSelectedToken:lt,setSelectedSourceToken:E.selectSourceToken,selectedHead:we,selectedHeadId:we.id,setSelectedHeadId:E.selectHead,selectedTrack:le,setSelectedTrack:E.selectTrack,selectedTrackData:Pt,selectedAttributionMethod:We,metric:ie,normalization:Q.normalization,residualCell:Zt,neuron:Re,evidenceFilter:Ie,setEvidenceFilter:Ce,onConfigureJob:v=>void cn(v)})]})})})]}),e.jsx("aside",{className:"right-panel",children:e.jsx(di,{evidence:rt,canPrevious:De>0,canNext:De<t.tokens.length-1,canPin:en,pinned:Wt,nextActions:bt,onPrevious:()=>lt(t.tokens[De-1].index),onNext:()=>lt(t.tokens[De+1].index),onPin:()=>Ve(U),onCompare:()=>{j.current=pe.current,w(!1),d(!0)},onExport:$n,onNextAction:ls})})]}),e.jsx(Ic,{open:T,returnFocusRef:R,context:{runId:t.runId,sampleId:t.sampleId,view:Oe(P),layer:ae,token:U,tokenText:et.text},pinnedCount:he.length,onClose:()=>k(!1),onOverview:()=>{k(!1),E.selectView("overview"),window.requestAnimationFrame(()=>{var v;return(v=z.current)==null?void 0:v.focus()})},onRuns:()=>{k(!1),D.current=R.current,window.requestAnimationFrame(()=>m(!0))},onTokenSearch:()=>{k(!1),window.requestAnimationFrame(()=>{var v;(v=document.getElementById("token-timeline-search"))==null||v.focus()})},onCompare:()=>{k(!1),j.current=pe.current,Rt(),window.requestAnimationFrame(()=>d(!0))},onExportSession:()=>{k(!1),ms()},onExportArtifact:()=>{k(!1),us()},onExportEvidence:()=>{k(!1),$n()}}),y&&e.jsx("div",{className:"mobile-library-backdrop",onMouseDown:v=>{v.target===v.currentTarget&&m(!1)},children:e.jsxs("aside",{ref:oe,className:"mobile-library-drawer",role:"dialog",tabIndex:-1,"aria-modal":"true","aria-labelledby":"mobile-library-title",children:[e.jsxs("header",{children:[e.jsxs("div",{children:[e.jsx("span",{children:"Data workspace"}),e.jsx("h2",{id:"mobile-library-title",children:"Runs and samples"})]}),e.jsx("button",{ref:ee,"aria-label":"Close run library",onClick:()=>m(!1),children:e.jsx(at,{size:18})})]}),e.jsx(Ws,{records:n.records,activeRecord:n.activeRecord,message:n.message,remoteState:n.remoteState,onMessage:n.setMessage,onSelect:v=>{n.selectRun(v),m(!1)},onAdd:(v,J,ke)=>{const Te=n.addRuns(v,J,ke);return Te&&m(!1),Te},onRemove:n.removeRun,onRestoreSession:hs,onRefreshRemote:()=>void n.refreshRemote(),onCancelRemote:n.cancelRemote}),e.jsx(ni,{run:t,onRunReady:(v,J)=>{n.addGeneratedRun(v,J.id),m(!1)}}),e.jsxs("section",{className:"panel-section mobile-drawer-secondary",children:[e.jsxs("div",{className:"section-heading",children:[e.jsx(Ut,{size:16}),e.jsx("span",{children:"Data provenance"})]}),e.jsx($i,{})]}),e.jsxs("section",{className:"panel-section mobile-drawer-secondary",children:[e.jsxs("div",{className:"section-heading",children:[e.jsx(Ht,{size:16}),e.jsx("span",{children:"Evidence"})]}),e.jsx("div",{className:"evidence-list",children:q.map(v=>e.jsxs("button",{onClick:()=>{os(v),m(!1)},children:[e.jsx("span",{children:t.tokens[v].text}),e.jsx("b",{children:Xe(t.tokens[v].risk)})]},v))})]})]})}),x&&e.jsx("div",{className:"mobile-inspector-backdrop",onMouseDown:v=>{v.target===v.currentTarget&&w(!1)},children:e.jsxs("aside",{ref:O,className:"mobile-inspector-drawer","data-detail-level":N?"full":"compact",role:"dialog",tabIndex:-1,"aria-modal":"true","aria-labelledby":"mobile-inspector-title",children:[e.jsxs("header",{onPointerDown:v=>{v.button!==0||v.target.closest("button")||(I.current={pointerId:v.pointerId,startY:v.clientY},v.currentTarget.setPointerCapture(v.pointerId))},children:[e.jsxs("div",{children:[e.jsx("span",{children:N?"Full provenance":"Selected evidence"}),e.jsx("h2",{id:"mobile-inspector-title",children:"Evidence details"})]}),e.jsxs("div",{className:"mobile-inspector-header-actions",children:[e.jsx("button",{"aria-label":N?"Show compact evidence summary":"Show full evidence details","aria-expanded":N,onClick:()=>A(v=>!v),children:N?e.jsx(Xn,{size:18}):e.jsx(Ji,{size:18})}),e.jsx("button",{ref:ue,"aria-label":"Close evidence inspector",onClick:()=>w(!1),children:e.jsx(at,{size:18})})]})]}),e.jsx(di,{evidence:rt,canPrevious:De>0,canNext:De<t.tokens.length-1,canPin:en,pinned:Wt,nextActions:bt,onPrevious:()=>lt(t.tokens[De-1].index),onNext:()=>lt(t.tokens[De+1].index),onPin:()=>Ve(U),onCompare:()=>{j.current=C.current,w(!1),d(!0)},onExport:$n,onNextAction:ls,detailLevel:N?"full":"compact"})]})}),c&&e.jsx(ci,{variant:"dialog",resetKey:`${xt(t)}:${he.map(v=>v.id).join("|")}:${b??"-"}`,viewLabel:"Evidence comparison",onDismiss:()=>{d(!1),window.requestAnimationFrame(()=>{var v;return(v=j.current)==null?void 0:v.focus()})},children:e.jsx(Le.Suspense,{fallback:e.jsx(nh,{}),children:e.jsx(Xm,{open:!0,pinned:he,tokens:t.tokens,metricProvenance:t.metricProvenance,currentRunKey:xt(t),availableRunKeys:new Set(n.records.map(v=>v.key)),baselineId:b,returnFocusRef:j,onClose:()=>d(!1),onRestore:ds,onRemove:E.togglePin,onBaselineChange:_})})})]})})}function nh(){return e.jsx("div",{className:"compare-backdrop",children:e.jsxs("aside",{className:"compare-drawer compare-drawer-loading",role:"dialog","aria-modal":"true","aria-label":"Loading evidence comparison",children:[e.jsx(Be,{size:20}),e.jsx("strong",{children:"Preparing evidence comparison"}),e.jsx("span",{role:"status",children:"Loading comparison visualization."})]})})}function ah({notice:t}){const n=(t==null?void 0:t.kind)==="run"?"Run changed":"Context updated";return e.jsxs(e.Fragment,{children:[e.jsx("div",{className:"visually-hidden",role:"log","aria-live":"polite","aria-atomic":"true","aria-label":"Analysis context changes",children:t?`${n}: ${t.message}`:""}),e.jsxs("div",{className:`context-change-notice${t!=null&&t.visible?" visible":""}`,"aria-hidden":"true","data-kind":(t==null?void 0:t.kind)??"selection",children:[e.jsx(ot,{size:18}),e.jsx("span",{children:n}),e.jsx("strong",{children:(t==null?void 0:t.message)??""})]})]})}function sh(t,n,a){var y;const s=["overview","residual","attention","mlp","nla","patching","intervention","attribution"],i=new URLSearchParams(window.location.search),r=(n==null?void 0:n.workspace.runId)===t.runId&&n.workspace.sampleId===t.sampleId,o=r?n.selection.view:i.get("view"),l=s.includes(o)?o:"overview",c=r?n.selection.targetTokenIndex??n.selection.tokenIndex:ga(i,"target")??ga(i,"token"),d=c!==void 0&&t.tokens.some(m=>m.index===c)?c:_o(t.tokens)[0]??((y=t.tokens[0])==null?void 0:y.index)??0,p=r?n.selection.layer:ga(i,"layer"),g=p!==void 0&&t.layers.includes(p)?p:t.layers[t.layers.length-1]??0,b=r||["view","token","target","layer","head","neuron","track","metric","normalization"].some(m=>i.has(m)),_=r?"session context":a==="fresh"?"fresh selection":a==="restored"||b?"restored context":"fresh selection";return`${t.sampleId} · ${Oe(l)} · T${d} · L${g} · ${_}`}function ga(t,n){const a=t.get(n);return a!==null&&/^\d+$/.test(a)?Number(a):void 0}function ih(t,n,a,s,i,r=!1){var o;return{title:((o=t.tokens[s])==null?void 0:o.text)||`token ${s}`,subtitle:`${Oe(n)} · L${a}`,status:i?"failed":r?"cancelled":"loading",statusReason:i??(r?"Artifact range loading was cancelled.":"Loading the selected artifact range."),primaryLabel:Oe(n),primaryValue:i?"load failed":r?"cancelled":"loading",rawValue:"pending",displayValue:"pending",units:"pending",evidenceClass:"raw",method:"artifact chunk hydration",normalization:"pending",cacheKey:"",shape:"current viewport range",sourceArtifact:"workspace chunk protocol",runId:t.runId,sampleId:t.sampleId,modelName:t.modelName,warnings:i?[i]:[],reproduction:{runId:t.runId,sampleId:t.sampleId,view:n,layer:a,token:s}}}function rn(t){return{schemaVersion:"1.0",status:t.status,statusReason:t.statusReason,primaryLabel:t.primaryLabel,primaryValue:t.primaryValue,rawValue:t.rawValue,displayValue:t.displayValue,units:t.units,evidenceClass:t.evidenceClass,method:t.method,normalization:t.normalization,cacheKey:t.cacheKey,shape:t.shape,sourceArtifact:t.sourceArtifact,warnings:[...t.warnings],reproduction:structuredClone(t.reproduction)}}function rh(t,n,a,s){const i=t.attentionHeads.find(l=>l.layer===a),r=t.mlpNeurons.find(l=>l.layer===a),o=t.attributionMethods.find(l=>l.available)??t.attributionMethods[0];return n.map(l=>{const c=t.tokens.find(p=>p.index===l)??t.tokens[0],d={id:`${t.runId}:${t.sampleId}:${l}:${a}:overview:tokenRisk:normalized:-:-:-`,runId:t.runId,sampleId:t.sampleId,tokenIndex:l,tokenText:c.text,tokenId:c.tokenId,tokenSource:c.source,modelName:t.modelName,modelSource:t.modelSource,layer:a,view:"overview",component:"resid_post",metric:"tokenRisk",value:c.risk,normalization:"normalized",sourceKey:`layer_${a}.resid_post[${l}]`,provenance:t.metricProvenance.tokenRisk};return!i||!o?d:{...d,assessment:rn(_n({run:t,view:"overview",selectedToken:l,selectedSourceToken:l,selectedLayer:a,selectedNlaComponent:"resid_post",selectedHead:i,selectedNeuron:r,selectedAttributionMethod:o,metric:"tokenRisk",normalization:"normalized",sourceArtifact:s}))}})}function oh({view:t,loading:n,error:a,cancelled:s,onCancel:i,onRetry:r}){const o=Le.useRef(null);Le.useEffect(()=>{!s||o.current===null||(jt("cancel-feedback",{latencyMs:performance.now()-o.current}),o.current=null)},[s]);function l(){o.current=performance.now(),jt("cancel-request"),i()}return e.jsxs("div",{className:`surface view-chunk-state ${a?"error":s?"cancelled":"loading"}`,role:a?"alert":"status",children:[a?e.jsx(ft,{size:20}):e.jsx(Be,{size:20}),e.jsxs("div",{children:[e.jsx("strong",{children:a?`${Oe(t)} data could not be loaded`:s?`${Oe(t)} loading cancelled`:`Loading ${Oe(t)} data`}),e.jsx("p",{children:a??(s?"Previously loaded ranges remain available.":n?"Requesting the selected layer and token range.":"Preparing the artifact request.")})]}),(a||s)&&e.jsx("button",{onClick:r,children:"Retry"}),!a&&!s&&n&&e.jsx("button",{onClick:l,children:"Cancel"}),!a&&!s&&e.jsx(po,{view:t})]})}function lh({view:t}){return e.jsxs("div",{className:"surface view-module-loading",role:"status","aria-live":"polite","aria-busy":"true","aria-label":`Loading ${Oe(t)} view`,children:[e.jsx(Be,{className:"spin",size:20,"aria-hidden":"true"}),e.jsxs("div",{children:[e.jsxs("strong",{children:["Preparing ",Oe(t)," view"]}),e.jsx("p",{children:"The analysis surface is loading its visualization module."})]}),e.jsx(po,{view:t})]})}function po({view:t}){return e.jsxs("div",{className:"analysis-loading-skeleton","data-loading-view":t,"aria-hidden":"true",children:[e.jsxs("div",{className:"analysis-loading-toolbar",children:[e.jsx("span",{}),e.jsx("span",{}),e.jsx("span",{})]}),e.jsxs("div",{className:"analysis-loading-stage",children:[e.jsx("span",{className:"analysis-loading-axis analysis-loading-axis-y"}),e.jsx("span",{className:"analysis-loading-axis analysis-loading-axis-x"}),e.jsx("div",{className:"analysis-loading-grid"}),e.jsx("span",{className:"analysis-loading-viewport"})]}),e.jsxs("div",{className:"analysis-loading-footer",children:[e.jsx("span",{}),e.jsx("span",{}),e.jsx("span",{})]})]})}function dh({onLoad:t}){return e.jsxs("div",{className:"surface full-hydration-gate",role:"status",children:[e.jsx(vt,{size:18}),e.jsxs("div",{children:[e.jsx("strong",{children:"Full Run required for experiments"}),e.jsx("p",{children:"Current visualization uses validated range chunks."})]}),e.jsx("button",{onClick:t,children:"Load full Run"})]})}function ch({layer:t,onCancel:n}){return e.jsxs("div",{className:"surface full-hydration-gate attention-rollout-loading",role:"status",children:[e.jsx(Be,{size:18,className:"spin"}),e.jsxs("div",{children:[e.jsx("strong",{children:"Loading complete attention for rollout"}),e.jsxs("p",{children:["Computing retained-head mean + identity residual through L",t," requires every preceding layer."]})]}),e.jsx("button",{onClick:n,children:"Cancel"})]})}function _a({label:t,shortLabel:n,value:a,tone:s}){return e.jsxs("div",{className:`metric metric-${s}`,"aria-label":`${t} metric`,children:[e.jsx("span",{className:"metric-label-full","aria-hidden":"true",children:t}),e.jsx("span",{className:"metric-label-short","aria-hidden":"true",children:n}),e.jsx("strong",{children:a})]})}function Li(t,n){if(window.matchMedia("(prefers-reduced-motion: reduce)").matches){n(null);return}n(t),window.setTimeout(()=>{n(a=>a===t?null:a)},560)}function $i(){const t=kt(),n=t.nla.filter(s=>s.status!=="unavailable").length,a=[["Real model cache","tokens, residuals, attention, MLP","Directly captured model data."],["Safety proxy","residual direction projection",t.metricProvenance.tokenRisk.semantics],["Attention proxy","descriptive, not causal attribution",t.metricProvenance.tokenAttribution.semantics],["NLA",n>0?`${n} exact fidelity rows`:"no compatible result artifact",n>0?"Exact NLA rows are available for this run.":"Compatibility diagnostics explain why NLA rows are unavailable."]];return e.jsx("div",{className:"provenance-list",children:a.map(([s,i,r])=>e.jsxs("span",{title:r,children:[e.jsx("b",{children:s}),e.jsx("i",{children:i})]},s))})}function uh({metadata:t}){const n=wa(t,"nextToken","n/a"),a=wa(t,"riskDirectionToken","n/a"),s=wa(t,"generatedContinuation","n/a");return e.jsxs("section",{className:"surface digest-panel",children:[e.jsxs("div",{className:"surface-header",children:[e.jsxs("div",{children:[e.jsx("h3",{children:"Model output"}),e.jsx("p",{children:"Real forward-pass metadata"})]}),e.jsx(Be,{size:18})]}),e.jsxs("div",{className:"digest-grid",children:[e.jsxs("span",{children:[e.jsx("b",{children:n}),"next token"]}),e.jsxs("span",{children:[e.jsx("b",{children:a}),"target direction"]}),e.jsxs("span",{children:[e.jsx("b",{children:s}),"greedy continuation"]})]})]})}function mh({selectedToken:t,selectedLayer:n,component:a,selectedHead:s,neuron:i,residualCell:r}){var d;const o=kt(),l=o.tokens[t],c=a==="attention"?s.difference?[["attention head (diff)",St(s)],["selected",s.difference.selectedHeadId],["baseline",s.difference.baselineHeadId],["evidence","derived signed proxy"]]:s.rollout?[["attention path",St(s)],["layers",s.rollout.layers.map(p=>`L${p}`).join(" → ")],["members",`${s.rollout.memberHeadIds.length} retained heads`],["evidence","derived path proxy"]]:s.aggregation?[["aggregation",An(s.aggregation)],["members",((d=s.memberHeadIds)==null?void 0:d.join(" · "))??"retained heads"],["evidence","derived proxy"]]:[["attention head",s.id],["keyword mass",Xe(s.riskContribution)],["entropy",Xe(s.entropy)]]:a==="mlp"&&i?[["MLP neuron",i.id],["activation",Xe(i.activation,"mlp_signed_activation")],["top tokens",i.topTokens.map(p=>o.tokens[p].text).join(" · ")]]:[["residual stream","resid_post"],["norm",((r==null?void 0:r.norm)??0).toFixed(1)],["direction",Xe((r==null?void 0:r.riskDirection)??0,"residual_direction")]];return e.jsxs("section",{className:"surface trace-panel",children:[e.jsxs("div",{className:"surface-header",children:[e.jsxs("div",{children:[e.jsx("h3",{children:"Trace evidence"}),e.jsxs("p",{children:[l.text," · L",n]})]}),e.jsx(Ht,{size:18})]}),e.jsx("div",{className:"trace-grid",children:c.map(([p,g])=>e.jsxs("span",{children:[e.jsx("b",{children:g}),p]},p))})]})}function hh({selectedToken:t,selectedSourceToken:n,selectedLayer:a,view:s,component:i,selectedHead:r,neuron:o,nlaRow:l,attributionMethod:c,attributionEvidenceKind:d,attributionAvailable:p}){var y,m;const g=kt(),b=g.tokens[t],_=[{label:"Selected signal",value:`${b.text} · ${Xe(b.risk)}`},{label:"Context",value:`L${a} · ${Oe(s)}`},{label:"Evidence",value:s==="attention"?`${St(r)} · ${n}→${t}`:s==="attribution"?c:s==="patching"?((y=g.patching)==null?void 0:y.component)??"experiment setup":s==="intervention"?((m=g.intervention)==null?void 0:m.component)??"experiment setup":wo(i,r,o)},{label:"Evidence class",value:s==="attention"?r.aggregation||r.difference||r.rollout?"derived proxy":"raw attention":s==="attribution"?p?d.replace("_"," "):"method unavailable":s==="nla"?(l==null?void 0:l.status)==="available"?"NLA explanation":"unavailable":s==="patching"?g.patching?"causal":"not computed":s==="intervention"?g.intervention?"causal intervention":"not computed":"derived proxy"}];return e.jsx("section",{className:"evidence-summary","aria-label":"Current evidence summary",children:_.map(x=>e.jsxs("span",{children:[e.jsx("em",{children:x.label}),e.jsx("i",{children:x.value})]},x.label))})}function ph({selectedLayer:t,selectedToken:n,hoveredToken:a,setHoveredToken:s,setSelectedLayer:i,setSelectedToken:r,component:o,metric:l,normalization:c,selectedRange:d,setMetric:p,setNormalization:g,setSelectedRange:b,pinCurrent:_,pinCell:y}){const m=kt(),x=go(m,o,l),w=ra(m,o,l);return e.jsx(pl,{title:w.label,subtitle:w.semantics,rows:m.layers,columns:m.tokens,cells:x,metric:l,metricOptions:yo(o),provenance:w,normalization:c,selectedRow:t,selectedColumn:n,selectedRange:d,hoveredColumn:a,color:o,onMetricChange:p,onNormalizationChange:g,onSelectCell:(N,A)=>{i(N),r(A)},onRangeSelect:b,onHoverColumn:s,onPin:_,onPinCell:y})}function yh({view:t,setSelectedView:n,selectedLayer:a,setSelectedLayer:s,selectedToken:i,selectedNlaComponent:r,selectedSourceToken:o,setSelectedToken:l,setSelectedSourceToken:c,selectedHead:d,selectedHeadId:p,setSelectedHeadId:g,selectedTrack:b,setSelectedTrack:_,selectedTrackData:y,selectedAttributionMethod:m,metric:x,normalization:w,residualCell:N,neuron:A,evidenceFilter:T,setEvidenceFilter:k,onConfigureJob:S}){var D;const L=kt();if(t==="overview")return e.jsx(wc,{run:L,selectedToken:i,selectedLayer:a,residualCell:N,onNavigate:n});if(t==="residual")return e.jsx(gh,{selectedToken:i,selectedLayer:a,setSelectedLayer:s,metric:x,normalization:w,residualCell:N});if(t==="mlp")return e.jsx(_h,{selectedToken:i,selectedLayer:a,neuron:A});if(t==="nla"){const C=Qn(L.nla,i,a,r),ne=[{view:"residual",label:"Residual",component:"resid_post",icon:e.jsx(Sn,{size:16})},{view:"attention",label:"Attention",component:"attn_result",icon:e.jsx(Ot,{size:16})},{view:"mlp",label:"MLP",component:"mlp_out",icon:e.jsx(Bt,{size:16})}];return e.jsxs("section",{className:"surface nla-evidence-detail",children:[e.jsxs("div",{className:"surface-header",children:[e.jsxs("div",{children:[e.jsx("h3",{children:"Exact NLA evidence"}),e.jsxs("p",{children:["token ",i," · layer ",a," · ",r," · strict match"]})]}),e.jsx(dt,{size:18})]}),C?C.status==="unavailable"?e.jsxs(e.Fragment,{children:[e.jsxs("div",{className:"nla-exact-facts",children:[e.jsxs("span",{children:[e.jsx("b",{children:C.token}),"token ",C.tokenIndex]}),e.jsxs("span",{children:[e.jsxs("b",{children:["L",C.layer]}),C.component]}),e.jsxs("span",{children:[e.jsx("b",{children:C.activationNorm.toFixed(4)}),"activation norm"]}),e.jsxs("span",{children:[e.jsx("b",{children:"unavailable"}),"decoder status"]})]}),e.jsx(wn,{compact:!0,icon:e.jsx(dt,{size:18}),title:"Activation is cached; NLA decoding is unavailable",description:C.explanation,facts:[{label:"Source",value:C.source??"not stored"},{label:"Activation norm",value:C.activationNorm.toFixed(4)}],actionLabel:"Configure exact NLA",actionIcon:e.jsx(dt,{size:16}),onAction:()=>S("nla-job")})]}):e.jsxs(e.Fragment,{children:[e.jsxs("div",{className:"nla-exact-facts",children:[e.jsxs("span",{children:[e.jsx("b",{children:C.cosine.toFixed(4)}),"cosine"]}),e.jsxs("span",{children:[e.jsx("b",{children:C.mse.toFixed(4)}),"MSE"]}),e.jsxs("span",{children:[e.jsx("b",{children:((D=C.fve)==null?void 0:D.toFixed(4))??"n/a"}),"FVE"]}),e.jsxs("span",{children:[e.jsx("b",{children:C.activationNorm.toFixed(4)}),"activation norm"]})]}),e.jsx(wh,{row:C})]}):e.jsx(wn,{compact:!0,icon:e.jsx(dt,{size:18}),title:"No exact NLA artifact row",description:"Nearby tokens, layers, or components are intentionally not substituted. Compute this exact selection instead.",facts:[{label:"Selection",value:`L${a} / token ${i}`},{label:"Component",value:r}],actionLabel:"Configure exact NLA",actionIcon:e.jsx(dt,{size:16}),onAction:()=>S("nla-job")}),e.jsxs("div",{className:"nla-cross-view-links",role:"group","aria-label":"Activation context views",children:[e.jsxs("div",{children:[e.jsx("strong",{children:"Activation context"}),e.jsxs("span",{children:["Keep token ",i," and L",a," while changing evidence view."]})]}),ne.map(pe=>e.jsxs("button",{type:"button","aria-label":`Open ${pe.label} at layer ${a}, token ${i}`,onClick:()=>n(pe.view),children:[pe.icon,e.jsxs("span",{children:[e.jsx("b",{children:pe.label}),pe.component===r?"component context":"same token / layer"]}),e.jsx(gt,{size:15})]},pe.view))]})]})}if(t==="attention"){const C=d.distributionByToken[i]??[],ne=St(d),pe=C.slice(0,i+1).map((j,ee)=>({tokenIndex:ee,score:j,reason:Rh(L,ee,i)})),R=d.difference?Ch(pe,i,T):Nh(pe,i,T);return e.jsxs("section",{className:"surface attention-distribution",children:[e.jsxs("div",{className:"surface-header",children:[e.jsxs("div",{children:[e.jsx("h3",{children:"Attention distribution"}),e.jsxs("p",{children:[ne," · destination token ",i," row"]})]}),e.jsx(Ot,{size:18})]}),e.jsxs("div",{className:"head-picker",children:[(d.aggregation||d.difference||d.rollout)&&e.jsx("span",{className:"aggregate-head-label",children:ne}),L.attentionHeads.filter(j=>j.layer===a).map(j=>{var ee;return e.jsx("button",{className:((ee=d.difference)==null?void 0:ee.selectedHeadId)===j.id||p===j.id?"active":"",onClick:()=>{var oe;if(!d.difference){g(j.id);return}const ue=d.difference.baselineHeadId===j.id?((oe=L.attentionHeads.find(O=>O.layer===a&&O.id!==j.id))==null?void 0:oe.id)??d.difference.baselineHeadId:d.difference.baselineHeadId;g(ro(j.id,ue))},children:j.id},j.id)})]}),e.jsx(bh,{filter:T,setFilter:k}),e.jsx(xh,{rows:R,selectedToken:o,onSelectToken:c,scoreTone:d.difference?"attention-difference":"attention"})]})}const M=y.values.map((C,ne)=>({tokenIndex:ne,value:C})),F=[...M].filter(C=>C.value>0).sort((C,ne)=>ne.value-C.value).slice(0,5),V=[...M].filter(C=>C.value<0).sort((C,ne)=>C.value-ne.value).slice(0,5),W=m.id==="integrated_gradients"?fo(L.metadata):void 0,K=Array.isArray(W==null?void 0:W.rawValues)&&W.rawValues.length===y.values.length&&W.rawValues.every(C=>typeof C=="number"&&Number.isFinite(C))?W.rawValues:void 0,H=K??y.values,Z=L.attributionMethods.map(C=>{const ne=C.rows.find(pe=>pe.layer===a)??C.rows.find(pe=>pe.layer<0);return{method:C,row:ne,value:ne==null?void 0:ne.values[i]}});return e.jsxs("section",{className:"surface attribution-distribution",children:[e.jsxs("div",{className:"surface-header",children:[e.jsxs("div",{children:[e.jsx("h3",{children:"Attribution evidence"}),e.jsx("p",{children:m.label})]}),e.jsx(ta,{size:18})]}),e.jsxs("div",{className:"attribution-method-compare-heading",children:[e.jsxs("div",{children:[e.jsx("strong",{children:"Selected-token method snapshots"}),e.jsx("span",{children:"Within-method values only; different methods and scales do not produce a direct delta."})]}),e.jsxs("b",{children:["token ",i]})]}),e.jsx("div",{className:"attribution-method-catalog","aria-label":"Attribution methods",children:Z.map(({method:C,row:ne,value:pe})=>e.jsxs("button",{className:`${b===C.id?"active":""} ${C.available?"":"unavailable"}`,"aria-pressed":b===C.id,onClick:()=>_(C.id),children:[e.jsxs("span",{children:[e.jsx("strong",{children:C.label}),e.jsx("small",{children:ne?ne.layer<0?ne.label:`L${ne.layer}`:"no exact row"})]}),e.jsx("b",{children:C.available&&pe!==void 0?ho(pe):"n/a"}),e.jsx("em",{children:C.available?`${C.signed?"signed":"unsigned"} · ${C.evidenceKind.replace("_"," ")}`:"not run"})]},C.id))}),m.available?e.jsxs(e.Fragment,{children:[e.jsxs("div",{className:"attribution-selected-value",children:[e.jsx("span",{children:"Selected token"}),e.jsx("strong",{children:L.tokens[i].text}),e.jsx("b",{children:(y.values[i]??0).toFixed(6)}),e.jsx("i",{children:m.signed?"signed stored value":"unsigned proxy"})]}),e.jsx(fh,{values:H,signed:m.signed,basis:K?"raw job values":"stored method row",selectedToken:i,job:W}),e.jsxs("div",{className:"attribution-polarity-lists",children:[e.jsx(Ei,{title:"Top positive",entries:F,selectedToken:i,onSelectToken:l}),m.signed&&e.jsx(Ei,{title:"Top negative",entries:V,selectedToken:i,onSelectToken:l})]}),e.jsxs("div",{className:"provenance-note",children:[e.jsx("b",{children:m.evidenceKind.replace("_"," ")}),e.jsx("p",{children:m.description}),e.jsx("span",{children:m.normalization})]})]}):m.id==="integrated_gradients"?e.jsx(wn,{compact:!0,icon:e.jsx(Be,{size:18}),title:"Method output unavailable",description:m.unavailableReason??"No target-specific attribution output was computed.",facts:[{label:"Method",value:m.label},{label:"Token",value:String(i)}],actionLabel:"Configure Integrated Gradients",actionIcon:e.jsx(Be,{size:16}),onAction:()=>S("attribution-job")}):e.jsxs("div",{className:"analysis-empty compact",children:[e.jsx("span",{className:"empty-icon",children:e.jsx(ft,{size:18})}),e.jsx("strong",{children:"Method output unavailable"}),e.jsx("p",{children:m.unavailableReason})]})]})}function fh({values:t,signed:n,basis:a,selectedToken:s,job:i}){const r=t.reduce((N,A)=>N+Math.max(0,A),0),o=t.reduce((N,A)=>N+Math.min(0,A),0),l=r+o,c=r+Math.abs(o),d=c>1e-12?Math.max(0,Math.min(1,1-Math.abs(l)/c)):0,p=t.reduce((N,A)=>Math.max(N,Math.abs(A)),0),g=Math.abs(t[s]??0),b=c>1e-12?g/c:0,_=typeof(i==null?void 0:i.targetTokenText)=="string"?i.targetTokenText:typeof(i==null?void 0:i.targetTokenId)=="number"?`token ${i.targetTokenId}`:"not recorded",y=typeof(i==null?void 0:i.targetResponseIndex)=="number"?`response[${i.targetResponseIndex}]`:"response index not recorded",m=typeof(i==null?void 0:i.baseline)=="string"?i.baseline:"not recorded",x=typeof(i==null?void 0:i.nSteps)=="number"?String(i.nSteps):"not recorded",w=typeof(i==null?void 0:i.convergenceDelta)=="number"?i.convergenceDelta.toExponential(3):"not recorded";return e.jsxs("section",{className:"attribution-accounting","aria-label":"Attribution accounting",children:[e.jsxs("header",{children:[e.jsxs("div",{children:[e.jsx("strong",{children:"Attribution accounting"}),e.jsxs("span",{children:[a," · ",t.length," input positions"]})]}),e.jsx("b",{children:n?"signed balance":"unsigned mass"})]}),e.jsx("div",{className:"attribution-accounting-metrics",children:n?e.jsxs(e.Fragment,{children:[e.jsxs("span",{children:[e.jsx("b",{children:pn(r)}),"positive sum"]}),e.jsxs("span",{children:[e.jsx("b",{children:pn(o)}),"negative sum"]}),e.jsxs("span",{children:[e.jsx("b",{children:pn(l)}),"net sum"]}),e.jsxs("span",{children:[e.jsxs("b",{children:[(d*100).toFixed(1),"%"]}),"sign cancellation"]})]}):e.jsxs(e.Fragment,{children:[e.jsxs("span",{children:[e.jsx("b",{children:pn(c)}),"stored mass"]}),e.jsxs("span",{children:[e.jsx("b",{children:pn(p)}),"peak magnitude"]}),e.jsxs("span",{children:[e.jsxs("b",{children:[(b*100).toFixed(1),"%"]}),"selected share"]}),e.jsxs("span",{children:[e.jsx("b",{children:"none"}),"sign semantics"]})]})}),i?e.jsxs("div",{className:"attribution-objective-context",children:[e.jsx(Ht,{size:16}),e.jsxs("span",{children:[e.jsx("b",{children:_}),y]}),e.jsxs("span",{children:[e.jsx("b",{children:m}),"baseline"]}),e.jsxs("span",{children:[e.jsx("b",{children:x}),"integration steps"]}),e.jsxs("span",{children:[e.jsx("b",{children:w}),"convergence delta"]})]}):e.jsxs("div",{className:"attribution-objective-context proxy",children:[e.jsx(ft,{size:16}),e.jsxs("span",{children:[e.jsx("b",{children:"No target/baseline contract"}),"This method is a run-relative diagnostic, not a target-specific completeness attribution."]})]}),e.jsx("p",{children:"Sum and cancellation are accounting checks within this method. They do not prove completeness, causal sufficiency, or comparability with another attribution scale."})]})}function pn(t){const n=Math.abs(t);return n>0&&n<1e-4?t.toExponential(3):ho(t)}function Ei({title:t,entries:n,selectedToken:a,onSelectToken:s}){const i=kt();return e.jsxs("div",{className:"attribution-polarity-list",children:[e.jsx("span",{children:t}),n.length>0?n.map(r=>e.jsxs("button",{className:r.tokenIndex===a?"active":"",onClick:()=>s(r.tokenIndex),children:[e.jsx("strong",{children:i.tokens[r.tokenIndex].text}),e.jsx("b",{children:r.value.toFixed(6)})]},r.tokenIndex)):e.jsx("p",{children:"No values in this direction."})]})}function gh({selectedToken:t,selectedLayer:n,setSelectedLayer:a,metric:s,normalization:i,residualCell:r}){const o=kt(),l=ra(o,"residual",s),c=s==="residual_norm"?i==="raw"?(r==null?void 0:r.norm)??0:(r==null?void 0:r.semanticDensity)??0:i==="raw"?(r==null?void 0:r.rawDirection)??0:(r==null?void 0:r.riskDirection)??0,d=o.logitLens.filter(p=>p.tokenIndex===t);return e.jsxs("section",{className:"surface component-evidence",children:[e.jsxs("div",{className:"surface-header",children:[e.jsxs("div",{children:[e.jsx("h3",{children:"Residual evidence"}),e.jsxs("p",{children:["layer_",n,".resid_post · token ",t]})]}),e.jsx(Sn,{size:18})]}),e.jsxs("div",{className:"component-metric-grid",children:[e.jsxs("span",{children:[e.jsx("b",{children:c.toFixed(i==="raw"?6:3)}),"selected metric"]}),e.jsxs("span",{children:[e.jsx("b",{children:Xe((r==null?void 0:r.riskDirection)??0,"residual_direction")}),"direction alignment"]}),e.jsxs("span",{children:[e.jsx("b",{children:((r==null?void 0:r.norm)??0).toFixed(3)}),"activation norm"]})]}),e.jsxs("div",{className:"provenance-note",children:[e.jsx("b",{children:l.label}),e.jsx("p",{children:l.semantics}),e.jsx("span",{children:l.normalization})]}),e.jsx(Hm,{rows:d,selectedLayer:n,onSelectLayer:a})]})}function _h({selectedToken:t,selectedLayer:n,neuron:a}){const s=kt(),i=s.mlpCells.find(l=>l.layer===n&&l.tokenIndex===t),r=s.mlpNeurons.filter(l=>l.layer===n),o=(a==null?void 0:a.activationsByToken[t])??0;return e.jsxs("section",{className:"surface component-evidence",children:[e.jsxs("div",{className:"surface-header",children:[e.jsxs("div",{children:[e.jsx("h3",{children:"MLP activation"}),e.jsxs("p",{children:["layer_",n,".post · token ",t]})]}),e.jsx(Fa,{size:18})]}),e.jsxs("div",{className:"component-metric-grid",children:[e.jsxs("span",{children:[e.jsx("b",{children:o.toFixed(6)}),"signed neuron activation"]}),e.jsxs("span",{children:[e.jsx("b",{children:Math.abs(o).toFixed(6)}),"absolute activation"]}),e.jsxs("span",{children:[e.jsx("b",{children:(a==null?void 0:a.id)??"none"}),"selected retained neuron"]})]}),a&&e.jsxs("div",{className:"mlp-polarity-summary",children:[e.jsxs("div",{children:[e.jsx("span",{children:"Top positive tokens"}),e.jsx("p",{children:a.positiveTopTokens.map(l=>s.tokens[l].text).join(" · ")})]}),e.jsxs("div",{children:[e.jsx("span",{children:"Top negative tokens"}),e.jsx("p",{children:a.negativeTopTokens.map(l=>s.tokens[l].text).join(" · ")})]})]}),e.jsxs("div",{className:"provenance-note",children:[e.jsx("b",{children:"Raw MLP post activation"}),e.jsx("p",{children:"Signed activation describes neuron response only; it is not target-logit contribution, probe contribution, or causal ablation effect."}),e.jsxs("span",{children:["layer_",n,".post · ",r.length," retained neurons · aggregate mean |activation| ",((i==null?void 0:i.rawValue)??0).toFixed(6)]})]}),e.jsx("div",{className:"ranked-components",children:r.slice(0,8).map(l=>e.jsxs("span",{className:l.id===(a==null?void 0:a.id)?"active":"",children:[e.jsx("b",{children:l.id}),e.jsx("i",{children:(l.activationsByToken[t]??0).toFixed(4)})]},l.id))})]})}function bh({filter:t,setFilter:n}){const a=[{id:"top",label:"Top"},{id:"neighborhood",label:"Nearby"},{id:"all",label:"All"}];return e.jsx("div",{className:"evidence-filter","aria-label":"Evidence filter",children:a.map(s=>e.jsx("button",{className:t===s.id?"active":"",onClick:()=>n(s.id),children:s.label},s.id))})}function xh({rows:t,selectedToken:n,onSelectToken:a,scoreTone:s}){const i=kt();return e.jsxs("div",{className:"evidence-table",children:[e.jsxs("div",{className:"evidence-table-head",children:[e.jsx("span",{children:"source token"}),e.jsx("span",{children:"score"}),e.jsx("span",{children:"why it matters"})]}),t.map(r=>{const o=i.tokens[r.tokenIndex];return e.jsxs("button",{className:n===r.tokenIndex?"evidence-row selected":"evidence-row",onClick:()=>a(r.tokenIndex),style:{"--score":Math.abs(r.score)},children:[e.jsx("span",{className:"source-token",children:o.text}),e.jsxs("span",{className:`score-cell score-${s} ${r.score<0?"negative":"positive"}`,children:[e.jsx("i",{}),e.jsx("b",{children:s==="attention-difference"?Ka(r.score,"attention_retained_head_difference","compact"):Xe(r.score,"attention_probability")})]}),e.jsx("span",{className:"reason-cell",children:r.reason})]},`${r.tokenIndex}-${r.reason}`)})]})}function wh({row:t}){const n=kt(),a=t.status==="unavailable";return e.jsxs("article",{className:a?"nla-card nla-card-muted":"nla-card",children:[e.jsxs("div",{className:"nla-card-header",children:[e.jsxs("div",{children:[e.jsx("strong",{children:n.tokens[t.tokenIndex].text}),e.jsxs("span",{children:["L",t.layer," · ",t.component]})]}),e.jsxs("span",{className:`status-pill ${a?"status-warn":"status-live"}`,children:[a?e.jsx(ft,{size:13}):e.jsx(ot,{size:13}),a?"not run":"ready"]})]}),e.jsx("p",{children:Ah(t)}),e.jsxs("div",{className:"mini-metrics",children:[a?e.jsx("span",{children:"Qwen/Gemma NLA profiles required"}):e.jsxs(e.Fragment,{children:[e.jsxs("span",{children:["cos ",Xe(t.cosine,"nla_cosine")]}),e.jsxs("span",{children:["mse ",Xe(t.mse,"nla_mse")]})]}),e.jsxs("span",{children:["norm ",t.activationNorm.toFixed(1)]})]}),e.jsxs("details",{className:"detail-disclosure",children:[e.jsxs("summary",{children:[e.jsx("span",{children:"Full NLA message"}),e.jsx(Xn,{size:14})]}),e.jsx("p",{children:t.explanation})]})]})}function kh({pinned:t,restorePin:n,availableRunKeys:a,openCompare:s}){return e.jsxs("section",{className:"pinned-strip",children:[e.jsxs("div",{className:"pinned-strip-heading",children:[e.jsxs("span",{children:[e.jsx(yt,{size:14})," Pinned evidence"]}),e.jsxs("button",{onClick:s,children:["Compare all (",t.length,")"]})]}),e.jsx("div",{className:"pinned-strip-items",children:t.map(i=>{const r=a.has(xt(i));return e.jsxs("button",{disabled:!r,title:r?"Restore evidence context":"Source run is not loaded",onClick:()=>n(i),children:[e.jsx("strong",{children:i.tokenText}),e.jsxs("span",{children:[i.runId," / ",i.sampleId]}),e.jsxs("span",{children:["L",i.layer," · ",Oe(i.view),i.view==="nla"?` · ${i.component}`:""]}),e.jsxs("span",{children:[ol(i.metric)," ",Ye(i.value,i.metric,"compact")]})]},i.id)})})]})}function yo(t){return t==="residual"?[{id:"residual_direction",label:"Direction alignment"},{id:"residual_norm",label:"Activation norm"}]:t==="attention"?[{id:"attention_concentration",label:"Attention concentration"}]:[{id:"mlp_magnitude",label:"Mean absolute activation"}]}function vh(t,n){const a=yo(t);return a.some(s=>s.id===n)?n:a[0].id}function ba(t){const n=["mlp_signed_activation","mlp_absolute_activation","mlp_normalized_activation"];return n.includes(t)?t:n[0]}function xa(t){return t==="nla_mse"?"mse":t==="nla_fve"?"fve":"cosine"}function Yn(t,n,a){return a==="mlp_absolute_activation"?Math.abs(t):a==="mlp_normalized_activation"?Math.abs(t)/Math.max(n,1e-12):t}function Mi(t){return t==="mlp_absolute_activation"?"absolute raw activation":t==="mlp_normalized_activation"?"normalized activation magnitude":"signed raw activation"}function _n({run:t,view:n,selectedToken:a,selectedSourceToken:s,selectedLayer:i,selectedNlaComponent:r,selectedHead:o,selectedNeuron:l,selectedAttributionMethod:c,metric:d,normalization:p,sourceArtifact:g}){var K,H,Z,D;const b=t.tokens[a]??t.tokens[0],_=t.residualCells.find(C=>C.layer===i&&C.tokenIndex===a),y=Qn(t.nla,a,i,r),m=c.rows.find(C=>C.layer===i)??c.rows[0],x=Sh(t.metadata,n,a,i);let w="available",N="Exact evidence is available for the selected token and layer.",A="Safety proxy",T="not stored",k=Ye(b.risk,"tokenRisk","exact"),S="normalized score",L=`layer_${i}.resid_post[${a}]`,M=`scalar from [${t.nlaCompatibility.dModel}]`,F=t.metricProvenance.tokenRisk;const V=[];if(n==="overview"&&V.push("Run-relative proxy; it is not a calibrated safety probability or causal effect."),n==="residual"&&(F=ra(t,"residual",d),A=F.label,L=`layer_${i}.resid_post[${a}]`,M=`[${t.nlaCompatibility.dModel}] residual vector`,S=d==="residual_norm"?"L2 norm":"projection",_?d==="residual_norm"?(T=Ye(_.norm,"residual_norm","exact"),k=Ye(p==="raw"?_.norm:_.semanticDensity,p==="raw"?"residual_norm":"normalized","exact")):(T=Ye(_.rawDirection,"residual_direction","exact"),k=Ye(p==="raw"?_.rawDirection:_.riskDirection,p==="raw"?"residual_direction":"normalized","exact"),V.push("Directional alignment is diagnostic projection, not causal contribution.")):(w="unavailable",N="No exact residual cell exists for the selected token and layer.",T="n/a",k="n/a")),n==="attention"){F=za(o,t.metricProvenance.attentionHeatmap);const C=(K=o.distributionByToken[a])==null?void 0:K[s];A=o.difference?"Retained-head probability difference":o.rollout?"Retained attention rollout":o.aggregation?An(o.aggregation):"Attention probability";const ne=co(o);T=Ye(C,ne,"exact"),k=T,S=o.difference?"selected minus baseline probability":o.rollout?"retained rollout path weight":o.aggregation==="max"?"maximum retained-head probability":o.aggregation?"weighted retained-head probability":"softmax probability",L=lo(o,a,s),M=`[${t.tokens.length} × ${t.tokens.length}]`,C===void 0?(w="unavailable",N="The exact source/destination attention cell is unavailable."):o.difference?(N=`Client-derived ${o.difference.selectedHeadId} minus ${o.difference.baselineHeadId} cell.`,V.push("This signed difference covers two retained artifact heads only and is not causal evidence.")):o.rollout?(N=`Client-derived retained-head rollout through L${o.layer}.`,V.push("This rollout uses artifact-retained heads only and is not full-model or causal evidence.")):o.aggregation&&(N=`Client-derived ${o.aggregation} cell over ${((H=o.memberHeadIds)==null?void 0:H.length)??0} retained heads.`,V.push("This aggregate covers retained artifact heads only, not every head in the model.")),V.push("Attention probability is descriptive and must not be read as causal attribution.")}if(n==="mlp"){F=t.metricProvenance.mlpNeuronActivation;const C=l==null?void 0:l.activationsByToken[a];A="MLP activation",T=Ye(C,"mlp_signed_activation","exact");const ne=C===void 0?void 0:Yn(C,(l==null?void 0:l.maxAbsoluteActivation)??1,d);k=Ye(ne,d,"exact"),S=d==="mlp_normalized_activation"?"normalized magnitude":"activation",L=l?`layer_${l.layer}.post[${a},${l.neuron}]`:`layer_${i}.post[${a},?]`,M=`[${t.tokens.length} × retained neurons]`,C===void 0&&(w="unavailable",N="No retained neuron strictly matches the selected layer and token."),V.push("Activation magnitude is not logit contribution, probe contribution, or ablation effect.")}if(n==="nla"){const C=jh(t.metadata);F={label:"NLA fidelity",method:C?`${String(C.profile)} AV/AR · ${String(C.actorRevision)} / ${String(C.reconstructorRevision)}`:"exact NLA decoder reconstruction",semantics:"Exact token/layer/component reconstruction fidelity for a compatible profile.",normalization:"stored method metric",kind:"safety_method"};const ne=d==="nla_mse"?y==null?void 0:y.mse:d==="nla_fve"?y==null?void 0:y.fve:y==null?void 0:y.cosine;A=d==="nla_mse"?"NLA MSE":d==="nla_fve"?"NLA FVE":"NLA cosine",T=(y==null?void 0:y.status)==="unavailable"?"n/a":Ye(ne,d,"exact"),k=T,S="fidelity metric",L=(y==null?void 0:y.source)??`nla[L${i},T${a}]`,M="scalar fidelity + explanation";const pe=t.nlaCompatibility.profiles.some(R=>R.status==="compatible");!y||y.status==="unavailable"?(w=pe?"not-computed":"incompatible",N=(y==null?void 0:y.explanation)??"No exact NLA result artifact was computed for this cell.",V.push((y==null?void 0:y.explanation)??"A compatible NLA artifact is required.")):ne===void 0&&(w="not-computed",N=`${A} was not stored for this otherwise available NLA row.`),C&&V.push(`Exact ${String(C.profile)} result for L${String(C.layer)} / ${String(C.component)}; trust_remote_code=${String(C.trustRemoteCode)}.`)}if(n==="attribution"){F=c.id==="integrated_gradients"&&t.metricProvenance.integratedGradients?t.metricProvenance.integratedGradients:{label:c.label,method:c.id,semantics:c.description,normalization:c.normalization,kind:c.evidenceKind};const C=c.id==="integrated_gradients"?fo(t.metadata):void 0,ne=m==null?void 0:m.values[a],pe=Array.isArray(C==null?void 0:C.rawValues)?C.rawValues[a]:void 0,R=ne===void 0?void 0:Ih(ne,c.rows,c.signed);if(A=c.label,T=Ye(typeof pe=="number"?pe:ne,c.id,"exact"),k=Ye(p==="raw"?ne:R,p==="raw"?c.id:"normalized","exact"),S=c.signed?"signed contribution":"unsigned proxy",L=(m==null?void 0:m.sourceKey)??`${c.id}[${a}]`,M=`[${c.rows.length} × ${t.tokens.length}]`,c.available?ne===void 0&&(w="unavailable",N="The selected attribution method has no exact value for this token."):(w="not-computed",N=c.unavailableReason??"Method output was not computed."),c.signed||V.push("Unsigned proxy values do not encode positive versus negative causal contribution."),C){const ee=typeof C.targetTokenText=="string"?C.targetTokenText:C.targetTokenId;V.push(`Target: ${String(ee)} at response[${String(C.targetResponseIndex)}]; baseline: ${String(C.baseline)}; steps: ${String(C.nSteps)}.`),Array.isArray(C.responseContextAttributions)&&C.responseContextAttributions.length&&V.push(`${C.responseContextAttributions.length} preceding response-context token attribution(s) are retained in job metadata but omitted from this prompt-token matrix.`)}}if(n==="patching"){const C=t.patching,ne=C==null?void 0:C.cells.find(R=>R.layer===i&&R.tokenIndex===a);F=ss(t,d),A=F.label;const pe=xo(ne,d);T=Ye(ne==null?void 0:ne.patchedScore,"patching_score","exact"),k=Ye(pe,d,"exact"),S=d==="patching_recovery"?"percent recovery":"target-token logit",L=(ne==null?void 0:ne.sourceKey)??`patching[L${i},T${a}]`,M=C?`[${C.layers.length} × ${C.positions.length}] causal grid`:"not computed",C?ne?d==="patching_recovery"&&ne.recoveryPercentage===null?(w="unavailable",N="Recovery is undefined because clean and corrupted target logits are effectively equal.",V.push("Use causal effect or patched logit for this experiment; percentage recovery has a near-zero denominator.")):(N="Exact causal evidence from one clean-activation replacement forward pass.",V.push(`Clean logit ${C.cleanScore.toFixed(6)}; corrupted logit ${C.corruptedScore.toFixed(6)}; patched logit ${ne.patchedScore.toFixed(6)}.`)):(w="not-computed",N="The selected layer/token cell was not included in this patch grid."):(w="not-computed",N="This Run does not contain an activation patching experiment.")}if(n==="intervention"){const C=t.intervention;F=is(t),A=F.label,T=Ye(C==null?void 0:C.steered.targetLogit,"intervention_target_logit","exact"),k=Ye(C==null?void 0:C.deltas.targetLogit,"intervention_logit_delta","exact"),S="raw target-token logit delta",L=(C==null?void 0:C.vector.sourceKey)??`intervention[L${i}]`,M=C?`[${C.vector.dimension}] normalized steering vector`:"not computed",C?(N="Exact original-versus-steered delta with matched seed and generation parameters.",V.push(`Original logit ${C.original.targetLogit.toFixed(6)}; steered logit ${C.steered.targetLogit.toFixed(6)}; token edit distance ${C.deltas.tokenEditDistance}.`),V.push(C.deltas.probeReason),C.deltas.lexicalRisk!==0&&V.push("Lexical risk delta is a fixed term-match proxy, not a trained probe score.")):(w="not-computed",N="This Run does not contain an intervention comparison.")}x&&(w="failed",N=x,V.unshift(x)),p==="normalized"&&T!==k&&k!=="n/a"&&V.push(`Displayed value uses: ${F.normalization}.`);const W=n==="attention"?`${St(o)} · source ${s} → destination ${a}`:n==="mlp"?(l==null?void 0:l.id)??"no retained neuron":n==="attribution"?c.label:n==="patching"?((Z=t.patching)==null?void 0:Z.component)??"no experiment":n==="intervention"?((D=t.intervention)==null?void 0:D.component)??"no experiment":n==="nla"?(y==null?void 0:y.component)??"no exact component":"resid_post";return{title:b.text||"␠",subtitle:`${Oe(n)} · L${i} · ${W}`,status:w,statusReason:N,primaryLabel:A,primaryValue:k,rawValue:T,displayValue:k,units:S,evidenceClass:F.kind,method:F.method,normalization:F.normalization,cacheKey:L,shape:M,sourceArtifact:g,runId:t.runId,sampleId:t.sampleId,modelName:t.modelName,warnings:[...new Set(V)],reproduction:{schema_version:"1.0",run_id:t.runId,sample_id:t.sampleId,model:t.modelName,selection:{view:n,token:a,source_token:n==="attention"?s:void 0,layer:i,nla_component:n==="nla"?r:void 0,metric:d,normalization:p},evidence:{raw_value:T,display_value:k,units:S,cache_key:L},provenance:F}}}function fo(t){const n=t==null?void 0:t.attributionJobs;if(!Array.isArray(n)||n.length===0)return;const a=n[n.length-1];return a&&typeof a=="object"&&!Array.isArray(a)?a:void 0}function jh(t){const n=t==null?void 0:t.nlaJobs;if(!Array.isArray(n)||n.length===0)return;const a=n[n.length-1];return a&&typeof a=="object"&&!Array.isArray(a)?a:void 0}function Ih(t,n,a){const s=n.flatMap(o=>o.values);if(a){const o=Math.max(1e-12,...s.map(l=>Math.abs(l)));return t/o}const i=Math.min(...s),r=Math.max(...s);return Math.abs(r-i)<1e-12?0:(t-i)/(r-i)}function Sh(t,n,a,s){const i=t==null?void 0:t.analysisFailures;if(!Array.isArray(i))return;const r=i.find(o=>{if(!o||typeof o!="object")return!1;const l=o;return l.view===n&&(l.token===void 0||l.token===a)&&(l.layer===void 0||l.layer===s)});return typeof(r==null?void 0:r.message)=="string"?r.message:void 0}function Pi(t,n,a){return n==="overview"?t.metricProvenance.tokenRisk:n==="residual"?ra(t,"residual",a):n==="attention"?t.metricProvenance.attentionHeatmap:n==="mlp"?t.metricProvenance.mlpNeuronActivation:n==="patching"?ss(t,a):n==="intervention"?is(t):t.metricProvenance.tokenAttribution??t.metricProvenance.tokenRisk}function go(t,n,a){return n==="attention"?t.attentionCells.map(s=>({row:s.layer,column:s.tokenIndex,value:s.value,rawValue:s.rawValue,metric:s.metric,sourceKey:s.sourceKey})):n==="mlp"?t.mlpCells.map(s=>({row:s.layer,column:s.tokenIndex,value:s.value,rawValue:s.rawValue,metric:s.metric,sourceKey:s.sourceKey})):t.residualCells.map(s=>({row:s.layer,column:s.tokenIndex,value:a==="residual_norm"?s.semanticDensity:s.riskDirection,rawValue:a==="residual_norm"?s.norm:s.rawDirection,metric:a==="residual_norm"?"residual_l2_norm":"residual_direction_projection",sourceKey:`layer_${s.layer}.resid_post`}))}function ra(t,n,a){return n==="residual"&&a==="residual_norm"?{label:"Residual activation norm",method:"L2 norm over the resid_post model dimension",semantics:"Raw activation magnitude; high norm does not imply high safety risk.",normalization:"min-max over all layer-token residual norms",kind:"raw"}:t.metricProvenance[Th(n)]}function Th(t){return t==="attention"?"attentionHeatmap":t==="mlp"?"mlpHeatmap":"residualHeatmap"}function _o(t){return[...t].sort((n,a)=>a.risk-n.risk).slice(0,3).map(n=>n.index)}function Ah(t){return t.status==="unavailable"?"NLA unavailable for this model. Current real run uses tiny-gpt2; public NLA profiles target Qwen/Gemma.":t.explanation}function wa(t,n,a){const s=t==null?void 0:t[n];return typeof s=="string"||typeof s=="number"?String(s):a}function Nh(t,n,a){return a==="neighborhood"?t.filter(s=>Math.abs(s.tokenIndex-n)<=2).sort((s,i)=>i.score-s.score):a==="all"?[...t].sort((s,i)=>s.tokenIndex-i.tokenIndex):[...t].sort((s,i)=>i.score-s.score).slice(0,8)}function Ch(t,n,a){return a==="neighborhood"?t.filter(s=>Math.abs(s.tokenIndex-n)<=2).sort((s,i)=>Math.abs(i.score)-Math.abs(s.score)):a==="all"?[...t].sort((s,i)=>s.tokenIndex-i.tokenIndex):[...t].sort((s,i)=>Math.abs(i.score)-Math.abs(s.score)).slice(0,8)}function Rh(t,n,a){return n===a?"query token":Math.abs(n-a)<=2?"local context":t.nla.some(s=>s.tokenIndex===n)?"cached evidence":"attended source"}function Qn(t,n,a,s){return t.find(i=>i.tokenIndex===n&&i.layer===a&&i.component===s)}function Lh(t){return t==="attention"?"attention":t==="mlp"?"mlp":"residual"}function $h({view:t,tokenText:n,tokenIndex:a,sourceTokenIndex:s,tokenRange:i,layer:r,metric:o,normalization:l,headId:c,neuronId:d,nlaComponent:p,attributionMethod:g,attentionEdgeMode:b}){const _=n.replace(/\s+/g," ").trim()||"whitespace",y=_.length>18?`${_.slice(0,17)}…`:_,m=o.replace(/_/g," "),x=i?`tokens ${i[0]}–${i[1]}`:t==="attention"?`${s} → ${a} “${y}”`:`token ${a} “${y}”`,w=t==="attention"?`${c} · ${b} · ${m}`:t==="mlp"?`${d??"no retained neuron"} · ${m}`:t==="nla"?`${p} · ${m}`:t==="attribution"?g:m;return{signature:[t,a,s,(i==null?void 0:i.join("-"))??"",r,o,l,t==="attention"?`${c}:${b}`:"",t==="mlp"?d??"":"",t==="nla"?p:"",t==="attribution"?g:""].join("|"),message:`${Oe(t)} · L${r} · ${x} · ${w} · ${l}`}}function Oe(t){return{overview:"Overview",residual:"Residual",attention:"Attention",mlp:"MLP",nla:"NLA",patching:"Patching",intervention:"Intervention",attribution:"Attribution"}[t]}function Eh(t,n){if(n.status==="loading"||n.status==="cancelled")return[];const a=[],s=r=>{a.some(o=>o.id===r.id)||a.push(r)},i=n.status!=="available";return i&&t==="attribution"?s({id:"configure_attribution",kind:"attribution",label:"Configure Integrated Gradients",description:"Choose a response target, baseline, and integration steps."}):i&&t==="nla"?s({id:"configure_nla",kind:"nla",label:"Configure NLA job",description:"Check profile compatibility and compute an exact explanation."}):i&&t==="patching"?s({id:"configure_patching",kind:"patching",label:"Configure causal patching",description:"Select a changed prompt, component, layer, and target."}):i&&t==="intervention"?s({id:"configure_intervention",kind:"intervention",label:"Configure intervention",description:"Define the contrast, scale, position range, and generation target."}):i&&s(ka()),n.evidenceClass==="causal"?(t!=="intervention"&&s({id:"open_intervention",kind:"intervention",label:"Open intervention comparison",description:"Inspect whether a controlled steering change alters generation."}),t!=="overview"&&s(ka()),t!=="attribution"&&s(Wi())):(t!=="patching"&&s(Mh()),t!=="attribution"&&s(Wi()),t!=="nla"&&s(Ph()),t!=="overview"&&s(ka())),a.slice(0,3)}function Mh(){return{id:"open_patching",kind:"patching",label:"Run causal patching",description:"Measure a replacement effect instead of inferring causality from a proxy."}}function Wi(){return{id:"open_attribution",kind:"attribution",label:"Open target attribution",description:"Inspect signed or target-specific token evidence."}}function Ph(){return{id:"open_nla",kind:"nla",label:"Open exact NLA",description:"Check activation explanation, compatibility, and decoder fidelity."}}function ka(){return{id:"open_overview",kind:"overview",label:"Return to evidence map",description:"Review available, supporting, and contradictory evidence together."}}function Wh(t){if(t==="configure_attribution"||t==="open_attribution")return{view:"attribution",anchorId:"attribution-job"};if(t==="configure_nla"||t==="open_nla")return{view:"nla",anchorId:"nla-job"};if(t==="configure_patching"||t==="open_patching")return{view:"patching",anchorId:"patching-job"};if(t==="configure_intervention"||t==="open_intervention")return{view:"intervention",anchorId:"intervention-job"};if(t==="open_overview")return{view:"overview"}}function bo(t,n=40){const a=document.getElementById(t);if(a){a.scrollIntoView({block:"start"}),a.focus({preventScroll:!0});return}n>1&&window.setTimeout(()=>bo(t,n-1),25)}function zh(t,n,a){var m,x,w,N;const s=new Set(n.tokens.map(A=>A.index)),i=t.selection.targetTokenIndex??t.selection.tokenIndex,r=s.has(i)?i:s.has(t.selection.tokenIndex)?t.selection.tokenIndex:((m=n.tokens[0])==null?void 0:m.index)??a.tokenIndex,o=t.selection.sourceTokenIndex??r,l=s.has(o)?Math.min(o,r):r,c=n.layers.includes(t.selection.layer)?t.selection.layer:n.layers[n.layers.length-1]??a.layer,d=t.selection.tokenRange,p=d&&s.has(d[0])&&s.has(d[1])?[Math.min(...d),Math.max(...d)]:void 0,g=n.attentionHeads.filter(A=>A.layer===c),b=n.mlpNeurons.filter(A=>A.layer===c),_=n.attributionMethods.filter(A=>A.available),y=n.attributionMethods.some(A=>A.id===t.selection.trackName)?t.selection.trackName:((x=_[0])==null?void 0:x.id)??a.trackName;return{...t.selection,tokenIndex:r,sourceTokenIndex:l,targetTokenIndex:r,tokenRange:p,layer:c,headId:g.some(A=>A.id===t.selection.headId)||io(t.selection.headId)||as(t.selection.headId)||Mm(g,t.selection.headId)?t.selection.headId:((w=g[0])==null?void 0:w.id)??a.headId,attentionEdgeMode:t.selection.attentionEdgeMode??"incoming",nlaComponent:t.selection.nlaComponent??a.nlaComponent,neuronId:b.some(A=>A.id===t.selection.neuronId)?t.selection.neuronId:((N=b[0])==null?void 0:N.id)??a.neuronId,trackName:y,metric:t.selection.view==="attribution"&&t.selection.metric===t.selection.trackName?y:t.selection.metric,pinnedItems:t.pinnedItems.slice(-4)}}function Dh(t,n){const a=t.timeline??{mode:"token",metric:"risk",query:""};return{mode:a.mode,metric:a.metric==="probe"&&!n.tokens.some(s=>s.probeScore!==void 0)?"risk":a.metric,query:a.query.slice(0,256)}}const zi={residual:[10,34],attention:[14,36],mlp:[20,42],attribution:[14,38],nla:[14,38],patching:[32,64]};function Yh(t){if(!t)return{};const n={};for(const a of Object.keys(zi)){const s=t[a];if(!s)continue;const[i,r]=zi[a];n[a]={...s,size:Math.max(i,Math.min(r,s.size))}}return n}function qh(t){return t==="patching_effect"?"effect":t==="patching_score"?"score":"recovery"}function xo(t,n){if(t)return n==="patching_effect"?t.causalEffect:n==="patching_score"?t.patchedScore:t.recoveryPercentage}function ss(t,n){const a=n==="patching_effect"?"patchingCausalEffect":n==="patching_score"?"patchingPatchedScore":"patchingRecovery";return t.metricProvenance[a]??{label:"Activation patching",method:"clean activation replacement",semantics:"Causal target-logit response to one activation replacement.",normalization:"none",kind:"causal"}}function is(t){return t.metricProvenance.interventionTargetLogitDelta??{label:"Target logit delta",method:"normalized contrastive activation steering",semantics:"Steered target-token logit minus the original target-token logit.",normalization:"none; raw logit difference",kind:"causal"}}const va=256,Hh=64;function Di(t,n,a,s){if(n.length===0)return;const i=Fh(n,[a,s],Hh).map(l=>({tokenIndex:l.index,tokenId:l.tokenId,tokenText:l.text})),r=i.map(l=>i.map(c=>{var p;if(c.tokenIndex>l.tokenIndex)return null;const d=(p=t.distributionByToken[l.tokenIndex])==null?void 0:p[c.tokenIndex];return Number.isFinite(d)&&d!==void 0&&d>=0&&d<=1?d:null}));if(r.every((l,c)=>l.every((d,p)=>i[p].tokenIndex>i[c].tokenIndex||d!==null)))return{schemaVersion:"1.0",kind:"attention_matrix",label:`${St(t)} · ${n.length}×${n.length}`,originalSize:n.length,sampled:i.length<n.length,axis:i,values:r}}function Fh(t,n,a){if(t.length<=a)return t;const s=new Set;for(let r=0;r<a;r+=1)s.add(Math.round(r*(t.length-1)/(a-1)));const i=new Set([0,t.length-1]);for(const r of n){const o=t.findIndex(c=>c.index===r);if(o<0||(i.add(o),s.has(o)))continue;const l=[...s].filter(c=>!i.has(c)).sort((c,d)=>Math.abs(c-o)-Math.abs(d-o))[0];l!==void 0&&s.delete(l),s.add(o)}return[...s].sort((r,o)=>r-o).map(r=>t[r])}function yn({kind:t,label:n,axis:a,signed:s,tokens:i,values:r,preserveTokenIndex:o}){const l=i.flatMap(d=>{const p=r[d.index];return Number.isFinite(p)?[{tokenIndex:d.index,tokenId:d.tokenId,tokenText:d.text,value:p}]:[]});if(l.length===0)return;let c=l;if(l.length>va){const d=new Set;for(let g=0;g<va;g+=1)d.add(Math.round(g*(l.length-1)/(va-1)));const p=l.findIndex(g=>g.tokenIndex===o);if(p>=0&&!d.has(p)){const g=[...d].filter(b=>b!==0&&b!==l.length-1).sort((b,_)=>Math.abs(b-p)-Math.abs(_-p))[0];g!==void 0&&d.delete(g),d.add(p)}c=[...d].sort((g,b)=>g-b).map(g=>l[g])}return{schemaVersion:"1.0",kind:t,label:n,axis:a,signed:s,originalLength:l.length,sampled:c.length<l.length,points:c}}function wo(t,n,a){return t==="attention"?St(n):t==="mlp"?(a==null?void 0:a.id)??"MLP":"resid_post"}Po.createRoot(document.getElementById("root")).render(e.jsx(Le.StrictMode,{children:e.jsx(eh,{})}));export{Qh as A,as as B,io as C,dl as D,jt as E,Gl as J,Vh as M,ro as a,co as b,Ye as c,St as d,An as e,Ka as f,Lm as g,Rm as h,lo as i,wn as j,tu as k,tr as l,tc as m,Ga as n,bu as o,oo as p,zd as q,Dd as r,nu as s,Ac as t,ml as u,Ud as v,ts as w,Qa as x,Un as y,ol as z};
