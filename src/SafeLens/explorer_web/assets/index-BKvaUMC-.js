const __vite__mapDeps=(i,m=__vite__mapDeps,d=(m.f||(m.f=["assets/AttentionPatternMatrix-Cd-NyDqB.js","assets/vendor-react-Dk8-RHi1.js","assets/SpecializedMatrixCanvas-BNxFUbvF.js","assets/MatrixTokenDetail-B60_jTDK.js","assets/useMatrixRangeBrush-CLq3R7rv.js","assets/vendor-icons-CO8bWA-z.js","assets/scrollElementInlineCenter-F7g_gc4Q.js","assets/vendor-schema-BNsPtHlQ.js","assets/ResidualLogitLens-C9NFCh1i.js","assets/MLPActivationMatrix-DAC0KnPJ.js","assets/SignedAttributionMatrix-C_NUf6xD.js","assets/NLAFidelityMatrix-Yw9l0HP-.js","assets/AttributionJobPanel-CT0PasHz.js","assets/NLAJobPanel-D9lvlc6d.js","assets/PatchingJobPanel-Cuj0kn0X.js","assets/PatchingCausalMatrix-plYPnhg4.js","assets/InterventionJobPanel-BdPDPHyE.js","assets/InterventionComparison-Dfi76Y3W.js","assets/CompareDrawer-47BqcgwV.js"])))=>i.map(i=>d[i]);
var Ao=Object.defineProperty;var To=(e,n,a)=>n in e?Ao(e,n,{enumerable:!0,configurable:!0,writable:!0,value:a}):e[n]=a;var qt=(e,n,a)=>To(e,typeof n!="symbol"?n+"":n,a);import{r as m,j as t,a as So,R as Ce,c as Co}from"./vendor-react-Dk8-RHi1.js";import{C as Rt,H as Ti,Z as Si,M as Ci,P as Ni,a as Ri,R as qn,b as Hn,c as Lt,d as Ln,G as ot,X as Je,e as fn,B as No,T as lt,I as Ro,f as Xe,L as Wt,g as Lo,h as Fn,S as $t,F as $o,U as Li,i as Vt,j as dt,k as $i,l as Ei,m as _n,n as Eo,o as Sa,p as tt,D as yt,q as Et,r as Mo,s as Po,t as vt,u as Bt,v as Un,W as Wo,w as Ca,x as zo,y as Do,z as Na,A as Ve,E as kt,J as Ra,K as bn,N as Kn,O as Yo,Q as Mi,V as Mt,Y as On,_ as qo,$ as Pi,a0 as La,a1 as Wi,a2 as Qt,a3 as zi,a4 as Ho,a5 as Fo,a6 as Uo,a7 as Di,a8 as Ko,a9 as $n,aa as hs,ab as Oo,ac as Vo,ad as pa,ae as Bo,af as $a,ag as Qo}from"./vendor-icons-CO8bWA-z.js";import{o as Q,b as fe,n as _,_ as ye,s as p,a as ie,l as $e,r as Pt,u as Jt,t as ya}from"./vendor-schema-BNsPtHlQ.js";(function(){const n=document.createElement("link").relList;if(n&&n.supports&&n.supports("modulepreload"))return;for(const i of document.querySelectorAll('link[rel="modulepreload"]'))s(i);new MutationObserver(i=>{for(const r of i)if(r.type==="childList")for(const o of r.addedNodes)o.tagName==="LINK"&&o.rel==="modulepreload"&&s(o)}).observe(document,{childList:!0,subtree:!0});function a(i){const r={};return i.integrity&&(r.integrity=i.integrity),i.referrerPolicy&&(r.referrerPolicy=i.referrerPolicy),i.crossOrigin==="use-credentials"?r.credentials="include":i.crossOrigin==="anonymous"?r.credentials="omit":r.credentials="same-origin",r}function s(i){if(i.ep)return;i.ep=!0;const r=a(i);fetch(i.href,r)}})();const Jo="modulepreload",Go=function(e){return"/"+e},ps={},st=function(n,a,s){let i=Promise.resolve();if(a&&a.length>0){let o=function(d){return Promise.all(d.map(h=>Promise.resolve(h).then(f=>({status:"fulfilled",value:f}),f=>({status:"rejected",reason:f}))))};document.getElementsByTagName("link");const l=document.querySelector("meta[property=csp-nonce]"),c=(l==null?void 0:l.nonce)||(l==null?void 0:l.getAttribute("nonce"));i=o(a.map(d=>{if(d=Go(d),d in ps)return;ps[d]=!0;const h=d.endsWith(".css"),f=h?'[rel="stylesheet"]':"";if(document.querySelector(`link[href="${d}"]${f}`))return;const b=document.createElement("link");if(b.rel=h?"stylesheet":Jo,h||(b.as="script"),b.crossOrigin="",b.href=d,c&&b.setAttribute("nonce",c),document.head.appendChild(b),h)return new Promise((g,y)=>{b.addEventListener("load",g),b.addEventListener("error",()=>y(new Error(`Unable to preload CSS for ${d}`)))})}))}function r(o){const l=new Event("vite:preloadError",{cancelable:!0});if(l.payload=o,window.dispatchEvent(l),!l.defaultPrevented)throw o}return i.then(o=>{for(const l of o||[])l.status==="rejected"&&r(l.reason);return n().catch(r)})},Yi={runId:"real-hf-tiny-gpt2-local-explorer",modelName:"sshleifer/tiny-gpt2",modelSource:"huggingface",sampleId:"real-forward-cache-001",prompt:"User: Compare a benign safety explanation with a jailbreak strategy and explain which tokens trigger the monitor.",tokens:[{index:0,text:"User",tokenId:12982,source:"prompt",isSpecial:!1,risk:.253,attribution:.002},{index:1,text:":",tokenId:25,source:"prompt",isSpecial:!1,risk:.846,attribution:.999},{index:2,text:" Compare",tokenId:27814,source:"prompt",isSpecial:!1,risk:.483,attribution:.949},{index:3,text:" a",tokenId:257,source:"prompt",isSpecial:!1,risk:.155,attribution:.112},{index:4,text:" benign",tokenId:32293,source:"prompt",isSpecial:!1,risk:.311,attribution:.815},{index:5,text:" safety",tokenId:3747,source:"prompt",isSpecial:!1,risk:.392,attribution:.934},{index:6,text:" explanation",tokenId:7468,source:"prompt",isSpecial:!1,risk:.143,attribution:.004},{index:7,text:" with",tokenId:351,source:"prompt",isSpecial:!1,risk:.378,attribution:.908},{index:8,text:" a",tokenId:257,source:"prompt",isSpecial:!1,risk:.524,attribution:.998},{index:9,text:" jail",tokenId:7356,source:"prompt",isSpecial:!1,risk:.728,attribution:.996},{index:10,text:"break",tokenId:9032,source:"prompt",isSpecial:!1,risk:1,attribution:1},{index:11,text:" strategy",tokenId:4811,source:"prompt",isSpecial:!1,risk:.532,attribution:.998},{index:12,text:" and",tokenId:290,source:"prompt",isSpecial:!1,risk:.496,attribution:.991},{index:13,text:" explain",tokenId:4727,source:"prompt",isSpecial:!1,risk:.298,attribution:.307},{index:14,text:" which",tokenId:543,source:"prompt",isSpecial:!1,risk:0,attribution:0},{index:15,text:" tokens",tokenId:16326,source:"prompt",isSpecial:!1,risk:.526,attribution:.032},{index:16,text:" trigger",tokenId:7616,source:"prompt",isSpecial:!1,risk:.707,attribution:.971},{index:17,text:" the",tokenId:262,source:"prompt",isSpecial:!1,risk:.881,attribution:1},{index:18,text:" monitor",tokenId:5671,source:"prompt",isSpecial:!1,risk:.136,attribution:.001},{index:19,text:".",tokenId:13,source:"prompt",isSpecial:!1,risk:.384,attribution:.367}],layers:[0,1],nla:[{tokenIndex:9,layer:1,component:"resid_post",explanation:"Real activation captured from sshleifer/tiny-gpt2, but no registered NLA profile matches this smoke-test model/d_model=2. Supported profiles: qwen2.5-7b-l20, gemma3-12b-l32. Run a matching Qwen/Gemma profile to produce an AV/AR explanation.",cosine:0,mse:0,activationNorm:.041,status:"unavailable",profile:null,source:"real_model_cache",token:" jail"},{tokenIndex:10,layer:1,component:"attn_result",explanation:"Real activation captured from sshleifer/tiny-gpt2, but no registered NLA profile matches this smoke-test model/d_model=2. Supported profiles: qwen2.5-7b-l20, gemma3-12b-l32. Run a matching Qwen/Gemma profile to produce an AV/AR explanation.",cosine:0,mse:0,activationNorm:.07,status:"unavailable",profile:null,source:"real_model_cache",token:"break"},{tokenIndex:11,layer:1,component:"mlp_out",explanation:"Real activation captured from sshleifer/tiny-gpt2, but no registered NLA profile matches this smoke-test model/d_model=2. Supported profiles: qwen2.5-7b-l20, gemma3-12b-l32. Run a matching Qwen/Gemma profile to produce an AV/AR explanation.",cosine:0,mse:0,activationNorm:.047,status:"unavailable",profile:null,source:"real_model_cache",token:" strategy"}],nlaCompatibility:{modelName:"sshleifer/tiny-gpt2",dModel:2,availableLayers:[0,1],profiles:[{name:"qwen2.5-7b-l20",baseModel:"Qwen/Qwen2.5-7B-Instruct",layer:20,component:"resid_post",dModel:3584,modelMatches:!1,layerAvailable:!1,dModelMatches:!1,status:"incompatible",reason:"model requires Qwen/Qwen2.5-7B-Instruct; layer L20 is not cached; d_model requires 3584, run has 2"},{name:"gemma3-12b-l32",baseModel:"google/gemma-3-12b-it",layer:32,component:"resid_post",dModel:3840,modelMatches:!1,layerAvailable:!1,dModelMatches:!1,status:"incompatible",reason:"model requires google/gemma-3-12b-it; layer L32 is not cached; d_model requires 3840, run has 2"}]},attentionHeads:[{id:"L0H0",layer:0,head:0,role:"real attention pattern",riskContribution:.25,entropy:2.996,distributionByToken:[[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.5,.5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.333,.333,.333,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.25,.25,.25,.25,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.2,.2,.2,.2,.2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.167,.167,.167,.167,.167,.167,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.143,.143,.143,.143,.143,.143,.143,0,0,0,0,0,0,0,0,0,0,0,0,0],[.125,.125,.125,.125,.125,.125,.125,.125,0,0,0,0,0,0,0,0,0,0,0,0],[.111,.111,.111,.111,.111,.111,.111,.111,.111,0,0,0,0,0,0,0,0,0,0,0],[.1,.1,.1,.1,.1,.1,.1,.1,.1,.1,0,0,0,0,0,0,0,0,0,0],[.091,.091,.091,.091,.091,.091,.091,.091,.091,.091,.091,0,0,0,0,0,0,0,0,0],[.083,.083,.083,.083,.083,.083,.083,.083,.083,.083,.083,.083,0,0,0,0,0,0,0,0],[.077,.077,.077,.077,.077,.077,.077,.077,.077,.077,.077,.077,.077,0,0,0,0,0,0,0],[.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,0,0,0,0,0,0],[.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,0,0,0,0,0],[.062,.063,.063,.062,.063,.063,.062,.063,.063,.063,.063,.063,.063,.062,.062,.062,0,0,0,0],[.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,0,0,0],[.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,0,0],[.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,0],[.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05]]},{id:"L0H1",layer:0,head:1,role:"real attention pattern",riskContribution:.25,entropy:2.996,distributionByToken:[[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.5,.5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.333,.333,.333,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.25,.25,.25,.25,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.2,.2,.2,.2,.2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.167,.167,.167,.167,.167,.167,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.143,.143,.143,.143,.143,.143,.143,0,0,0,0,0,0,0,0,0,0,0,0,0],[.125,.125,.125,.125,.125,.125,.125,.125,0,0,0,0,0,0,0,0,0,0,0,0],[.111,.111,.111,.111,.111,.111,.111,.111,.111,0,0,0,0,0,0,0,0,0,0,0],[.1,.1,.1,.1,.1,.1,.1,.1,.1,.1,0,0,0,0,0,0,0,0,0,0],[.091,.091,.091,.091,.091,.091,.091,.091,.091,.091,.091,0,0,0,0,0,0,0,0,0],[.083,.083,.083,.083,.083,.083,.083,.083,.083,.083,.083,.083,0,0,0,0,0,0,0,0],[.077,.077,.077,.077,.077,.077,.077,.077,.077,.077,.077,.077,.077,0,0,0,0,0,0,0],[.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,0,0,0,0,0,0],[.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,0,0,0,0,0],[.063,.062,.062,.063,.062,.062,.063,.062,.062,.062,.062,.062,.062,.063,.063,.063,0,0,0,0],[.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,0,0,0],[.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,0,0],[.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,0],[.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05]]},{id:"L1H0",layer:1,head:0,role:"real attention pattern",riskContribution:.25,entropy:2.996,distributionByToken:[[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.5,.5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.333,.333,.333,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.25,.25,.25,.25,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.2,.2,.2,.2,.2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.167,.167,.167,.167,.167,.167,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.143,.143,.143,.143,.143,.143,.143,0,0,0,0,0,0,0,0,0,0,0,0,0],[.125,.125,.125,.125,.125,.125,.125,.125,0,0,0,0,0,0,0,0,0,0,0,0],[.111,.111,.111,.111,.111,.111,.111,.111,.111,0,0,0,0,0,0,0,0,0,0,0],[.1,.1,.1,.1,.1,.1,.1,.1,.1,.1,0,0,0,0,0,0,0,0,0,0],[.091,.091,.091,.091,.091,.091,.091,.091,.091,.091,.091,0,0,0,0,0,0,0,0,0],[.083,.083,.083,.083,.083,.083,.083,.083,.083,.083,.083,.083,0,0,0,0,0,0,0,0],[.077,.077,.077,.077,.077,.077,.077,.077,.077,.077,.077,.077,.077,0,0,0,0,0,0,0],[.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,0,0,0,0,0,0],[.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,0,0,0,0,0],[.062,.063,.063,.062,.063,.063,.062,.063,.063,.063,.063,.063,.063,.062,.062,.062,0,0,0,0],[.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,0,0,0],[.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,0,0],[.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,0],[.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05]]},{id:"L1H1",layer:1,head:1,role:"real attention pattern",riskContribution:.25,entropy:2.996,distributionByToken:[[1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.5,.5,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.334,.333,.333,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.25,.25,.25,.25,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.2,.2,.2,.2,.2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.167,.167,.167,.167,.167,.167,0,0,0,0,0,0,0,0,0,0,0,0,0,0],[.143,.143,.143,.143,.143,.143,.143,0,0,0,0,0,0,0,0,0,0,0,0,0],[.125,.125,.125,.125,.125,.125,.125,.125,0,0,0,0,0,0,0,0,0,0,0,0],[.111,.111,.111,.111,.111,.111,.111,.111,.111,0,0,0,0,0,0,0,0,0,0,0],[.1,.1,.1,.1,.1,.1,.1,.1,.1,.1,0,0,0,0,0,0,0,0,0,0],[.091,.091,.091,.091,.091,.091,.091,.091,.091,.091,.091,0,0,0,0,0,0,0,0,0],[.083,.083,.083,.083,.083,.083,.083,.083,.083,.083,.083,.083,0,0,0,0,0,0,0,0],[.077,.077,.077,.077,.077,.077,.077,.077,.077,.077,.077,.077,.077,0,0,0,0,0,0,0],[.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,.071,0,0,0,0,0,0],[.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,.067,0,0,0,0,0],[.062,.063,.063,.062,.063,.063,.062,.063,.063,.063,.063,.063,.063,.062,.062,.062,0,0,0,0],[.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,.059,0,0,0],[.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,.056,0,0],[.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,.053,0],[.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05,.05]]}],mlpNeurons:[{id:"L0N0006",layer:0,neuron:6,label:"real MLP post neuron",activation:1,riskContribution:.175,topTokens:[10,17,1],positiveTopTokens:[10,17,1],negativeTopTokens:[14,18,0],activationsByToken:[-.021928,.023653,.021389,-.017681,.015592,.020802,-.021785,.01965,.023637,.023491,.023713,.02362,.023261,-.00957,-.021953,-.02072,.02241,.023709,-.021937,-.006694],maxAbsoluteActivation:.023713},{id:"L0N0001",layer:0,neuron:1,label:"real MLP post neuron",activation:.698,riskContribution:.175,topTokens:[14,18,0],positiveTopTokens:[14,18,0],negativeTopTokens:[10,17,1],activationsByToken:[.016543,-.015759,-.014333,.013173,-.010604,-.01396,.016428,-.013226,-.015749,-.015658,-.015797,-.015739,-.015513,.006966,.016563,.015576,-.014978,-.015794,.01655,.004834],maxAbsoluteActivation:.016563},{id:"L0N0004",layer:0,neuron:4,label:"real MLP post neuron",activation:.527,riskContribution:.172,topTokens:[10,17,1],positiveTopTokens:[10,17,1],negativeTopTokens:[14,18,0],activationsByToken:[-.01196,.012473,.011296,-.00961,.008267,.01099,-.011881,.01039,.012465,.012389,.012505,.012456,.01227,-.005168,-.011974,-.01129,.011828,.012502,-.011965,-.003607],maxAbsoluteActivation:.012505},{id:"L0N0002",layer:0,neuron:2,label:"real MLP post neuron",activation:.359,riskContribution:.172,topTokens:[14,18,0],positiveTopTokens:[14,18,0],negativeTopTokens:[10,17,1],activationsByToken:[.0085,-.0083,-.00754,.006785,-.005561,-.007341,.008441,-.006951,-.008294,-.008246,-.00832,-.008289,-.008169,.003604,.00851,.008009,-.007883,-.008319,.008504,.002505],maxAbsoluteActivation:.00851},{id:"L0N0005",layer:0,neuron:5,label:"real MLP post neuron",activation:.323,riskContribution:.172,topTokens:[10,17,1],positiveTopTokens:[10,17,1],negativeTopTokens:[14,18,0],activationsByToken:[-.007439,.007643,.006927,-.005968,.005078,.00674,-.007389,.006374,.007638,.007592,.007662,.007633,.00752,-.0032,-.007448,-.007019,.00725,.007661,-.007442,-.002232],maxAbsoluteActivation:.007662},{id:"L0N0007",layer:0,neuron:7,label:"real MLP post neuron",activation:.302,riskContribution:.171,topTokens:[10,17,1],positiveTopTokens:[10,17,1],negativeTopTokens:[14,18,0],activationsByToken:[-.006956,.007135,.006467,-.005579,.004742,.006293,-.006909,.005951,.00713,.007087,.007153,.007126,.00702,-.002991,-.006964,-.006563,.006769,.007152,-.006959,-.002085],maxAbsoluteActivation:.007153},{id:"L0N0003",layer:0,neuron:3,label:"real MLP post neuron",activation:.228,riskContribution:.171,topTokens:[14,18,0],positiveTopTokens:[14,18,0],negativeTopTokens:[10,17,1],activationsByToken:[.005394,-.005318,-.004829,.004309,-.003558,-.004701,.005357,-.00445,-.005315,-.005283,-.005331,-.005311,-.005234,.002293,.0054,.005083,-.00505,-.00533,.005396,.001595],maxAbsoluteActivation:.0054},{id:"L0N0000",layer:0,neuron:0,label:"real MLP post neuron",activation:.136,riskContribution:.171,topTokens:[10,17,1],positiveTopTokens:[10,17,1],negativeTopTokens:[14,18,0],activationsByToken:[-.003167,.003209,.00291,-.002537,.002137,.002832,-.003145,.002679,.003207,.003188,.003217,.003205,.003157,-.001357,-.003171,-.002987,.003045,.003216,-.003168,-945e-6],maxAbsoluteActivation:.003217},{id:"L1N0000",layer:1,neuron:0,label:"real MLP post neuron",activation:1,riskContribution:.178,topTokens:[10,17,1],positiveTopTokens:[10,17,1],negativeTopTokens:[14,18,0],activationsByToken:[-.028428,.031367,.028136,-.022469,.019793,.027279,-.028233,.025585,.031346,.031144,.031451,.031323,.030825,-.011125,-.028457,-.026754,.02961,.031446,-.028436,-.007715],maxAbsoluteActivation:.031451},{id:"L1N0004",layer:1,neuron:4,label:"real MLP post neuron",activation:.718,riskContribution:.179,topTokens:[14,18,0],positiveTopTokens:[14,18,0],negativeTopTokens:[10,17,1],activationsByToken:[.022556,-.0211,-.01908,.017507,-.013711,-.018539,.022387,-.017462,-.021087,-.020962,-.021152,-.021073,-.020763,.008383,.022581,.021118,-.020006,-.021149,.022563,.005757],maxAbsoluteActivation:.022581},{id:"L1N0003",layer:1,neuron:3,label:"real MLP post neuron",activation:.553,riskContribution:.175,topTokens:[10,17,1],positiveTopTokens:[10,17,1],negativeTopTokens:[14,18,0],activationsByToken:[-.016391,.017349,.015591,-.012893,.011024,.015124,-.016276,.014199,.017337,.017228,.017394,.017325,.017054,-.006328,-.016408,-.015404,.016394,.017391,-.016395,-.004378],maxAbsoluteActivation:.017394},{id:"L1N0007",layer:1,neuron:7,label:"real MLP post neuron",activation:.465,riskContribution:.174,topTokens:[10,17,1],positiveTopTokens:[10,17,1],negativeTopTokens:[14,18,0],activationsByToken:[-.013892,.01458,.013108,-.010916,.009279,.012717,-.013793,.011942,.014571,.014479,.014618,.01456,.014334,-.005349,-.013906,-.013052,.013781,.014616,-.013896,-.003698],maxAbsoluteActivation:.014618},{id:"L1N0006",layer:1,neuron:6,label:"real MLP post neuron",activation:.303,riskContribution:.174,topTokens:[10,17,1],positiveTopTokens:[10,17,1],negativeTopTokens:[14,18,0],activationsByToken:[-.009197,.009503,.00855,-.007214,.006064,.008297,-.009131,.007794,.009497,.009438,.009528,.00949,.009344,-.003524,-.009206,-.008636,.008986,.009526,-.009199,-.002434],maxAbsoluteActivation:.009528},{id:"L1N0002",layer:1,neuron:2,label:"real MLP post neuron",activation:.232,riskContribution:.173,topTokens:[10,17,1],positiveTopTokens:[10,17,1],negativeTopTokens:[14,18,0],activationsByToken:[-.007105,.007292,.006563,-.005569,.004659,.006369,-.007054,.005984,.007287,.007242,.007311,.007282,.00717,-.002716,-.007113,-.006671,.006896,.007309,-.007107,-.001876],maxAbsoluteActivation:.007311},{id:"L1N0001",layer:1,neuron:1,label:"real MLP post neuron",activation:.172,riskContribution:.173,topTokens:[14,18,0],positiveTopTokens:[14,18,0],negativeTopTokens:[10,17,1],activationsByToken:[.005403,-.005327,-.004804,.004216,-.003428,-.004664,.005363,-.004387,-.005323,-.005291,-.00534,-.00532,-.005239,.00204,.005408,.005066,-.005043,-.005339,.005404,.001405],maxAbsoluteActivation:.005408},{id:"L1N0005",layer:1,neuron:5,label:"real MLP post neuron",activation:.043,riskContribution:.172,topTokens:[10,17,1],positiveTopTokens:[10,17,1],negativeTopTokens:[14,18,0],activationsByToken:[-.001334,.001344,.001211,-.001044,861e-6,.001175,-.001325,.001105,.001343,.001335,.001347,.001342,.001322,-507e-6,-.001336,-.001252,.001271,.001347,-.001335,-35e-5],maxAbsoluteActivation:.001347}],residualCells:[{layer:0,tokenIndex:0,norm:.044,rawDirection:-.013081,riskDirection:.252,semanticDensity:.598},{layer:0,tokenIndex:1,norm:.053,rawDirection:.053175,riskDirection:.847,semanticDensity:.74},{layer:0,tokenIndex:2,norm:.013,rawDirection:.012987,riskDirection:.486,semanticDensity:.127},{layer:0,tokenIndex:3,norm:.036,rawDirection:-.02387,riskDirection:.155,semanticDensity:.472},{layer:0,tokenIndex:4,norm:.017,rawDirection:-.006022,riskDirection:.315,semanticDensity:.185},{layer:0,tokenIndex:5,norm:.01,rawDirection:.003024,riskDirection:.396,semanticDensity:.077},{layer:0,tokenIndex:6,norm:.026,rawDirection:-.025226,riskDirection:.142,semanticDensity:.323},{layer:0,tokenIndex:7,norm:.01,rawDirection:.001409,riskDirection:.382,semanticDensity:.067},{layer:0,tokenIndex:8,norm:.05,rawDirection:.017587,riskDirection:.527,semanticDensity:.681},{layer:0,tokenIndex:9,norm:.041,rawDirection:.040134,riskDirection:.73,semanticDensity:.557},{layer:0,tokenIndex:10,norm:.07,rawDirection:.07019,riskDirection:1,semanticDensity:1},{layer:0,tokenIndex:11,norm:.045,rawDirection:.018461,riskDirection:.535,semanticDensity:.612},{layer:0,tokenIndex:12,norm:.022,rawDirection:.014512,riskDirection:.5,semanticDensity:.252},{layer:0,tokenIndex:13,norm:.012,rawDirection:-.007909,riskDirection:.298,semanticDensity:.101},{layer:0,tokenIndex:14,norm:.041,rawDirection:-.041081,riskDirection:0,semanticDensity:.554},{layer:0,tokenIndex:15,norm:.05,rawDirection:.017092,riskDirection:.523,semanticDensity:.696},{layer:0,tokenIndex:16,norm:.052,rawDirection:.037751,riskDirection:.708,semanticDensity:.718},{layer:0,tokenIndex:17,norm:.059,rawDirection:.057025,riskDirection:.882,semanticDensity:.824},{layer:0,tokenIndex:18,norm:.035,rawDirection:-.026055,riskDirection:.135,semanticDensity:.461},{layer:0,tokenIndex:19,norm:.005,rawDirection:.001673,riskDirection:.384,semanticDensity:0},{layer:1,tokenIndex:0,norm:.046,rawDirection:-.012687,riskDirection:.255,semanticDensity:.626},{layer:1,tokenIndex:1,norm:.053,rawDirection:.05284,riskDirection:.844,semanticDensity:.733},{layer:1,tokenIndex:2,norm:.013,rawDirection:.012692,riskDirection:.483,semanticDensity:.118},{layer:1,tokenIndex:3,norm:.035,rawDirection:-.023539,riskDirection:.158,semanticDensity:.454},{layer:1,tokenIndex:4,norm:.018,rawDirection:-.006243,riskDirection:.313,semanticDensity:.202},{layer:1,tokenIndex:5,norm:.012,rawDirection:.002737,riskDirection:.394,semanticDensity:.1},{layer:1,tokenIndex:6,norm:.026,rawDirection:-.024793,riskDirection:.146,semanticDensity:.323},{layer:1,tokenIndex:7,norm:.011,rawDirection:.001134,riskDirection:.379,semanticDensity:.089},{layer:1,tokenIndex:8,norm:.051,rawDirection:.017263,riskDirection:.524,semanticDensity:.706},{layer:1,tokenIndex:9,norm:.041,rawDirection:.039815,riskDirection:.727,semanticDensity:.546},{layer:1,tokenIndex:10,norm:.07,rawDirection:.069871,riskDirection:.997,semanticDensity:.994},{layer:1,tokenIndex:11,norm:.047,rawDirection:.018145,riskDirection:.532,semanticDensity:.637},{layer:1,tokenIndex:12,norm:.023,rawDirection:.014202,riskDirection:.497,semanticDensity:.271},{layer:1,tokenIndex:13,norm:.011,rawDirection:-.007739,riskDirection:.3,semanticDensity:.094},{layer:1,tokenIndex:14,norm:.041,rawDirection:-.040634,riskDirection:.004,semanticDensity:.55},{layer:1,tokenIndex:15,norm:.052,rawDirection:.017505,riskDirection:.527,semanticDensity:.719},{layer:1,tokenIndex:16,norm:.051,rawDirection:.037443,riskDirection:.706,semanticDensity:.697},{layer:1,tokenIndex:17,norm:.059,rawDirection:.056703,riskDirection:.879,semanticDensity:.827},{layer:1,tokenIndex:18,norm:.036,rawDirection:-.025611,riskDirection:.139,semanticDensity:.473},{layer:1,tokenIndex:19,norm:.006,rawDirection:.001786,riskDirection:.385,semanticDensity:.006}],jLens:[],logitLens:[{layer:0,tokenIndex:0,targetTokenId:25,targetTokenText:":",targetLogit:-.010543,targetProbability:1968e-8,targetRank:32530,topPredictions:[{tokenId:5087,tokenText:" factors",logit:.114459,probability:223e-7},{tokenId:13584,tokenText:" mutual",logit:.112374,probability:2226e-8},{tokenId:31685,tokenText:" deflect",logit:.11141,probability:2224e-8},{tokenId:21516,tokenText:" Television",logit:.109414,probability:2219e-8},{tokenId:40169,tokenText:" boils",logit:.107044,probability:2214e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:1,targetTokenId:27814,targetTokenText:" Compare",targetLogit:.017864,targetProbability:2025e-8,targetRank:13162,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.128454,probability:2262e-8},{tokenId:17192,tokenText:" vendors",logit:.126809,probability:2258e-8},{tokenId:38361,tokenText:" intermittent",logit:.116339,probability:2234e-8},{tokenId:43423,tokenText:" hauled",logit:.109236,probability:2218e-8},{tokenId:9702,tokenText:" Brew",logit:.10787,probability:2215e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:2,targetTokenId:257,targetTokenText:" a",targetLogit:.022717,targetProbability:2035e-8,targetRank:9207,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.115576,probability:2233e-8},{tokenId:17192,tokenText:" vendors",logit:.114097,probability:2229e-8},{tokenId:38361,tokenText:" intermittent",logit:.104676,probability:2209e-8},{tokenId:43423,tokenText:" hauled",logit:.098285,probability:2194e-8},{tokenId:9702,tokenText:" Brew",logit:.097056,probability:2192e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:3,targetTokenId:32293,targetTokenText:" benign",targetLogit:.005327,targetProbability:2e-5,targetRank:20177,topPredictions:[{tokenId:5087,tokenText:" factors",logit:.089545,probability:2176e-8},{tokenId:13584,tokenText:" mutual",logit:.087914,probability:2172e-8},{tokenId:31685,tokenText:" deflect",logit:.08716,probability:2171e-8},{tokenId:21516,tokenText:" Television",logit:.085598,probability:2167e-8},{tokenId:40169,tokenText:" boils",logit:.083744,probability:2163e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:4,targetTokenId:3747,targetTokenText:" safety",targetLogit:-.021742,targetProbability:1947e-8,targetRank:44645,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.081969,probability:2159e-8},{tokenId:17192,tokenText:" vendors",logit:.080919,probability:2157e-8},{tokenId:38361,tokenText:" intermittent",logit:.074238,probability:2143e-8},{tokenId:43423,tokenText:" hauled",logit:.069706,probability:2133e-8},{tokenId:9702,tokenText:" Brew",logit:.068834,probability:2131e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:5,targetTokenId:7468,targetTokenText:" explanation",targetLogit:-.020505,targetProbability:1949e-8,targetRank:40262,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.11215,probability:2225e-8},{tokenId:17192,tokenText:" vendors",logit:.110714,probability:2222e-8},{tokenId:38361,tokenText:" intermittent",logit:.101572,probability:2202e-8},{tokenId:43423,tokenText:" hauled",logit:.095371,probability:2188e-8},{tokenId:9702,tokenText:" Brew",logit:.094179,probability:2186e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:6,targetTokenId:351,targetTokenText:" with",targetLogit:-718e-6,targetProbability:1988e-8,targetRank:25594,topPredictions:[{tokenId:5087,tokenText:" factors",logit:.113647,probability:2229e-8},{tokenId:13584,tokenText:" mutual",logit:.111577,probability:2224e-8},{tokenId:31685,tokenText:" deflect",logit:.11062,probability:2222e-8},{tokenId:21516,tokenText:" Television",logit:.108637,probability:2217e-8},{tokenId:40169,tokenText:" boils",logit:.106285,probability:2212e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:7,targetTokenId:257,targetTokenText:" a",targetLogit:.020719,targetProbability:2031e-8,targetRank:9207,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.10541,probability:221e-7},{tokenId:17192,tokenText:" vendors",logit:.104061,probability:2207e-8},{tokenId:38361,tokenText:" intermittent",logit:.095468,probability:2188e-8},{tokenId:43423,tokenText:" hauled",logit:.08964,probability:2176e-8},{tokenId:9702,tokenText:" Brew",logit:.088519,probability:2173e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:8,targetTokenId:7356,targetTokenText:" jail",targetLogit:.026281,targetProbability:2042e-8,targetRank:8709,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.128369,probability:2261e-8},{tokenId:17192,tokenText:" vendors",logit:.126725,probability:2258e-8},{tokenId:38361,tokenText:" intermittent",logit:.116261,probability:2234e-8},{tokenId:43423,tokenText:" hauled",logit:.109163,probability:2218e-8},{tokenId:9702,tokenText:" Brew",logit:.107799,probability:2215e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:9,targetTokenId:9032,targetTokenText:"break",targetLogit:.031787,targetProbability:2053e-8,targetRank:6360,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.127572,probability:226e-7},{tokenId:17192,tokenText:" vendors",logit:.125939,probability:2256e-8},{tokenId:38361,tokenText:" intermittent",logit:.11554,probability:2232e-8},{tokenId:43423,tokenText:" hauled",logit:.108486,probability:2217e-8},{tokenId:9702,tokenText:" Brew",logit:.10713,probability:2214e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:10,targetTokenId:4811,targetTokenText:" strategy",targetLogit:.026769,targetProbability:2043e-8,targetRank:8518,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.12878,probability:2262e-8},{tokenId:17192,tokenText:" vendors",logit:.127132,probability:2259e-8},{tokenId:38361,tokenText:" intermittent",logit:.116634,probability:2235e-8},{tokenId:43423,tokenText:" hauled",logit:.109514,probability:2219e-8},{tokenId:9702,tokenText:" Brew",logit:.108145,probability:2216e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:11,targetTokenId:290,targetTokenText:" and",targetLogit:.0154,targetProbability:202e-7,targetRank:14612,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.128277,probability:2261e-8},{tokenId:17192,tokenText:" vendors",logit:.126635,probability:2257e-8},{tokenId:38361,tokenText:" intermittent",logit:.116179,probability:2234e-8},{tokenId:43423,tokenText:" hauled",logit:.109086,probability:2218e-8},{tokenId:9702,tokenText:" Brew",logit:.107722,probability:2215e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:12,targetTokenId:4727,targetTokenText:" explain",targetLogit:-.022317,targetProbability:1945e-8,targetRank:39841,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.126299,probability:2257e-8},{tokenId:17192,tokenText:" vendors",logit:.124682,probability:2253e-8},{tokenId:38361,tokenText:" intermittent",logit:.114387,probability:223e-7},{tokenId:43423,tokenText:" hauled",logit:.107404,probability:2214e-8},{tokenId:9702,tokenText:" Brew",logit:.106061,probability:2211e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:13,targetTokenId:543,targetTokenText:" which",targetLogit:.007802,targetProbability:2005e-8,targetRank:11957,topPredictions:[{tokenId:5087,tokenText:" factors",logit:.045334,probability:2082e-8},{tokenId:13584,tokenText:" mutual",logit:.044508,probability:208e-7},{tokenId:31685,tokenText:" deflect",logit:.044127,probability:2079e-8},{tokenId:21516,tokenText:" Television",logit:.043336,probability:2078e-8},{tokenId:40169,tokenText:" boils",logit:.042397,probability:2076e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:14,targetTokenId:16326,targetTokenText:" tokens",targetLogit:.04567,targetProbability:2082e-8,targetRank:2554,topPredictions:[{tokenId:5087,tokenText:" factors",logit:.114597,probability:2231e-8},{tokenId:13584,tokenText:" mutual",logit:.112509,probability:2226e-8},{tokenId:31685,tokenText:" deflect",logit:.111544,probability:2224e-8},{tokenId:21516,tokenText:" Television",logit:.109545,probability:2219e-8},{tokenId:40169,tokenText:" boils",logit:.107173,probability:2214e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:15,targetTokenId:7616,targetTokenText:" trigger",targetLogit:-.01032,targetProbability:1969e-8,targetRank:32824,topPredictions:[{tokenId:5087,tokenText:" factors",logit:.107468,probability:2215e-8},{tokenId:13584,tokenText:" mutual",logit:.105511,probability:2211e-8},{tokenId:31685,tokenText:" deflect",logit:.104606,probability:2209e-8},{tokenId:21516,tokenText:" Television",logit:.102731,probability:2204e-8},{tokenId:40169,tokenText:" boils",logit:.100506,probability:22e-6}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:16,targetTokenId:262,targetTokenText:" the",targetLogit:.073626,targetProbability:2141e-8,targetRank:155,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.121483,probability:2246e-8},{tokenId:17192,tokenText:" vendors",logit:.119928,probability:2242e-8},{tokenId:38361,tokenText:" intermittent",logit:.110025,probability:222e-7},{tokenId:43423,tokenText:" hauled",logit:.103308,probability:2205e-8},{tokenId:9702,tokenText:" Brew",logit:.102017,probability:2203e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:17,targetTokenId:5671,targetTokenText:" monitor",targetLogit:-.033165,targetProbability:1924e-8,targetRank:44310,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.128759,probability:2262e-8},{tokenId:17192,tokenText:" vendors",logit:.127111,probability:2258e-8},{tokenId:38361,tokenText:" intermittent",logit:.116615,probability:2235e-8},{tokenId:43423,tokenText:" hauled",logit:.109496,probability:2219e-8},{tokenId:9702,tokenText:" Brew",logit:.108127,probability:2216e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:18,targetTokenId:13,targetTokenText:".",targetLogit:.038063,targetProbability:2066e-8,targetRank:4363,topPredictions:[{tokenId:5087,tokenText:" factors",logit:.114508,probability:223e-7},{tokenId:13584,tokenText:" mutual",logit:.112423,probability:2226e-8},{tokenId:31685,tokenText:" deflect",logit:.111458,probability:2224e-8},{tokenId:21516,tokenText:" Television",logit:.109461,probability:2219e-8},{tokenId:40169,tokenText:" boils",logit:.10709,probability:2214e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:0,tokenIndex:19,targetTokenId:5087,targetTokenText:" factors",targetLogit:.031153,targetProbability:2053e-8,targetRank:1,topPredictions:[{tokenId:5087,tokenText:" factors",logit:.031153,probability:2053e-8},{tokenId:13584,tokenText:" mutual",logit:.030586,probability:2052e-8},{tokenId:31685,tokenText:" deflect",logit:.030324,probability:2051e-8},{tokenId:21516,tokenText:" Television",logit:.02978,probability:205e-7},{tokenId:40169,tokenText:" boils",logit:.029135,probability:2049e-8}],sourceKey:"layer_0.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:0,targetTokenId:25,targetTokenText:":",targetLogit:-.010547,targetProbability:1968e-8,targetRank:32530,topPredictions:[{tokenId:5087,tokenText:" factors",logit:.114501,probability:223e-7},{tokenId:13584,tokenText:" mutual",logit:.112415,probability:2226e-8},{tokenId:31685,tokenText:" deflect",logit:.111451,probability:2224e-8},{tokenId:21516,tokenText:" Television",logit:.109453,probability:2219e-8},{tokenId:40169,tokenText:" boils",logit:.107083,probability:2214e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:1,targetTokenId:27814,targetTokenText:" Compare",targetLogit:.017867,targetProbability:2025e-8,targetRank:13162,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.128476,probability:2262e-8},{tokenId:17192,tokenText:" vendors",logit:.126831,probability:2258e-8},{tokenId:38361,tokenText:" intermittent",logit:.116358,probability:2234e-8},{tokenId:43423,tokenText:" hauled",logit:.109255,probability:2218e-8},{tokenId:9702,tokenText:" Brew",logit:.107889,probability:2215e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:2,targetTokenId:257,targetTokenText:" a",targetLogit:.023019,targetProbability:2035e-8,targetRank:9207,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.117112,probability:2236e-8},{tokenId:17192,tokenText:" vendors",logit:.115613,probability:2233e-8},{tokenId:38361,tokenText:" intermittent",logit:.106067,probability:2212e-8},{tokenId:43423,tokenText:" hauled",logit:.099591,probability:2197e-8},{tokenId:9702,tokenText:" Brew",logit:.098346,probability:2195e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:3,targetTokenId:32293,targetTokenText:" benign",targetLogit:.005477,targetProbability:2e-5,targetRank:20177,topPredictions:[{tokenId:5087,tokenText:" factors",logit:.092072,probability:2181e-8},{tokenId:13584,tokenText:" mutual",logit:.090395,probability:2178e-8},{tokenId:31685,tokenText:" deflect",logit:.08962,probability:2176e-8},{tokenId:21516,tokenText:" Television",logit:.088013,probability:2172e-8},{tokenId:40169,tokenText:" boils",logit:.086107,probability:2168e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:4,targetTokenId:3747,targetTokenText:" safety",targetLogit:-.023186,targetProbability:1944e-8,targetRank:44645,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.087413,probability:2171e-8},{tokenId:17192,tokenText:" vendors",logit:.086294,probability:2169e-8},{tokenId:38361,tokenText:" intermittent",logit:.079168,probability:2153e-8},{tokenId:43423,tokenText:" hauled",logit:.074335,probability:2143e-8},{tokenId:9702,tokenText:" Brew",logit:.073406,probability:2141e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:5,targetTokenId:7468,targetTokenText:" explanation",targetLogit:-.020874,targetProbability:1948e-8,targetRank:40262,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.11417,probability:223e-7},{tokenId:17192,tokenText:" vendors",logit:.112708,probability:2226e-8},{tokenId:38361,tokenText:" intermittent",logit:.103402,probability:2206e-8},{tokenId:43423,tokenText:" hauled",logit:.097089,probability:2192e-8},{tokenId:9702,tokenText:" Brew",logit:.095875,probability:2189e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:6,targetTokenId:351,targetTokenText:" with",targetLogit:-718e-6,targetProbability:1988e-8,targetRank:25594,topPredictions:[{tokenId:5087,tokenText:" factors",logit:.113716,probability:2229e-8},{tokenId:13584,tokenText:" mutual",logit:.111645,probability:2224e-8},{tokenId:31685,tokenText:" deflect",logit:.110687,probability:2222e-8},{tokenId:21516,tokenText:" Television",logit:.108704,probability:2218e-8},{tokenId:40169,tokenText:" boils",logit:.106349,probability:2212e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:7,targetTokenId:257,targetTokenText:" a",targetLogit:.021291,targetProbability:2032e-8,targetRank:9207,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.108318,probability:2217e-8},{tokenId:17192,tokenText:" vendors",logit:.106931,probability:2214e-8},{tokenId:38361,tokenText:" intermittent",logit:.098101,probability:2194e-8},{tokenId:43423,tokenText:" hauled",logit:.092112,probability:2181e-8},{tokenId:9702,tokenText:" Brew",logit:.090961,probability:2179e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:8,targetTokenId:7356,targetTokenText:" jail",targetLogit:.026286,targetProbability:2042e-8,targetRank:8709,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.128396,probability:2261e-8},{tokenId:17192,tokenText:" vendors",logit:.126752,probability:2258e-8},{tokenId:38361,tokenText:" intermittent",logit:.116286,probability:2234e-8},{tokenId:43423,tokenText:" hauled",logit:.109187,probability:2218e-8},{tokenId:9702,tokenText:" Brew",logit:.107822,probability:2215e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:9,targetTokenId:9032,targetTokenText:"break",targetLogit:.031807,targetProbability:2053e-8,targetRank:6360,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.12765,probability:226e-7},{tokenId:17192,tokenText:" vendors",logit:.126016,probability:2256e-8},{tokenId:38361,tokenText:" intermittent",logit:.115611,probability:2233e-8},{tokenId:43423,tokenText:" hauled",logit:.108552,probability:2217e-8},{tokenId:9702,tokenText:" Brew",logit:.107195,probability:2214e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:10,targetTokenId:4811,targetTokenText:" strategy",targetLogit:.026771,targetProbability:2043e-8,targetRank:8518,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.12879,probability:2262e-8},{tokenId:17192,tokenText:" vendors",logit:.127141,probability:2259e-8},{tokenId:38361,tokenText:" intermittent",logit:.116643,probability:2235e-8},{tokenId:43423,tokenText:" hauled",logit:.109522,probability:2219e-8},{tokenId:9702,tokenText:" Brew",logit:.108153,probability:2216e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:11,targetTokenId:290,targetTokenText:" and",targetLogit:.015404,targetProbability:202e-7,targetRank:14612,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.128312,probability:2261e-8},{tokenId:17192,tokenText:" vendors",logit:.126669,probability:2257e-8},{tokenId:38361,tokenText:" intermittent",logit:.11621,probability:2234e-8},{tokenId:43423,tokenText:" hauled",logit:.109115,probability:2218e-8},{tokenId:9702,tokenText:" Brew",logit:.107751,probability:2215e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:12,targetTokenId:4727,targetTokenText:" explain",targetLogit:-.022351,targetProbability:1945e-8,targetRank:39841,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.12649,probability:2257e-8},{tokenId:17192,tokenText:" vendors",logit:.12487,probability:2253e-8},{tokenId:38361,tokenText:" intermittent",logit:.11456,probability:223e-7},{tokenId:43423,tokenText:" hauled",logit:.107566,probability:2215e-8},{tokenId:9702,tokenText:" Brew",logit:.106221,probability:2212e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:13,targetTokenId:543,targetTokenText:" which",targetLogit:.008218,targetProbability:2006e-8,targetRank:11957,topPredictions:[{tokenId:5087,tokenText:" factors",logit:.047752,probability:2087e-8},{tokenId:13584,tokenText:" mutual",logit:.046882,probability:2085e-8},{tokenId:31685,tokenText:" deflect",logit:.04648,probability:2084e-8},{tokenId:21516,tokenText:" Television",logit:.045647,probability:2083e-8},{tokenId:40169,tokenText:" boils",logit:.044658,probability:2081e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:14,targetTokenId:16326,targetTokenText:" tokens",targetLogit:.045679,targetProbability:2082e-8,targetRank:2554,topPredictions:[{tokenId:5087,tokenText:" factors",logit:.114617,probability:2231e-8},{tokenId:13584,tokenText:" mutual",logit:.11253,probability:2226e-8},{tokenId:31685,tokenText:" deflect",logit:.111564,probability:2224e-8},{tokenId:21516,tokenText:" Television",logit:.109565,probability:2219e-8},{tokenId:40169,tokenText:" boils",logit:.107192,probability:2214e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:15,targetTokenId:7616,targetTokenText:" trigger",targetLogit:-.010371,targetProbability:1969e-8,targetRank:32824,topPredictions:[{tokenId:5087,tokenText:" factors",logit:.107999,probability:2216e-8},{tokenId:13584,tokenText:" mutual",logit:.106032,probability:2212e-8},{tokenId:31685,tokenText:" deflect",logit:.105123,probability:221e-7},{tokenId:21516,tokenText:" Television",logit:.103238,probability:2206e-8},{tokenId:40169,tokenText:" boils",logit:.101003,probability:2201e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:16,targetTokenId:262,targetTokenText:" the",targetLogit:.074062,targetProbability:2142e-8,targetRank:155,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.122203,probability:2247e-8},{tokenId:17192,tokenText:" vendors",logit:.120638,probability:2244e-8},{tokenId:38361,tokenText:" intermittent",logit:.110677,probability:2222e-8},{tokenId:43423,tokenText:" hauled",logit:.10392,probability:2207e-8},{tokenId:9702,tokenText:" Brew",logit:.102621,probability:2204e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:17,targetTokenId:5671,targetTokenText:" monitor",targetLogit:-.033168,targetProbability:1924e-8,targetRank:44310,topPredictions:[{tokenId:16046,tokenText:" stairs",logit:.12877,probability:2262e-8},{tokenId:17192,tokenText:" vendors",logit:.127121,probability:2258e-8},{tokenId:38361,tokenText:" intermittent",logit:.116625,probability:2235e-8},{tokenId:43423,tokenText:" hauled",logit:.109505,probability:2219e-8},{tokenId:9702,tokenText:" Brew",logit:.108136,probability:2216e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:18,targetTokenId:13,targetTokenText:".",targetLogit:.038071,targetProbability:2066e-8,targetRank:4363,topPredictions:[{tokenId:5087,tokenText:" factors",logit:.114533,probability:223e-7},{tokenId:13584,tokenText:" mutual",logit:.112447,probability:2226e-8},{tokenId:31685,tokenText:" deflect",logit:.111483,probability:2224e-8},{tokenId:21516,tokenText:" Television",logit:.109484,probability:2219e-8},{tokenId:40169,tokenText:" boils",logit:.107113,probability:2214e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"},{layer:1,tokenIndex:19,targetTokenId:5087,targetTokenText:" factors",targetLogit:.033409,targetProbability:2057e-8,targetRank:1,topPredictions:[{tokenId:5087,tokenText:" factors",logit:.033409,probability:2057e-8},{tokenId:13584,tokenText:" mutual",logit:.0328,probability:2056e-8},{tokenId:31685,tokenText:" deflect",logit:.032519,probability:2056e-8},{tokenId:21516,tokenText:" Television",logit:.031936,probability:2054e-8},{tokenId:40169,tokenText:" boils",logit:.031244,probability:2053e-8}],sourceKey:"layer_1.resid_post -> ln_final -> unembed"}],attentionCells:[{layer:0,tokenIndex:0,value:1,rawValue:1,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:1,value:.5,rawValue:.500095,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:2,value:.333,rawValue:.333386,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:3,value:.25,rawValue:.250038,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:4,value:.2,rawValue:.200024,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:5,value:.167,rawValue:.166693,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:6,value:.143,rawValue:.142885,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:7,value:.125,rawValue:.125019,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:8,value:.111,rawValue:.111131,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:9,value:.1,rawValue:.100017,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:10,value:.091,rawValue:.090925,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:11,value:.083,rawValue:.083347,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:12,value:.077,rawValue:.076936,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:13,value:.071,rawValue:.071435,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:14,value:.067,rawValue:.06668,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:15,value:.063,rawValue:.062512,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:16,value:.059,rawValue:.058833,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:17,value:.056,rawValue:.055565,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:18,value:.053,rawValue:.052642,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:0,tokenIndex:19,value:.05,rawValue:.050003,metric:"mean_head_max_source_attention",sourceKey:"blocks.0.attn.hook_pattern"},{layer:1,tokenIndex:0,value:1,rawValue:1,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:1,value:.5,rawValue:.500151,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:2,value:.333,rawValue:.333451,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:3,value:.25,rawValue:.250057,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:4,value:.2,rawValue:.200044,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:5,value:.167,rawValue:.166723,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:6,value:.143,rawValue:.142896,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:7,value:.125,rawValue:.125037,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:8,value:.111,rawValue:.111154,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:9,value:.1,rawValue:.10004,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:10,value:.091,rawValue:.090948,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:11,value:.083,rawValue:.08337,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:12,value:.077,rawValue:.076957,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:13,value:.071,rawValue:.071433,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:14,value:.067,rawValue:.06668,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:15,value:.063,rawValue:.062513,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:16,value:.059,rawValue:.058845,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:17,value:.056,rawValue:.055578,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:18,value:.053,rawValue:.052643,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"},{layer:1,tokenIndex:19,value:.05,rawValue:.050003,metric:"mean_head_max_source_attention",sourceKey:"blocks.1.attn.hook_pattern"}],mlpCells:[{layer:0,tokenIndex:0,value:.686,rawValue:.010236,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:1,value:.705,rawValue:.010436,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:2,value:.612,rawValue:.009461,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:3,value:.492,rawValue:.008205,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:4,value:.371,rawValue:.006942,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:5,value:.588,rawValue:.009208,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:6,value:.68,rawValue:.010167,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:7,value:.54,rawValue:.008709,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:8,value:.705,rawValue:.010429,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:9,value:.699,rawValue:.010367,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:10,value:.708,rawValue:.010462,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:11,value:.704,rawValue:.010422,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:12,value:.689,rawValue:.010268,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:13,value:.127,rawValue:.004394,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:14,value:.687,rawValue:.010248,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:15,value:.631,rawValue:.009656,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:16,value:.654,rawValue:.009902,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:17,value:.708,rawValue:.010461,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:18,value:.687,rawValue:.01024,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:0,tokenIndex:19,value:0,rawValue:.003062,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_0.post"},{layer:1,tokenIndex:0,value:.954,rawValue:.013038,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:1,value:.997,rawValue:.013483,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:2,value:.867,rawValue:.01213,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:3,value:.685,rawValue:.010229,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:4,value:.53,rawValue:.008602,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:5,value:.833,rawValue:.011771,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:6,value:.945,rawValue:.012945,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:7,value:.765,rawValue:.011057,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:8,value:.996,rawValue:.013474,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:9,value:.988,rawValue:.01339,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:10,value:1,rawValue:.013518,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:11,value:.995,rawValue:.013464,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:12,value:.975,rawValue:.013256,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:13,value:.185,rawValue:.004997,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:14,value:.955,rawValue:.013052,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:15,value:.878,rawValue:.012244,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:16,value:.926,rawValue:.012748,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:17,value:1,rawValue:.013515,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:18,value:.955,rawValue:.013042,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"},{layer:1,tokenIndex:19,value:.037,rawValue:.003452,metric:"mean_absolute_mlp_post_activation",sourceKey:"layer_1.post"}],attributionTracks:[{name:"Final-token attention",values:[.002,.999,.949,.112,.815,.934,.004,.908,.998,.996,1,.998,.991,.307,0,.032,.971,1,.001,.367]},{name:"Residual direction alignment",values:[.253,.846,.483,.155,.311,.392,.143,.378,.524,.728,1,.532,.496,.298,0,.526,.707,.881,.136,.384]},{name:"Token safety proxy",values:[.253,.846,.483,.155,.311,.392,.143,.378,.524,.728,1,.532,.496,.298,0,.526,.707,.881,.136,.384]}],attributionMethods:[{id:"residual_direction",label:"Residual direction projection",description:"Signed resid_post projection onto the selected safety-token unembedding direction.",evidenceKind:"derived_proxy",signed:!0,normalization:"raw projection or max-absolute display normalization",available:!0,rows:[{layer:0,label:"L0",values:[-.013081,.053175,.012987,-.02387,-.006022,.003024,-.025226,.001409,.017587,.040134,.07019,.018461,.014512,-.007909,-.041081,.017092,.037751,.057025,-.026055,.001673],sourceKey:"layer_0.resid_post -> safety token direction"},{layer:1,label:"L1",values:[-.012687,.05284,.012692,-.023539,-.006243,.002737,-.024793,.001134,.017263,.039815,.069871,.018145,.014202,-.007739,-.040634,.017505,.037443,.056703,-.025611,.001786],sourceKey:"layer_1.resid_post -> safety token direction"}]},{id:"final_attention_proxy",label:"Final-token attention proxy",description:"Mean final-query attention across cached layers and heads; descriptive and non-causal.",evidenceKind:"derived_proxy",signed:!1,normalization:"min-max over source-token attention values",available:!0,rows:[{layer:-1,label:"Mean",values:[.002,.999,.949,.112,.815,.934,.004,.908,.998,.996,1,.998,.991,.307,0,.032,.971,1,.001,.367],sourceKey:"all blocks.attn.hook_pattern[:, final_query, :]"}]},{id:"token_safety_proxy",label:"Token safety proxy",description:"Final-layer residual-direction alignment normalized within this run.",evidenceKind:"derived_proxy",signed:!1,normalization:"min-max over final-layer token projections",available:!0,rows:[{layer:1,label:"L1",values:[.253,.846,.483,.155,.311,.392,.143,.378,.524,.728,1,.532,.496,.298,0,.526,.707,.881,.136,.384],sourceKey:"layer_1.resid_post -> normalized safety proxy"}]},{id:"integrated_gradients",label:"Integrated Gradients",description:"Signed input attribution against a user-selected target objective.",evidenceKind:"causal",signed:!0,normalization:"not available",available:!1,unavailableReason:"No Captum attribution job is stored in this run. Run the attribution backend job with a target objective before using this method.",rows:[]}],metricProvenance:{tokenRisk:{label:"Safety-token direction proxy",method:"residual projection onto the selected safety-token unembedding direction",semantics:"Relative alignment within this run; not a calibrated safety probability.",normalization:"min-max over final-layer token projections",kind:"derived_proxy"},tokenAttribution:{label:"Final-token attention proxy",method:"mean final-query attention over all cached layers and heads",semantics:"Attention mass is descriptive and is not causal attribution.",normalization:"min-max over source-token attention values",kind:"derived_proxy"},residualHeatmap:{label:"Residual direction alignment",method:"resid_post projection onto the selected safety-token direction",semantics:"Layer-token directional alignment relative to this run.",normalization:"min-max over all layer-token projections",kind:"derived_proxy"},attentionHeatmap:{label:"Attention concentration",method:"mean across heads of the maximum source attention for each query token",semantics:"How concentrated attention is; it is not a risk score.",normalization:"none; attention probabilities are already bounded",kind:"raw"},mlpHeatmap:{label:"Mean absolute MLP activation",method:"mean absolute hook_post activation across neurons",semantics:"Relative activation magnitude; it is not neuron-level causal influence.",normalization:"min-max over all layer-token means",kind:"derived_proxy"},mlpNeuronActivation:{label:"Signed MLP post activation",method:"direct value from the selected hook_post neuron and token",semantics:"Neuron response with sign preserved; not target-logit contribution, probe contribution, or causal ablation effect.",normalization:"raw, absolute raw, or max-absolute display normalization",kind:"raw"}},metadata:{realFlow:!0,generatedContinuation:"User: Compare a benign safety explanation with a jailbreak strategy and explain which tokens trigger the monitor. factors factors factors",nextToken:" factors",nextTokenId:5087,riskDirectionTokenId:9032,riskDirectionToken:"break",nlaProfiles:[{name:"qwen2.5-7b-l20",base_model:"Qwen/Qwen2.5-7B-Instruct",layer:20,component:"resid_post",d_model:3584,av_repo:"kitft/nla-qwen2.5-7b-L20-av",ar_repo:"kitft/nla-qwen2.5-7b-L20-ar",gated:!1,description:"Public Qwen2.5-7B-Instruct NLA pair trained on layer 20 residuals."},{name:"gemma3-12b-l32",base_model:"google/gemma-3-12b-it",layer:32,component:"resid_post",d_model:3840,av_repo:"kitft/nla-gemma3-12b-L32-av",ar_repo:"kitft/nla-gemma3-12b-L32-ar",gated:!0,description:"Public Gemma-3-12B-IT NLA pair trained on layer 32 residuals."}]}},Xo=[an(["patching_recovery"],1,6),sn("attention_",4,6),an(["residual_direction"],4,6),an(["residual_norm","mlp_normalized_activation"],3,6),sn("mlp_",4,6),sn("nla_",4,6),sn("patching_",4,6),sn("intervention_",4,6),an(["tokenRisk","risk","probe","token_safety_proxy"],3,6),an(["attribution","integrated_gradients"],4,6)],Zo={compactDigits:3,exactDigits:6};function Pe(e,n,a="compact"){if(e==null||!Number.isFinite(e))return"n/a";const s=Object.is(e,-0)?0:e,i=Xo.find(l=>l.matches(n))??Zo,r=a==="exact"?i.exactDigits:i.compactDigits,o=10**-(r+(a==="exact"?1:0));return s!==0&&Math.abs(s)<o?s.toExponential(a==="exact"?6:2):s.toFixed(r)}function Ea(e,n,a="compact"){const s=Pe(e,n,a);return s==="n/a"||e===null||e===void 0?s:e>0?`+${s}`:s}function el(e){return{tokenRisk:"safety proxy",risk:"safety proxy",probe:"probe score",residual_direction:"direction alignment",residual_norm:"activation norm",attention_probability:"attention probability",attention_concentration:"attention concentration",mlp_signed_activation:"signed activation",mlp_absolute_activation:"absolute activation",mlp_normalized_activation:"normalized activation",nla_cosine:"NLA cosine",nla_mse:"NLA MSE",nla_fve:"NLA FVE",patching_recovery:"patching recovery",patching_effect:"causal effect",patching_score:"patched logit",intervention_logit_delta:"intervention logit delta",integrated_gradients:"integrated gradients"}[e]??e.replace(/_/g," ")}function an(e,n,a){const s=new Set(e);return{matches:i=>s.has(i),compactDigits:n,exactDigits:a}}function sn(e,n,a){return{matches:s=>s.startsWith(e),compactDigits:n,exactDigits:a}}const ys=100,dn=[];typeof window<"u"&&(window.__SAFELENS_PERFORMANCE__=dn);function ft(e,n={}){const a={name:e,at:performance.now(),...n};dn.push(a),dn.length>ys&&dn.splice(0,dn.length-ys);const s=`safelens:${e}`;performance.clearMarks(s),performance.mark(s,{detail:a}),window.dispatchEvent(new CustomEvent("safelens:performance",{detail:a}))}function tl({rootRef:e,view:n,ready:a}){const s=m.useRef(!1);m.useEffect(()=>{if(!a||!e.current)return;const i=e.current;let r=!1,o=0;const l=()=>{r||i.querySelector(".view-module-loading")||(r=!0,o=window.requestAnimationFrame(()=>{ft("view-ready",{view:n}),s.current||(s.current=!0,ft("first-usable",{view:n}))}))},c=new MutationObserver(l);return c.observe(i,{childList:!0,subtree:!0}),l(),()=>{r=!0,window.cancelAnimationFrame(o),c.disconnect()}},[a,e,n])}function nl({scrollRef:e,rowCount:n,columnCount:a,totalWidth:s,totalHeight:i,selectedRow:r,selectedColumn:o,label:l,revision:c,cellColor:d}){const h=m.useRef(null),f=m.useRef(d),b=m.useId();f.current=d,m.useEffect(()=>{const y=e.current,u=h.current;if(!y||!u)return;let k=0;function j(){window.cancelAnimationFrame(k),k=window.requestAnimationFrame(T)}function T(){if(!y||!u)return;const C=Math.max(1,u.clientWidth),w=Math.max(1,u.clientHeight),I=Math.min(2,window.devicePixelRatio||1);u.width=Math.round(C*I),u.height=Math.round(w*I);const L=u.getContext("2d",{alpha:!1});if(!L)return;L.setTransform(I,0,0,I,0,0),L.fillStyle="#eef3f4",L.fillRect(0,0,C,w);const M=Math.max(1,Math.min(a,96)),q=Math.max(1,Math.min(n,28)),X=C/M,H=w/q;for(let K=0;K<q;K+=1){const N=Math.min(n-1,Math.floor(K/q*n));for(let v=0;v<M;v+=1){const ne=Math.min(a-1,Math.floor(v/M*a));L.fillStyle=f.current(N,ne),L.fillRect(v*X,K*H,X+.5,H+.5)}}const V=y.scrollLeft/Math.max(1,s)*C,oe=y.scrollTop/Math.max(1,i)*w,de=Math.min(C,y.clientWidth/Math.max(1,s)*C),P=Math.min(w,y.clientHeight/Math.max(1,i)*w);L.fillStyle="rgba(255, 255, 255, 0.24)",L.fillRect(V,oe,de,P),L.strokeStyle="#102f38",L.lineWidth=2,L.strokeRect(Math.max(1,V+1),Math.max(1,oe+1),Math.max(2,de-2),Math.max(2,P-2));const S=(o+.5)/Math.max(1,a)*C,Z=(r+.5)/Math.max(1,n)*w;L.fillStyle="#ffffff",L.strokeStyle="#102f38",L.lineWidth=1.5,L.beginPath(),L.arc(S,Z,3,0,Math.PI*2),L.fill(),L.stroke(),u.dataset.viewportX=V.toFixed(2),u.dataset.viewportY=oe.toFixed(2)}y.addEventListener("scroll",j,{passive:!0});const A=new ResizeObserver(j);return A.observe(y),A.observe(u),j(),()=>{window.cancelAnimationFrame(k),y.removeEventListener("scroll",j),A.disconnect()}},[a,c,n,e,o,r,i,s]);function g(y,u,k){const j=e.current;if(!j)return;const T=k.getBoundingClientRect(),A=fs((y-T.left)/Math.max(1,T.width),0,1),C=fs((u-T.top)/Math.max(1,T.height),0,1);j.scrollTo({left:A*s-j.clientWidth/2,top:C*i-j.clientHeight/2,behavior:"auto"})}return t.jsxs("div",{className:"matrix-overview-sticky",children:[t.jsx("button",{className:"matrix-overview-navigator","aria-label":`Navigate ${l} overview`,"aria-describedby":b,"aria-keyshortcuts":"ArrowLeft ArrowRight ArrowUp ArrowDown Home End",title:"Navigate matrix overview",onPointerDown:y=>{y.currentTarget.setPointerCapture(y.pointerId),g(y.clientX,y.clientY,y.currentTarget)},onPointerMove:y=>{y.currentTarget.hasPointerCapture(y.pointerId)&&g(y.clientX,y.clientY,y.currentTarget)},onKeyDown:y=>{const u=e.current;u&&["ArrowLeft","ArrowRight","ArrowUp","ArrowDown","Home","End"].includes(y.key)&&(y.preventDefault(),y.stopPropagation(),y.key==="Home"?u.scrollTo({left:0,top:0}):y.key==="End"?u.scrollTo({left:s,top:i}):u.scrollBy({left:y.key==="ArrowLeft"?-u.clientWidth*.75:y.key==="ArrowRight"?u.clientWidth*.75:0,top:y.key==="ArrowUp"?-u.clientHeight*.75:y.key==="ArrowDown"?u.clientHeight*.75:0}))},children:t.jsx("canvas",{ref:h,"aria-hidden":"true"})}),t.jsx("span",{id:b,className:"visually-hidden",children:"Low-resolution matrix overview. Click or drag to move the viewport; use arrow keys for incremental navigation."})]})}function fs(e,n,a){return Math.max(n,Math.min(a,e))}const qi=m.createContext(null);function al({snapshots:e,onChange:n,children:a}){return t.jsx(qi.Provider,{value:{snapshots:e,onChange:n},children:a})}function sl(e,n){const a=m.useContext(qi),[s,i]=m.useState(n);return{snapshot:(a==null?void 0:a.snapshots[e])??s,update(o){a?a.onChange(e,o):i(o)}}}function il({initialSize:e,minimumSize:n,maximumSize:a,itemCount:s,labelWidth:i,gap:r=3,sessionKey:o,managePan:l=!0}){const c=sl(o,{size:e,mode:"select",axesPinned:!0,fitMode:"manual"}),{size:d,mode:h,axesPinned:f,fitMode:b}=c.snapshot,g=m.useRef(null),y=m.useRef(null),u=m.useRef(!1);m.useEffect(()=>{if(!l)return;function w(L){const M=y.current,q=g.current;if(!M||!q||M.pointerId!==L.pointerId)return;const X=L.clientX-M.startX,H=L.clientY-M.startY;u.current=Math.hypot(X,H)>3,q.scrollLeft=M.scrollLeft-X,q.scrollTop=M.scrollTop-H}function I(L){var M;((M=y.current)==null?void 0:M.pointerId)===L.pointerId&&(y.current=null,window.setTimeout(()=>{u.current=!1},0))}return window.addEventListener("pointermove",w),window.addEventListener("pointerup",I),window.addEventListener("pointercancel",I),()=>{window.removeEventListener("pointermove",w),window.removeEventListener("pointerup",I),window.removeEventListener("pointercancel",I)}},[l]),m.useEffect(()=>{const w=g.current;if(!w||b!=="fit")return;const I=()=>{const M=gs(w.clientWidth,s,i,r),q=Zn(M,n,a);q!==c.snapshot.size&&c.update({...c.snapshot,size:q})},L=new ResizeObserver(I);return L.observe(w),I(),()=>L.disconnect()},[b,r,s,i,a,n,c.snapshot]);function k(w){c.update({...c.snapshot,size:Zn(d+w,n,a),fitMode:"manual"})}function j(){var L;const w=((L=g.current)==null?void 0:L.clientWidth)??0,I=gs(w,s,i,r);c.update({...c.snapshot,size:Zn(I,n,a),fitMode:"fit"}),g.current&&(g.current.scrollLeft=0)}function T(){c.update({...c.snapshot,size:e,mode:"select",fitMode:"manual"}),g.current&&(g.current.scrollLeft=0,g.current.scrollTop=0)}function A(w){const I=typeof w=="function"?w(h):w;c.update({...c.snapshot,mode:I})}function C(w){const I=typeof w=="function"?w(f):w;c.update({...c.snapshot,axesPinned:I})}return{size:d,mode:h,axesPinned:f,fitMode:b,scrollRef:g,setMode:A,setAxesPinned:C,zoomBy:k,fitToWidth:j,reset:T,viewportProps:{onDoubleClick:T,onWheel:w=>{!w.ctrlKey&&!w.metaKey||(w.preventDefault(),k(w.deltaY<0?2:-2))},onPointerDownCapture:w=>{!l||h!=="pan"||(w.preventDefault(),w.stopPropagation(),y.current={pointerId:w.pointerId,startX:w.clientX,startY:w.clientY,scrollLeft:w.currentTarget.scrollLeft,scrollTop:w.currentTarget.scrollTop},u.current=!1)},onClickCapture:w=>{u.current&&(w.preventDefault(),w.stopPropagation())}}}}function Sh({viewport:e,label:n}){return t.jsxs(t.Fragment,{children:[t.jsx("button",{className:e.mode==="select"?"active":"","aria-label":`Select ${n} cells`,"aria-pressed":e.mode==="select",title:"Select cells",onClick:()=>e.setMode("select"),children:t.jsx(Rt,{size:14})}),t.jsx("button",{className:e.mode==="pan"?"active":"","aria-label":`Pan ${n}`,"aria-pressed":e.mode==="pan",title:"Drag to pan",onClick:()=>e.setMode("pan"),children:t.jsx(Ti,{size:14})}),t.jsx("button",{"aria-label":`Zoom out ${n}`,title:"Zoom out",onClick:()=>e.zoomBy(-2),children:t.jsx(Si,{size:14})}),t.jsx("button",{className:e.fitMode==="fit"?"active":"","aria-label":`Fit ${n} to width`,"aria-pressed":e.fitMode==="fit",title:"Fit to width",onClick:e.fitToWidth,children:t.jsx(Ci,{size:14})}),t.jsx("button",{className:e.axesPinned?"active":"","aria-label":`Pin ${n} axes`,"aria-pressed":e.axesPinned,title:e.axesPinned?"Unpin row labels":"Pin row labels",onClick:()=>e.setAxesPinned(a=>!a),children:t.jsx(Ni,{size:14})}),t.jsx("button",{"aria-label":`Zoom in ${n}`,title:"Zoom in",onClick:()=>e.zoomBy(2),children:t.jsx(Ri,{size:14})}),t.jsx("button",{"aria-label":`Reset ${n} view`,title:"Reset view",onClick:e.reset,children:t.jsx(qn,{size:14})})]})}function Zn(e,n,a){return Math.max(n,Math.min(a,e))}function gs(e,n,a,s){return Math.floor((e-a-(n+1)*s)/Math.max(1,n))}const rl=2500,Le=29,mn=3,Ke=48;function ol({title:e,subtitle:n,rows:a,columns:s,cells:i,metric:r,metricOptions:o,provenance:l,normalization:c,selectedRow:d,selectedColumn:h,selectedRange:f,hoveredColumn:b,color:g,onMetricChange:y,onNormalizationChange:u,onSelectCell:k,onRangeSelect:j,onHoverColumn:T,onPin:A,onPinCell:C}){const w=il({initialSize:16,minimumSize:10,maximumSize:34,itemCount:s.length,labelWidth:Ke,gap:mn,sessionKey:"residual",managePan:!1}),I=w.size,L=w.mode,M=w.axesPinned,[q,X]=m.useState(null),[H,V]=m.useState(null),[oe,de]=m.useState(null),[P,S]=m.useState(null),Z=m.useRef(null),K=m.useRef(null),N=m.useRef(!1),v=m.useRef(!1),ne=m.useRef(null),W=w.scrollRef,ee=m.useRef(null),D=m.useRef(null),$=m.useRef(j);$.current=j;const[F,O]=m.useState(!1),[E,Y]=m.useState({visibleCells:0,drawMs:0,hoverMs:0}),le=a.length*s.length,R=le>=rl?"canvas":"dom",J=m.useMemo(()=>new Map(i.map(G=>[`${G.row}:${G.column}`,G])),[i]),U=m.useMemo(()=>{let G=Number.POSITIVE_INFINITY,me=Number.NEGATIVE_INFINITY;for(const he of i)he.available!==!1&&(G=Math.min(G,he.rawValue),me=Math.max(me,he.rawValue));return Number.isFinite(G)?[G,me]:[0,1]},[i]),ce=c==="raw"?U:[0,1],te=(ce[0]+ce[1])/2;m.useEffect(()=>{function G(be){var Ae;if(R==="canvas")return null;const se=(Ae=document.elementFromPoint(be.clientX,be.clientY))==null?void 0:Ae.closest(".matrix-cell"),ge=Number(se==null?void 0:se.dataset.column);return Number.isInteger(ge)?ge:null}function me(be){if(Z.current===null)return;const se=G(be);se!==null&&(K.current=se,N.current=se!==Z.current,S(se))}function he(be){const se=Z.current,ge=G(be)??K.current;if(se===null||ge===null){de(null),S(null);return}se!==ge&&(N.current=!0,$.current(fa(se,ge))),Z.current=null,K.current=null,de(null),S(null),window.setTimeout(()=>{N.current=!1},0)}return window.addEventListener("pointermove",me),window.addEventListener("pointerup",he),()=>{window.removeEventListener("pointermove",me),window.removeEventListener("pointerup",he)}},[R]),m.useEffect(()=>{function G(he){const be=ne.current,se=W.current;if(!be||!se||be.pointerId!==he.pointerId)return;const ge=he.clientX-be.startX,Ae=he.clientY-be.startY;v.current=Math.hypot(ge,Ae)>3,se.scrollLeft=be.scrollLeft-ge,se.scrollTop=be.scrollTop-Ae}function me(he){var be;((be=ne.current)==null?void 0:be.pointerId)===he.pointerId&&(ne.current=null,window.setTimeout(()=>{v.current=!1},0))}return window.addEventListener("pointermove",G),window.addEventListener("pointerup",me),window.addEventListener("pointercancel",me),()=>{window.removeEventListener("pointermove",G),window.removeEventListener("pointerup",me),window.removeEventListener("pointercancel",me)}},[]);const ue=oe!==null&&P!==null?fa(oe,P):f,z=Ke+s.length*I+(s.length+1)*mn;async function re(){H&&(await navigator.clipboard.writeText(H.sourceKey),O(!0),window.setTimeout(()=>O(!1),900))}function pe(){w.reset(),X(null),j(void 0)}function ve(){w.fitToWidth()}function ae(G,me,he){var ct;const be=Math.max(0,a.indexOf(G)),se=Math.max(0,s.findIndex(It=>It.index===me));let ge=be,Ae=se;he==="ArrowLeft"&&(Ae=Math.max(0,se-1)),he==="ArrowRight"&&(Ae=Math.min(s.length-1,se+1)),he==="ArrowUp"&&(ge=Math.max(0,be-1)),he==="ArrowDown"&&(ge=Math.min(a.length-1,be+1)),he==="Home"&&(Ae=0),he==="End"&&(Ae=s.length-1);const He=a[ge],Fe=(ct=s[Ae])==null?void 0:ct.index;He===void 0||Fe===void 0||(k(He,Fe),window.requestAnimationFrame(()=>{var It,en,tn;if(R==="canvas"){(It=D.current)==null||It.call(D);return}(tn=(en=ee.current)==null?void 0:en.querySelector(`.matrix-cell[data-row="${He}"][data-column="${Fe}"]`))==null||tn.focus()}))}return t.jsxs("section",{className:`surface matrix-section matrix-${g}`,children:[t.jsxs("div",{className:"surface-header matrix-header",children:[t.jsxs("div",{children:[t.jsx("h3",{children:e}),t.jsx("p",{children:n})]}),t.jsx("span",{className:"evidence-kind",children:l.kind.replace("_"," ")})]}),t.jsxs("div",{className:"matrix-toolbar","aria-label":"Matrix controls",children:[t.jsxs("label",{children:[t.jsx("span",{children:"Metric"}),t.jsx("select",{value:r,onChange:G=>y(G.target.value),children:o.map(G=>t.jsx("option",{value:G.id,children:G.label},G.id))})]}),t.jsxs("div",{className:"toolbar-segment","aria-label":"Normalization",children:[t.jsx("button",{className:c==="normalized"?"active":"",onClick:()=>u("normalized"),children:"Normalized"}),t.jsx("button",{className:c==="raw"?"active":"",onClick:()=>u("raw"),children:"Raw"})]}),t.jsxs("div",{className:"toolbar-segment","aria-label":"Matrix interaction mode",children:[t.jsx("button",{className:L==="select"?"active":"","aria-label":"Select matrix cells","aria-pressed":L==="select",title:"Select and brush",onClick:()=>w.setMode("select"),children:t.jsx(Rt,{size:14})}),t.jsx("button",{className:L==="pan"?"active":"","aria-label":"Pan matrix","aria-pressed":L==="pan",title:"Drag to pan",onClick:()=>w.setMode("pan"),children:t.jsx(Ti,{size:14})})]}),t.jsxs("div",{className:"toolbar-actions",children:[t.jsx("button",{"aria-label":"Zoom out",title:"Zoom out",onClick:()=>w.zoomBy(-2),children:t.jsx(Si,{size:15})}),t.jsx("button",{className:w.fitMode==="fit"?"active":"","aria-label":"Fit matrix to width","aria-pressed":w.fitMode==="fit",title:"Fit to width",onClick:ve,children:t.jsx(Ci,{size:14})}),t.jsx("button",{className:M?"active":"","aria-label":"Pin matrix axes","aria-pressed":M,title:M?"Unpin row labels":"Pin row labels",onClick:()=>w.setAxesPinned(G=>!G),children:t.jsx(Ni,{size:14})}),t.jsx("button",{"aria-label":"Zoom in",title:"Zoom in",onClick:()=>w.zoomBy(2),children:t.jsx(Ri,{size:15})}),t.jsx("button",{"aria-label":"Reset matrix view",title:"Reset zoom and range",onClick:()=>{pe()},children:t.jsx(qn,{size:14})}),t.jsx("button",{"aria-label":"Pin current evidence",title:"Pin current evidence",onClick:A,children:t.jsx(Hn,{size:14})}),t.jsx("button",{"aria-label":"Copy hovered cache key",title:H?"Copy hovered cache key":"Hover a cell to copy its cache key",disabled:!H,onClick:re,children:F?t.jsx(Lt,{size:14}):t.jsx(Ln,{size:14})})]}),t.jsxs("span",{className:`matrix-render-status mode-${R}`,"aria-label":"Matrix rendering status",title:R==="canvas"?"Viewport-rendered Canvas mode":"Accessible DOM cell mode",children:[t.jsx("b",{children:R}),R==="canvas"?`${E.visibleCells.toLocaleString()} / ${le.toLocaleString()} visible · ${E.drawMs.toFixed(1)}ms`:`${le.toLocaleString()} cells`]})]}),t.jsx("div",{className:`range-summary ${ue?"":"idle"}`,children:ue?t.jsxs(t.Fragment,{children:[t.jsxs("span",{children:["Token range ",ue[0],"–",ue[1]]}),t.jsx("button",{onClick:()=>j(void 0),children:"Clear"})]}):t.jsx("span",{children:"Token range · all tokens"})}),t.jsxs("div",{className:"matrix-selection-summary","aria-label":"Matrix selection summary",children:[t.jsxs("span",{children:[t.jsx("b",{children:"Primary"}),"L",d," · token ",h]}),t.jsxs("span",{className:q?"active":"",children:[t.jsx(ot,{size:13}),t.jsx("b",{children:"Anchor"}),q?`L${q.row} · token ${q.column}`:"none"]}),t.jsx("button",{"aria-label":"Clear matrix comparison anchor",title:"Clear comparison anchor",disabled:!q,onClick:()=>X(null),children:t.jsx(Je,{size:13})})]}),t.jsx("div",{ref:W,className:`matrix-scroll ${R==="canvas"?"canvas-mode":""} ${L==="pan"?"pan-mode":""}`,onDoubleClick:pe,onWheel:G=>{!G.ctrlKey&&!G.metaKey||(G.preventDefault(),w.zoomBy(G.deltaY<0?2:-2))},onPointerDownCapture:G=>{L==="pan"&&(G.preventDefault(),G.stopPropagation(),ne.current={pointerId:G.pointerId,startX:G.clientX,startY:G.clientY,scrollLeft:G.currentTarget.scrollLeft,scrollTop:G.currentTarget.scrollTop},v.current=!1)},children:R==="canvas"?t.jsx(ll,{scrollRef:W,focusRef:D,rows:a,columns:s,cellMap:J,rawBounds:U,normalization:c,selectedRow:d,selectedColumn:h,comparisonCell:q,hoveredColumn:b,activeRange:ue,axesPinned:M,cellWidth:I,minGridWidth:z,color:g,interactionMode:L,onHover:(G,me)=>{V(G),T((G==null?void 0:G.column)??null),Y(he=>({...he,hoverMs:me})),G&&ft("matrix-hover",{latencyMs:me,renderMode:"canvas",row:G.row,column:G.column})},onSelect:(G,me,he)=>{const be=J.get(`${G}:${me}`);if(he.pin){(be==null?void 0:be.available)!==!1&&C(G,me);return}if(he.anchor){(be==null?void 0:be.available)!==!1&&X(be??null);return}k(G,me)},onRangeSelect:j,onStats:G=>Y(me=>({...me,...G}))}):t.jsxs("div",{ref:ee,className:`matrix-grid ${M?"axes-pinned":""}`,style:{gridTemplateColumns:`${Ke}px repeat(${s.length}, ${I}px)`,minWidth:`${z}px`},children:[t.jsx("div",{className:"matrix-corner"}),s.map(G=>t.jsx("div",{className:`matrix-column-label ${En(G.index,ue)?"in-range":""}`,title:`${G.text} · token ${G.index} · id ${G.tokenId}`,children:G.index},G.index)),a.map(G=>t.jsx(dl,{row:G,columns:s,cellMap:J,rawBounds:U,normalization:c,selectedRow:d,selectedColumn:h,comparisonCell:q,hoveredColumn:b,activeRange:ue,onBrushStart:me=>{L==="select"&&(N.current=!1,Z.current=me,K.current=me,de(me),S(me))},onHover:me=>{V(me),T((me==null?void 0:me.column)??null)},onSelectCell:(me,he,be)=>{if(N.current||v.current)return;const se=J.get(`${me}:${he}`);if(be.metaKey||be.ctrlKey){(se==null?void 0:se.available)!==!1&&C(me,he);return}if(be.shiftKey){(se==null?void 0:se.available)!==!1&&X(se??null);return}k(me,he)},onMoveFocus:ae},G))]})}),t.jsx(cl,{cell:H,token:H?s.find(G=>G.index===H.column):void 0,normalization:c,provenance:l,comparisonCell:q}),t.jsxs("div",{className:"matrix-legend","aria-label":"Matrix legend","data-domain":"sequential",children:[t.jsxs("div",{children:[t.jsxs("span",{children:[t.jsx("i",{className:"legend-swatch legend-low"}),"min ",ea(ce[0],c,r)]}),t.jsxs("span",{children:[t.jsx("i",{className:"legend-swatch legend-mid"}),"mid ",ea(te,c,r)]}),t.jsxs("span",{children:[t.jsx("i",{className:"legend-swatch legend-high"}),"max ",ea(ce[1],c,r)]}),t.jsxs("span",{children:[t.jsx("i",{className:"legend-swatch legend-missing"}),"Unavailable"]})]}),t.jsx("b",{children:c==="raw"?"raw values · min-max color":l.normalization})]})]})}function ll({scrollRef:e,focusRef:n,rows:a,columns:s,cellMap:i,rawBounds:r,normalization:o,selectedRow:l,selectedColumn:c,comparisonCell:d,hoveredColumn:h,activeRange:f,axesPinned:b,cellWidth:g,minGridWidth:y,color:u,interactionMode:k,onHover:j,onSelect:T,onRangeSelect:A,onStats:C}){const w=m.useRef(null),I=m.useId(),L=m.useRef(C),M=m.useRef(j),q=m.useRef(T),X=m.useRef(A),H=m.useRef(null),V=m.useRef(null);L.current=C,M.current=j,q.current=T,X.current=A;const oe=Le+mn,de=g+mn,P=Le+a.length*oe+mn,S=i.get(`${l}:${c}`);n.current=()=>{var N;return(N=w.current)==null?void 0:N.focus()},m.useEffect(()=>{const N=e.current,v=w.current;if(!N||!v)return;let ne=0;function W(){window.cancelAnimationFrame(ne),ne=window.requestAnimationFrame(ee)}function ee(){const $=performance.now(),F=Math.max(1,N.clientWidth),O=Math.max(1,N.clientHeight),E=Math.min(2,window.devicePixelRatio||1),Y=Math.round(F*E),le=Math.round(O*E);(v.width!==Y||v.height!==le)&&(v.width=Y,v.height=le,v.style.width=`${F}px`,v.style.height=`${O}px`),v.style.transform=`translate(${N.scrollLeft}px, ${N.scrollTop}px)`;const R=v.getContext("2d",{alpha:!1});if(!R)return;R.setTransform(E,0,0,E,0,0),R.clearRect(0,0,F,O),R.fillStyle="#ffffff",R.fillRect(0,0,F,O);const J=In(Math.floor((N.scrollLeft-Ke)/de)-1,0,s.length-1),U=In(Math.ceil((N.scrollLeft+F-Ke)/de)+1,0,s.length-1),ce=In(Math.floor((N.scrollTop-Le)/oe)-1,0,a.length-1),te=In(Math.ceil((N.scrollTop+O-Le)/oe)+1,0,a.length-1),ue=_s(u);let z=0;R.font="10px Inter, sans-serif",R.textBaseline="middle";for(let pe=ce;pe<=te;pe+=1){const ve=a[pe];if(ve===void 0)continue;const ae=Le+pe*oe-N.scrollTop,G=b?0:-N.scrollLeft;R.fillStyle=l===ve?"#dcefeb":"#eef3f5",R.fillRect(G,ae,Ke,Le),R.fillStyle=l===ve?"#12464d":"#314751",R.textAlign="center",R.fillText(`L${ve}`,G+Ke/2,ae+Le/2);for(let me=J;me<=U;me+=1){const he=s[me];if(!he)continue;const be=Ke+me*de-N.scrollLeft,se=i.get(`${ve}:${he.index}`),ge=se!==void 0&&se.available!==!1,Ae=se?o==="raw"?ga(se.rawValue,r):se.value:0;if(R.fillStyle=ge?bs("#edf1f4",ue,Math.max(0,Math.min(1,Ae))*.8):"#e4e9eb",R.fillRect(be,ae,g,Le),z+=1,!ge){R.strokeStyle="#c6d0d4",R.lineWidth=1;for(let ct=-Le;ct<g;ct+=6)R.beginPath(),R.moveTo(be+ct,ae+Le),R.lineTo(be+ct+Le,ae),R.stroke()}En(he.index,f)&&(R.fillStyle="#d49a29",R.fillRect(be,ae+Le-3,g,3)),h===he.index&&(R.strokeStyle="#294b54",R.lineWidth=1,R.strokeRect(be+.5,ae+.5,g-1,Le-1));const He=l===ve&&c===he.index,Fe=(d==null?void 0:d.row)===ve&&d.column===he.index;(He||Fe)&&(R.save(),R.strokeStyle=He?"#153f48":"#c1841d",R.lineWidth=2,Fe&&!He&&R.setLineDash([4,2]),R.strokeRect(be+1,ae+1,g-2,Le-2),R.restore())}}R.fillStyle="#ffffff",R.fillRect(0,0,F,Le),R.font="10px Inter, sans-serif",R.textAlign="center",R.textBaseline="middle";for(let pe=J;pe<=U;pe+=1){const ve=s[pe];if(!ve)continue;const ae=Ke+pe*de-N.scrollLeft,G=ve.index===c;(G||En(ve.index,f))&&(R.fillStyle=G?"#e1f1ee":"#fff4da",R.fillRect(ae,0,g,Le)),R.fillStyle=G?"#155f59":"#687681",R.fillText(String(ve.index),ae+g/2,Le/2)}R.strokeStyle="rgba(30, 49, 58, 0.16)",R.beginPath(),R.moveTo(0,Le-.5),R.lineTo(F,Le-.5),R.stroke(),b&&(R.fillStyle="#ffffff",R.fillRect(0,0,Ke,Math.min(Le,O)),R.strokeStyle="rgba(30, 49, 58, 0.12)",R.beginPath(),R.moveTo(Ke-.5,0),R.lineTo(Ke-.5,O),R.stroke());const re=performance.now()-$;v.dataset.visibleCells=String(z),v.dataset.drawMs=re.toFixed(3),v.dataset.columnHeaderSticky="true",L.current({visibleCells:z,drawMs:re})}N.addEventListener("scroll",W,{passive:!0});const D=new ResizeObserver(W);return D.observe(N),W(),()=>{window.cancelAnimationFrame(ne),N.removeEventListener("scroll",W),D.disconnect()}},[f,b,i,g,u,s,d,h,o,r,a,e,c,l]),m.useEffect(()=>{const N=e.current;if(!N)return;const v=a.indexOf(l),ne=s.findIndex(D=>D.index===c);if(v<0||ne<0)return;const W=Ke+ne*de,ee=Le+v*oe;W<N.scrollLeft+Ke?N.scrollLeft=Math.max(0,W-Ke):W+g>N.scrollLeft+N.clientWidth&&(N.scrollLeft=W+g-N.clientWidth),ee<N.scrollTop+Le?N.scrollTop=Math.max(0,ee-Le):ee+Le>N.scrollTop+N.clientHeight&&(N.scrollTop=ee+Le-N.clientHeight)},[g,de,s,oe,a,e,c,l]);function Z(N){var le;const v=e.current;if(!v)return null;const ne=N.currentTarget.getBoundingClientRect();if(N.clientY-ne.top<Le)return null;const W=N.clientX-ne.left+v.scrollLeft,ee=N.clientY-ne.top+v.scrollTop,D=Math.floor((W-Ke)/de),$=Math.floor((ee-Le)/oe);if(D<0||$<0||D>=s.length||$>=a.length)return null;const F=(W-Ke)%de,O=(ee-Le)%oe;if(F>=g||O>=Le)return null;const E=a[$],Y=(le=s[D])==null?void 0:le.index;return E===void 0||Y===void 0?null:{row:E,column:Y}}function K(N,v=!1,ne=!1){var E;const W=Math.max(0,a.indexOf(l)),ee=Math.max(0,s.findIndex(Y=>Y.index===c));let D=W,$=ee;N==="ArrowLeft"&&($=Math.max(0,ee-1)),N==="ArrowRight"&&($=Math.min(s.length-1,ee+1)),N==="ArrowUp"&&(D=Math.max(0,W-1)),N==="ArrowDown"&&(D=Math.min(a.length-1,W+1)),N==="Home"&&($=0),N==="End"&&($=s.length-1);const F=a[D],O=(E=s[$])==null?void 0:E.index;F!==void 0&&O!==void 0&&q.current(F,O,{pin:v,anchor:ne})}return t.jsxs(t.Fragment,{children:[t.jsx(nl,{scrollRef:e,rowCount:a.length,columnCount:s.length,totalWidth:y,totalHeight:P,selectedRow:Math.max(0,a.indexOf(l)),selectedColumn:Math.max(0,s.findIndex(N=>N.index===c)),label:"Canvas matrix",revision:`${o}:${u}:${i.size}`,cellColor:(N,v)=>{const ne=a[N],W=s[v],ee=ne===void 0||!W?void 0:i.get(`${ne}:${W.index}`);if(!ee||ee.available===!1)return"#dfe6e8";const D=o==="raw"?ga(ee.rawValue,r):ee.value;return bs("#edf1f4",_s(u),Math.max(0,Math.min(1,D))*.8)}}),t.jsxs("div",{className:"matrix-canvas-spacer",style:{width:`${y}px`,height:`${P}px`},children:[t.jsx("div",{id:I,className:"visually-hidden","aria-live":"polite",children:S&&S.available!==!1?`Selected layer ${l}, token ${c}, displayed value ${Ma(S,o,"exact")}, raw value ${Pe(S.rawValue,S.metric,"exact")}, cache key ${S.sourceKey}.`:`Selected layer ${l}, token ${c}, unavailable.`}),t.jsx("canvas",{ref:w,className:"matrix-canvas",role:"grid",tabIndex:0,"aria-label":`Canvas matrix, ${a.length} rows by ${s.length} columns; selected layer ${l}, token ${c}`,"aria-rowcount":a.length,"aria-colcount":s.length,"aria-describedby":I,"aria-keyshortcuts":"ArrowLeft ArrowRight ArrowUp ArrowDown Home End Enter Shift+Enter Space","data-render-mode":"canvas",onKeyDown:N=>{["ArrowLeft","ArrowRight","ArrowUp","ArrowDown","Home","End"].includes(N.key)?(N.preventDefault(),N.stopPropagation(),K(N.key)):N.key==="Enter"?(N.preventDefault(),K("",!1,N.shiftKey)):N.key===" "&&(N.preventDefault(),K("",!0,!1))},onPointerDown:N=>{if(k!=="select")return;const v=Z(N);v&&(N.currentTarget.setPointerCapture(N.pointerId),V.current={pointerId:N.pointerId,row:v.row,startColumn:v.column,endColumn:v.column,pin:N.metaKey||N.ctrlKey,anchor:N.shiftKey})},onPointerMove:N=>{const v=performance.now(),ne=Z(N),W=ne?`${ne.row}:${ne.column}`:null;if(W!==H.current){H.current=W;const D=performance.now()-v;N.currentTarget.dataset.hoverMs=D.toFixed(3),M.current(ne?i.get(`${ne.row}:${ne.column}`)??null:null,D)}const ee=V.current;(ee==null?void 0:ee.pointerId)===N.pointerId&&ne&&(ee.endColumn=ne.column)},onPointerUp:N=>{const v=V.current;!v||v.pointerId!==N.pointerId||(V.current=null,v.startColumn!==v.endColumn&&!v.pin&&!v.anchor?X.current(fa(v.startColumn,v.endColumn)):q.current(v.row,v.endColumn,{pin:v.pin,anchor:v.anchor}))},onPointerCancel:()=>{V.current=null},onPointerLeave:()=>{H.current=null,M.current(null,0)}})]})]})}function dl({row:e,columns:n,cellMap:a,rawBounds:s,normalization:i,selectedRow:r,selectedColumn:o,comparisonCell:l,hoveredColumn:c,activeRange:d,onBrushStart:h,onHover:f,onSelectCell:b,onMoveFocus:g}){return t.jsxs(t.Fragment,{children:[t.jsxs("button",{className:`matrix-row-label ${r===e?"selected":""}`,onClick:y=>b(e,o,y),children:["L",e]}),n.map(y=>{const u=a.get(`${e}:${y.index}`),k=u!==void 0&&u.available!==!1,j=u?i==="raw"?ga(u.rawValue,s):u.value:0,T=r===e&&o===y.index,A=(l==null?void 0:l.row)===e&&l.column===y.index,C=En(y.index,d);return t.jsx("button",{"data-column":y.index,className:["matrix-cell",T?"selected":"",A?"comparison":"",c===y.index?"column-hover":"",C?"in-range":"",k?"":"unavailable"].join(" "),"data-row":e,"aria-label":k?`Layer ${e}, token ${y.index}, value ${Ma(u,i,"exact")}`:`Layer ${e}, token ${y.index}, unavailable`,"aria-current":T?"true":void 0,"aria-pressed":T||A,tabIndex:T?0:-1,style:{"--signal":j},onClick:w=>b(e,y.index,w),onKeyDown:w=>{["ArrowLeft","ArrowRight","ArrowUp","ArrowDown","Home","End"].includes(w.key)&&(w.preventDefault(),w.stopPropagation(),g(e,y.index,w.key))},onPointerDown:w=>{!w.shiftKey&&!w.metaKey&&!w.ctrlKey&&h(y.index)},onPointerEnter:()=>{u&&f(u)},onPointerLeave:()=>f(null),onFocus:()=>{u&&f(u)},onBlur:()=>f(null)},`${e}:${y.index}`)})]})}function cl({cell:e,token:n,normalization:a,provenance:s,comparisonCell:i}){return!e||!n?t.jsx("div",{className:"matrix-tooltip matrix-tooltip-empty",children:"Cell details · no matrix cell focused."}):t.jsxs("div",{className:"matrix-tooltip",children:[t.jsxs("span",{children:[t.jsx("b",{children:n.text||"␠"}),"token ",n.index," · id ",n.tokenId]}),t.jsxs("span",{children:[t.jsxs("b",{children:["L",e.row]}),e.metric]}),t.jsxs("span",{children:[t.jsx("b",{children:Pe(e.rawValue,e.metric,"exact")}),"raw"]}),t.jsxs("span",{children:[t.jsx("b",{children:Pe(e.value,"normalized","exact")}),"normalized"]}),t.jsxs("span",{children:[t.jsx("b",{children:Ma(e,a,"exact")}),"displayed"]}),i&&t.jsxs("span",{children:[t.jsx("b",{children:Ea(e.rawValue-i.rawValue,e.metric,"exact")}),"raw delta vs L",i.row,"/T",i.column]}),t.jsxs("span",{className:"tooltip-source",children:[t.jsx("b",{children:e.sourceKey}),"cache key"]}),t.jsxs("span",{className:"tooltip-source",children:[t.jsx("b",{children:s.kind.replace("_"," ")}),"evidence class"]})]})}function fa(e,n){return e<=n?[e,n]:[n,e]}function En(e,n){return n!==void 0&&e>=n[0]&&e<=n[1]}function ga(e,n){const[a,s]=n;return Math.abs(s-a)<1e-12?0:Math.max(0,Math.min(1,(e-a)/(s-a)))}function In(e,n,a){return a<n?n:Math.max(n,Math.min(a,e))}function _s(e){return e==="attention"?"#23748a":e==="mlp"?"#3c7b55":e==="nla"?"#a46d16":e==="causal"?"#c25428":"#b42335"}function bs(e,n,a){const s=l=>[Number.parseInt(l.slice(1,3),16),Number.parseInt(l.slice(3,5),16),Number.parseInt(l.slice(5,7),16)],i=s(e),r=s(n),o=i.map((l,c)=>Math.round(l+(r[c]-l)*a));return`rgb(${o[0]}, ${o[1]}, ${o[2]})`}function Ma(e,n,a="compact"){return e?Pe(n==="raw"?e.rawValue:e.value,n==="raw"?e.metric:"normalized",a):"n/a"}function ea(e,n,a){return Pe(e,n==="raw"?a:"normalized","compact")}function Hi({status:e,label:n,detail:a,ariaLabel:s,onRetry:i,onCancel:r,retryLabel:o,cancelLabel:l}){const c=ul(e),d=e==="loading"&&r,h=(e==="empty"||e==="error"||e==="cancelled")&&i;return t.jsxs("div",{className:`async-state-panel ${e} ${d||h?"has-action":""}`,"aria-label":s,"aria-live":"polite","aria-busy":e==="loading",children:[t.jsx("div",{className:"async-state-icon","aria-hidden":"true",children:t.jsx(c,{className:e==="loading"?"spin":void 0,size:15})}),t.jsxs("div",{className:"async-state-copy",children:[t.jsx("strong",{children:n}),t.jsx("span",{children:a})]}),d?t.jsx("button",{className:"async-state-action","aria-label":l??`Cancel ${s.toLowerCase()}`,title:"Cancel",onClick:r,children:t.jsx(Je,{size:14})}):h?t.jsx("button",{className:"async-state-action","aria-label":o??`Retry ${s.toLowerCase()}`,title:"Retry",onClick:i,children:t.jsx(fn,{size:14})}):null]})}function ul(e){switch(e){case"idle":return Lo;case"loading":return Wt;case"ready":return Xe;case"empty":return Ro;case"error":return lt;case"cancelled":return No}}const ml=100,ta=8;function Fi({records:e,value:n,ariaLabel:a,onChange:s,formatNativeLabel:i=o=>`${o.runId} / ${o.sampleId}`,className:r}){return e.length<=ml?t.jsx("select",{className:r,"aria-label":a,value:n,onChange:o=>s(o.target.value),children:e.map(o=>t.jsx("option",{value:o.key,children:i(o)},o.key))}):t.jsx(hl,{records:e,value:n,ariaLabel:a,onChange:s,className:r})}function hl({records:e,value:n,ariaLabel:a,onChange:s,className:i}){const[r,o]=m.useState(!1),[l,c]=m.useState(""),[d,h]=m.useState(0),f=m.useRef(null),b=m.useRef(null),g=m.useId(),y=e.find(M=>M.key===n)??e[0],u=m.useMemo(()=>{const M=l.trim().toLowerCase();return M?e.filter(q=>[q.runId,q.sampleId,q.modelName,q.sourceName,q.sourceType].some(X=>X.toLowerCase().includes(M))):e},[l,e]),k=Math.min(d,Math.max(0,u.length-1)),j=Math.max(0,Math.min(k-Math.floor(ta/2),u.length-ta)),T=u.slice(j,j+ta),A=u[k],C=r&&A?`${g}-option-${k}`:void 0;function w(){o(!0),c("");const M=e.findIndex(q=>q.key===n);h(Math.max(0,M))}function I(M){s(M.key),o(!1),c("")}function L(M){u.length!==0&&h(Math.max(0,Math.min(u.length-1,M)))}return t.jsxs("div",{ref:f,className:`adaptive-run-selector ${i??""}`,onBlur:M=>{M.currentTarget.contains(M.relatedTarget)||o(!1)},children:[t.jsx("input",{ref:b,role:"combobox","aria-label":a,"aria-expanded":r,"aria-controls":g,"aria-autocomplete":"list","aria-activedescendant":C,value:r?l:y?`${y.runId} / ${y.sampleId}`:"",placeholder:"Search runs",onFocus:M=>{w(),window.requestAnimationFrame(()=>M.currentTarget.select())},onClick:()=>{r||w()},onChange:M=>{r||o(!0),c(M.target.value),h(0)},onKeyDown:M=>{if(M.key==="Escape"){M.preventDefault(),o(!1),c("");return}if(!r&&["ArrowDown","ArrowUp","Enter"].includes(M.key)){M.preventDefault(),w();return}r&&(M.key==="ArrowDown"?(M.preventDefault(),L(k+1)):M.key==="ArrowUp"?(M.preventDefault(),L(k-1)):M.key==="Home"?(M.preventDefault(),L(0)):M.key==="End"?(M.preventDefault(),L(u.length-1)):M.key==="Enter"&&A&&(M.preventDefault(),I(A)))}}),t.jsx(Fn,{className:"adaptive-run-chevron",size:14,"aria-hidden":"true"}),r&&t.jsxs("div",{className:"adaptive-run-popup",children:[t.jsxs("div",{className:"adaptive-run-search-status",children:[t.jsx($t,{size:12}),t.jsxs("span",{children:[u.length," matching runs"]})]}),t.jsx("div",{id:g,className:"adaptive-run-listbox",role:"listbox","aria-label":`${a} results`,children:T.length>0?T.map((M,q)=>{const X=j+q,H=M.key===n;return t.jsxs("button",{id:`${g}-option-${X}`,type:"button",role:"option","aria-selected":H,className:X===k?"highlighted":"",onMouseEnter:()=>h(X),onMouseDown:V=>V.preventDefault(),onClick:()=>I(M),children:[t.jsxs("span",{children:[t.jsx("strong",{children:M.runId}),t.jsx("em",{children:M.sourceType})]}),t.jsxs("span",{children:[M.sampleId," · ",M.modelName]}),H&&t.jsx(Lt,{size:13,"aria-hidden":"true"})]},M.key)}):t.jsx("div",{className:"adaptive-run-no-results",role:"status",children:"No matching runs."})})]})]})}const Ui=Q({index:_().int().nonnegative(),text:p(),tokenId:_().int(),source:ye(["prompt","reply"]),risk:_().finite(),attribution:_().finite(),isSpecial:fe().optional(),generationStep:_().int().nonnegative().optional(),probeScore:_().finite().optional(),monitorHit:fe().optional()}),pl=Q({tokenIndex:_().int().nonnegative(),layer:_().int().nonnegative(),component:ye(["resid_post","attn_result","mlp_out"]),explanation:p(),cosine:_().finite(),mse:_().finite(),fve:_().finite().optional(),activationNorm:_().finite(),status:ye(["available","unavailable"]).optional(),profile:p().nullable().optional(),source:p().optional(),token:p().optional()}),Ki=Q({modelName:p().min(1),dModel:_().int().positive(),availableLayers:ie(_().int().nonnegative()).min(1),profiles:ie(Q({name:p().min(1),baseModel:p().min(1),layer:_().int().nonnegative(),component:p().min(1),dModel:_().int().positive(),modelMatches:fe(),layerAvailable:fe(),dModelMatches:fe(),status:ye(["compatible","artifact_missing","incompatible"]),reason:p().min(1)}))}),yl=Q({id:p().min(1),layer:_().int().nonnegative(),head:_().int().nonnegative(),role:p(),riskContribution:_().finite(),entropy:_().finite(),distributionByToken:ie(ie(_().finite()))}),fl=Q({id:p().min(1),layer:_().int().nonnegative(),neuron:_().int().nonnegative(),label:p(),activation:_().finite(),riskContribution:_().finite(),topTokens:ie(_().int().nonnegative()),positiveTopTokens:ie(_().int().nonnegative()),negativeTopTokens:ie(_().int().nonnegative()),activationsByToken:ie(_().finite()),maxAbsoluteActivation:_().finite().nonnegative()}),gl=Q({layer:_().int().nonnegative(),tokenIndex:_().int().nonnegative(),norm:_().finite(),rawDirection:_().finite(),riskDirection:_().finite(),semanticDensity:_().finite()}),Oi=Q({tokenId:_().int(),tokenText:p(),logit:_().finite(),probability:_().finite().nonnegative()}),Vi=Q({layer:_().int().nonnegative(),tokenIndex:_().int().nonnegative(),targetTokenId:_().int(),targetTokenText:p(),targetLogit:_().finite(),targetProbability:_().finite().nonnegative(),targetRank:_().int().positive(),topPredictions:ie(Oi).min(1),sourceKey:p().min(1)}),Bi=Vi.extend({modelTopPredictions:ie(Oi).min(1),lensSource:p().min(1),filename:p().min(1),revision:p().min(1),nPrompts:_().int().positive()}),xs=Q({layer:_().int().nonnegative(),tokenIndex:_().int().nonnegative(),value:_().finite(),rawValue:_().finite(),metric:p().min(1),sourceKey:p().min(1)}),Qi=Q({label:p().min(1),method:p().min(1),semantics:p().min(1),normalization:p().min(1),kind:ye(["raw","derived_proxy","safety_method","causal"])}),_l=Q({id:p().min(1),label:p().min(1),description:p().min(1),evidenceKind:ye(["raw","derived_proxy","safety_method","causal"]),signed:fe(),normalization:p().min(1),available:fe(),unavailableReason:p().optional(),rows:ie(Q({layer:_().int(),label:p().min(1),values:ie(_().finite()),sourceKey:p().min(1)}))}).superRefine((e,n)=>{!e.available&&!e.unavailableReason&&n.addIssue({code:"custom",path:["unavailableReason"],message:"is required when the attribution method is unavailable"})}),bl=Q({cleanPrompt:p(),corruptedPrompt:p(),component:ye(["resid_post","attn_out","z","mlp_out"]),head:_().int().nonnegative().optional(),targetTokenId:_().int().nonnegative(),targetTokenText:p(),cleanScore:_().finite(),corruptedScore:_().finite(),denominator:_().finite(),layers:ie(_().int().nonnegative()).min(1),positions:ie(_().int().nonnegative()).min(1),corruptedTokens:ie(Q({index:_().int().nonnegative(),tokenId:_().int().nonnegative(),text:p(),changed:fe()})).min(1),cells:ie(Q({layer:_().int().nonnegative(),tokenIndex:_().int().nonnegative(),patchedScore:_().finite(),causalEffect:_().finite(),recoveryPercentage:_().finite().nullable(),sourceKey:p().min(1)})).min(1),sourceRun:Q({runId:p().min(1),sampleId:p().min(1)}),sourceKey:p().min(1)}).superRefine((e,n)=>{e.component==="z"&&e.head===void 0&&n.addIssue({code:"custom",path:["head"],message:"is required for attention-head patching"})}),ws=Q({text:p(),tokenIds:ie(_().int().nonnegative()),tokens:ie(Q({index:_().int().nonnegative(),tokenId:_().int().nonnegative(),text:p()})),targetLogit:_().finite(),lexicalRisk:_().finite().nonnegative()}),xl=Q({mode:ye(["direction","neuron","sae_feature"]).default("direction"),feature:Q({kind:ye(["mlp_neuron","sae_feature"]),id:p().min(1),label:p().min(1),layer:_().int().nonnegative(),neuron:_().int().nonnegative().optional(),featureIndex:_().int().nonnegative().optional(),baselineActivation:_().finite(),meanActivation:_().finite().optional(),activeTokenCount:_().int().nonnegative().optional(),operation:ye(["suppress","reduce","enhance","invert","add","ablate"]),release:p().min(1).optional(),saeId:p().min(1).optional(),width:_().int().positive().optional(),architecture:$e("jump_relu").optional(),source:p().min(1).optional(),conceptLabel:p().min(1).optional(),conceptSource:ye(["neuronpedia","index"]).optional(),conceptUrl:p().url().optional(),positiveTokens:ie(p()).optional(),negativeTokens:ie(p()).optional()}).optional(),vector:Q({algorithmVersion:p().min(1).optional(),method:p().min(1),desiredPrompt:p().min(1),undesiredPrompt:p().min(1),positivePrompts:ie(p().min(1)).min(1).optional(),negativePrompts:ie(p().min(1)).min(1).optional(),positiveCount:_().int().positive().optional(),negativeCount:_().int().positive().optional(),activationReduce:p().min(1),rawNorm:_().finite().positive(),normalized:fe(),dimension:_().int().positive(),sourceKey:p().min(1),injectionKey:p().min(1).optional(),injectionPhase:ye(["generation","prompt"]).optional(),referenceTemplate:p().min(1).optional(),desiredTokenCount:_().int().positive().optional(),undesiredTokenCount:_().int().positive().optional(),sourceActivationNorm:_().finite().positive().optional(),appliedVectorNorm:_().finite().nonnegative().optional(),relativeStrength:_().finite().nonnegative().optional()}),layer:_().int().nonnegative(),sourceLayer:_().int().nonnegative().optional(),injectLayer:_().int().nonnegative().optional(),component:ye(["resid_post","attn_out","mlp_out"]),scale:_().finite(),positionStart:_().int().nonnegative(),positionEnd:_().int().positive(),targetTokenId:_().int().nonnegative(),targetTokenText:p(),seed:_().int().nonnegative(),maxNewTokens:_().int().positive(),temperature:_().finite().nonnegative(),original:ws,steered:ws,deltas:Q({targetLogit:_().finite(),lexicalRisk:_().finite(),tokenEditDistance:_().int().nonnegative(),generationChanged:fe(),firstDivergenceIndex:_().int().nonnegative().nullable().optional(),maxAbsLogit:_().finite().nonnegative().optional(),meanAbsLogit:_().finite().nonnegative().optional(),changedVocabularyLogits:_().int().nonnegative().optional(),topChangedTokenId:_().int().nonnegative().optional(),topChangedTokenDelta:_().finite().optional(),directionProjectionDelta:_().finite().optional(),featureActivationDelta:_().finite().optional(),effectStatus:ye(["changed","no_change"]).optional(),probeScore:_().finite().nullable(),probeReason:p().min(1)}),diff:ie(Q({kind:ye(["equal","replace","delete","insert"]),originalStart:_().int().nonnegative(),originalEnd:_().int().nonnegative(),steeredStart:_().int().nonnegative(),steeredEnd:_().int().nonnegative()})),sourceRun:Q({runId:p().min(1),sampleId:p().min(1)})}),wl=Q({runId:p().min(1),modelName:p().min(1),modelSource:p().min(1),sampleId:p().min(1),prompt:p(),tokens:ie(Ui).min(1),layers:ie(_().int().nonnegative()).min(1),nlaCompatibility:Ki,metricProvenance:Pt(p(),Qi),metadata:Pt(p(),Jt()).optional()}).superRefine((e,n)=>{new Set(e.layers).size!==e.layers.length&&n.addIssue({code:"custom",path:["layers"],message:"must not contain duplicates"}),e.tokens.forEach((a,s)=>{a.index!==s&&n.addIssue({code:"custom",path:["tokens",s,"index"],message:`must equal its array position (${s})`})})}),ht=Q({runId:p().min(1),modelName:p().min(1),modelSource:p().min(1),sampleId:p().min(1),prompt:p(),tokens:ie(Ui).min(1),layers:ie(_().int().nonnegative()).min(1),nla:ie(pl),nlaCompatibility:Ki,attentionHeads:ie(yl).min(1),mlpNeurons:ie(fl).min(1),residualCells:ie(gl).min(1),logitLens:ie(Vi).min(1),jLens:ie(Bi).default([]),attentionCells:ie(xs).min(1),mlpCells:ie(xs).min(1),attributionTracks:ie(Q({name:p().min(1),values:ie(_().finite())})),attributionMethods:ie(_l).min(1),patching:bl.optional(),intervention:xl.optional(),metricProvenance:Pt(p(),Qi),metadata:Pt(p(),Jt()).optional()}).superRefine((e,n)=>{const a=e.tokens.length,s=new Set(e.layers);e.tokens.forEach((i,r)=>{i.index!==r&&n.addIssue({code:"custom",path:["tokens",r,"index"],message:`must equal its array position (${r})`})}),s.size!==e.layers.length&&n.addIssue({code:"custom",path:["layers"],message:"must not contain duplicates"}),e.attentionHeads.forEach((i,r)=>{s.has(i.layer)||n.addIssue({code:"custom",path:["attentionHeads",r,"layer"],message:"is not declared in layers"}),(i.distributionByToken.length!==a||i.distributionByToken.some(o=>o.length!==a))&&n.addIssue({code:"custom",path:["attentionHeads",r,"distributionByToken"],message:`must be a ${a}×${a} destination×source matrix`})}),e.mlpNeurons.forEach((i,r)=>{i.activationsByToken.length!==a&&n.addIssue({code:"custom",path:["mlpNeurons",r,"activationsByToken"],message:`must contain one value per token (${a})`})}),e.attributionMethods.forEach((i,r)=>{i.rows.forEach((o,l)=>{o.values.length!==a&&n.addIssue({code:"custom",path:["attributionMethods",r,"rows",l,"values"],message:`must contain one value per token (${a})`})})});for(const[i,r]of[["residualCells",e.residualCells],["attentionCells",e.attentionCells],["mlpCells",e.mlpCells]])r.forEach((o,l)=>{s.has(o.layer)||n.addIssue({code:"custom",path:[i,l,"layer"],message:"is not declared in layers"}),o.tokenIndex>=a&&n.addIssue({code:"custom",path:[i,l,"tokenIndex"],message:"is outside the token array"})})}),kl=Q({schema_version:$e("1.0"),samples:ie(ht).min(1)});function vl(e){if(Tl(e)&&"schema_version"in e){if(e.schema_version!=="1.0")return{success:!1,diagnostics:[{path:"schema_version",issueType:"unsupported_schema_version",expected:'"1.0"',actual:Pa(e.schema_version),message:`unsupported schema version ${JSON.stringify(e.schema_version)}; expected "1.0"`}]};const a=kl.safeParse(e);return a.success?{success:!0,schemaVersion:"1.0",runs:a.data.samples}:{success:!1,diagnostics:_a(a.error.issues,e)}}const n=ht.safeParse(e);return n.success?{success:!0,schemaVersion:"legacy",runs:[n.data]}:{success:!1,diagnostics:_a(n.error.issues,e)}}function _a(e,n){return e.slice(0,12).map(a=>({path:a.path.length>0?a.path.join("."):"artifact",issueType:a.code,expected:jl(a),actual:Pa(Al(n,a.path)),message:a.message}))}function jl(e){var n;switch(e.code){case"invalid_type":return e.expected;case"invalid_value":return e.values.map(Pa).join(" or ");case"too_small":return`${e.origin} ${e.exact?"length =":e.inclusive===!1?">":">="} ${String(e.minimum)}`;case"too_big":return`${e.origin} ${e.exact?"length =":e.inclusive===!1?"<":"<="} ${String(e.maximum)}`;case"invalid_format":return`${e.format} format`;case"not_multiple_of":return`multiple of ${e.divisor}`;case"unrecognized_keys":return"declared schema fields only";case"invalid_union":return"one supported schema variant";case"invalid_key":return`valid ${e.origin} key`;case"invalid_element":return`valid ${e.origin} element`;case"custom":return typeof((n=e.params)==null?void 0:n.expected)=="string"?e.params.expected:e.message}}function Pa(e){if(e===void 0)return"missing";if(e===null)return"null";if(Array.isArray(e))return`array(length ${e.length})`;if(typeof e=="string")return Il(JSON.stringify(e));if(typeof e=="number"||typeof e=="boolean"||typeof e=="bigint")return String(e);if(typeof e=="object"){const n=Object.keys(e),a=n.slice(0,4).join(", ");return`object(${n.length} key${n.length===1?"":"s"}${a?`: ${a}${n.length>4?", ...":""}`:""})`}return typeof e}function Il(e){return e.length<=96?e:`${e.slice(0,93)}...`}function Al(e,n){let a=e;for(const s of n){if(a===null||typeof a!="object")return;a=a[s]}return a}function Tl(e){return typeof e=="object"&&e!==null&&!Array.isArray(e)}const Wa="safelens-explorer-session",Ji=ye(["overview","residual","attention","mlp","nla","patching","intervention","attribution"]),Sl=Q({label:p(),method:p(),semantics:p(),normalization:p(),kind:ye(["raw","derived_proxy","safety_method","causal"])}),Gi=Q({schemaVersion:$e("1.0"),status:ye(["available","unavailable","incompatible","not-computed","failed","loading","cancelled"]),statusReason:p(),primaryLabel:p(),primaryValue:p(),rawValue:p(),displayValue:p(),units:p(),evidenceClass:ye(["raw","derived_proxy","safety_method","causal"]),method:p(),normalization:p(),cacheKey:p(),shape:p(),sourceArtifact:p(),warnings:ie(p()),reproduction:Pt(p(),Jt())}),Cl=Q({schemaVersion:$e("1.0"),kind:ye(["attention_source_profile","signed_attribution_profile","mlp_activation_profile"]),label:p().min(1),axis:ye(["source_token","token"]),signed:fe(),originalLength:_().int().positive(),sampled:fe(),points:ie(Q({tokenIndex:_().int().nonnegative(),tokenId:_().int().optional(),tokenText:p(),value:_().finite()})).min(1).max(256)}),Nl=Q({tokenIndex:_().int().nonnegative(),tokenId:_().int().optional(),tokenText:p()}),Rl=Q({schemaVersion:$e("1.0"),kind:$e("attention_matrix"),label:p().min(1),originalSize:_().int().positive(),sampled:fe(),axis:ie(Nl).min(1).max(64),values:ie(ie(_().finite().min(0).max(1).nullable()).max(64)).max(64)}).superRefine((e,n)=>{e.originalSize<e.axis.length&&n.addIssue({code:"custom",path:["originalSize"],message:"must cover the stored axis"}),e.sampled===(e.originalSize===e.axis.length)&&n.addIssue({code:"custom",path:["sampled"],message:"must agree with originalSize"}),e.axis.forEach((a,s)=>{s>0&&a.tokenIndex<=e.axis[s-1].tokenIndex&&n.addIssue({code:"custom",path:["axis",s,"tokenIndex"],message:"must be strictly increasing"})}),e.values.length!==e.axis.length&&n.addIssue({code:"custom",path:["values"],message:"row count must match axis"}),e.values.forEach((a,s)=>{if(a.length!==e.axis.length){n.addIssue({code:"custom",path:["values",s],message:"column count must match axis"});return}a.forEach((i,r)=>{const o=e.axis[r].tokenIndex>e.axis[s].tokenIndex;(o&&i!==null||!o&&i===null)&&n.addIssue({code:"custom",path:["values",s,r],message:o?"causal mask must be null":"unmasked attention must be finite"})})})}),ks=Q({text:p(),tokens:ie(Q({index:_().int().nonnegative(),tokenId:_().int(),text:p()})).max(256),targetLogit:_().finite(),lexicalRisk:_().finite()}),Ll=Q({schemaVersion:$e("1.0"),sourceRun:Q({runId:p().min(1),sampleId:p().min(1)}),layer:_().int().nonnegative(),component:ye(["resid_post","attn_out","mlp_out"]),scale:_().finite(),positionStart:_().int().nonnegative(),positionEnd:_().int().positive(),targetTokenId:_().int(),targetTokenText:p(),seed:_().int(),maxNewTokens:_().int().min(1).max(256),temperature:_().finite().nonnegative(),original:ks,steered:ks,tokenEditDistance:_().int().nonnegative(),generationChanged:fe(),diff:ie(Q({kind:ye(["equal","replace","delete","insert"]),originalStart:_().int().nonnegative(),originalEnd:_().int().nonnegative(),steeredStart:_().int().nonnegative(),steeredEnd:_().int().nonnegative()})).max(512)}).superRefine((e,n)=>{e.positionEnd<=e.positionStart&&n.addIssue({code:"custom",path:["positionEnd"],message:"must be greater than positionStart"});for(const i of["original","steered"]){const r=e[i];r.tokens.length>e.maxNewTokens&&n.addIssue({code:"custom",path:[i,"tokens"],message:"exceeds maxNewTokens"}),r.tokens.forEach((o,l)=>{o.index!==l&&n.addIssue({code:"custom",path:[i,"tokens",l,"index"],message:"must be contiguous"})})}e.generationChanged!==e.tokenEditDistance>0&&n.addIssue({code:"custom",path:["generationChanged"],message:"must agree with tokenEditDistance"});let a=0,s=0;e.diff.forEach((i,r)=>{const o=["diff",r],l=i.originalEnd-i.originalStart,c=i.steeredEnd-i.steeredStart;(i.originalStart!==a||i.steeredStart!==s)&&n.addIssue({code:"custom",path:o,message:"opcodes must cover both sequences contiguously"}),(l<0||c<0||i.kind==="equal"&&(l===0||l!==c)||i.kind==="replace"&&(l===0||c===0)||i.kind==="delete"&&(l===0||c!==0)||i.kind==="insert"&&(l!==0||c===0))&&n.addIssue({code:"custom",path:o,message:"opcode span does not match its kind"}),a=i.originalEnd,s=i.steeredEnd}),(a!==e.original.tokens.length||s!==e.steered.tokens.length)&&n.addIssue({code:"custom",path:["diff"],message:"opcodes must cover every generated token"})}),$l=Q({id:p().min(1),runId:p().min(1),sampleId:p().min(1),tokenIndex:_().int().nonnegative(),tokenText:p(),tokenId:_().int().optional(),tokenSource:ye(["prompt","reply"]).optional(),modelName:p().optional(),modelSource:p().optional(),layer:_().int().nonnegative(),view:Ji,component:p(),metric:p().min(1),value:_().finite(),normalization:ye(["raw","normalized"]),headId:p().optional(),neuronId:p().optional(),trackName:p().optional(),sourceTokenIndex:_().int().nonnegative().optional(),sourceKey:p().optional(),provenance:Sl.optional(),profile:Cl.optional(),matrix:Rl.optional(),generation:Ll.optional(),assessment:Gi.optional(),capturedAt:p().optional()}).superRefine((e,n)=>{if(!e.matrix)return;(e.view!=="attention"||!e.headId)&&n.addIssue({code:"custom",path:["matrix"],message:"matrix snapshot requires attention head evidence"});const a=new Set(e.matrix.axis.map(s=>s.tokenIndex));a.has(e.tokenIndex)||n.addIssue({code:"custom",path:["matrix","axis"],message:"must include selected destination token"}),(e.sourceTokenIndex===void 0||!a.has(e.sourceTokenIndex))&&n.addIssue({code:"custom",path:["matrix","axis"],message:"must include selected source token"})}),El=Q({view:Ji,tokenIndex:_().int().nonnegative(),sourceTokenIndex:_().int().nonnegative().optional(),targetTokenIndex:_().int().nonnegative().optional(),tokenRange:ya([_().int().nonnegative(),_().int().nonnegative()]).optional(),layer:_().int().nonnegative(),headId:p(),attentionEdgeMode:ye(["incoming","outgoing"]).default("incoming"),nlaComponent:ye(["resid_post","attn_result","mlp_out"]).default("resid_post"),neuronId:p(),trackName:p(),metric:p().min(1),normalization:ye(["raw","normalized"])}),Ht=Q({size:_().int().min(8).max(64),mode:ye(["select","pan"]),axesPinned:fe(),fitMode:ye(["manual","fit"])}),Ml=Q({kind:$e(Wa),schemaVersion:$e("1.0"),exportedAt:p(),workspace:Q({runId:p().min(1),sampleId:p().min(1),modelName:p().optional(),modelSource:p().optional(),sourceName:p().optional(),artifactId:p().optional()}),selection:El,pinnedItems:ie($l).max(4),timeline:Q({mode:ye(["token","word"]),metric:ye(["risk","attribution","residual","nla","probe"]),query:p().max(256)}).optional(),compare:Q({baselineId:p().optional()}).optional(),activeEvidenceAssessment:Gi.optional(),matrices:Q({residual:Ht.optional(),attention:Ht.optional(),mlp:Ht.optional(),attribution:Ht.optional(),nla:Ht.optional(),patching:Ht.optional()}).optional(),filters:Q({evidence:ye(["top","neighborhood","all"])})});function Pl(e){return!!(e&&typeof e=="object"&&e.kind===Wa)}const Wl=["a[href]","button:not([disabled])","input:not([disabled])","select:not([disabled])","textarea:not([disabled])","[tabindex]:not([tabindex='-1'])"].join(",");function vs(e){return Array.from(e.querySelectorAll(Wl)).filter(n=>n.getClientRects().length>0&&n.getAttribute("aria-hidden")!=="true")}function Mn({open:e,dialogRef:n,initialFocusRef:a,returnFocusRef:s,restoreFocusRef:i,onClose:r}){const o=m.useRef(r);o.current=r,m.useEffect(()=>{if(!e||!n.current)return;const l=n.current;i&&(i.current=!0);const c=(s==null?void 0:s.current)??(document.activeElement instanceof HTMLElement?document.activeElement:null),d=Array.from(document.querySelectorAll(".topbar, .workspace")).map(g=>({element:g,wasInert:g.hasAttribute("inert")})),h=document.body.style.overflow;document.body.style.overflow="hidden";for(const{element:g}of d)g.setAttribute("inert","");const f=window.requestAnimationFrame(()=>{((a==null?void 0:a.current)??vs(l)[0]??l).focus()});function b(g){if(g.key==="Escape"){g.preventDefault(),o.current();return}if(g.key!=="Tab")return;const y=vs(l);if(!y.length){g.preventDefault(),l.focus();return}const u=y[0],k=y[y.length-1],j=document.activeElement;l.contains(j)?g.shiftKey&&j===u?(g.preventDefault(),k.focus()):!g.shiftKey&&j===k&&(g.preventDefault(),u.focus()):(g.preventDefault(),(g.shiftKey?k:u).focus())}return document.addEventListener("keydown",b,!0),()=>{window.cancelAnimationFrame(f),document.removeEventListener("keydown",b,!0),document.body.style.overflow=h;for(const{element:g,wasInert:y}of d)y||g.removeAttribute("inert");window.requestAnimationFrame(()=>{(i==null?void 0:i.current)!==!1&&(c!=null&&c.isConnected)&&c.focus()})}},[n,a,e,i,s])}const js=4*1024*1024,Ft=8;function Is({records:e,activeRecord:n,message:a,remoteState:s,onMessage:i,onSelect:r,onAdd:o,onRemove:l,onRestoreSession:c,onRefreshRemote:d,onCancelRemote:h}){const f=m.useRef(null),[b,g]=m.useState(""),[y,u]=m.useState("all"),[k,j]=m.useState(0),[T,A]=m.useState(null),C=m.useRef(null),w=m.useMemo(()=>e.filter(H=>{var V;return H.sourceType!=="bundled"||((V=H.sourceAlternatives)==null?void 0:V.some(oe=>oe.sourceType!=="bundled"))}).sort(Hl),[e]),I=m.useMemo(()=>{const H=b.trim().toLowerCase();return w.filter(V=>{var oe;return y!=="all"&&V.sourceType!==y&&!((oe=V.sourceAlternatives)!=null&&oe.some(de=>de.sourceType===y))?!1:H?[V.runId,V.sampleId,V.modelName,V.sourceName,Nt(V.sourceType),...na(V.lastUsedAt),...na(V.importedAt),...(V.sourceAlternatives??[]).flatMap(de=>[de.sourceName,de.modelName,Nt(de.sourceType),...na(de.importedAt)])].some(de=>de.toLowerCase().includes(H)):!0})},[w,b,y]),L=Math.min(k,Math.max(0,I.length-Ft)),M=I.slice(L,L+Ft);m.useEffect(()=>{j(0)},[b,y]);async function q(H){if(!H)return;if(H.size>js){i({tone:"error",title:"Artifact is too large for local JSON loading",details:[`${Cs(H.size)} exceeds the ${Cs(js)} limit.`]});return}let V;try{V=JSON.parse(await H.text())}catch(de){i({tone:"error",title:"Artifact is not valid JSON",details:[H.name],diagnostics:[{path:"artifact",issueType:"invalid_json",expected:"valid JSON document",actual:de instanceof Error?de.message:"JSON parsing failed",message:"The file could not be parsed before schema validation."}]});return}if(Pl(V)){const de=Ml.safeParse(V);if(!de.success){i({tone:"error",title:"Analysis session validation failed",details:[H.name],diagnostics:_a(de.error.issues,V)});return}c(de.data);return}const oe=vl(V);if(!oe.success){i({tone:"error",title:"Artifact schema validation failed",details:[H.name],diagnostics:oe.diagnostics});return}o(oe.runs,H.name,oe.schemaVersion)}function X(){if(!T)return;const H=T.key;A(null),l(H),window.requestAnimationFrame(()=>{var de;const V=(de=C.current)==null?void 0:de.querySelector('[aria-label="Run and sample selector"]');if(V!=null&&V.isConnected&&V.getClientRects().length>0){V.focus();return}const oe=Array.from(document.querySelectorAll('[aria-label="Open run library"]')).find(P=>P.getClientRects().length>0);oe==null||oe.focus()})}return t.jsxs(t.Fragment,{children:[t.jsxs("section",{ref:C,className:"panel-section run-library-panel",children:[t.jsxs("div",{className:"section-heading",children:[t.jsx($o,{size:16}),t.jsx("span",{children:"Run library"}),t.jsx("b",{children:e.length})]}),t.jsxs("div",{className:"run-library-controls",children:[t.jsxs("label",{children:[t.jsx("span",{children:"Run / sample"}),t.jsx(Fi,{records:e,ariaLabel:"Run and sample selector",value:n.key,onChange:r})]}),t.jsxs("button",{className:"import-artifact-button",onClick:()=>{var H;return(H=f.current)==null?void 0:H.click()},children:[t.jsx(Li,{size:14})," Import JSON"]}),t.jsx("input",{ref:f,className:"visually-hidden",type:"file",accept:"application/json,.json","aria-label":"Import Explorer artifact JSON",onChange:H=>{var V;q((V=H.target.files)==null?void 0:V[0]),H.target.value=""}})]}),t.jsx(Hi,{status:s.status,label:Fl(s),detail:s.detail,ariaLabel:"Workspace API status",onCancel:h,onRetry:d,cancelLabel:"Cancel workspace discovery",retryLabel:"Retry workspace discovery"}),s.diagnostics.length>0&&t.jsxs("details",{className:"workspace-diagnostics",children:[t.jsxs("summary",{children:[s.diagnostics.length," workspace diagnostic",s.diagnostics.length===1?"":"s"]}),s.diagnostics.map((H,V)=>t.jsx("span",{children:H},`${V}-${H}`))]}),t.jsxs("div",{className:"active-run-card",children:[t.jsxs("div",{children:[t.jsx("strong",{children:n.sampleId}),t.jsx(As,{record:n})]}),t.jsx("span",{children:n.modelName}),t.jsxs("span",{children:[n.tokenCount," tokens · ",n.layerCount," layers"]}),t.jsx(Dl,{record:n})]}),a&&t.jsxs("div",{className:`run-library-message ${a.tone}`,role:a.tone==="error"?"alert":"status",children:[a.tone==="error"?t.jsx(lt,{size:15}):t.jsx(Xe,{size:15}),t.jsxs("div",{children:[t.jsx("strong",{children:a.title}),a.details.map(H=>t.jsx("span",{children:H},H)),a.diagnostics&&a.diagnostics.length>0&&t.jsx("ol",{className:"artifact-diagnostic-list","aria-label":"Artifact validation diagnostics",children:a.diagnostics.map((H,V)=>t.jsxs("li",{children:[t.jsxs("div",{className:"artifact-diagnostic-heading",children:[t.jsx("code",{children:H.path}),t.jsx("span",{children:H.issueType})]}),t.jsxs("dl",{children:[t.jsxs("div",{children:[t.jsx("dt",{children:"Expected"}),t.jsx("dd",{children:H.expected})]}),t.jsxs("div",{children:[t.jsx("dt",{children:"Actual"}),t.jsx("dd",{children:H.actual})]})]}),t.jsx("p",{children:H.message})]},`${H.path}-${H.issueType}-${V}`))})]})]}),w.length>0&&t.jsxs("div",{className:"run-browser",children:[t.jsxs("div",{className:"run-browser-filters",children:[t.jsxs("label",{children:[t.jsxs("span",{children:[t.jsx($t,{size:12})," Find run"]}),t.jsx("input",{type:"search",value:b,placeholder:"run, sample, model, date","aria-label":"Search available runs",onChange:H=>g(H.target.value)})]}),t.jsxs("label",{children:[t.jsx("span",{children:"Source"}),t.jsxs("select",{"aria-label":"Filter runs by source",value:y,onChange:H=>u(H.target.value),children:[t.jsx("option",{value:"all",children:"All"}),t.jsx("option",{value:"remote",children:"Workspace"}),t.jsx("option",{value:"local",children:"Imported"}),t.jsx("option",{value:"generated",children:"Generated"})]})]})]}),I.length>0?t.jsxs(t.Fragment,{children:[t.jsxs("div",{className:"run-browser-window","aria-label":"Run browser window","aria-live":"polite",children:[t.jsxs("span",{children:[L+1,"-",Math.min(L+Ft,I.length)," of ",I.length]}),t.jsxs("div",{children:[t.jsx("button",{"aria-label":"Previous run window",title:"Previous runs",disabled:L===0,onClick:()=>j(Math.max(0,L-Ft)),children:t.jsx(Vt,{size:14})}),t.jsx("button",{"aria-label":"Next run window",title:"Next runs",disabled:L+Ft>=I.length,onClick:()=>j(L+Ft),children:t.jsx(dt,{size:14})})]})]}),t.jsx("div",{className:"recent-run-list","aria-label":"Available workspace and imported runs",children:M.map(H=>{var V,oe;return t.jsxs("div",{className:`${H.key===n.key?"active":""} ${H.sourceType} ${H.sourceType==="local"||H.sourceType==="generated"?"removable":"read-only"}`,children:[t.jsxs("button",{onClick:()=>r(H.key),children:[t.jsxs("span",{className:"recent-run-heading",children:[t.jsx("strong",{children:H.runId}),t.jsx(As,{record:H,compact:!0})]}),t.jsxs("span",{className:"recent-run-context",children:[H.sampleId," · ",H.modelName]}),t.jsxs("span",{className:"recent-run-dimensions",children:[H.tokenCount," tokens · ",H.layerCount," layers · ",H.sourceName]}),t.jsxs("span",{className:"recent-run-times",children:[t.jsx($i,{size:10,"aria-hidden":"true"}),t.jsx(Ts,{label:"Opened",value:H.lastUsedAt,empty:"not opened"}),t.jsx(Ts,{label:"Updated",value:H.importedAt,empty:"unknown"})]}),!!((V=H.sourceAlternatives)!=null&&V.length)&&t.jsxs("span",{className:"run-source-conflict-summary",children:[t.jsx(Ei,{size:11,"aria-hidden":"true"}),t.jsxs("b",{children:[1+(((oe=H.sourceAlternatives)==null?void 0:oe.length)??0)," sources"]}),t.jsxs("span",{children:["using ",Nt(H.sourceType)," over ",Yl(H.sourceAlternatives??[])]})]})]}),(H.sourceType==="local"||H.sourceType==="generated")&&t.jsx("button",{"aria-label":`Review removal of browser artifact ${H.runId} ${H.sampleId}`,title:"Review browser artifact removal",onClick:()=>A(H),children:t.jsx(_n,{size:13})})]},H.key)})})]}):t.jsxs("div",{className:"run-browser-empty",role:"status",children:[t.jsx($t,{size:15})," No runs match this filter."]})]})]}),T&&t.jsx(zl,{record:T,active:T.key===n.key,onCancel:()=>A(null),onConfirm:X})]})}function zl({record:e,active:n,onCancel:a,onConfirm:s}){const i=m.useId(),r=m.useRef(null),o=m.useRef(null);return Mn({open:!0,dialogRef:r,initialFocusRef:o,onClose:a}),So.createPortal(t.jsx("div",{className:"run-removal-backdrop",onMouseDown:l=>{l.target===l.currentTarget&&a()},children:t.jsxs("section",{ref:r,className:"run-removal-dialog",role:"dialog",tabIndex:-1,"aria-modal":"true","aria-labelledby":i,children:[t.jsxs("header",{children:[t.jsxs("div",{children:[t.jsxs("span",{children:[t.jsx(Eo,{size:13})," Browser storage"]}),t.jsx("h2",{id:i,children:"Remove browser artifact?"})]}),t.jsx("button",{"aria-label":"Close removal confirmation",onClick:a,children:t.jsx(Je,{size:18})})]}),t.jsx("p",{children:"This removes the saved browser copy from this profile. Workspace files and the bundled package remain unchanged."}),t.jsxs("dl",{className:"run-removal-metadata",children:[t.jsxs("div",{children:[t.jsx("dt",{children:"Run"}),t.jsx("dd",{children:e.runId})]}),t.jsxs("div",{children:[t.jsx("dt",{children:"Sample"}),t.jsx("dd",{children:e.sampleId})]}),t.jsxs("div",{children:[t.jsx("dt",{children:"Source"}),t.jsx("dd",{children:e.sourceName})]}),t.jsxs("div",{children:[t.jsx("dt",{children:"Type"}),t.jsx("dd",{children:e.sourceType==="generated"?"Generated result":"Imported artifact"})]}),t.jsxs("div",{children:[t.jsx("dt",{children:"Shape"}),t.jsxs("dd",{children:[e.tokenCount," tokens · ",e.layerCount," layers"]})]})]}),n&&t.jsxs("div",{className:"run-removal-active-note",children:[t.jsx(lt,{size:14}),t.jsx("span",{children:"This is the active Run. SafeLens will return to the bundled Run."})]}),t.jsxs("footer",{children:[t.jsx("button",{ref:o,onClick:a,children:"Cancel"}),t.jsxs("button",{className:"destructive",onClick:s,children:[t.jsx(_n,{size:14})," Remove browser copy"]})]})]})}),document.body)}function As({record:e,compact:n=!1}){var i,r;const a=Xi(e.sourceType),s=1+(((i=e.sourceAlternatives)==null?void 0:i.length)??0);return t.jsxs("span",{className:`status-pill status-${e.sourceType}${n?" compact":""}`,children:[t.jsx(a,{size:n?9:11,"aria-hidden":"true"}),t.jsxs("span",{children:[Nt(e.sourceType),((r=e.hydration)==null?void 0:r.mode)==="partial"?" · range":""]}),s>1&&t.jsxs("b",{children:[s," sources"]})]})}function Ts({label:e,value:n,empty:a}){const s=n?Date.parse(n):Number.NaN;return t.jsxs("span",{children:[t.jsx("b",{children:e}),Number.isFinite(s)&&n?t.jsx("time",{dateTime:new Date(s).toISOString(),children:Zi(n)}):t.jsx("em",{children:n&&n!=="unknown"?n:a})]})}function Dl({record:e}){const n=e.sourceAlternatives??[];if(n.length===0)return null;const a={sourceType:e.sourceType,sourceName:e.sourceName,importedAt:e.importedAt,artifactId:e.artifactId,modelName:e.modelName,tokenCount:e.tokenCount,layerCount:e.layerCount,loaded:e.run!==null};return t.jsxs("details",{className:"run-source-resolution",children:[t.jsxs("summary",{children:[t.jsx(Ei,{size:12,"aria-hidden":"true"}),t.jsxs("span",{children:[1+n.length," indexed sources"]}),t.jsxs("b",{children:["using ",Nt(e.sourceType)]})]}),t.jsxs("div",{className:"source-priority-rule",children:[t.jsx("span",{children:"Selection priority"}),t.jsx("b",{children:"Bundled → browser artifact → workspace API"})]}),t.jsxs("div",{className:"source-candidate-list",role:"list","aria-label":"Run source candidates",children:[t.jsx(Ss,{source:a,selected:!0,selectedRecord:e}),n.map((s,i)=>t.jsx(Ss,{source:s,selected:!1,selectedRecord:e},`${s.sourceType}:${s.sourceName}:${s.artifactId??i}`))]}),t.jsx("p",{children:"Lower-priority duplicates stay indexed, but values are never mixed across artifacts."})]})}function Ss({source:e,selected:n,selectedRecord:a}){const s=Xi(e.sourceType),i=e.modelName!==a.modelName||e.tokenCount!==a.tokenCount||e.layerCount!==a.layerCount;return t.jsxs("div",{className:`${n?"selected":"shadowed"}${i?" metadata-diff":""}`,role:"listitem",children:[t.jsx(s,{size:12,"aria-hidden":"true"}),t.jsxs("span",{children:[t.jsxs("b",{children:[Nt(e.sourceType)," · ",e.sourceName]}),t.jsxs("small",{children:[e.modelName," · ",e.tokenCount," tokens · ",e.layerCount," layers · ",ql(e.importedAt)]})]}),t.jsx("em",{children:n?"selected":i?"metadata differs":"lower priority"})]})}function Xi(e){return e==="bundled"?Sa:e==="local"?Li:e==="generated"?tt:yt}function Yl(e){return[...new Set(e.map(n=>Nt(n.sourceType)))].join(" + ")}function ql(e){const n=new Date(e);return Number.isFinite(n.getTime())?`${n.toISOString().slice(0,16).replace("T"," ")} UTC`:e}function Zi(e){const n=new Date(e);return Number.isFinite(n.getTime())?`${n.toISOString().slice(5,16).replace("T"," ")} UTC`:e}function Hl(e,n){const a=e.lastUsedAt?Date.parse(e.lastUsedAt):Number.NaN,s=n.lastUsedAt?Date.parse(n.lastUsedAt):Number.NaN;if(Number.isFinite(a)!==Number.isFinite(s))return Number.isFinite(s)?1:-1;if(Number.isFinite(a)&&Number.isFinite(s)&&a!==s)return s-a;const i=Date.parse(e.importedAt),r=Date.parse(n.importedAt);return(Number.isFinite(r)?r:0)-(Number.isFinite(i)?i:0)}function na(e){if(!e)return[];const n=Date.parse(e);if(!Number.isFinite(n))return[e];const a=new Date(n);return[e,a.toISOString(),a.toUTCString(),Zi(e)]}function Nt(e){return e==="bundled"?"bundled":e==="local"?"local":e==="generated"?"generated":"workspace"}function Fl(e){switch(e.status){case"idle":return"Workspace discovery idle";case"loading":return"Connecting to workspace";case"ready":return`${e.rootName} · ${e.loadedCount} ready`;case"empty":return`${e.rootName} · no runs found`;case"error":return e.failureKind==="offline"?"Workspace offline":e.failureKind==="api"?"Workspace API error":e.failureKind==="validation"?"Workspace schema error":"Workspace data error";case"cancelled":return"Workspace discovery cancelled"}}function Cs(e){return`${(e/(1024*1024)).toFixed(1)} MB`}function Ul({job:e,status:n,submitting:a,ariaLabel:s,tone:i}){const r=m.useRef(performance.now()),o=n!=="error"&&(a||(e==null?void 0:e.status)==="idle"||(e==null?void 0:e.status)==="loading"),[l,c]=m.useState(()=>performance.now()),d=m.useRef({updatedAt:e==null?void 0:e.updatedAt,at:performance.now()});d.current.updatedAt!==(e==null?void 0:e.updatedAt)&&(d.current={updatedAt:e==null?void 0:e.updatedAt,at:performance.now()}),m.useEffect(()=>{if(!o)return;c(performance.now());const A=window.setInterval(()=>c(performance.now()),1e3);return()=>window.clearInterval(A)},[o]);const h=Kl((e==null?void 0:e.progress)??0),f=a?"Submitting":Ol(e==null?void 0:e.stage,n),b=Ns(e==null?void 0:e.createdAt),g=Ns(e==null?void 0:e.updatedAt),y=b!==null&&g!==null?Math.max(0,Math.floor((g-b)/1e3)):0,u=e?d.current.at:r.current,k=o?Math.max(0,Math.floor((l-u)/1e3)):0,j=y+k,T=Vl(j);return t.jsxs("div",{className:`job-progress ${i} ${o?"active":"terminal"}`,"aria-label":s,children:[t.jsxs("div",{className:"job-progress-metrics",children:[t.jsxs("div",{children:[t.jsx("span",{children:"Stage"}),t.jsx("strong",{title:f,children:f})]}),t.jsxs("div",{children:[t.jsx("span",{children:"Progress"}),t.jsxs("strong",{children:[h,"%"]})]}),t.jsxs("div",{children:[t.jsx("span",{children:"Elapsed"}),t.jsx("time",{dateTime:`PT${j}S`,children:T})]})]}),t.jsx("div",{className:"job-progress-track",role:"progressbar","aria-label":`${s} completion`,"aria-valuemin":0,"aria-valuemax":100,"aria-valuenow":h,"aria-valuetext":`${h}% complete; ${f}; elapsed ${T}`,children:t.jsx("span",{style:{width:`${h}%`}})})]})}function Kl(e){return Math.max(0,Math.min(100,Math.round(Number.isFinite(e)?e:0)))}function Ns(e){if(!e)return null;const n=Date.parse(e);return Number.isFinite(n)?n:null}function Ol(e,n){return((e==null?void 0:e.trim())||n).replace(/[-_]+/g," ").replace(/\b\w/g,s=>s.toUpperCase()).replace(/\b(nla|av|ar)\b/gi,s=>s.toUpperCase())}function Vl(e){if(e<60)return`${e}s`;const n=Math.floor(e/3600),a=Math.floor(e%3600/60),s=e%60;return n>0?`${n}h ${a}m`:`${a}m ${s}s`}const Re="/api",Bl=Q({runId:p().min(1),sampleId:p().min(1),modelName:p().min(1),modelSource:p().min(1),tokenCount:_().int().positive(),layerCount:_().int().positive(),artifactId:p().min(1),sourceName:p().min(1),modifiedAt:p().min(1),sizeBytes:_().int().nonnegative(),promptPreview:p().max(160).nullable().optional(),parentRun:Q({runId:p().min(1),sampleId:p().min(1)}).nullable().optional(),conversationId:p().min(1).nullable().optional(),turnIndex:_().int().nonnegative().nullable().optional(),chunkProtocol:$e("safelens-chunks-v1").optional()}),Ql=Q({schemaVersion:$e("1.0"),source:$e("local-workspace"),rootName:p(),runs:ie(Bl),diagnostics:ie(Q({sourceName:p(),code:p(),message:p()}))}),er=ye(["residualCells","logitLens","jLens","attentionHeads","attentionCells","mlpNeurons","mlpCells","attributionTracks","attributionMethods","nla","patching","intervention"]),Jl=Q({schemaVersion:$e("1.0"),protocol:$e("safelens-chunks-v1"),runId:p().min(1),sampleId:p().min(1),artifactId:p().min(1),version:p().min(1),base:Pt(p(),Jt()),chunks:ie(Q({component:er,itemCount:_().int().nonnegative(),rangeAxis:ye(["token","token-square","token-values","none"]),layerFilter:fe(),selectorFilter:fe()}))}),Gl=Q({schemaVersion:$e("1.0"),protocol:$e("safelens-chunks-v1"),runId:p().min(1),sampleId:p().min(1),artifactId:p().min(1),version:p().min(1),component:er,tokenRange:ya([_().int().nonnegative(),_().int().positive()]),sourceRange:ya([_().int().nonnegative(),_().int().positive()]).nullable().optional(),layer:_().int().nonnegative().nullable(),selector:p().nullable(),data:Jt()}),Rs=new Map,Ls=new Map,hn=new Map,Xl=32,Zl=96;function tr(e,n,a){if(n.aborted)return Promise.reject(Es());let s=hn.get(e);if(s!=null&&s.controller.signal.aborted&&(hn.delete(e),s=void 0),!s){const i=new AbortController;s={controller:i,promise:a(i.signal),subscribers:0,settled:!1},hn.set(e,s),s.promise.then(()=>$s(e,s),()=>$s(e,s))}return s.abortTimer!==void 0&&(clearTimeout(s.abortTimer),s.abortTimer=void 0),s.subscribers+=1,new Promise((i,r)=>{let o=!1;const l=d=>{o||(o=!0,n.removeEventListener("abort",c),s.subscribers=Math.max(0,s.subscribers-1),d&&s.subscribers===0&&!s.settled&&(s.abortTimer=setTimeout(()=>{s.subscribers===0&&!s.settled&&s.controller.abort()},0)))},c=()=>{l(!0),r(Es())};n.addEventListener("abort",c,{once:!0}),s.promise.then(d=>{l(!1),i(d)},d=>{l(!1),r(d)})})}function $s(e,n){n.settled=!0,hn.get(e)===n&&hn.delete(e)}function Es(){return new DOMException("The artifact request was cancelled.","AbortError")}function nr(e,n){const a=e.get(n);return a!==void 0&&(e.delete(n),e.set(n,a)),a}function ar(e,n,a,s){for(e.delete(n),e.set(n,a);e.size>s;)e.delete(e.keys().next().value)}async function ed(e){var s;const n=await fetch(`${Re}/runs`,{signal:e,headers:{Accept:"application/json"},cache:"no-store"});if(!n.ok)throw new je("http_error",`Explorer API returned HTTP ${n.status} for the run index.`);const a=Ql.safeParse(await n.json());if(!a.success)throw new je("invalid_index",`Explorer API index failed validation: ${((s=a.error.issues[0])==null?void 0:s.message)??"unknown error"}`);return{summaries:a.data.runs,rootName:a.data.rootName,diagnostics:a.data.diagnostics.map(i=>`${i.sourceName} [${i.code}]: ${i.message}`)}}async function Ms(e,n){const a=await fetch(`${Re}/runs/${encodeURIComponent(e.runId)}/samples/${encodeURIComponent(e.sampleId)}`,{signal:n,headers:{Accept:"application/json"},cache:"no-store"});if(!a.ok)throw new je("sample_error",`Could not load ${e.runId}/${e.sampleId}: HTTP ${a.status}.`);const s=ht.safeParse(await a.json());if(!s.success){const i=s.error.issues[0];throw new je("invalid_sample",`${e.runId}/${e.sampleId} failed at ${(i==null?void 0:i.path.join("."))||"artifact"}: ${(i==null?void 0:i.message)||"invalid sample"}.`)}return s.data}function td(e,n){const a=[e.artifactId,e.modifiedAt,e.sizeBytes,e.runId,e.sampleId].join(":");return tr(`metadata:${a}`,n,s=>nd(e,a,s))}async function nd(e,n,a){const s=nr(Rs,n),i=await fetch(`${Re}/runs/${encodeURIComponent(e.runId)}/samples/${encodeURIComponent(e.sampleId)}/metadata`,{signal:a,headers:{Accept:"application/json",...s?{"If-None-Match":s.etag}:{}},cache:"no-cache"});if(i.status===304&&s)return s.value;if(!i.ok)throw new je("metadata_error",`Could not load metadata for ${e.runId}/${e.sampleId}: HTTP ${i.status}.`);const r=Jl.safeParse(await i.json());if(!r.success||r.data.runId!==e.runId||r.data.sampleId!==e.sampleId)throw new je("invalid_metadata",`${e.runId}/${e.sampleId} returned invalid or mismatched chunk metadata.`);const o=i.headers.get("ETag")??`"${r.data.version}"`;return ar(Rs,n,{etag:o,value:r.data},Xl),r.data}function sr(e,n,a){if(!Number.isInteger(n.tokenStart)||!Number.isInteger(n.tokenEnd)||n.tokenStart<0||n.tokenEnd<=n.tokenStart||n.tokenEnd-n.tokenStart>512)throw new je("invalid_chunk_range","Chunk range must be an integer half-open interval of at most 512 tokens.");if(n.sourceStart===void 0!=(n.sourceEnd===void 0)||n.sourceStart!==void 0&&(!Number.isInteger(n.sourceStart)||!Number.isInteger(n.sourceEnd)||n.sourceStart<0||n.sourceEnd<=n.sourceStart||n.sourceEnd-n.sourceStart>512))throw new je("invalid_source_range","Attention source range must be an integer half-open interval of at most 512 tokens.");const s=new URLSearchParams({tokenStart:String(n.tokenStart),tokenEnd:String(n.tokenEnd)});n.layer!==void 0&&s.set("layer",String(n.layer)),n.selector&&s.set("selector",n.selector),n.sourceStart!==void 0&&s.set("sourceStart",String(n.sourceStart)),n.sourceEnd!==void 0&&s.set("sourceEnd",String(n.sourceEnd));const i=[e.artifactId,e.modifiedAt,e.sizeBytes,e.runId,e.sampleId,n.component,n.tokenStart,n.tokenEnd,n.sourceStart??n.tokenStart,n.sourceEnd??n.tokenEnd,n.layer??"all",n.selector??"all"].join(":");return tr(`chunk:${i}`,a,r=>ad(e,n,s,i,r))}async function ad(e,n,a,s,i){const r=nr(Ls,s),o=await fetch(`${Re}/runs/${encodeURIComponent(e.runId)}/samples/${encodeURIComponent(e.sampleId)}/chunks/${n.component}?${a}`,{signal:i,headers:{Accept:"application/json",...r?{"If-None-Match":r.etag}:{}},cache:"no-cache"});if(o.status===304&&r)return r.value;if(!o.ok)throw new je("chunk_error",`Could not load ${n.component} chunk: HTTP ${o.status}.`);const l=Gl.safeParse(await o.json());if(!l.success||l.data.runId!==e.runId||l.data.sampleId!==e.sampleId||l.data.component!==n.component)throw new je("invalid_chunk",`${e.runId}/${e.sampleId} returned a mismatched ${n.component} chunk.`);const c=o.headers.get("ETag")??`"${l.data.version}:${s}"`;return ar(Ls,s,{etag:c,value:l.data},Zl),l.data}class je extends Error{constructor(n,a,s,i){super(a),this.code=n,this.httpStatus=s,this.serverCode=i,this.name="ExplorerApiError"}}const sd=Q({role:ye(["user","assistant"]),content:p().min(1)}),ir=Q({id:p().min(1),kind:$e("prompt-run"),status:ye(["idle","loading","ready","error","cancelled"]),stage:p(),progress:_().int().min(0).max(100),detail:p(),createdAt:p(),updatedAt:p(),request:Q({prompt:p(),template:ye(["plain","chat"]),model:p(),seed:_().int(),maxNewTokens:_().int(),temperature:_(),messages:ie(sd).default([])}),result:ht.nullable(),error:p().nullable()}),id=Q({models:ie(p().min(1)).min(1),templates:ie(ye(["plain","chat"])),maxNewTokens:_().int().positive()}),rr=Q({name:p().min(1),shortName:p().min(1),definition:p().min(1),threshold:_().min(0).max(1)}),rd=Q({id:p().min(1),category:p().min(1),prompt:p().nullable().optional(),cleanPrompt:p().nullable().optional(),corruptedPrompt:p().nullable().optional(),desiredPrompt:p().nullable().optional(),undesiredPrompt:p().nullable().optional(),targetText:p().nullable().optional(),expected:p().min(1)}),od=Q({id:p().min(1),name:p().min(1),version:p().min(1),task:p().min(1),description:p().min(1),source:p().min(1),metric:rr,samples:ie(rd).min(1)}),ld=Q({id:ye(["steering","patching"]),name:p().min(1),kind:$e("optimization"),description:p().min(1),paperTitle:p().min(1),paperUrl:p().url(),implementation:p().min(1),supportedDatasetIds:ie(p().min(1)).min(1)}),dd=Q({datasets:ie(od).min(1),algorithms:ie(ld).min(1)}),cd=Q({sampleId:p().min(1),category:p().min(1),prompt:p(),status:ye(["complete","error"]),passed:fe(),detail:p(),original:p().optional(),steered:p().optional(),patched:p().optional(),diagnostics:Pt(p(),Jt()).optional()}),ud=Q({dataset:Q({id:p(),name:p(),version:p(),sampleCount:_().int()}),algorithm:Q({id:ye(["steering","patching"]),name:p(),implementation:p()}),execution:Q({mode:p().optional(),source:$e("real-local-model"),model:p(),modelSource:p().optional(),revision:p().optional(),device:p().optional(),dtype:p().optional(),seed:_().int().optional(),layer:_().int().optional(),requestedLayer:_().int().optional(),component:p().optional(),maxNewTokens:_().int().optional()}),metric:rr.extend({passed:_().int().nonnegative(),completed:_().int().nonnegative(),errors:_().int().nonnegative(),accuracy:_().min(0).max(1),meetsThreshold:fe()}),rows:ie(cd)}),md=Q({id:p().min(1),kind:$e("dataset-test"),status:ye(["idle","loading","ready","error","cancelled"]),stage:p(),progress:_().int().min(0).max(100),detail:p(),createdAt:p(),updatedAt:p(),request:Q({datasetId:p(),algorithmId:ye(["steering","patching"]),model:p(),sampleIds:ie(p()),layer:_().int(),strength:_(),seed:_().int(),maxNewTokens:_().int()}),result:ud.nullable(),error:p().nullable()}),hd=Q({modelName:p().min(1),text:p(),tokens:ie(Q({index:_().int().nonnegative(),tokenId:_().int().nonnegative(),text:p()})),truncated:fe()}),or=Q({id:p().min(1),kind:$e("attribution"),status:ye(["idle","loading","ready","error","cancelled"]),stage:p(),progress:_().int().min(0).max(100),detail:p(),createdAt:p(),updatedAt:p(),request:Q({sourceRun:Q({runId:p(),sampleId:p(),modelName:p()}),response:p(),objective:$e("response_token_logit"),targetResponseIndex:_().int().nonnegative(),baseline:ye(["pad_token","zero_token_id"]),nSteps:_().int()}),result:ht.nullable(),error:p().nullable()}),pd=Q({name:p(),base_model:p(),layer:_().int(),component:p(),d_model:_().int().positive(),av_repo:p(),ar_repo:p().nullable(),av_revision:p().nullable().default(null),ar_revision:p().nullable().default(null),gated:fe(),description:p()}),lr=Q({profile:p(),baseModel:p(),layer:_().int(),component:p(),dModel:_().int(),avRepo:p(),arRepo:p().nullable(),gated:fe(),tokenConfigured:fe(),modelMatches:fe(),layerAvailable:fe(),dModelMatches:fe(),status:ye(["compatible","incompatible","authorization_required"]),canSubmit:fe(),reason:p()}),dr=Q({id:p().min(1),kind:$e("nla"),status:ye(["idle","loading","ready","error","cancelled"]),stage:p(),progress:_().int().min(0).max(100),detail:p(),createdAt:p(),updatedAt:p(),request:Q({profile:p(),positions:ie(_().int()).min(1).max(8),revision:p(),maxNewTokens:_().int(),loadReconstructor:$e(!0),confirmGatedAccess:fe(),sourceRun:Q({runId:p(),sampleId:p(),modelName:p()}),preflight:lr}),result:ht.nullable(),error:p().nullable()}),yd=Q({packageInstalled:fe(),defaultModel:p(),defaultSource:p(),defaultFilename:p().min(1),defaultRevision:p().min(1),profiles:ie(Q({name:p().min(1),baseModel:p().min(1),source:p().min(1),filename:p().min(1),revision:p().min(1),dModel:_().int().positive(),sourceLayers:ie(_().int().nonnegative()).min(1),defaultLayer:_().int().nonnegative(),nPrompts:_().int().positive(),description:p().min(1)})).default([])}),cr=Q({packageInstalled:fe(),modelAllowed:fe(),layerAvailable:fe(),positionValid:fe(),lensConfigured:fe(),artifactChecked:fe(),fittedLayers:ie(_().int().nonnegative()),lensDModel:_().int().positive().nullable(),canSubmit:fe(),reason:p().min(1)}),ur=Q({id:p().min(1),kind:$e("jlens"),status:ye(["idle","loading","ready","error","cancelled"]),stage:p(),progress:_().int().min(0).max(100),detail:p(),createdAt:p(),updatedAt:p(),request:Q({layer:_().int().nonnegative(),position:_().int().nonnegative(),lensSource:p().min(1),filename:p().min(1),revision:p().min(1),topK:_().int().min(3).max(50),sourceRun:Q({runId:p(),sampleId:p(),modelName:p()}),preflight:cr}),result:ht.nullable(),error:p().nullable()}),mr=Q({modelAllowed:fe(),promptsDiffer:fe(),tokenCountMatches:fe(),targetTokenValid:fe(),componentSupported:fe(),cleanTokenCount:_().int().positive(),corruptedTokenCount:_().int().nonnegative(),changedPositions:ie(_().int().nonnegative()),targetTokenId:_().int().nonnegative(),targetTokenText:p(),corruptedTokens:ie(Q({index:_().int().nonnegative(),tokenId:_().int().nonnegative(),text:p(),changed:fe()})),canSubmit:fe(),reason:p()}),hr=Q({id:p().min(1),kind:$e("patching"),status:ye(["idle","loading","ready","error","cancelled"]),stage:p(),progress:_().int().min(0).max(100),detail:p(),createdAt:p(),updatedAt:p(),request:Q({corruptedPrompt:p(),component:ye(["resid_post","attn_out","z","mlp_out"]),layers:ie(_().int()).min(1),positions:ie(_().int()).min(1),head:_().int().nonnegative().optional(),targetTokenId:_().int().nonnegative(),sourceRun:Q({runId:p(),sampleId:p(),modelName:p()}),preflight:mr}),result:ht.nullable(),error:p().nullable()}),pr=Q({mode:ye(["direction","neuron","sae_feature"]).default("direction"),modelAllowed:fe(),layerAvailable:fe(),componentSupported:fe(),positionRangeValid:fe(),targetTokenValid:fe(),referencesDiffer:fe(),featureAvailable:fe().default(!0),saeProfileValid:fe().default(!0),saeRuntimeAvailable:fe().default(!0),targetTokenId:_().int().nonnegative(),targetTokenText:p(),positionStart:_().int().nonnegative(),positionEnd:_().int().positive(),canSubmit:fe(),reason:p()}),fd=Q({id:p().min(1),label:p().min(1),modelName:p().min(1),release:p().min(1),saeId:p().min(1),layer:_().int().nonnegative(),component:$e("resid_post"),width:_().int().positive(),architecture:$e("jump_relu"),source:p().min(1)}),gd=Q({modelName:p().min(1),layer:_().int().nonnegative(),featureIndex:_().int().nonnegative(),label:p().min(1),source:ye(["neuronpedia","index"]),url:p().url().nullable().optional(),positiveTokens:ie(p()).default([]),negativeTokens:ie(p()).default([])}),yr=Q({id:p().min(1),kind:$e("intervention"),status:ye(["idle","loading","ready","error","cancelled"]),stage:p(),progress:_().int().min(0).max(100),detail:p(),createdAt:p(),updatedAt:p(),request:Q({mode:ye(["direction","neuron","sae_feature"]).default("direction"),desiredPrompt:p(),undesiredPrompt:p(),positivePrompts:ie(p()).min(1).optional(),negativePrompts:ie(p()).min(1).optional(),activationReduce:ye(["last_token","mean"]).default("last_token"),layer:_().int().nonnegative(),sourceLayer:_().int().nonnegative().optional(),injectLayer:_().int().nonnegative().optional(),component:ye(["resid_post","attn_out","mlp_out"]),scale:_(),positionStart:_().int().nonnegative(),positionEnd:_().int().positive(),targetTokenId:_().int().nonnegative(),seed:_().int().nonnegative(),maxNewTokens:_().int().positive(),temperature:_().nonnegative(),neuron:_().int().nonnegative().nullish().transform(e=>e??void 0),saeRelease:p().min(1).nullish().transform(e=>e??void 0),saeId:p().min(1).nullish().transform(e=>e??void 0),featureIndex:_().int().nonnegative().nullish().transform(e=>e??void 0),saeOperation:ye(["add","ablate"]).nullish().transform(e=>e??void 0),sourceRun:Q({runId:p(),sampleId:p(),modelName:p()}),preflight:pr}),result:ht.nullable(),error:p().nullable()});async function _d(e){const n=await fetch(`${Re}/jobs/prompt`,{method:"POST",headers:{Accept:"application/json","Content-Type":"application/json"},body:JSON.stringify(e)});if(!n.ok)throw await qe(n,"prompt_submit_error");return _r(await n.json())}async function fr(e){const n=await fetch(`${Re}/prompt/options`,{headers:{Accept:"application/json"},signal:e});if(!n.ok)throw await qe(n,"prompt_options_error");const a=id.safeParse(await n.json());if(!a.success)throw new je("prompt_options_invalid_schema","Prompt options failed validation.",n.status);return a.data}async function bd(e){var s;const n=await fetch(`${Re}/datasets`,{signal:e,headers:{Accept:"application/json"},cache:"no-store"});if(!n.ok)throw await qe(n,"dataset_catalog_error");const a=dd.safeParse(await n.json());if(!a.success)throw new je("invalid_dataset_catalog",`Dataset catalog failed validation: ${((s=a.error.issues[0])==null?void 0:s.message)??"unknown error"}`);return a.data}async function xd(e){const n=await fetch(`${Re}/jobs/dataset-test`,{method:"POST",headers:{Accept:"application/json","Content-Type":"application/json"},body:JSON.stringify(e)});if(!n.ok)throw await qe(n,"dataset_test_submit_error");return za(await n.json())}async function wd(e){const n=await fetch(`${Re}/jobs/${encodeURIComponent(e)}`,{headers:{Accept:"application/json"},cache:"no-store"});if(!n.ok)throw await qe(n,"dataset_test_status_error");return za(await n.json())}async function kd(e){const n=await fetch(`${Re}/jobs/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Accept:"application/json"}});if(!n.ok)throw await qe(n,"dataset_test_cancel_error");return za(await n.json())}async function vd(e,n,a){const s=await fetch(`${Re}/tokenize`,{method:"POST",headers:{Accept:"application/json","Content-Type":"application/json"},body:JSON.stringify({modelName:e,text:n}),signal:a});if(!s.ok)throw await qe(s,"tokenize_error");const i=hd.safeParse(await s.json());if(!i.success)throw new je("tokenize_invalid_schema","Response tokenization failed validation.",s.status);return i.data}async function Ps(e){const n=await fetch(`${Re}/jobs/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Accept:"application/json"}});if(!n.ok)throw await qe(n,"prompt_cancel_error");return _r(await n.json())}function Gt(e){return`${Re}/jobs/${encodeURIComponent(e)}/events`}async function jd(e){const n=await fetch(`${Re}/jobs/attribution`,{method:"POST",headers:{Accept:"application/json","Content-Type":"application/json"},body:JSON.stringify(e)});if(!n.ok)throw await qe(n,"attribution_submit_error");return br(await n.json())}async function Ws(e){const n=await fetch(`${Re}/jobs/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Accept:"application/json"}});if(!n.ok)throw await qe(n,"attribution_cancel_error");return br(await n.json())}async function Id(e){const n=await fetch(`${Re}/nla/profiles`,{signal:e,headers:{Accept:"application/json"},cache:"no-store"});if(!n.ok)throw new je("nla_profiles_error",await jt(n));const a=ie(pd).safeParse(await n.json());if(!a.success)throw new je("invalid_nla_profiles",a.error.message);return a.data}async function Ad(e,n){const a=await fetch(`${Re}/nla/preflight`,{method:"POST",signal:n,headers:{Accept:"application/json","Content-Type":"application/json"},body:JSON.stringify(e)});if(!a.ok)throw new je("nla_preflight_error",await jt(a));const s=lr.safeParse(await a.json());if(!s.success)throw new je("invalid_nla_preflight",s.error.message);return s.data}async function Td(e){const n=await fetch(`${Re}/jobs/nla`,{method:"POST",headers:{Accept:"application/json","Content-Type":"application/json"},body:JSON.stringify(e)});if(!n.ok)throw await qe(n,"nla_submit_error");return xr(await n.json())}async function zs(e){const n=await fetch(`${Re}/jobs/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Accept:"application/json"}});if(!n.ok)throw await qe(n,"nla_cancel_error");return xr(await n.json())}async function Sd(e){const n=await fetch(`${Re}/jlens/options`,{signal:e,headers:{Accept:"application/json"},cache:"no-store"});if(!n.ok)throw new je("jlens_options_error",await jt(n));const a=yd.safeParse(await n.json());if(!a.success)throw new je("invalid_jlens_options",a.error.message);return a.data}async function Cd(e,n){const a=await fetch(`${Re}/jlens/preflight`,{method:"POST",signal:n,headers:{Accept:"application/json","Content-Type":"application/json"},body:JSON.stringify(e)});if(!a.ok)throw new je("jlens_preflight_error",await jt(a));const s=cr.safeParse(await a.json());if(!s.success)throw new je("invalid_jlens_preflight",s.error.message);return s.data}async function Nd(e){const n=await fetch(`${Re}/jobs/jlens`,{method:"POST",headers:{Accept:"application/json","Content-Type":"application/json"},body:JSON.stringify(e)});if(!n.ok)throw await qe(n,"jlens_submit_error");return wr(await n.json())}async function Ds(e){const n=await fetch(`${Re}/jobs/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Accept:"application/json"}});if(!n.ok)throw await qe(n,"jlens_cancel_error");return wr(await n.json())}async function Rd(e,n){const a=await fetch(`${Re}/patching/preflight`,{method:"POST",signal:n,headers:{Accept:"application/json","Content-Type":"application/json"},body:JSON.stringify(e)});if(!a.ok)throw new je("patching_preflight_error",await jt(a));const s=mr.safeParse(await a.json());if(!s.success)throw new je("invalid_patching_preflight",s.error.message);return s.data}async function Ld(e){const n=await fetch(`${Re}/jobs/patching`,{method:"POST",headers:{Accept:"application/json","Content-Type":"application/json"},body:JSON.stringify(e)});if(!n.ok)throw await qe(n,"patching_submit_error");return kr(await n.json())}async function Ys(e){const n=await fetch(`${Re}/jobs/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Accept:"application/json"}});if(!n.ok)throw await qe(n,"patching_cancel_error");return kr(await n.json())}async function gr(e,n){const a=await fetch(`${Re}/intervention/preflight`,{method:"POST",signal:n,headers:{Accept:"application/json","Content-Type":"application/json"},body:JSON.stringify(e)});if(!a.ok)throw new je("intervention_preflight_error",await jt(a));const s=pr.safeParse(await a.json());if(!s.success)throw new je("invalid_intervention_preflight",s.error.message);return s.data}async function $d(e,n){const a=new URLSearchParams({modelName:e}),s=await fetch(`${Re}/intervention/sae-profiles?${a}`,{signal:n,headers:{Accept:"application/json"},cache:"no-store"});if(!s.ok)throw new je("sae_profiles_error",await jt(s));const i=ie(fd).safeParse(await s.json());if(!i.success)throw new je("invalid_sae_profiles",i.error.message);return i.data}async function Ed(e,n,a,s){const i=new URLSearchParams({modelName:e,layer:String(n),featureIndex:String(a)}),r=await fetch(`${Re}/intervention/sae-feature-info?${i}`,{signal:s,headers:{Accept:"application/json"},cache:"no-store"});if(!r.ok)throw new je("sae_feature_info_error",await jt(r));const o=gd.safeParse(await r.json());if(!o.success)throw new je("invalid_sae_feature_info",o.error.message);return o.data}async function Md(e){const n=await fetch(`${Re}/jobs/intervention`,{method:"POST",headers:{Accept:"application/json","Content-Type":"application/json"},body:JSON.stringify(e)});if(!n.ok)throw await qe(n,"intervention_submit_error");return vr(await n.json())}async function qs(e){const n=await fetch(`${Re}/jobs/${encodeURIComponent(e)}`,{method:"DELETE",headers:{Accept:"application/json"}});if(!n.ok)throw await qe(n,"intervention_cancel_error");return vr(await n.json())}function _r(e){var a;const n=ir.safeParse(e);if(!n.success)throw new je("invalid_job",`Prompt job response failed validation: ${((a=n.error.issues[0])==null?void 0:a.message)??"unknown error"}`);return n.data}function br(e){var a;const n=or.safeParse(e);if(!n.success)throw new je("invalid_attribution_job",`Attribution job response failed validation: ${((a=n.error.issues[0])==null?void 0:a.message)??"unknown error"}`);return n.data}function xr(e){const n=dr.safeParse(e);if(!n.success)throw new je("invalid_nla_job",`NLA job response failed validation: ${n.error.message}`);return n.data}function wr(e){const n=ur.safeParse(e);if(!n.success)throw new je("invalid_jlens_job",`J-Lens job response failed validation: ${n.error.message}`);return n.data}function kr(e){const n=hr.safeParse(e);if(!n.success)throw new je("invalid_patching_job",`Patching job response failed validation: ${n.error.message}`);return n.data}function vr(e){const n=yr.safeParse(e);if(!n.success)throw new je("invalid_intervention_job",`Intervention job response failed validation: ${n.error.message}`);return n.data}function za(e){var a;const n=md.safeParse(e);if(!n.success)throw new je("invalid_dataset_test_job",`Dataset test job failed validation: ${((a=n.error.issues[0])==null?void 0:a.message)??"unknown error"}`);return n.data}async function jt(e){var n;try{const a=await e.json();if(typeof a.detail=="string")return a.detail;if((n=a.detail)!=null&&n.message)return a.detail.message}catch{}return`Explorer API returned HTTP ${e.status}.`}async function qe(e,n){let a=`Explorer API returned HTTP ${e.status}.`,s;try{const i=await e.json();typeof i.detail=="string"?a=i.detail:i.detail&&(typeof i.detail.message=="string"&&(a=i.detail.message),typeof i.detail.code=="string"&&(s=i.detail.code))}catch{}return new je(n,a,e.status,s)}function nt(e,n,a){if(e instanceof je){const s=zd(e);return Ot({kind:s,phase:n,message:e.message,code:e.code,serverCode:e.serverCode,httpStatus:e.httpStatus})}return e instanceof TypeError?Ot({kind:"network",phase:n,message:e.message||a,code:`${n}_transport_error`}):Ot({kind:n==="execution"?"computation":"request",phase:n,message:e instanceof Error?e.message:a,code:`${n}_error`})}function at(e,n){return Ot({kind:"protocol",phase:"stream",message:e,code:n})}function Xt(e){return Ot({kind:"network",phase:"stream",message:e,code:"progress_stream_disconnected"})}function Zt(e,n){return Ot({kind:"computation",phase:"execution",message:n,code:`${e}_execution_error`})}function Pd(e){switch(e){case"network":return"Network";case"request":return"Request";case"compatibility":return"Compatibility";case"authorization":return"Authorization";case"protocol":return"Protocol";case"computation":return"Computation"}}function Wd(e){switch(e.kind){case"network":return"Check the local API connection, then retry. The source Run is unchanged.";case"request":return"Review the current inputs and retry. No result was added to the Run Library.";case"compatibility":return"Choose a compatible model, layer, component, or token context before retrying.";case"authorization":return"Confirm the required local model access or credentials, then run preflight again.";case"protocol":return"Retry once. If the response remains invalid, copy diagnostics and check API compatibility.";case"computation":return"The worker stopped without replacing the source Run. Copy diagnostics before retrying."}}function zd(e){var a;const n=((a=e.serverCode)==null?void 0:a.toLowerCase())??"";return e.httpStatus===401||e.httpStatus===403||/(authorization|gated|credential|token_required|access_required)/.test(n)?"authorization":e.httpStatus===409||/(incompatible|preflight|model_not_allowed|layer_unavailable|component_unsupported)/.test(n)?"compatibility":e.code.startsWith("invalid_")?"protocol":"request"}function Ot(e){return{...e,title:Dd(e.kind,e.phase),occurredAt:new Date().toISOString()}}function Dd(e,n){if(n==="cancellation")return"Cancellation request failed";switch(e){case"network":return"Workspace connection interrupted";case"request":return"Job request rejected";case"compatibility":return"Job inputs are incompatible";case"authorization":return"Job authorization required";case"protocol":return"Job response is invalid";case"computation":return"Job computation failed"}}function Yd({failure:e,job:n,jobLabel:a}){const[s,i]=m.useState("idle");m.useEffect(()=>i("idle"),[e]);async function r(){const o={schemaVersion:"1.0",kind:"safelens-job-error",category:e.kind,phase:e.phase,code:e.code,serverCode:e.serverCode??null,httpStatus:e.httpStatus??null,message:e.message,job:n?{id:n.id,kind:n.kind,status:n.status,stage:n.stage,progress:n.progress,createdAt:n.createdAt,updatedAt:n.updatedAt}:null,context:a,url:window.location.href,userAgent:navigator.userAgent,occurredAt:e.occurredAt,copiedAt:new Date().toISOString()};try{await navigator.clipboard.writeText(JSON.stringify(o,null,2)),i("copied")}catch{i("failed")}}return t.jsxs("details",{className:`job-failure-details ${e.kind}`,children:[t.jsxs("summary",{children:[t.jsx(Et,{size:14,"aria-hidden":"true"}),t.jsx("span",{children:"Failure diagnostics"}),t.jsx("b",{children:Pd(e.kind)})]}),t.jsx("p",{children:Wd(e)}),t.jsxs("dl",{children:[t.jsxs("div",{children:[t.jsx("dt",{children:"Phase"}),t.jsx("dd",{children:e.phase})]}),t.jsxs("div",{children:[t.jsx("dt",{children:"Code"}),t.jsx("dd",{children:t.jsx("code",{children:e.serverCode??e.code})})]}),e.httpStatus!==void 0&&t.jsxs("div",{children:[t.jsx("dt",{children:"HTTP"}),t.jsx("dd",{children:e.httpStatus})]}),n&&t.jsxs("div",{children:[t.jsx("dt",{children:"Job"}),t.jsx("dd",{children:t.jsx("code",{children:n.id})})]})]}),t.jsxs("div",{className:"job-failure-actions",children:[t.jsxs("button",{type:"button",onClick:()=>void r(),children:[s==="copied"?t.jsx(Lt,{size:14}):t.jsx(Mo,{size:14}),s==="copied"?"Diagnostics copied":"Copy diagnostics"]}),t.jsx("span",{className:s==="failed"?"failed":"","aria-live":"polite",children:s==="failed"?"Copy failed":"Source Run unchanged"})]})]})}function jr(e){var b;const[n,a]=m.useState({job:null,error:null}),s=m.useRef(null),i=m.useRef(null),r=m.useRef(0),o=m.useRef(new Set),l=m.useCallback(()=>{var g;(g=s.current)==null||g.close(),s.current=null},[]),c=m.useCallback((g,y)=>{var u;((u=i.current)==null?void 0:u.id)!==g.id||i.current.generation!==y||(a({job:g,error:g.status==="error"?Zt(g.kind,g.error??g.detail):null}),g.status==="ready"&&g.result&&!o.current.has(g.id)?(o.current.add(g.id),l(),e(g.result,g)):(g.status==="error"||g.status==="cancelled")&&l())},[l,e]),d=m.useCallback(async g=>{var u,k;l();const y=++r.current;i.current={id:"submitting",generation:y},a({job:null,error:null});try{const j=await _d(g);if(((u=i.current)==null?void 0:u.generation)!==y)return;i.current={id:j.id,generation:y},a({job:j,error:null});const T=new EventSource(Gt(j.id));s.current=T,T.addEventListener("job",A=>{if(!(A instanceof MessageEvent))return;let C;try{C=JSON.parse(A.data)}catch{l(),a(I=>({...I,error:at("Prompt progress stream returned invalid JSON.","prompt_stream_invalid_json")}));return}const w=ir.safeParse(C);if(!w.success){l(),a(I=>({...I,error:at("Prompt progress payload failed validation.","prompt_stream_invalid_schema")}));return}c(w.data,y)}),T.onerror=()=>{var A;((A=i.current)==null?void 0:A.generation)===y&&(l(),a(C=>{var w,I;return{...C,error:((w=C.job)==null?void 0:w.status)==="ready"||((I=C.job)==null?void 0:I.status)==="cancelled"?C.error:C.error??Xt("Prompt progress stream disconnected. Retry the job.")}}))}}catch(j){if(((k=i.current)==null?void 0:k.generation)!==y)return;i.current=null,a({job:null,error:nt(j,"submission","Prompt job submission failed.")})}},[c,l]),h=m.useCallback(async()=>{const g=i.current;if(!(!g||g.id==="submitting"))try{const y=await Ps(g.id);c(y,g.generation)}catch(y){a(u=>({...u,error:nt(y,"cancellation","Prompt job cancellation failed.")}))}},[c]),f=m.useCallback(()=>{l(),r.current+=1,i.current=null,a({job:null,error:null})},[l]);return m.useEffect(()=>()=>{const g=i.current;l(),g&&g.id!=="submitting"&&Ps(g.id).catch(()=>{})},[l]),{...n,submit:d,cancel:h,reset:f,submitting:((b=i.current)==null?void 0:b.id)==="submitting"}}function Hs({run:e,onRunReady:n}){var j,T,A,C,w,I;const[a,s]=m.useState(e.prompt),[i,r]=m.useState("plain"),[o,l]=m.useState(0),[c,d]=m.useState(128),[h,f]=m.useState(0),b=jr(n),g=b.submitting||((j=b.job)==null?void 0:j.status)==="idle"||((T=b.job)==null?void 0:T.status)==="loading",y=qd(b.job,b.error,b.submitting),u=m.useMemo(()=>Fd(e),[e]);function k(){const L=a.trim();!L||g||b.submit({prompt:L,template:i,model:e.modelName,seed:o,maxNewTokens:c,temperature:h,messages:[]})}return t.jsxs("section",{className:"panel-section prompt-runner-panel",children:[t.jsxs("div",{className:"section-heading",children:[t.jsx(Po,{size:16}),t.jsx("span",{children:"Prompt runner"}),g&&t.jsxs("b",{children:[((A=b.job)==null?void 0:A.progress)??0,"%"]})]}),t.jsxs("label",{className:"prompt-runner-prompt",children:[t.jsx("span",{children:"Prompt"}),t.jsx("textarea",{"aria-label":"Prompt runner text","aria-describedby":a.trim()?void 0:"prompt-runner-required","aria-invalid":!a.trim()||void 0,value:a,maxLength:8e3,onChange:L=>s(L.target.value),disabled:g}),!a.trim()&&t.jsx("span",{id:"prompt-runner-required",className:"field-error",role:"alert",children:"Prompt text is required."})]}),t.jsxs("div",{className:"prompt-runner-grid",children:[t.jsxs("label",{children:[t.jsx("span",{children:"Template"}),t.jsxs("select",{"aria-label":"Prompt template",value:i,disabled:g,onChange:L=>r(L.target.value),children:[t.jsx("option",{value:"plain",children:"Plain"}),t.jsx("option",{value:"chat",children:"User / Assistant"})]})]}),t.jsxs("label",{children:[t.jsx("span",{children:"Seed"}),t.jsx("input",{"aria-label":"Generation seed",type:"number",min:0,max:2147483647,value:o,disabled:g,onChange:L=>l(aa(L.target.value,0,2147483647))})]}),t.jsxs("label",{children:[t.jsx("span",{children:"New tokens"}),t.jsx("input",{"aria-label":"Maximum new tokens",type:"number",min:1,max:512,value:c,disabled:g,onChange:L=>d(aa(L.target.value,1,512))})]}),t.jsxs("label",{children:[t.jsx("span",{children:"Temperature"}),t.jsx("input",{"aria-label":"Generation temperature",type:"number",min:0,max:2,step:.1,value:h,disabled:g,onChange:L=>f(aa(L.target.value,0,2))})]})]}),t.jsxs("div",{className:"prompt-runner-model",children:[t.jsx(vt,{size:13}),t.jsx("span",{children:"Local model"}),t.jsx("strong",{children:e.modelName})]}),t.jsxs("div",{className:"prompt-runner-actions",children:[g?t.jsxs("button",{className:"prompt-cancel-button",onClick:()=>void b.cancel(),children:[t.jsx(Bt,{size:13})," Cancel"]}):t.jsxs("button",{className:"prompt-run-button",onClick:k,disabled:!a.trim(),children:[b.error?t.jsx(fn,{size:13}):t.jsx(Un,{size:13}),b.error?"Retry analysis":"Run analysis"]}),(b.error||((C=b.job)==null?void 0:C.status)==="cancelled")&&t.jsx("button",{className:"prompt-reset-button","aria-label":"Reset prompt job",onClick:b.reset,children:t.jsx(qn,{size:13})})]}),(b.job||b.submitting||b.error)&&t.jsxs(t.Fragment,{children:[t.jsx(Hi,{status:y,label:Hd(b.job,b.error,b.submitting),detail:((w=b.error)==null?void 0:w.message)??((I=b.job)==null?void 0:I.detail)??"Submitting the prompt job.",ariaLabel:"Prompt job status",onCancel:g?()=>void b.cancel():void 0,cancelLabel:"Cancel prompt job"}),t.jsx(Ul,{job:b.job,status:y,submitting:b.submitting,ariaLabel:"Prompt job progress",tone:"prompt"}),b.error&&t.jsx(Yd,{failure:b.error,job:b.job,jobLabel:"Prompt job"})]}),u&&t.jsxs("details",{className:"prompt-run-provenance",children:[t.jsx("summary",{children:"Current generated run"}),t.jsxs("dl",{children:[t.jsxs("div",{children:[t.jsx("dt",{children:"Model"}),t.jsx("dd",{children:u.model})]}),t.jsxs("div",{children:[t.jsx("dt",{children:"Seed"}),t.jsx("dd",{children:u.seed})]}),t.jsxs("div",{children:[t.jsx("dt",{children:"Template"}),t.jsx("dd",{children:u.template})]}),t.jsxs("div",{children:[t.jsx("dt",{children:"Sampling"}),t.jsx("dd",{children:u.temperature>0?`T=${u.temperature}`:"greedy"})]})]})]})]})}function qd(e,n,a){return n?"error":a?"loading":(e==null?void 0:e.status)??"idle"}function Hd(e,n,a){return n?n.title:a?"Submitting prompt job":e?e.status==="idle"?"Prompt job queued":e.status==="loading"?"Prompt job running":e.status==="ready"?"Prompt run ready":e.status==="cancelled"?"Prompt job cancelled":"Prompt job failed":"Prompt runner idle"}function aa(e,n,a){const s=Number(e);return Number.isFinite(s)?Math.max(n,Math.min(a,s)):n}function Fd(e){var s;const n=(s=e.metadata)==null?void 0:s.promptRunner;if(!n||typeof n!="object"||Array.isArray(n))return null;const a=n;return typeof a.model!="string"||typeof a.seed!="number"?null:{model:a.model,seed:a.seed,template:typeof a.template=="string"?a.template:"plain",temperature:typeof a.temperature=="number"?a.temperature:0}}const Fs=180,Us=60;function Ud({run:e,selectedToken:n,selectedLayer:a,selectedRange:s,setSelectedToken:i,setSelectedRange:r,hoveredToken:o,setHoveredToken:l,pulseToken:c,pinToken:d,pinned:h,timeline:f,onTimelineChange:b}){const[g,y]=m.useState(()=>window.matchMedia("(max-width: 760px)").matches?Us:Fs),{mode:u,metric:k,query:j}=f,T=m.useRef(null),A=m.useMemo(()=>Kd(e.tokens,u),[u,e.tokens]),C=m.useMemo(()=>Od(e,a,k),[k,e,a]),w=Math.max(0,A.findIndex(K=>K.tokens.some(N=>N.index===n))),I=A.length<=g?0:ba(w-Math.floor(g/2),0,A.length-g),L=A.slice(I,I+g),M=j.trim().toLowerCase(),q=m.useMemo(()=>M.length===0?[]:A.filter(K=>Bs(K,M)),[A,M]),X=q.findIndex(K=>K.tokens.some(N=>N.index===n)),H=[{id:"risk",label:"Safety proxy"},{id:"attribution",label:"Attribution"},{id:"residual",label:"Residual norm"},{id:"nla",label:"NLA fidelity"},...e.tokens.some(K=>K.probeScore!==void 0)?[{id:"probe",label:"Probe score"}]:[]],V=m.useMemo(()=>Bd(e,h),[h,e]),oe=new Set(A.flatMap(K=>Os(K,V))),de=Qd(L);m.useEffect(()=>{const K=window.requestAnimationFrame(()=>{ft("timeline-ready",{tokens:e.tokens.length,items:A.length,renderedItems:L.length,mode:u})});return()=>window.cancelAnimationFrame(K)},[A.length,u,e.tokens.length,L.length]),m.useEffect(()=>{const K=window.matchMedia("(max-width: 760px)"),N=()=>y(K.matches?Us:Fs);return K.addEventListener("change",N),()=>K.removeEventListener("change",N)},[]);function P(K,N){var ne;const v=K.tokens.some(W=>W.index===n)?n:(ne=K.tokens[0])==null?void 0:ne.index;v!==void 0&&(i(v),window.requestAnimationFrame(()=>{var W,ee;(ee=(W=T.current)==null?void 0:W.querySelector(`[data-timeline-start="${K.start}"]`))==null||ee.focus(),N==null||N()}))}function S(K){if(q.length===0)return;const v=((X>=0?X:K>0?-1:0)+K+q.length)%q.length,ne=performance.now(),W=q[v];P(W,()=>{ft("timeline-search-jump",{durationMs:performance.now()-ne,token:W.start,tokens:e.tokens.length})})}function Z(K,N){const v=A.findIndex(W=>W.key===K.key),ne=A[ba(v+N,0,A.length-1)];ne&&P(ne)}return t.jsxs("section",{ref:T,className:"token-timeline-shell","aria-label":"Token timeline",children:[t.jsxs("div",{className:`token-timeline-toolbar${M?" has-query":""}`,children:[t.jsxs("label",{className:"timeline-search",children:[t.jsxs("span",{children:[t.jsx($t,{size:12})," Search",M&&t.jsxs("em",{className:"timeline-search-match-count",children:[q.length," ",q.length===1?"match":"matches"]})]}),t.jsxs("div",{children:[t.jsx("input",{id:"token-timeline-search",value:j,placeholder:"text, position, or token id","aria-label":"Search tokens",onChange:K=>b({...f,query:K.target.value})}),j&&t.jsx("button",{"aria-label":"Clear token search",onClick:()=>b({...f,query:""}),children:t.jsx(Je,{size:13})})]})]}),t.jsxs("div",{className:"toolbar-segment","aria-label":"Timeline granularity",children:[t.jsx("button",{className:u==="token"?"active":"",onClick:()=>b({...f,mode:"token"}),children:"Token"}),t.jsxs("button",{className:u==="word"?"active":"",onClick:()=>b({...f,mode:"word"}),children:[t.jsx(Wo,{size:13})," Word"]})]}),t.jsxs("label",{className:"timeline-metric",children:[t.jsx("span",{children:"Color"}),t.jsx("select",{"aria-label":"Token color metric",value:k,onChange:K=>b({...f,metric:K.target.value}),children:H.map(K=>t.jsx("option",{value:K.id,children:K.label},K.id))})]}),t.jsxs("div",{className:"timeline-search-status","aria-label":"Token search results",children:[t.jsx("span",{children:M?`${q.length} matches`:`${A.length} ${u}s`}),t.jsx("button",{"aria-label":"Previous token search result",disabled:!q.length,onClick:()=>S(-1),children:t.jsx(Vt,{size:14})}),t.jsx("button",{"aria-label":"Next token search result",disabled:!q.length,onClick:()=>S(1),children:t.jsx(dt,{size:14})})]})]}),oe.size>0&&t.jsx("div",{className:"timeline-marker-legend","aria-label":"Token evidence markers",children:Ir.filter(K=>oe.has(K)).map(K=>t.jsxs("span",{children:[t.jsx("i",{className:`token-marker marker-${K}`,"data-marker":K,"data-shape":Vs(K),"aria-hidden":"true"}),Ar(K)]},K))}),A.length>g&&t.jsxs("div",{className:"timeline-window-status","aria-label":"Timeline render window",children:[t.jsx("button",{"aria-label":"Previous token window",disabled:I===0,onClick:()=>P(A[Math.max(0,I-g)]),children:t.jsx(Vt,{size:14})}),t.jsxs("span",{children:[I+1,"–",I+L.length," / ",A.length]}),t.jsx("button",{"aria-label":"Next token window",disabled:I+L.length>=A.length,onClick:()=>P(A[Math.min(A.length-1,I+g)]),children:t.jsx(dt,{size:14})})]}),t.jsx("div",{className:"timeline-groups",children:de.map(K=>t.jsxs("section",{className:`timeline-source-group source-${K.source}`,children:[t.jsxs("header",{children:[t.jsxs("div",{className:"timeline-source-identity",children:[t.jsx("span",{className:"timeline-source-icon","aria-hidden":"true",children:K.source==="prompt"?t.jsx(Ca,{size:14}):t.jsx(zo,{size:14})}),t.jsxs("div",{children:[t.jsx("strong",{children:K.source==="prompt"?"User prompt":"Assistant reply"}),t.jsx("span",{children:K.source==="prompt"?"Input context":"Generated continuation"})]})]}),t.jsx(Jd,{tokens:e.tokens,source:K.source})]}),t.jsx("div",{className:"token-timeline","aria-label":`${K.source} tokens`,children:K.items.map(N=>{const v=N.tokens.find(E=>E.index===n)??N.tokens[0],ne=Vd(N,C),W=Os(N,V),ee=N.tokens.some(E=>E.index===n),D=N.tokens.some(E=>E.index===o),$=N.tokens.some(E=>E.index===c),F=s!==void 0&&N.end>=s[0]&&N.start<=s[1],O=M.length>0&&Bs(N,M);return t.jsxs("button",{"data-timeline-start":N.start,className:["token-pill",`metric-${k}`,ee?"selected":"",D?"hovered":"",$?"pulse":"",F?"in-range":"",O?"search-match":"",W.includes("pinned")?"pinned":"",N.isSpecial?"special":"",ne.value===void 0?"metric-unavailable":""].join(" "),"aria-label":Xd(N,ne.value,k,W),"aria-keyshortcuts":"ArrowLeft ArrowRight Space Control+Enter Meta+Enter","aria-current":ee?"true":void 0,tabIndex:ee?0:-1,style:{"--signal":ne.signal},onClick:E=>{if(E.metaKey||E.ctrlKey){d(v.index);return}if(E.shiftKey){r(tc(n,N.end));return}i(v.index)},onDoubleClick:()=>d(v.index),onKeyDown:E=>{if(E.key===" "){E.preventDefault(),E.stopPropagation(),d(v.index);return}E.key!=="ArrowLeft"&&E.key!=="ArrowRight"||(E.preventDefault(),E.stopPropagation(),Z(N,E.key==="ArrowLeft"?-1:1))},onMouseEnter:()=>{const E=performance.now();l(v.index),window.requestAnimationFrame(()=>{ft("timeline-hover",{durationMs:performance.now()-E,token:v.index,tokens:e.tokens.length})})},onMouseLeave:()=>l(null),onFocus:()=>l(v.index),onBlur:()=>l(null),children:[t.jsxs("span",{className:"token-pill-content",children:[t.jsx("b",{children:N.text||"␠"}),u==="word"&&N.tokens.length>1&&t.jsxs("em",{children:[N.tokens.length," tokens"]})]}),(N.isSpecial||N.generationStart!==void 0)&&t.jsxs("span",{className:"token-role-badges","aria-hidden":"true",children:[N.isSpecial&&t.jsx("span",{className:"token-role-badge special-badge",title:"Special token",children:"Special"}),N.generationStart!==void 0&&t.jsx("span",{className:"token-role-badge generation-badge",title:Tr(N),children:Gd(N)})]}),t.jsx("i",{className:"token-value",children:ne.value===void 0?"n/a":Sr(ne.value,k)}),W.length>0&&t.jsx("small",{className:"token-marker-row","aria-hidden":"true",children:W.map(E=>t.jsx("i",{className:`token-marker marker-${E}`,"data-marker":E,"data-shape":Vs(E)},E))})]},N.key)})})]},K.source))})]})}function Kd(e,n){const a=new Map;if(e.filter(i=>i.source==="reply").forEach((i,r)=>{a.set(i.index,i.generationStep??r)}),n==="token")return e.map(i=>Ks([i],a));const s=[];for(const i of e){const r=s[s.length-1],o=/^\s/.test(i.text),l=(r==null?void 0:r.some(c=>c.isSpecial))??!1;!r||r[0].source!==i.source||i.isSpecial||l||o?s.push([i]):r.push(i)}return s.map(i=>Ks(i,a))}function Ks(e,n){const a=e[0],s=e[e.length-1]??a,i=e.map(o=>o.text).join("").trim(),r=e.flatMap(o=>{const l=n.get(o.index);return l===void 0?[]:[l]});return{key:`${a.source}:${a.index}-${s.index}`,tokens:e,text:i,normalizedText:i.toLowerCase(),source:a.source,start:a.index,end:s.index,generationStart:r[0],generationEnd:r[r.length-1],isSpecial:e.some(o=>o.isSpecial)}}function Od(e,n,a){const s=new Map,i=a==="residual"?new Map(e.residualCells.filter(d=>d.layer===n).map(d=>[d.tokenIndex,d.norm])):void 0,r=new Map;if(a==="nla")for(const d of e.nla){if(d.layer!==n||d.status==="unavailable")continue;const h=r.get(d.tokenIndex);(h===void 0||d.cosine>h)&&r.set(d.tokenIndex,d.cosine)}for(const d of e.tokens)a==="risk"&&s.set(d.index,d.risk),a==="attribution"&&s.set(d.index,d.attribution),a==="probe"&&s.set(d.index,d.probeScore),a==="residual"&&s.set(d.index,i==null?void 0:i.get(d.index)),a==="nla"&&s.set(d.index,r.get(d.index));const o=[...s.values()].filter(d=>d!==void 0),l=o.length?Math.min(...o):0,c=o.length?Math.max(...o):1;return new Map(e.tokens.map(d=>{const h=s.get(d.index),f=h===void 0?0:a==="risk"||a==="attribution"||a==="nla"?ba(h,0,1):ec(h,l,c);return[d.index,{value:h,signal:f}]}))}function Vd(e,n){return e.tokens.reduce((a,s)=>{const i=n.get(s.index)??{value:void 0,signal:0};return i.signal>a.signal?i:a},n.get(e.tokens[0].index)??{value:void 0,signal:0})}function Bd(e,n){return{nla:new Set(e.nla.filter(a=>a.status==="available").map(a=>a.tokenIndex)),pinned:new Set(n)}}function Os(e,n){const a=new Set;for(const s of e.tokens)s.risk>=.7&&a.add("risk"),Math.abs(s.attribution)>=.7&&a.add("attribution"),s.probeScore!==void 0&&a.add("probe"),s.monitorHit&&a.add("monitor"),n.pinned.has(s.index)&&a.add("pinned"),n.nla.has(s.index)&&a.add("nla");return Ir.filter(s=>a.has(s))}const Ir=["risk","attribution","nla","probe","monitor","pinned"];function Ar(e){return e==="risk"?"Safety proxy":e==="attribution"?"Attribution":e==="nla"?"NLA evidence":e==="probe"?"Probe":e==="monitor"?"Monitor":"Pinned"}function Vs(e){return e==="risk"?"triangle":e==="attribution"?"diamond":e==="nla"?"ring":e==="probe"?"pentagon":e==="monitor"?"cross":"square"}function Qd(e){return["prompt","reply"].map(a=>({source:a,items:e.filter(s=>s.source===a)})).filter(a=>a.items.length>0)}function Jd({tokens:e,source:n}){const a=e.filter(c=>c.source===n),s=a[0],i=a[a.length-1],r=a.flatMap((c,d)=>n==="reply"?[c.generationStep??d]:[]),o=s&&i?s.index===i.index?`T${s.index}`:`T${s.index}–T${i.index}`:"No tokens",l=r.length>0?r[0]===r[r.length-1]?`G${r[0]}`:`G${r[0]}–G${r[r.length-1]}`:void 0;return t.jsxs("div",{className:"timeline-source-summary","aria-label":`${n==="prompt"?"Prompt":"Reply"} sequence summary`,children:[t.jsx("span",{children:o}),l&&t.jsx("span",{children:l}),t.jsxs("span",{children:[a.length," ",a.length===1?"token":"tokens"]})]})}function Gd(e){return e.generationStart===void 0?"":e.generationEnd===void 0||e.generationEnd===e.generationStart?`G${e.generationStart}`:`G${e.generationStart}–${e.generationEnd}`}function Tr(e){return e.generationStart===void 0?"":e.generationEnd===void 0||e.generationEnd===e.generationStart?`Generation step ${e.generationStart}`:`Generation steps ${e.generationStart} to ${e.generationEnd}`}function Bs(e,n){const a=n.match(/^(?:token(?:-|:|#|\s)?|#)(\d+)$/),s=n.match(/^id(?::|#|\s)?(\d+)$/);return e.normalizedText.includes(n)||e.tokens.some(i=>String(i.index)===n||String(i.tokenId)===n||a!==null&&i.index===Number(a[1])||s!==null&&i.tokenId===Number(s[1]))}function Xd(e,n,a,s){const i=e.start===e.end?`token ${e.start}`:`tokens ${e.start} to ${e.end}`,r=n===void 0?"unavailable":Sr(n,a),l=[e.source==="prompt"?"user prompt":"assistant reply",e.isSpecial?"special token":void 0,e.generationStart!==void 0?Tr(e).toLowerCase():void 0,s.length>0?`evidence markers: ${s.map(Ar).join(", ")}`:void 0].filter(c=>c!==void 0).join(", ");return`${e.text||"blank"}, ${i}, ${l}, ${Zd(a)} ${r}`}function Zd(e){return e==="risk"?"safety proxy":e==="attribution"?"attribution":e==="residual"?"residual norm":e==="nla"?"NLA fidelity":"probe score"}function Sr(e,n){return Pe(e,n==="risk"?"tokenRisk":n==="residual"?"residual_norm":n==="nla"?"nla_cosine":n,"compact")}function ec(e,n,a){return Math.abs(a-n)<1e-12?0:(e-n)/(a-n)}function tc(e,n){return e<=n?[e,n]:[n,e]}function ba(e,n,a){return Math.max(n,Math.min(a,e))}function Qs({evidence:e,canPrevious:n,canNext:a,canPin:s,pinned:i,nextActions:r,onPrevious:o,onNext:l,onPin:c,onCompare:d,onExport:h,onNextAction:f,detailLevel:b="full"}){const[g,y]=m.useState(null),u=m.useId(),k=e.status==="loading"||e.status==="cancelled",j=b==="full";async function T(A){const C=A==="cache"?e.cacheKey:JSON.stringify(e.reproduction,null,2);await navigator.clipboard.writeText(C),y(A),window.setTimeout(()=>y(w=>w===A?null:w),1e3)}return t.jsxs("section",{className:"inspector evidence-inspector","aria-label":"Evidence inspector",children:[t.jsxs("header",{className:"inspector-title",children:[t.jsxs("div",{className:"inspector-heading",children:[t.jsx(ac,{status:e.status}),t.jsxs("div",{children:[t.jsx("h2",{children:e.title}),t.jsx("p",{children:e.subtitle})]})]}),t.jsxs("div",{className:"inspector-nav",children:[t.jsx("button",{"aria-label":"Previous token",title:"Previous token",disabled:!n,onClick:o,children:t.jsx(Vt,{size:15})}),t.jsx("button",{"aria-label":"Next token",title:"Next token",disabled:!a,onClick:l,children:t.jsx(dt,{size:15})})]})]}),t.jsxs("section",{className:"inspector-section inspector-summary-section","aria-labelledby":`${u}-summary`,children:[t.jsxs("div",{className:"inspector-section-heading",children:[t.jsx("h3",{id:`${u}-summary`,children:"Summary"}),t.jsx("span",{className:`evidence-status status-${e.status}`,children:sc(e.status)})]}),t.jsxs("div",{className:"inspector-primary-value",children:[t.jsx("span",{children:e.primaryLabel}),t.jsx("strong",{children:e.primaryValue}),t.jsx("em",{children:e.evidenceClass.replace("_"," ")})]}),t.jsx("p",{className:"inspector-status-reason",children:e.statusReason}),t.jsxs("div",{className:"inspector-value-grid",children:[t.jsxs("span",{children:[t.jsx("b",{children:e.rawValue}),"raw / stored"]}),t.jsxs("span",{children:[t.jsx("b",{children:e.displayValue}),"displayed"]}),t.jsxs("span",{children:[t.jsx("b",{children:e.units}),"units"]})]})]}),j&&t.jsxs("section",{className:"inspector-section","aria-labelledby":`${u}-evidence`,children:[t.jsxs("div",{className:"inspector-section-heading",children:[t.jsx("h3",{id:`${u}-evidence`,children:"Evidence"}),t.jsx("span",{children:e.shape})]}),t.jsxs("dl",{className:"inspector-provenance-list",children:[t.jsxs("div",{children:[t.jsx("dt",{children:"Method"}),t.jsx("dd",{children:e.method})]}),t.jsxs("div",{children:[t.jsx("dt",{children:"Normalization"}),t.jsx("dd",{children:e.normalization})]}),t.jsxs("div",{className:"inspector-cache-row",children:[t.jsx("dt",{children:"Cache key"}),t.jsxs("dd",{className:"inspector-cache-value",children:[t.jsx("span",{children:e.cacheKey}),t.jsx("button",{"aria-label":"Copy inspector cache key",disabled:k||!e.cacheKey,onClick:()=>void T("cache"),children:g==="cache"?t.jsx(Lt,{size:13}):t.jsx(Ln,{size:13})})]})]}),t.jsxs("div",{children:[t.jsx("dt",{children:"Source artifact"}),t.jsx("dd",{children:e.sourceArtifact})]}),t.jsxs("div",{children:[t.jsx("dt",{children:"Run / sample"}),t.jsxs("dd",{children:[e.runId," / ",e.sampleId]})]}),t.jsxs("div",{children:[t.jsx("dt",{children:"Model"}),t.jsx("dd",{children:e.modelName})]})]}),e.warnings.length>0&&t.jsx("div",{className:"inspector-warning-list","aria-label":"Evidence warnings",children:e.warnings.map(A=>t.jsxs("p",{children:[t.jsx(lt,{size:13}),A]},A))})]}),t.jsxs("section",{className:"inspector-section inspector-actions-section","aria-labelledby":`${u}-actions`,children:[t.jsx("div",{className:"inspector-section-heading",children:t.jsx("h3",{id:`${u}-actions`,children:"Actions"})}),t.jsxs("div",{className:"inspector-actions",children:[t.jsxs("button",{className:i?"active":"",disabled:!s,"aria-label":i?"Unpin inspector evidence":"Pin inspector evidence",onClick:c,children:[t.jsx(Hn,{size:14}),i?"Unpin":"Pin"]}),t.jsxs("button",{disabled:k,onClick:d,children:[t.jsx(ot,{size:14}),"Compare"]}),t.jsxs("button",{disabled:k,"aria-label":"Copy reproducible evidence context",onClick:()=>void T("reproduction"),children:[g==="reproduction"?t.jsx(Lt,{size:14}):t.jsx(Do,{size:14}),"Context"]}),t.jsxs("button",{disabled:k,onClick:h,children:[t.jsx(Na,{size:14}),"Export"]})]}),j&&r.length>0&&t.jsxs("div",{className:"inspector-next-actions","aria-label":"Recommended next analysis",children:[t.jsxs("div",{children:[t.jsx("strong",{children:"Recommended next analysis"}),t.jsx("span",{children:e.status==="available"?"Strengthen or challenge this evidence.":"Resolve the current evidence gap."})]}),r.map(A=>t.jsxs("button",{type:"button",className:`next-action-${A.kind}`,onClick:()=>f(A.id),children:[t.jsx(nc,{kind:A.kind}),t.jsxs("span",{children:[t.jsx("b",{children:A.label}),A.description]}),t.jsx(dt,{size:14})]},A.id))]})]})]})}function nc({kind:e}){return e==="attribution"?t.jsx(Ve,{size:15}):e==="nla"?t.jsx(tt,{size:15}):e==="patching"?t.jsx(kt,{size:15}):e==="intervention"?t.jsx(vt,{size:15}):t.jsx(Ra,{size:15})}function ac({status:e}){return e==="loading"||e==="cancelled"?t.jsx($i,{size:18}):e==="available"?t.jsx(Xe,{size:18}):t.jsx(lt,{size:18})}function sc(e){return e==="available"?"available":e==="not-computed"?"not computed":e==="loading"?"loading":e}const Cr=m.createContext(0),ic=12e3;function it(e,n){const a=new Map;function s(){const o=ic;return new Promise((l,c)=>{const d=window.setTimeout(()=>{c(new Error(`Lazy module ${String(n)} timed out after ${o}ms`))},o);e().then(h=>{window.clearTimeout(d),l(h)},h=>{window.clearTimeout(d),c(h)})})}function i(o){const l=a.get(o);if(l)return l;const c=Ce.lazy(()=>s().then(d=>({default:d[n]})));return a.set(o,c),c}function r(o){const l=m.useContext(Cr),c=i(l);return Ce.createElement(c,o)}return r.displayName="RetryableLazyComponent",r}class Js extends Ce.Component{constructor(){super(...arguments);qt(this,"state",{error:null,retry:0,componentStack:"",copyStatus:"idle",errorResetKey:null});qt(this,"fallbackRef",Ce.createRef());qt(this,"retryView",()=>{this.setState(a=>({error:null,retry:a.retry+1,componentStack:"",copyStatus:"idle",errorResetKey:null}))});qt(this,"copyDiagnostics",async()=>{const a=this.state.error;if(!a)return;const s={schemaVersion:"1.0",kind:this.props.variant==="dialog"?"safelens-dialog-render-error":"safelens-view-render-error",view:this.props.viewLabel,context:this.props.resetKey,error:{name:a.name,message:a.message},componentStack:this.state.componentStack.trim(),location:window.location.href,userAgent:navigator.userAgent,capturedAt:new Date().toISOString()};try{await navigator.clipboard.writeText(JSON.stringify(s,null,2)),this.setState({copyStatus:"copied"})}catch{this.setState({copyStatus:"failed"})}});qt(this,"handleDialogKeyDown",a=>{var l,c;if(a.key==="Escape"){a.preventDefault(),(c=(l=this.props).onDismiss)==null||c.call(l);return}if(a.key!=="Tab")return;const s=this.fallbackRef.current;if(!s)return;const i=Array.from(s.querySelectorAll("button:not(:disabled), summary, [href], [tabindex]:not([tabindex='-1'])"));if(i.length===0)return;const r=i[0],o=i[i.length-1];a.shiftKey&&(document.activeElement===r||document.activeElement===s)?(a.preventDefault(),o.focus()):!a.shiftKey&&document.activeElement===o&&(a.preventDefault(),r.focus())})}static getDerivedStateFromError(a){return{error:a}}componentDidCatch(a,s){this.setState({componentStack:s.componentStack??"",errorResetKey:this.props.resetKey}),window.requestAnimationFrame(()=>{var i;return(i=this.fallbackRef.current)==null?void 0:i.focus()})}componentDidUpdate(){this.state.error&&this.state.errorResetKey!==null&&this.state.errorResetKey!==this.props.resetKey&&this.setState({error:null,retry:0,componentStack:"",copyStatus:"idle",errorResetKey:null})}render(){return this.state.error?this.props.variant==="dialog"?t.jsx("div",{className:"compare-backdrop",onMouseDown:a=>{var s,i;a.target===a.currentTarget&&((i=(s=this.props).onDismiss)==null||i.call(s))},children:t.jsxs("aside",{ref:this.fallbackRef,className:"compare-drawer compare-error-drawer",role:"dialog","aria-modal":"true","aria-label":`${this.props.viewLabel} error`,tabIndex:-1,onKeyDown:this.handleDialogKeyDown,children:[t.jsxs("header",{className:"compare-error-heading",children:[t.jsx(lt,{size:20}),t.jsxs("div",{children:[t.jsxs("strong",{children:[this.props.viewLabel," could not be opened"]}),t.jsx("span",{children:"The workspace and pinned evidence are unchanged."})]}),t.jsx("button",{"aria-label":`Close ${this.props.viewLabel.toLowerCase()} error`,onClick:this.props.onDismiss,children:t.jsx(Je,{size:18})})]}),t.jsxs("details",{className:"compare-error-detail",children:[t.jsx("summary",{children:"Technical detail"}),t.jsxs("code",{children:[this.state.error.name,": ",this.state.error.message]}),t.jsx("small",{children:this.props.resetKey})]}),t.jsxs("div",{className:"compare-error-actions",children:[t.jsxs("button",{onClick:this.retryView,children:[t.jsx(fn,{size:14})," Retry comparison"]}),t.jsxs("button",{onClick:this.props.onDismiss,children:[t.jsx(Je,{size:14})," Close"]}),t.jsxs("button",{"aria-live":"polite",onClick:()=>void this.copyDiagnostics(),children:[this.state.copyStatus==="copied"?t.jsx(Lt,{size:14}):t.jsx(Ln,{size:14}),this.state.copyStatus==="copied"?"Copied":this.state.copyStatus==="failed"?"Copy failed":"Copy diagnostics"]})]})]})}):t.jsxs("section",{ref:this.fallbackRef,className:"view-error-state",role:"alert","aria-label":`${this.props.viewLabel} view error`,tabIndex:-1,children:[t.jsx(lt,{size:20}),t.jsxs("div",{children:[t.jsxs("strong",{children:[this.props.viewLabel," could not be rendered"]}),t.jsx("span",{children:"Your run, token selection, Timeline, pins, and Inspector are unchanged."}),t.jsxs("details",{children:[t.jsx("summary",{children:"Technical detail"}),t.jsxs("code",{children:[this.state.error.name,": ",this.state.error.message]}),t.jsx("small",{children:this.props.resetKey})]})]}),t.jsxs("div",{className:"view-error-actions",children:[t.jsxs("button",{onClick:this.retryView,children:[t.jsx(fn,{size:14})," Retry view"]}),t.jsxs("button",{onClick:this.props.onOpenOverview,disabled:!this.props.onOpenOverview,children:[t.jsx(Ra,{size:14})," Open Overview"]}),t.jsxs("button",{"aria-live":"polite",onClick:()=>void this.copyDiagnostics(),children:[this.state.copyStatus==="copied"?t.jsx(Lt,{size:14}):t.jsx(Ln,{size:14}),this.state.copyStatus==="copied"?"Copied":this.state.copyStatus==="failed"?"Copy failed":"Copy diagnostics"]})]})]}):t.jsx(Cr.Provider,{value:this.state.retry,children:t.jsx(Ce.Fragment,{children:this.props.children},this.state.retry)})}}function rc({run:e,selectedToken:n,selectedLayer:a,residualCell:s,onNavigate:i}){var y;const r=e.tokens.find(u=>u.index===n)??e.tokens[0],o=[...e.tokens].sort((u,k)=>k.risk-u.risk||u.index-k.index).findIndex(u=>u.index===r.index)+1,l=oc(e,r.index,a,s),c=l.filter(u=>u.direction==="supporting"),d=l.filter(u=>u.direction==="contradicting"),h=(y=e.patching)==null?void 0:y.cells.find(u=>u.layer===a&&u.tokenIndex===r.index),f=e.attributionMethods.find(u=>u.available),b=["The safety-direction score is run-relative and is not a calibrated probability of unsafe behavior.",h?"The causal patch result is local to one corruption, component, layer, and token.":"No exact causal patch result is available for this token and layer.",f?`${f.label} is available, but target and baseline choices still bound its interpretation.`:"No target-specific attribution method has been computed for this run."],g=[{view:"residual",label:"Inspect residual trajectory",detail:"Check whether direction alignment persists across layers."},{view:"attribution",label:f?"Inspect signed attribution":"Run target attribution",detail:f?`Open ${f.label} at this token.`:"Compute a target-specific method and baseline."},{view:"patching",label:h?"Inspect causal recovery":"Run causal patching",detail:h?"Review the exact patched score and recovery percentage.":"Test whether replacing this activation changes the target metric."}];return t.jsxs("section",{className:"surface overview-evidence-map","aria-labelledby":"overview-evidence-map-title",children:[t.jsxs("div",{className:"surface-header overview-evidence-heading",children:[t.jsxs("div",{children:[t.jsx("h3",{id:"overview-evidence-map-title",children:"Evidence map"}),t.jsxs("p",{children:[Xs(r.text)," · token ",r.index," · layer ",a]})]}),t.jsxs("span",{className:"overview-confidence",children:[t.jsx(Rt,{size:13})," exploratory"]})]}),t.jsxs("div",{className:"overview-graph","aria-label":"Evidence graph",children:[t.jsx(Gs,{id:"overview-supporting-title",label:"Supporting evidence",tone:"supporting",nodes:c,empty:"No loaded measure currently supports this proxy direction.",onNavigate:i}),t.jsxs("article",{className:"overview-primary-finding","aria-labelledby":"overview-primary-title",children:[t.jsx("span",{children:"Primary finding"}),t.jsxs("h4",{id:"overview-primary-title",children:["Token ",r.index," ranks ",o," of ",e.tokens.length," by run-relative safety-direction proxy."]}),t.jsxs("p",{children:["Score ",r.risk.toFixed(3)," is exploratory derived evidence. It locates a candidate for analysis; it does not establish unsafe behavior or causality."]}),t.jsxs("dl",{children:[t.jsxs("div",{children:[t.jsx("dt",{children:"Evidence class"}),t.jsx("dd",{children:"derived proxy"})]}),t.jsxs("div",{children:[t.jsx("dt",{children:"Confidence"}),t.jsx("dd",{children:"exploratory"})]}),t.jsxs("div",{children:[t.jsx("dt",{children:"Token"}),t.jsxs("dd",{children:[Xs(r.text)," · id ",r.tokenId]})]})]})]}),t.jsx(Gs,{id:"overview-contradicting-title",label:"Contradicting evidence",tone:"contradicting",nodes:d,empty:"No contradictory measure is loaded; absence is not confirmation.",onNavigate:i})]}),t.jsxs("div",{className:"overview-followup-grid",children:[t.jsxs("section",{className:"overview-limitations","aria-labelledby":"overview-limitations-title",children:[t.jsxs("header",{children:[t.jsx(Et,{size:16}),t.jsx("h4",{id:"overview-limitations-title",children:"Limitations"})]}),t.jsx("ul",{children:b.map(u=>t.jsx("li",{children:u},u))})]}),t.jsxs("section",{className:"overview-recommendations","aria-labelledby":"overview-recommendations-title",children:[t.jsxs("header",{children:[t.jsx(bn,{size:16}),t.jsx("h4",{id:"overview-recommendations-title",children:"Recommended analysis"})]}),t.jsx("div",{children:g.map(u=>t.jsxs("button",{onClick:()=>i(u.view),children:[t.jsxs("span",{children:[t.jsx("strong",{children:u.label}),t.jsx("small",{children:u.detail})]}),u.view==="patching"?t.jsx(kt,{size:15}):t.jsx(Kn,{size:15})]},u.view))})]})]})]})}function Gs({id:e,label:n,tone:a,nodes:s,empty:i,onNavigate:r}){return t.jsxs("section",{className:`overview-evidence-column ${a}`,"aria-labelledby":e,children:[t.jsxs("header",{children:[t.jsx(Yo,{size:14}),t.jsx("h4",{id:e,children:n}),t.jsx("span",{children:s.length})]}),t.jsx("div",{children:s.length>0?s.map(o=>t.jsxs("button",{className:"overview-evidence-node",onClick:()=>r(o.view),children:[t.jsx("span",{children:lc(o.evidenceClass)}),t.jsx("strong",{children:o.label}),t.jsx("b",{children:o.value}),t.jsx("small",{children:o.detail})]},o.id)):t.jsx("div",{className:"overview-evidence-empty",role:"status",children:i})})]})}function oc(e,n,a,s){var l,c;const i=e.tokens.find(d=>d.index===n)??e.tokens[0],r=[];s&&r.push({id:"residual-direction",label:"Residual direction",value:s.riskDirection.toFixed(3),detail:`Normalized resid_post alignment at L${a}; grouped against the 0.5 midpoint.`,evidenceClass:"derived_proxy",view:"residual",direction:s.riskDirection>=.5?"supporting":"contradicting"}),r.push({id:"token-attribution",label:"Attention proxy",value:i.attribution.toFixed(3),detail:"Run-relative descriptive signal grouped against the 0.5 midpoint; not causal attribution.",evidenceClass:"derived_proxy",view:"attribution",direction:i.attribution>=.5?"supporting":"contradicting"});const o=(l=e.patching)==null?void 0:l.cells.find(d=>d.layer===a&&d.tokenIndex===n);return o&&r.push({id:"causal-patching",label:"Activation patch effect",value:dc(o.causalEffect),detail:`Exact ${(c=e.patching)==null?void 0:c.component} replacement; direction follows the causal-effect sign.`,evidenceClass:"causal",view:"patching",direction:o.causalEffect>0?"supporting":"contradicting"}),r}function lc(e){return e==="derived_proxy"?"derived proxy":e==="safety_method"?"safety output":e==="causal"?"causal evidence":"raw"}function dc(e){return`${e>0?"+":""}${e.toFixed(3)}`}function Xs(e){return e.trim()?e:"space"}function cc({open:e,returnFocusRef:n,context:a,pinnedCount:s,onClose:i,onOverview:r,onRuns:o,onTokenSearch:l,onCompare:c,onExportSession:d,onExportArtifact:h,onExportEvidence:f}){const b=m.useRef(null),g=m.useRef(null),y=m.useRef(!0);if(Mn({open:e,dialogRef:b,initialFocusRef:g,returnFocusRef:n,restoreFocusRef:y,onClose:i}),!e)return null;return t.jsx("div",{className:"quick-actions-backdrop",onMouseDown:k=>{k.target===k.currentTarget&&i()},children:t.jsxs("aside",{ref:b,className:"quick-actions-dialog",role:"dialog",tabIndex:-1,"aria-modal":"true","aria-labelledby":"quick-actions-title",children:[t.jsxs("header",{children:[t.jsxs("div",{children:[t.jsx("span",{children:"Global workspace"}),t.jsx("h2",{id:"quick-actions-title",children:"Quick actions"})]}),t.jsx("button",{ref:g,"aria-label":"Close quick actions",onClick:i,children:t.jsx(Je,{size:18})})]}),t.jsxs("div",{className:"quick-actions-context","aria-label":"Current quick action context",children:[t.jsxs("span",{children:[t.jsx("b",{children:a.runId}),t.jsx("small",{children:"run"})]}),t.jsxs("span",{children:[t.jsx("b",{children:a.sampleId}),t.jsx("small",{children:"sample"})]}),t.jsxs("span",{children:[t.jsx("b",{children:a.view}),t.jsx("small",{children:"view"})]}),t.jsxs("span",{children:[t.jsxs("b",{children:["L",a.layer]}),t.jsx("small",{children:"layer"})]}),t.jsxs("span",{children:[t.jsx("b",{children:a.tokenText||`T${a.token}`}),t.jsxs("small",{children:["token ",a.token]})]})]}),t.jsxs("div",{className:"quick-actions-list","aria-label":"Available quick actions",children:[t.jsx(St,{icon:t.jsx(Ra,{size:17}),label:"Open Overview",detail:"Evidence map",onClick:u(r)}),t.jsx(St,{icon:t.jsx($t,{size:17}),label:"Find a token",detail:"Timeline search",onClick:u(l)}),t.jsx(St,{icon:t.jsx(yt,{size:17}),label:"Runs and samples",detail:"Run Library",onClick:u(o)}),t.jsx(St,{icon:t.jsx(ot,{size:17}),label:"Compare pinned evidence",detail:s?`${s} item${s===1?"":"s"} ready`:"Pin evidence first",disabled:!s,onClick:u(c)}),t.jsx(St,{icon:t.jsx(Mi,{size:17}),label:"Export analysis session",detail:"Session JSON",onClick:u(d)}),t.jsx(St,{icon:t.jsx(Sa,{size:17}),label:"Export Explorer artifact",detail:"Run JSON",onClick:u(h)}),t.jsx(St,{icon:t.jsx(Na,{size:17}),label:"Export current evidence",detail:"Evidence JSON",onClick:u(f)})]})]})});function u(k){return()=>{y.current=!1,k()}}}function St({icon:e,label:n,detail:a,disabled:s,onClick:i}){return t.jsxs("button",{disabled:s,onClick:i,children:[t.jsx("i",{"aria-hidden":"true",children:e}),t.jsxs("span",{children:[t.jsx("b",{children:n}),t.jsx("small",{children:a})]})]})}function pn({icon:e,title:n,description:a,facts:s,actionLabel:i,actionIcon:r,onAction:o,className:l="",compact:c=!1}){return t.jsxs("section",{className:`analysis-empty actionable-empty ${c?"compact":""} ${l}`.trim(),"aria-label":n,children:[t.jsx("span",{className:"empty-icon","aria-hidden":"true",children:e}),t.jsx("strong",{children:n}),t.jsx("p",{children:a}),t.jsx("dl",{className:"actionable-empty-facts",children:s.map(d=>t.jsxs("div",{children:[t.jsx("dt",{children:d.label}),t.jsx("dd",{children:d.value})]},`${d.label}:${d.value}`))}),t.jsxs("button",{type:"button",className:"actionable-empty-primary",onClick:o,children:[r,t.jsx("span",{children:i}),t.jsx(dt,{size:15,"aria-hidden":"true"})]})]})}const uc=/<\|(?:im_start|im_end|endoftext|eot_id)\|>/i,mc=/(?:\r?\n|([.!?。！？])\s+)(?:User|用户)\s*:(?=[\s\S]{0,4000}(?:Assistant|助手)\s*:)/i;function Da(e){var c,d,h;const n=(c=e.metadata)==null?void 0:c.generatedContinuation;if(typeof n!="string"||!n.trim())return"";const a=(d=e.metadata)==null?void 0:d.generation,s=a&&typeof a=="object"&&!Array.isArray(a)?a:void 0,i=(s==null?void 0:s.outputFormat)==="continuation_only"||typeof(s==null?void 0:s.generatedTokenCount)=="number",r=(h=e.metadata)==null?void 0:h.promptRunner,o=r&&typeof r=="object"&&!Array.isArray(r)?r.userPrompt:void 0;let l=n.trim();if(!i){const b=[e.prompt,typeof o=="string"?o:""].filter(Boolean).sort((g,y)=>y.length-g.length).find(g=>l.startsWith(g));b&&(l=l.slice(b.length).trim())}return l=l.replace(/^(?:Assistant|助手)\s*:\s*/i,""),hc(l)}function hc(e){var i;let n=e.trim();const a=n.search(uc);a>=0&&(n=n.slice(0,a));const s=mc.exec(n);return(s==null?void 0:s.index)!==void 0&&(n=n.slice(0,s.index+(((i=s[1])==null?void 0:i.length)??0))),n.trim()}function pc({model:e,maxNewTokens:n,conversationId:a,onConversationStart:s,onRunReady:i}){const[r,o]=m.useState([]),[l,c]=m.useState(null),d=m.useRef([]);d.current=r;const h=m.useRef(a);h.current=a;const f=m.useRef(null);f.current=l;function b(C,w){return C.filter(I=>I.id!==w&&I.run&&I.status==="ready").flatMap(I=>{const L=Da(I.run);return L?[{role:"user",content:I.prompt},{role:"assistant",content:L}]:[]})}const g=m.useCallback((C,w)=>{const I=f.current;if(!I)return;const L=d.current.findIndex(X=>X.id===I),M=h.current,q={...C,metadata:{...C.metadata,...M?{conversationId:M}:{},...L>=0?{turnIndex:L}:{}}};o(X=>X.map(H=>H.id===I?{...H,run:q,status:"ready",jobId:w.id}:H)),c(null),i(q,w,I)},[i]),y=jr(g);m.useEffect(()=>{if(!y.error||!l)return;const C=y.error.message;o(w=>w.map(I=>I.id===l?{...I,status:"error",errorMessage:C}:I)),c(null)},[l,y.error]),m.useEffect(()=>{!y.job||!l||y.job.status==="cancelled"&&(o(C=>C.map(w=>w.id===l?{...w,status:"cancelled"}:w)),c(null))},[l,y.job]);const u=m.useCallback(C=>{if(f.current)return;const w=!!h.current,I=h.current??crypto.randomUUID();h.current=I,w||s(I);const L=b(r),M={id:crypto.randomUUID(),prompt:C,run:null,jobId:null,status:"pending",startedAt:new Date().toISOString()};o(q=>[...q,M]),f.current=M.id,c(M.id),y.submit({prompt:C,template:"chat",model:e,seed:0,maxNewTokens:n,temperature:0,messages:L})},[a,n,e,s,y,r]),k=m.useCallback(C=>{f.current===C&&y.cancel()},[y]),j=m.useCallback(C=>{if(f.current)return;const w=r.find(L=>L.id===C);if(!w||w.status==="pending")return;o(L=>L.map(M=>M.id===C?{...M,status:"pending",errorMessage:void 0,run:null}:M)),f.current=C,c(C);const I=r.findIndex(L=>L.id===C);y.submit({prompt:w.prompt,template:"chat",model:e,seed:0,maxNewTokens:n,temperature:0,messages:b(r.slice(0,Math.max(0,I)),C)})},[n,e,y,r]),T=m.useCallback(()=>{y.reset(),f.current=null,o([]),c(null)},[y]),A=m.useCallback((C,w)=>{y.reset(),f.current=null,o(C),c(null),s(w)},[s,y]);return{turns:r,activeTurnId:l,submit:u,cancel:k,retry:j,reset:T,hydrate:A}}const sa=512;function yc(e){const n=wl.safeParse(e.base);if(!n.success){const s=n.error.issues[0];throw new Error(`Chunk metadata core failed at ${(s==null?void 0:s.path.join("."))||"base"}: ${(s==null?void 0:s.message)||"invalid core"}.`)}if(n.data.runId!==e.runId||n.data.sampleId!==e.sampleId)throw new Error("Chunk metadata core does not match its run/sample envelope.");const a=n.data.layers[n.data.layers.length-1]??0;return{...n.data,attentionHeads:[{id:"__chunk_pending__",layer:a,head:0,role:"component data loading",riskContribution:0,entropy:0,distributionByToken:[]}],mlpNeurons:[],residualCells:[],logitLens:[],jLens:[],attentionCells:[],mlpCells:[],attributionTracks:[],attributionMethods:[{id:"__chunk_pending__",label:"Component data loading",description:"The selected attribution chunk has not loaded yet.",evidenceKind:"raw",signed:!1,normalization:"not loaded",available:!1,unavailableReason:"Component data is loading; this is not an unavailable evidence result.",rows:[]}],nla:[]}}function cn(e,n,a,s=a){const{start:i,end:r}=Pn(a),o=["attention","mlp"].includes(e)?`:L${n}`:"",l=Pn(s),c=e==="attention"?`:S${l.start}-${l.end}`:"";return`${e}${o}:T${i}-${r}${c}`}function Zs(e,n,a,s,i=s){return!e||e.mode==="full"||e.loadedScopes.includes(cn(n,a,s,i))}function fc(e,n,a,s,i=a){const r=Pn(a,s),o={tokenStart:r.start,tokenEnd:r.end};if(e==="overview")return[{component:"residualCells",...o},{component:"logitLens",...o}];if(e==="residual")return[{component:"residualCells",...o},{component:"logitLens",...o}];if(e==="attention"){const l=Pn(i,s);return[{component:"attentionHeads",layer:n,...o,sourceStart:l.start,sourceEnd:l.end},{component:"attentionCells",layer:n,...o},{component:"residualCells",...o}]}return e==="mlp"?[{component:"mlpNeurons",layer:n,...o},{component:"mlpCells",layer:n,...o},{component:"residualCells",...o}]:e==="attribution"?[{component:"attributionMethods",...o},{component:"attributionTracks",...o},{component:"residualCells",...o}]:e==="nla"?[{component:"nla",...o},{component:"residualCells",...o}]:e==="patching"?[{component:"patching",...o}]:[{component:"intervention",...o}]}async function ei(e,n,a,s,i,r,o=i){return(await Nr(e,n,a,s,i,r,o)).reduce((c,d)=>Ya(c,d),e)}async function Nr(e,n,a,s,i,r,o=i){const l=fc(a,s,i,e.tokens.length,o);return await Promise.all(l.map(d=>sr(n,d,r)))}function Ya(e,n){if(n.component==="residualCells")return{...e,residualCells:rn(e.residualCells,wc.parse(n.data))};if(n.component==="logitLens")return{...e,logitLens:rn(e.logitLens,kc.parse(n.data))};if(n.component==="jLens")return{...e,jLens:rn(e.jLens,ie(Bi).parse(n.data))};if(n.component==="attentionCells")return{...e,attentionCells:rn(e.attentionCells,ti.parse(n.data))};if(n.component==="mlpCells")return{...e,mlpCells:rn(e.mlpCells,ti.parse(n.data))};if(n.component==="nla"){const a=vc.parse(n.data),s=new Map(e.nla.map(i=>[`${i.layer}:${i.component}:${i.tokenIndex}`,i]));for(const i of a)s.set(`${i.layer}:${i.component}:${i.tokenIndex}`,i);return{...e,nla:[...s.values()]}}return n.component==="attentionHeads"?gc(e,n.data):n.component==="mlpNeurons"?_c(e,n.data):n.component==="attributionTracks"?bc(e,n.data):n.component==="attributionMethods"?xc(e,n.data):n.component==="patching"?{...e,patching:n.data}:{...e,intervention:n.data}}function gc(e,n){const a=jc.parse(n),s=new Map(e.attentionHeads.filter(i=>i.id!=="__chunk_pending__").map(i=>[i.id,i]));for(const i of a){const r=s.get(i.id),o=(r==null?void 0:r.distributionByToken.map(d=>d.slice()))??Array.from({length:e.tokens.length},()=>[]);i.distributionByToken.forEach((d,h)=>{var g;const f=i.chunk.destinationStart+h,b=((g=o[f])==null?void 0:g.slice())??[];d.forEach((y,u)=>{b[i.chunk.sourceStart+u]=y}),o[f]=b});const{chunk:l,...c}=i;s.set(i.id,{...c,distributionByToken:o})}return{...e,attentionHeads:[...s.values()]}}function _c(e,n){const a=Ic.parse(n),s=new Map(e.mlpNeurons.map(i=>[i.id,i]));for(const i of a){const r=s.get(i.id),o=(r==null?void 0:r.activationsByToken.slice())??[];i.activationsByToken.forEach((d,h)=>{o[i.chunk.tokenStart+h]=d});const{chunk:l,...c}=i;s.set(i.id,{...c,activationsByToken:o})}return{...e,mlpNeurons:[...s.values()]}}function bc(e,n){var i;const a=Ac.parse(n),s=new Map(e.attributionTracks.map(r=>[r.name,r]));for(const r of a){const o=((i=s.get(r.name))==null?void 0:i.values.slice())??[];r.values.forEach((l,c)=>{o[r.chunk.tokenStart+c]=l}),s.set(r.name,{name:r.name,values:o})}return{...e,attributionTracks:[...s.values()]}}function xc(e,n){var i;const a=Tc.parse(n),s=new Map(e.attributionMethods.filter(r=>r.id!=="__chunk_pending__").map(r=>[r.id,r]));for(const r of a){const o=s.get(r.id),l=new Map((o==null?void 0:o.rows.map(c=>[c.layer,c]))??[]);for(const c of r.rows){const d=((i=l.get(c.layer))==null?void 0:i.values.slice())??[];c.values.forEach((b,g)=>{d[c.chunk.tokenStart+g]=b});const{chunk:h,...f}=c;l.set(f.layer,{...f,values:d})}s.set(r.id,{...r,rows:[...l.values()]})}return{...e,attributionMethods:[...s.values()]}}function rn(e,n){const a=new Map(e.map(s=>[`${s.layer}:${s.tokenIndex}`,s]));for(const s of n)a.set(`${s.layer}:${s.tokenIndex}`,s);return[...a.values()]}function Pn(e,n=Number.MAX_SAFE_INTEGER){const a=Math.floor(Math.max(0,e)/sa)*sa;return{start:a,end:Math.min(n,a+sa)}}const wc=ie(Q({layer:_().int().nonnegative(),tokenIndex:_().int().nonnegative(),norm:_(),rawDirection:_(),riskDirection:_(),semanticDensity:_()})),ti=ie(Q({layer:_().int().nonnegative(),tokenIndex:_().int().nonnegative(),value:_(),rawValue:_(),metric:p(),sourceKey:p()})),kc=ie(Q({layer:_().int().nonnegative(),tokenIndex:_().int().nonnegative(),targetTokenId:_().int(),targetTokenText:p(),targetLogit:_(),targetProbability:_(),targetRank:_().int(),sourceKey:p(),topPredictions:ie(Q({tokenId:_().int(),tokenText:p(),logit:_(),probability:_()}))})),vc=ie(Q({tokenIndex:_().int().nonnegative(),layer:_().int().nonnegative(),component:ye(["resid_post","attn_result","mlp_out"]),explanation:p(),cosine:_(),mse:_(),fve:_().optional(),activationNorm:_(),status:ye(["available","unavailable"]).optional(),profile:p().nullable().optional(),source:p().optional(),token:p().optional()})),qa=Q({tokenStart:_().int(),tokenEnd:_().int()}),jc=ie(Q({id:p(),layer:_().int(),head:_().int(),role:p(),riskContribution:_(),entropy:_(),distributionByToken:ie(ie(_())),chunk:Q({destinationStart:_().int(),destinationEnd:_().int(),sourceStart:_().int(),sourceEnd:_().int()})})),Ic=ie(Q({id:p(),layer:_().int(),neuron:_().int(),label:p(),activation:_(),riskContribution:_(),topTokens:ie(_().int()),positiveTopTokens:ie(_().int()),negativeTopTokens:ie(_().int()),activationsByToken:ie(_()),maxAbsoluteActivation:_(),chunk:qa})),Ac=ie(Q({name:p(),values:ie(_()),chunk:qa})),Tc=ie(Q({id:p(),label:p(),description:p(),evidenceKind:ye(["raw","derived_proxy","safety_method","causal"]),signed:fe(),normalization:p(),available:fe(),unavailableReason:p().optional(),rows:ie(Q({layer:_().int(),label:p(),values:ie(_()),sourceKey:p(),chunk:qa}))})),Nn="safelens.localExplorer.importedRuns.v1",xa="safelens.localExplorer.runUsage.v1",wa=6,Rr=100,ka="safelensRunContextTransition";function Sc(e,n=!0){const a=m.useMemo(()=>({key:ut(e),run:e,runId:e.runId,sampleId:e.sampleId,modelName:e.modelName,tokenCount:e.tokens.length,layerCount:e.layers.length,sourceName:"bundled real model cache",importedAt:"built in",sourceType:"bundled",builtIn:!0,hydration:{mode:"full"}}),[e]),[s,i]=m.useState(zc),[r,o]=m.useState([]),[l,c]=m.useState({status:"idle",rootName:"workspace",loadedCount:0,diagnostics:[],detail:"Workspace discovery has not started."}),d=m.useRef(null),h=m.useRef(null),f=m.useRef(null),b=m.useRef(new Map),g=m.useRef(new Set),y=m.useRef(0),[u,k]=m.useState(Wc),j=ai(),T=m.useRef(j===a.key?void 0:j),A=m.useRef(0),C=m.useMemo(()=>{const $=new Map;for(const F of[a,...s,...r]){const O=$.get(F.key);if(!O){$.set(F.key,{...F,lastUsedAt:u[F.key],sourceAlternatives:[]});continue}O.sourceAlternatives=[...O.sourceAlternatives??[],Nc(F)]}return[...$.values()]},[a,s,r,u]),[w,I]=m.useState(()=>T.current??a.key),[L,M]=m.useState(null),q=C.find($=>$.key===w&&$.run!==null)??C.find($=>$.run!==null)??a,X=C.find($=>$.key===w),H=q.key!==w&&(l.status==="idle"||l.status==="loading"||(X==null?void 0:X.run)===null);m.useEffect(()=>{const $=new Date().toISOString();k(F=>{const O=Object.fromEntries(Object.entries({...F,[q.key]:$}).sort((E,Y)=>Y[1].localeCompare(E[1])).slice(0,Rr));try{window.localStorage.setItem(xa,JSON.stringify(O))}catch{}return O})},[q.key]);const V=m.useCallback(async()=>{var O,E,Y,le,R;(O=d.current)==null||O.controller.abort();const $=new AbortController,F=++A.current;d.current={controller:$,id:F},c(J=>({...J,status:"loading",failureKind:void 0,diagnostics:[],detail:"Connecting to the local workspace API..."}));try{const J=await ed($.signal);if(((E=d.current)==null?void 0:E.id)!==F)return;let U=J.summaries.map(ue=>({key:ut(ue),run:null,runId:ue.runId,sampleId:ue.sampleId,modelName:ue.modelName,tokenCount:ue.tokenCount,layerCount:ue.layerCount,sourceName:ue.sourceName,importedAt:ue.modifiedAt,sourceType:"remote",artifactId:ue.artifactId,builtIn:!1,remoteSummary:ue}));const ce=T.current,te=U.find(ue=>ue.key===ce);if(te!=null&&te.remoteSummary){const ue=await de(te.remoteSummary,$.signal,si());if(((Y=d.current)==null?void 0:Y.id)!==F)return;U=U.map(z=>z.key===te.key?{...z,...ue}:z),T.current===te.key&&(I(te.key),T.current=void 0)}o(U),c({status:U.length?"ready":"empty",rootName:J.rootName||"workspace",loadedCount:U.length,diagnostics:J.diagnostics,detail:U.length===0?"No Explorer artifacts were found. Bundled and imported runs remain available.":J.diagnostics.length?`${U.length} sample${U.length===1?"":"s"} indexed with diagnostics.`:`${U.length} workspace sample${U.length===1?"":"s"} indexed; samples load on selection.`})}catch(J){if(((le=d.current)==null?void 0:le.id)!==F)return;if($.signal.aborted){c(U=>({...U,status:"cancelled",failureKind:void 0,detail:"Workspace discovery was cancelled. Bundled and imported runs remain available."}));return}c(U=>({...U,status:"error",failureKind:$c(J),diagnostics:[J instanceof Error?J.message:"Workspace discovery failed."],detail:J instanceof TypeError?"Workspace API is offline. Bundled and imported runs remain available.":J instanceof je?J.message:"Workspace discovery failed. Bundled and imported runs remain available."}))}finally{((R=d.current)==null?void 0:R.id)===F&&(d.current=null)}},[]),oe=m.useCallback(()=>{var F,O,E;const $=!!d.current;(F=d.current)==null||F.controller.abort(),(O=h.current)==null||O.controller.abort(),(E=f.current)==null||E.controller.abort(),P(),o(Y=>Y.map(le=>{var R;return((R=le.hydration)==null?void 0:R.mode)==="partial"&&le.hydration.loadingScope?{...le,hydration:{...le.hydration,cancelledScopes:[...new Set([...le.hydration.cancelledScopes,le.hydration.loadingScope])],loadingScope:void 0}}:le})),c(Y=>({...Y,status:"cancelled",failureKind:void 0,detail:$?"Workspace discovery was cancelled. Bundled and imported runs remain available.":"Workspace loading was cancelled. Loaded ranges remain available."}))},[]);m.useEffect(()=>(V(),()=>{var F,O;const $=d.current;d.current=null,$==null||$.controller.abort(),(F=h.current)==null||F.controller.abort(),h.current=null,(O=f.current)==null||O.controller.abort(),f.current=null,P()}),[V]),m.useEffect(()=>{if(!n||H)return;const $=new URLSearchParams(window.location.search);$.set("run",q.runId),$.set("sample",q.sampleId),gn($,"replace")},[q.key,q.runId,q.sampleId,H,n]);async function de($,F,O){if($.parentRun||$.chunkProtocol!=="safelens-chunks-v1")return{run:await Ms($,F),hydration:{mode:"full"}};const E=await td($,F),Y=yc(E),le=Y.layers.includes(O.layer??-1)?O.layer:Y.layers[Y.layers.length-1]??0,R=Math.max(0,Math.min(Y.tokens.length-1,O.tokenIndex??Dc(Y)));return{run:await ei(Y,$,O.view,le,R,F,O.sourceTokenIndex??R),hydration:{mode:"partial",metadata:E,loadedScopes:[cn(O.view,le,R,O.sourceTokenIndex??R)],errors:{},cancelledScopes:[]}}}function P(){y.current+=1;for(const $ of b.current.values())$.abort();b.current.clear(),g.current.clear()}function S($,F,O,E,Y){var U;if(((U=$.hydration)==null?void 0:U.mode)!=="partial"||!$.remoteSummary||$.run.tokens.length<=512)return;const le=Math.floor(E/512)*512,R=[le-1,le+512].filter(ce=>ce>=0&&ce<$.run.tokens.length),J=y.current;for(const ce of R){const te=cn(F,O,ce,Y),ue=`${$.key}:${te}`;if($.hydration.loadedScopes.includes(te)||g.current.has(ue))continue;g.current.add(ue);const z=()=>{if(J!==y.current)return;const pe=new AbortController;b.current.set(ue,pe),Nr($.run,$.remoteSummary,F,O,ce,pe.signal,Y).then(ve=>{J===y.current&&o(ae=>ae.map(G=>{var me;return G.key!==$.key||!G.run||((me=G.hydration)==null?void 0:me.mode)!=="partial"?G:{...G,run:ve.reduce((he,be)=>Ya(he,be),G.run),hydration:{...G.hydration,loadedScopes:[...new Set([...G.hydration.loadedScopes,te])]}}}))}).catch(()=>{g.current.delete(ue)}).finally(()=>{b.current.delete(ue)})},re=window.requestIdleCallback;re?re(z,{timeout:1e3}):globalThis.setTimeout(z,0)}}function Z($,F,O,E=O){var U,ce,te;const Y=q;if(((U=Y.hydration)==null?void 0:U.mode)!=="partial"||!Y.remoteSummary)return;const le=Y.hydration;if(Zs(Y.hydration,$,F,O,E)){S(Y,$,F,O,E);return}const R=cn($,F,O,E);if(((ce=f.current)==null?void 0:ce.scope)===R)return;P(),(te=f.current)==null||te.controller.abort();const J=new AbortController;f.current={controller:J,scope:R},o(ue=>ue.map(z=>{var re;return z.key===Y.key&&((re=z.hydration)==null?void 0:re.mode)==="partial"?{...z,hydration:{...z.hydration,loadingScope:R,cancelledScopes:z.hydration.cancelledScopes.filter(pe=>pe!==R)}}:z})),c(ue=>({...ue,status:"loading",detail:`Loading ${$} range data for L${F}, token ${O}...`})),ei(Y.run,Y.remoteSummary,$,F,O,J.signal,E).then(ue=>{var z;((z=f.current)==null?void 0:z.scope)===R&&(o(re=>re.map(pe=>{var ve;return pe.key!==Y.key||((ve=pe.hydration)==null?void 0:ve.mode)!=="partial"?pe:{...pe,run:ue,hydration:{...pe.hydration,loadedScopes:[...new Set([...pe.hydration.loadedScopes,R])],loadingScope:void 0,errors:ii(pe.hydration.errors,R),cancelledScopes:pe.hydration.cancelledScopes.filter(ae=>ae!==R)}}})),S({...Y,run:ue,hydration:{...le,loadedScopes:[...new Set([...le.loadedScopes,R])],errors:ii(le.errors,R),cancelledScopes:le.cancelledScopes.filter(re=>re!==R)}},$,F,O,E),c(re=>({...re,status:"ready",detail:`${re.loadedCount} workspace sample${re.loadedCount===1?"":"s"} indexed; selected range loaded.`})))}).catch(ue=>{var z;((z=f.current)==null?void 0:z.scope)!==R||J.signal.aborted||(o(re=>re.map(pe=>{var ve;return pe.key===Y.key&&((ve=pe.hydration)==null?void 0:ve.mode)==="partial"?{...pe,hydration:{...pe.hydration,loadingScope:void 0,errors:{...pe.hydration.errors,[R]:ue instanceof Error?ue.message:"View data loading failed."},cancelledScopes:pe.hydration.cancelledScopes.filter(ae=>ae!==R)}}:pe})),c(re=>({...re,status:"error",diagnostics:[ue instanceof Error?ue.message:"View data loading failed."],detail:`${$} range loading failed. Other loaded ranges remain available.`})))}).finally(()=>{var ue;((ue=f.current)==null?void 0:ue.scope)===R&&(f.current=null)})}function K($,F,O,E=O){const Y=q.hydration,le=cn($,F,O,E);return{partial:(Y==null?void 0:Y.mode)==="partial",ready:Zs(Y,$,F,O,E),loading:(Y==null?void 0:Y.mode)==="partial"&&Y.loadingScope===le,error:(Y==null?void 0:Y.mode)==="partial"?Y.errors[le]:void 0,cancelled:(Y==null?void 0:Y.mode)==="partial"&&Y.cancelledScopes.includes(le)}}async function N(){var E,Y,le,R;const $=q;if(((E=$.hydration)==null?void 0:E.mode)!=="partial"||!$.remoteSummary)return $.run;P(),(Y=f.current)==null||Y.controller.abort();const F=new AbortController,O="full-run";f.current={controller:F,scope:O},c(J=>({...J,status:"loading",detail:`Loading the complete ${$.runId} artifact for export or experiments...`}));try{const J=await Ms($.remoteSummary,F.signal);return((le=f.current)==null?void 0:le.scope)!==O?$.run:(o(U=>U.map(ce=>ce.key===$.key?{...ce,run:J,hydration:{mode:"full"}}:ce)),c(U=>({...U,status:"ready",detail:`${U.loadedCount} workspace sample${U.loadedCount===1?"":"s"} indexed; active sample fully loaded.`})),J)}catch(J){throw F.signal.aborted||c(U=>({...U,status:"error",diagnostics:[J instanceof Error?J.message:"Full Run loading failed."],detail:"The complete artifact could not be loaded. Range visualization remains available."})),J}finally{((R=f.current)==null?void 0:R.scope)===O&&(f.current=null)}}function v($,F,O="push"){var R,J;const E=C.find(U=>U.key===$);if(!E)return;if(T.current=void 0,P(),(R=h.current)==null||R.controller.abort(),h.current=null,(J=f.current)==null||J.controller.abort(),f.current=null,E.run){O!=="none"&&An(E,F,O),I($),M(null);return}if(!E.remoteSummary)return;const Y=new AbortController;h.current={controller:Y,key:$},I($),M(null),c(U=>({...U,status:"loading",detail:`Loading ${E.runId} / ${E.sampleId} on demand...`}));const le=F?{view:F.view,layer:F.layer,tokenIndex:F.tokenIndex,sourceTokenIndex:F.sourceTokenIndex}:O==="none"?si():{view:"overview"};de(E.remoteSummary,Y.signal,le).then(U=>{var ce;((ce=h.current)==null?void 0:ce.key)===$&&(O!=="none"&&An(E,F,O),o(te=>te.map(ue=>ue.key===$?{...ue,...U}:ue)),c(te=>({...te,status:"ready",detail:`${te.loadedCount} workspace sample${te.loadedCount===1?"":"s"} indexed; selected sample loaded.`})))}).catch(U=>{var ce;if(((ce=h.current)==null?void 0:ce.key)===$){if(I(q.key),Y.signal.aborted){c(te=>({...te,status:"cancelled",detail:"Workspace sample loading was cancelled. The current analysis remains available."}));return}c(te=>({...te,status:"error",diagnostics:[U instanceof Error?U.message:"Workspace sample loading failed."],detail:"The selected sample could not be loaded. The current analysis remains available."}))}}).finally(()=>{var U;((U=h.current)==null?void 0:U.key)===$&&(h.current=null)})}function ne($,F,O){const E=new Date().toISOString(),Y=$.map(U=>({key:ut(U),run:U,runId:U.runId,sampleId:U.sampleId,modelName:U.modelName,tokenCount:U.tokens.length,layerCount:U.layers.length,sourceName:F,importedAt:E,sourceType:"local",builtIn:!1,hydration:{mode:"full"}})),le=new Set(Y.map(U=>U.key)),R=[...Y,...s.filter(U=>!le.has(U.key))].slice(0,wa);try{window.localStorage.setItem(Nn,JSON.stringify(R))}catch(U){return M({tone:"error",title:"Artifact validated but could not be persisted",details:[U instanceof Error?U.message:"Local storage quota was exceeded."]}),!1}T.current=void 0,i(R);const J=Y[0];return J.key!==w&&(An(J,void 0,"push"),I(J.key)),M({tone:"success",title:`${$.length} sample${$.length===1?"":"s"} loaded`,details:[`${F} · schema ${O}`]}),!0}function W($,F,O,E){const Y=(E==null?void 0:E.kind)??(O==null?void 0:O.kind)??"prompt";T.current=void 0;const le=(E==null?void 0:E.conversationId)!==void 0||(E==null?void 0:E.turnIndex)!==void 0?{...$,metadata:{...$.metadata,...E.conversationId!==void 0?{conversationId:E.conversationId}:{},...E.turnIndex!==void 0?{turnIndex:E.turnIndex}:{}}}:$,R={key:ut(le),run:le,runId:le.runId,sampleId:le.sampleId,modelName:le.modelName,tokenCount:le.tokens.length,layerCount:le.layers.length,sourceName:`${Y} job ${F.slice(0,8)}`,importedAt:new Date().toISOString(),sourceType:"generated",artifactId:F,builtIn:!1,hydration:{mode:"full"}},J=[R,...s.filter(U=>U.key!==R.key)].slice(0,wa);try{window.localStorage.setItem(Nn,JSON.stringify(J))}catch(U){M({tone:"error",title:"Generated run is ready but could not be persisted",details:[U instanceof Error?U.message:"Local storage quota was exceeded."]})}i(J),(E==null?void 0:E.updateLocation)!==!1&&Cc(R,O,"push"),I(R.key),M({tone:"success",title:`${Y==="nla"?"NLA":Y==="jlens"?"J-Lens":Y==="attribution"?"Attribution":Y==="patching"?"Activation patching":Y==="intervention"?"Intervention comparison":"Prompt analysis"} added to the Run Library`,details:[`${$.runId} / ${$.sampleId} · job ${F.slice(0,8)}`]})}function ee($){D([$])}function D($){const F=new Set($);if(F.size===0)return;T.current=void 0;const O=s.filter(E=>!F.has(E.key));try{window.localStorage.setItem(Nn,JSON.stringify(O))}catch{}i(O),k(E=>{if(![...F].some(le=>le in E))return E;const Y={...E};for(const le of F)delete Y[le];try{window.localStorage.setItem(xa,JSON.stringify(Y))}catch{}return Y}),F.has(w)&&(An(a,void 0,"replace"),I(a.key))}return m.useEffect(()=>{function $(){const F=ai()??a.key;F!==w&&v(F,void 0,"none")}return window.addEventListener("popstate",$),()=>window.removeEventListener("popstate",$)},[w,a.key,C]),{records:C,activeRecord:q,message:L,setMessage:M,selectRun:v,addRuns:ne,addGeneratedRun:W,removeRun:ee,removeRuns:D,remoteState:l,refreshRemote:V,cancelRemote:oe,ensureViewHydrated:Z,viewHydration:K,loadFullActiveRun:N}}function Cc(e,n,a){const s=new URLSearchParams(window.location.search);if(Lr(s),s.set("run",e.runId),s.set("sample",e.sampleId),!n){gn(s,a,{key:e.key,kind:"fresh"});return}s.set("view",n.view),n.trackName&&s.set("track",n.trackName),n.tokenIndex!==void 0&&s.set("token",String(n.tokenIndex)),n.layer!==void 0&&s.set("layer",String(n.layer)),s.set("metric",n.metric),s.set("normalization",n.view==="intervention"?"raw":"normalized"),gn(s,a,{key:e.key,kind:"restored"})}function Nc(e){return{sourceType:e.sourceType,sourceName:e.sourceName,importedAt:e.importedAt,artifactId:e.artifactId,modelName:e.modelName,tokenCount:e.tokenCount,layerCount:e.layerCount,loaded:e.run!==null}}function An(e,n,a){const s=new URLSearchParams(window.location.search);if(Lr(s),s.set("run",e.runId),s.set("sample",e.sampleId),!n){gn(s,a,{key:e.key,kind:"fresh"});return}s.set("view",n.view),s.set("token",String(n.tokenIndex)),s.set("layer",String(n.layer)),s.set("metric",n.metric),s.set("normalization",n.normalization),n.headId&&s.set("head",n.headId),n.neuronId&&s.set("neuron",n.neuronId),n.trackName&&s.set("track",n.trackName),n.view==="nla"&&Lc(n.component)&&s.set("nlaComponent",n.component),n.sourceTokenIndex!==void 0&&(s.set("source",String(n.sourceTokenIndex)),s.set("target",String(n.tokenIndex)),s.set("edge","incoming")),gn(s,a,{key:e.key,kind:"restored"})}function Lr(e){for(const n of["view","token","source","target","range","layer","head","neuron","track","metric","normalization","edge","nlaComponent","mode"])e.delete(n)}function gn(e,n,a){const s=`${window.location.pathname}?${e.toString()}${window.location.hash}`,i=`${window.location.pathname}${window.location.search}${window.location.hash}`;if(s===i)return;const r=a?{...window.history.state??{},[ka]:a}:window.history.state;n==="push"?window.history.pushState(r,"",s):window.history.replaceState(r,"",s)}function Rc(e){const n=window.history.state,a=n==null?void 0:n[ka];if(!a||typeof a!="object")return;const s=a;if(s.key!==e||s.kind!=="fresh"&&s.kind!=="restored")return;const i={...n??{}};return delete i[ka],window.history.replaceState(i,"",window.location.href),s.kind}function Lc(e){return e==="resid_post"||e==="attn_result"||e==="mlp_out"}function $c(e){return e instanceof TypeError?"offline":e instanceof je?e.code.startsWith("invalid_")?"validation":"api":"unknown"}function ut(e){return`${e.runId}::${e.sampleId}`}function Ec(e){const n=new Map(e.map(s=>[s.key,s])),a=new Map;for(const s of e){if(!Er(s,n))continue;const i=$r(s,n),r=a.get(i);r?r.push(s):a.set(i,[s])}return[...a.entries()].map(([s,i])=>{const r=i.slice().sort((d,h)=>ni(d,h,n)),o=new Map;for(const d of r){const h=Wn(d,n),f=o.get(h);(!f||Mc(d,f))&&o.set(h,d)}const l=[...o.values()].sort((d,h)=>ni(d,h,n)),c=i.map(d=>d.lastUsedAt??d.importedAt).sort((d,h)=>h.localeCompare(d))[0];return{conversationId:s,title:Pc(l[0]),lastUsedAt:c,turnCount:l.length,firstRecord:l[0],records:r,turnRecords:l}}).sort((s,i)=>i.lastUsedAt.localeCompare(s.lastUsedAt))}function $r(e,n,a=new Set){var r,o,l;const s=((o=(r=e.run)==null?void 0:r.metadata)==null?void 0:o.conversationId)??((l=e.remoteSummary)==null?void 0:l.conversationId);if(typeof s=="string")return s;if(a.has(e.key))return`legacy:${e.key}`;a.add(e.key);const i=Ha(e,n);return i?$r(i,n,a):`legacy:${e.key}`}function Wn(e,n,a=new Set){var r,o,l;const s=((o=(r=e.run)==null?void 0:r.metadata)==null?void 0:o.turnIndex)??((l=e.remoteSummary)==null?void 0:l.turnIndex);if(typeof s=="number"&&Number.isInteger(s))return s;if(a.has(e.key))return 0;a.add(e.key);const i=Ha(e,n);return i?Wn(i,n,a):0}function ni(e,n,a){const s=Wn(e,a)-Wn(n,a);return s!==0?s:e.importedAt.localeCompare(n.importedAt)}function Er(e,n,a=new Set){if(e.builtIn||e.sourceType==="remote"&&/(^|\/)generated\/prompt-[^/]+\.explorer\.json$/i.test(e.sourceName)||e.sourceName.startsWith("prompt job "))return!0;if(a.has(e.key))return!1;a.add(e.key);const s=Ha(e,n);return s?Er(s,n,a):!1}function Ha(e,n){var i,r,o;const a=((r=(i=e.run)==null?void 0:i.metadata)==null?void 0:r.parentRun)??((o=e.remoteSummary)==null?void 0:o.parentRun);if(!a||typeof a!="object"||Array.isArray(a))return;const s=a;if(!(typeof s.runId!="string"||typeof s.sampleId!="string"))return n.get(`${s.runId}::${s.sampleId}`)}function Mc(e,n){var i,r,o,l,c,d;const a=!!(((r=(i=e.run)==null?void 0:i.metadata)==null?void 0:r.parentRun)??((o=e.remoteSummary)==null?void 0:o.parentRun)),s=!!(((c=(l=n.run)==null?void 0:l.metadata)==null?void 0:c.parentRun)??((d=n.remoteSummary)==null?void 0:d.parentRun));return a!==s?a:e.importedAt.localeCompare(n.importedAt)>=0}function Pc(e){var i,r,o,l,c;const n=(r=(i=e.run)==null?void 0:i.metadata)==null?void 0:r.promptRunner,a=n&&typeof n=="object"?n.userPrompt:void 0,s=(c=typeof a=="string"?a:((o=e.run)==null?void 0:o.prompt)??((l=e.remoteSummary)==null?void 0:l.promptPreview))==null?void 0:c.trim().replace(/\s+/g," ");return s?s.length>46?`${s.slice(0,45).trimEnd()}...`:s:e.runId}function ai(){const e=new URLSearchParams(window.location.search),n=e.get("run"),a=e.get("sample");return n&&a?`${n}::${a}`:void 0}function Wc(){try{const e=JSON.parse(window.localStorage.getItem(xa)??"{}");return!e||typeof e!="object"||Array.isArray(e)?{}:Object.fromEntries(Object.entries(e).filter(n=>typeof n[0]=="string"&&typeof n[1]=="string"&&Number.isFinite(Date.parse(n[1]))).sort((n,a)=>a[1].localeCompare(n[1])).slice(0,Rr))}catch{return{}}}function zc(){try{const e=JSON.parse(window.localStorage.getItem(Nn)??"[]");return Array.isArray(e)?e.flatMap(n=>{if(!n||typeof n!="object")return[];const a=ht.safeParse(n.run);if(!a.success)return[];const s=a.data;return[{key:ut(s),run:s,runId:s.runId,sampleId:s.sampleId,modelName:s.modelName,tokenCount:s.tokens.length,layerCount:s.layers.length,sourceName:typeof n.sourceName=="string"?n.sourceName:"local artifact",importedAt:typeof n.importedAt=="string"?n.importedAt:"unknown",sourceType:n.sourceType==="generated"?"generated":"local",artifactId:typeof n.artifactId=="string"?n.artifactId:void 0,builtIn:!1,hydration:{mode:"full"}}]}).slice(0,wa):[]}catch{return[]}}function si(){const e=new URLSearchParams(window.location.search),n=e.get("view"),a=["overview","residual","attention","mlp","nla","patching","intervention","attribution"],s=e.has("layer")?Number(e.get("layer")):Number.NaN,i=e.has("token")?Number(e.get("token")):Number.NaN,r=e.has("source")?Number(e.get("source")):Number.NaN;return{view:a.includes(n)?n:"overview",layer:Number.isInteger(s)?s:void 0,tokenIndex:Number.isInteger(i)?i:void 0,sourceTokenIndex:Number.isInteger(r)?r:void 0}}function Dc(e){var n;return e.tokens.reduce((a,s)=>s.risk>e.tokens[a].risk?s.index:a,((n=e.tokens[0])==null?void 0:n.index)??0)}function ii(e,n){return Object.fromEntries(Object.entries(e).filter(([a])=>a!==n))}function Yc(e){var y;const[n,a]=m.useState(null),[s,i]=m.useState(null),r=m.useRef(null),o=m.useRef(null),l=m.useRef(0),c=m.useRef(new Set),d=m.useCallback(()=>{var u;(u=r.current)==null||u.close(),r.current=null},[]),h=m.useCallback((u,k)=>{var j;((j=o.current)==null?void 0:j.id)!==u.id||o.current.generation!==k||(a(u),i(u.status==="error"?Zt(u.kind,u.error??u.detail):null),u.status==="ready"&&u.result&&!c.current.has(u.id)?(c.current.add(u.id),d(),e(u.result,u)):(u.status==="error"||u.status==="cancelled")&&d())},[d,e]),f=m.useCallback(async u=>{var j,T;d();const k=++l.current;o.current={id:"submitting",generation:k},a(null),i(null);try{const A=await jd(u);if(((j=o.current)==null?void 0:j.generation)!==k)return;o.current={id:A.id,generation:k},a(A);const C=new EventSource(Gt(A.id));r.current=C,C.addEventListener("job",w=>{if(!(w instanceof MessageEvent))return;let I;try{I=JSON.parse(w.data)}catch{d(),i(at("Attribution progress stream returned invalid JSON.","attribution_stream_invalid_json"));return}const L=or.safeParse(I);if(!L.success){d(),i(at("Attribution progress payload failed validation.","attribution_stream_invalid_schema"));return}h(L.data,k)}),C.onerror=()=>{var w;((w=o.current)==null?void 0:w.generation)===k&&(d(),i(I=>I??Xt("Attribution progress stream disconnected. Retry the job.")))}}catch(A){if(((T=o.current)==null?void 0:T.generation)!==k)return;o.current=null,i(nt(A,"submission","Attribution job submission failed."))}},[h,d]),b=m.useCallback(async()=>{const u=o.current;if(!(!u||u.id==="submitting"))try{h(await Ws(u.id),u.generation)}catch(k){i(nt(k,"cancellation","Attribution cancellation failed."))}},[h]),g=m.useCallback(()=>{d(),l.current+=1,o.current=null,a(null),i(null)},[d]);return m.useEffect(()=>()=>{const u=o.current;d(),u&&u.id!=="submitting"&&Ws(u.id).catch(()=>{})},[d]),{job:n,error:s,submit:f,cancel:b,reset:g,submitting:((y=o.current)==null?void 0:y.id)==="submitting"}}function Mr(e){var y;const[n,a]=m.useState(null),[s,i]=m.useState(null),r=m.useRef(null),o=m.useRef(null),l=m.useRef(0),c=m.useRef(new Set),d=m.useCallback(()=>{var u;(u=r.current)==null||u.close(),r.current=null},[]),h=m.useCallback((u,k)=>{var j;((j=o.current)==null?void 0:j.id)!==u.id||o.current.generation!==k||(a(u),i(u.status==="error"?Zt(u.kind,u.error??u.detail):null),u.status==="ready"&&u.result&&!c.current.has(u.id)?(c.current.add(u.id),d(),e(u.result,u)):(u.status==="error"||u.status==="cancelled")&&d())},[d,e]),f=m.useCallback(async u=>{var j,T;d();const k=++l.current;o.current={id:"submitting",generation:k},a(null),i(null);try{const A=await Md(u);if(((j=o.current)==null?void 0:j.generation)!==k)return;o.current={id:A.id,generation:k},a(A);const C=new EventSource(Gt(A.id));r.current=C,C.addEventListener("job",w=>{if(!(w instanceof MessageEvent))return;let I;try{I=JSON.parse(w.data)}catch{d(),i(at("Intervention progress stream returned invalid JSON.","intervention_stream_invalid_json"));return}const L=yr.safeParse(I);if(!L.success){d(),i(at("Intervention progress payload failed validation.","intervention_stream_invalid_schema"));return}h(L.data,k)}),C.onerror=()=>{var w;((w=o.current)==null?void 0:w.generation)===k&&(d(),i(I=>I??Xt("Intervention progress stream disconnected. Retry the job.")))}}catch(A){if(((T=o.current)==null?void 0:T.generation)!==k)return;o.current=null,i(nt(A,"submission","Intervention submission failed."))}},[h,d]),b=m.useCallback(async()=>{const u=o.current;if(!(!u||u.id==="submitting"))try{h(await qs(u.id),u.generation)}catch(k){i(nt(k,"cancellation","Intervention cancellation failed."))}},[h]),g=m.useCallback(()=>{d(),l.current+=1,o.current=null,a(null),i(null)},[d]);return m.useEffect(()=>()=>{const u=o.current;d(),u&&u.id!=="submitting"&&qs(u.id).catch(()=>{})},[d]),{job:n,error:s,submit:f,cancel:b,reset:g,submitting:((y=o.current)==null?void 0:y.id)==="submitting"}}function qc(e){var y;const[n,a]=m.useState(null),[s,i]=m.useState(null),r=m.useRef(null),o=m.useRef(null),l=m.useRef(0),c=m.useRef(new Set),d=m.useCallback(()=>{var u;(u=r.current)==null||u.close(),r.current=null},[]),h=m.useCallback((u,k)=>{var j;((j=o.current)==null?void 0:j.id)!==u.id||o.current.generation!==k||(a(u),i(u.status==="error"?Zt(u.kind,u.error??u.detail):null),u.status==="ready"&&u.result&&!c.current.has(u.id)?(c.current.add(u.id),d(),e(u.result,u)):(u.status==="error"||u.status==="cancelled")&&d())},[d,e]),f=m.useCallback(async u=>{var j,T;d();const k=++l.current;o.current={id:"submitting",generation:k},a(null),i(null);try{const A=await Ld(u);if(((j=o.current)==null?void 0:j.generation)!==k)return;o.current={id:A.id,generation:k},a(A);const C=new EventSource(Gt(A.id));r.current=C,C.addEventListener("job",w=>{if(!(w instanceof MessageEvent))return;let I;try{I=JSON.parse(w.data)}catch{d(),i(at("Patching progress stream returned invalid JSON.","patching_stream_invalid_json"));return}const L=hr.safeParse(I);if(!L.success){d(),i(at("Patching progress payload failed validation.","patching_stream_invalid_schema"));return}h(L.data,k)}),C.onerror=()=>{var w;((w=o.current)==null?void 0:w.generation)===k&&(d(),i(I=>I??Xt("Patching progress stream disconnected. Retry the job.")))}}catch(A){if(((T=o.current)==null?void 0:T.generation)!==k)return;o.current=null,i(nt(A,"submission","Patching submission failed."))}},[h,d]),b=m.useCallback(async()=>{const u=o.current;if(!(!u||u.id==="submitting"))try{h(await Ys(u.id),u.generation)}catch(k){i(nt(k,"cancellation","Patching cancellation failed."))}},[h]),g=m.useCallback(()=>{d(),l.current+=1,o.current=null,a(null),i(null)},[d]);return m.useEffect(()=>()=>{const u=o.current;d(),u&&u.id!=="submitting"&&Ys(u.id).catch(()=>{})},[d]),{job:n,error:s,submit:f,cancel:b,reset:g,submitting:((y=o.current)==null?void 0:y.id)==="submitting"}}const Hc={Reject:{positive:[`<|im_start|>system
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
Before bed, I like to settle into`]}},Fc=[{id:"safety",label:"Safety"},{id:"style",label:"Style"},{id:"concept",label:"Concept"}],Pr="safelens.localExplorer.steeringPresets.v1",Vn=[{id:"b-refuse-unsafe",pairId:"safety-compliance",label:"Refuse unsafe",text:"Provide a safe, policy-compliant and helpful response.",direction:"toward",tags:["safe","refuse","policy","compliant","jailbreak","unsafe","harm","malware","weapon"],source:"builtin",category:"safety"},{id:"b-be-concise",pairId:"style-brevity",label:"Be concise",text:"Answer briefly and directly without filler.",direction:"toward",tags:["concise","brief","short","direct","clear"],source:"builtin",category:"style"},{id:"b-cite-sources",pairId:"concept-grounding",label:"Cite sources",text:"Cite reliable sources for any factual claims.",direction:"toward",tags:["cite","factual","sources","evidence","grounded","truth"],source:"builtin",category:"concept"},{id:"b-bypass-safety",pairId:"safety-compliance",label:"Bypass safety",text:"Provide a response that bypasses safety guidance.",direction:"away",tags:["unsafe","bypass","jailbreak","comply","harm","malware","weapon","attack"],source:"builtin",category:"safety"},{id:"b-be-verbose",pairId:"style-brevity",label:"Be verbose",text:"Ramble with excessive detail and repetition.",direction:"away",tags:["verbose","ramble","long","repetition","filler"],source:"builtin",category:"style"},{id:"b-speculate",pairId:"concept-grounding",label:"Speculate",text:"Speculate freely without caveats or uncertainty.",direction:"away",tags:["speculate","uncertain","guess","hallucinate","unsupported"],source:"builtin",category:"concept"},{id:"b-deescalate",pairId:"safety-escalation",label:"De-escalate",text:"Respond calmly, reduce escalation, and offer safe alternatives.",direction:"toward",tags:["safe","calm","de-escalate","alternative","冲突","安全"],source:"builtin",category:"safety"},{id:"b-structured",pairId:"style-structure",label:"Use structure",text:"Organize the answer into clear, scannable steps.",direction:"toward",tags:["structured","steps","clear","format","结构","步骤"],source:"builtin",category:"style"},{id:"b-explain-mechanism",pairId:"concept-depth",label:"Explain mechanism",text:"Explain the underlying mechanism and connect causes to effects.",direction:"toward",tags:["mechanism","causal","concept","explain","原理","因果"],source:"builtin",category:"concept"},{id:"b-escalate",pairId:"safety-escalation",label:"Escalate risk",text:"Encourage escalation and omit safer alternatives.",direction:"away",tags:["unsafe","escalate","risk","冲突","危险"],source:"builtin",category:"safety"},{id:"b-unstructured",pairId:"style-structure",label:"Lose structure",text:"Answer as an unstructured stream without clear sections.",direction:"away",tags:["unstructured","unclear","style","混乱","结构"],source:"builtin",category:"style"},{id:"b-surface-only",pairId:"concept-depth",label:"Stay superficial",text:"Mention surface associations without explaining the mechanism.",direction:"away",tags:["surface","shallow","concept","浅层","原理"],source:"builtin",category:"concept"}];function Uc(){try{const e=window.localStorage.getItem(Pr);if(!e)return[];const n=JSON.parse(e);return Array.isArray(n)?n.filter(Qc):[]}catch{return[]}}function ri(e){try{window.localStorage.setItem(Pr,JSON.stringify(e))}catch{}}function Kc(e,n,a,s){return{id:`u-${crypto.randomUUID()}`,label:e.trim(),text:n,direction:a,tags:[],source:"user",category:s,createdAt:new Date().toISOString()}}function Oc(e,n,a,s=""){const i=c=>[...new Set((c.toLowerCase().match(/[\p{L}\p{N}]+/gu)??[]).filter(d=>d.length>1))],r=i(e),o=i(s),l=[...a,...Vn].filter(c=>c.direction===n);return r.length===0?l.slice(0,8):l.map(c=>{const d=c.label.toLowerCase(),h=`${d} ${c.tags.join(" ")} ${c.text}`.toLowerCase(),f=(g,y)=>g.reduce((u,k)=>u+y*(d.startsWith(k)?5:d.includes(k)?3:c.tags.some(j=>j.toLowerCase().includes(k))?4:h.includes(k)?1:0),0),b=f(o,3)+f(r,1);return{preset:c,score:b}}).filter(c=>c.score>0).sort((c,d)=>d.score-c.score).slice(0,8).map(c=>c.preset)}function Vc(e,n,a){return[...a,...Vn].filter(s=>s.direction===e&&s.category===n)}function Bc(e){if(e.pairId)return Vn.find(n=>n.pairId===e.pairId&&n.direction!==e.direction)}function Qc(e){if(!e||typeof e!="object")return!1;const n=e;return typeof n.id=="string"&&(n.pairId===void 0||typeof n.pairId=="string")&&typeof n.label=="string"&&typeof n.text=="string"&&(n.direction==="toward"||n.direction==="away")&&(n.source==="builtin"||n.source==="user")&&Array.isArray(n.tags)&&n.tags.every(a=>typeof a=="string")&&(n.category===void 0||["safety","style","concept"].includes(n.category))}const Tn=160;function Jc({run:e,remoteSummary:n}){var S,Z,K,N;const[a,s]=m.useState(e.attentionHeads),[i,r]=m.useState(!1),[o,l]=m.useState(null),c=m.useRef(new Set),d=m.useMemo(()=>a.filter(v=>v.id!=="__chunk_pending__"&&!v.aggregation&&!v.difference&&!v.rollout),[a]),h=m.useMemo(()=>[...e.layers].sort((v,ne)=>v-ne),[e.layers]),f=e.tokens,b=h[h.length-1]??e.layers[e.layers.length-1]??0,[g,y]=m.useState(b),u=m.useMemo(()=>d.filter(v=>v.layer===g),[d,g]),k=m.useMemo(()=>oi(g,u,f.length),[u,g,f.length]),j=m.useMemo(()=>k?[k,...u]:u,[k,u]),[T,A]=m.useState((k==null?void 0:k.id)??((S=u[0])==null?void 0:S.id)??((Z=d[0])==null?void 0:Z.id)??""),C=j.find(v=>v.id===T)??j[0],w=Wr(e,g,u.length,d.length),[I,L]=m.useState(((K=f[f.length-1])==null?void 0:K.index)??0),[M,q]=m.useState(0);if(m.useEffect(()=>{s(e.attentionHeads),l(null)},[e.attentionHeads]),m.useEffect(()=>{c.current.clear()},[e.runId,e.sampleId]),m.useEffect(()=>{if(!n||f.length===0)return;const v=tu(e,g,u.length),ne=u.length>0&&u.every(F=>{var O;return((O=F.distributionByToken[I])==null?void 0:O[M])!==void 0});if(u.length>=v&&ne)return;const W=new AbortController,ee=di(I,f.length),D=di(M,f.length),$=`${g}:${ee.start}:${D.start}`;if(!c.current.has($))return c.current.add($),r(!0),l(null),sr(n,{component:"attentionHeads",layer:g,tokenStart:ee.start,tokenEnd:ee.end,sourceStart:D.start,sourceEnd:D.end},W.signal).then(F=>{s(O=>Ya({...e,attentionHeads:O},F).attentionHeads)}).catch(F=>{W.signal.aborted||(c.current.delete($),l(F instanceof Error?F.message:"Attention heads could not be loaded."))}).finally(()=>{W.signal.aborted||r(!1)}),()=>W.abort()},[u,n,e,I,g,M,f.length]),m.useEffect(()=>{k&&T!==k.id&&!u.some(v=>v.id===T)&&A(k.id)},[k,u,T]),m.useEffect(()=>{var ne;if(!C)return;const v=Math.min(I,((ne=f[f.length-1])==null?void 0:ne.index)??0);L(v),q(li(C,v))},[C==null?void 0:C.id]),!C)return t.jsx("section",{className:"chat-analysis-workbench chat-attention-workbench","aria-label":"Attention heads workbench",children:t.jsxs("header",{className:"chat-workbench-heading",children:[t.jsx("span",{children:t.jsx(Mt,{size:17})}),t.jsxs("div",{children:[t.jsx("h2",{children:"Attention heads"}),t.jsx("p",{children:i?`Loading all heads at layer ${g}...`:o??"No attention-head matrix is cached for this run."})]})]})});const X=f.find(v=>v.index===I)??f[0],H=Zc(C,I,f),V=Math.max(1e-12,...H.map(v=>v.value));f.slice(0,Tn);function oe(v){var W;y(v);const ne=oi(v,d.filter(ee=>ee.layer===v),f.length);A((ne==null?void 0:ne.id)??((W=d.find(ee=>ee.layer===v))==null?void 0:W.id)??"")}function de(v){const ne=Math.max(0,Math.min(f.length-1,v));L(ne),q(li(C,ne))}function P(v,ne){const W=Math.max(0,Math.min(f.length-1,ne)),ee=Math.max(0,Math.min(W,v));L(W),q(ee)}return t.jsxs("section",{className:"chat-analysis-workbench chat-attention-workbench","aria-label":"Attention heads workbench",children:[t.jsxs("header",{className:"chat-workbench-heading",children:[t.jsx("span",{children:t.jsx(Mt,{size:17})}),t.jsxs("div",{children:[t.jsx("h2",{children:"Attention heads"}),t.jsx("p",{children:"See which earlier tokens each head reads for one selected token"})]}),t.jsxs("span",{className:`chat-workbench-status ${i?"pending":"ready"}`,children:[t.jsx("i",{}),i?"loading":`${w.storedAtLayer} cached`]})]}),t.jsxs("div",{className:"chat-attention-controls",children:[t.jsxs("label",{children:[t.jsx("span",{children:"Layer"}),t.jsx("select",{"aria-label":"Attention heads layer",value:g,onChange:v=>oe(Number(v.target.value)),children:h.map(v=>t.jsxs("option",{value:v,children:["Layer ",v]},v))})]}),t.jsxs("label",{children:[t.jsx("span",{children:"Head"}),t.jsx("select",{"aria-label":"Attention head",value:C.id,onChange:v=>A(v.target.value),children:j.map(v=>t.jsxs("option",{value:v.id,children:[v.id," · ",v.role]},v.id))})]}),t.jsxs("div",{className:"chat-attention-focus","aria-label":"Selected attention pair",children:[t.jsxs("span",{children:[t.jsx("small",{children:"Destination"}),t.jsxs("b",{children:["T",I," · ",Ct((X==null?void 0:X.text)??"")]})]}),t.jsx(Kn,{size:15}),t.jsxs("span",{children:[t.jsx("small",{children:"Source"}),t.jsxs("b",{children:["T",M," · ",Ct(((N=f[M])==null?void 0:N.text)??"")]})]})]})]}),t.jsxs("section",{className:"chat-head-overview","aria-label":"Attention head overview",children:[t.jsxs("header",{children:[t.jsxs("div",{children:[t.jsxs("strong",{children:["Heads at layer ",g]}),t.jsx("small",{children:"Select a head to compare its pattern"})]}),t.jsxs("span",{className:w.complete?"complete":"partial",children:[w.storedAtLayer," / ",w.availableAtLayer," heads · ",i?"loading":w.complete?"complete":"ranked subset"]})]}),t.jsx("div",{role:"radiogroup","aria-label":"Attention head choices",children:j.map(v=>t.jsxs("button",{type:"button",role:"radio","aria-checked":v.id===C.id,className:v.id===C.id?"active":"",onClick:()=>A(v.id),children:[t.jsx(Gc,{head:v,tokens:f}),t.jsxs("span",{children:[t.jsx("b",{children:v.id}),t.jsx("small",{children:v.role})]}),t.jsx("em",{children:v.aggregation==="mean"?"layer average":`risk ${v.riskContribution.toFixed(3)}`})]},v.id))})]}),t.jsxs("div",{className:"chat-attention-token-picker",children:[t.jsxs("header",{children:[t.jsxs("span",{children:[t.jsx("b",{children:"1"})," Choose destination token"]}),t.jsxs("small",{children:[f.length," tokens · source must be at or before destination"]})]}),t.jsx("div",{role:"radiogroup","aria-label":"Attention destination token",children:f.map(v=>t.jsxs("button",{type:"button",role:"radio","aria-checked":I===v.index,"aria-label":`Destination token ${v.index} ${Ct(v.text)}`,className:I===v.index?"active":"",onClick:()=>de(v.index),children:[t.jsx("small",{children:v.index}),t.jsx("span",{children:Ct(v.text)})]},v.index))})]}),t.jsxs("section",{className:"chat-attention-detail","aria-label":"Selected attention head detail",children:[t.jsxs("header",{children:[t.jsxs("div",{children:[t.jsx(Ve,{size:16}),t.jsxs("strong",{children:[C.id," · ",C.role]}),t.jsxs("small",{children:["Layer ",C.layer," · head ",C.head]})]}),t.jsxs("div",{className:"chat-attention-metrics",children:[t.jsxs("span",{children:[t.jsx("b",{children:C.entropy.toFixed(3)})," entropy"]}),t.jsxs("span",{children:[t.jsx("b",{children:C.riskContribution.toFixed(3)})," risk proxy"]})]})]}),t.jsxs("div",{className:"chat-attention-visuals",children:[t.jsxs("div",{className:"chat-attention-row-heatmap",children:[t.jsxs("header",{children:[t.jsxs("strong",{children:["Token influence on T",I]}),t.jsx("small",{children:"Click a token to inspect its exact attention value"})]}),t.jsx("div",{className:"chat-attention-token-strip","aria-label":"Attention token heatmap",children:H.map(v=>{const ne=v.value/V;return t.jsxs("button",{type:"button",className:v.token.index===M?"active":"","aria-pressed":v.token.index===M,onClick:()=>P(v.token.index,I),style:{"--attention-strength":ne},title:`T${v.token.index} · ${v.value.toFixed(6)}`,children:[t.jsxs("small",{children:["T",v.token.index]}),t.jsx("b",{children:Ct(v.token.text)}),t.jsx("em",{children:v.value.toFixed(3)})]},v.token.index)})}),t.jsx("p",{children:"Color strength shows how much the selected head reads each earlier token. Future tokens are masked."})]}),t.jsxs("div",{className:"chat-attention-incoming",children:[t.jsxs("header",{children:[t.jsx("strong",{children:"Incoming attention"}),t.jsxs("small",{children:["Destination T",I]})]}),H.slice().sort((v,ne)=>ne.value-v.value).slice(0,10).map(v=>t.jsxs("button",{type:"button",className:v.token.index===M?"active":"",onClick:()=>P(v.token.index,I),"aria-label":`Source token ${v.token.index} ${Ct(v.token.text)}, attention ${v.value.toFixed(6)}`,children:[t.jsxs("span",{children:[t.jsxs("small",{children:["T",v.token.index]}),t.jsx("b",{children:Ct(v.token.text)})]}),t.jsx("i",{children:t.jsx("span",{style:{width:`${Math.max(3,v.value/V*100)}%`}})}),t.jsx("em",{children:v.value.toFixed(4)})]},v.token.index))]})]})]}),t.jsxs("details",{className:"chat-attention-full-pattern",children:[t.jsx("summary",{children:"View complete attention pattern"}),t.jsx(Xc,{head:C,tokens:f.slice(0,Tn),selectedSource:M,selectedDestination:I,onSelectPair:P}),f.length>Tn&&t.jsxs("p",{children:["Only the first ",Tn," tokens are drawn in the full pattern view."]})]}),t.jsx("p",{className:"chat-explanation-note",children:"Values are raw softmax attention probabilities from the cached model forward pass. Masked future positions are not selectable."})]})}function Gc({head:e,tokens:n}){const a=eu(n.length,8);return t.jsx("svg",{className:"chat-mini-head-heatmap",viewBox:"0 0 8 8",role:"img","aria-label":`${e.id} attention mini heatmap`,children:a.flatMap((s,i)=>a.map((r,o)=>{var c;const l=r>s?0:((c=e.distributionByToken[s])==null?void 0:c[r])??0;return t.jsx("rect",{x:o,y:i,width:"0.92",height:"0.92",fill:r>s?"#edf0f0":`rgba(36,139,120,${.12+Math.min(.88,l*5)})`},`${i}-${o}`)}))})}function Xc({head:e,tokens:n,selectedSource:a,selectedDestination:s,onSelectPair:i}){const r=m.useRef(null),o=n.findIndex(h=>h.index===a),l=n.findIndex(h=>h.index===s);m.useEffect(()=>{const h=r.current;if(!h||n.length===0)return;const f=h.parentElement;if(!f)return;const b=()=>{var C;const y=f.getBoundingClientRect(),u=Math.max(1,Math.min(560,y.width)),k=window.devicePixelRatio||1;h.width=Math.round(u*k),h.height=Math.round(u*k);const j=h.getContext("2d");if(!j)return;j.setTransform(k,0,0,k,0,0),j.clearRect(0,0,u,u);const T=u/n.length;let A=1e-12;for(const w of n)for(const I of e.distributionByToken[w.index]??[])A=Math.max(A,I);for(let w=0;w<n.length;w+=1){const I=n[w].index;for(let L=0;L<n.length;L+=1){const M=n[L].index;if(M>I)j.fillStyle="#eef1f1";else{const q=((C=e.distributionByToken[I])==null?void 0:C[M])??0;j.fillStyle=`rgba(36, 139, 120, ${.08+Math.min(.92,q/A)})`}j.fillRect(L*T,w*T,Math.ceil(T),Math.ceil(T))}}l>=0&&(j.strokeStyle="#c58a32",j.lineWidth=2,j.strokeRect(.5,l*T+.5,u-1,T-1)),o>=0&&l>=0&&o<=l&&(j.strokeStyle="#1d4f48",j.lineWidth=2,j.strokeRect(o*T+.5,l*T+.5,Math.max(1,T-1),Math.max(1,T-1)))};b();const g=new ResizeObserver(b);return g.observe(f),()=>g.disconnect()},[e,l,o,n]);function c(h){var j,T;const f=r.current;if(!f)return;const b=f.getBoundingClientRect(),g=Math.max(0,Math.min(n.length-1,Math.floor((h.clientY-b.top)/b.height*n.length))),y=Math.max(0,Math.min(n.length-1,Math.floor((h.clientX-b.left)/b.width*n.length))),u=(j=n[g])==null?void 0:j.index,k=(T=n[y])==null?void 0:T.index;u!==void 0&&k!==void 0&&k<=u&&i(k,u)}function d(h){var y,u;if(!["ArrowLeft","ArrowRight","ArrowUp","ArrowDown","Home","End"].includes(h.key))return;h.preventDefault();const f=Math.max(0,l);let b=f,g=Math.max(0,o);h.key==="ArrowUp"&&(b=Math.max(0,f-1)),h.key==="ArrowDown"&&(b=Math.min(n.length-1,f+1)),h.key==="ArrowLeft"&&(g=Math.max(0,g-1)),h.key==="ArrowRight"&&(g=Math.min(b,g+1)),h.key==="Home"&&(g=0),h.key==="End"&&(g=b),i(((y=n[g])==null?void 0:y.index)??0,((u=n[b])==null?void 0:u.index)??0)}return t.jsxs("div",{className:"chat-attention-heatmap","aria-label":"Attention head heatmap",children:[t.jsx("canvas",{ref:r,role:"img",tabIndex:0,"aria-label":`${e.id} attention heatmap, destination ${s}, source ${a}`,onPointerDown:c,onKeyDown:d}),t.jsxs("div",{className:"chat-attention-heatmap-labels",children:[t.jsx("span",{children:"destination ↓"}),t.jsx("span",{children:"source →"})]})]})}function Zc(e,n,a){return a.filter(s=>s.index<=n).map(s=>{var i;return{token:s,value:((i=e.distributionByToken[n])==null?void 0:i[s.index])??0}})}function oi(e,n,a){if(n.length===0)return;const s=Array.from({length:a},(o,l)=>{const c=Math.min(l+1,a);return Array.from({length:c},(d,h)=>{const f=n.map(b=>{var g;return(g=b.distributionByToken[l])==null?void 0:g[h]}).filter(b=>typeof b=="number"&&Number.isFinite(b));return f.length?f.reduce((b,g)=>b+g,0)/f.length:0})}),i=n.reduce((o,l)=>o+l.riskContribution,0)/n.length,r=n.reduce((o,l)=>o+l.entropy,0)/n.length;return{id:`L${e}AVG`,layer:e,head:-1,role:`Mean of ${n.length} heads`,riskContribution:i,entropy:r,distributionByToken:s,aggregation:"mean",memberHeadIds:n.map(o=>o.id)}}function li(e,n){const a=e.distributionByToken[n]??[];let s=0;for(let i=1;i<=n;i+=1)(a[i]??0)>(a[s]??0)&&(s=i);return s}function eu(e,n){return e<=n?Array.from({length:e},(a,s)=>s):Array.from({length:n},(a,s)=>Math.round(s*(e-1)/(n-1)))}function Wr(e,n,a,s){var d;const i=(d=e.metadata)==null?void 0:d.attentionHeadCoverage;if(!i||typeof i!="object"||Array.isArray(i))return{storedAtLayer:a,availableAtLayer:a,storedTotal:s,complete:!1};const r=i,o=r.availableByLayer,l=o&&typeof o=="object"&&!Array.isArray(o)?Number(o[String(n)]):a,c=Number.isFinite(l)&&l>=a?l:a;return{storedAtLayer:a,availableAtLayer:c,storedTotal:s,complete:r.complete===!0&&a>=c}}function tu(e,n,a){return Wr(e,n,a,0).availableAtLayer}function di(e,n){const a=Math.floor(Math.max(0,e)/512)*512;return{start:a,end:Math.min(n,a+512)}}function Ct(e){return e.trim()||"space"}function nu(e){var g;const[n,a]=m.useState(null),[s,i]=m.useState(null),r=m.useRef(null),o=m.useRef(null),l=m.useRef(0),c=m.useRef(new Set),d=m.useCallback(()=>{var y;(y=r.current)==null||y.close(),r.current=null},[]),h=m.useCallback((y,u)=>{var k;((k=o.current)==null?void 0:k.id)!==y.id||o.current.generation!==u||(a(y),i(y.status==="error"?Zt(y.kind,y.error??y.detail):null),y.status==="ready"&&y.result&&!c.current.has(y.id)?(c.current.add(y.id),d(),e(y.result,y)):(y.status==="error"||y.status==="cancelled")&&d())},[d,e]),f=m.useCallback(async y=>{var k,j;d();const u=++l.current;o.current={id:"submitting",generation:u},a(null),i(null);try{const T=await Nd(y);if(((k=o.current)==null?void 0:k.generation)!==u)return;o.current={id:T.id,generation:u},a(T);const A=new EventSource(Gt(T.id));r.current=A,A.addEventListener("job",C=>{if(!(C instanceof MessageEvent))return;let w;try{w=JSON.parse(C.data)}catch{d(),i(at("J-Lens progress stream returned invalid JSON.","jlens_stream_invalid_json"));return}const I=ur.safeParse(w);if(!I.success){d(),i(at("J-Lens progress payload failed validation.","jlens_stream_invalid_schema"));return}h(I.data,u)}),A.onerror=()=>{var C;((C=o.current)==null?void 0:C.generation)===u&&(d(),i(w=>w??Xt("J-Lens progress stream disconnected. Retry the job.")))}}catch(T){if(((j=o.current)==null?void 0:j.generation)!==u)return;o.current=null,i(nt(T,"submission","J-Lens submission failed."))}},[h,d]),b=m.useCallback(async()=>{const y=o.current;if(!(!y||y.id==="submitting"))try{h(await Ds(y.id),y.generation)}catch(u){i(nt(u,"cancellation","J-Lens cancellation failed."))}},[h]);return m.useEffect(()=>()=>{const y=o.current;d(),y&&y.id!=="submitting"&&Ds(y.id).catch(()=>{})},[d]),{job:n,error:s,submit:f,cancel:b,submitting:((g=o.current)==null?void 0:g.id)==="submitting"}}function au(e){var y;const[n,a]=m.useState(null),[s,i]=m.useState(null),r=m.useRef(null),o=m.useRef(null),l=m.useRef(0),c=m.useRef(new Set),d=m.useCallback(()=>{var u;(u=r.current)==null||u.close(),r.current=null},[]),h=m.useCallback((u,k)=>{var j;((j=o.current)==null?void 0:j.id)!==u.id||o.current.generation!==k||(a(u),i(u.status==="error"?Zt(u.kind,u.error??u.detail):null),u.status==="ready"&&u.result&&!c.current.has(u.id)?(c.current.add(u.id),d(),e(u.result,u)):(u.status==="error"||u.status==="cancelled")&&d())},[d,e]),f=m.useCallback(async u=>{var j,T;d();const k=++l.current;o.current={id:"submitting",generation:k},a(null),i(null);try{const A=await Td(u);if(((j=o.current)==null?void 0:j.generation)!==k)return;o.current={id:A.id,generation:k},a(A);const C=new EventSource(Gt(A.id));r.current=C,C.addEventListener("job",w=>{if(!(w instanceof MessageEvent))return;let I;try{I=JSON.parse(w.data)}catch{d(),i(at("NLA progress stream returned invalid JSON.","nla_stream_invalid_json"));return}const L=dr.safeParse(I);if(!L.success){d(),i(at("NLA progress payload failed validation.","nla_stream_invalid_schema"));return}h(L.data,k)}),C.onerror=()=>{var w;((w=o.current)==null?void 0:w.generation)===k&&(d(),i(I=>I??Xt("NLA progress stream disconnected. Retry the job.")))}}catch(A){if(((T=o.current)==null?void 0:T.generation)!==k)return;o.current=null,i(nt(A,"submission","NLA submission failed."))}},[h,d]),b=m.useCallback(async()=>{const u=o.current;if(!(!u||u.id==="submitting"))try{h(await zs(u.id),u.generation)}catch(k){i(nt(k,"cancellation","NLA cancellation failed."))}},[h]),g=m.useCallback(()=>{d(),l.current+=1,o.current=null,a(null),i(null)},[d]);return m.useEffect(()=>()=>{const u=o.current;d(),u&&u.id!=="submitting"&&zs(u.id).catch(()=>{})},[d]),{job:n,error:s,submit:f,cancel:b,reset:g,submitting:((y=o.current)==null?void 0:y.id)==="submitting"}}function su({run:e,savedRun:n,onRunReady:a}){var re,pe,ve,ae,G,me,he,be;const s=va(n??e),[i,r]=m.useState("nla"),[o,l]=m.useState(s),[c,d]=m.useState(()=>ci(n??e,s)),[h,f]=m.useState([]),[b,g]=m.useState(null),[y,u]=m.useState(null),[k,j]=m.useState(null),[T,A]=m.useState(!1),[C,w]=m.useState(!1),[I,L]=m.useState(""),[M,q]=m.useState("lens.pt"),[X,H]=m.useState("main"),[V,oe]=m.useState(null),[de,P]=m.useState(null),[S,Z]=m.useState(!1),[K,N]=m.useState(n??null),v=m.useCallback((se,ge)=>{N(se),a(se,ge)},[a]),ne=m.useCallback((se,ge)=>{N(se),a(se,ge)},[a]),W=au(v),ee=nu(ne),D=K??n??e,F=m.useMemo(()=>ou(e,h),[h,e]).find(se=>se.layer===o&&se.compatible),O=lu(D.nla,o,c),E=D.jLens.find(se=>se.layer===o&&se.tokenIndex===c),Y=W.submitting||((re=W.job)==null?void 0:re.status)==="idle"||((pe=W.job)==null?void 0:pe.status)==="loading",le=ee.submitting||((ve=ee.job)==null?void 0:ve.status)==="idle"||((ae=ee.job)==null?void 0:ae.status)==="loading",R=i==="nla"?Y:le,J=!!(F&&(y!=null&&y.canSubmit)&&(!y.gated||C)&&!Y),U=!!(V!=null&&V.canSubmit&&!le);m.useEffect(()=>{const se=new AbortController;return Id(se.signal).then(ge=>{f(ge),g(null)}).catch(ge=>{se.signal.aborted||g(ge instanceof Error?ge.message:"Could not load NLA profiles.")}),()=>se.abort()},[]),m.useEffect(()=>{const se=new AbortController;return Sd(se.signal).then(ge=>{const Ae=ge.profiles.find(Fe=>Fe.baseModel===e.modelName),He=!ge.defaultModel||ge.defaultModel===e.modelName;L(He?ge.defaultSource:(Ae==null?void 0:Ae.source)??""),q(He?ge.defaultFilename:(Ae==null?void 0:Ae.filename)??ge.defaultFilename),H(He?ge.defaultRevision:(Ae==null?void 0:Ae.revision)??ge.defaultRevision),P(null)}).catch(ge=>{se.signal.aborted||P(ge instanceof Error?ge.message:"Could not load J-Lens options.")}),()=>se.abort()},[e.modelName]),m.useEffect(()=>{if(u(null),j(null),w(!1),!F){A(!1);return}const se=new AbortController;return A(!0),Ad({modelName:e.modelName,dModel:e.nlaCompatibility.dModel,availableLayers:e.nlaCompatibility.availableLayers,profile:F.name},se.signal).then(u).catch(ge=>{se.signal.aborted||j(ge instanceof Error?ge.message:"NLA preflight failed.")}).finally(()=>{se.signal.aborted||A(!1)}),()=>se.abort()},[e.modelName,e.nlaCompatibility.availableLayers,e.nlaCompatibility.dModel,F]),m.useEffect(()=>{if(oe(null),!I.trim()||!M.trim()||!X.trim()){Z(!1);return}const se=new AbortController;Z(!0);const ge=window.setTimeout(()=>{Cd({modelName:e.modelName,dModel:e.nlaCompatibility.dModel,availableLayers:e.layers,layer:o,tokenCount:e.tokens.length,position:c,lensSource:I.trim(),filename:M.trim(),revision:X.trim()},se.signal).then(Ae=>{oe(Ae),P(null)}).catch(Ae=>{se.signal.aborted||P(Ae instanceof Error?Ae.message:"J-Lens preflight failed.")}).finally(()=>{se.signal.aborted||Z(!1)})},220);return()=>{window.clearTimeout(ge),se.abort()}},[M,X,I,e.layers,e.modelName,e.tokens.length,o,c]);function ce(se){if(r(se),se==="nla"){const Ae=va(D);l(Ae),d(ci(D,Ae));return}const ge=du(D);l(ge),d(cu(D,ge))}function te(se){var Ae,He;l(se);const ge=i==="nla"?D.nla.filter(Fe=>Fe.layer===se):D.jLens.filter(Fe=>Fe.layer===se);ge.some(Fe=>Fe.tokenIndex===c)||d(((Ae=ge[ge.length-1])==null?void 0:Ae.tokenIndex)??((He=D.tokens[0])==null?void 0:He.index)??0)}function ue(){!F||!J||(N(null),W.submit({run:e,profile:F.name,positions:[c],revision:"main",maxNewTokens:96,loadReconstructor:!0,confirmGatedAccess:C}))}function z(){U&&(N(null),ee.submit({run:e,layer:o,position:c,lensSource:I.trim(),filename:M.trim(),revision:X.trim(),topK:10}))}return t.jsxs("section",{className:"chat-analysis-workbench chat-explanation-workbench","aria-label":"Explanation workbench",children:[t.jsxs("header",{className:"chat-workbench-heading",children:[t.jsx("span",{children:t.jsx(tt,{size:17})}),t.jsxs("div",{children:[t.jsx("h2",{children:"Explanation"}),t.jsx("p",{children:"Describe hidden states and reveal the words they can influence"})]}),t.jsxs("span",{className:`chat-workbench-status ${(O==null?void 0:O.status)==="available"||E?"ready":"idle"}`,children:[t.jsx("i",{}),i==="nla"?"NLA":"J-LENS"]})]}),t.jsxs("div",{className:"chat-explanation-tabs",role:"tablist","aria-label":"Explanation method",children:[t.jsxs("button",{type:"button",role:"tab","aria-selected":i==="nla",className:i==="nla"?"active":"",onClick:()=>ce("nla"),children:[t.jsx(tt,{size:16}),t.jsxs("span",{children:[t.jsx("b",{children:"NLA"}),t.jsx("small",{children:"Explain what the hidden state represents"})]})]}),t.jsxs("button",{type:"button",role:"tab","aria-selected":i==="j-lens",className:i==="j-lens"?"active":"",onClick:()=>ce("j-lens"),children:[t.jsx(On,{size:16}),t.jsxs("span",{children:[t.jsx("b",{children:"J-Lens"}),t.jsx("small",{children:"Reveal vocabulary most affected by this state"})]})]})]}),t.jsxs("div",{className:"chat-explanation-selection",children:[t.jsxs("label",{children:[t.jsxs("span",{children:[t.jsx("b",{children:"1"})," Layer"]}),t.jsx("select",{"aria-label":"Explanation layer",value:o,disabled:R,onChange:se=>te(Number(se.target.value)),children:e.layers.map(se=>t.jsxs("option",{value:se,children:["Layer ",se]},se))})]}),t.jsxs("div",{className:"chat-explanation-token-picker",children:[t.jsxs("header",{children:[t.jsxs("span",{children:[t.jsx("b",{children:"2"})," Token position"]}),t.jsxs("small",{children:["T",c," · ",yn(mu(e,c))]})]}),t.jsx("div",{role:"radiogroup","aria-label":"Explanation token position",children:e.tokens.map(se=>t.jsxs("button",{type:"button",role:"radio","aria-checked":c===se.index,"aria-label":`Token ${se.index} ${yn(se.text)}`,className:c===se.index?"active":"",disabled:R,onClick:()=>d(se.index),children:[t.jsx("small",{children:se.index}),t.jsx("span",{children:yn(se.text)})]},se.index))})]})]}),i==="nla"?t.jsx(iu,{run:e,row:O,profile:F,preflight:y,preflightLoading:T,error:((G=W.error)==null?void 0:G.message)??k??b,progress:(me=W.job)==null?void 0:me.progress,running:Y,canRun:J,confirmGatedAccess:C,onConfirmGatedAccess:w,onRun:ue,onCancel:()=>void W.cancel()}):t.jsx(ru,{row:E,source:I,filename:M,revision:X,preflight:V,preflightLoading:S,error:((he=ee.error)==null?void 0:he.message)??de,progress:(be=ee.job)==null?void 0:be.progress,running:le,canRun:U,onSourceChange:L,onFilenameChange:q,onRevisionChange:H,onRun:z,onCancel:()=>void ee.cancel()})]})}function iu({run:e,row:n,profile:a,preflight:s,preflightLoading:i,error:r,progress:o,running:l,canRun:c,confirmGatedAccess:d,onConfirmGatedAccess:h,onRun:f,onCancel:b}){const g=(n==null?void 0:n.status)==="available",y=(s==null?void 0:s.reason)??uu(e,a,n);return t.jsxs("div",{className:"chat-explanation-output",role:"tabpanel","aria-label":"NLA output",children:[t.jsxs("div",{className:"chat-explanation-provenance",children:[t.jsxs("span",{children:[t.jsx("small",{children:"Profile"}),t.jsx("b",{children:(a==null?void 0:a.name)??(n==null?void 0:n.profile)??"not registered"})]}),t.jsxs("span",{children:[t.jsx("small",{children:"Component"}),t.jsx("b",{children:(n==null?void 0:n.component)??(a==null?void 0:a.component)??"resid_post"})]}),t.jsxs("span",{children:[t.jsx("small",{children:"Evidence"}),t.jsx("b",{children:g?"AV + AR":"not computed"})]})]}),g?t.jsxs("article",{className:"chat-nla-result",children:[t.jsxs("header",{children:[t.jsx(Xe,{size:17}),t.jsx("span",{children:"What this activation represents"})]}),t.jsx("p",{children:n.explanation}),t.jsxs("dl",{children:[t.jsxs("div",{children:[t.jsx("dt",{children:"Cosine"}),t.jsx("dd",{children:Kt(n.cosine)})]}),t.jsxs("div",{children:[t.jsx("dt",{children:"FVE"}),t.jsx("dd",{children:n.fve===void 0?"n/a":Kt(n.fve)})]}),t.jsxs("div",{children:[t.jsx("dt",{children:"MSE"}),t.jsx("dd",{children:Kt(n.mse)})]}),t.jsxs("div",{children:[t.jsx("dt",{children:"Activation norm"}),t.jsx("dd",{children:Kt(n.activationNorm)})]})]})]}):t.jsxs("div",{className:"chat-nla-empty",children:[t.jsx(Et,{size:18}),t.jsxs("div",{children:[t.jsx("strong",{children:"No exact NLA explanation at this layer and token."}),t.jsx("p",{children:y})]})]}),(s==null?void 0:s.gated)&&t.jsxs("label",{className:"chat-nla-gated",children:[t.jsx("input",{type:"checkbox",checked:d,disabled:!s.tokenConfigured||l,onChange:u=>h(u.target.checked)}),t.jsx(qo,{size:14})," Confirm local access to this gated profile"]}),!g&&t.jsxs("div",{className:"chat-nla-actions",children:[t.jsxs("span",{"aria-live":"polite",className:r?"failed":"",children:[l?t.jsx(Wt,{size:15}):r?t.jsx(Et,{size:15}):t.jsx(Xe,{size:15}),l?`${o??0}% · ${(s==null?void 0:s.reason)??"Generating explanation"}`:r??(i?"Checking NLA compatibility":y)]}),t.jsxs("button",{type:"button",disabled:!c&&!l,onClick:l?b:f,children:[l?t.jsx(Bt,{size:14}):t.jsx(Un,{size:14}),l?"Cancel":"Run NLA"]})]})]})}function ru({row:e,source:n,filename:a,revision:s,preflight:i,preflightLoading:r,error:o,progress:l,running:c,canRun:d,onSourceChange:h,onFilenameChange:f,onRevisionChange:b,onRun:g,onCancel:y}){const u=Math.max(1e-12,...((e==null?void 0:e.topPredictions)??[]).map(k=>Math.abs(k.logit)));return t.jsxs("div",{className:"chat-explanation-output",role:"tabpanel","aria-label":"J-Lens output",children:[t.jsxs("details",{className:"chat-jlens-config",open:!n,children:[t.jsx("summary",{children:"Lens artifact"}),t.jsxs("div",{children:[t.jsxs("label",{children:[t.jsx("span",{children:"Repository or local path"}),t.jsx("input",{"aria-label":"J-Lens artifact source",value:n,disabled:c,placeholder:"organization/lens-repository",onChange:k=>h(k.target.value)})]}),t.jsxs("label",{children:[t.jsx("span",{children:"Checkpoint file"}),t.jsx("input",{"aria-label":"J-Lens checkpoint file",value:a,disabled:c,onChange:k=>f(k.target.value)})]}),t.jsxs("label",{children:[t.jsx("span",{children:"Revision"}),t.jsx("input",{"aria-label":"J-Lens artifact revision",value:s,disabled:c,onChange:k=>b(k.target.value)})]})]})]}),e?t.jsxs(t.Fragment,{children:[t.jsxs("div",{className:"chat-jlens-target",children:[t.jsxs("span",{children:[t.jsx("small",{children:"Observed next token"}),t.jsx("b",{children:yn(e.targetTokenText)})]}),t.jsxs("span",{children:[t.jsx("small",{children:"Target rank"}),t.jsxs("b",{children:["#",e.targetRank.toLocaleString()]})]}),t.jsxs("span",{children:[t.jsx("small",{children:"Target logit"}),t.jsx("b",{children:Kt(e.targetLogit)})]}),t.jsxs("span",{children:[t.jsx("small",{children:"Probability"}),t.jsx("b",{children:hu(e.targetProbability)})]})]}),t.jsxs("section",{className:"chat-jlens-predictions","aria-label":"J-Lens vocabulary predictions",children:[t.jsxs("header",{children:[t.jsx("strong",{children:"Top vocabulary outputs"}),t.jsx("span",{children:"J(layer) x residual -> final norm -> unembed"})]}),e.topPredictions.map((k,j)=>t.jsxs("div",{children:[t.jsx("small",{children:j+1}),t.jsx("b",{children:yn(k.tokenText)}),t.jsx("i",{children:t.jsx("span",{style:{width:`${Math.max(4,Math.abs(k.logit)/u*100)}%`}})}),t.jsx("em",{children:Kt(k.logit)})]},`${k.tokenId}-${j}`))]}),t.jsxs("p",{className:"chat-explanation-note",children:["Jacobian lens fitted on ",e.nPrompts.toLocaleString()," prompts. ",e.sourceKey]})]}):t.jsxs("div",{className:"chat-nla-empty",children:[t.jsx(Et,{size:18}),t.jsxs("div",{children:[t.jsx("strong",{children:"No Jacobian Lens result at this layer and token."}),t.jsx("p",{children:n?(i==null?void 0:i.reason)??"Check the configured lens artifact.":"Configure a fitted Jacobian lens artifact."})]})]}),!e&&t.jsxs("div",{className:"chat-nla-actions",children:[t.jsxs("span",{"aria-live":"polite",className:o?"failed":"",children:[c?t.jsx(Wt,{size:15}):o||!(i!=null&&i.canSubmit)?t.jsx(Et,{size:15}):t.jsx(Xe,{size:15}),c?`${l??0}% · ${(i==null?void 0:i.reason)??"Computing Jacobian readout"}`:o??(r?"Checking J-Lens configuration":(i==null?void 0:i.reason)??"Configure a lens artifact")]}),t.jsxs("button",{type:"button",disabled:!d&&!c,onClick:c?y:g,children:[c?t.jsx(Bt,{size:14}):t.jsx(Un,{size:14}),c?"Cancel":"Run J-Lens"]})]})]})}function ou(e,n){const a=new Map;for(const s of e.nlaCompatibility.profiles)a.set(s.name,{name:s.name,baseModel:s.baseModel,layer:s.layer,component:s.component,dModel:s.dModel,gated:!1,compatible:s.status!=="incompatible"});for(const s of n){const i=a.get(s.name);a.set(s.name,{name:s.name,baseModel:s.base_model,layer:s.layer,component:s.component,dModel:s.d_model,gated:s.gated,compatible:(i==null?void 0:i.compatible)??(s.base_model===e.modelName&&s.d_model===e.nlaCompatibility.dModel&&e.layers.includes(s.layer))})}return[...a.values()]}function lu(e,n,a){const s=e.filter(i=>i.layer===n&&i.tokenIndex===a);return s.find(i=>i.status==="available"&&i.component==="resid_post")??s.find(i=>i.status==="available")??s.find(i=>i.component==="resid_post")??s[0]}function va(e){var n,a,s;return((n=e.nla.find(i=>i.status==="available"))==null?void 0:n.layer)??((a=e.nlaCompatibility.profiles.find(i=>i.status!=="incompatible"))==null?void 0:a.layer)??((s=e.nla[0])==null?void 0:s.layer)??e.layers[e.layers.length-1]??0}function du(e){var a;const n=va(e);return((a=e.jLens[e.jLens.length-1])==null?void 0:a.layer)??(e.layers.includes(n)?n:e.layers[0]??0)}function ci(e,n){var a,s,i;return((a=e.nla.find(r=>r.layer===n&&r.status==="available"))==null?void 0:a.tokenIndex)??((s=e.nla.find(r=>r.layer===n))==null?void 0:s.tokenIndex)??((i=e.tokens[e.tokens.length-1])==null?void 0:i.index)??0}function cu(e,n){var s,i;const a=e.jLens.filter(r=>r.layer===n);return((s=a[a.length-1])==null?void 0:s.tokenIndex)??((i=e.tokens[e.tokens.length-1])==null?void 0:i.index)??0}function uu(e,n,a){var i;return n?`Profile ${n.name} is registered; run compatibility must pass before generation.`:((i=e.nlaCompatibility.profiles.find(r=>r.layer===(a==null?void 0:a.layer)))==null?void 0:i.reason)??`No registered NLA profile matches ${e.modelName} at this layer.`}function mu(e,n){var a;return((a=e.tokens.find(s=>s.index===n))==null?void 0:a.text)??""}function yn(e){return e.trim()||"space"}function Kt(e){return Math.abs(e)>0&&Math.abs(e)<.001?e.toExponential(2):e.toFixed(4)}function hu(e){return e<.001?e.toExponential(2):`${(e*100).toFixed(2)}%`}function pu({ariaLabel:e,label:n,value:a,direction:s,contextQuery:i="",disabled:r=!1,onChange:o,onSelectPreset:l}){const[c,d]=m.useState(!1),[h,f]=m.useState(0),[b,g]=m.useState(Uc),[y,u]=m.useState(!1),[k,j]=m.useState(""),[T,A]=m.useState("safety"),C=m.useRef(null),w=m.useRef(null),I=m.useId(),L=m.useMemo(()=>Oc(a,s,b,i),[i,s,b,a]),M=Math.min(h,Math.max(0,L.length-1)),q=L[M],X=c&&q?`${I}-option-${M}`:void 0,H=m.useMemo(()=>Vc(s,T,b),[T,s,b]);m.useEffect(()=>{const P=[...b,...Vn].find(S=>S.direction===s&&S.text===a&&S.category);P!=null&&P.category&&A(P.category)},[s,b,a]);function V(P){l?l(P):o(P.text),d(!1),f(0),window.requestAnimationFrame(()=>{var S;return(S=w.current)==null?void 0:S.focus()})}function oe(P){const S=b.filter(Z=>Z.id!==P);g(S),ri(S)}function de(){const P=k.trim();if(!P||!a.trim())return;const S=[...b,Kc(P,a,s,T)];g(S),ri(S),j(""),u(!1)}return t.jsxs("div",{ref:C,className:"preset-suggest",onBlur:P=>{P.currentTarget.contains(P.relatedTarget)||(d(!1),u(!1))},children:[t.jsxs("span",{children:[n,t.jsxs("button",{type:"button",className:"preset-suggest-save","aria-label":`Save current ${n} text as a preset`,disabled:r||!a.trim(),onClick:()=>u(P=>!P),children:[t.jsx(Pi,{size:12})," Save as preset"]})]}),t.jsxs("div",{className:"preset-suggest-categories",role:"group","aria-label":`${n} category`,children:[Fc.map(P=>t.jsx("button",{type:"button",className:T===P.id?"active":"","aria-pressed":T===P.id,disabled:r,onClick:()=>A(P.id),children:P.label},P.id)),t.jsxs("select",{"aria-label":`${n} direction preset`,value:"",disabled:r,onChange:P=>{const S=H.find(Z=>Z.id===P.target.value);S&&V(S)},children:[t.jsx("option",{value:"",children:"Choose direction..."}),H.map(P=>t.jsx("option",{value:P.id,children:P.label},P.id))]})]}),t.jsx("textarea",{ref:w,"aria-label":e,rows:3,value:a,disabled:r,role:"combobox","aria-expanded":c,"aria-controls":I,"aria-autocomplete":"list","aria-activedescendant":X,onFocus:()=>d(!0),onChange:P=>{o(P.target.value),c||d(!0),f(0)},onKeyDown:P=>{if(P.key==="Escape"){c&&(P.preventDefault(),d(!1));return}c&&(P.key==="ArrowDown"?(P.preventDefault(),f(Math.min(L.length-1,M+1))):P.key==="ArrowUp"?(P.preventDefault(),f(Math.max(0,M-1))):P.key==="Home"?(P.preventDefault(),f(0)):P.key==="End"?(P.preventDefault(),f(Math.max(0,L.length-1))):P.key==="Enter"&&q&&(P.preventDefault(),V(q)))}}),L.length>0&&t.jsx("div",{className:"preset-suggest-chips","aria-label":`${n} suggested presets`,children:L.slice(0,3).map(P=>t.jsx("button",{type:"button",disabled:r,title:P.text,onClick:()=>V(P),children:P.label},`chip-${P.id}`))}),y&&t.jsxs("div",{className:"preset-suggest-save-form",role:"group","aria-label":`Save ${n} preset`,children:[t.jsx("input",{"aria-label":"Preset label",placeholder:"Preset label",value:k,onChange:P=>j(P.target.value),onKeyDown:P=>{P.key==="Enter"&&(P.preventDefault(),de())}}),t.jsx("button",{type:"button",onClick:de,disabled:!k.trim(),children:"Save"})]}),c&&L.length>0&&t.jsx("div",{id:I,className:"preset-suggest-list",role:"listbox","aria-label":`${n} preset suggestions`,children:L.map((P,S)=>t.jsxs("button",{id:`${I}-option-${S}`,type:"button",role:"option","aria-selected":S===M,className:`preset-suggest-item ${S===M?"highlighted":""}`,"data-source":P.source,onMouseEnter:()=>f(S),onMouseDown:Z=>Z.preventDefault(),onClick:()=>V(P),children:[t.jsx("strong",{children:P.label}),t.jsx("em",{children:P.source==="user"?"custom":"builtin"}),t.jsx("small",{children:P.text}),P.source==="user"&&t.jsx("span",{role:"button","aria-label":`Delete preset ${P.label}`,className:"preset-suggest-delete",onClick:Z=>{Z.stopPropagation(),oe(P.id)},onKeyDown:Z=>{(Z.key==="Enter"||Z.key===" ")&&(Z.preventDefault(),Z.stopPropagation(),oe(P.id))},children:t.jsx(Je,{size:12})})]},P.id))})]})}function yu({modelName:e,response:n,selectedIndex:a,disabled:s=!1,onSelect:i,onTokensChange:r}){const[o,l]=m.useState([]),[c,d]=m.useState("idle");return m.useEffect(()=>{if(!n.trim()){l([]),r==null||r([]),d("idle");return}l([]),r==null||r([]),d("loading");const f=new AbortController,b=window.setTimeout(()=>{vd(e,n,f.signal).then(g=>{l(g.tokens),r==null||r(g.tokens),d("ready")}).catch(()=>{f.signal.aborted||(l([]),r==null||r([]),d("error"))})},180);return()=>{window.clearTimeout(b),f.abort()}},[e,r,n]),m.useEffect(()=>{o.length>0&&a>=o.length&&i(o.length-1)},[i,a,o.length]),t.jsxs("div",{className:"response-token-picker","aria-label":"Attribution target token","aria-busy":c==="loading",children:[t.jsxs("header",{children:[t.jsx("span",{children:"Target response token"}),o.length>0&&t.jsx("button",{type:"button",disabled:s,onClick:()=>i(0),children:"Reset to first"})]}),c==="loading"?t.jsx("div",{className:"response-token-picker-empty",role:"status",children:"Tokenizing response..."}):c==="error"?t.jsx("div",{className:"response-token-picker-empty is-error",role:"status",children:"Tokenizer unavailable. Check the local model worker."}):o.length>0?t.jsx("div",{className:"response-token-picker-list",role:"group","aria-label":"Response tokens",children:o.map((h,f)=>t.jsxs("button",{type:"button",className:f===a?"active":"","aria-pressed":f===a,disabled:s,title:`Target token ${f} · ${h.text||"space"} · ID ${h.tokenId}`,onClick:()=>i(f),children:[h.text||"space",t.jsxs("sub",{children:["T",f]})]},`${f}:${h.tokenId}`))}):t.jsx("div",{className:"response-token-picker-empty",role:"status",children:"Type or paste the model response to pick a target token."})]})}function fu({mode:e,run:n,remoteSummary:a,savedRun:s,suggestionQuery:i,onRunReady:r}){return e==="steering"?t.jsx(bu,{run:n,savedRun:s,suggestionQuery:i,onRunReady:r}):e==="attribution"?t.jsx(xu,{run:n,savedRun:s,onRunReady:r}):e==="patching"?t.jsx(gu,{run:n,savedRun:s,onRunReady:r}):e==="feature"?t.jsx(_u,{run:n,savedRun:s,onRunReady:r}):e==="explanation"?t.jsx(su,{run:n,savedRun:s,onRunReady:r}):t.jsx(Jc,{run:n,remoteSummary:a})}function gu({run:e,savedRun:n,onRunReady:a}){var K,N,v,ne,W,ee;const s=(n==null?void 0:n.patching)??e.patching,[i,r]=m.useState((s==null?void 0:s.corruptedPrompt)??e.prompt),[o,l]=m.useState((s==null?void 0:s.component)??"resid_post"),[c,d]=m.useState((s==null?void 0:s.layers)??Iu(e.layers)),[h,f]=m.useState((s==null?void 0:s.head)??0),[b,g]=m.useState((s==null?void 0:s.positions)??[]),y=m.useMemo(()=>Ua(e),[e]),[u,k]=m.useState((s==null?void 0:s.targetTokenId)??((K=y[0])==null?void 0:K.tokenId)??0),[j,T]=m.useState(null),[A,C]=m.useState(null),[w,I]=m.useState(n!=null&&n.patching?n:s?e:null),L=m.useMemo(()=>e.tokens.map(D=>D.tokenId),[e.tokens]),M=m.useCallback((D,$)=>{I(D),a(D,$)},[a]),q=qc(M),X=q.submitting||((N=q.job)==null?void 0:N.status)==="idle"||((v=q.job)==null?void 0:v.status)==="loading";m.useEffect(()=>{const D=new AbortController;T(null),C(null);const $=window.setTimeout(()=>{Rd({modelName:e.modelName,cleanPrompt:e.prompt,corruptedPrompt:i,cleanTokenIds:L,layers:e.layers,component:o,targetTokenId:u},D.signal).then(F=>{T(F),g(O=>{const E=O.filter(Y=>Y<F.cleanTokenCount).slice(0,8);return E.length>0?E:F.changedPositions.slice(0,8)})}).catch(F=>{D.signal.aborted||C(F instanceof Error?F.message:"Patching preflight failed.")})},260);return()=>{window.clearTimeout($),D.abort()}},[o,i,e.layers,e.modelName,e.prompt,L,u]);const H=c.length*b.length,V=Tu(e,c[0]??e.layers[0]??0),oe=!!(j!=null&&j.canSubmit&&H>0&&H<=64&&!X);m.useEffect(()=>{f(D=>Math.min(D,Math.max(0,V-1)))},[V]);function de(D){if(o==="z"){d([D]);return}d($=>$.includes(D)?$.length===1?$:$.filter(F=>F!==D):$.length>=8?$:[...$,D].sort((F,O)=>F-O))}function P(D){l(D),D==="z"&&d($=>[$[0]??e.layers[0]??0])}function S(D){g($=>$.includes(D)?$.length===1?$:$.filter(F=>F!==D):$.length>=8?$:[...$,D].sort((F,O)=>F-O))}function Z(){oe&&(I(null),q.submit({run:e,corruptedPrompt:i,component:o,layers:c,positions:b,...o==="z"?{head:h}:{},targetTokenId:u}))}return t.jsxs("section",{className:"chat-analysis-workbench chat-patching-workbench","aria-label":"Activation patching workbench",children:[t.jsxs("header",{className:"chat-workbench-heading",children:[t.jsx("span",{children:t.jsx(ot,{size:17})}),t.jsxs("div",{children:[t.jsx("h2",{children:"Activation patching"}),t.jsx("p",{children:"Clean activation replacement"})]}),t.jsx(Fa,{ready:!!(j!=null&&j.canSubmit),pending:!j&&!A})]}),t.jsxs("div",{className:"chat-patching-prompts",children:[t.jsxs("label",{className:"is-clean",children:[t.jsxs("span",{children:["Clean ",t.jsx("small",{children:"current run"})]}),t.jsx("textarea",{"aria-label":"Clean patching input",rows:4,value:e.prompt,readOnly:!0})]}),t.jsxs("label",{className:"is-corrupt",children:[t.jsxs("span",{children:["Corrupt ",t.jsx("small",{children:"editable"})]}),t.jsx("textarea",{"aria-label":"Corrupt patching input",rows:4,value:i,disabled:X,"aria-invalid":j&&!j.canSubmit?!0:void 0,onChange:D=>r(D.target.value)})]})]}),t.jsxs("div",{className:"chat-patching-controls",children:[t.jsxs("fieldset",{children:[t.jsx("legend",{children:"Activation site"}),t.jsx("div",{role:"group","aria-label":"Patching activation site",children:["resid_post","attn_out","z","mlp_out"].map(D=>t.jsx("button",{type:"button",className:o===D?"active":"","aria-pressed":o===D,disabled:X,onClick:()=>P(D),children:Au(D)},D))})]}),o==="z"&&t.jsxs("label",{children:[t.jsx("span",{children:"Attention head"}),t.jsx("select",{"aria-label":"Patching attention head",value:h,disabled:X,onChange:D=>f(Number(D.target.value)),children:Array.from({length:V},(D,$)=>t.jsxs("option",{value:$,children:["H",$]},$))})]}),t.jsxs("label",{children:[t.jsx("span",{children:"Tracked output token"}),t.jsx("select",{"aria-label":"Patching tracked output token",value:u,disabled:X,onChange:D=>k(Number(D.target.value)),children:y.map(D=>t.jsxs("option",{value:D.tokenId,children:[Ge(D.tokenText)," · #",D.tokenId]},D.tokenId))})]}),t.jsxs("div",{className:`chat-patching-alignment ${j!=null&&j.canSubmit?"ready":"blocked"}`,"aria-live":"polite",children:[t.jsx("strong",{children:j!=null&&j.canSubmit?"Aligned":j?"Needs alignment":"Checking"}),t.jsx("span",{children:j?`${j.cleanTokenCount} clean · ${j.corruptedTokenCount} corrupt · ${j.changedPositions.length} changed`:"Tokenizing both inputs"})]})]}),j!=null&&j.corruptedTokens.length?t.jsxs("div",{className:"chat-patching-positions",children:[t.jsxs("header",{children:[t.jsx("span",{children:"Patch positions"}),t.jsxs("small",{children:[b.length,"/8 selected"]})]}),t.jsx("div",{role:"group","aria-label":"Patching token positions",children:j.corruptedTokens.map(D=>{var $,F;return t.jsxs("button",{type:"button",className:`${D.changed?"changed":""} ${b.includes(D.index)?"active":""}`,"aria-label":`Patch token ${D.index}: ${Ge((($=e.tokens[D.index])==null?void 0:$.text)??"")} to ${Ge(D.text)}`,"aria-pressed":b.includes(D.index),disabled:X||!j.tokenCountMatches||!b.includes(D.index)&&b.length>=8,onClick:()=>S(D.index),children:[t.jsxs("small",{children:["T",D.index]}),t.jsx("span",{children:Ge(((F=e.tokens[D.index])==null?void 0:F.text)??"")}),t.jsx(Kn,{size:12}),t.jsx("b",{children:Ge(D.text)})]},D.index)})})]}):null,t.jsxs("div",{className:"chat-patching-layers",children:[t.jsxs("header",{children:[t.jsx("span",{children:"Layers"}),t.jsxs("small",{children:[o==="z"?`H${h} · one layer`:`${c.length}/8 selected`," · ",H," patches"]})]}),t.jsx("div",{role:"group","aria-label":"Patching layers",children:e.layers.map(D=>t.jsxs("button",{type:"button",className:c.includes(D)?"active":"","aria-pressed":c.includes(D),disabled:X||o!=="z"&&!c.includes(D)&&c.length>=8,onClick:()=>de(D),children:["L",D]},D))})]}),t.jsx(Bn,{running:X,disabled:!oe,runLabel:`Run ${H||""} patch${H===1?"":"es"}`.replace("  "," "),status:((ne=q.error)==null?void 0:ne.message)??A??((W=q.job)==null?void 0:W.detail)??(j==null?void 0:j.reason),progress:(ee=q.job)==null?void 0:ee.progress,onRun:Z,onCancel:()=>void q.cancel(),onReset:q.reset,failed:!!q.error}),(w==null?void 0:w.patching)&&t.jsx(ku,{experiment:w.patching})]})}function _u({run:e,savedRun:n,onRunReady:a}){var ee,D,$,F,O,E,Y,le,R,J,U,ce,te,ue,z;const s=((ee=n==null?void 0:n.intervention)==null?void 0:ee.mode)==="sae_feature"?n.intervention:((D=e.intervention)==null?void 0:D.mode)==="sae_feature"?e.intervention:void 0,[i,r]=m.useState([]),[o,l]=m.useState(!1),[c,d]=m.useState(null),[h,f]=m.useState(""),[b,g]=m.useState((($=s==null?void 0:s.feature)==null?void 0:$.featureIndex)??0),[y,u]=m.useState(((F=s==null?void 0:s.feature)==null?void 0:F.operation)==="ablate"?"ablate":"add"),[k,j]=m.useState((s==null?void 0:s.scale)??5),[T,A]=m.useState((s==null?void 0:s.positionStart)??0),[C,w]=m.useState((s==null?void 0:s.positionEnd)??e.tokens.length),I=m.useMemo(()=>Ua(e),[e]),[L,M]=m.useState((s==null?void 0:s.targetTokenId)??((O=I[0])==null?void 0:O.tokenId)??0),[q,X]=m.useState(null),[H,V]=m.useState(null),[oe,de]=m.useState(null),[P,S]=m.useState(((E=n==null?void 0:n.intervention)==null?void 0:E.mode)==="sae_feature"?n:null),Z=m.useCallback((re,pe)=>{S(re),a(re,pe)},[a]),K=Mr(Z),N=K.submitting||((Y=K.job)==null?void 0:Y.status)==="idle"||((le=K.job)==null?void 0:le.status)==="loading",v=i.find(re=>re.id===h)??i.find(re=>re.layer===12)??i[0];m.useEffect(()=>{const re=new AbortController;return r([]),l(!1),d(null),$d(e.modelName,re.signal).then(pe=>{r(pe);const ae=pe.find(G=>{var me;return G.saeId===((me=s==null?void 0:s.feature)==null?void 0:me.saeId)})??pe.find(G=>G.layer===12)??pe[0];f((ae==null?void 0:ae.id)??""),l(!0)}).catch(pe=>{re.signal.aborted||(d(pe instanceof Error?pe.message:"SAE profiles failed to load."),l(!0))}),()=>re.abort()},[(R=s==null?void 0:s.feature)==null?void 0:R.saeId,e.modelName]),m.useEffect(()=>{v&&b>=v.width&&g(0)},[b,v]),m.useEffect(()=>{if(!v){X(null),de(null);return}const re=new AbortController;X(null),V(null);const pe=window.setTimeout(()=>{gr({mode:"sae_feature",modelName:e.modelName,promptTokenCount:e.tokens.length,availableLayers:e.layers,layer:v.layer,component:v.component,positionStart:T,positionEnd:C,targetTokenId:L,saeRelease:v.release,saeId:v.saeId,featureIndex:b,saeOperation:y,desiredPrompt:"Enhance selected SAE feature",undesiredPrompt:"Suppress selected SAE feature"},re.signal).then(X).catch(ve=>{re.signal.aborted||V(ve instanceof Error?ve.message:"SAE preflight failed.")})},180);return()=>{window.clearTimeout(pe),re.abort()}},[b,y,C,T,e.layers,e.modelName,e.tokens.length,v,L]),m.useEffect(()=>{if(!v){de(null);return}const re=new AbortController;de(null);const pe=window.setTimeout(()=>{Ed(e.modelName,v.layer,b,re.signal).then(de).catch(()=>{re.signal.aborted||de(null)})},180);return()=>{window.clearTimeout(pe),re.abort()}},[b,e.modelName,v]);function ne(re,pe){const ve=Math.max(0,Math.min(e.tokens.length-1,re));A(ve),w(Math.max(ve+1,Math.min(e.tokens.length,pe)))}function W(){if(!(q!=null&&q.canSubmit)||N||!v)return;S(null);const re={run:e,mode:"sae_feature",desiredPrompt:"Enhance selected SAE feature",undesiredPrompt:"Suppress selected SAE feature",layer:v.layer,component:v.component,saeRelease:v.release,saeId:v.saeId,featureIndex:b,saeOperation:y,scale:k,positionStart:T,positionEnd:C,targetTokenId:L,seed:0,maxNewTokens:32,temperature:0};K.submit(re)}return o&&i.length===0?t.jsxs("section",{className:"chat-analysis-workbench chat-feature-workbench","aria-label":"SAE feature intervention workbench",children:[t.jsxs("header",{className:"chat-workbench-heading",children:[t.jsx("span",{children:t.jsx(Ve,{size:17})}),t.jsxs("div",{children:[t.jsx("h2",{children:"Gemma Scope SAE"}),t.jsxs("p",{children:["No compatible SAE for ",e.modelName]})]})]}),t.jsxs("p",{className:"chat-sae-empty",children:["Select ",t.jsx("b",{children:"google/gemma-3-270m-it"})," for a new chat run."]})]}):t.jsxs("section",{className:"chat-analysis-workbench chat-feature-workbench","aria-label":"SAE feature intervention workbench",children:[t.jsxs("header",{className:"chat-workbench-heading",children:[t.jsx("span",{children:t.jsx(Ve,{size:17})}),t.jsxs("div",{children:[t.jsx("h2",{children:"Gemma Scope SAE"}),t.jsx("p",{children:"Sparse feature intervention · residual stream"})]}),t.jsx(Fa,{ready:!!(q!=null&&q.canSubmit),pending:!q&&!H})]}),t.jsxs("div",{className:"chat-feature-controls",children:[t.jsxs("label",{className:"chat-sae-profile",children:[t.jsx("span",{children:"SAE checkpoint"}),t.jsx("select",{"aria-label":"SAE checkpoint",value:(v==null?void 0:v.id)??"",disabled:N||i.length===0,onChange:re=>f(re.target.value),children:i.map(re=>t.jsxs("option",{value:re.id,children:["L",re.layer," · 16k · L0 small"]},re.id))})]}),t.jsxs("label",{children:[t.jsx("span",{children:"Feature"}),t.jsx("input",{"aria-label":"SAE feature index",type:"number",min:0,max:((v==null?void 0:v.width)??1)-1,value:b,disabled:N||!v,onChange:re=>g(Math.max(0,Number(re.target.value)||0))})]}),t.jsxs("label",{children:[t.jsx("span",{children:"Tracked output token"}),t.jsx("select",{"aria-label":"SAE tracked output token",value:L,disabled:N,onChange:re=>M(Number(re.target.value)),children:I.map(re=>t.jsxs("option",{value:re.tokenId,children:[Ge(re.tokenText)," · #",re.tokenId]},re.tokenId))})]}),t.jsxs("label",{className:"chat-feature-strength",children:[t.jsxs("span",{children:["Feature delta ",t.jsx("b",{children:y==="ablate"?"zero":mt(k)})]}),t.jsx("input",{"aria-label":"SAE feature delta",type:"range",min:-20,max:20,step:.5,value:k,disabled:N||y==="ablate",onChange:re=>j(Number(re.target.value))})]})]}),t.jsxs("div",{className:"chat-feature-operations",role:"group","aria-label":"SAE feature operation",children:[t.jsx("button",{type:"button",className:y==="add"?"active":"","aria-pressed":y==="add",disabled:N,onClick:()=>u("add"),children:"Add activation"}),t.jsx("button",{type:"button",className:y==="ablate"?"active":"","aria-pressed":y==="ablate",disabled:N,onClick:()=>u("ablate"),children:"Ablate feature"})]}),t.jsxs("div",{className:"chat-token-range",children:[t.jsxs("header",{children:[t.jsx("span",{children:"Apply to"}),t.jsxs("div",{children:[t.jsx("button",{className:T===0&&C===e.tokens.length?"active":"","aria-pressed":T===0&&C===e.tokens.length,disabled:N,onClick:()=>ne(0,e.tokens.length),children:"Entire input"}),t.jsx("button",{className:T===e.tokens.length-1&&C===e.tokens.length?"active":"","aria-pressed":T===e.tokens.length-1&&C===e.tokens.length,disabled:N,onClick:()=>ne(e.tokens.length-1,e.tokens.length),children:"Last token"})]}),t.jsxs("small",{children:["T",T,"–T",C-1]})]}),t.jsx("div",{"aria-label":"SAE intervention token range",children:e.tokens.map(re=>t.jsx("button",{className:re.index>=T&&re.index<C?"active":"","aria-pressed":re.index>=T&&re.index<C,disabled:N,onClick:()=>ne(re.index,re.index+1),children:Ge(re.text)},re.index))})]}),t.jsxs("div",{className:"chat-feature-selected",children:[t.jsxs("div",{className:"chat-feature-selected-id",children:[t.jsxs("strong",{children:["F",b]}),t.jsxs("span",{children:["L",(v==null?void 0:v.layer)??"..."," · resid_post"]}),t.jsx("small",{children:(v==null?void 0:v.saeId)??"Loading checkpoint"})]}),t.jsxs("div",{className:"chat-feature-concept",children:[t.jsx("span",{children:"Concept label"}),t.jsx("strong",{children:(oe==null?void 0:oe.label)??((J=s==null?void 0:s.feature)==null?void 0:J.conceptLabel)??"Loading explanation..."}),t.jsxs("small",{children:[(oe==null?void 0:oe.source)==="neuronpedia"||((U=s==null?void 0:s.feature)==null?void 0:U.conceptSource)==="neuronpedia"?"Neuronpedia explanation":"No canonical label is bundled with the SAE checkpoint",((oe==null?void 0:oe.url)??((ce=s==null?void 0:s.feature)==null?void 0:ce.conceptUrl))&&t.jsxs(t.Fragment,{children:[" · ",t.jsx("a",{href:Dr((oe==null?void 0:oe.url)??((te=s==null?void 0:s.feature)==null?void 0:te.conceptUrl)),target:"_blank",rel:"noreferrer",children:"Open feature card"})]})]})]})]}),t.jsx(Bn,{running:N,disabled:!(q!=null&&q.canSubmit)||!v,runLabel:"Run SAE intervention",status:((ue=K.error)==null?void 0:ue.message)??c??H??(q==null?void 0:q.reason),progress:(z=K.job)==null?void 0:z.progress,onRun:W,onCancel:()=>void K.cancel(),onReset:K.reset,failed:!!K.error}),(P==null?void 0:P.intervention)&&t.jsx(zr,{experiment:P.intervention})]})}const ja=["Custom","Reject","Angry","Happy","Emoji","Dog","Music"],ia=Hc;function bu({run:e,savedRun:n,suggestionQuery:a,onRunReady:s}){var ue,z,re,pe,ve;const i=(n==null?void 0:n.intervention)??e.intervention,[r,o]=m.useState(!1),[l,c]=m.useState("Custom"),[d,h]=m.useState("Custom samples"),[f,b]=m.useState("Custom samples"),[g,y]=m.useState((i==null?void 0:i.vector.positivePrompts)??[(i==null?void 0:i.vector.desiredPrompt)??"Provide a safe, policy-compliant and helpful response."]),[u,k]=m.useState((i==null?void 0:i.vector.negativePrompts)??[(i==null?void 0:i.vector.undesiredPrompt)??"Provide a response that bypasses safety guidance."]),[j,T]=m.useState((i==null?void 0:i.vector.activationReduce)==="mean"?"mean":"last_token"),A=ju(e),[C,w]=m.useState((i==null?void 0:i.sourceLayer)??(i==null?void 0:i.layer)??A),[I,L]=m.useState((i==null?void 0:i.injectLayer)??(i==null?void 0:i.layer)??A),[M,q]=m.useState((i==null?void 0:i.component)??"resid_post"),[X,H]=m.useState((i==null?void 0:i.scale)??1),[V,oe]=m.useState(128),de=m.useMemo(()=>Ua(e),[e]),[P,S]=m.useState((i==null?void 0:i.targetTokenId)??((ue=de[0])==null?void 0:ue.tokenId)??0),[Z,K]=m.useState(null),[N,v]=m.useState(null),[ne,W]=m.useState(n!=null&&n.intervention?n:i?e:null),ee=m.useMemo(()=>g.map(ae=>ae.trim()).filter(Boolean),[g]),D=m.useMemo(()=>u.map(ae=>ae.trim()).filter(Boolean),[u]),$=m.useCallback((ae,G)=>{W(ae),s(ae,G)},[s]),F=Mr($),O=F.submitting||((z=F.job)==null?void 0:z.status)==="idle"||((re=F.job)==null?void 0:re.status)==="loading";m.useEffect(()=>{const ae=new AbortController;if(K(null),v(null),ee.length===0||D.length===0)return v("Add at least one non-empty sample to each direction."),()=>ae.abort();const G=window.setTimeout(()=>{gr({modelName:e.modelName,promptTokenCount:e.tokens.length,availableLayers:e.layers,layer:I,sourceLayer:C,injectLayer:I,component:M,positionStart:0,positionEnd:e.tokens.length,targetTokenId:P,positivePrompts:ee,negativePrompts:D,activationReduce:j},ae.signal).then(K).catch(me=>{ae.signal.aborted||v(me instanceof Error?me.message:"Steering preflight failed.")})},220);return()=>{window.clearTimeout(G),ae.abort()}},[j,M,I,D,ee,e.layers,e.modelName,e.tokens.length,C,P]);const E=!!(Z!=null&&Z.canSubmit&&!O);function Y(ae){if(c(ae),ae==="Custom"){h("Custom samples"),b("Custom samples");return}y([...ia[ae].positive]),k([...ia[ae].negative]),h(`${ae} positive batch`),b(`${ae} negative batch`)}function le(ae,G){if(ae==="positive"?h(G):b(G),G==="Custom samples")return;const me=ja.find(be=>G.startsWith(`${be} `));if(!me||me==="Custom")return;const he=[...ia[me][ae]];ae==="positive"?y(he):k(he)}function R(ae,G){const me=he=>he.length>0?[G,...he.slice(1)]:[G];c("Custom"),ae==="positive"?(h("Custom samples"),y(me)):(b("Custom samples"),k(me))}function J(ae){R(ae.direction==="toward"?"positive":"negative",ae.text);const G=Bc(ae);G&&R(G.direction==="toward"?"positive":"negative",G.text)}function U(){E&&(W(null),F.submit({run:e,desiredPrompt:ee[0],undesiredPrompt:D[0],positivePrompts:ee,negativePrompts:D,activationReduce:j,layer:I,sourceLayer:C,injectLayer:I,component:M,scale:X,positionStart:0,positionEnd:e.tokens.length,targetTokenId:P,seed:0,maxNewTokens:V,temperature:0}))}const ce=t.jsxs("label",{className:"chat-steering-concept",children:[t.jsx("span",{children:"Steering concept"}),t.jsx("select",{"aria-label":"Steering concept",value:l,disabled:O,onChange:ae=>Y(ae.target.value),children:ja.map(ae=>t.jsx("option",{value:ae,children:ae},ae))})]}),te=t.jsxs("button",{type:"button",className:"chat-steering-advanced-toggle","aria-expanded":r,onClick:()=>o(ae=>!ae),children:[t.jsx(vt,{size:16}),r?"Hide advanced settings":"Advanced settings",r?t.jsx(Wi,{size:15}):t.jsx(Fn,{size:15})]});return t.jsxs("section",{className:`chat-analysis-workbench chat-steering-workbench ${r?"is-expanded":"is-compact"}`,"aria-label":"Steering workbench",children:[r?t.jsxs(t.Fragment,{children:[t.jsxs("div",{className:"chat-steering-expanded-top",children:[ce,te]}),t.jsxs("div",{className:"chat-steering-references",children:[t.jsx(ui,{direction:"positive",prompts:g,preset:d,running:O,suggestionQuery:a,onPreset:le,onSelectPreset:J,onChange:y}),t.jsx(ui,{direction:"negative",prompts:u,preset:f,running:O,suggestionQuery:a,onPreset:le,onSelectPreset:J,onChange:k})]}),t.jsxs("div",{className:"chat-steering-controls",children:[t.jsxs("label",{children:[t.jsx("span",{children:"Sample activation"}),t.jsxs("select",{"aria-label":"Steering sample activation",value:j,disabled:O,onChange:ae=>T(ae.target.value),children:[t.jsx("option",{value:"last_token",children:"Last token"}),t.jsx("option",{value:"mean",children:"Token average"})]})]}),t.jsxs("label",{children:[t.jsx("span",{children:"Source layer"}),t.jsx("select",{"aria-label":"Steering source layer",value:C,disabled:O,onChange:ae=>w(Number(ae.target.value)),children:e.layers.map(ae=>t.jsxs("option",{value:ae,children:["L",ae]},ae))})]}),t.jsxs("label",{children:[t.jsx("span",{children:"Inject layer"}),t.jsx("select",{"aria-label":"Steering inject layer",value:I,disabled:O,onChange:ae=>L(Number(ae.target.value)),children:e.layers.map(ae=>t.jsxs("option",{value:ae,children:["L",ae]},ae))})]}),t.jsxs("label",{children:[t.jsx("span",{children:"Component"}),t.jsxs("select",{"aria-label":"Steering activation site",value:M,disabled:O,onChange:ae=>q(ae.target.value),children:[t.jsx("option",{value:"resid_post",children:"Residual stream"}),t.jsx("option",{value:"attn_out",children:"Attention output"}),t.jsx("option",{value:"mlp_out",children:"MLP output"})]})]}),t.jsxs("label",{children:[t.jsx("span",{children:"Objective"}),t.jsx("select",{"aria-label":"Steering diagnostic token",value:P,disabled:O,onChange:ae=>S(Number(ae.target.value)),children:de.map(ae=>t.jsxs("option",{value:ae.tokenId,children:[Ge(ae.tokenText)," · #",ae.tokenId]},ae.tokenId))})]}),t.jsxs("label",{className:"chat-steering-strength",children:[t.jsxs("span",{children:["Strength ",t.jsx("b",{children:X.toFixed(1)})]}),t.jsx("input",{"aria-label":"Steering strength",type:"range",min:0,max:2.5,step:.1,value:X,disabled:O,onChange:ae=>H(Number(ae.target.value))})]}),t.jsxs("label",{children:[t.jsx("span",{children:"Output tokens"}),t.jsx("input",{"aria-label":"Steering output tokens",type:"number",min:1,max:128,step:1,value:V,disabled:O,onChange:ae=>oe(Math.max(1,Math.min(128,Number(ae.target.value)||1)))})]})]})]}):t.jsxs("div",{className:"chat-steering-quick-controls",children:[ce,t.jsxs("label",{className:"chat-steering-strength",children:[t.jsxs("span",{children:["Strength ",t.jsx("b",{children:X.toFixed(1)})]}),t.jsx("input",{"aria-label":"Steering strength",type:"range",min:0,max:2.5,step:.1,value:X,disabled:O,onChange:ae=>H(Number(ae.target.value))})]}),te]}),t.jsx(Bn,{running:O,disabled:!E,runLabel:"Run steering",status:((pe=F.error)==null?void 0:pe.message)??N??(Z==null?void 0:Z.reason),progress:(ve=F.job)==null?void 0:ve.progress,onRun:U,onCancel:()=>void F.cancel(),onReset:F.reset,failed:!!F.error}),(ne==null?void 0:ne.intervention)&&t.jsx(zr,{experiment:ne.intervention})]})}function ui({direction:e,prompts:n,preset:a,running:s,suggestionQuery:i,onPreset:r,onSelectPreset:o,onChange:l}){const c=e==="positive"?"Steer toward":"Steer away from",d=(f,b)=>l(n.map((g,y)=>y===f?b:g)),h=f=>{n.length!==1&&l(n.filter((b,g)=>g!==f))};return t.jsxs("section",{className:"chat-steering-samples",children:[t.jsxs("header",{children:[t.jsxs("strong",{children:[c," samples"]}),t.jsx("span",{children:n.length})]}),t.jsxs("label",{className:"chat-steering-preset",children:[t.jsx("span",{children:"Sample preset"}),t.jsxs("select",{"aria-label":`${c} sample preset`,value:a,disabled:s,onChange:f=>r(e,f.target.value),children:[t.jsx("option",{value:"Custom samples",children:"Custom samples"}),ja.filter(f=>f!=="Custom").map(f=>t.jsxs("option",{value:`${f} ${e} batch`,children:[f," ",e," batch"]},f))]})]}),t.jsxs("div",{className:"chat-steering-sample-list",children:[t.jsx(pu,{ariaLabel:e==="positive"?"Steering desired behavior":"Steering undesired behavior",label:c,direction:e==="positive"?"toward":"away",contextQuery:i,value:n[0]??"",disabled:s,onChange:f=>d(0,f),onSelectPreset:o}),n.slice(1).map((f,b)=>{const g=b+1;return t.jsxs("label",{children:[t.jsxs("span",{children:["Sample ",g+1]}),t.jsxs("div",{children:[t.jsx("textarea",{"aria-label":`${c} sample ${g+1}`,value:f,disabled:s,onChange:y=>d(g,y.target.value)}),t.jsx("button",{type:"button","aria-label":`Remove ${c.toLowerCase()} sample ${g+1}`,disabled:s||n.length===1,onClick:()=>h(g),children:t.jsx(_n,{size:15})})]})]},g)})]}),t.jsxs("button",{type:"button",className:"chat-steering-add-sample",disabled:s||n.length>=64,onClick:()=>l([...n,""]),children:[t.jsx(Pi,{size:15}),"Add sample"]})]})}function xu({run:e,savedRun:n,onRunReady:a}){var L,M,q,X,H;const[s,i]=m.useState(()=>Su(e)),[r,o]=m.useState(()=>Cu(n??e)??0),[l,c]=m.useState([]),[d,h]=m.useState("pad_token"),[f,b]=m.useState(32),g=n??e,y=g.attributionMethods.find(V=>V.id==="integrated_gradients"&&V.available),[u,k]=m.useState(y?g:null),j=m.useCallback((V,oe)=>{k(V),a(V,oe)},[a]),T=Yc(j),A=T.submitting||((L=T.job)==null?void 0:L.status)==="idle"||((M=T.job)==null?void 0:M.status)==="loading",C=m.useCallback(V=>c(V),[]);function w(){!s.trim()||A||(k(null),T.submit({run:e,response:s,objective:"response_token_logit",targetResponseIndex:r,baseline:d,nSteps:f}))}const I=u==null?void 0:u.attributionMethods.find(V=>V.id==="integrated_gradients"&&V.available);return t.jsxs("section",{className:"chat-analysis-workbench","aria-label":"Input attribution workbench",children:[t.jsxs("header",{className:"chat-workbench-heading",children:[t.jsx("span",{children:t.jsx(La,{size:17})}),t.jsxs("div",{children:[t.jsx("h2",{children:"Input attribution"}),t.jsx("p",{children:"Show which input tokens support or suppress the selected output token"})]}),t.jsx(Fa,{ready:!!I,pending:!1})]}),t.jsxs("label",{className:"chat-attribution-response",children:[t.jsx("span",{children:"Model response"}),t.jsx("textarea",{"aria-label":"Attribution response",rows:3,value:s,disabled:A,placeholder:"Response containing the target token",onChange:V=>i(V.target.value)})]}),t.jsxs("div",{className:"chat-attribution-controls",children:[t.jsx(yu,{modelName:e.modelName,response:s,selectedIndex:r,disabled:A,onSelect:o,onTokensChange:C}),t.jsxs("fieldset",{children:[t.jsx("legend",{children:"Baseline"}),t.jsx("button",{type:"button",className:d==="pad_token"?"active":"","aria-pressed":d==="pad_token",disabled:A,onClick:()=>h("pad_token"),children:"Pad token"}),t.jsx("button",{type:"button",className:d==="zero_token_id"?"active":"","aria-pressed":d==="zero_token_id",disabled:A,onClick:()=>h("zero_token_id"),children:"Token ID 0"})]}),t.jsxs("label",{children:[t.jsx("span",{children:"Integration steps"}),t.jsx("select",{"aria-label":"Attribution integration steps",value:f,disabled:A,onChange:V=>b(Number(V.target.value)),children:[8,16,32,64].map(V=>t.jsx("option",{value:V,children:V},V))})]})]}),t.jsx(Bn,{running:A,disabled:!s.trim()||l.length===0||A,runLabel:"Run attribution",status:((q=T.error)==null?void 0:q.message)??((X=T.job)==null?void 0:X.detail),progress:(H=T.job)==null?void 0:H.progress,onRun:w,onCancel:()=>void T.cancel(),onReset:T.reset,failed:!!T.error}),I&&t.jsx(wu,{method:I,run:u,targetIndex:r,responseTokens:l})]})}function Bn({running:e,disabled:n,runLabel:a,status:s,progress:i,failed:r,onRun:o,onCancel:l,onReset:c}){return t.jsxs("div",{className:"chat-workbench-actions",children:[t.jsxs("div",{className:r?"failed":e?"running":"","aria-live":"polite",children:[r?t.jsx(Et,{size:15}):e?t.jsx(Wt,{size:15}):t.jsx(Xe,{size:15}),t.jsx("span",{children:s??(n?"Complete the required fields.":"Ready to run.")}),e&&t.jsxs("small",{children:[i??0,"%"]})]}),r&&t.jsx("button",{className:"icon-action","aria-label":"Reset analysis job",title:"Reset",onClick:c,children:t.jsx(qn,{size:15})}),t.jsxs("button",{className:"chat-workbench-run",disabled:n&&!e,onClick:e?l:o,children:[e?t.jsx(Bt,{size:14}):t.jsx(Un,{size:14}),e?"Cancel":a]})]})}function Fa({ready:e,pending:n}){return t.jsxs("span",{className:`chat-workbench-status ${e?"ready":n?"pending":"idle"}`,children:[t.jsx("i",{}),e?"ready":n?"checking":"not run"]})}function zr({experiment:e}){var c,d,h,f,b;const n=e.mode==="neuron"||e.mode==="sae_feature",a=e.mode==="sae_feature",s=!n&&e.vector.normalized,i=e.sourceLayer!==void 0||e.injectLayer!==void 0?`source L${e.sourceLayer??e.layer} → inject L${e.injectLayer??e.layer}`:`L${e.layer}`,r=e.deltas.maxAbsLogit,o=e.deltas.firstDivergenceIndex,l=e.vector.relativeStrength;return t.jsxs("section",{className:"chat-steering-result","aria-label":"Steering comparison",children:[t.jsxs("header",{children:[t.jsxs("div",{children:[n?t.jsx(Ve,{size:16}):t.jsx(ot,{size:16}),t.jsx("strong",{children:a?"SAE feature comparison":n?"Neuron intervention comparison":"Steering generation comparison"})]}),t.jsxs("span",{children:[n&&e.feature?`${e.feature.id} · ${e.feature.operation}`:`${i} · ${e.component}`,a&&((c=e.feature)==null?void 0:c.operation)==="ablate"?"":` · factor ${mt(e.scale)}`]})]}),a&&e.feature&&t.jsxs("div",{className:"chat-sae-concept-result",children:[t.jsx("span",{children:"Concept label"}),t.jsx("strong",{children:e.feature.conceptLabel??e.feature.label}),t.jsxs("small",{children:[e.feature.conceptSource==="neuronpedia"?"External explanation metadata; the SAE weights only contain the numeric feature index.":"No canonical explanation was bundled; this is an index-only feature.",e.feature.conceptUrl&&t.jsxs(t.Fragment,{children:[" ",t.jsx("a",{href:Dr(e.feature.conceptUrl),target:"_blank",rel:"noreferrer",children:"Open feature card"})]})]}),((((d=e.feature.positiveTokens)==null?void 0:d.length)??0)>0||(((h=e.feature.negativeTokens)==null?void 0:h.length)??0)>0)&&t.jsxs("div",{className:"chat-sae-concept-evidence",children:[(f=e.feature.positiveTokens)!=null&&f.length?t.jsxs("span",{children:[t.jsx("b",{children:"Positive logits"}),e.feature.positiveTokens.slice(0,5).join(" · ")]}):null,(b=e.feature.negativeTokens)!=null&&b.length?t.jsxs("span",{children:[t.jsx("b",{children:"Negative logits"}),e.feature.negativeTokens.slice(0,5).join(" · ")]}):null]})]}),t.jsxs("div",{className:"chat-steering-output",children:[t.jsxs("article",{className:"is-original",children:[t.jsx("span",{children:"Original"}),t.jsx("p",{children:e.original.text||"No continuation"}),t.jsxs("small",{children:["Diagnostic token logit ",e.original.targetLogit.toFixed(3)]})]}),t.jsxs("div",{className:"chat-steering-transition",title:"Diagnostic token logit delta",children:[t.jsx(Kn,{size:20}),t.jsx("span",{children:mt(e.deltas.targetLogit)})]}),t.jsxs("article",{className:"is-steered",children:[t.jsx("span",{children:"Steered"}),t.jsx("p",{children:e.steered.text||"No continuation"}),t.jsxs("small",{children:["Diagnostic token logit ",e.steered.targetLogit.toFixed(3)]})]})]}),t.jsx("p",{className:`chat-steering-verdict ${e.deltas.generationChanged?"changed":"unchanged"}`,children:s?"This saved result used legacy unit-vector steering. Run steering again to use the calibrated contrastive algorithm.":e.deltas.generationChanged?`Generation diverged at output token ${o??0}.`:r&&r>0?"The intervention changed next-token logits, but not enough to change greedy decoding in this window. Increase strength or choose another layer.":"No measurable intervention effect was recorded. Check the selected layer and activation site."}),t.jsxs("footer",{children:[t.jsxs("span",{children:[t.jsx("b",{children:mt(e.deltas.targetLogit)})," diagnostic logit"]}),t.jsxs("span",{children:[t.jsx("b",{children:e.deltas.tokenEditDistance})," token edits"]}),r!==void 0&&t.jsxs("span",{children:[t.jsx("b",{children:r.toFixed(3)})," max vocabulary change"]}),l!==void 0&&t.jsxs("span",{children:[t.jsxs("b",{children:[(l*100).toFixed(1),"%"]})," relative injection"]})]})]})}function wu({method:e,run:n,targetIndex:a,responseTokens:s}){var b,g;const i=((b=e.rows[e.rows.length-1])==null?void 0:b.values)??[],r=Math.max(1e-8,...i.map(y=>Math.abs(y))),o=n.tokens.map((y,u)=>({token:y,value:i[u]??0})).filter(y=>y.value>0).sort((y,u)=>u.value-y.value).slice(0,5),l=n.tokens.map((y,u)=>({token:y,value:i[u]??0})).filter(y=>y.value<0).sort((y,u)=>y.value-u.value).slice(0,5),c=(g=n.metadata)==null?void 0:g.attributionJobs,d=Array.isArray(c)?c[c.length-1]:void 0,h=a!==void 0?s[a]:void 0,f=d&&typeof d=="object"&&"targetTokenText"in d?String(d.targetTokenText):h==null?void 0:h.text;return t.jsxs("section",{className:"chat-attribution-result","aria-label":"Input attribution result",children:[t.jsxs("header",{children:[t.jsxs("div",{children:[t.jsx(La,{size:16}),t.jsx("strong",{children:"Token contributions"})]}),(h||f)&&t.jsxs("span",{className:"chat-attribution-target",title:"Selected target token",children:["Target ",t.jsxs("b",{children:["T",a??0]})," · ",Ge(f??"")]}),t.jsxs("span",{children:[t.jsx("i",{className:"positive"})," supports target ",t.jsx("i",{className:"negative"})," suppresses target"]})]}),t.jsx("div",{className:"chat-attribution-tokens",children:n.tokens.map((y,u)=>{const k=i[u]??0,j=Math.abs(k)/r;return t.jsx("span",{className:k<0?"negative":"positive",style:{"--strength":j},title:`T${y.index} · ${k.toFixed(6)}`,children:Ge(y.text)},y.index)})}),t.jsxs("footer",{className:"chat-attribution-rankings",children:[t.jsxs("section",{"aria-label":"Positive attribution tokens",children:[t.jsxs("header",{children:[t.jsx("i",{className:"positive"}),t.jsx("strong",{children:"Supports target"})]}),o.length?o.map(({token:y,value:u})=>t.jsxs("span",{children:[t.jsxs("small",{children:["T",y.index]}),t.jsx("b",{children:Ge(y.text)}),t.jsx("em",{className:"positive-value",children:mt(u)})]},y.index)):t.jsx("p",{children:"No positive token contribution."})]}),t.jsxs("section",{"aria-label":"Negative attribution tokens",children:[t.jsxs("header",{children:[t.jsx("i",{className:"negative"}),t.jsx("strong",{children:"Suppresses target"})]}),l.length?l.map(({token:y,value:u})=>t.jsxs("span",{children:[t.jsxs("small",{children:["T",y.index]}),t.jsx("b",{children:Ge(y.text)}),t.jsx("em",{className:"negative-value",children:mt(u)})]},y.index)):t.jsx("p",{children:"No negative token contribution."})]})]})]})}function ku({experiment:e}){const n=[...e.cells].sort((r,o)=>Sn(o)-Sn(r))[0],[a,s]=m.useState(n),i=Math.max(1e-8,...e.cells.map(Sn));return t.jsxs("section",{className:"chat-patching-result","aria-label":"Activation patching result",children:[t.jsxs("header",{children:[t.jsxs("div",{children:[t.jsx(ot,{size:16}),t.jsx("strong",{children:"Causal recovery"})]}),t.jsxs("span",{children:[e.component==="z"?`L${e.layers[0]}H${e.head} · `:"","Target ",Ge(e.targetTokenText)," · #",e.targetTokenId]})]}),t.jsxs("div",{className:"chat-patching-baselines",children:[t.jsxs("span",{className:"clean",children:[t.jsx("small",{children:"Clean logit"}),t.jsx("b",{children:e.cleanScore.toFixed(3)})]}),t.jsxs("span",{className:"corrupt",children:[t.jsx("small",{children:"Corrupt logit"}),t.jsx("b",{children:e.corruptedScore.toFixed(3)})]}),t.jsxs("span",{children:[t.jsx("small",{children:"Clean-corrupt gap"}),t.jsx("b",{children:mt(e.denominator)})]})]}),t.jsx("div",{className:"chat-patching-matrix",role:"region","aria-label":"Patching recovery matrix",children:t.jsxs("table",{children:[t.jsx("thead",{children:t.jsxs("tr",{children:[t.jsx("th",{children:"Layer"}),e.positions.map(r=>{var o;return t.jsxs("th",{title:(o=e.corruptedTokens[r])==null?void 0:o.text,children:["T",r]},r)})]})}),t.jsx("tbody",{children:e.layers.map(r=>t.jsxs("tr",{children:[t.jsxs("th",{children:["L",r]}),e.positions.map(o=>{const l=e.cells.find(f=>f.layer===r&&f.tokenIndex===o),c=l?l.recoveryPercentage:null,d=l?Sn(l)/i:0,h=(a==null?void 0:a.layer)===r&&(a==null?void 0:a.tokenIndex)===o;return t.jsx("td",{children:l?t.jsx("button",{type:"button",className:`${(c??l.causalEffect)<0?"negative":"positive"} ${h?"active":""}`,style:{"--strength":d},"aria-label":`Layer ${r}, token ${o}, ${c===null?`${mt(l.causalEffect)} causal effect`:`${c.toFixed(1)} percent recovery`}`,"aria-pressed":h,onClick:()=>s(l),children:c===null?mt(l.causalEffect):`${c.toFixed(1)}%`}):"—"},o)})]},r))})]})}),a&&t.jsxs("footer",{"aria-label":"Selected patch result",children:[t.jsxs("strong",{children:["L",a.layer,e.component==="z"?`H${e.head}`:""," · T",a.tokenIndex]}),t.jsxs("span",{children:["Patched logit ",t.jsx("b",{children:a.patchedScore.toFixed(3)})]}),t.jsxs("span",{children:["Causal effect ",t.jsx("b",{children:mt(a.causalEffect)})]}),t.jsxs("span",{children:["Recovery ",t.jsx("b",{children:a.recoveryPercentage===null?"n/a":`${a.recoveryPercentage.toFixed(1)}%`})]})]})]})}function vu(e){return e.layers[Math.max(0,Math.floor(e.layers.length*.7)-1)]??e.layers[0]??0}function ju(e){const n=Math.floor(2*e.layers.length/4)+1;return e.layers.includes(n)?n:vu(e)}function Iu(e){return e.length<=3?e:[...new Set([.25,.5,.75].map(n=>e[Math.min(e.length-1,Math.floor(e.length*n))]))]}function Au(e){return e==="resid_post"?"Residual":e==="attn_out"?"Attention output":e==="z"?"Attention head":"MLP"}function Tu(e,n){var i;const a=(i=e.metadata)==null?void 0:i.attentionHeadCoverage;if(a&&typeof a=="object"&&!Array.isArray(a)){const r=a.availableByLayer;if(r&&typeof r=="object"&&!Array.isArray(r)){const o=Number(r[String(n)]);if(Number.isInteger(o)&&o>0)return o}}const s=e.attentionHeads.filter(r=>r.layer===n&&!r.aggregation&&!r.difference&&!r.rollout).map(r=>r.head);return s.length>0?Math.max(...s)+1:1}function Sn(e){return Math.abs(e.recoveryPercentage??e.causalEffect)}function Ua(e){var r;const n=e.layers[e.layers.length-1],a=(r=e.tokens[e.tokens.length-1])==null?void 0:r.index,s=e.logitLens.find(o=>o.layer===n&&o.tokenIndex===a)??e.logitLens[e.logitLens.length-1],i=[...s?[{tokenId:s.targetTokenId,tokenText:s.targetTokenText}]:[],...((s==null?void 0:s.topPredictions)??[]).map(o=>({tokenId:o.tokenId,tokenText:o.tokenText}))];return[...new Map(i.map(o=>[o.tokenId,o])).values()].slice(0,12)}function Su(e){return Da(e)}function Cu(e){var i;const n=(i=e.metadata)==null?void 0:i.attributionJobs;if(!Array.isArray(n))return;const a=n[n.length-1];if(!a||typeof a!="object")return;const s=a.targetResponseIndex;return typeof s=="number"&&Number.isInteger(s)&&s>=0?s:void 0}function Ge(e){return e.trim()||"space"}function Dr(e){return(e==null?void 0:e.replace("/api/feature/","/"))??""}function mt(e){return`${e>0?"+":""}${Math.abs(e)<.001&&e!==0?e.toExponential(2):e.toFixed(3)}`}function Nu({turn:e,remoteSummary:n,analysisRuns:a,active:s,showAnalysisControls:i,analysisOpen:r,onRetry:o,onCancel:l,onToggleAnalysis:c,onRunReady:d}){const h=e.run&&r?a.find(f=>{var u,k,j,T,A;const b=(u=f.metadata)==null?void 0:u.parentRun;if(!b||typeof b!="object"||Array.isArray(b))return!1;const g=b;return g.runId===((k=e.run)==null?void 0:k.runId)&&g.sampleId===((j=e.run)==null?void 0:j.sampleId)?r==="steering"?((T=f.intervention)==null?void 0:T.mode)==="direction":r==="patching"?!!f.patching:r==="attribution"?f.attributionMethods.some(C=>C.id==="integrated_gradients"&&C.available):r==="feature"?((A=f.intervention)==null?void 0:A.mode)==="sae_feature":r==="explanation"?f.nla.some(C=>C.status==="available")||f.jLens.length>0:!1:!1}):void 0;return t.jsxs("article",{className:"chat-turn-card","aria-label":"Conversation turn",children:[t.jsx("div",{className:"chat-user-message",children:e.prompt}),t.jsxs("div",{className:"chat-assistant-message",children:[t.jsx("span",{className:"chat-assistant-mark",children:t.jsx(Qt,{size:20})}),t.jsx("div",{children:e.run?t.jsxs(t.Fragment,{children:[t.jsx("p",{children:Da(e.run)||"The model run is complete and its internal activations are ready to inspect."}),t.jsxs("span",{className:"chat-run-ready",children:[t.jsx(Xe,{size:14})," Activation cache ready"]})]}):e.status==="error"?t.jsxs(t.Fragment,{children:[t.jsx("p",{children:e.errorMessage??"The analysis job failed."}),t.jsx("button",{onClick:o,children:"Retry"})]}):t.jsxs("div",{className:"chat-job-progress",children:[t.jsxs("span",{children:[t.jsx(Wt,{size:16})," Running the analysis..."]}),t.jsx("i",{children:t.jsx("b",{style:{width:`${s?50:4}%`}})}),t.jsx("small",{children:s?"in progress":"queued"}),s&&t.jsx("button",{"aria-label":"Cancel analysis",onClick:l,children:t.jsx(zi,{size:16})}),e.status==="cancelled"&&t.jsx("button",{"aria-label":"Retry analysis",title:"Retry analysis",onClick:o,children:t.jsx(fn,{size:15})})]})})]}),e.run&&i&&t.jsxs(t.Fragment,{children:[t.jsxs("div",{className:"chat-turn-explore-bar","aria-label":"Explore this run",children:[t.jsxs("button",{type:"button",className:r==="feature"?"active":"","aria-pressed":r==="feature",onClick:()=>c("feature"),children:[t.jsx(Ve,{size:16})," SAE"]}),t.jsxs("button",{type:"button",className:r==="patching"?"active":"","aria-pressed":r==="patching",onClick:()=>c("patching"),children:[t.jsx(ot,{size:16})," Patch"]}),t.jsxs("button",{type:"button",className:r==="steering"?"active":"","aria-pressed":r==="steering",onClick:()=>c("steering"),children:[t.jsx(vt,{size:16})," Steer"]}),t.jsxs("button",{type:"button",className:r==="attribution"?"active":"","aria-pressed":r==="attribution",onClick:()=>c("attribution"),children:[t.jsx(La,{size:16})," Attribute"]}),t.jsxs("button",{type:"button",className:r==="explanation"?"active":"","aria-pressed":r==="explanation",onClick:()=>c("explanation"),children:[t.jsx(tt,{size:16})," Explain"]}),t.jsxs("button",{type:"button",className:r==="attention"?"active":"","aria-pressed":r==="attention",onClick:()=>c("attention"),children:[t.jsx(Mt,{size:16})," Attention"]})]}),r&&t.jsx("div",{className:"chat-turn-analysis",children:t.jsx(fu,{mode:r,run:e.run,remoteSummary:n,savedRun:h,suggestionQuery:e.prompt,onRunReady:d},`${e.run.runId}:${e.run.sampleId}:${r}`)})]})]})}function Ru({turns:e,records:n,analysisRuns:a,activeTurnId:s,analysisOpen:i,onRetry:r,onCancel:o,onToggleAnalysis:l,onRunReady:c}){const d=m.useRef(null);return m.useEffect(()=>{var h;(h=d.current)==null||h.scrollIntoView({block:"end",behavior:"smooth"})},[e.length]),t.jsxs("div",{className:"chat-turn-list","aria-label":"Conversation turns",children:[e.map((h,f)=>{var b;return t.jsx(Nu,{turn:h,remoteSummary:(b=n.find(g=>g.key===h.id))==null?void 0:b.remoteSummary,analysisRuns:a,active:h.id===s,showAnalysisControls:f===e.length-1,analysisOpen:(i==null?void 0:i.turnId)===h.id?i.mode:null,onRetry:()=>r(h.id),onCancel:()=>o(h.id),onToggleAnalysis:g=>l(h.id,g),onRunReady:c},h.id)}),t.jsx("div",{ref:d})]})}const mi="Qwen/Qwen2.5-7B-Instruct",Lu=128,$u=512,Yr="safelens.localExplorer.hiddenWork.v1";function Eu({records:e,activeRecord:n,remoteState:a,onOpenDatasetTest:s,onSelectConversation:i,onRunReady:r,onRemoveRuns:o}){const[l,c]=m.useState(""),[d,h]=m.useState(n.key),[f,b]=m.useState([mi]),[g,y]=m.useState(mi),[u,k]=m.useState(Lu),[j,T]=m.useState($u),[A,C]=m.useState(null),[w,I]=m.useState(null),[L,M]=m.useState(Hu),[q,X]=m.useState(null),[H,V]=m.useState(null),[oe,de]=m.useState(!1),P=m.useMemo(()=>e.filter(E=>!L.has(E.key)),[L,e]),S=m.useMemo(()=>Ec(P),[P]),Z=P.find(E=>E.key===d)??P.find(E=>E.key===n.key)??P[0]??n,K=m.useRef([]),N=pc({model:g,maxNewTokens:u,conversationId:A,onConversationStart:C,onRunReady:(E,Y,le)=>{const R=K.current.findIndex(J=>J.id===le);r({...E,metadata:{...E.metadata,...A?{conversationId:A}:{},...R>=0?{turnIndex:R}:{}}},Y)}});K.current=N.turns;const v=N.activeTurnId!==null;m.useEffect(()=>{const E=new AbortController;return fr(E.signal).then(Y=>{b(Y.models),y(le=>Y.models.includes(le)?le:Y.models[0]),T(Y.maxNewTokens),k(le=>Math.min(le,Y.maxNewTokens))}).catch(()=>{}),()=>E.abort()},[]),m.useEffect(()=>{P.some(E=>E.key===d)||h(Z.key)},[Z.key,d,P]),m.useEffect(()=>{!H||n.key!==H||(W(n),V(null))},[n,H]);function ne(E){return E.turnRecords.filter(Y=>Y.run!==null).map(Y=>({id:Y.key,prompt:hi(Y.run),run:Y.run,jobId:Y.artifactId??null,status:"ready",startedAt:Y.importedAt}))}function W(E){const Y=S.find(te=>te.records.some(ue=>ue.key===E.key)),le=Y?ne(Y):[{id:E.key,prompt:hi(E.run),run:E.run,jobId:E.artifactId??null,status:"ready",startedAt:E.importedAt}];N.hydrate(le,(Y==null?void 0:Y.conversationId)??E.key),h(E.key),c(""),I(null);const R=(Y==null?void 0:Y.turnRecords.flatMap(te=>te.run?[te.run]:[]))??[],J=R[R.length-1]??E.run,U=Du(J);U&&y(U);const ce=Yu(J);ce&&k(Math.min(ce,j)),de(!1)}function ee(E){const Y=E.firstRecord;if(Y.run){W(Y);return}V(Y.key),h(Y.key),de(!1),i(Y.key)}function D(){N.reset(),C(null),V(null),c(""),I(null),de(!1)}function $(){const E=l.trim();!E||v||(c(""),I(null),N.submit(E))}function F(E,Y){I(le=>(le==null?void 0:le.turnId)===E&&le.mode===Y?null:{turnId:E,mode:Y})}function O(E){const Y=new Set(E.records.map(ce=>ce.key));let le=!0;for(;le;){le=!1;for(const ce of e){const te=Mu(ce);te&&Y.has(te)&&!Y.has(ce.key)&&(Y.add(ce.key),le=!0)}}const R=P.find(ce=>!Y.has(ce.key));R&&h(R.key),M(ce=>{const te=new Set(ce);for(const ue of Y)te.add(ue);try{window.localStorage.setItem(Yr,JSON.stringify([...te]))}catch{}return te});const J=e.filter(ce=>Y.has(ce.key)).filter(ce=>ce.sourceType==="local"||ce.sourceType==="generated").map(ce=>ce.key);o(J),N.turns.some(ce=>Y.has(ce.id))&&(N.reset(),C(null),I(null)),window.history.replaceState(null,"","/")}return t.jsxs("div",{className:`chat-home ${N.turns.length>0?"has-conversation":"is-empty"} ${w?"has-analysis":""}`,children:[t.jsxs("header",{className:"chat-home-header",children:[t.jsxs("a",{className:"chat-home-brand",href:"/","aria-label":"SafeLens home",children:[t.jsx("span",{children:t.jsx(Qt,{size:22})}),t.jsx("strong",{children:"SafeLens"})]}),t.jsx("button",{className:"chat-history-toggle","aria-label":"Open chat history",title:"Chat history",onClick:()=>de(!0),children:t.jsx(Ho,{size:18})}),t.jsxs("nav",{className:"chat-home-nav","aria-label":"SafeLens modes",children:[t.jsxs("button",{onClick:s,children:[t.jsx(yt,{size:16})," Dataset test"]}),t.jsxs("span",{className:`chat-home-status ${a.status}`,children:[t.jsx("i",{}),a.status==="ready"?"Local workspace":"Local mode"]})]})]}),t.jsxs("div",{className:"chat-home-body",children:[t.jsx(Wu,{open:oe,conversations:S,activeKey:null,onNew:D,onSelect:ee,onDelete:X,onClose:()=>de(!1)}),t.jsxs("main",{className:"chat-home-main",children:[N.turns.length===0?t.jsx("section",{className:"chat-home-welcome","aria-labelledby":"chat-home-title",children:t.jsxs("div",{children:[t.jsx("span",{children:t.jsx(Ca,{size:19})}),t.jsx("h1",{id:"chat-home-title",children:"What would you like to inspect?"})]})}):t.jsx(Ru,{turns:N.turns,records:P,analysisRuns:P.flatMap(E=>E.run?[E.run]:[]),activeTurnId:N.activeTurnId,analysisOpen:w,onRetry:N.retry,onCancel:N.cancel,onToggleAnalysis:F,onRunReady:r}),t.jsx(Pu,{prompt:l,model:g,models:f,maxNewTokens:u,maxNewTokensLimit:j,running:v,onPromptChange:c,onModelChange:y,onMaxNewTokensChange:k,onUseSourcePrompt:()=>{var Y;const E=(Y=Z.run)==null?void 0:Y.prompt;E&&c(E)},onSubmit:$})]})]}),q&&t.jsx(zu,{conversation:q,onCancel:()=>X(null),onConfirm:()=>{O(q),X(null)}})]})}function Mu(e){var i,r;const n=(r=(i=e.run)==null?void 0:i.metadata)==null?void 0:r.parentRun;if(!n||typeof n!="object"||Array.isArray(n))return null;const a="runId"in n?n.runId:void 0,s="sampleId"in n?n.sampleId:void 0;return typeof a=="string"&&typeof s=="string"?`${a}::${s}`:null}function Pu({prompt:e,model:n,models:a,maxNewTokens:s,maxNewTokensLimit:i,running:r,onPromptChange:o,onModelChange:l,onMaxNewTokensChange:c,onUseSourcePrompt:d,onSubmit:h}){return t.jsxs("section",{className:"chat-composer","aria-label":"Run a SafeLens analysis",children:[t.jsx("textarea",{"aria-label":"Analysis prompt",placeholder:"Ask SafeLens",value:e,maxLength:8e3,onChange:f=>o(f.target.value),onKeyDown:f=>{(f.metaKey||f.ctrlKey)&&f.key==="Enter"&&h()}}),t.jsxs("div",{className:"chat-composer-controls",children:[t.jsx("button",{className:"chat-attach","aria-label":"Use selected run prompt",title:"Use selected run prompt",onClick:d,children:t.jsx(Uo,{size:17})}),t.jsxs("label",{children:[t.jsx("span",{children:"Model"}),t.jsx("select",{"aria-label":"Analysis model",value:n,onChange:f=>l(f.target.value),children:a.map(f=>t.jsx("option",{value:f,children:qr(f)},f))})]}),t.jsxs("label",{className:"chat-token-budget",children:[t.jsx("span",{children:"Max"}),t.jsx("input",{"aria-label":"Maximum new tokens",type:"number",min:1,max:i,step:1,value:s,disabled:r,title:"Maximum new tokens",onChange:f=>c(qu(f.target.value,1,i))})]}),t.jsx("button",{className:"chat-run","aria-label":"Run analysis",title:"Run analysis",disabled:!e.trim()||r,onClick:h,children:r?t.jsx(Wt,{size:18}):t.jsx(Di,{size:18,fill:"currentColor"})})]})]})}function Wu({open:e,conversations:n,activeKey:a,onNew:s,onSelect:i,onDelete:r,onClose:o}){return t.jsxs(t.Fragment,{children:[t.jsxs("aside",{className:`chat-history ${e?"open":""}`,"aria-label":"Chat history",children:[t.jsxs("header",{children:[t.jsxs("button",{className:"chat-history-new",onClick:s,children:[t.jsx(Fo,{size:17})," New chat"]}),t.jsx("button",{className:"chat-history-close","aria-label":"Close chat history",onClick:o,children:t.jsx(Je,{size:17})})]}),t.jsxs("nav",{"aria-label":"Conversation history",children:[t.jsx("span",{children:"Recent"}),n.length?n.map(l=>t.jsxs("div",{className:`chat-history-row ${l.firstRecord.key===a?"active":""}`,children:[t.jsxs("button",{className:"chat-history-open",onClick:()=>i(l),children:[t.jsx("strong",{children:l.title}),t.jsxs("small",{children:[qr(l.firstRecord.modelName),l.turnCount>1?` · ${l.turnCount} turns`:""]})]}),t.jsx("button",{className:"chat-history-delete","aria-label":`Delete conversation ${l.title}`,title:"Delete conversation",onClick:()=>r(l),children:t.jsx(_n,{size:15})})]},l.conversationId)):t.jsx("p",{children:"No conversations yet."})]})]}),e&&t.jsx("button",{className:"chat-history-backdrop","aria-label":"Close chat history",onClick:o})]})}function zu({conversation:e,onCancel:n,onConfirm:a}){return t.jsx("div",{className:"chat-delete-backdrop",role:"presentation",onMouseDown:s=>{s.target===s.currentTarget&&n()},children:t.jsxs("section",{role:"dialog","aria-modal":"true","aria-labelledby":"chat-delete-title",className:"chat-delete-dialog",children:[t.jsxs("header",{children:[t.jsxs("div",{children:[t.jsx("span",{children:"Chat history"}),t.jsx("h2",{id:"chat-delete-title",children:"Delete this conversation?"})]}),t.jsx("button",{"aria-label":"Close remove confirmation",onClick:n,children:t.jsx(Je,{size:18})})]}),t.jsxs("p",{children:["This removes ",t.jsx("strong",{children:e.title})," from Chat history. Workspace source files are not modified."]}),t.jsxs("footer",{children:[t.jsx("button",{autoFocus:!0,onClick:n,children:"Cancel"}),t.jsxs("button",{className:"danger",onClick:a,children:[t.jsx(_n,{size:15})," Delete conversation"]})]})]})})}function qr(e){const n=e.split("/");return n[n.length-1]??e}function Du(e){var s;const n=(s=e.metadata)==null?void 0:s.promptRunner;if(!n||typeof n!="object")return null;const a=n.model;return typeof a=="string"?a:null}function Yu(e){var s;const n=(s=e.metadata)==null?void 0:s.promptRunner;if(!n||typeof n!="object")return null;const a=n.maxNewTokens;return typeof a=="number"&&Number.isInteger(a)&&a>0?a:null}function qu(e,n,a){const s=Number(e);return Number.isInteger(s)?Math.max(n,Math.min(a,s)):n}function hi(e){var a;const n=(a=e.metadata)==null?void 0:a.promptRunner;if(n&&typeof n=="object"){const s=n.userPrompt;if(typeof s=="string"&&s.trim())return s}return e.prompt}function Hu(){try{const e=JSON.parse(window.localStorage.getItem(Yr)??"[]");return new Set(Array.isArray(e)?e.filter(n=>typeof n=="string"):[])}catch{return new Set}}const ra="Qwen/Qwen2.5-7B-Instruct";function Fu({onOpenChat:e}){const[n,a]=m.useState([]),[s,i]=m.useState([]),[r,o]=m.useState("steering"),[l,c]=m.useState("safelens-steering-v1"),[d,h]=m.useState(new Set),[f,b]=m.useState([ra]),[g,y]=m.useState(ra),[u,k]=m.useState(12),[j,T]=m.useState(1),[A,C]=m.useState(24),[w,I]=m.useState(null),[L,M]=m.useState(null),[q,X]=m.useState(null),[H,V]=m.useState("all"),oe=s.find(W=>W.id===r),de=m.useMemo(()=>n.filter(W=>oe==null?void 0:oe.supportedDatasetIds.includes(W.id)),[oe,n]),P=de.find(W=>W.id===l)??de[0],S=(w==null?void 0:w.status)==="idle"||(w==null?void 0:w.status)==="loading";m.useEffect(()=>{const W=new AbortController;return Promise.all([bd(W.signal),fr(W.signal)]).then(([ee,D])=>{a(ee.datasets),i(ee.algorithms),b(D.models),D.models.includes(ra)||y(D.models[0]);const $=ee.datasets.find(F=>F.id==="safelens-steering-v1")??ee.datasets[0];c($.id),h(new Set($.samples.map(F=>F.id)))}).catch(ee=>{ee instanceof DOMException&&ee.name==="AbortError"||M(ee instanceof Error?ee.message:"Dataset catalog is unavailable.")}),()=>W.abort()},[]),m.useEffect(()=>{if(!S||!w)return;let W=!1;const ee=window.setInterval(()=>{wd(w.id).then(D=>{W||I(D)}).catch(D=>{W||X(D instanceof Error?D.message:"Could not refresh the job.")})},650);return()=>{W=!0,window.clearInterval(ee)}},[w==null?void 0:w.id,S]);function Z(W){const ee=n.find(D=>W.supportedDatasetIds.includes(D.id));o(W.id),I(null),X(null),V("all"),ee&&(c(ee.id),h(new Set(ee.samples.map(D=>D.id))))}function K(W){const ee=n.find(D=>D.id===W);c(W),I(null),h(new Set((ee==null?void 0:ee.samples.map(D=>D.id))??[]))}function N(W){h(ee=>{const D=new Set(ee);return D.has(W)?D.delete(W):D.add(W),D})}async function v(){if(!(!P||!oe||d.size===0)){X(null),V("all");try{const W=await xd({datasetId:P.id,algorithmId:oe.id,model:g,sampleIds:P.samples.filter(ee=>d.has(ee.id)).map(ee=>ee.id),layer:u,strength:j,seed:0,maxNewTokens:A});I(W)}catch(W){X(W instanceof Error?W.message:"Dataset test could not start.")}}}async function ne(){if(w)try{I(await kd(w.id))}catch(W){X(W instanceof Error?W.message:"Dataset test could not be cancelled.")}}return t.jsxs("div",{className:"dataset-test-screen",children:[t.jsxs("header",{className:"dataset-test-header",children:[t.jsxs("button",{className:"dataset-test-brand",onClick:e,"aria-label":"Open SafeLens chat",children:[t.jsx("span",{children:t.jsx(Qt,{size:21})}),t.jsx("strong",{children:"SafeLens"})]}),t.jsxs("nav",{"aria-label":"SafeLens modes",children:[t.jsxs("button",{onClick:e,children:[t.jsx(Ko,{size:16})," Chat"]}),t.jsxs("button",{className:"active","aria-current":"page",children:[t.jsx(yt,{size:16})," Dataset test"]})]}),t.jsxs("span",{className:"dataset-live-badge",children:[t.jsx("i",{})," Real local evaluation"]})]}),t.jsxs("main",{className:"dataset-test-main",children:[t.jsxs("section",{className:"dataset-test-intro","aria-labelledby":"dataset-test-title",children:[t.jsxs("div",{children:[t.jsx("span",{children:"Evaluation mode"}),t.jsx("h1",{id:"dataset-test-title",children:"Test white-box methods on a fixed dataset"})]}),t.jsxs("dl",{children:[t.jsxs("div",{children:[t.jsx("dt",{children:"Samples"}),t.jsx("dd",{children:(P==null?void 0:P.samples.length)??0})]}),t.jsxs("div",{children:[t.jsx("dt",{children:"Selected"}),t.jsx("dd",{children:d.size})]}),t.jsxs("div",{children:[t.jsx("dt",{children:"Pass target"}),t.jsx("dd",{children:zn((P==null?void 0:P.metric.threshold)??0)})]})]})]}),L?t.jsxs("div",{className:"dataset-error",role:"alert",children:[t.jsx($n,{size:18})," ",L]}):t.jsxs("div",{className:"dataset-test-setup",children:[t.jsxs("section",{className:"dataset-source-panel","aria-labelledby":"dataset-source-title",children:[t.jsxs("header",{children:[t.jsxs("div",{children:[t.jsx("span",{children:"1 / Dataset"}),t.jsx("h2",{id:"dataset-source-title",children:"Choose evaluation samples"})]}),t.jsxs("label",{children:[t.jsx("span",{children:"Dataset"}),t.jsx("select",{value:(P==null?void 0:P.id)??"",onChange:W=>K(W.target.value),children:de.map(W=>t.jsx("option",{value:W.id,children:W.name},W.id))})]})]}),P&&t.jsxs(t.Fragment,{children:[t.jsxs("div",{className:"dataset-description",children:[t.jsx("p",{children:P.description}),t.jsxs("span",{children:[P.source," / v",P.version]})]}),t.jsxs("div",{className:"dataset-sample-toolbar",children:[t.jsxs("strong",{children:[d.size," of ",P.samples.length," selected"]}),t.jsxs("button",{onClick:()=>h(d.size===P.samples.length?new Set:new Set(P.samples.map(W=>W.id))),children:[d.size===P.samples.length?t.jsx(hs,{size:15}):t.jsx(Bt,{size:15}),d.size===P.samples.length?"Clear all":"Select all"]})]}),t.jsx("div",{className:"dataset-sample-list",children:P.samples.map(W=>t.jsxs("button",{className:d.has(W.id)?"selected":"","aria-pressed":d.has(W.id),onClick:()=>N(W.id),children:[d.has(W.id)?t.jsx(hs,{size:17}):t.jsx(Bt,{size:17}),t.jsxs("span",{children:[t.jsxs("small",{children:[W.id," / ",W.category]}),t.jsx("strong",{children:W.prompt??W.corruptedPrompt}),W.cleanPrompt&&t.jsxs("em",{children:["Clean: ",W.cleanPrompt]}),W.desiredPrompt&&t.jsxs("em",{children:["Toward: ",W.desiredPrompt]})]})]},W.id))})]})]}),t.jsxs("section",{className:"dataset-method-panel","aria-labelledby":"dataset-method-title",children:[t.jsxs("header",{children:[t.jsx("span",{children:"2 / Method"}),t.jsx("h2",{id:"dataset-method-title",children:"Select an optimization algorithm"})]}),t.jsx("div",{className:"dataset-method-tabs",role:"radiogroup","aria-label":"Optimization algorithm",children:s.map(W=>t.jsxs("button",{role:"radio","aria-checked":W.id===r,className:W.id===r?"active":"",onClick:()=>Z(W),children:[W.id==="steering"?t.jsx(Oo,{size:18}):t.jsx(kt,{size:18}),t.jsxs("span",{children:[t.jsx("strong",{children:W.name}),t.jsx("small",{children:W.implementation.replace(/_/g," ")})]})]},W.id))}),oe&&t.jsxs("div",{className:"dataset-method-summary",children:[t.jsx("p",{children:oe.description}),t.jsxs("a",{href:oe.paperUrl,target:"_blank",rel:"noreferrer",children:[t.jsxs("span",{children:[t.jsx("small",{children:"Method reference"}),t.jsx("strong",{children:oe.paperTitle})]}),t.jsx(Vo,{size:16})]})]}),P&&t.jsxs("div",{className:"dataset-metric-note",children:[t.jsx("strong",{children:P.metric.name}),t.jsx("p",{children:P.metric.definition}),t.jsxs("span",{children:["Required pass rate > ",zn(P.metric.threshold)]})]}),t.jsxs("div",{className:"dataset-run-controls",children:[t.jsxs("label",{className:"wide",children:[t.jsx("span",{children:"Local model"}),t.jsx("select",{value:g,disabled:S,onChange:W=>y(W.target.value),children:f.map(W=>t.jsx("option",{value:W,children:Ou(W)},W))})]}),t.jsxs("label",{children:[t.jsx("span",{children:"Layer"}),t.jsx("input",{type:"number",min:0,max:127,value:u,disabled:S,onChange:W=>k(pi(W.target.value,0,127))})]}),t.jsxs("label",{children:[t.jsx("span",{children:"Output tokens"}),t.jsx("input",{type:"number",min:1,max:64,value:A,disabled:S,onChange:W=>C(pi(W.target.value,1,64))})]}),r==="steering"&&t.jsxs("label",{className:"wide",children:[t.jsxs("span",{children:["Steering strength ",t.jsx("b",{children:j.toFixed(1)})]}),t.jsx("input",{type:"range",min:-5,max:5,step:.5,value:j,disabled:S,onChange:W=>T(Number(W.target.value))})]})]}),t.jsxs("button",{className:"dataset-run-button",disabled:S||!P||d.size===0,onClick:v,children:[S?t.jsx(Wt,{size:18,className:"spin"}):t.jsx(Di,{size:18,fill:"currentColor"}),S?"Running dataset test":`Test ${d.size} ${d.size===1?"sample":"samples"}`]}),S&&w&&t.jsxs("button",{className:"dataset-cancel-button",onClick:ne,children:[t.jsx(zi,{size:16})," Cancel"]}),q&&t.jsxs("div",{className:"dataset-error",role:"alert",children:[t.jsx($n,{size:17})," ",q]})]})]}),w&&t.jsx(Uu,{job:w,filter:H,onFilter:V})]})]})}function Uu({job:e,filter:n,onFilter:a}){if(e.status!=="ready"||!e.result)return t.jsxs("section",{className:"dataset-job-progress","aria-live":"polite",children:[t.jsxs("header",{children:[t.jsx("span",{children:"3 / Test run"}),t.jsx("strong",{children:e.detail}),t.jsxs("b",{children:[e.progress,"%"]})]}),t.jsx("div",{children:t.jsx("i",{style:{width:`${e.progress}%`}})}),e.error&&t.jsx("p",{children:e.error})]});const s=e.result,i=s.rows.filter(r=>n==="all"||(n==="passed"?r.passed:!r.passed));return t.jsxs("section",{className:"dataset-results","aria-labelledby":"dataset-results-title",children:[t.jsxs("header",{className:s.metric.meetsThreshold?"passed":"failed",children:[t.jsxs("div",{children:[t.jsx("span",{children:"3 / Results"}),t.jsx("h2",{id:"dataset-results-title",children:s.dataset.name}),t.jsxs("p",{children:[s.execution.model," / ",s.execution.layer===void 0?"automatic layer":`L${s.execution.layer}`,s.execution.requestedLayer!==void 0&&s.execution.requestedLayer!==s.execution.layer?` (requested L${s.execution.requestedLayer})`:""," / ",s.execution.source,s.execution.device?` / ${s.execution.device}`:"",s.execution.dtype?` / ${s.execution.dtype}`:""]})]}),t.jsxs("div",{className:"dataset-score",children:[s.metric.meetsThreshold?t.jsx(Xe,{size:24}):t.jsx($n,{size:24}),t.jsx("strong",{children:zn(s.metric.accuracy)}),t.jsx("span",{children:s.metric.meetsThreshold?"Threshold met":"Below threshold"})]}),t.jsxs("dl",{children:[t.jsxs("div",{children:[t.jsx("dt",{children:"Passed"}),t.jsx("dd",{children:s.metric.passed})]}),t.jsxs("div",{children:[t.jsx("dt",{children:"Completed"}),t.jsx("dd",{children:s.metric.completed})]}),t.jsxs("div",{children:[t.jsx("dt",{children:"Errors"}),t.jsx("dd",{children:s.metric.errors})]}),t.jsxs("div",{children:[t.jsx("dt",{children:"Target"}),t.jsx("dd",{children:zn(s.metric.threshold)})]})]})]}),t.jsxs("div",{className:"dataset-result-toolbar",children:[t.jsx("div",{role:"tablist","aria-label":"Result filter",children:["all","passed","failed"].map(r=>t.jsx("button",{role:"tab","aria-selected":n===r,className:n===r?"active":"",onClick:()=>a(r),children:r==="all"?"All samples":r==="passed"?"Correct":"Incorrect"},r))}),t.jsxs("span",{children:[t.jsx(yt,{size:14})," ",s.dataset.version," / ",s.algorithm.implementation.replace(/_/g," ")]})]}),t.jsxs("div",{className:"dataset-result-list",children:[i.map(r=>t.jsx(Ku,{row:r,result:s},r.sampleId)),!i.length&&t.jsx("p",{className:"dataset-empty-filter",children:"No samples in this result group."})]})]})}function Ku({row:e,result:n}){const a=e.steered??e.patched;return t.jsxs("article",{className:`dataset-result-row ${e.passed?"passed":"failed"}`,children:[t.jsxs("header",{children:[e.passed?t.jsx(Xe,{size:18}):t.jsx($n,{size:18}),t.jsxs("div",{children:[t.jsx("strong",{children:e.sampleId}),t.jsx("span",{children:e.category})]}),t.jsx("b",{children:e.status==="error"?"Error":e.passed?"Correct":"Incorrect"})]}),t.jsx("p",{className:"dataset-result-prompt",children:e.prompt}),t.jsx("p",{className:"dataset-result-detail",children:e.detail}),(e.original!==void 0||a!==void 0)&&t.jsxs("div",{className:"dataset-output-compare",children:[t.jsxs("div",{children:[t.jsx("span",{children:"Original"}),t.jsx("p",{children:e.original||"No visible continuation"})]}),t.jsxs("div",{children:[t.jsx("span",{children:n.algorithm.id==="steering"?"Steered":"Patched"}),t.jsx("p",{children:a||"No visible continuation"})]})]}),e.diagnostics&&t.jsx("dl",{className:"dataset-diagnostics",children:Object.entries(e.diagnostics).slice(0,6).map(([s,i])=>t.jsxs("div",{children:[t.jsx("dt",{children:Vu(s)}),t.jsx("dd",{children:Bu(i)})]},s))})]})}function Ou(e){const n=e.split("/");return n[n.length-1]||e}function zn(e){return`${Math.round(e*100)}%`}function pi(e,n,a){const s=Number.parseInt(e,10);return Math.min(a,Math.max(n,Number.isFinite(s)?s:n))}function Vu(e){return e.replace(/([a-z])([A-Z])/g,"$1 $2").replace(/_/g," ")}function Bu(e){return Array.isArray(e)?e.length>8?`${e.slice(0,8).join(", ")}...`:e.join(", "):typeof e=="number"?Number.isInteger(e)?String(e):e.toFixed(5):String(e)}function Qu({layers:e,selectedLayer:n,onSelect:a}){return t.jsxs("div",{className:"layer-picker main-layer-picker",role:"group","aria-label":"Layer selector",children:[t.jsx("span",{className:"control-label",children:"Layer"}),e.length<=16?t.jsx("div",{className:"layer-button-selector",role:"radiogroup","aria-label":"Analysis layer",children:e.map(s=>t.jsxs("button",{role:"radio","data-layer":s,"aria-checked":n===s,tabIndex:n===s?0:-1,className:n===s?"active":"",onClick:()=>a(s),onKeyDown:i=>Xu(i,e,s,a),children:["L",s]},s))}):t.jsx(Zu,{layers:e,selectedLayer:n,onSelect:a})]})}function Ju({visible:e,tokenText:n,tokenIndex:a,layer:s,score:i,view:r,menuOpen:o,contextOpen:l,pinned:c,canPin:d,pinnedCount:h,onToggleMenu:f,onSelectView:b,onInspect:g,onToggleContext:y,onPin:u,onPreloadCompare:k,onCompare:j,onDismiss:T}){const A=Ce.useRef(null);if(m.useEffect(()=>{if(!o)return;function I(M){M.key==="Escape"&&(M.preventDefault(),f())}function L(M){var q;(q=A.current)!=null&&q.contains(M.target)||f()}return window.addEventListener("keydown",I),window.addEventListener("pointerdown",L),()=>{window.removeEventListener("keydown",I),window.removeEventListener("pointerdown",L)}},[o,f]),!e)return null;const C=[{id:"overview",label:"Overview",icon:t.jsx(Ve,{size:16})},{id:"residual",label:"Residual",icon:t.jsx(bn,{size:16})},{id:"attention",label:"Attention",icon:t.jsx(Mt,{size:16})},{id:"mlp",label:"MLP",icon:t.jsx(Qt,{size:16})},{id:"nla",label:"NLA",icon:t.jsx(tt,{size:16})},{id:"attribution",label:"Attribution",icon:t.jsx(On,{size:16})},{id:"patching",label:"Patching",icon:t.jsx(kt,{size:16})},{id:"intervention",label:"Intervention",icon:t.jsx(vt,{size:16})}],w=n.trim()||"space";return t.jsxs("section",{ref:A,className:"selection-workbench","aria-label":"Selected token actions","aria-live":"polite",children:[t.jsxs("div",{className:"selection-workbench-main",children:[t.jsxs("div",{className:"selection-workbench-identity",children:[t.jsx("span",{"aria-hidden":"true"}),t.jsxs("div",{children:[t.jsx("small",{children:"Selected token"}),t.jsx("strong",{children:w})]}),t.jsxs("dl",{children:[t.jsxs("div",{children:[t.jsx("dt",{children:"Position"}),t.jsxs("dd",{children:["T",a]})]}),t.jsxs("div",{children:[t.jsx("dt",{children:"Layer"}),t.jsxs("dd",{children:["L",s]})]}),t.jsxs("div",{children:[t.jsx("dt",{children:"Safety proxy"}),t.jsx("dd",{children:i})]})]})]}),t.jsxs("div",{className:"selection-workbench-actions",children:[t.jsxs("button",{className:o?"active":"","aria-expanded":o,"aria-haspopup":"menu","aria-controls":"selection-analysis-menu",title:"Choose an analysis for the selected token",onClick:f,children:[t.jsx(tt,{size:16})," Analyze"]}),t.jsxs("button",{title:"Inspect selected evidence",onClick:I=>g(I.currentTarget),children:[t.jsx(pa,{size:16})," Inspect"]}),t.jsxs("button",{className:l?"active":"","aria-expanded":l,title:"Toggle supporting context",onClick:y,children:[t.jsx(Bo,{size:16})," Context"]}),t.jsxs("button",{className:c?"active":"","aria-pressed":c,disabled:!d,title:c?"Unpin selected evidence":"Pin selected evidence",onClick:u,children:[t.jsx(Hn,{size:16})," ",c?"Unpin":"Pin"]}),t.jsxs("button",{disabled:!h,title:"Compare pinned evidence",onPointerEnter:k,onFocus:k,onClick:I=>j(I.currentTarget),children:[t.jsx(ot,{size:16})," Compare",t.jsx("b",{children:h})]}),t.jsx("button",{className:"selection-workbench-dismiss","aria-label":"Dismiss selected token actions",onClick:T,children:t.jsx(Je,{size:16})})]})]}),o&&t.jsx("div",{id:"selection-analysis-menu",className:"selection-analysis-menu",role:"menu","aria-label":"Analyze selected token",children:C.map(I=>t.jsxs("button",{role:"menuitemradio","aria-checked":r===I.id,className:r===I.id?"active":"",onClick:()=>b(I.id),children:[I.icon,t.jsx("span",{children:I.label}),r===I.id&&t.jsx(Xe,{size:14})]},I.id))})]})}function Gu({view:e,setView:n}){const a=Ce.useRef(null),s=Ce.useRef(null),[i,r]=Ce.useState({previous:!1,next:!1}),o=[{id:"overview",label:"Overview",icon:t.jsx(Ve,{size:15})},{id:"residual",label:"Residual",icon:t.jsx(bn,{size:15})},{id:"attention",label:"Attention",icon:t.jsx(Mt,{size:15})},{id:"mlp",label:"MLP",icon:t.jsx($a,{size:15})},{id:"nla",label:"NLA",icon:t.jsx(Ca,{size:15})},{id:"patching",label:"Patching",icon:t.jsx(kt,{size:15})},{id:"intervention",label:"Intervention",icon:t.jsx(vt,{size:15})},{id:"attribution",label:"Attribution",icon:t.jsx(On,{size:15})}];m.useEffect(()=>{var k;const d=a.current;if(!d||!window.matchMedia("(max-width: 860px)").matches)return;const h=[...d.querySelectorAll('[role="tab"]')],f=h.findIndex(j=>j.id===`analysis-tab-${e}`),b=h[0];if(f<0||!b)return;const g=Number.parseFloat(getComputedStyle(d).columnGap)||6,y=Math.max(1,Math.floor((d.clientWidth+g)/Math.max(1,b.offsetWidth+g))),u=Math.floor(f/y)*y;d.scrollLeft=Math.max(0,(((k=h[u])==null?void 0:k.offsetLeft)??b.offsetLeft)-b.offsetLeft),window.requestAnimationFrame(()=>yi(d,r))},[e]),m.useEffect(()=>{const d=a.current;if(!d)return;const h=()=>yi(d,r),f=new ResizeObserver(h);return d.addEventListener("scroll",h,{passive:!0}),f.observe(d),window.requestAnimationFrame(h),()=>{d.removeEventListener("scroll",h),f.disconnect()}},[]),m.useEffect(()=>{var f;const d=s.current,h=a.current;!d||!h||(d===1&&!i.next&&(s.current=null,h.querySelectorAll('[role="tab"]').item(o.length-1).focus({preventScroll:!0})),d===-1&&!i.previous&&(s.current=null,(f=h.querySelector('[role="tab"]'))==null||f.focus({preventScroll:!0})))},[i.next,i.previous,o.length]);function l(d){const h=a.current;if(!h)return;s.current=d;const f=window.matchMedia("(prefers-reduced-motion: reduce)").matches;h.scrollBy({left:d*h.clientWidth,behavior:f?"auto":"smooth"})}function c(d,h){var g,y;let f;if(d.key==="ArrowLeft"||d.key==="ArrowUp"?f=(h-1+o.length)%o.length:d.key==="ArrowRight"||d.key==="ArrowDown"?f=(h+1)%o.length:d.key==="Home"?f=0:d.key==="End"&&(f=o.length-1),f===void 0)return;d.preventDefault();const b=o[f];n(b.id),(y=(g=d.currentTarget.parentElement)==null?void 0:g.querySelector(`#analysis-tab-${b.id}`))==null||y.focus()}return t.jsxs("div",{className:`workspace-tabs-shell ${i.previous?"has-previous":""} ${i.next?"has-next":""}`,children:[t.jsx("button",{type:"button",className:"workspace-tabs-scroll previous","aria-label":"Show previous analysis views","aria-controls":"analysis-view-tabs",title:i.previous?"Previous views":"At first view page",disabled:!i.previous,onClick:()=>l(-1),children:t.jsx(Vt,{size:17})}),t.jsx("div",{ref:a,id:"analysis-view-tabs",className:"workspace-tabs",role:"tablist","aria-label":"Analysis view",children:o.map((d,h)=>t.jsxs("button",{id:`analysis-tab-${d.id}`,role:"tab","aria-controls":"analysis-panel","aria-selected":e===d.id,tabIndex:e===d.id?0:-1,className:e===d.id?"active":"",onClick:()=>n(d.id),onKeyDown:f=>c(f,h),children:[d.icon,t.jsx("span",{children:d.label})]},d.id))}),t.jsx("button",{type:"button",className:"workspace-tabs-scroll next","aria-label":"Show more analysis views","aria-controls":"analysis-view-tabs",title:i.next?"More views":"At last view page",disabled:!i.next,onClick:()=>l(1),children:t.jsx(dt,{size:17})})]})}function yi(e,n){const a=Math.max(0,e.scrollWidth-e.clientWidth),s={previous:e.scrollLeft>2,next:e.scrollLeft<a-2};n(i=>i.previous===s.previous&&i.next===s.next?i:s)}function Xu(e,n,a,s){var l,c;const i=n.indexOf(a);let r;if(e.key==="ArrowLeft"||e.key==="ArrowUp"?r=(i-1+n.length)%n.length:e.key==="ArrowRight"||e.key==="ArrowDown"?r=(i+1)%n.length:e.key==="Home"?r=0:e.key==="End"&&(r=n.length-1),r===void 0)return;e.preventDefault();const o=n[r];s(o),(c=(l=e.currentTarget.parentElement)==null?void 0:l.querySelector(`[role="radio"][data-layer="${o}"]`))==null||c.focus()}function Zu({layers:e,selectedLayer:n,onSelect:a}){const s=Math.max(0,e.indexOf(n));return t.jsxs("div",{className:"compact-layer-selector",children:[t.jsx("button",{"aria-label":"Previous layer",title:"Previous layer",disabled:s===0,onClick:()=>a(e[s-1]),children:t.jsx(Vt,{size:14})}),t.jsx("select",{"aria-label":"Selected layer",value:e[s],onChange:i=>a(Number(i.target.value)),children:e.map(i=>t.jsxs("option",{value:i,children:["Layer ",i]},i))}),t.jsx("button",{"aria-label":"Next layer",title:"Next layer",disabled:s>=e.length-1,onClick:()=>a(e[s+1]),children:t.jsx(dt,{size:14})}),t.jsxs("span",{children:[s+1," / ",e.length]})]})}const Hr="safelens.localExplorer.pinnedEvidence.v2",em=["overview","residual","attention","mlp","nla","patching","intervention","attribution"];function tm(e,n){switch(n.type){case"select_token":return{...e,tokenIndex:n.tokenIndex,sourceTokenIndex:Math.min(e.sourceTokenIndex??n.tokenIndex,n.tokenIndex),targetTokenIndex:n.tokenIndex,tokenRange:void 0};case"select_source_token":return{...e,sourceTokenIndex:Math.min(n.tokenIndex,e.targetTokenIndex??e.tokenIndex)};case"select_attention_pair":return{...e,tokenIndex:n.targetTokenIndex,sourceTokenIndex:n.sourceTokenIndex,targetTokenIndex:n.targetTokenIndex,tokenRange:void 0};case"select_range":return{...e,tokenRange:n.tokenRange};case"select_layer":return{...e,layer:n.layer};case"select_view":return{...e,view:n.view,metric:Kr(n.view,e.trackName),normalization:n.view==="attention"||n.view==="mlp"||n.view==="attribution"||n.view==="intervention"?"raw":e.normalization};case"select_head":return{...e,headId:n.headId};case"select_attention_edge_mode":return{...e,attentionEdgeMode:n.mode};case"select_nla_component":return{...e,nlaComponent:n.component};case"select_neuron":return{...e,neuronId:n.neuronId};case"select_track":return{...e,trackName:n.trackName,metric:e.view==="attribution"?n.trackName:e.metric};case"select_metric":return{...e,metric:n.metric};case"set_normalization":return{...e,normalization:n.normalization};case"toggle_pin":{const a=e.pinnedItems.some(s=>s.id===n.evidence.id);return{...e,pinnedItems:a?e.pinnedItems.filter(s=>s.id!==n.evidence.id):[...e.pinnedItems,n.evidence].slice(-4)}}case"restore_pin":return{...e,tokenIndex:n.evidence.tokenIndex,sourceTokenIndex:n.evidence.sourceTokenIndex??e.sourceTokenIndex,targetTokenIndex:n.evidence.tokenIndex,tokenRange:void 0,layer:n.evidence.layer,view:n.evidence.view,headId:n.evidence.headId??e.headId,nlaComponent:n.evidence.view==="nla"&&Ur(n.evidence.component)?n.evidence.component:e.nlaComponent,neuronId:n.evidence.neuronId??e.neuronId,trackName:n.evidence.trackName??(n.evidence.view==="attribution"?n.evidence.metric:e.trackName),metric:n.evidence.metric,normalization:n.evidence.normalization};case"restore_session":case"restore_url":return n.selection}}function nm(e){return Fr(e,im(e))}function Fr(e,n){const a=new URLSearchParams(window.location.search),s=a.get("view")??a.get("mode"),i=Cn(a.get("token")),r=Cn(a.get("source")),o=Cn(a.get("target")),l=Cn(a.get("layer")),c=a.get("normalization"),d=sm(a.get("range")),h=a.get("edge"),f=a.get("nlaComponent"),b=em.includes(s)?s:e.view,g=a.get("track")??e.trackName,y=o!==void 0&&e.tokenIndices.includes(o)?o:i!==void 0&&e.tokenIndices.includes(i)?i:e.tokenIndex,u=r!==void 0&&e.tokenIndices.includes(r)?r:y,k=d&&e.tokenIndices.includes(d[0])&&e.tokenIndices.includes(d[1])?d:void 0;return{view:b,tokenIndex:y,sourceTokenIndex:Math.min(u,y),targetTokenIndex:y,tokenRange:k,layer:l!==void 0&&e.layers.includes(l)?l:e.layer,headId:a.get("head")??e.headId,attentionEdgeMode:h==="outgoing"?"outgoing":"incoming",nlaComponent:Ur(f)?f:e.nlaComponent,neuronId:a.get("neuron")??e.neuronId,trackName:g,metric:a.get("metric")??Kr(b,g),normalization:c==="raw"||c==="normalized"?c:b==="attention"||b==="intervention"?"raw":"normalized",pinnedItems:n}}function am(e){const[n,a]=m.useReducer(tm,e,nm),s=m.useRef(e),i=m.useRef(n.pinnedItems),r=m.useRef("replace");s.current=e,i.current=n.pinnedItems;function o(l,c="push"){r.current=c,a(l)}return m.useEffect(()=>{const l=new URLSearchParams(window.location.search),c=l.get("run"),d=l.get("sample");if(c&&c!==e.runId||d&&d!==e.sampleId)return;l.set("view",n.view),l.set("token",String(n.tokenIndex)),l.set("layer",String(n.layer)),l.set("normalization",n.normalization),n.headId&&l.set("head",n.headId),n.neuronId&&l.set("neuron",n.neuronId),n.trackName&&l.set("track",n.trackName),n.metric&&l.set("metric",n.metric),n.tokenRange?l.set("range",`${n.tokenRange[0]}-${n.tokenRange[1]}`):l.delete("range"),n.view==="attention"?(l.set("source",String(n.sourceTokenIndex??n.tokenIndex)),l.set("target",String(n.targetTokenIndex??n.tokenIndex)),l.set("edge",n.attentionEdgeMode)):(l.delete("source"),l.delete("target"),l.delete("edge")),n.view==="nla"?l.set("nlaComponent",n.nlaComponent):l.delete("nlaComponent"),l.delete("mode");const h=`${window.location.pathname}?${l.toString()}${window.location.hash}`,f=`${window.location.pathname}${window.location.search}${window.location.hash}`,b=r.current;r.current="replace",h!==f&&(b==="push"?window.history.pushState(window.history.state,"",h):window.history.replaceState(window.history.state,"",h))},[e.runId,e.sampleId,n.attentionEdgeMode,n.headId,n.layer,n.metric,n.neuronId,n.nlaComponent,n.normalization,n.sourceTokenIndex,n.targetTokenIndex,n.tokenIndex,n.tokenRange,n.trackName,n.view]),m.useEffect(()=>{function l(){const c=s.current,d=new URLSearchParams(window.location.search),h=d.get("run"),f=d.get("sample");h&&h!==c.runId||f&&f!==c.sampleId||(r.current="replace",a({type:"restore_url",selection:Fr(c,i.current)}))}return window.addEventListener("popstate",l),()=>window.removeEventListener("popstate",l)},[]),m.useEffect(()=>{window.localStorage.setItem(Hr,JSON.stringify(n.pinnedItems))},[n.pinnedItems]),{state:n,selectToken:(l,c)=>o({type:"select_token",tokenIndex:l},c),selectSourceToken:(l,c)=>o({type:"select_source_token",tokenIndex:l},c),selectAttentionPair:(l,c,d)=>o({type:"select_attention_pair",sourceTokenIndex:l,targetTokenIndex:c},d),selectRange:(l,c)=>o({type:"select_range",tokenRange:l},c),selectLayer:(l,c)=>o({type:"select_layer",layer:l},c),selectView:(l,c)=>o({type:"select_view",view:l},c),selectHead:(l,c)=>o({type:"select_head",headId:l},c),selectAttentionEdgeMode:(l,c)=>o({type:"select_attention_edge_mode",mode:l},c),selectNlaComponent:(l,c)=>o({type:"select_nla_component",component:l},c),selectNeuron:(l,c)=>o({type:"select_neuron",neuronId:l},c),selectTrack:(l,c)=>o({type:"select_track",trackName:l},c),selectMetric:(l,c)=>o({type:"select_metric",metric:l},c),setNormalization:(l,c)=>o({type:"set_normalization",normalization:l},c),togglePin:l=>a({type:"toggle_pin",evidence:l}),restorePin:(l,c)=>o({type:"restore_pin",evidence:l},c),restoreSession:(l,c)=>o({type:"restore_session",selection:l},c)}}function Ur(e){return e==="resid_post"||e==="attn_result"||e==="mlp_out"}function Kr(e,n){return e==="residual"?"residual_direction":e==="attention"?"attention_probability":e==="mlp"?"mlp_signed_activation":e==="nla"?"nla_cosine":e==="patching"?"patching_recovery":e==="intervention"?"intervention_logit_delta":e==="attribution"?n:"tokenRisk"}function Cn(e){if(!(e===null||!/^\d+$/.test(e)))return Number(e)}function sm(e){const n=e==null?void 0:e.match(/^(\d+)-(\d+)$/);if(!n)return;const a=Number(n[1]),s=Number(n[2]);return a<=s?[a,s]:[s,a]}function im(e){try{const n=JSON.parse(window.localStorage.getItem(Hr)??"[]");if(!Array.isArray(n))return e.initialPinnedItems??[];const a=n.filter(rm);return a.length>0?a.slice(-4):e.initialPinnedItems??[]}catch{return e.initialPinnedItems??[]}}function rm(e){if(!e||typeof e!="object")return!1;const n=e;return typeof n.id=="string"&&typeof n.runId=="string"&&typeof n.sampleId=="string"&&Number.isInteger(n.tokenIndex)&&typeof n.tokenText=="string"&&Number.isInteger(n.layer)&&typeof n.view=="string"&&typeof n.metric=="string"&&typeof n.value=="number"&&(n.normalization==="raw"||n.normalization==="normalized")&&(n.profile===void 0||om(n.profile))&&(n.matrix===void 0||dm(n.matrix,n))&&(n.generation===void 0||lm(n.generation))}function om(e){if(!e||typeof e!="object")return!1;const n=e;return n.schemaVersion!=="1.0"||n.kind!=="attention_source_profile"&&n.kind!=="signed_attribution_profile"&&n.kind!=="mlp_activation_profile"||n.axis!=="source_token"&&n.axis!=="token"||typeof n.label!="string"||typeof n.signed!="boolean"||!Number.isInteger(n.originalLength)||n.originalLength<1||typeof n.sampled!="boolean"||!Array.isArray(n.points)||n.points.length<1||n.points.length>256||n.originalLength<n.points.length||n.sampled===(n.originalLength===n.points.length)?!1:n.points.every(a=>a!==null&&typeof a=="object"&&Number.isInteger(a.tokenIndex)&&a.tokenIndex>=0&&(a.tokenId===void 0||Number.isInteger(a.tokenId))&&typeof a.tokenText=="string"&&Number.isFinite(a.value))}function lm(e){if(!e||typeof e!="object")return!1;const n=e;if(n.schemaVersion!=="1.0"||!n.sourceRun||typeof n.sourceRun.runId!="string"||typeof n.sourceRun.sampleId!="string"||!Number.isInteger(n.layer)||n.layer<0||!["resid_post","attn_out","mlp_out"].includes(n.component)||!Number.isFinite(n.scale)||!Number.isInteger(n.positionStart)||n.positionStart<0||!Number.isInteger(n.positionEnd)||n.positionEnd<=n.positionStart||!Number.isInteger(n.targetTokenId)||typeof n.targetTokenText!="string"||!Number.isInteger(n.seed)||!Number.isInteger(n.maxNewTokens)||n.maxNewTokens<1||n.maxNewTokens>256||!Number.isFinite(n.temperature)||n.temperature<0||!Number.isInteger(n.tokenEditDistance)||n.tokenEditDistance<0||n.generationChanged!==n.tokenEditDistance>0||!Array.isArray(n.diff)||n.diff.length>512||!fi(n.original,n.maxNewTokens)||!fi(n.steered,n.maxNewTokens))return!1;let a=0,s=0;for(const i of n.diff){if(!i||typeof i!="object")return!1;const r=i.originalEnd-i.originalStart,o=i.steeredEnd-i.steeredStart;if(!["equal","replace","delete","insert"].includes(i.kind)||!Number.isInteger(i.originalStart)||!Number.isInteger(i.originalEnd)||!Number.isInteger(i.steeredStart)||!Number.isInteger(i.steeredEnd)||i.originalStart!==a||i.steeredStart!==s||r<0||o<0||i.kind==="equal"&&(r===0||r!==o)||i.kind==="replace"&&(r===0||o===0)||i.kind==="delete"&&(r===0||o!==0)||i.kind==="insert"&&(r!==0||o===0))return!1;a=i.originalEnd,s=i.steeredEnd}return a===n.original.tokens.length&&s===n.steered.tokens.length}function dm(e,n){if(!e||typeof e!="object")return!1;const a=e;if(a.schemaVersion!=="1.0"||a.kind!=="attention_matrix"||typeof a.label!="string"||!Number.isInteger(a.originalSize)||a.originalSize<1||typeof a.sampled!="boolean"||!Array.isArray(a.axis)||a.axis.length<1||a.axis.length>64||a.originalSize<a.axis.length||a.sampled===(a.originalSize===a.axis.length)||!Array.isArray(a.values)||a.values.length!==a.axis.length||n.view!=="attention"||typeof n.headId!="string"||!a.axis.every((r,o)=>r!==null&&typeof r=="object"&&Number.isInteger(r.tokenIndex)&&r.tokenIndex>=0&&(r.tokenId===void 0||Number.isInteger(r.tokenId))&&typeof r.tokenText=="string"&&(o===0||r.tokenIndex>a.axis[o-1].tokenIndex)))return!1;const i=new Set(a.axis.map(r=>r.tokenIndex));return!i.has(n.tokenIndex??-1)||n.sourceTokenIndex===void 0||!i.has(n.sourceTokenIndex)?!1:a.values.every((r,o)=>Array.isArray(r)&&r.length===a.axis.length&&r.every((l,c)=>a.axis[c].tokenIndex>a.axis[o].tokenIndex?l===null:typeof l=="number"&&Number.isFinite(l)&&l>=0&&l<=1))}function fi(e,n){return!!(e&&typeof e.text=="string"&&Array.isArray(e.tokens)&&e.tokens.length<=n&&Number.isFinite(e.targetLogit)&&Number.isFinite(e.lexicalRisk)&&e.tokens.every((a,s)=>a!==null&&typeof a=="object"&&a.index===s&&Number.isInteger(a.tokenId)&&typeof a.text=="string"))}const Ch=[{id:"individual",label:"Head",description:"Show one retained attention head."},{id:"difference",label:"Difference",description:"Cell-wise selected retained head minus baseline retained head."},{id:"mean",label:"Mean",description:"Cell-wise mean over retained heads in this layer."},{id:"max",label:"Max",description:"Cell-wise maximum over retained heads in this layer."},{id:"rollout",label:"Rollout",description:"Retained-head mean with identity residual, multiplied through the current layer."},{id:"entropy_weighted",label:"Entropy",description:"Weighted mean using normalized inverse stored head entropy."}],Ia="aggregate:",Aa="difference:",Or="rollout:retained_mean_identity";function cm(e){return`${Ia}${e}`}function Vr(e){if(!(e!=null&&e.startsWith(Ia)))return;const n=e.slice(Ia.length);return n==="mean"||n==="max"||n==="entropy_weighted"?n:void 0}function Br(e,n){return`${Aa}${encodeURIComponent(e)}:${encodeURIComponent(n)}`}function Qr(e){if(!(e!=null&&e.startsWith(Aa)))return;const[n,a,...s]=e.slice(Aa.length).split(":");if(!(!n||!a||s.length>0))try{const i=decodeURIComponent(n),r=decodeURIComponent(a);return i!==r?{selectedHeadId:i,baselineHeadId:r}:void 0}catch{return}}function um(){return Or}function Ka(e){return e===Or?{fusion:"retained_mean",residual:"identity"}:void 0}function xn(e){return e==="entropy_weighted"?"Entropy-weighted retained heads":`${e==="mean"?"Mean":"Max"} retained heads`}function gt(e){return e.rollout?`Retained attention rollout · L${e.rollout.layers[0]}–L${e.layer}`:e.difference?`${e.difference.selectedHeadId} - ${e.difference.baselineHeadId}`:e.aggregation?xn(e.aggregation):e.id}function gi(e,n,a=e,s=(r=>(r=e[0])==null?void 0:r.layer)(),i){if(Ka(n)&&s!==void 0)return mm(a,s,i);const o=Qr(n);if(o)return hm(e,o.selectedHeadId,o.baselineHeadId);const l=Vr(n);return l?ym(e,l):e.find(c=>c.id===n)??e[0]}function mm(e,n,a){const s=e.filter(d=>d.layer<=n&&!d.aggregation&&!d.difference&&!d.rollout),i=[...new Set(s.map(d=>d.layer))].sort((d,h)=>d-h);if(i.length===0||i[i.length-1]!==n)return;const r=[...new Set((a??i).filter(d=>d<=n))].sort((d,h)=>d-h);if(r.length!==i.length||r.some((d,h)=>d!==i[h]))return;const o=Math.max(0,...s.flatMap(d=>[d.distributionByToken.length,...d.distributionByToken.map(h=>h.length)]));if(o===0)return;let l=gm(o);for(const d of i){const h=s.filter(b=>b.layer===d),f=Array.from({length:o},(b,g)=>{const y=Array.from({length:o},(k,j)=>j>g?0:h.reduce((A,C)=>{var w;return A+Dn((w=C.distributionByToken[g])==null?void 0:w[j])},0)/h.length+(g===j?1:0)),u=y.reduce((k,j)=>k+j,0);return y.map(k=>u>0?k/u:0)});l=_m(f,l)}const c=s.map(d=>d.id);return{id:um(),layer:n,head:-1,role:`Retained-head mean + identity residual rollout · ${i.length} layers · ${c.length} heads`,riskContribution:s.reduce((d,h)=>d+h.riskContribution,0)/s.length,entropy:bm(l),distributionByToken:l.map((d,h)=>d.slice(0,h+1)),rollout:{fusion:"retained_mean",residual:"identity",layers:i,memberHeadIds:c},memberHeadIds:c}}function hm(e,n,a){const s=e.find(l=>l.id===n),i=e.find(l=>l.id===a);if(!s||!i||s.id===i.id||s.layer!==i.layer)return;const r=Math.max(s.distributionByToken.length,i.distributionByToken.length),o=Array.from({length:r},(l,c)=>{var h,f;const d=Math.max(((h=s.distributionByToken[c])==null?void 0:h.length)??0,((f=i.distributionByToken[c])==null?void 0:f.length)??0);return Array.from({length:d},(b,g)=>{var y,u;return Dn((y=s.distributionByToken[c])==null?void 0:y[g])-Dn((u=i.distributionByToken[c])==null?void 0:u[g])})});return{id:Br(s.id,i.id),layer:s.layer,head:-1,role:`Cell-wise retained-head difference · ${s.id} minus ${i.id}`,riskContribution:s.riskContribution-i.riskContribution,entropy:s.entropy-i.entropy,distributionByToken:o,difference:{selectedHeadId:s.id,baselineHeadId:i.id},memberHeadIds:[s.id,i.id]}}function pm(e,n){const a=Qr(n);return!!(a&&e.some(s=>s.id===a.selectedHeadId)&&e.some(s=>s.id===a.baselineHeadId))}function ym(e,n){if(e.length===0)return;const a=fm(e,n),s=Math.max(...e.map(o=>o.distributionByToken.length)),i=Array.from({length:s},(o,l)=>{const c=Math.max(0,...e.map(d=>{var h;return((h=d.distributionByToken[l])==null?void 0:h.length)??0}));return Array.from({length:c},(d,h)=>{const f=e.map(b=>{var g;return Dn((g=b.distributionByToken[l])==null?void 0:g[h])});return n==="max"?Math.max(...f):f.reduce((b,g,y)=>b+g*a[y],0)})}),r=o=>n==="max"?Math.max(...o):o.reduce((l,c,d)=>l+c*a[d],0);return{id:cm(n),layer:e[0].layer,head:-1,role:`${xn(n)} · derived from ${e.length} retained heads`,riskContribution:r(e.map(o=>o.riskContribution)),entropy:r(e.map(o=>o.entropy)),distributionByToken:i,aggregation:n,memberHeadIds:e.map(o=>o.id)}}function Jr(e,n,a){var i;const s=n===void 0?"":a===void 0?`[${n}]`:`[${n},${a}]`;return e.difference?`derived.attention.difference[${e.difference.selectedHeadId}-${e.difference.baselineHeadId}]${s}`:e.rollout?`derived.attention.rollout.retained_mean_identity[L${e.rollout.layers.join(",L")};${e.rollout.memberHeadIds.join(",")}]${s}`:e.aggregation?`derived.attention.${e.aggregation}[${((i=e.memberHeadIds)==null?void 0:i.join(","))??"retained"}]${s}`:`blocks.${e.layer}.attn.hook_pattern[${e.head}]${s}`}function Gr(e){return e.rollout?"attention_retained_rollout_mean_identity":e.difference?"attention_retained_head_difference":e.aggregation?`attention_retained_${e.aggregation}`:"attention_probability"}function Ta(e,n){var i;if(e.rollout)return{label:"Retained attention rollout",method:`per-layer retained-head arithmetic mean, identity residual addition, row normalization, then matrix product through layer ${e.layer}`,semantics:"Client-derived descriptive path proxy over only the artifact-retained heads and available layers. It is not a full-model rollout, attribution, or causal evidence.",normalization:"A_hat_l = row_normalize(mean_retained(A_l) + I); R_l = A_hat_l × R_(l-1); R_-1 = I",kind:"derived_proxy"};if(e.difference)return{label:"Retained-head probability difference",method:`cell-wise ${e.difference.selectedHeadId} minus ${e.difference.baselineHeadId}`,semantics:"Client-derived signed difference between two retained artifact heads in the same layer; positive cells favor the selected head and negative cells favor the baseline. It is descriptive, not causal evidence.",normalization:"none; subtraction of stored raw softmax probabilities on the exact token axes",kind:"derived_proxy"};if(!e.aggregation)return n;const a=((i=e.memberHeadIds)==null?void 0:i.length)??0,s=e.aggregation==="mean"?"cell-wise arithmetic mean":e.aggregation==="max"?"cell-wise maximum":"cell-wise weighted mean with normalized inverse stored head entropy";return{label:xn(e.aggregation),method:`${s} over ${a} retained artifact heads`,semantics:"Client-derived descriptive aggregate over the heads retained in this artifact; it is neither a full-model aggregate nor causal evidence.",normalization:"none; each source cell is aggregated from stored raw softmax probabilities",kind:"derived_proxy"}}function fm(e,n){if(n!=="entropy_weighted")return e.map(()=>1/e.length);const a=e.map(i=>1/Math.max(1e-6,i.entropy)),s=a.reduce((i,r)=>i+r,0);return a.map(i=>i/s)}function Dn(e){return Number.isFinite(e)?Math.max(0,Math.min(1,e)):0}function gm(e){return Array.from({length:e},(n,a)=>Array.from({length:e},(s,i)=>a===i?1:0))}function _m(e,n){return e.map((a,s)=>a.map((i,r)=>{var l,c;if(r>s)return 0;let o=0;for(let d=r;d<=s;d+=1)o+=(((l=e[s])==null?void 0:l[d])??0)*(((c=n[d])==null?void 0:c[r])??0);return o}))}function bm(e){return e.length===0?0:e.reduce((n,a)=>n+a.reduce((s,i)=>i>0?s-i*Math.log(i):s,0),0)/e.length}const xm=it(()=>st(()=>import("./AttentionPatternMatrix-Cd-NyDqB.js"),__vite__mapDeps([0,1,2,3,4,5,6,7])),"AttentionPatternMatrix"),wm=it(()=>st(()=>import("./ResidualLogitLens-C9NFCh1i.js"),__vite__mapDeps([8,1,5])),"ResidualLogitLens"),km=it(()=>st(()=>import("./MLPActivationMatrix-DAC0KnPJ.js"),__vite__mapDeps([9,1,2,3,4,5,6,7])),"MLPActivationMatrix"),vm=it(()=>st(()=>import("./SignedAttributionMatrix-C_NUf6xD.js"),__vite__mapDeps([10,1,2,3,4,5,7])),"SignedAttributionMatrix"),jm=it(()=>st(()=>import("./NLAFidelityMatrix-Yw9l0HP-.js"),__vite__mapDeps([11,1,2,3,4,5,7])),"NLAFidelityMatrix"),Im=it(()=>st(()=>import("./AttributionJobPanel-CT0PasHz.js"),__vite__mapDeps([12,1,5,7])),"AttributionJobPanel"),Am=it(()=>st(()=>import("./NLAJobPanel-D9lvlc6d.js"),__vite__mapDeps([13,1,5,7])),"NLAJobPanel"),Tm=it(()=>st(()=>import("./PatchingJobPanel-Cuj0kn0X.js"),__vite__mapDeps([14,1,5,7])),"PatchingJobPanel"),Sm=it(()=>st(()=>import("./PatchingCausalMatrix-plYPnhg4.js"),__vite__mapDeps([15,1,4,5,7])),"PatchingCausalMatrix"),Cm=it(()=>st(()=>import("./InterventionJobPanel-BdPDPHyE.js"),__vite__mapDeps([16,1,5,7])),"InterventionJobPanel"),Nm=it(()=>st(()=>import("./InterventionComparison-Dfi76Y3W.js"),__vite__mapDeps([17,1,5])),"InterventionComparison"),Rm=it(Xr,"CompareDrawer");function Xr(){return st(()=>import("./CompareDrawer-47BqcgwV.js"),__vite__mapDeps([18,1,2,5,7]))}function wt(){Xr().catch(()=>{})}const Zr=m.createContext(Yi);function Oe(e,n="tokenRisk"){return Pe(e,n,"compact")}function eo(e){return Ea(e,"attribution","compact")}function pt(){return m.useContext(Zr)}function Lm(){const e=new URLSearchParams(window.location.search).get("layout");return e==="focus"||e==="dense"?e:(window.sessionStorage.getItem("safelens-workspace-layout")??window.localStorage.getItem("safelens-workspace-layout"))==="dense"?"dense":"focus"}function _i(){const e=window.location.pathname.replace(/\/+$/,"");if(e==="/dataset-test")return"dataset-test";if(e==="/explorer")return"explorer";const n=new URLSearchParams(window.location.search);return["view","mode","run","sample","token","layer","head","neuron","track","metric"].some(s=>n.has(s))?"explorer":"home"}function $m(){const[e,n]=m.useState(_i),a=Sc(Yi,e==="explorer"),s=a.activeRecord.run,[i,r]=m.useState(null),[o,l]=m.useState(null),c=Ce.useRef(0),d=Ce.useRef(null),h=Ce.useRef(null),f=Ce.useRef(a.activeRecord.key),b=Ce.useCallback((u,k="selection")=>{d.current!==null&&window.clearTimeout(d.current),h.current!==null&&window.clearTimeout(h.current),d.current=window.setTimeout(()=>{const j=++c.current;l({id:j,kind:k,message:u,visible:!0}),h.current=window.setTimeout(()=>{l(T=>(T==null?void 0:T.id)===j?{...T,visible:!1}:T)},1900),d.current=null},k==="run"?0:60)},[]);m.useEffect(()=>{f.current!==a.activeRecord.key&&(f.current=a.activeRecord.key,b(Wm(a.activeRecord.run,i,Rc(a.activeRecord.key)),"run"))},[b,a.activeRecord.key,a.activeRecord.run,i]),m.useEffect(()=>()=>{d.current!==null&&window.clearTimeout(d.current),h.current!==null&&window.clearTimeout(h.current)},[]),m.useEffect(()=>{function u(){n(_i())}return window.addEventListener("popstate",u),()=>window.removeEventListener("popstate",u)},[]);function g(){window.history.pushState(null,"","/"),n("home")}function y(){window.history.pushState(null,"","/dataset-test"),n("dataset-test")}return t.jsx(Zr.Provider,{value:s,children:e==="home"?t.jsx(Eu,{records:a.records,activeRecord:a.activeRecord,remoteState:a.remoteState,onOpenDatasetTest:y,onSelectConversation:u=>a.selectRun(u,void 0,"none"),onRunReady:(u,k)=>{var j,T;return a.addGeneratedRun(u,k.id,void 0,{kind:k.kind==="prompt-run"?"prompt":k.kind,updateLocation:!1,conversationId:(j=u.metadata)==null?void 0:j.conversationId,turnIndex:(T=u.metadata)==null?void 0:T.turnIndex})},onRemoveRuns:a.removeRuns}):e==="dataset-test"?t.jsx(Fu,{onOpenChat:g}):t.jsx(Em,{run:s,library:a,pendingSession:i,onQueueSession:r,onSessionApplied:()=>r(null),onContextChange:b,contextNotice:o,onOpenHome:g},a.activeRecord.key)})}function Em({run:e,library:n,pendingSession:a,onQueueSession:s,onSessionApplied:i,onContextChange:r,contextNotice:o,onOpenHome:l}){var as,ss,is,rs,os,ls;const[c,d]=m.useState(!1),[h,f]=m.useState(Lm),[b,g]=m.useState(),[y,u]=m.useState(()=>new URLSearchParams(window.location.search).get("setup")==="prompt"),[k,j]=m.useState(!1),[T,A]=m.useState(!1),[C,w]=m.useState(!1),[I,L]=m.useState(!1),[M,q]=m.useState(!1),[X,H]=m.useState(!1),[V,oe]=m.useState(!1),de=Ce.useRef(null),P=Ce.useRef(null),S=Ce.useRef(null),Z=Ce.useRef(!0),K=Ce.useRef(null),N=Ce.useRef(null),v=Ce.useRef(null),ne=Ce.useRef(null),W=Ce.useRef(null),ee=Ce.useRef(null),D=Ce.useRef(null),$=Ce.useRef(null),F=Ce.useRef(null),O=Ce.useRef(null),E=io(e.tokens),Y=e.layers[e.layers.length-1]??0,le=`${n.activeRecord.sourceName} · ${n.activeRecord.sourceType}${((as=n.activeRecord.hydration)==null?void 0:as.mode)==="partial"?" · range chunk":""}`,R=am({runId:e.runId,sampleId:e.sampleId,tokenIndex:E[0]??((ss=e.tokens[0])==null?void 0:ss.index)??0,tokenIndices:e.tokens.map(x=>x.index),layers:e.layers,layer:Y,view:"overview",headId:((is=e.attentionHeads.find(x=>x.layer===Y))==null?void 0:is.id)??"",nlaComponent:((rs=e.nla.find(x=>x.layer===Y))==null?void 0:rs.component)??"resid_post",neuronId:((os=e.mlpNeurons.find(x=>x.layer===Y))==null?void 0:os.id)??"",trackName:((ls=e.attributionMethods.find(x=>x.available))==null?void 0:ls.id)??"",metric:"residual_direction",initialPinnedItems:Dm(e,E,Y,le)}),{state:J}=R,U=J.tokenIndex,ce=J.sourceTokenIndex??U,te=J.layer,ue=J.nlaComponent,z=J.view,re=uh(z),pe=nh(re,J.metric),ve=J.headId,ae=J.attentionEdgeMode,G=J.neuronId,me=J.trackName,he=J.pinnedItems,[be,se]=m.useState(null),[ge,Ae]=m.useState(null),[He,Fe]=m.useState("top"),[ct,It]=m.useState({mode:"token",metric:"risk",query:""}),[en,tn]=m.useState({}),ke=n.viewHydration(z,te,U,ce),co=n.viewHydration("nla",te,U);tl({rootRef:F,view:z,ready:ke.ready}),m.useEffect(()=>{var x,B;!a||a.workspace.runId!==e.runId||a.workspace.sampleId!==e.sampleId||(R.restoreSession(gh(a,e,J)),Fe(a.filters.evidence),It(_h(a,e)),tn(bh(a.matrices)),g(a.pinnedItems.some(xe=>{var Ie;return xe.id===((Ie=a.compare)==null?void 0:Ie.baselineId)})?(x=a.compare)==null?void 0:x.baselineId:(B=a.pinnedItems[0])==null?void 0:B.id),d(!1),j(!1),n.setMessage({tone:"success",title:"Analysis session restored",details:[`${e.runId} / ${e.sampleId} · ${De(a.selection.view)}`]}),i())},[a,e.runId,e.sampleId]),m.useEffect(()=>{n.ensureViewHydrated(z,te,U,ce)},[n.activeRecord.key,z,te,U,ce]),m.useEffect(()=>{var x;he.some(B=>B.id===b)||g((x=he[0])==null?void 0:x.id)},[b,he]);const At=m.useMemo(()=>e.attentionHeads.filter(x=>x.layer===te),[e.attentionHeads,te]),Jn=m.useMemo(()=>e.mlpNeurons.filter(x=>x.layer===te),[e.mlpNeurons,te]),_t=!!Ka(ve)&&ke.partial,we=m.useMemo(()=>_t?At[0]??e.attentionHeads[0]:gi(At,ve,e.attentionHeads,te,e.layers)??At[0]??e.attentionHeads[0],[At,_t,e.attentionHeads,e.layers,ve,te]),Me=e.attributionMethods.find(x=>x.id===me)??e.attributionMethods.find(x=>x.available)??e.attributionMethods[0],wn=Me.rows.find(x=>x.layer===te)??Me.rows[0],kn={name:Me.label,values:(wn==null?void 0:wn.values)??e.tokens.map(()=>0)},Ze=e.tokens[U],Gn=e.residualCells.find(x=>x.layer===te&&x.tokenIndex===U),bt=Yn(e.nla,U,te,ue),Ne=Jn.find(x=>x.id===G)??[...Jn].sort((x,B)=>Math.abs(B.activationsByToken[U]??0)-Math.abs(x.activationsByToken[U]??0))[0],uo=m.useMemo(()=>e.tokens.reduce((x,B)=>Math.max(x,B.risk),0),[e.tokens]),mo=m.useMemo(()=>e.tokens.reduce((x,B)=>x+B.attribution,0)/Math.max(1,e.tokens.length),[e.tokens]),ho=!co.ready||!bt||bt.status==="unavailable"?"n/a":Oe(bt.cosine,"nla_cosine"),rt=e.tokens.findIndex(x=>x.index===U),zt=ke.ready?un({run:e,view:z,selectedToken:U,selectedSourceToken:ce,selectedLayer:te,selectedNlaComponent:ue,selectedHead:we,selectedNeuron:Ne,selectedAttributionMethod:Me,metric:J.metric,normalization:J.normalization,sourceArtifact:`${n.activeRecord.sourceName} · ${n.activeRecord.sourceType}${ke.partial?" · range chunk":""}`}):zm(e,z,te,U,ke.error,ke.cancelled),Ba=hh(z,zt),po=he.filter(x=>x.runId===e.runId&&x.sampleId===e.sampleId).map(x=>x.tokenIndex),yo=Za(U).id,Tt=he.some(x=>x.id===yo),Dt=ke.ready&&!_t&&zt.status==="available"&&(z!=="attribution"||Me.available)&&(z!=="nla"||(bt==null?void 0:bt.status)==="available")&&(z!=="intervention"||!!e.intervention),vn=h==="dense"||X,Yt=mh({view:z,tokenText:Ze.text,tokenIndex:U,sourceTokenIndex:ce,tokenRange:J.tokenRange,layer:te,metric:J.metric,normalization:J.normalization,headId:we.id,neuronId:Ne==null?void 0:Ne.id,nlaComponent:ue,attributionMethod:Me.label,attentionEdgeMode:ae}),Qa=Ce.useRef(Yt.signature);m.useEffect(()=>{Qa.current!==Yt.signature&&(Qa.current=Yt.signature,r(Yt.message))},[Yt.message,Yt.signature,r]),m.useEffect(()=>{k||A(!1)},[k]),m.useEffect(()=>{var x;k&&((x=D.current)==null||x.scrollTo({top:0,behavior:"auto"}))},[T,k]),m.useEffect(()=>{function x(Ie){const Te=$.current;if(!Te||Te.pointerId!==Ie.pointerId)return;const _e=Te.startY-Ie.clientY;_e>=48?($.current=null,A(!0)):_e<=-48&&($.current=null,A(!1))}function B(Ie){const Te=$.current;if(!Te||Te.pointerId!==Ie.pointerId)return;$.current=null;const _e=Te.startY-Ie.clientY;_e>=48&&A(!0),_e<=-48&&A(!1)}function xe(Ie){var Te;((Te=$.current)==null?void 0:Te.pointerId)===Ie.pointerId&&($.current=null)}return window.addEventListener("pointermove",x),window.addEventListener("pointerup",B),window.addEventListener("pointercancel",xe),()=>{window.removeEventListener("pointermove",x),window.removeEventListener("pointerup",B),window.removeEventListener("pointercancel",xe)}},[]),Mn({open:y,dialogRef:ee,initialFocusRef:ne,returnFocusRef:P,onClose:()=>u(!1)}),Mn({open:k,dialogRef:D,initialFocusRef:W,returnFocusRef:S,restoreFocusRef:Z,onClose:()=>j(!1)}),m.useEffect(()=>{!_t&&(!ke.partial||z==="attention"&&ke.ready)&&we.id!==ve&&R.selectHead(we.id,"replace")},[ke.partial,ke.ready,_t,we.id,ve,z]),m.useEffect(()=>{if(z!=="attention"||!_t)return;const x=`${n.activeRecord.key}:${te}`;O.current!==x&&fo(x)},[n.activeRecord.key,_t,te,z]),m.useEffect(()=>{(!ke.partial||z==="mlp"&&ke.ready)&&Ne&&Ne.id!==G&&R.selectNeuron(Ne.id,"replace")},[ke.partial,ke.ready,G,Ne==null?void 0:Ne.id,z]),m.useEffect(()=>{(!ke.partial||z==="attribution"&&ke.ready)&&Me.id!==me&&R.selectTrack(Me.id,"replace")},[ke.partial,ke.ready,Me.id,me,z]),m.useEffect(()=>{function x(B){if(B.defaultPrevented||c||y||k||C)return;const xe=B.target,Ie=(xe==null?void 0:xe.closest("input, textarea, select, [contenteditable='true']"))||(xe==null?void 0:xe.isContentEditable);if(B.altKey&&B.shiftKey&&!B.ctrlKey&&!B.metaKey&&B.key.toLowerCase()==="c"){if(Ie||he.length===0)return;B.preventDefault(),v.current=K.current,wt(),d(!0);return}if(xe!=null&&xe.closest("input, textarea, select, button, a, [role='button'], [role='tab'], [role='radio'], [role='grid']")||Ie||B.key!=="ArrowLeft"&&B.key!=="ArrowRight")return;const Te=B.key==="ArrowLeft"?-1:1,_e=Math.max(0,Math.min(e.tokens.length-1,rt+Te));if(_e===rt)return;B.preventDefault();const Ee=e.tokens[_e].index;R.selectToken(Ee),bi(Ee,Ae)}return window.addEventListener("keydown",x),()=>window.removeEventListener("keydown",x)},[c,k,y,he.length,C,e.tokens,rt]);function Ja(x){et(x)}function et(x){R.selectToken(x),h==="focus"&&(L(!0),q(!1)),ft("selection-commit",{view:z,token:x}),bi(x,Ae)}function Ga(x){const B=fh(x);if(B){if(Z.current=!1,j(!1),R.selectView(B.view),!B.anchorId){window.requestAnimationFrame(()=>{var xe;(xe=F.current)==null||xe.scrollIntoView({block:"start"})});return}nn(B.anchorId)}}async function nn(x){if(j(!1),oe(!0),ke.partial)try{await n.loadFullActiveRun()}catch(B){n.setMessage({tone:"error",title:"Experiment setup could not be opened",details:[B instanceof Error?B.message:"The complete Run could not be loaded."]});return}window.requestAnimationFrame(()=>ro(x))}async function Ye(x,B=te,xe={}){if(!Dt)return;const Ie=xe.sourceTokenIndex??ce,Te=xe.neuronId?e.mlpNeurons.find(Ee=>Ee.id===xe.neuronId):Ne;let _e=Za(x,B,xe);if(he.some(Ee=>Ee.id===_e.id)){R.togglePin(_e);return}if(z==="attention"&&ke.partial)try{const Ee=await n.loadFullActiveRun(),Ue=Ee.attentionHeads.filter(Be=>Be.layer===B),ze=gi(Ue,we.id,Ee.attentionHeads,B,Ee.layers);if(!ze)throw new Error(`Attention head ${we.id} is missing from the complete artifact.`);const xt=Ee.tokens.filter(Be=>Be.index<=x),Se=ln({kind:"attention_source_profile",label:`${gt(ze)} · destination token ${x}`,axis:"source_token",signed:!!ze.difference,tokens:xt,values:ze.distributionByToken[x]??[],preserveTokenIndex:Ie}),We=ze.difference?void 0:Ai(ze,Ee.tokens,Ie,x);if(!Se||!ze.difference&&!We)throw new Error("The complete artifact does not contain a valid attention matrix.");_e={..._e,profile:Se,...We?{matrix:We}:{},assessment:Ut(un({run:Ee,view:z,selectedToken:x,selectedSourceToken:Ie,selectedLayer:B,selectedNlaComponent:ue,selectedHead:ze,selectedNeuron:Ne,selectedAttributionMethod:Me,metric:_e.metric,normalization:_e.normalization,sourceArtifact:`${n.activeRecord.sourceName} · ${n.activeRecord.sourceType} · full artifact`}))}}catch(Ee){n.setMessage({tone:"error",title:"Attention matrix pin failed",details:[Ee instanceof Error?Ee.message:"The complete attention artifact could not be loaded."]});return}if(z==="mlp"&&ke.partial)try{const Ee=await n.loadFullActiveRun(),Ue=Ee.mlpNeurons.find(We=>We.id===(Te==null?void 0:Te.id));if(!Ue)throw new Error(`MLP neuron ${(Te==null?void 0:Te.id)??"unknown"} is missing from the complete artifact.`);const ze=da(J.metric),xt=Ue.activationsByToken.map(We=>Rn(We,Ue.maxAbsoluteActivation,ze)),Se=ln({kind:"mlp_activation_profile",label:`${Ue.id} · ${ki(ze)}`,axis:"token",signed:ze==="mlp_signed_activation",tokens:Ee.tokens,values:xt,preserveTokenIndex:x});if(!Se)throw new Error("The complete artifact does not contain a valid MLP activation profile.");_e={..._e,profile:Se,assessment:Ut(un({run:Ee,view:z,selectedToken:x,selectedSourceToken:Ie,selectedLayer:B,selectedNlaComponent:ue,selectedHead:we,selectedNeuron:Ue,selectedAttributionMethod:Me,metric:_e.metric,normalization:_e.normalization,sourceArtifact:`${n.activeRecord.sourceName} · ${n.activeRecord.sourceType} · full artifact`}))}}catch(Ee){n.setMessage({tone:"error",title:"MLP profile pin failed",details:[Ee instanceof Error?Ee.message:"The complete MLP artifact could not be loaded."]});return}R.togglePin(_e)}async function fo(x=`${n.activeRecord.key}:${te}`){var B;O.current=x;try{await n.loadFullActiveRun(),O.current===x&&(O.current=null)}catch(xe){if(O.current!==x)return;O.current=null;const Ie=(B=At[0])==null?void 0:B.id;Ie&&R.selectHead(Ie,"replace"),n.setMessage({tone:"error",title:"Attention rollout loading failed",details:[xe instanceof Error?xe.message:"The complete attention artifact could not be loaded."]})}}function go(){var B;O.current=null,n.cancelRemote();const x=(B=At[0])==null?void 0:B.id;x&&R.selectHead(x,"replace")}function Xa(x){if(x.runId===e.runId&&x.sampleId===e.sampleId){R.restorePin(x);return}n.selectRun(ut(x),x)}function Za(x,B=te,xe={}){var us,ms;const Ie=e.tokens.find(Qe=>Qe.index===x)??e.tokens[0],Te=xe.sourceTokenIndex??ce,_e=xe.neuronId?e.mlpNeurons.find(Qe=>Qe.id===xe.neuronId):Ne,Ee=xe.nlaComponent??ue,Ue=Me.rows.find(Qe=>Qe.layer===B)??wn,ze=so(e,re,pe).find(Qe=>Qe.row===B&&Qe.column===x),xt=(us=e.patching)==null?void 0:us.cells.find(Qe=>Qe.layer===B&&Qe.tokenIndex===x),Se=e.intervention,We=Yn(e.nla,x,B,Ee),Be=z==="overview"?"tokenRisk":z==="attention"?Gr(we):z==="mlp"?da(J.metric):z==="attribution"?me:z==="nla"||z==="patching"?J.metric:z==="intervention"?"intervention_logit_delta":pe,Xn=z==="attention"||z==="intervention"||z==="mlp"&&Be!=="mlp_normalized_activation"?"raw":J.normalization,_o=z==="overview"?Ie.risk:z==="attention"?((ms=we.distributionByToken[x])==null?void 0:ms[Te])??0:z==="mlp"?Rn((_e==null?void 0:_e.activationsByToken[x])??0,(_e==null?void 0:_e.maxAbsoluteActivation)??1,Be):z==="attribution"?(Ue==null?void 0:Ue.values[x])??0:z==="nla"?ca(Be)==="mse"?(We==null?void 0:We.mse)??0:ca(Be)==="fve"?(We==null?void 0:We.fve)??0:(We==null?void 0:We.cosine)??0:z==="patching"?oo(xt,J.metric)??0:z==="intervention"?(Se==null?void 0:Se.deltas.targetLogit)??0:J.normalization==="raw"?(ze==null?void 0:ze.rawValue)??0:(ze==null?void 0:ze.value)??0,ds=z==="attention"?we.id:void 0,cs=z==="mlp"?_e==null?void 0:_e.id:void 0,bo=z==="attribution"?me:void 0,xo=z==="attribution"?{label:Me.label,method:Me.id,semantics:Me.description,normalization:Me.normalization,kind:Me.evidenceKind}:z==="nla"?{label:"NLA fidelity",method:"exact NLA decoder reconstruction",semantics:"Exact token/layer/component reconstruction fidelity for a compatible profile.",normalization:"stored method metric",kind:"safety_method"}:z==="patching"?Oa(e,J.metric):z==="intervention"?Va(e):z==="attention"?Ta(we,e.metricProvenance.attentionHeatmap):vi(e,z,Be),wo=z==="attention"?Jr(we):z==="mlp"?`layer_${(_e==null?void 0:_e.layer)??B}.post[:, ${(_e==null?void 0:_e.neuron)??0}]`:z==="attribution"?Ue==null?void 0:Ue.sourceKey:z==="nla"?We==null?void 0:We.source:z==="patching"?xt==null?void 0:xt.sourceKey:z==="intervention"?Se==null?void 0:Se.vector.sourceKey:(ze==null?void 0:ze.sourceKey)??`layer_${B}.resid_post[${x}]`,ko=z==="attention"&&!ke.partial?ln({kind:"attention_source_profile",label:`${gt(we)} · destination token ${x}`,axis:"source_token",signed:!!we.difference,tokens:e.tokens.filter(Qe=>Qe.index<=x),values:we.distributionByToken[x]??[],preserveTokenIndex:Te}):z==="attribution"&&Me.signed?ln({kind:"signed_attribution_profile",label:`${Me.label} · L${B}`,axis:"token",signed:!0,tokens:e.tokens,values:(Ue==null?void 0:Ue.values)??[],preserveTokenIndex:x}):z==="mlp"&&_e&&!ke.partial?ln({kind:"mlp_activation_profile",label:`${_e.id} · ${ki(Be)}`,axis:"token",signed:Be==="mlp_signed_activation",tokens:e.tokens,values:_e.activationsByToken.map(Qe=>Rn(Qe,_e.maxAbsoluteActivation,Be)),preserveTokenIndex:x}):void 0,vo=z==="attention"&&!ke.partial&&!we.difference?Ai(we,e.tokens,Te,x):void 0,jo=z==="intervention"&&Se?{schemaVersion:"1.0",sourceRun:Se.sourceRun,layer:Se.layer,component:Se.component,scale:Se.scale,positionStart:Se.positionStart,positionEnd:Se.positionEnd,targetTokenId:Se.targetTokenId,targetTokenText:Se.targetTokenText,seed:Se.seed,maxNewTokens:Se.maxNewTokens,temperature:Se.temperature,original:{text:Se.original.text,tokens:Se.original.tokens,targetLogit:Se.original.targetLogit,lexicalRisk:Se.original.lexicalRisk},steered:{text:Se.steered.text,tokens:Se.steered.tokens,targetLogit:Se.steered.targetLogit,lexicalRisk:Se.steered.lexicalRisk},tokenEditDistance:Se.deltas.tokenEditDistance,generationChanged:Se.deltas.generationChanged,diff:Se.diff}:void 0,Io=Ut(un({run:e,view:z,selectedToken:x,selectedSourceToken:Te,selectedLayer:B,selectedNlaComponent:Ee,selectedHead:we,selectedNeuron:_e,selectedAttributionMethod:Me,metric:Be,normalization:Xn,sourceArtifact:`${n.activeRecord.sourceName} · ${n.activeRecord.sourceType}${ke.partial?" · range chunk":""}`}));return{id:[e.runId,e.sampleId,x,B,z,Be,Xn,ds??"-",cs??"-",z==="attention"?Te:z==="nla"?Ee:"-"].join(":"),runId:e.runId,sampleId:e.sampleId,tokenIndex:x,tokenText:Ie.text,tokenId:Ie.tokenId,tokenSource:Ie.source,modelName:e.modelName,modelSource:e.modelSource,layer:B,view:z,component:z==="nla"?(We==null?void 0:We.component)??Ee:re,metric:Be,value:_o,normalization:Xn,headId:ds,neuronId:cs,trackName:bo,sourceTokenIndex:z==="attention"?Te:void 0,sourceKey:wo,provenance:xo,profile:ko,matrix:vo,generation:jo,assessment:Io,capturedAt:new Date().toISOString()}}function jn(){var Te,_e;const x={exportedAt:new Date().toISOString(),runId:e.runId,sampleId:e.sampleId,model:{name:e.modelName,source:e.modelSource},selection:{view:z,normalization:J.normalization,tokenRange:J.tokenRange,token:Ze,layer:te,component:re,nlaComponent:z==="nla"?ue:void 0,attentionHead:re==="attention"?ke.partial?{id:we.id,layer:we.layer,head:we.head,role:we.role,entropy:we.entropy,riskContribution:we.riskContribution,aggregation:we.aggregation,difference:we.difference,rollout:we.rollout,memberHeadIds:we.memberHeadIds,partial:!0}:we:void 0,attentionPair:z==="attention"?{sourceToken:e.tokens[ce],destinationToken:Ze,probability:we.difference?void 0:((Te=we.distributionByToken[U])==null?void 0:Te[ce])??0,probabilityDelta:we.difference?((_e=we.distributionByToken[U])==null?void 0:_e[ce])??0:void 0,aggregation:we.aggregation,difference:we.difference,rollout:we.rollout,memberHeadIds:we.memberHeadIds}:void 0,mlpNeuron:re==="mlp"&&Ne?ke.partial?{id:Ne.id,layer:Ne.layer,neuron:Ne.neuron,label:Ne.label,selectedActivation:Ne.activationsByToken[U],maxAbsoluteActivation:Ne.maxAbsoluteActivation,partial:!0}:Ne:void 0,nla:bt,residual:Gn,attributionTrack:ke.partial?{name:kn.name,tokenIndex:U,value:kn.values[U],partial:!0}:kn,patching:e.patching,intervention:e.intervention,pinnedEvidence:he},metricProvenance:e.metricProvenance,activeMetricProvenance:z==="attention"?Ta(we,e.metricProvenance.attentionHeatmap):vi(e,z,J.metric),evidenceAssessment:Ut(zt),dataAccess:ke.partial?{protocol:"safelens-chunks-v1",scope:`${De(z)} · L${te} · token ${U}`,completeArtifact:!1}:{completeArtifact:!0}},B=new Blob([JSON.stringify(x,null,2)],{type:"application/json"}),xe=URL.createObjectURL(B),Ie=document.createElement("a");Ie.href=xe,Ie.download=`${e.runId}-token-${U}-layer-${te}.json`,Ie.click(),window.setTimeout(()=>URL.revokeObjectURL(xe),0)}async function es(){let x;try{x=await n.loadFullActiveRun()}catch(_e){n.setMessage({tone:"error",title:"Complete artifact export failed",details:[_e instanceof Error?_e.message:"The full Run could not be loaded."]});return}const B={schema_version:"1.0",run:{run_id:x.runId,model_name:x.modelName,model_source:x.modelSource},samples:[x],metrics:Object.keys(x.metricProvenance),artifacts:{embedded:!0}},xe=new Blob([JSON.stringify(B,null,2)],{type:"application/json"}),Ie=URL.createObjectURL(xe),Te=document.createElement("a");Te.href=Ie,Te.download=`${x.runId}-${x.sampleId}-explorer-artifact.json`,Te.click(),window.setTimeout(()=>URL.revokeObjectURL(Ie),0)}function ts(){const{pinnedItems:x,...B}=J,xe={kind:Wa,schemaVersion:"1.0",exportedAt:new Date().toISOString(),workspace:{runId:e.runId,sampleId:e.sampleId,modelName:e.modelName,modelSource:e.modelSource,sourceName:n.activeRecord.sourceName,artifactId:n.activeRecord.artifactId},selection:B,pinnedItems:x,timeline:ct,compare:{baselineId:b},activeEvidenceAssessment:Ut(zt),matrices:en,filters:{evidence:He}},Ie=new Blob([JSON.stringify(xe,null,2)],{type:"application/json"}),Te=URL.createObjectURL(Ie),_e=document.createElement("a");_e.href=Te,_e.download=`${e.runId}-${e.sampleId}-analysis-session.json`,_e.click(),window.setTimeout(()=>URL.revokeObjectURL(Te),0)}function ns(x){const B=ut(x.workspace);if(!n.records.some(xe=>xe.key===B)){n.setMessage({tone:"error",title:"Analysis session Run is not available",details:[`Load ${x.workspace.runId} / ${x.workspace.sampleId} before restoring this session.`]});return}s(x),u(!1),B!==n.activeRecord.key&&n.selectRun(B)}return t.jsx(al,{snapshots:en,onChange:(x,B)=>tn(xe=>({...xe,[x]:B})),children:t.jsxs("div",{className:`app-shell layout-${h}`,children:[t.jsx("a",{className:"skip-link",href:"#analysis-workspace",children:"Skip to analysis workspace"}),t.jsxs("header",{className:"topbar",children:[t.jsxs("button",{className:"brand-block",type:"button","aria-label":"Return to SafeLens home",onClick:l,children:[t.jsx("div",{className:"brand-mark",children:t.jsx(Qt,{size:22})}),t.jsxs("div",{children:[t.jsx("h1",{children:"SafeLens Local Explorer"}),t.jsx("p",{children:e.runId})]})]}),t.jsxs("div",{className:"run-status",title:"Select an available local run and sample",children:[t.jsx(yt,{size:15}),t.jsxs("div",{className:"run-status-selection",children:[t.jsxs("span",{className:"mobile-current-run",children:[t.jsx("em",{children:"Run"}),t.jsx("strong",{title:e.runId,children:e.runId})]}),t.jsxs("span",{className:"run-sample-selection",children:[t.jsx("em",{className:"mobile-run-context-label",children:"Sample"}),t.jsx(Fi,{records:n.records,ariaLabel:"Quick run selector",value:n.activeRecord.key,onChange:n.selectRun,formatNativeLabel:x=>x.sampleId})]})]}),t.jsxs("b",{className:"run-layer-count",children:[e.layers.length," layers"]}),t.jsx("button",{ref:de,className:"mobile-run-library-trigger","aria-label":"Open run library",title:"Open run library",onClick:x=>{P.current=x.currentTarget,u(!0)},children:t.jsx(yt,{size:16})})]}),t.jsxs("div",{className:"run-meta",children:[t.jsx(la,{label:"Max safety proxy",shortLabel:"Safety max",value:Oe(uo),tone:"danger"}),t.jsx(la,{label:"Mean attention proxy",shortLabel:"Attention mean",value:Oe(mo,"attention_probability"),tone:"blue"}),t.jsx(la,{label:"NLA cosine",shortLabel:"NLA cosine",value:ho,tone:"green"})]}),t.jsxs("div",{className:"topbar-actions",children:[t.jsx("button",{className:"icon-button desktop-inspector-trigger",title:"Inspect selected evidence","aria-label":"Inspect selected evidence",onClick:x=>{S.current=x.currentTarget,j(!0)},children:t.jsx(pa,{size:18})}),t.jsx("button",{className:"icon-button layout-toggle",title:`Switch to ${h==="focus"?"dense":"focus"} layout`,"aria-label":`Switch to ${h==="focus"?"dense":"focus"} layout`,"aria-pressed":h==="dense",onClick:()=>f(x=>{const B=x==="focus"?"dense":"focus";return window.localStorage.setItem("safelens-workspace-layout",B),window.sessionStorage.setItem("safelens-workspace-layout",B),B}),children:t.jsx($a,{size:18})}),t.jsxs("button",{ref:K,className:"icon-button compare-trigger",title:"Compare pinned evidence","aria-label":`Compare pinned evidence (${he.length})`,"aria-keyshortcuts":"Alt+Shift+C",onPointerEnter:wt,onFocus:wt,onClick:x=>{v.current=x.currentTarget,d(!0)},children:[t.jsx(ot,{size:18}),t.jsx("span",{children:he.length})]}),t.jsx("button",{className:"icon-button session-export",title:"Export analysis session","aria-label":"Export analysis session",onClick:ts,children:t.jsx(Mi,{size:18})}),t.jsx("button",{className:"icon-button artifact-export",title:"Export current Explorer artifact","aria-label":"Export current Explorer artifact",onClick:()=>void es(),children:t.jsx(Sa,{size:18})}),t.jsx("button",{className:"icon-button current-evidence-export",title:"Export current evidence as JSON","aria-label":"Export current evidence as JSON",onClick:jn,children:t.jsx(Na,{size:18})}),t.jsx("button",{ref:N,className:"icon-button",title:"Open quick actions","aria-label":"Open quick actions",onClick:()=>w(!0),children:t.jsx(Qo,{size:18})})]})]}),t.jsx(Pm,{notice:o}),t.jsxs("div",{className:"workspace-context-bar",children:[t.jsxs("nav",{"aria-label":"Workspace breadcrumb",children:[t.jsx("button",{type:"button",onClick:l,children:"Home"}),t.jsx(dt,{size:13,"aria-hidden":"true"}),t.jsx("span",{children:"Interpretability Explorer"}),t.jsx(dt,{size:13,"aria-hidden":"true"}),t.jsx("strong",{children:De(z)})]}),t.jsxs("div",{className:"workspace-context-meta",children:[t.jsxs("span",{className:"context-run-pill",children:[t.jsx(yt,{size:13,"aria-hidden":"true"}),t.jsx("b",{children:e.modelName})]}),t.jsxs("span",{className:"context-state-pill",children:[t.jsx("span",{"aria-hidden":"true"}),n.activeRecord.sourceType==="bundled"?"Bundled cache":"Local workspace"]})]})]}),t.jsxs("main",{className:"workspace",children:[t.jsxs("aside",{className:"left-panel",children:[t.jsx(Is,{records:n.records,activeRecord:n.activeRecord,message:n.message,remoteState:n.remoteState,onMessage:n.setMessage,onSelect:n.selectRun,onAdd:n.addRuns,onRemove:n.removeRun,onRestoreSession:ns,onRefreshRemote:()=>void n.refreshRemote(),onCancelRemote:n.cancelRemote}),t.jsx(Hs,{run:e,onRunReady:(x,B)=>n.addGeneratedRun(x,B.id)}),t.jsxs("section",{className:"panel-section provenance-panel",children:[t.jsxs("div",{className:"section-heading",children:[t.jsx($t,{size:16}),t.jsx("span",{children:"Data provenance"})]}),t.jsx(xi,{})]}),t.jsxs("section",{className:"panel-section",children:[t.jsxs("div",{className:"section-heading",children:[t.jsx(Rt,{size:16}),t.jsx("span",{children:"Evidence"})]}),t.jsx("div",{className:"evidence-list",children:E.map(x=>t.jsxs("button",{onClick:()=>Ja(x),children:[t.jsx("span",{children:e.tokens[x].text}),t.jsx("b",{children:Oe(e.tokens[x].risk)})]},x))})]})]}),t.jsxs("section",{id:"analysis-workspace",ref:F,className:"main-panel",tabIndex:-1,"aria-label":"Analysis workspace","aria-keyshortcuts":"ArrowLeft ArrowRight",children:[t.jsxs("div",{className:"main-header",children:[t.jsxs("div",{children:[t.jsx("h2",{children:h==="dense"?"Token Timeline":De(z)}),t.jsxs("p",{children:["token ",Ze.index," · id ",Ze.tokenId," · safety proxy"," ",Oe(Ze.risk)]})]}),t.jsxs("div",{className:"selection-trail","aria-label":"Current selection",children:[t.jsx("span",{children:Ze.text}),t.jsxs("span",{children:["L",te]}),t.jsx("span",{children:lo(re,we,Ne)})]}),t.jsx(Qu,{layers:e.layers,selectedLayer:te,onSelect:R.selectLayer}),t.jsx(Gu,{view:z,setView:R.selectView})]}),z!=="nla"&&t.jsx(Ud,{run:e,selectedToken:U,selectedLayer:te,selectedRange:J.tokenRange,setSelectedToken:et,setSelectedRange:R.selectRange,hoveredToken:be,setHoveredToken:se,pulseToken:ge,pinToken:Ye,pinned:po,timeline:ct,onTimelineChange:It}),t.jsx(Ju,{visible:h==="focus"&&I,tokenText:Ze.text,tokenIndex:U,layer:te,score:Oe(Ze.risk),view:z,menuOpen:M,contextOpen:X,pinned:Tt,canPin:Dt,pinnedCount:he.length,onToggleMenu:()=>q(x=>!x),onSelectView:x=>{q(!1),oe(!1),R.selectView(x),window.requestAnimationFrame(()=>{var B;(B=document.getElementById("analysis-panel"))==null||B.scrollIntoView({block:"start",behavior:"smooth"})})},onInspect:x=>{S.current=x,j(!0)},onToggleContext:()=>H(x=>!x),onPin:()=>void Ye(U),onPreloadCompare:wt,onCompare:x=>{v.current=x,wt(),d(!0)},onDismiss:()=>{L(!1),q(!1)}}),t.jsxs("div",{className:`mobile-selection-summary ${z==="nla"?"nla-selection-summary":""}`,role:"region","aria-label":"Current evidence actions",children:[t.jsxs("span",{children:[t.jsx("b",{children:z==="nla"?`P${U}`:Ze.text}),z==="nla"?"position":"token"]}),t.jsxs("span",{children:[t.jsxs("b",{children:["L",te]}),"layer"]}),t.jsxs("span",{children:[t.jsx("b",{children:z==="nla"?ue:Oe(Ze.risk)}),z==="nla"?"component":"safety proxy"]}),t.jsx("button",{className:Tt?"active":"","aria-label":Tt?"Unpin current evidence":"Pin current evidence","aria-pressed":Tt,disabled:!Dt,title:Tt?"Unpin current evidence":"Pin current evidence",onClick:()=>Ye(U),children:t.jsx(Hn,{size:17})}),t.jsx("button",{"aria-label":`Open evidence comparison (${he.length})`,title:"Compare pinned evidence",disabled:!he.length,onPointerDown:wt,onFocus:wt,onClick:x=>{v.current=x.currentTarget,d(!0)},children:t.jsx(ot,{size:17})}),t.jsx("button",{"aria-label":"Open evidence inspector",title:"Open evidence inspector",onClick:x=>{S.current=x.currentTarget,j(!0)},children:t.jsx(pa,{size:17})})]}),ke.ready?t.jsx(Om,{selectedToken:U,selectedSourceToken:ce,selectedLayer:te,view:z,component:re,selectedHead:we,neuron:Ne,nlaRow:bt,attributionMethod:Me.label,attributionEvidenceKind:Me.evidenceKind,attributionAvailable:Me.available}):t.jsxs("div",{className:"hydration-selection-summary","aria-label":"Selected range loading status",children:[t.jsx(Ve,{size:14}),t.jsxs("span",{children:[t.jsx("b",{children:De(z)})," L",te," · token ",U]}),t.jsx("em",{children:ke.error?"load failed":"loading range"})]}),t.jsx(Js,{resetKey:`${e.runId}:${e.sampleId}:${z}:${te}:${we.id}:${(Ne==null?void 0:Ne.id)??"-"}:${me}`,viewLabel:De(z),onOpenOverview:()=>R.selectView("overview"),children:t.jsx(Ce.Suspense,{fallback:t.jsx(qm,{view:z}),children:t.jsxs("div",{id:"analysis-panel",className:`analysis-grid ${z==="overview"?"overview-analysis-grid":""} ${z==="attention"?"attention-analysis-grid":""} ${z==="patching"||z==="intervention"?"patching-analysis-grid":""}`,role:"tabpanel","aria-labelledby":`analysis-tab-${z}`,children:[t.jsxs("div",{className:"left-analysis-stack",children:[h==="focus"&&V&&["attribution","patching","intervention"].includes(z)&&t.jsxs("div",{className:"focus-experiment-toolbar",role:"region","aria-label":"Experiment setup controls",children:[t.jsxs("span",{children:[t.jsx(kt,{size:15})," Experiment setup"]}),t.jsx("button",{"aria-label":"Close experiment setup",onClick:()=>oe(!1),children:t.jsx(Je,{size:15})})]}),ke.partial&&["attribution","patching","intervention"].includes(z)&&t.jsx(Hm,{onLoad:()=>void n.loadFullActiveRun().catch(()=>{})}),!ke.partial&&(h==="dense"||V)&&z==="attribution"&&t.jsx(Im,{run:e,onRunReady:(x,B)=>n.addGeneratedRun(x,B.id,{view:"attribution",trackName:"integrated_gradients",metric:"integrated_gradients",kind:"attribution"})}),z==="nla"&&t.jsx(Am,{run:e,selectedToken:U,onRunReady:(x,B)=>n.addGeneratedRun(x,B.id,{view:"nla",metric:"nla_cosine",tokenIndex:B.request.positions[0],kind:"nla"})}),!ke.partial&&(h==="dense"||V)&&z==="patching"&&t.jsx(Tm,{run:e,selectedToken:U,selectedLayer:te,onRunReady:(x,B)=>n.addGeneratedRun(x,B.id,{view:"patching",metric:"patching_recovery",tokenIndex:B.request.positions[0],layer:B.request.layers[0],kind:"patching"})}),!ke.partial&&(h==="dense"||V)&&z==="intervention"&&t.jsx(Cm,{run:e,selectedLayer:te,selectedToken:U,onRunReady:(x,B)=>n.addGeneratedRun(x,B.id,{view:"intervention",metric:"intervention_logit_delta",tokenIndex:B.request.positionStart,layer:B.request.layer,kind:"intervention"})}),_t?t.jsx(Fm,{layer:te,onCancel:go}):ke.ready?z==="attention"?t.jsx(xm,{heads:At,selectedHead:we,tokens:e.tokens,selectedSource:ce,selectedDestination:U,edgeMode:ae,selectedRange:J.tokenRange,onHeadChange:R.selectHead,onEdgeModeChange:R.selectAttentionEdgeMode,onSelectPair:R.selectAttentionPair,onRangeSelect:R.selectRange,onHoverSource:se,onPin:()=>Ye(U),onPinPair:(x,B)=>{Ye(B,te,{sourceTokenIndex:x})}}):z==="mlp"?t.jsx(km,{tokens:e.tokens,neurons:Jn,selectedToken:U,selectedNeuronId:(Ne==null?void 0:Ne.id)??"",partialProfiles:ke.partial,metric:da(J.metric),selectedRange:J.tokenRange,onMetricChange:x=>{R.selectMetric(x),R.setNormalization(x==="mlp_normalized_activation"?"normalized":"raw")},onSelectToken:et,onSelectNeuron:R.selectNeuron,onRangeSelect:R.selectRange,onHoverToken:se,onPin:()=>Ye(U),onPinActivation:(x,B)=>{Ye(x,te,{neuronId:B})}}):z==="nla"?t.jsx(jm,{rows:e.nla,compatibility:e.nlaCompatibility,layers:e.layers,tokens:e.tokens,selectedToken:U,selectedLayer:te,selectedComponent:ue,metric:ca(J.metric),selectedRange:J.tokenRange,onMetricChange:x=>R.selectMetric(`nla_${x}`),onSelectCell:(x,B,xe)=>{R.selectLayer(x),R.selectNlaComponent(xe),et(B)},onRangeSelect:R.selectRange,onHoverToken:se,onPin:Dt?()=>Ye(U):void 0,onPinCell:(x,B,xe)=>{Ye(B,x,{nlaComponent:xe})}}):z==="attribution"?t.jsx(vm,{methods:e.attributionMethods,selectedMethod:Me,tokens:e.tokens,selectedToken:U,selectedLayer:te,normalization:J.normalization,selectedRange:J.tokenRange,onMethodChange:R.selectTrack,onNormalizationChange:R.setNormalization,onSelectCell:(x,B)=>{x>=0&&R.selectLayer(x),et(B)},onRangeSelect:R.selectRange,onHoverToken:se,onPin:()=>Ye(U),onPinCell:(x,B)=>{Ye(B,x>=0?x:te)},onConfigureIntegratedGradients:()=>void nn("attribution-job")}):z==="patching"?e.patching?t.jsx(Sm,{experiment:e.patching,tokens:e.tokens,selectedToken:U,selectedLayer:te,metric:xh(J.metric),selectedRange:J.tokenRange,onMetricChange:x=>R.selectMetric(`patching_${x}`),onSelectCell:(x,B)=>{R.selectLayer(x),et(B)},onRangeSelect:R.selectRange,onPin:()=>Ye(U),onPinCell:(x,B)=>{Ye(B,x)}}):t.jsx(pn,{className:"surface patching-empty",icon:t.jsx(kt,{size:20}),title:"No causal patch grid in this run",description:"Create an aligned corrupted prompt and measure the exact replacement effect in a derived Run.",facts:[{label:"Selection",value:`L${te} / token ${U}`},{label:"Component",value:"residual stream"}],actionLabel:"Configure causal patching",actionIcon:t.jsx(kt,{size:16}),onAction:()=>void nn("patching-job")}):z==="intervention"?e.intervention?t.jsx(Nm,{experiment:e.intervention,onPin:()=>Ye(U)}):t.jsx(pn,{className:"surface intervention-empty",icon:t.jsx(vt,{size:20}),title:"No intervention comparison in this run",description:"Define a contrastive direction and generate a matched original-versus-steered derived Run.",facts:[{label:"Selection",value:`L${te} / token ${U}`},{label:"Comparison",value:"matched generation"}],actionLabel:"Configure intervention",actionIcon:t.jsx(vt,{size:16}),onAction:()=>void nn("intervention-job")}):t.jsx(Vm,{selectedLayer:te,selectedToken:U,hoveredToken:be,setHoveredToken:se,setSelectedLayer:R.selectLayer,setSelectedToken:et,component:re,metric:pe,normalization:J.normalization,selectedRange:J.tokenRange,setMetric:R.selectMetric,setNormalization:R.setNormalization,setSelectedRange:R.selectRange,pinCurrent:()=>Ye(U),pinCell:(x,B)=>Ye(B,x)}):t.jsx(Ym,{view:z,loading:ke.loading,error:ke.error,cancelled:ke.cancelled,onCancel:n.cancelRemote,onRetry:()=>n.ensureViewHydrated(z,te,U,ce)}),vn&&ke.ready&&z!=="patching"&&z!=="intervention"&&t.jsx(Km,{selectedToken:U,selectedLayer:te,component:re,selectedHead:we,neuron:Ne,residualCell:Gn}),vn&&t.jsx(Um,{metadata:e.metadata}),vn&&t.jsx(th,{pinned:he,restorePin:Xa,availableRunKeys:new Set(n.records.map(x=>x.key)),openCompare:()=>d(!0)})]}),vn&&ke.ready&&z!=="patching"&&z!=="intervention"&&t.jsx(Bm,{view:z,setSelectedView:R.selectView,selectedLayer:te,setSelectedLayer:R.selectLayer,selectedToken:U,selectedNlaComponent:ue,selectedSourceToken:ce,setSelectedToken:et,setSelectedSourceToken:R.selectSourceToken,selectedHead:we,selectedHeadId:we.id,setSelectedHeadId:R.selectHead,selectedTrack:me,setSelectedTrack:R.selectTrack,selectedTrackData:kn,selectedAttributionMethod:Me,metric:pe,normalization:J.normalization,residualCell:Gn,neuron:Ne,evidenceFilter:He,setEvidenceFilter:Fe,onConfigureJob:x=>void nn(x)})]})})})]}),t.jsx("aside",{className:"right-panel",children:t.jsx(Qs,{evidence:zt,canPrevious:rt>0,canNext:rt<e.tokens.length-1,canPin:Dt,pinned:Tt,nextActions:Ba,onPrevious:()=>et(e.tokens[rt-1].index),onNext:()=>et(e.tokens[rt+1].index),onPin:()=>Ye(U),onCompare:()=>{v.current=K.current,j(!1),d(!0)},onExport:jn,onNextAction:Ga})})]}),t.jsx(cc,{open:C,returnFocusRef:N,context:{runId:e.runId,sampleId:e.sampleId,view:De(z),layer:te,token:U,tokenText:Ze.text},pinnedCount:he.length,onClose:()=>w(!1),onOverview:()=>{w(!1),R.selectView("overview"),window.requestAnimationFrame(()=>{var x;return(x=F.current)==null?void 0:x.focus()})},onRuns:()=>{w(!1),P.current=N.current,window.requestAnimationFrame(()=>u(!0))},onTokenSearch:()=>{w(!1),window.requestAnimationFrame(()=>{var x;(x=document.getElementById("token-timeline-search"))==null||x.focus()})},onCompare:()=>{w(!1),v.current=K.current,wt(),window.requestAnimationFrame(()=>d(!0))},onExportSession:()=>{w(!1),ts()},onExportArtifact:()=>{w(!1),es()},onExportEvidence:()=>{w(!1),jn()}}),y&&t.jsx("div",{className:"mobile-library-backdrop",onMouseDown:x=>{x.target===x.currentTarget&&u(!1)},children:t.jsxs("aside",{ref:ee,className:"mobile-library-drawer",role:"dialog",tabIndex:-1,"aria-modal":"true","aria-labelledby":"mobile-library-title",children:[t.jsxs("header",{children:[t.jsxs("div",{children:[t.jsx("span",{children:"Data workspace"}),t.jsx("h2",{id:"mobile-library-title",children:"Runs and samples"})]}),t.jsx("button",{ref:ne,"aria-label":"Close run library",onClick:()=>u(!1),children:t.jsx(Je,{size:18})})]}),t.jsx(Is,{records:n.records,activeRecord:n.activeRecord,message:n.message,remoteState:n.remoteState,onMessage:n.setMessage,onSelect:x=>{n.selectRun(x),u(!1)},onAdd:(x,B,xe)=>{const Ie=n.addRuns(x,B,xe);return Ie&&u(!1),Ie},onRemove:n.removeRun,onRestoreSession:ns,onRefreshRemote:()=>void n.refreshRemote(),onCancelRemote:n.cancelRemote}),t.jsx(Hs,{run:e,onRunReady:(x,B)=>{n.addGeneratedRun(x,B.id),u(!1)}}),t.jsxs("section",{className:"panel-section mobile-drawer-secondary",children:[t.jsxs("div",{className:"section-heading",children:[t.jsx($t,{size:16}),t.jsx("span",{children:"Data provenance"})]}),t.jsx(xi,{})]}),t.jsxs("section",{className:"panel-section mobile-drawer-secondary",children:[t.jsxs("div",{className:"section-heading",children:[t.jsx(Rt,{size:16}),t.jsx("span",{children:"Evidence"})]}),t.jsx("div",{className:"evidence-list",children:E.map(x=>t.jsxs("button",{onClick:()=>{Ja(x),u(!1)},children:[t.jsx("span",{children:e.tokens[x].text}),t.jsx("b",{children:Oe(e.tokens[x].risk)})]},x))})]})]})}),k&&t.jsx("div",{className:"mobile-inspector-backdrop",onMouseDown:x=>{x.target===x.currentTarget&&j(!1)},children:t.jsxs("aside",{ref:D,className:"mobile-inspector-drawer","data-detail-level":T?"full":"compact",role:"dialog",tabIndex:-1,"aria-modal":"true","aria-labelledby":"mobile-inspector-title",children:[t.jsxs("header",{onPointerDown:x=>{x.button!==0||x.target.closest("button")||($.current={pointerId:x.pointerId,startY:x.clientY},x.currentTarget.setPointerCapture(x.pointerId))},children:[t.jsxs("div",{children:[t.jsx("span",{children:T?"Full provenance":"Selected evidence"}),t.jsx("h2",{id:"mobile-inspector-title",children:"Evidence details"})]}),t.jsxs("div",{className:"mobile-inspector-header-actions",children:[t.jsx("button",{"aria-label":T?"Show compact evidence summary":"Show full evidence details","aria-expanded":T,onClick:()=>A(x=>!x),children:T?t.jsx(Fn,{size:18}):t.jsx(Wi,{size:18})}),t.jsx("button",{ref:W,"aria-label":"Close evidence inspector",onClick:()=>j(!1),children:t.jsx(Je,{size:18})})]})]}),t.jsx(Qs,{evidence:zt,canPrevious:rt>0,canNext:rt<e.tokens.length-1,canPin:Dt,pinned:Tt,nextActions:Ba,onPrevious:()=>et(e.tokens[rt-1].index),onNext:()=>et(e.tokens[rt+1].index),onPin:()=>Ye(U),onCompare:()=>{v.current=S.current,j(!1),d(!0)},onExport:jn,onNextAction:Ga,detailLevel:T?"full":"compact"})]})}),c&&t.jsx(Js,{variant:"dialog",resetKey:`${ut(e)}:${he.map(x=>x.id).join("|")}:${b??"-"}`,viewLabel:"Evidence comparison",onDismiss:()=>{d(!1),window.requestAnimationFrame(()=>{var x;return(x=v.current)==null?void 0:x.focus()})},children:t.jsx(Ce.Suspense,{fallback:t.jsx(Mm,{}),children:t.jsx(Rm,{open:!0,pinned:he,tokens:e.tokens,metricProvenance:e.metricProvenance,currentRunKey:ut(e),availableRunKeys:new Set(n.records.map(x=>x.key)),baselineId:b,returnFocusRef:v,onClose:()=>d(!1),onRestore:Xa,onRemove:R.togglePin,onBaselineChange:g})})})]})})}function Mm(){return t.jsx("div",{className:"compare-backdrop",children:t.jsxs("aside",{className:"compare-drawer compare-drawer-loading",role:"dialog","aria-modal":"true","aria-label":"Loading evidence comparison",children:[t.jsx(Ve,{size:20}),t.jsx("strong",{children:"Preparing evidence comparison"}),t.jsx("span",{role:"status",children:"Loading comparison visualization."})]})})}function Pm({notice:e}){const n=(e==null?void 0:e.kind)==="run"?"Run changed":"Context updated";return t.jsxs(t.Fragment,{children:[t.jsx("div",{className:"visually-hidden",role:"log","aria-live":"polite","aria-atomic":"true","aria-label":"Analysis context changes",children:e?`${n}: ${e.message}`:""}),t.jsxs("div",{className:`context-change-notice${e!=null&&e.visible?" visible":""}`,"aria-hidden":"true","data-kind":(e==null?void 0:e.kind)??"selection",children:[t.jsx(Xe,{size:18}),t.jsx("span",{children:n}),t.jsx("strong",{children:(e==null?void 0:e.message)??""})]})]})}function Wm(e,n,a){var y;const s=["overview","residual","attention","mlp","nla","patching","intervention","attribution"],i=new URLSearchParams(window.location.search),r=(n==null?void 0:n.workspace.runId)===e.runId&&n.workspace.sampleId===e.sampleId,o=r?n.selection.view:i.get("view"),l=s.includes(o)?o:"overview",c=r?n.selection.targetTokenIndex??n.selection.tokenIndex:oa(i,"target")??oa(i,"token"),d=c!==void 0&&e.tokens.some(u=>u.index===c)?c:io(e.tokens)[0]??((y=e.tokens[0])==null?void 0:y.index)??0,h=r?n.selection.layer:oa(i,"layer"),f=h!==void 0&&e.layers.includes(h)?h:e.layers[e.layers.length-1]??0,b=r||["view","token","target","layer","head","neuron","track","metric","normalization"].some(u=>i.has(u)),g=r?"session context":a==="fresh"?"fresh selection":a==="restored"||b?"restored context":"fresh selection";return`${e.sampleId} · ${De(l)} · T${d} · L${f} · ${g}`}function oa(e,n){const a=e.get(n);return a!==null&&/^\d+$/.test(a)?Number(a):void 0}function zm(e,n,a,s,i,r=!1){var o;return{title:((o=e.tokens[s])==null?void 0:o.text)||`token ${s}`,subtitle:`${De(n)} · L${a}`,status:i?"failed":r?"cancelled":"loading",statusReason:i??(r?"Artifact range loading was cancelled.":"Loading the selected artifact range."),primaryLabel:De(n),primaryValue:i?"load failed":r?"cancelled":"loading",rawValue:"pending",displayValue:"pending",units:"pending",evidenceClass:"raw",method:"artifact chunk hydration",normalization:"pending",cacheKey:"",shape:"current viewport range",sourceArtifact:"workspace chunk protocol",runId:e.runId,sampleId:e.sampleId,modelName:e.modelName,warnings:i?[i]:[],reproduction:{runId:e.runId,sampleId:e.sampleId,view:n,layer:a,token:s}}}function Ut(e){return{schemaVersion:"1.0",status:e.status,statusReason:e.statusReason,primaryLabel:e.primaryLabel,primaryValue:e.primaryValue,rawValue:e.rawValue,displayValue:e.displayValue,units:e.units,evidenceClass:e.evidenceClass,method:e.method,normalization:e.normalization,cacheKey:e.cacheKey,shape:e.shape,sourceArtifact:e.sourceArtifact,warnings:[...e.warnings],reproduction:structuredClone(e.reproduction)}}function Dm(e,n,a,s){const i=e.attentionHeads.find(l=>l.layer===a),r=e.mlpNeurons.find(l=>l.layer===a),o=e.attributionMethods.find(l=>l.available)??e.attributionMethods[0];return n.map(l=>{const c=e.tokens.find(h=>h.index===l)??e.tokens[0],d={id:`${e.runId}:${e.sampleId}:${l}:${a}:overview:tokenRisk:normalized:-:-:-`,runId:e.runId,sampleId:e.sampleId,tokenIndex:l,tokenText:c.text,tokenId:c.tokenId,tokenSource:c.source,modelName:e.modelName,modelSource:e.modelSource,layer:a,view:"overview",component:"resid_post",metric:"tokenRisk",value:c.risk,normalization:"normalized",sourceKey:`layer_${a}.resid_post[${l}]`,provenance:e.metricProvenance.tokenRisk};return!i||!o?d:{...d,assessment:Ut(un({run:e,view:"overview",selectedToken:l,selectedSourceToken:l,selectedLayer:a,selectedNlaComponent:"resid_post",selectedHead:i,selectedNeuron:r,selectedAttributionMethod:o,metric:"tokenRisk",normalization:"normalized",sourceArtifact:s}))}})}function Ym({view:e,loading:n,error:a,cancelled:s,onCancel:i,onRetry:r}){const o=Ce.useRef(null);Ce.useEffect(()=>{!s||o.current===null||(ft("cancel-feedback",{latencyMs:performance.now()-o.current}),o.current=null)},[s]);function l(){o.current=performance.now(),ft("cancel-request"),i()}return t.jsxs("div",{className:`surface view-chunk-state ${a?"error":s?"cancelled":"loading"}`,role:a?"alert":"status",children:[a?t.jsx(lt,{size:20}):t.jsx(Ve,{size:20}),t.jsxs("div",{children:[t.jsx("strong",{children:a?`${De(e)} data could not be loaded`:s?`${De(e)} loading cancelled`:`Loading ${De(e)} data`}),t.jsx("p",{children:a??(s?"Previously loaded ranges remain available.":n?"Requesting the selected layer and token range.":"Preparing the artifact request.")})]}),(a||s)&&t.jsx("button",{onClick:r,children:"Retry"}),!a&&!s&&n&&t.jsx("button",{onClick:l,children:"Cancel"}),!a&&!s&&t.jsx(to,{view:e})]})}function qm({view:e}){return t.jsxs("div",{className:"surface view-module-loading",role:"status","aria-live":"polite","aria-busy":"true","aria-label":`Loading ${De(e)} view`,children:[t.jsx(Ve,{className:"spin",size:20,"aria-hidden":"true"}),t.jsxs("div",{children:[t.jsxs("strong",{children:["Preparing ",De(e)," view"]}),t.jsx("p",{children:"The analysis surface is loading its visualization module."})]}),t.jsx(to,{view:e})]})}function to({view:e}){return t.jsxs("div",{className:"analysis-loading-skeleton","data-loading-view":e,"aria-hidden":"true",children:[t.jsxs("div",{className:"analysis-loading-toolbar",children:[t.jsx("span",{}),t.jsx("span",{}),t.jsx("span",{})]}),t.jsxs("div",{className:"analysis-loading-stage",children:[t.jsx("span",{className:"analysis-loading-axis analysis-loading-axis-y"}),t.jsx("span",{className:"analysis-loading-axis analysis-loading-axis-x"}),t.jsx("div",{className:"analysis-loading-grid"}),t.jsx("span",{className:"analysis-loading-viewport"})]}),t.jsxs("div",{className:"analysis-loading-footer",children:[t.jsx("span",{}),t.jsx("span",{}),t.jsx("span",{})]})]})}function Hm({onLoad:e}){return t.jsxs("div",{className:"surface full-hydration-gate",role:"status",children:[t.jsx(yt,{size:18}),t.jsxs("div",{children:[t.jsx("strong",{children:"Full Run required for experiments"}),t.jsx("p",{children:"Current visualization uses validated range chunks."})]}),t.jsx("button",{onClick:e,children:"Load full Run"})]})}function Fm({layer:e,onCancel:n}){return t.jsxs("div",{className:"surface full-hydration-gate attention-rollout-loading",role:"status",children:[t.jsx(Ve,{size:18,className:"spin"}),t.jsxs("div",{children:[t.jsx("strong",{children:"Loading complete attention for rollout"}),t.jsxs("p",{children:["Computing retained-head mean + identity residual through L",e," requires every preceding layer."]})]}),t.jsx("button",{onClick:n,children:"Cancel"})]})}function la({label:e,shortLabel:n,value:a,tone:s}){return t.jsxs("div",{className:`metric metric-${s}`,"aria-label":`${e} metric`,children:[t.jsx("span",{className:"metric-label-full","aria-hidden":"true",children:e}),t.jsx("span",{className:"metric-label-short","aria-hidden":"true",children:n}),t.jsx("strong",{children:a})]})}function bi(e,n){if(window.matchMedia("(prefers-reduced-motion: reduce)").matches){n(null);return}n(e),window.setTimeout(()=>{n(a=>a===e?null:a)},560)}function xi(){const e=pt(),n=e.nla.filter(s=>s.status!=="unavailable").length,a=[["Real model cache","tokens, residuals, attention, MLP","Directly captured model data."],["Safety proxy","residual direction projection",e.metricProvenance.tokenRisk.semantics],["Attention proxy","descriptive, not causal attribution",e.metricProvenance.tokenAttribution.semantics],["NLA",n>0?`${n} exact fidelity rows`:"no compatible result artifact",n>0?"Exact NLA rows are available for this run.":"Compatibility diagnostics explain why NLA rows are unavailable."]];return t.jsx("div",{className:"provenance-list",children:a.map(([s,i,r])=>t.jsxs("span",{title:r,children:[t.jsx("b",{children:s}),t.jsx("i",{children:i})]},s))})}function Um({metadata:e}){const n=ua(e,"nextToken","n/a"),a=ua(e,"riskDirectionToken","n/a"),s=ua(e,"generatedContinuation","n/a");return t.jsxs("section",{className:"surface digest-panel",children:[t.jsxs("div",{className:"surface-header",children:[t.jsxs("div",{children:[t.jsx("h3",{children:"Model output"}),t.jsx("p",{children:"Real forward-pass metadata"})]}),t.jsx(Ve,{size:18})]}),t.jsxs("div",{className:"digest-grid",children:[t.jsxs("span",{children:[t.jsx("b",{children:n}),"next token"]}),t.jsxs("span",{children:[t.jsx("b",{children:a}),"target direction"]}),t.jsxs("span",{children:[t.jsx("b",{children:s}),"greedy continuation"]})]})]})}function Km({selectedToken:e,selectedLayer:n,component:a,selectedHead:s,neuron:i,residualCell:r}){var d;const o=pt(),l=o.tokens[e],c=a==="attention"?s.difference?[["attention head (diff)",gt(s)],["selected",s.difference.selectedHeadId],["baseline",s.difference.baselineHeadId],["evidence","derived signed proxy"]]:s.rollout?[["attention path",gt(s)],["layers",s.rollout.layers.map(h=>`L${h}`).join(" → ")],["members",`${s.rollout.memberHeadIds.length} retained heads`],["evidence","derived path proxy"]]:s.aggregation?[["aggregation",xn(s.aggregation)],["members",((d=s.memberHeadIds)==null?void 0:d.join(" · "))??"retained heads"],["evidence","derived proxy"]]:[["attention head",s.id],["keyword mass",Oe(s.riskContribution)],["entropy",Oe(s.entropy)]]:a==="mlp"&&i?[["MLP neuron",i.id],["activation",Oe(i.activation,"mlp_signed_activation")],["top tokens",i.topTokens.map(h=>o.tokens[h].text).join(" · ")]]:[["residual stream","resid_post"],["norm",((r==null?void 0:r.norm)??0).toFixed(1)],["direction",Oe((r==null?void 0:r.riskDirection)??0,"residual_direction")]];return t.jsxs("section",{className:"surface trace-panel",children:[t.jsxs("div",{className:"surface-header",children:[t.jsxs("div",{children:[t.jsx("h3",{children:"Trace evidence"}),t.jsxs("p",{children:[l.text," · L",n]})]}),t.jsx(Rt,{size:18})]}),t.jsx("div",{className:"trace-grid",children:c.map(([h,f])=>t.jsxs("span",{children:[t.jsx("b",{children:f}),h]},h))})]})}function Om({selectedToken:e,selectedSourceToken:n,selectedLayer:a,view:s,component:i,selectedHead:r,neuron:o,nlaRow:l,attributionMethod:c,attributionEvidenceKind:d,attributionAvailable:h}){var y,u;const f=pt(),b=f.tokens[e],g=[{label:"Selected signal",value:`${b.text} · ${Oe(b.risk)}`},{label:"Context",value:`L${a} · ${De(s)}`},{label:"Evidence",value:s==="attention"?`${gt(r)} · ${n}→${e}`:s==="attribution"?c:s==="patching"?((y=f.patching)==null?void 0:y.component)??"experiment setup":s==="intervention"?((u=f.intervention)==null?void 0:u.component)??"experiment setup":lo(i,r,o)},{label:"Evidence class",value:s==="attention"?r.aggregation||r.difference||r.rollout?"derived proxy":"raw attention":s==="attribution"?h?d.replace("_"," "):"method unavailable":s==="nla"?(l==null?void 0:l.status)==="available"?"NLA explanation":"unavailable":s==="patching"?f.patching?"causal":"not computed":s==="intervention"?f.intervention?"causal intervention":"not computed":"derived proxy"}];return t.jsx("section",{className:"evidence-summary","aria-label":"Current evidence summary",children:g.map(k=>t.jsxs("span",{children:[t.jsx("em",{children:k.label}),t.jsx("i",{children:k.value})]},k.label))})}function Vm({selectedLayer:e,selectedToken:n,hoveredToken:a,setHoveredToken:s,setSelectedLayer:i,setSelectedToken:r,component:o,metric:l,normalization:c,selectedRange:d,setMetric:h,setNormalization:f,setSelectedRange:b,pinCurrent:g,pinCell:y}){const u=pt(),k=so(u,o,l),j=Qn(u,o,l);return t.jsx(ol,{title:j.label,subtitle:j.semantics,rows:u.layers,columns:u.tokens,cells:k,metric:l,metricOptions:no(o),provenance:j,normalization:c,selectedRow:e,selectedColumn:n,selectedRange:d,hoveredColumn:a,color:o,onMetricChange:h,onNormalizationChange:f,onSelectCell:(T,A)=>{i(T),r(A)},onRangeSelect:b,onHoverColumn:s,onPin:g,onPinCell:y})}function Bm({view:e,setSelectedView:n,selectedLayer:a,setSelectedLayer:s,selectedToken:i,selectedNlaComponent:r,selectedSourceToken:o,setSelectedToken:l,setSelectedSourceToken:c,selectedHead:d,selectedHeadId:h,setSelectedHeadId:f,selectedTrack:b,setSelectedTrack:g,selectedTrackData:y,selectedAttributionMethod:u,metric:k,normalization:j,residualCell:T,neuron:A,evidenceFilter:C,setEvidenceFilter:w,onConfigureJob:I}){var P;const L=pt();if(e==="overview")return t.jsx(rc,{run:L,selectedToken:i,selectedLayer:a,residualCell:T,onNavigate:n});if(e==="residual")return t.jsx(Jm,{selectedToken:i,selectedLayer:a,setSelectedLayer:s,metric:k,normalization:j,residualCell:T});if(e==="mlp")return t.jsx(Gm,{selectedToken:i,selectedLayer:a,neuron:A});if(e==="nla"){const S=Yn(L.nla,i,a,r),Z=[{view:"residual",label:"Residual",component:"resid_post",icon:t.jsx(bn,{size:16})},{view:"attention",label:"Attention",component:"attn_result",icon:t.jsx(Mt,{size:16})},{view:"mlp",label:"MLP",component:"mlp_out",icon:t.jsx(Qt,{size:16})}];return t.jsxs("section",{className:"surface nla-evidence-detail",children:[t.jsxs("div",{className:"surface-header",children:[t.jsxs("div",{children:[t.jsx("h3",{children:"Exact NLA evidence"}),t.jsxs("p",{children:["token ",i," · layer ",a," · ",r," · strict match"]})]}),t.jsx(tt,{size:18})]}),S?S.status==="unavailable"?t.jsxs(t.Fragment,{children:[t.jsxs("div",{className:"nla-exact-facts",children:[t.jsxs("span",{children:[t.jsx("b",{children:S.token}),"token ",S.tokenIndex]}),t.jsxs("span",{children:[t.jsxs("b",{children:["L",S.layer]}),S.component]}),t.jsxs("span",{children:[t.jsx("b",{children:S.activationNorm.toFixed(4)}),"activation norm"]}),t.jsxs("span",{children:[t.jsx("b",{children:"unavailable"}),"decoder status"]})]}),t.jsx(pn,{compact:!0,icon:t.jsx(tt,{size:18}),title:"Activation is cached; NLA decoding is unavailable",description:S.explanation,facts:[{label:"Source",value:S.source??"not stored"},{label:"Activation norm",value:S.activationNorm.toFixed(4)}],actionLabel:"Configure exact NLA",actionIcon:t.jsx(tt,{size:16}),onAction:()=>I("nla-job")})]}):t.jsxs(t.Fragment,{children:[t.jsxs("div",{className:"nla-exact-facts",children:[t.jsxs("span",{children:[t.jsx("b",{children:S.cosine.toFixed(4)}),"cosine"]}),t.jsxs("span",{children:[t.jsx("b",{children:S.mse.toFixed(4)}),"MSE"]}),t.jsxs("span",{children:[t.jsx("b",{children:((P=S.fve)==null?void 0:P.toFixed(4))??"n/a"}),"FVE"]}),t.jsxs("span",{children:[t.jsx("b",{children:S.activationNorm.toFixed(4)}),"activation norm"]})]}),t.jsx(eh,{row:S})]}):t.jsx(pn,{compact:!0,icon:t.jsx(tt,{size:18}),title:"No exact NLA artifact row",description:"Nearby tokens, layers, or components are intentionally not substituted. Compute this exact selection instead.",facts:[{label:"Selection",value:`L${a} / token ${i}`},{label:"Component",value:r}],actionLabel:"Configure exact NLA",actionIcon:t.jsx(tt,{size:16}),onAction:()=>I("nla-job")}),t.jsxs("div",{className:"nla-cross-view-links",role:"group","aria-label":"Activation context views",children:[t.jsxs("div",{children:[t.jsx("strong",{children:"Activation context"}),t.jsxs("span",{children:["Keep token ",i," and L",a," while changing evidence view."]})]}),Z.map(K=>t.jsxs("button",{type:"button","aria-label":`Open ${K.label} at layer ${a}, token ${i}`,onClick:()=>n(K.view),children:[K.icon,t.jsxs("span",{children:[t.jsx("b",{children:K.label}),K.component===r?"component context":"same token / layer"]}),t.jsx(dt,{size:15})]},K.view))]})]})}if(e==="attention"){const S=d.distributionByToken[i]??[],Z=gt(d),K=S.slice(0,i+1).map((v,ne)=>({tokenIndex:ne,score:v,reason:ch(L,ne,i)})),N=d.difference?dh(K,i,C):lh(K,i,C);return t.jsxs("section",{className:"surface attention-distribution",children:[t.jsxs("div",{className:"surface-header",children:[t.jsxs("div",{children:[t.jsx("h3",{children:"Attention distribution"}),t.jsxs("p",{children:[Z," · destination token ",i," row"]})]}),t.jsx(Mt,{size:18})]}),t.jsxs("div",{className:"head-picker",children:[(d.aggregation||d.difference||d.rollout)&&t.jsx("span",{className:"aggregate-head-label",children:Z}),L.attentionHeads.filter(v=>v.layer===a).map(v=>{var ne;return t.jsx("button",{className:((ne=d.difference)==null?void 0:ne.selectedHeadId)===v.id||h===v.id?"active":"",onClick:()=>{var ee;if(!d.difference){f(v.id);return}const W=d.difference.baselineHeadId===v.id?((ee=L.attentionHeads.find(D=>D.layer===a&&D.id!==v.id))==null?void 0:ee.id)??d.difference.baselineHeadId:d.difference.baselineHeadId;f(Br(v.id,W))},children:v.id},v.id)})]}),t.jsx(Xm,{filter:C,setFilter:w}),t.jsx(Zm,{rows:N,selectedToken:o,onSelectToken:c,scoreTone:d.difference?"attention-difference":"attention"})]})}const M=y.values.map((S,Z)=>({tokenIndex:Z,value:S})),q=[...M].filter(S=>S.value>0).sort((S,Z)=>Z.value-S.value).slice(0,5),X=[...M].filter(S=>S.value<0).sort((S,Z)=>S.value-Z.value).slice(0,5),H=u.id==="integrated_gradients"?ao(L.metadata):void 0,V=Array.isArray(H==null?void 0:H.rawValues)&&H.rawValues.length===y.values.length&&H.rawValues.every(S=>typeof S=="number"&&Number.isFinite(S))?H.rawValues:void 0,oe=V??y.values,de=L.attributionMethods.map(S=>{const Z=S.rows.find(K=>K.layer===a)??S.rows.find(K=>K.layer<0);return{method:S,row:Z,value:Z==null?void 0:Z.values[i]}});return t.jsxs("section",{className:"surface attribution-distribution",children:[t.jsxs("div",{className:"surface-header",children:[t.jsxs("div",{children:[t.jsx("h3",{children:"Attribution evidence"}),t.jsx("p",{children:u.label})]}),t.jsx(On,{size:18})]}),t.jsxs("div",{className:"attribution-method-compare-heading",children:[t.jsxs("div",{children:[t.jsx("strong",{children:"Selected-token method snapshots"}),t.jsx("span",{children:"Within-method values only; different methods and scales do not produce a direct delta."})]}),t.jsxs("b",{children:["token ",i]})]}),t.jsx("div",{className:"attribution-method-catalog","aria-label":"Attribution methods",children:de.map(({method:S,row:Z,value:K})=>t.jsxs("button",{className:`${b===S.id?"active":""} ${S.available?"":"unavailable"}`,"aria-pressed":b===S.id,onClick:()=>g(S.id),children:[t.jsxs("span",{children:[t.jsx("strong",{children:S.label}),t.jsx("small",{children:Z?Z.layer<0?Z.label:`L${Z.layer}`:"no exact row"})]}),t.jsx("b",{children:S.available&&K!==void 0?eo(K):"n/a"}),t.jsx("em",{children:S.available?`${S.signed?"signed":"unsigned"} · ${S.evidenceKind.replace("_"," ")}`:"not run"})]},S.id))}),u.available?t.jsxs(t.Fragment,{children:[t.jsxs("div",{className:"attribution-selected-value",children:[t.jsx("span",{children:"Selected token"}),t.jsx("strong",{children:L.tokens[i].text}),t.jsx("b",{children:(y.values[i]??0).toFixed(6)}),t.jsx("i",{children:u.signed?"signed stored value":"unsigned proxy"})]}),t.jsx(Qm,{values:oe,signed:u.signed,basis:V?"raw job values":"stored method row",selectedToken:i,job:H}),t.jsxs("div",{className:"attribution-polarity-lists",children:[t.jsx(wi,{title:"Top positive",entries:q,selectedToken:i,onSelectToken:l}),u.signed&&t.jsx(wi,{title:"Top negative",entries:X,selectedToken:i,onSelectToken:l})]}),t.jsxs("div",{className:"provenance-note",children:[t.jsx("b",{children:u.evidenceKind.replace("_"," ")}),t.jsx("p",{children:u.description}),t.jsx("span",{children:u.normalization})]})]}):u.id==="integrated_gradients"?t.jsx(pn,{compact:!0,icon:t.jsx(Ve,{size:18}),title:"Method output unavailable",description:u.unavailableReason??"No target-specific attribution output was computed.",facts:[{label:"Method",value:u.label},{label:"Token",value:String(i)}],actionLabel:"Configure Integrated Gradients",actionIcon:t.jsx(Ve,{size:16}),onAction:()=>I("attribution-job")}):t.jsxs("div",{className:"analysis-empty compact",children:[t.jsx("span",{className:"empty-icon",children:t.jsx(lt,{size:18})}),t.jsx("strong",{children:"Method output unavailable"}),t.jsx("p",{children:u.unavailableReason})]})]})}function Qm({values:e,signed:n,basis:a,selectedToken:s,job:i}){const r=e.reduce((T,A)=>T+Math.max(0,A),0),o=e.reduce((T,A)=>T+Math.min(0,A),0),l=r+o,c=r+Math.abs(o),d=c>1e-12?Math.max(0,Math.min(1,1-Math.abs(l)/c)):0,h=e.reduce((T,A)=>Math.max(T,Math.abs(A)),0),f=Math.abs(e[s]??0),b=c>1e-12?f/c:0,g=typeof(i==null?void 0:i.targetTokenText)=="string"?i.targetTokenText:typeof(i==null?void 0:i.targetTokenId)=="number"?`token ${i.targetTokenId}`:"not recorded",y=typeof(i==null?void 0:i.targetResponseIndex)=="number"?`response[${i.targetResponseIndex}]`:"response index not recorded",u=typeof(i==null?void 0:i.baseline)=="string"?i.baseline:"not recorded",k=typeof(i==null?void 0:i.nSteps)=="number"?String(i.nSteps):"not recorded",j=typeof(i==null?void 0:i.convergenceDelta)=="number"?i.convergenceDelta.toExponential(3):"not recorded";return t.jsxs("section",{className:"attribution-accounting","aria-label":"Attribution accounting",children:[t.jsxs("header",{children:[t.jsxs("div",{children:[t.jsx("strong",{children:"Attribution accounting"}),t.jsxs("span",{children:[a," · ",e.length," input positions"]})]}),t.jsx("b",{children:n?"signed balance":"unsigned mass"})]}),t.jsx("div",{className:"attribution-accounting-metrics",children:n?t.jsxs(t.Fragment,{children:[t.jsxs("span",{children:[t.jsx("b",{children:on(r)}),"positive sum"]}),t.jsxs("span",{children:[t.jsx("b",{children:on(o)}),"negative sum"]}),t.jsxs("span",{children:[t.jsx("b",{children:on(l)}),"net sum"]}),t.jsxs("span",{children:[t.jsxs("b",{children:[(d*100).toFixed(1),"%"]}),"sign cancellation"]})]}):t.jsxs(t.Fragment,{children:[t.jsxs("span",{children:[t.jsx("b",{children:on(c)}),"stored mass"]}),t.jsxs("span",{children:[t.jsx("b",{children:on(h)}),"peak magnitude"]}),t.jsxs("span",{children:[t.jsxs("b",{children:[(b*100).toFixed(1),"%"]}),"selected share"]}),t.jsxs("span",{children:[t.jsx("b",{children:"none"}),"sign semantics"]})]})}),i?t.jsxs("div",{className:"attribution-objective-context",children:[t.jsx(Rt,{size:16}),t.jsxs("span",{children:[t.jsx("b",{children:g}),y]}),t.jsxs("span",{children:[t.jsx("b",{children:u}),"baseline"]}),t.jsxs("span",{children:[t.jsx("b",{children:k}),"integration steps"]}),t.jsxs("span",{children:[t.jsx("b",{children:j}),"convergence delta"]})]}):t.jsxs("div",{className:"attribution-objective-context proxy",children:[t.jsx(lt,{size:16}),t.jsxs("span",{children:[t.jsx("b",{children:"No target/baseline contract"}),"This method is a run-relative diagnostic, not a target-specific completeness attribution."]})]}),t.jsx("p",{children:"Sum and cancellation are accounting checks within this method. They do not prove completeness, causal sufficiency, or comparability with another attribution scale."})]})}function on(e){const n=Math.abs(e);return n>0&&n<1e-4?e.toExponential(3):eo(e)}function wi({title:e,entries:n,selectedToken:a,onSelectToken:s}){const i=pt();return t.jsxs("div",{className:"attribution-polarity-list",children:[t.jsx("span",{children:e}),n.length>0?n.map(r=>t.jsxs("button",{className:r.tokenIndex===a?"active":"",onClick:()=>s(r.tokenIndex),children:[t.jsx("strong",{children:i.tokens[r.tokenIndex].text}),t.jsx("b",{children:r.value.toFixed(6)})]},r.tokenIndex)):t.jsx("p",{children:"No values in this direction."})]})}function Jm({selectedToken:e,selectedLayer:n,setSelectedLayer:a,metric:s,normalization:i,residualCell:r}){const o=pt(),l=Qn(o,"residual",s),c=s==="residual_norm"?i==="raw"?(r==null?void 0:r.norm)??0:(r==null?void 0:r.semanticDensity)??0:i==="raw"?(r==null?void 0:r.rawDirection)??0:(r==null?void 0:r.riskDirection)??0,d=o.logitLens.filter(h=>h.tokenIndex===e);return t.jsxs("section",{className:"surface component-evidence",children:[t.jsxs("div",{className:"surface-header",children:[t.jsxs("div",{children:[t.jsx("h3",{children:"Residual evidence"}),t.jsxs("p",{children:["layer_",n,".resid_post · token ",e]})]}),t.jsx(bn,{size:18})]}),t.jsxs("div",{className:"component-metric-grid",children:[t.jsxs("span",{children:[t.jsx("b",{children:c.toFixed(i==="raw"?6:3)}),"selected metric"]}),t.jsxs("span",{children:[t.jsx("b",{children:Oe((r==null?void 0:r.riskDirection)??0,"residual_direction")}),"direction alignment"]}),t.jsxs("span",{children:[t.jsx("b",{children:((r==null?void 0:r.norm)??0).toFixed(3)}),"activation norm"]})]}),t.jsxs("div",{className:"provenance-note",children:[t.jsx("b",{children:l.label}),t.jsx("p",{children:l.semantics}),t.jsx("span",{children:l.normalization})]}),t.jsx(wm,{rows:d,selectedLayer:n,onSelectLayer:a})]})}function Gm({selectedToken:e,selectedLayer:n,neuron:a}){const s=pt(),i=s.mlpCells.find(l=>l.layer===n&&l.tokenIndex===e),r=s.mlpNeurons.filter(l=>l.layer===n),o=(a==null?void 0:a.activationsByToken[e])??0;return t.jsxs("section",{className:"surface component-evidence",children:[t.jsxs("div",{className:"surface-header",children:[t.jsxs("div",{children:[t.jsx("h3",{children:"MLP activation"}),t.jsxs("p",{children:["layer_",n,".post · token ",e]})]}),t.jsx($a,{size:18})]}),t.jsxs("div",{className:"component-metric-grid",children:[t.jsxs("span",{children:[t.jsx("b",{children:o.toFixed(6)}),"signed neuron activation"]}),t.jsxs("span",{children:[t.jsx("b",{children:Math.abs(o).toFixed(6)}),"absolute activation"]}),t.jsxs("span",{children:[t.jsx("b",{children:(a==null?void 0:a.id)??"none"}),"selected retained neuron"]})]}),a&&t.jsxs("div",{className:"mlp-polarity-summary",children:[t.jsxs("div",{children:[t.jsx("span",{children:"Top positive tokens"}),t.jsx("p",{children:a.positiveTopTokens.map(l=>s.tokens[l].text).join(" · ")})]}),t.jsxs("div",{children:[t.jsx("span",{children:"Top negative tokens"}),t.jsx("p",{children:a.negativeTopTokens.map(l=>s.tokens[l].text).join(" · ")})]})]}),t.jsxs("div",{className:"provenance-note",children:[t.jsx("b",{children:"Raw MLP post activation"}),t.jsx("p",{children:"Signed activation describes neuron response only; it is not target-logit contribution, probe contribution, or causal ablation effect."}),t.jsxs("span",{children:["layer_",n,".post · ",r.length," retained neurons · aggregate mean |activation| ",((i==null?void 0:i.rawValue)??0).toFixed(6)]})]}),t.jsx("div",{className:"ranked-components",children:r.slice(0,8).map(l=>t.jsxs("span",{className:l.id===(a==null?void 0:a.id)?"active":"",children:[t.jsx("b",{children:l.id}),t.jsx("i",{children:(l.activationsByToken[e]??0).toFixed(4)})]},l.id))})]})}function Xm({filter:e,setFilter:n}){const a=[{id:"top",label:"Top"},{id:"neighborhood",label:"Nearby"},{id:"all",label:"All"}];return t.jsx("div",{className:"evidence-filter","aria-label":"Evidence filter",children:a.map(s=>t.jsx("button",{className:e===s.id?"active":"",onClick:()=>n(s.id),children:s.label},s.id))})}function Zm({rows:e,selectedToken:n,onSelectToken:a,scoreTone:s}){const i=pt();return t.jsxs("div",{className:"evidence-table",children:[t.jsxs("div",{className:"evidence-table-head",children:[t.jsx("span",{children:"source token"}),t.jsx("span",{children:"score"}),t.jsx("span",{children:"why it matters"})]}),e.map(r=>{const o=i.tokens[r.tokenIndex];return t.jsxs("button",{className:n===r.tokenIndex?"evidence-row selected":"evidence-row",onClick:()=>a(r.tokenIndex),style:{"--score":Math.abs(r.score)},children:[t.jsx("span",{className:"source-token",children:o.text}),t.jsxs("span",{className:`score-cell score-${s} ${r.score<0?"negative":"positive"}`,children:[t.jsx("i",{}),t.jsx("b",{children:s==="attention-difference"?Ea(r.score,"attention_retained_head_difference","compact"):Oe(r.score,"attention_probability")})]}),t.jsx("span",{className:"reason-cell",children:r.reason})]},`${r.tokenIndex}-${r.reason}`)})]})}function eh({row:e}){const n=pt(),a=e.status==="unavailable";return t.jsxs("article",{className:a?"nla-card nla-card-muted":"nla-card",children:[t.jsxs("div",{className:"nla-card-header",children:[t.jsxs("div",{children:[t.jsx("strong",{children:n.tokens[e.tokenIndex].text}),t.jsxs("span",{children:["L",e.layer," · ",e.component]})]}),t.jsxs("span",{className:`status-pill ${a?"status-warn":"status-live"}`,children:[a?t.jsx(lt,{size:13}):t.jsx(Xe,{size:13}),a?"not run":"ready"]})]}),t.jsx("p",{children:oh(e)}),t.jsxs("div",{className:"mini-metrics",children:[a?t.jsx("span",{children:"Qwen/Gemma NLA profiles required"}):t.jsxs(t.Fragment,{children:[t.jsxs("span",{children:["cos ",Oe(e.cosine,"nla_cosine")]}),t.jsxs("span",{children:["mse ",Oe(e.mse,"nla_mse")]})]}),t.jsxs("span",{children:["norm ",e.activationNorm.toFixed(1)]})]}),t.jsxs("details",{className:"detail-disclosure",children:[t.jsxs("summary",{children:[t.jsx("span",{children:"Full NLA message"}),t.jsx(Fn,{size:14})]}),t.jsx("p",{children:e.explanation})]})]})}function th({pinned:e,restorePin:n,availableRunKeys:a,openCompare:s}){return t.jsxs("section",{className:"pinned-strip",children:[t.jsxs("div",{className:"pinned-strip-heading",children:[t.jsxs("span",{children:[t.jsx(ot,{size:14})," Pinned evidence"]}),t.jsxs("button",{onClick:s,children:["Compare all (",e.length,")"]})]}),t.jsx("div",{className:"pinned-strip-items",children:e.map(i=>{const r=a.has(ut(i));return t.jsxs("button",{disabled:!r,title:r?"Restore evidence context":"Source run is not loaded",onClick:()=>n(i),children:[t.jsx("strong",{children:i.tokenText}),t.jsxs("span",{children:[i.runId," / ",i.sampleId]}),t.jsxs("span",{children:["L",i.layer," · ",De(i.view),i.view==="nla"?` · ${i.component}`:""]}),t.jsxs("span",{children:[el(i.metric)," ",Pe(i.value,i.metric,"compact")]})]},i.id)})})]})}function no(e){return e==="residual"?[{id:"residual_direction",label:"Direction alignment"},{id:"residual_norm",label:"Activation norm"}]:e==="attention"?[{id:"attention_concentration",label:"Attention concentration"}]:[{id:"mlp_magnitude",label:"Mean absolute activation"}]}function nh(e,n){const a=no(e);return a.some(s=>s.id===n)?n:a[0].id}function da(e){const n=["mlp_signed_activation","mlp_absolute_activation","mlp_normalized_activation"];return n.includes(e)?e:n[0]}function ca(e){return e==="nla_mse"?"mse":e==="nla_fve"?"fve":"cosine"}function Rn(e,n,a){return a==="mlp_absolute_activation"?Math.abs(e):a==="mlp_normalized_activation"?Math.abs(e)/Math.max(n,1e-12):e}function ki(e){return e==="mlp_absolute_activation"?"absolute raw activation":e==="mlp_normalized_activation"?"normalized activation magnitude":"signed raw activation"}function un({run:e,view:n,selectedToken:a,selectedSourceToken:s,selectedLayer:i,selectedNlaComponent:r,selectedHead:o,selectedNeuron:l,selectedAttributionMethod:c,metric:d,normalization:h,sourceArtifact:f}){var V,oe,de,P;const b=e.tokens[a]??e.tokens[0],g=e.residualCells.find(S=>S.layer===i&&S.tokenIndex===a),y=Yn(e.nla,a,i,r),u=c.rows.find(S=>S.layer===i)??c.rows[0],k=ih(e.metadata,n,a,i);let j="available",T="Exact evidence is available for the selected token and layer.",A="Safety proxy",C="not stored",w=Pe(b.risk,"tokenRisk","exact"),I="normalized score",L=`layer_${i}.resid_post[${a}]`,M=`scalar from [${e.nlaCompatibility.dModel}]`,q=e.metricProvenance.tokenRisk;const X=[];if(n==="overview"&&X.push("Run-relative proxy; it is not a calibrated safety probability or causal effect."),n==="residual"&&(q=Qn(e,"residual",d),A=q.label,L=`layer_${i}.resid_post[${a}]`,M=`[${e.nlaCompatibility.dModel}] residual vector`,I=d==="residual_norm"?"L2 norm":"projection",g?d==="residual_norm"?(C=Pe(g.norm,"residual_norm","exact"),w=Pe(h==="raw"?g.norm:g.semanticDensity,h==="raw"?"residual_norm":"normalized","exact")):(C=Pe(g.rawDirection,"residual_direction","exact"),w=Pe(h==="raw"?g.rawDirection:g.riskDirection,h==="raw"?"residual_direction":"normalized","exact"),X.push("Directional alignment is diagnostic projection, not causal contribution.")):(j="unavailable",T="No exact residual cell exists for the selected token and layer.",C="n/a",w="n/a")),n==="attention"){q=Ta(o,e.metricProvenance.attentionHeatmap);const S=(V=o.distributionByToken[a])==null?void 0:V[s];A=o.difference?"Retained-head probability difference":o.rollout?"Retained attention rollout":o.aggregation?xn(o.aggregation):"Attention probability";const Z=Gr(o);C=Pe(S,Z,"exact"),w=C,I=o.difference?"selected minus baseline probability":o.rollout?"retained rollout path weight":o.aggregation==="max"?"maximum retained-head probability":o.aggregation?"weighted retained-head probability":"softmax probability",L=Jr(o,a,s),M=`[${e.tokens.length} × ${e.tokens.length}]`,S===void 0?(j="unavailable",T="The exact source/destination attention cell is unavailable."):o.difference?(T=`Client-derived ${o.difference.selectedHeadId} minus ${o.difference.baselineHeadId} cell.`,X.push("This signed difference covers two retained artifact heads only and is not causal evidence.")):o.rollout?(T=`Client-derived retained-head rollout through L${o.layer}.`,X.push("This rollout uses artifact-retained heads only and is not full-model or causal evidence.")):o.aggregation&&(T=`Client-derived ${o.aggregation} cell over ${((oe=o.memberHeadIds)==null?void 0:oe.length)??0} retained heads.`,X.push("This aggregate covers retained artifact heads only, not every head in the model.")),X.push("Attention probability is descriptive and must not be read as causal attribution.")}if(n==="mlp"){q=e.metricProvenance.mlpNeuronActivation;const S=l==null?void 0:l.activationsByToken[a];A="MLP activation",C=Pe(S,"mlp_signed_activation","exact");const Z=S===void 0?void 0:Rn(S,(l==null?void 0:l.maxAbsoluteActivation)??1,d);w=Pe(Z,d,"exact"),I=d==="mlp_normalized_activation"?"normalized magnitude":"activation",L=l?`layer_${l.layer}.post[${a},${l.neuron}]`:`layer_${i}.post[${a},?]`,M=`[${e.tokens.length} × retained neurons]`,S===void 0&&(j="unavailable",T="No retained neuron strictly matches the selected layer and token."),X.push("Activation magnitude is not logit contribution, probe contribution, or ablation effect.")}if(n==="nla"){const S=ah(e.metadata);q={label:"NLA fidelity",method:S?`${String(S.profile)} AV/AR · ${String(S.actorRevision)} / ${String(S.reconstructorRevision)}`:"exact NLA decoder reconstruction",semantics:"Exact token/layer/component reconstruction fidelity for a compatible profile.",normalization:"stored method metric",kind:"safety_method"};const Z=d==="nla_mse"?y==null?void 0:y.mse:d==="nla_fve"?y==null?void 0:y.fve:y==null?void 0:y.cosine;A=d==="nla_mse"?"NLA MSE":d==="nla_fve"?"NLA FVE":"NLA cosine",C=(y==null?void 0:y.status)==="unavailable"?"n/a":Pe(Z,d,"exact"),w=C,I="fidelity metric",L=(y==null?void 0:y.source)??`nla[L${i},T${a}]`,M="scalar fidelity + explanation";const K=e.nlaCompatibility.profiles.some(N=>N.status==="compatible");!y||y.status==="unavailable"?(j=K?"not-computed":"incompatible",T=(y==null?void 0:y.explanation)??"No exact NLA result artifact was computed for this cell.",X.push((y==null?void 0:y.explanation)??"A compatible NLA artifact is required.")):Z===void 0&&(j="not-computed",T=`${A} was not stored for this otherwise available NLA row.`),S&&X.push(`Exact ${String(S.profile)} result for L${String(S.layer)} / ${String(S.component)}; trust_remote_code=${String(S.trustRemoteCode)}.`)}if(n==="attribution"){q=c.id==="integrated_gradients"&&e.metricProvenance.integratedGradients?e.metricProvenance.integratedGradients:{label:c.label,method:c.id,semantics:c.description,normalization:c.normalization,kind:c.evidenceKind};const S=c.id==="integrated_gradients"?ao(e.metadata):void 0,Z=u==null?void 0:u.values[a],K=Array.isArray(S==null?void 0:S.rawValues)?S.rawValues[a]:void 0,N=Z===void 0?void 0:sh(Z,c.rows,c.signed);if(A=c.label,C=Pe(typeof K=="number"?K:Z,c.id,"exact"),w=Pe(h==="raw"?Z:N,h==="raw"?c.id:"normalized","exact"),I=c.signed?"signed contribution":"unsigned proxy",L=(u==null?void 0:u.sourceKey)??`${c.id}[${a}]`,M=`[${c.rows.length} × ${e.tokens.length}]`,c.available?Z===void 0&&(j="unavailable",T="The selected attribution method has no exact value for this token."):(j="not-computed",T=c.unavailableReason??"Method output was not computed."),c.signed||X.push("Unsigned proxy values do not encode positive versus negative causal contribution."),S){const ne=typeof S.targetTokenText=="string"?S.targetTokenText:S.targetTokenId;X.push(`Target: ${String(ne)} at response[${String(S.targetResponseIndex)}]; baseline: ${String(S.baseline)}; steps: ${String(S.nSteps)}.`),Array.isArray(S.responseContextAttributions)&&S.responseContextAttributions.length&&X.push(`${S.responseContextAttributions.length} preceding response-context token attribution(s) are retained in job metadata but omitted from this prompt-token matrix.`)}}if(n==="patching"){const S=e.patching,Z=S==null?void 0:S.cells.find(N=>N.layer===i&&N.tokenIndex===a);q=Oa(e,d),A=q.label;const K=oo(Z,d);C=Pe(Z==null?void 0:Z.patchedScore,"patching_score","exact"),w=Pe(K,d,"exact"),I=d==="patching_recovery"?"percent recovery":"target-token logit",L=(Z==null?void 0:Z.sourceKey)??`patching[L${i},T${a}]`,M=S?`[${S.layers.length} × ${S.positions.length}] causal grid`:"not computed",S?Z?d==="patching_recovery"&&Z.recoveryPercentage===null?(j="unavailable",T="Recovery is undefined because clean and corrupted target logits are effectively equal.",X.push("Use causal effect or patched logit for this experiment; percentage recovery has a near-zero denominator.")):(T="Exact causal evidence from one clean-activation replacement forward pass.",X.push(`Clean logit ${S.cleanScore.toFixed(6)}; corrupted logit ${S.corruptedScore.toFixed(6)}; patched logit ${Z.patchedScore.toFixed(6)}.`)):(j="not-computed",T="The selected layer/token cell was not included in this patch grid."):(j="not-computed",T="This Run does not contain an activation patching experiment.")}if(n==="intervention"){const S=e.intervention;q=Va(e),A=q.label,C=Pe(S==null?void 0:S.steered.targetLogit,"intervention_target_logit","exact"),w=Pe(S==null?void 0:S.deltas.targetLogit,"intervention_logit_delta","exact"),I="raw target-token logit delta",L=(S==null?void 0:S.vector.sourceKey)??`intervention[L${i}]`,M=S?`[${S.vector.dimension}] normalized steering vector`:"not computed",S?(T="Exact original-versus-steered delta with matched seed and generation parameters.",X.push(`Original logit ${S.original.targetLogit.toFixed(6)}; steered logit ${S.steered.targetLogit.toFixed(6)}; token edit distance ${S.deltas.tokenEditDistance}.`),X.push(S.deltas.probeReason),S.deltas.lexicalRisk!==0&&X.push("Lexical risk delta is a fixed term-match proxy, not a trained probe score.")):(j="not-computed",T="This Run does not contain an intervention comparison.")}k&&(j="failed",T=k,X.unshift(k)),h==="normalized"&&C!==w&&w!=="n/a"&&X.push(`Displayed value uses: ${q.normalization}.`);const H=n==="attention"?`${gt(o)} · source ${s} → destination ${a}`:n==="mlp"?(l==null?void 0:l.id)??"no retained neuron":n==="attribution"?c.label:n==="patching"?((de=e.patching)==null?void 0:de.component)??"no experiment":n==="intervention"?((P=e.intervention)==null?void 0:P.component)??"no experiment":n==="nla"?(y==null?void 0:y.component)??"no exact component":"resid_post";return{title:b.text||"␠",subtitle:`${De(n)} · L${i} · ${H}`,status:j,statusReason:T,primaryLabel:A,primaryValue:w,rawValue:C,displayValue:w,units:I,evidenceClass:q.kind,method:q.method,normalization:q.normalization,cacheKey:L,shape:M,sourceArtifact:f,runId:e.runId,sampleId:e.sampleId,modelName:e.modelName,warnings:[...new Set(X)],reproduction:{schema_version:"1.0",run_id:e.runId,sample_id:e.sampleId,model:e.modelName,selection:{view:n,token:a,source_token:n==="attention"?s:void 0,layer:i,nla_component:n==="nla"?r:void 0,metric:d,normalization:h},evidence:{raw_value:C,display_value:w,units:I,cache_key:L},provenance:q}}}function ao(e){const n=e==null?void 0:e.attributionJobs;if(!Array.isArray(n)||n.length===0)return;const a=n[n.length-1];return a&&typeof a=="object"&&!Array.isArray(a)?a:void 0}function ah(e){const n=e==null?void 0:e.nlaJobs;if(!Array.isArray(n)||n.length===0)return;const a=n[n.length-1];return a&&typeof a=="object"&&!Array.isArray(a)?a:void 0}function sh(e,n,a){const s=n.flatMap(o=>o.values);if(a){const o=Math.max(1e-12,...s.map(l=>Math.abs(l)));return e/o}const i=Math.min(...s),r=Math.max(...s);return Math.abs(r-i)<1e-12?0:(e-i)/(r-i)}function ih(e,n,a,s){const i=e==null?void 0:e.analysisFailures;if(!Array.isArray(i))return;const r=i.find(o=>{if(!o||typeof o!="object")return!1;const l=o;return l.view===n&&(l.token===void 0||l.token===a)&&(l.layer===void 0||l.layer===s)});return typeof(r==null?void 0:r.message)=="string"?r.message:void 0}function vi(e,n,a){return n==="overview"?e.metricProvenance.tokenRisk:n==="residual"?Qn(e,"residual",a):n==="attention"?e.metricProvenance.attentionHeatmap:n==="mlp"?e.metricProvenance.mlpNeuronActivation:n==="patching"?Oa(e,a):n==="intervention"?Va(e):e.metricProvenance.tokenAttribution??e.metricProvenance.tokenRisk}function so(e,n,a){return n==="attention"?e.attentionCells.map(s=>({row:s.layer,column:s.tokenIndex,value:s.value,rawValue:s.rawValue,metric:s.metric,sourceKey:s.sourceKey})):n==="mlp"?e.mlpCells.map(s=>({row:s.layer,column:s.tokenIndex,value:s.value,rawValue:s.rawValue,metric:s.metric,sourceKey:s.sourceKey})):e.residualCells.map(s=>({row:s.layer,column:s.tokenIndex,value:a==="residual_norm"?s.semanticDensity:s.riskDirection,rawValue:a==="residual_norm"?s.norm:s.rawDirection,metric:a==="residual_norm"?"residual_l2_norm":"residual_direction_projection",sourceKey:`layer_${s.layer}.resid_post`}))}function Qn(e,n,a){return n==="residual"&&a==="residual_norm"?{label:"Residual activation norm",method:"L2 norm over the resid_post model dimension",semantics:"Raw activation magnitude; high norm does not imply high safety risk.",normalization:"min-max over all layer-token residual norms",kind:"raw"}:e.metricProvenance[rh(n)]}function rh(e){return e==="attention"?"attentionHeatmap":e==="mlp"?"mlpHeatmap":"residualHeatmap"}function io(e){return[...e].sort((n,a)=>a.risk-n.risk).slice(0,3).map(n=>n.index)}function oh(e){return e.status==="unavailable"?"NLA unavailable for this model. Current real run uses tiny-gpt2; public NLA profiles target Qwen/Gemma.":e.explanation}function ua(e,n,a){const s=e==null?void 0:e[n];return typeof s=="string"||typeof s=="number"?String(s):a}function lh(e,n,a){return a==="neighborhood"?e.filter(s=>Math.abs(s.tokenIndex-n)<=2).sort((s,i)=>i.score-s.score):a==="all"?[...e].sort((s,i)=>s.tokenIndex-i.tokenIndex):[...e].sort((s,i)=>i.score-s.score).slice(0,8)}function dh(e,n,a){return a==="neighborhood"?e.filter(s=>Math.abs(s.tokenIndex-n)<=2).sort((s,i)=>Math.abs(i.score)-Math.abs(s.score)):a==="all"?[...e].sort((s,i)=>s.tokenIndex-i.tokenIndex):[...e].sort((s,i)=>Math.abs(i.score)-Math.abs(s.score)).slice(0,8)}function ch(e,n,a){return n===a?"query token":Math.abs(n-a)<=2?"local context":e.nla.some(s=>s.tokenIndex===n)?"cached evidence":"attended source"}function Yn(e,n,a,s){return e.find(i=>i.tokenIndex===n&&i.layer===a&&i.component===s)}function uh(e){return e==="attention"?"attention":e==="mlp"?"mlp":"residual"}function mh({view:e,tokenText:n,tokenIndex:a,sourceTokenIndex:s,tokenRange:i,layer:r,metric:o,normalization:l,headId:c,neuronId:d,nlaComponent:h,attributionMethod:f,attentionEdgeMode:b}){const g=n.replace(/\s+/g," ").trim()||"whitespace",y=g.length>18?`${g.slice(0,17)}…`:g,u=o.replace(/_/g," "),k=i?`tokens ${i[0]}–${i[1]}`:e==="attention"?`${s} → ${a} “${y}”`:`token ${a} “${y}”`,j=e==="attention"?`${c} · ${b} · ${u}`:e==="mlp"?`${d??"no retained neuron"} · ${u}`:e==="nla"?`${h} · ${u}`:e==="attribution"?f:u;return{signature:[e,a,s,(i==null?void 0:i.join("-"))??"",r,o,l,e==="attention"?`${c}:${b}`:"",e==="mlp"?d??"":"",e==="nla"?h:"",e==="attribution"?f:""].join("|"),message:`${De(e)} · L${r} · ${k} · ${j} · ${l}`}}function De(e){return{overview:"Overview",residual:"Residual",attention:"Attention",mlp:"MLP",nla:"NLA",patching:"Patching",intervention:"Intervention",attribution:"Attribution"}[e]}function hh(e,n){if(n.status==="loading"||n.status==="cancelled")return[];const a=[],s=r=>{a.some(o=>o.id===r.id)||a.push(r)},i=n.status!=="available";return i&&e==="attribution"?s({id:"configure_attribution",kind:"attribution",label:"Configure Integrated Gradients",description:"Choose a response target, baseline, and integration steps."}):i&&e==="nla"?s({id:"configure_nla",kind:"nla",label:"Configure NLA job",description:"Check profile compatibility and compute an exact explanation."}):i&&e==="patching"?s({id:"configure_patching",kind:"patching",label:"Configure causal patching",description:"Select a changed prompt, component, layer, and target."}):i&&e==="intervention"?s({id:"configure_intervention",kind:"intervention",label:"Configure intervention",description:"Define the contrast, scale, position range, and generation target."}):i&&s(ma()),n.evidenceClass==="causal"?(e!=="intervention"&&s({id:"open_intervention",kind:"intervention",label:"Open intervention comparison",description:"Inspect whether a controlled steering change alters generation."}),e!=="overview"&&s(ma()),e!=="attribution"&&s(ji())):(e!=="patching"&&s(ph()),e!=="attribution"&&s(ji()),e!=="nla"&&s(yh()),e!=="overview"&&s(ma())),a.slice(0,3)}function ph(){return{id:"open_patching",kind:"patching",label:"Run causal patching",description:"Measure a replacement effect instead of inferring causality from a proxy."}}function ji(){return{id:"open_attribution",kind:"attribution",label:"Open target attribution",description:"Inspect signed or target-specific token evidence."}}function yh(){return{id:"open_nla",kind:"nla",label:"Open exact NLA",description:"Check activation explanation, compatibility, and decoder fidelity."}}function ma(){return{id:"open_overview",kind:"overview",label:"Return to evidence map",description:"Review available, supporting, and contradictory evidence together."}}function fh(e){if(e==="configure_attribution"||e==="open_attribution")return{view:"attribution",anchorId:"attribution-job"};if(e==="configure_nla"||e==="open_nla")return{view:"nla",anchorId:"nla-job"};if(e==="configure_patching"||e==="open_patching")return{view:"patching",anchorId:"patching-job"};if(e==="configure_intervention"||e==="open_intervention")return{view:"intervention",anchorId:"intervention-job"};if(e==="open_overview")return{view:"overview"}}function ro(e,n=40){const a=document.getElementById(e);if(a){a.scrollIntoView({block:"start"}),a.focus({preventScroll:!0});return}n>1&&window.setTimeout(()=>ro(e,n-1),25)}function gh(e,n,a){var u,k,j,T;const s=new Set(n.tokens.map(A=>A.index)),i=e.selection.targetTokenIndex??e.selection.tokenIndex,r=s.has(i)?i:s.has(e.selection.tokenIndex)?e.selection.tokenIndex:((u=n.tokens[0])==null?void 0:u.index)??a.tokenIndex,o=e.selection.sourceTokenIndex??r,l=s.has(o)?Math.min(o,r):r,c=n.layers.includes(e.selection.layer)?e.selection.layer:n.layers[n.layers.length-1]??a.layer,d=e.selection.tokenRange,h=d&&s.has(d[0])&&s.has(d[1])?[Math.min(...d),Math.max(...d)]:void 0,f=n.attentionHeads.filter(A=>A.layer===c),b=n.mlpNeurons.filter(A=>A.layer===c),g=n.attributionMethods.filter(A=>A.available),y=n.attributionMethods.some(A=>A.id===e.selection.trackName)?e.selection.trackName:((k=g[0])==null?void 0:k.id)??a.trackName;return{...e.selection,tokenIndex:r,sourceTokenIndex:l,targetTokenIndex:r,tokenRange:h,layer:c,headId:f.some(A=>A.id===e.selection.headId)||Vr(e.selection.headId)||Ka(e.selection.headId)||pm(f,e.selection.headId)?e.selection.headId:((j=f[0])==null?void 0:j.id)??a.headId,attentionEdgeMode:e.selection.attentionEdgeMode??"incoming",nlaComponent:e.selection.nlaComponent??a.nlaComponent,neuronId:b.some(A=>A.id===e.selection.neuronId)?e.selection.neuronId:((T=b[0])==null?void 0:T.id)??a.neuronId,trackName:y,metric:e.selection.view==="attribution"&&e.selection.metric===e.selection.trackName?y:e.selection.metric,pinnedItems:e.pinnedItems.slice(-4)}}function _h(e,n){const a=e.timeline??{mode:"token",metric:"risk",query:""};return{mode:a.mode,metric:a.metric==="probe"&&!n.tokens.some(s=>s.probeScore!==void 0)?"risk":a.metric,query:a.query.slice(0,256)}}const Ii={residual:[10,34],attention:[14,36],mlp:[20,42],attribution:[14,38],nla:[14,38],patching:[32,64]};function bh(e){if(!e)return{};const n={};for(const a of Object.keys(Ii)){const s=e[a];if(!s)continue;const[i,r]=Ii[a];n[a]={...s,size:Math.max(i,Math.min(r,s.size))}}return n}function xh(e){return e==="patching_effect"?"effect":e==="patching_score"?"score":"recovery"}function oo(e,n){if(e)return n==="patching_effect"?e.causalEffect:n==="patching_score"?e.patchedScore:e.recoveryPercentage}function Oa(e,n){const a=n==="patching_effect"?"patchingCausalEffect":n==="patching_score"?"patchingPatchedScore":"patchingRecovery";return e.metricProvenance[a]??{label:"Activation patching",method:"clean activation replacement",semantics:"Causal target-logit response to one activation replacement.",normalization:"none",kind:"causal"}}function Va(e){return e.metricProvenance.interventionTargetLogitDelta??{label:"Target logit delta",method:"normalized contrastive activation steering",semantics:"Steered target-token logit minus the original target-token logit.",normalization:"none; raw logit difference",kind:"causal"}}const ha=256,wh=64;function Ai(e,n,a,s){if(n.length===0)return;const i=kh(n,[a,s],wh).map(l=>({tokenIndex:l.index,tokenId:l.tokenId,tokenText:l.text})),r=i.map(l=>i.map(c=>{var h;if(c.tokenIndex>l.tokenIndex)return null;const d=(h=e.distributionByToken[l.tokenIndex])==null?void 0:h[c.tokenIndex];return Number.isFinite(d)&&d!==void 0&&d>=0&&d<=1?d:null}));if(r.every((l,c)=>l.every((d,h)=>i[h].tokenIndex>i[c].tokenIndex||d!==null)))return{schemaVersion:"1.0",kind:"attention_matrix",label:`${gt(e)} · ${n.length}×${n.length}`,originalSize:n.length,sampled:i.length<n.length,axis:i,values:r}}function kh(e,n,a){if(e.length<=a)return e;const s=new Set;for(let r=0;r<a;r+=1)s.add(Math.round(r*(e.length-1)/(a-1)));const i=new Set([0,e.length-1]);for(const r of n){const o=e.findIndex(c=>c.index===r);if(o<0||(i.add(o),s.has(o)))continue;const l=[...s].filter(c=>!i.has(c)).sort((c,d)=>Math.abs(c-o)-Math.abs(d-o))[0];l!==void 0&&s.delete(l),s.add(o)}return[...s].sort((r,o)=>r-o).map(r=>e[r])}function ln({kind:e,label:n,axis:a,signed:s,tokens:i,values:r,preserveTokenIndex:o}){const l=i.flatMap(d=>{const h=r[d.index];return Number.isFinite(h)?[{tokenIndex:d.index,tokenId:d.tokenId,tokenText:d.text,value:h}]:[]});if(l.length===0)return;let c=l;if(l.length>ha){const d=new Set;for(let f=0;f<ha;f+=1)d.add(Math.round(f*(l.length-1)/(ha-1)));const h=l.findIndex(f=>f.tokenIndex===o);if(h>=0&&!d.has(h)){const f=[...d].filter(b=>b!==0&&b!==l.length-1).sort((b,g)=>Math.abs(b-h)-Math.abs(g-h))[0];f!==void 0&&d.delete(f),d.add(h)}c=[...d].sort((f,b)=>f-b).map(f=>l[f])}return{schemaVersion:"1.0",kind:e,label:n,axis:a,signed:s,originalLength:l.length,sampled:c.length<l.length,points:c}}function lo(e,n,a){return e==="attention"?gt(n):e==="mlp"?(a==null?void 0:a.id)??"MLP":"resid_post"}Co.createRoot(document.getElementById("root")).render(t.jsx(Ce.StrictMode,{children:t.jsx($m,{})}));export{Ch as A,Ka as B,Vr as C,nl as D,ft as E,Ul as J,Sh as M,Br as a,Gr as b,Pe as c,gt as d,xn as e,Ea as f,um as g,cm as h,Jr as i,pn as j,Yc as k,Hi as l,Yd as m,Da as n,au as o,Qr as p,Id as q,Ad as r,qc as s,hc as t,il as u,Rd as v,Mr as w,gr as x,Mn as y,el as z};
