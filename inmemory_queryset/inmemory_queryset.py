import operator
from copy import deepcopy

from django.core.exceptions import MultipleObjectsReturned
from django.db.models import QuerySet


def in_operator(field, values):
    return field in values


def not_in_operator(field, values):
    return field not in values


class InMemoryCache(object):
    """
    Mutable storage for results.
    This is needed for `InMemoryQuerySet.refresh()` to affect child instances
    """
    def __init__(self):
        self._result = None

    def reset(self):
        self._result = None

    def items(self, queryset: QuerySet):
        """
        Return result set. Fetch and cache results if needed
        """
        if self._result is None:
            self._result = list(queryset)
        return self._result


class InMemoryQuerySet(object):
    def __init__(self, queryset: QuerySet):
        self._queryset = queryset
        self._cached_results = InMemoryCache()
        self._filters = []

    def refresh(self):
        """
        Trigger refresh from database
        """
        self._queryset = self._queryset._clone()
        self._cached_results.reset()

    def __iter__(self):
        # Fetch from database and cache results if necessary
        for obj in self._cached_results.items(self._queryset):
            if not self._conditions_met(obj):
                continue
            yield obj

    def all(self):
        for obj in self.__iter__():
            yield obj

    def _conditions_met(self, obj):
        """
        Check that object matches all filters
        """
        matched = True
        for filter in self._filters:
            op, field_name, expected_value = filter
            if op(getattr(obj, field_name), expected_value) is False:
                matched = False
                break

        return matched

    def filter(self, **kwargs):
        return self._copy_with_filters(operator.eq, **kwargs)

    def exclude(self, **kwargs):
        return self._copy_with_filters(operator.ne, **kwargs)

    def get(self, **kwargs):
        """
        Similar to Django's `QuerySet.get()` method
        :return:
        """
        qs = self._copy_with_filters(operator.eq, **kwargs)
        items = list(qs.__iter__())
        num_found = len(items)
        if num_found == 1:
            return items[0]
        elif num_found > 1:
            raise MultipleObjectsReturned()
        raise self._queryset.model.DoesNotExist

    def _copy_with_filters(self, op, **kwargs):
        qs = InMemoryQuerySet(self._queryset)
        qs._cached_results = self._cached_results
        qs._filters = deepcopy(self._filters)
        for field, value in kwargs.items():
            # Support for "__in" suffix just like regular `QuerySet`
            if field.endswith("__in"):
                field = field[0:-4]
                # Use "in" operator for filters added by `.filter()` and "not in" for `.exclude()`
                _op = in_operator if op == operator.eq else not_in_operator
            else:
                _op = op

            qs._filters.append((_op, field, value))
        return qs

    def first(self):
        try:
            return list(self.__iter__())[0]
        except IndexError:
            return None

    def last(self):
        try:
            return list(self.__iter__())[-1]
        except IndexError:
            return None

    def count(self):
        return len(list(self.__iter__()))

    def exists(self):
        for _ in self.__iter__():
            # Break search when at least one item found and return result
            return True
        return False
