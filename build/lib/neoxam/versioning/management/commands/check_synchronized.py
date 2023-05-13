# -*- coding: utf-8 -*-
import os
import ftplib
import hashlib

from django.core.management.base import BaseCommand
from django.db.models.aggregates import Max

from neoxam.versioning.models import AdlObj


class Command(BaseCommand):
    help = 'Closes the specified poll for voting'

    def handle(self, *args, **options):
        data = AdlObj.objects.filter(
            revision__gte=0,
            version__in=(2006, 2009),
            local__in=('mag', 'bib', 'ent', 'msg', 'hlp', 'frm', 'agl', 'amg'),
        ).values('version', 'local', 'name', 'ext').annotate(revision=Max('revision'))

        cx = {
            2006: ftplib.FTP('10.215.39.17', 'gp2006ro', 'ntic2004'),
            2009: ftplib.FTP('10.215.39.17', 'gp2009ro', 'ntic2004'),
        }

        try:
            do = False
            # data = [{'ext': 'adl', 'revision': 90678, 'local': 'mag', 'version': 2009, 'name': 'newport.gesopc.valopc'}]
            count = 0
            for query in data:
                count += 1
                adl_obj = AdlObj.objects.get(**query)
                # if adl_obj.command_line_key == 'bib:bibconsultenstableresulbis.bib':
                #     do = True

                if do:
                    # Check if up to date for the Versioning
                    vms_date = adl_obj.get_date(cx[adl_obj.version])

                    if vms_date and adl_obj.vmsdate >= vms_date:
                        content = adl_obj.get_venus_content(cx[adl_obj.version])
                        checksum = hashlib.md5(content.encode('iso-8859-1')).hexdigest()
                        if checksum != adl_obj.checksum:

                            svn_path = os.path.join('/workspace/src/gp', adl_obj.get_svn_path())

                            if self.has_changed(svn_path, content):
                                # print(str(count) + " " + adl_obj.get_svn_path())
                                print('# %d' % count)
                                print(
                                    "committer -u omansion -a xxx -c /home/gp2006p/versioning/conf/versioning/gpd.cfg -s %d -k TECH -t desynchro -f desynchro -r VERSIONING-677 -l 20 -p %s" % (
                                        adl_obj.version, adl_obj.command_line_key))
                                with open(svn_path, 'w', encoding='iso-8859-1') as fd:
                                    fd.write(content)
                                    # print(checksum)
                                    # print(adl_obj.checksum)

        finally:
            for conn in cx.values():
                try:
                    conn.quit()
                except:
                    import traceback
                    traceback.print_exc()

    def has_changed(self, svn_path, content):
        with open(svn_path, encoding='iso-8859-1') as fd:
            return fd.read().replace('\n', '').replace('\r', '') != content.replace('\n', '').replace('\r', '')

    def is_foo(self, content):
        new_content = []
        for n, line in enumerate(content.split('\n')):
            if n % 2 == 1:
                if line != '':
                    return False
            else:
                new_content.append(line)
        return '\n'.join(new_content)
