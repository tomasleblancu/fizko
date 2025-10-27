from app.routers import calendar

routes = calendar.router.routes
print(f'Total routes in calendar router: {len(routes)}')

delete_routes = [r for r in routes if hasattr(r, 'methods') and 'DELETE' in r.methods]
print(f'\nDELETE routes: {len(delete_routes)}')
for r in delete_routes:
    print(f'  - {r.path} -> {r.name}')

post_routes = [r for r in routes if hasattr(r, 'methods') and 'POST' in r.methods]
print(f'\nPOST routes: {len(post_routes)}')
for r in post_routes:
    print(f'  - {r.path} -> {r.name}')

event_type_routes = [r for r in routes if 'event-types' in r.path]
print(f'\nRoutes with event-types: {len(event_type_routes)}')
for r in event_type_routes:
    methods = getattr(r, 'methods', ['NO_METHODS'])
    print(f'  - {r.path} -> {methods}')
