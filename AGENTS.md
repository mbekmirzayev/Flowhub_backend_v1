# Flowhub Backend v1 — Agent Context

## Arxitektura
- Django + DRF, multi-tenant (TenantManager + LinkedTenantManager)
- 11 app: attendance, category, common, course, device, enrollment,
  history, notification, organization, payment, users
- Servis qatlami: `apps/<app>/services/` (lifecycle.py, writer.py)
- Tarix: immutable `History` modeli, 14 action type
- Auth: JWT + Device/UserSession, phone-based login

## API versiyasi: /api/v1/
## Asosiy papka: src/apps/ (models) va src/api/ (views/serializers/urls)