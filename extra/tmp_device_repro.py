import os
import sys
import traceback
from pathlib import Path

os.environ['QT_QPA_PLATFORM'] = 'offscreen'
wd = Path.cwd()
sys.path.insert(0, str(wd))

from ui import BrahmaUI
from brahma_connect.service import get_service

try:
    ui = BrahmaUI(str(wd / 'assets' / 'Brahma_Lite_Logo.png'), show_immediately=False)
    svc = get_service(wd)
    ui.set_brahma_connect_service(svc)
    dp = ui._win._devices_page
    print('device page created')
    print('wizard idx before', dp._wizard_stack.currentIndex())
    print('service obj ok', dp._service_obj() is svc)

    try:
        dp._cinema_select_android()
        print('selected android, wizard idx', dp._wizard_stack.currentIndex())
    except Exception:
        traceback.print_exc()

    try:
        dp._refresh_onboarding_offer()
        print('refreshed offer', dp._onb_code_lbl.text(), dp._onb_status_lbl.text())
    except Exception:
        traceback.print_exc()

    try:
        dm = svc.gateway.device_manager
        record, secret = dm.create_from_pairing(name='Test Device', platform='android', capabilities=['media'])
        dm.touch(record.device_id)
        print('created device', record.device_id)
    except Exception:
        traceback.print_exc()

    try:
        dp._tick_onboarding()
        print('tick_onboarding completed')
    except Exception:
        traceback.print_exc()

    try:
        dp._trigger_onboarding_success()
        print('trigger_onboarding_success completed')
    except Exception:
        traceback.print_exc()

    try:
        dp.refresh(force=True)
        print('refresh completed')
    except Exception:
        traceback.print_exc()

except Exception:
    traceback.print_exc()
