"""Read-only PZNS gate against the installed game's actual class files."""
import json, re, struct, zipfile, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAME = Path(r'G:\Games\ProjectZomboid')
MOD = ROOT / 'vendor/PZNS/PZNS_Framework'

def read_class(data):
    pos = 8
    def u(n):
        nonlocal pos
        result = int.from_bytes(data[pos:pos+n], 'big'); pos += n
        return result
    count = u(2); cp = [None] * count; i = 1
    while i < count:
        tag = u(1)
        if tag == 1:
            size = u(2); cp[i] = data[pos:pos+size].decode('utf8', 'replace'); pos += size
        elif tag in (7, 8, 16, 19, 20): cp[i] = u(2)
        elif tag in (3, 4): pos += 4
        elif tag in (5, 6): pos += 8; i += 1
        elif tag in (9, 10, 11, 12, 17, 18): pos += 4
        elif tag == 15: pos += 3
        else: raise ValueError(tag)
        i += 1
    u(2); u(2); parent = u(2)
    superclass = cp[cp[parent]] if parent else None
    for _ in range(u(2)): u(2)
    def members():
        result = []
        for _ in range(u(2)):
            access, name, desc = u(2), cp[u(2)], cp[u(2)]
            result.append({'name': name, 'descriptor': desc, 'public': bool(access & 1)})
            for _ in range(u(2)):
                u(2); size = u(4); nonlocal_skip(size)
        return result
    def nonlocal_skip(size):
        nonlocal pos
        pos += size
    fields = members(); methods = members()
    return superclass, methods, [x for x in cp if isinstance(x, str)]

with zipfile.ZipFile(GAME / 'projectzomboid.jar') as jar:
    cache = {}
    def cls(name):
        if name not in cache: cache[name] = read_class(jar.read(name + '.class'))
        return cache[name]
    def methods(name):
        parent, own, _ = cls(name)
        return own + (methods(parent) if parent and parent + '.class' in jar.namelist() else [])
    player = methods('zombie/characters/IsoPlayer')
    checks = []
    for name, desc in [('setNPC','(Z)V'), ('setSceneCulled','(Z)V'),
                       ('setForname','(Ljava/lang/String;)V'), ('setSurname','(Ljava/lang/String;)V')]:
        checks.append({'check': 'IsoPlayer.' + name + desc,
                       'pass': any(m['name']==name and m['descriptor']==desc and m['public'] for m in player)})
    constructors = [m for m in cls('zombie/characters/IsoPlayer')[1] if m['name']=='<init>']
    expected = '(Lzombie/iso/IsoCell;Lzombie/characters/SurvivorDesc;III)V'
    checks.append({'check': 'PZNS five-argument IsoPlayer constructor', 'pass': any(m['descriptor']==expected and m['public'] for m in constructors)})
    versions = [s for s in cls('zombie/core/Core')[2] if re.fullmatch(r'42\.\d+(?:\.\d+)?', s)]
    factory = [m for m in cls('zombie/characters/SurvivorFactory')[1] if m['name']=='CreateSurvivor']
    checks.append({'check':'SurvivorFactory.CreateSurvivor(type, boolean)', 'pass':any(m['descriptor']=='(Lzombie/characters/SurvivorFactory$SurvivorType;Z)Lzombie/characters/SurvivorDesc;' and m['public'] for m in factory)})

mod_files = list((MOD / 'media/lua').rglob('*.lua'))
available = {p.relative_to(base).with_suffix('').as_posix().lower() for base in [MOD/'media/lua/client',MOD/'media/lua/shared',MOD/'media/lua/server',GAME/'media/lua/client',GAME/'media/lua/shared',GAME/'media/lua/server'] if base.exists() for p in base.rglob('*.lua')}
missing = []
for p in mod_files:
    text = p.read_text(encoding='utf-8-sig')
    text = re.sub(r'--\[\[.*?\]\]', '', text, flags=re.S)
    text = re.sub(r'--[^\n]*', '', text)
    for req in re.findall(r'\brequire\s*\(?\s*[\"\x27]([^\"\x27]+)', text):
        if req.lower().removesuffix('.lua') not in available:
            missing.append({'file':str(p.relative_to(MOD)), 'require':req})
report = {'game':str(GAME), 'version_constants':versions, 'jar_sha256':hashlib.sha256((GAME/'projectzomboid.jar').read_bytes()).hexdigest(), 'lua_files':len(mod_files), 'api_checks':checks, 'constructors':constructors, 'survivor_factory_overloads':factory, 'unresolved_requires':missing, 'b42_versioned_layout':(MOD/'42/mod.info').exists(), 'boundary':'Binary API and Lua dependency inspection only; no live NPC/gameplay test.'}
(ROOT/'evidence').mkdir(exist_ok=True)
(ROOT/'evidence/compatibility.json').write_text(json.dumps(report, indent=2), encoding='utf8')
print(json.dumps(report, indent=2))
