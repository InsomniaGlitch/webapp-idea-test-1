from django.urls import reverse

from .forms import FilterForm


def attach_media_urls(items, preview_ids=None):
    preview_ids = preview_ids or set()
    for item in items:
        item.stream_url = reverse("audio_stream", args=[item.id])
        if item.id in preview_ids:
            item.stream_url += "?preview=1"
        item.image_url = reverse("image_stream", args=[item.id])


def build_filter_form(request, queryset):
    categories = sorted(queryset.values_list("category", flat=True).distinct())
    form = FilterForm(request.GET or None)
    form.fields["categories"].choices = [(category, category) for category in categories]

    selected_sort = request.GET.get("sort_by") or request.GET.get("active_sort") or ""
    if selected_sort:
        form.fields["sort_by"].initial = selected_sort

    if not request.GET.get("order"):
        form.fields["order"].initial = "asc"

    return form


def apply_filters(queryset, form):
    if not form.is_valid():
        return queryset

    sort_by = form.cleaned_data.get("sort_by")
    order = form.cleaned_data.get("order")
    categories = form.cleaned_data.get("categories")
    min_price = form.cleaned_data.get("min_price")
    max_price = form.cleaned_data.get("max_price")
    start_date = form.cleaned_data.get("start_date")
    end_date = form.cleaned_data.get("end_date")

    if categories:
        queryset = queryset.filter(category__in=categories)
    if min_price is not None:
        queryset = queryset.filter(price__gte=min_price)
    if max_price is not None:
        queryset = queryset.filter(price__lte=max_price)
    if start_date is not None:
        queryset = queryset.filter(publish_date__gte=start_date)
    if end_date is not None:
        queryset = queryset.filter(publish_date__lte=end_date)

    if sort_by:
        prefix = "" if order == "asc" else "-"
        queryset = queryset.order_by(prefix + sort_by)
    else:
        queryset = queryset.order_by("-publish_date")

    return queryset
