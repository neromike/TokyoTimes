import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from ai.schedule import ScheduleController

class DummyNPC:
    npc_type = 'henry'
    def _get_feet_position(self):
        return (0, 0)
    path = []
    current_waypoint_idx = 0
    velocity_x = 0
    velocity_y = 0
    destination = None
    scene_path = None
    target_scene = None
    def pathfind_to(self, x, y):
        pass
    def pathfind_to_scene(self, scene, x, y):
        pass

class DummyGame:
    hour = 8
    minute = 0

if __name__ == '__main__':
    s = ScheduleController('henry.json', DummyNPC(), DummyGame())
    print('Loaded', len(s.actions), 'actions; first:', s.actions[0].action_type)
