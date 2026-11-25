const fs=require('fs');const h=fs.readFileSync(require('path').join(__dirname,'..','index.html'),'utf8');
const src=h.split('/*ENGINE*/')[1].split('/*END*/')[0];
const E=new Function(src+';return{pump,refCode,commission,applyCallback,COUNTY,PIPE}')();
module.exports=E;
if(require.main===module){const cases=JSON.parse(fs.readFileSync(process.argv[2]));console.log(JSON.stringify(cases.map(c=>E.pump(c))))}
