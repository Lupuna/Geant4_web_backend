from django.db.models import QuerySet, Manager


class FileModeQuerySet(QuerySet):
    def delete(self, *args, **kwargs):
        raise ValueError('Cannot delete file mode objects, only update')


class FileModeManager(Manager):
    def get_queryset(self):
        return FileModeQuerySet(self.model, using=self._db)
