import sys, traceback
sys.path.insert(0, 'c:/Users/wifik/Desktop/projects/larger-lab')
try:
    from oce.backend.oc2_gateway import OCGateway
    print('Import OK')
    gw = OCGateway()
    print('Gateway created:', gw.gateway_id)
except Exception as e:
    traceback.print_exc()