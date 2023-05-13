# -*- coding: utf-8 -*-
from django.db import models
from neoxam.adltrack import models as adl_models

class Record(models.Model):

    class Meta:
        unique_together = ('commit', 'from_version', 'to_version')
    commit = models.OneToOneField(adl_models.Commit, on_delete=models.CASCADE ,
                                  related_name='backport_record')    
    from_version = models.CharField(max_length=32)
    to_version = models.CharField(max_length=32)
    backported = models.BooleanField()
 
    def __str__(self):
        if self.backported:
            return '{}: {}, from {} to {}'.format(self.commit.revision,
                                                  'backported',
                                                  self.from_version,
                                                  self.to_version)
        else:
            return '{}: {}, from {} to {}'.format(self.commit.revision, 'not yet backported',
                                                  self.from_version,
                                                  self.to_version)            
