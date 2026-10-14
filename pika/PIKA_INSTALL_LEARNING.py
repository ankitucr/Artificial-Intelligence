from pathlib import Path
import importlib.util, shutil, sys
ROOT=Path.cwd(); BRAIN=ROOT/'core'/'brain.py'; SOURCE=Path(__file__).with_name('pika_code_learning.py'); TARGET=ROOT/'core'/'pika_code_learning.py'
if not BRAIN.is_file() or not (ROOT/'data'/'github_code_corpus').exists(): raise SystemExit('Run from PIKA root; core/brain.py or data/github_code_corpus missing.')
src=BRAIN.read_text(encoding='utf-8')
if 'PIKA_GITHUB_KNOWLEDGE_INTEGRATION_V1' in src: raise SystemExit('Already installed; no duplicate patch made.')
anchors=[('import','from core.learning_engine import LearningEngine'),('init','''        self.learning_engine = LearningEngine(
            project_root / "data" / "learning_engine.json"
        )'''),('context','''            context = {
                "plan": plan,'''),('execute','''            result = await agent.execute(
                task,
                context=context,
            )''')]
for name,a in anchors:
 if a not in src: raise SystemExit(f'Safe stop: Brain anchor missing: {name}. No Brain edits made.')
if not SOURCE.is_file(): raise SystemExit(f'Missing companion module: {SOURCE}')
new=src.replace(anchors[0][1],anchors[0][1]+'\nfrom core.pika_code_learning import PikaCodeLearning',1)
new=new.replace(anchors[1][1],anchors[1][1]+'''\n        # PIKA_GITHUB_KNOWLEDGE_INTEGRATION_V1
        self.github_knowledge = PikaCodeLearning(project_root)
        self.github_knowledge.index_corpus()''',1)
new=new.replace(anchors[2][1],'''            github_knowledge_context = self.github_knowledge.retrieve(task, limit=4)
            context = {
                "github_code_knowledge": github_knowledge_context,
                "plan": plan,''',1)
new=new.replace(anchors[3][1],anchors[3][1]+'''\n            self.github_knowledge.record_outcome(
                task, github_knowledge_context,
                success=bool(result.get("success")), evaluation=None,
                used=bool(github_knowledge_context.get("items")), attempt=attempt_number,
            )''',1)
compile(new,str(BRAIN),'exec'); compile(SOURCE.read_text(encoding='utf-8'),str(TARGET),'exec')
backup=BRAIN.with_name('brain.py.pre_github_learning_v1')
if not backup.exists(): shutil.copy2(BRAIN,backup)
shutil.copy2(SOURCE,TARGET)
tmp=BRAIN.with_suffix('.py.pika_tmp'); tmp.write_text(new,encoding='utf-8'); compile(tmp.read_text(encoding='utf-8'),str(tmp),'exec'); tmp.replace(BRAIN)
spec=importlib.util.spec_from_file_location('pika_learning_check',TARGET); mod=importlib.util.module_from_spec(spec); sys.modules[spec.name]=mod; spec.loader.exec_module(mod)
learner=mod.PikaCodeLearning(ROOT); indexing=learner.index_corpus(); retrieval=learner.retrieve('agent memory retrieval planning evaluation testing',limit=3)
print('INSTALLATION: PASS'); print('Backup:',backup); print('Index:',indexing); print('Retrieval hits:',len(retrieval['items']))
for item in retrieval['items']: print('-',item['source'],'score=',item['relevance'])
print('Public source is indexed as data; downloaded code was not executed.')
print('Logs:',ROOT/'data'/'pika_learning_events.jsonl')
