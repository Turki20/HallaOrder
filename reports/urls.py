# reports/urls.py
from django.urls import path
from . import views_ai, views_customers
from . import views
app_name = "reports"

urlpatterns = [
    path("ai/",         views_ai.ai_view,               name="ai"),
    path("dashboard/",  views.dashboard_view,               name="dashboard"), 
    path("customers/",  views_customers.customers_page, name="customers"),
]

def _add_ai(route, view_attr, name_):
    v = getattr(views_ai, view_attr, None)
    if v:
        urlpatterns.append(path(route, v, name=name_))

_add_ai("api/insights/summary/",   "insights_summary",   "api_insights_summary")
_add_ai("api/reco/trending/",      "reco_trending",      "api_reco_trending")
_add_ai("api/reco/also-bought/",   "reco_also_bought",   "api_reco_also_bought")
_add_ai("api/products/search/",    "product_search",     "api_products_search")
_add_ai("api/reco/bundles/",       "reco_bundles",       "api_reco_bundles")
_add_ai("api/reco/top-customers/", "top_customers",      "api_top_customers")
_add_ai("api/heatmap/time/",       "heatmap_time",       "api_heatmap_time")
_add_ai("api/branches/compare/",   "branches_compare",   "api_branches_compare")
_add_ai("api/products/abc/",       "products_abc",       "api_products_abc")
_add_ai("api/simulate/discount/",  "simulate_discount",  "api_simulate_discount")

urlpatterns += [
    path("api/customers/",            views_customers.customers_list,       name="api_customers_list"),
    path("api/customers/bulk-tag/",   views_customers.customers_bulk_tag,   name="api_customers_bulk_tag"),
    path("api/customers/bulk-block/", views_customers.customers_bulk_block, name="api_customers_bulk_block"),
    path("api/customers/export/",     views_customers.customers_export_csv, name="api_customers_export"),
]
