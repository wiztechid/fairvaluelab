#!/usr/bin/env node
const fs=require('fs'),path=require('path'),os=require('os'),cp=require('child_process'),{authorize}=require('./scanner-publication-authorization-v1'),{verifyActivation}=require('./scanner-production-activation-v1');
const fail=m=>{throw new Error('[scanner-publisher] '+m)};
const write=(p,v)=>{fs.mkdirSync(path.dirname(p),{recursive:true});fs.writeFileSync(p,JSON.stringify(v,null,2)+'\n')};
function stageAuthorizedPublication({batch,authorization,now,root,sourceRoot=path.resolve(__dirname,'..')}={}){
 if(!root||path.resolve(root)===path.resolve(sourceRoot))fail('staging root required');
 const proof=authorize({batch,authorization,now});
 const stage=fs.mkdtempSync(path.join(path.dirname(path.resolve(root)),'.scanner-publish-'));
 try{
  for(const p of ['data/summary.json','data/scanner/reason-registry.json','contracts/scanner-summary-v1.schema.json','contracts/scanner-ticker-v1.schema.json']){const d=path.join(stage,p);fs.mkdirSync(path.dirname(d),{recursive:true});fs.copyFileSync(path.join(sourceRoot,p),d)}
  for(const ticker of Object.keys(batch.tickers)){const src=path.join(sourceRoot,'data',ticker+'.json');if(!fs.existsSync(src))fail('canonical Fair Value record missing '+ticker);fs.copyFileSync(src,path.join(stage,'data',ticker+'.json'))}
  write(path.join(stage,'data/scanner/summary.json'),batch.summary);
  for(const [ticker,obj] of Object.entries(batch.tickers))write(path.join(stage,'data/scanner/tickers',ticker+'.json'),obj);
  cp.execFileSync(process.execPath,[path.join(sourceRoot,'scripts/scanner-publication-gate.js')],{stdio:'pipe',env:{...process.env,SCANNER_PUBLICATION_ROOT:stage}});
  return {stage,proof,authorization:Object.freeze({...authorization})};
 }catch(e){fs.rmSync(stage,{recursive:true,force:true});throw e}
}
function promoteStagedPublication({stage,root,authorization,activation,activationAuthorityKey,now,simulateFailureAfterBackup=false}={}){
 const productionMode=require('./scanner-production-mode-gate-v1');if(productionMode.mode!=='CONTROLLED_ACTIVATION')fail('production mode locked');
 verifyActivation(activation,activationAuthorityKey,{authorization,now});
 if(!stage||!root||!fs.existsSync(path.join(stage,'data/scanner/summary.json')))fail('validated stage required');
 const stageReal=fs.realpathSync(stage),rootReal=fs.realpathSync(root);
 if(path.dirname(stageReal)!==path.dirname(rootReal)||!path.basename(stageReal).startsWith('.scanner-publish-'))fail('untrusted stage location');
 const target=path.join(path.resolve(root),'data/scanner'),backup=target+'.backup-'+process.pid;
 try{
  if(fs.existsSync(target))fs.renameSync(target,backup);
  if(simulateFailureAfterBackup)throw new Error('simulated promote failure');
  fs.mkdirSync(path.dirname(target),{recursive:true});fs.renameSync(path.join(stage,'data/scanner'),target);
  if(fs.existsSync(backup))fs.rmSync(backup,{recursive:true,force:true});fs.rmSync(stage,{recursive:true,force:true});
 }catch(e){if(fs.existsSync(target))fs.rmSync(target,{recursive:true,force:true});if(fs.existsSync(backup))fs.renameSync(backup,target);throw e}
}
module.exports={stageAuthorizedPublication,promoteStagedPublication};
