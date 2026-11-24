import { cp, mkdir, readFile, writeFile, readdir, stat } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
for(const id of ['era5','gpm','hku','fire','vegetation','pm25','blackmarble']){
  const catalog=JSON.parse(await readFile(path.join(root,'public','catalog',id+'.json'),'utf8'));
  const first=path.join(root,'public','data',id,'maps',(catalog.map_layout==='month_blocks'?catalog.periods[0].slice(0,7):catalog.periods[0])+'.bin.gz');
  try { await stat(first); } catch (error) {
    if(error.code!=='ENOENT')throw error;
    console.error(`C05_DATA_MISSING: ${first}\nRestore local webdata with scripts/restore_webdata.py --packages PATH. On Netlify use scripts/build_netlify.py and a published BOLIVIA_DATA_RELEASE_TAG.`);
    process.exit(1);
  }
}
await mkdir(path.join(root,'dist'),{recursive:true});
for(const dir of ['public','src'])await cp(path.join(root,dir),path.join(root,'dist'),{recursive:true,force:true});
if(process.env.BOLIVIA_RELEASE_BASE_URL){
  const base=process.env.BOLIVIA_RELEASE_BASE_URL;
  if(!/^https:\/\/github\.com\/Favioleiva\/BoliviaSatellites\/releases\/download\/[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/.test(base)||base.endsWith('/latest'))throw new Error('C05_INVALID_RELEASE_BASE_URL');
  const file=path.join(root,'dist','downloads','download_manifest.json');
  const manifest=JSON.parse(await readFile(file,'utf8'));
  for(const asset of manifest.files)asset.url=base+'/'+encodeURIComponent(asset.name);
  manifest.download_resolution={kind:'versioned_release',base_url:base};
  await writeFile(file,JSON.stringify(manifest,null,2));
}
const walk=async d=>(await Promise.all((await readdir(d)).map(async n=>{let p=path.join(d,n);return (await stat(p)).isDirectory()?walk(p):p}))).flat();
let files=await walk(path.join(root,'dist'));let bytes=0;for(const f of files)bytes+=(await stat(f)).size;
console.log(JSON.stringify({files:files.length,bytes,limitBytes:250*1024*1024,limitFiles:15000}));
if(bytes>250*1024*1024||files.length>15000){
  console.error(`C05_BUDGET_EXCEEDED: ${bytes} bytes / ${files.length} files; limits 262144000 bytes / 15000 files. Data restoration succeeded, but deployment is still blocked.`);
  process.exitCode=1;
}
