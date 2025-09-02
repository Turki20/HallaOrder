from django.urls import path
from . import views_sales, views_customers, views

app_name = "reports"

urlpatterns = [
    path("dashboard/",  views.dashboard_view,           name="dashboard"),
    path("customers/",  views_customers.customers_page, name="customers"),
    path("sales/",      views_sales.sales_view,         name="sales"),

    path("api/sales/summary/",   views_sales.api_sales_summary,   name="api_sales_summary"),
    path("api/sales/by-branch/", views_sales.api_sales_by_branch, name="api_sales_by_branch"),
    path("api/sales/by-type/",   views_sales.api_sales_by_type,   name="api_sales_by_type"),
    path("api/sales/list/",      views_sales.api_sales_list,      name="api_sales_list"),
    path("api/sales/export/",    views_sales.api_sales_export,    name="api_sales_export"),
    path("api/growth/reengage/",      views_sales.api_growth_reengage,      name="api_growth_reengage"),
    path("api/growth/top-customers/", views_sales.api_growth_top_customers,  name="api_growth_top_customers"),
    path("api/growth/bundles/",       views_sales.api_growth_bundles,        name="api_growth_bundles"),
    path("api/growth/best-times/",    views_sales.api_growth_best_times,     name="api_growth_best_times"),
    path("api/ai/promo/",                 views_sales.api_ai_promo,                 name="api_ai_promo"),
    path("api/marketing/whatsapp.csv",    views_sales.api_marketing_whatsapp_csv,   name="api_marketing_whatsapp_csv"),
    path("api/ds/rfm/",                   views_sales.api_ds_rfm,                   name="api_ds_rfm"),

    path("api/customers/",                 views_customers.customers_list,            name="api_customers_list"),
    path("api/customers/export/",          views_customers.customers_export_csv,      name="api_customers_export"),
    path("api/customers/bulk-tag/",        views_customers.customers_bulk_tag,        name="api_customers_bulk_tag"),
    path("api/customers/bulk-block/",      views_customers.customers_bulk_block,      name="api_customers_bulk_block"),
    path("api/customers/orders-preview/",  views_customers.customer_orders_preview,   name="api_customer_orders_preview"),

    path("api/customers/ai-tags/",         views_customers.customers_ai_tags,         name="api_customers_ai_tags"),
    path("api/customers/tags-apply-all/",  views_customers.customers_tags_apply_all,  name="api_customers_tags_apply_all"),
    path("api/customers/duplicates/",      views_customers.customers_find_duplicates, name="api_customers_duplicates"),
    path("api/customers/merge/",           views_customers.customers_merge,           name="api_customers_merge"),
]
