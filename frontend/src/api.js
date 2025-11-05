export async function analyzeDrug(drug,indication,useGpu){
const res=await fetch("http://localhost:5000/analyze",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({drug,indication,use_gpu:useGpu})});
if(!res.ok)throw new Error("fail");return res.json();}
export async function checkGpuStatus(){try{const r=await fetch("http://localhost:9000/health");if(!r.ok)return{status:"offline"};const d=await r.json();return{status:"online",device:d.device}}catch{return{status:"offline"}}}