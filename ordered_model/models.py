from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db import models

def compact_order(manager):
    u"""Removes gaps between orders. [2,3,5,7] becomes: [0,1,2,3]."""

    last = -1
    for (pk, order) in manager.values_list('pk', 'order').order_by('order'):
        if order - last > 1:
            manager.filter(pk=pk).update(order=last + 1)
        last += 1

class OrderedModel(models.Model):
    """
    An abstract model that allows objects to be ordered relative to each other.
    Provides an ``order`` field.
    """
    
    order = models.PositiveIntegerField(editable=False)

    class Meta:
        abstract = True
        ordering = ('order',)
    
    def save(self, *args, **kwargs):
        if not self.id:
            qs = self.__class__.objects.order_by('-order')
            try:
                self.order = qs[0].order + 1
            except IndexError:
                self.order = 0
        super(OrderedModel, self).save(*args, **kwargs)
    
    def _move(self, up):
        manager = self.__class__._default_manager
        if up:
            qs = manager.order_by('-order').filter(order__lt=self.order)
        else:
            qs = manager.filter(order__gt=self.order)
        try:
            replacement = qs[0]
        except IndexError:
            # already first/last
            return

        # Save the re-ordered objects bypassing the save methods to not 
        # trigger save-signals, custom save methods  and other weirdnesses.
        manager.filter(pk=self.pk).update(order=replacement.order)
        manager.filter(pk=replacement.pk).update(order=self.order)

        compact_order(manager)

    def move_down(self):
        """
        Move this object down one position.
        """
        return self._move(up=False)
    
    def move_up(self):
        """
        Move this object up one position.
        """
        return self._move(up=True)
