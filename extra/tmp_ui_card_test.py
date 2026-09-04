import sys
from pathlib import Path
cwd = Path.cwd()
sys.path.insert(0, str(cwd))
from ui import BrahmaUI
from brahma_connect.service import get_service
ui = BrahmaUI(str(cwd / 'assets' / 'Brahma_Lite_Logo.png'), show_immediately=False)
svc = get_service(cwd)
ui.set_brahma_connect_service(svc)
dp = ui._win._devices_page
print('trigger add device')
dp._trigger_add_device()
print('wizard index', dp._wizard_stack.currentIndex())
dp._cinema_select_android()
print('selected index', dp._wizard_stack.currentIndex())
print('known ids before', dp._onboarding_known_device_ids)
record, secret = svc.gateway.device_manager.create_from_pairing(name='Test Device', platform='android', capabilities=['media'])
svc.gateway.device_manager.touch(record.device_id)
print('created', record.device_id)
try:
    dp._tick_onboarding()
    print('tick ok', dp._wizard_stack.currentIndex(), dp._onb_success_name.text())
except Exception as e:
    print('tick failed', e)
try:
    dp.refresh(force=True)
    print('refresh ok card count', len(dp._cards))
    if dp._cards:
        dp._on_device_selected(str(dp._cards[0].device.get('id')))
        print('selected card id after', dp._selected_device_id)
        print('action visible', dp._cards[0]._action_container.isVisible())
except Exception as e:
    print('refresh/select failed', e)
