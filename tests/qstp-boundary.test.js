const assert=require('assert');
function tickSize(p){return p<200?1:p<500?2:p<2000?5:p<5000?10:25}
function tickDown(p){const t=tickSize(p);return Math.floor(p/t)*t}
function tickUp(p){const t=tickSize(p);return Math.ceil(p/t)*t}
const boundaries=[[199,1],[200,2],[499,2],[500,5],[1999,5],[2000,10],[4999,10],[5000,25],[10000,25]];
for(const [p,t] of boundaries)assert.strictEqual(tickSize(p),t,'tick '+p);
assert.strictEqual(tickDown(663),660); assert.strictEqual(tickUp(663),665);
assert.strictEqual(tickDown(5627),5625); assert.strictEqual(tickUp(5627),5650);
function lots({cap,e,sl,risk=.01,max=.35,deploy=.8,heat=.03,used=0,heatUsed=0}){const rps=e-sl;return Math.max(0,Math.min(Math.floor(cap*risk/rps/100),Math.floor(cap*max/e/100),Math.floor(Math.max(0,cap*deploy-used)/e/100),Math.floor(Math.max(0,cap*heat-heatUsed)/rps/100)))}
assert.strictEqual(lots({cap:500000,e:660,sl:625}),1,'small capital');
assert.strictEqual(lots({cap:1000000,e:10000,sl:9500}),0,'expensive stock');
assert.strictEqual(lots({cap:20000000,e:660,sl:655}),106,'tight stop max position');
assert.strictEqual(lots({cap:20000000,e:660,sl:500}),12,'wide stop risk budget');
assert.strictEqual(lots({cap:20000000,e:1000,sl:990,heat:.02,heatUsed:400000}),0,'heat exhausted');
assert.strictEqual(lots({cap:20000000,e:1000,sl:990,deploy:1,used:20000000}),0,'capital exhausted');
console.log('QSTP v1.2 boundary tests PASS:',boundaries.length+6,'checks');