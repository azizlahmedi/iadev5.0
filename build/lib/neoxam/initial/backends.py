from neoxam.versioning import models
from neoxam.initial import consts
from neoxam.initial import models as init_models
from django.utils import timezone
from django.db.models import Max
from django.core.exceptions import ObjectDoesNotExist


class InitialCommitBackend:
    def populate_pool(self):

        max_revision = init_models.InitialCommitRecord.objects.all().aggregate(
            max_revision=Max('revision')).get('max_revision')

        if max_revision is None:
            max_revision = consts.STARTING_REVISION

        for adlobj in models.AdlObj.objects.filter(revision__gte=max_revision,
                                                   svndate__lte=timezone.now() - consts.FILTERING_THRESHOLD):
            init_models.InitialCommitRecord.objects.get_or_create(adlobj_id=adlobj.pk,
                                                                  defaults={'initial_commit': self.is_initial(adlobj),
                                                                            'version': adlobj.version,
                                                                            'svndate': adlobj.svndate,
                                                                            'user': adlobj.user,
                                                                            'revision': adlobj.revision,
                                                                            'svn_path': adlobj.get_svn_path()})

    def is_initial(self, adlobj):
        if models.AdlObj.objects.filter(revision__gt=0,
                                        svndate__lt=adlobj.svndate,
                                        version=adlobj.version,
                                        local=adlobj.local,
                                        name=adlobj.name,
                                        ext=adlobj.ext).exists():
            return False
        else:
            return True

    def get_initial_commits_without_update(self, version):
        return init_models.InitialCommitRecord.objects.filter(initial_commit=True,
                                                              version=version).order_by('-svndate')

    def get_initial_commits(self, version):
        self.populate_pool()
        return self.get_initial_commits_without_update(version)

    def sync(self):
        for record in init_models.InitialCommitRecord.objects.all():
            try:
                adlobj = models.AdlObj.objects.get(pk=record.adlobj_id)
            except ObjectDoesNotExist:
                record.delete()
            else:
                record.version = adlobj.version
                record.svndate = adlobj.svndate
                record.user = adlobj.user
                record.revision = adlobj.revision
                record.svn_path = adlobj.get_svn_path()
                record.save()


initialcommitbackend = InitialCommitBackend()
