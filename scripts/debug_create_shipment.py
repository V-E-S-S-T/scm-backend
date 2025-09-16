from app.services.logistics_service import LogisticsService

svc = LogisticsService()
try:
    res = svc.create_shipment({'destination':'Mumbai','items_count':10,'weight':25.5})
    print('OK', res['id'])
except Exception as e:
    import traceback
    traceback.print_exc()
    print('Error:', e)
