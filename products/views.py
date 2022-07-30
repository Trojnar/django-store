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
        phrase = self.request.GET.get("phrase", None)
        if phrase:
            queryset = self.search(phrase)
            context["search_result"] = queryset

        return context

    def search(self, phrase):
        # Dictionary with field names to search in and priority rate as keys and list
        # to store matches. Priority of search result display is sum of sum of matches
        # in fields. Sum in fields is multiplied by priority rate.
        fields = {("name", 1.0): [], ("producer", 1.2): []}

        for word in phrase.split():
            for key in fields.keys():
                fields[key].append(
                    Product.objects.all().filter(**{f"{key[0]}__icontains": word})
                )

        # Count match for each field, replace matches in fields dict to matches count.
        # Count is multiplied by priority rate.
        for key in fields.keys():
            temp_dict = {}
            result_l = list(chain.from_iterable(fields[key]))
            for result in result_l:
                temp_dict[result] = result_l.count(result) * key[1]
            fields[key] = temp_dict

        # Sum of counts for each object.
        result = {}
        for queryset in fields.values():
            for key, value in queryset.items():
                if key in result:
                    result[key] += value
                else:
                    result[key] = value

        # sorting dictionary by value
        sorted_tuples = sorted(result.items(), key=lambda item: item[1], reverse=True)
        sorted_dict = {k: v for k, v in sorted_tuples}

        return sorted_dict.keys()
