# django-inmemory-queryset
QuerySet for Django ORM that fetches data once and allows to apply different filters later

## Installation
```python
pip install django-inmemory-queryset
```

## Usage
```python
from inmemory_queryset import InMemoryQuerySet

qs = InMemoryQuerySet(Mymodel.objects.all())
# To make lookups faster
qs.add_index("myfield_name")
...
filtered_objects = qs.filter(myfield_name="abc")  #  all records are fetched from database and indexes are built  
single_object = qs.get(myfield_name="cde")  # no queries to database, DoesNotExist exception can be raised
count = qs.filter(myfield_name="A").count()  # number of records that match the condition

```