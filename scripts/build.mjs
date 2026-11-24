import { cp, mkdir, readFile, writeFile, readdir, stat } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
for(const id of ['era5','gpm','hku','fire','vegetation','pm25','blackmarble']){
  const catalog=JSON.parse(await readFile(path.join(root,'public','catalog',id+'.json'),'utf8'));
  await stat(path.join(root,'public','data',id,'maps',(catalog.map_layout==='month_blocks'?catalog.periods[0].slice(0,7):catalog.periods[0])+'.bin.gz'));
}
await mkdir(path.join(root,'dist'),{recursive:true});
for(const dir of ['public','src'])await cp(path.join(root,dir),path.join(root,'dist'),{recursive:true,force:true});
const walk=async d=>(await Promise.all((await readdir(d)).map(async n=>{let p=path.join(d,n);return (await stat(p)).isDirectory()?walk(p):p}))).flat();
let files=await walk(path.join(root,'dist'));let bytes=0;for(const f of files)bytes+=(await stat(f)).size;
console.log(JSON.stringify({files:files.length,bytes,limitBytes:250*1024*1024,limitFiles:15000}));
if(bytes>250*1024*1024||files.length>15000)process.exitCode=1;
