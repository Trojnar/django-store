from django.views.generic import ListView, DetailView, TemplateView
from .models import Product

# from django.contrib.auth.mixins import PermissionRequiredMixin
from itertools import chain
from django.db.models import Q


class ProductListView(ListView):
    model = Product
    template_name = "product_list.html"


class ProductDetailsView(DetailView):
    model = Product
    template_name = "product_details.html"


class SearchResultView(TemplateView):
    template_name = "search_result.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        keyword = self.request.GET.get("keyword", None)
        if keyword:
            queryset = self.search(keyword)
            context["search_result"] = queryset

        return context

    def search(self, phrase):
        results = {"title_match": [], "producer_match": []}
        phrase = phrase.split(" ")
        for word in phrase:
            results["title_match"].append(
                Product.objects.all().filter(name__icontains=word)
            )
            results["producer_match"].append(
                Product.objects.all().filter(producer__icontains=word)
            )

        result_title = list(chain.from_iterable(results["title_match"]))
        result_producer = list(chain.from_iterable(results["producer_match"]))
        title_count_matches = {}
        for result in result_title:
            title_count_matches[result] = result_title.count(result)
        producer_count_matches = {}
        for result in result_producer:
            producer_count_matches[result] = result_producer.count(result)
        producer_discount = 1.2

        for key in producer_count_matches.keys():
            if key not in title_count_matches.keys():
                title_count_matches[key] = (
                    producer_discount * producer_count_matches[key]
                )
            else:
                title_count_matches[key] += (
                    producer_discount * producer_count_matches[key]
                )

        # sorting dictionary by
        sorted_tuples = sorted(
            title_count_matches.items(), key=lambda item: item[1], reverse=True
        )
        sorted_dict = {k: v for k, v in sorted_tuples}
        return sorted_dict.keys()
