// One-time source migration: explicit i18next calls, not DOM mutation.
import ts from '../frontend/node_modules/typescript/lib/typescript.js';
import fs from 'node:fs';
import path from 'node:path';
const root=path.resolve('frontend/src');
const keys=new Set();
const factory=ts.factory;
for(const folder of ['pages','layouts','components']){
 for(const name of fs.readdirSync(path.join(root,folder)).filter(n=>n.endsWith('.tsx')&&!n.includes('.test.')&&n!=='LanguageSwitcher.tsx')){
  const target=path.join(root,folder,name),source=fs.readFileSync(target,'utf8');
  if(source.includes("from '../i18n'"))continue;
  const parsed=ts.createSourceFile(target,source,ts.ScriptTarget.Latest,true,ts.ScriptKind.TSX);
  const call=value=>{keys.add(value);return factory.createCallExpression(factory.createIdentifier('t'),undefined,[factory.createStringLiteral(value)]);};
  const result=ts.transform(parsed,[context=>{
   const visit=node=>{
    if(ts.isJsxText(node)&&node.text.trim()){
      const value=node.text.replace(/\s+/g,' ').trim();
      return factory.createJsxExpression(undefined,call(value));
    }
    if(ts.isJsxAttribute(node)&&['eyebrow','title','description','placeholder','aria-label'].includes(node.name.text)&&node.initializer&&ts.isStringLiteral(node.initializer)){
      return factory.updateJsxAttribute(node,node.name,factory.createJsxExpression(undefined,call(node.initializer.text)));
    }
    if(ts.isFunctionDeclaration(node)&&node.name&&/^[A-Z]/.test(node.name.text)&&node.body){
      const updated=ts.visitEachChild(node,visit,context);
      return factory.updateFunctionDeclaration(updated,updated.modifiers,updated.asteriskToken,updated.name,updated.typeParameters,updated.parameters,updated.type,factory.updateBlock(updated.body,[factory.createExpressionStatement(factory.createCallExpression(factory.createIdentifier('useLanguage'),undefined,[])),...updated.body.statements]));
    }
    return ts.visitEachChild(node,visit,context);
   };return node=>ts.visitNode(node,visit);
  }]);
  const output=ts.createPrinter().printFile(result.transformed[0]);
  fs.writeFileSync(target,"import {t,useLanguage} from '../i18n';\n"+output);result.dispose();
 }
}
const en=Object.fromEntries([...keys].sort().map(k=>[k,k]));
fs.writeFileSync(path.join(root,'i18n/en.json'),JSON.stringify(en,null,2)+'\n');
console.log(JSON.stringify([...keys].sort(),null,2));
