# -*- coding: utf-8 -*-
import logging
import os
import tempfile

import polib
import requests

from factory import consts

log = logging.getLogger(__name__)


class I18nBackend(object):
    def __init__(self, subversion_backend, subversion_url, legacy_mo_url, languages):
        self.subversion_backend = subversion_backend
        self.subversion_url = subversion_url.rstrip('/')
        self.legacy_mo_url = legacy_mo_url.rstrip('/')
        self.languages = languages

    def get_po_url(self, schema_version, procedure_name, lang):
        return self.subversion_url + '/gp{schema_version}/adl/src/mlg/{lang}/{procedure_basename}_{lang}.po'.format(
            schema_version=schema_version,
            procedure_basename=procedure_name.replace('.', '_'),
            lang=lang
        )

    def get_mo_url(self, schema_version, procedure_name, lang):
        return self.legacy_mo_url + '/{schema_version}/{lang}/{procedure_basename}_{lang}.mo'.format(
            schema_version=schema_version,
            procedure_basename=procedure_name.replace('.', '_'),
            lang=lang
        )

    def download_po(self, schema_version, procedure_name, lang, output_dir, revision):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        path = os.path.join(output_dir, '%s_%s.po' % (procedure_name.replace('.', '_'), lang))
        schema_versions = [schema_version, ]
        schema_versions.extend(consts.FALLBACK_SCHEMA_VERSIONS.get(schema_version, []))
        for schema_version in schema_versions:
            url = self.get_po_url(schema_version, procedure_name, lang)
            if self.subversion_backend.safe_export(url, path, revision=revision):
                return path

    def download_all_po(self, schema_version, procedure_name, output_dir, revision):
        log.info('download %d:%s .po', schema_version, procedure_name)
        paths = {}
        for lang in self.languages:
            path = self.download_po(schema_version, procedure_name, lang, os.path.join(output_dir, lang), revision=revision)
            if path:
                paths[lang] = path
        return paths

    def download_and_compile_all_po(self, schema_version, procedure_name, output_dir, revision):
        with tempfile.TemporaryDirectory() as temp:
            self.download_all_po(schema_version, procedure_name, temp, revision=revision)
            return self.compile_all_po(procedure_name, temp, output_dir)

    def download_legacy_mo(self, schema_version, procedure_name, lang, output_dir):
        # Destination path
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        mo_path = os.path.join(output_dir, '%s_%s.mo' % (procedure_name.replace('.', '_'), lang))
        # If ignore legacy MO, generate an empty MO
        if lang in consts.IGNORE_LEGACY_MO_FOR_LANGUAGES:
            polib.MOFile(encoding='utf-8').save(mo_path)
            return mo_path
        # Get schema versions where the mo can be found
        schema_versions = [schema_version]
        schema_versions.extend(consts.FALLBACK_SCHEMA_VERSIONS.get(schema_version, []))
        for schema_version in schema_versions:
            url = self.get_mo_url(schema_version, procedure_name, lang)
            response = requests.get(url, stream=True)
            if response.ok:
                with open(mo_path, 'wb') as fd:
                    for chunk in response.iter_content(chunk_size=128):
                        fd.write(chunk)
                return mo_path
        # Always generate a MO
        polib.MOFile(encoding='utf-8').save(mo_path)
        return mo_path

    def download_all_legacy_mo(self, schema_version, procedure_name, output_dir):
        log.info('download %d:%s legacy .mo', schema_version, procedure_name)
        all_mo = {}
        for lang in self.languages:
            mo_path = self.download_legacy_mo(schema_version, procedure_name, lang, os.path.join(output_dir, lang))
            if mo_path:
                all_mo[lang] = mo_path
        return all_mo

    def compile_all_po(self, procedure_name, input_dir, output_dir):
        log.info('compile %s .po', procedure_name)
        procedure_basename = procedure_name.replace('.', '_')
        all_mo = {}
        for lang in self.languages:
            output_dir_lang = os.path.join(output_dir, lang)
            if not os.path.exists(output_dir_lang):
                os.makedirs(output_dir_lang)
            mo_path = os.path.join(output_dir_lang, procedure_basename + '_' + lang + '.mo')
            po_path = os.path.join(input_dir, lang, procedure_basename + '_' + lang + '.po')
            if os.path.isfile(po_path):
                polib.pofile(po_path, encoding='utf-8').save_as_mofile(mo_path)
            else:
                # Create an empty MO to be able to get untranslated
                polib.MOFile(encoding='utf-8').save(mo_path)
            all_mo[lang] = polib.mofile(mo_path, encoding='utf-8')
        return all_mo
