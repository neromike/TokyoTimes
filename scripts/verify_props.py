from pathlib import Path
import json
import sys
from pathlib import Path
# Ensure project root is on sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from scenes.scene_registry import SCENE_REGISTRY

props_path = Path('data/props')
print('Props discovery from data/props:')
for f in sorted(props_path.glob('*.json')):
    with open(f, 'r') as fh:
        cfg = json.load(fh)
    pid = cfg.get('prop_id') or f.stem
    scene = cfg.get('initial_scene')
    x = cfg.get('x')
    y = cfg.get('y')
    print(f'  - {pid}: scene={scene}, pos=({x},{y})')
    if scene and scene not in SCENE_REGISTRY:
        print(f'    ! Warning: scene "{scene}" not registered')

print('\nRegistered scenes:', list(SCENE_REGISTRY.keys()))
