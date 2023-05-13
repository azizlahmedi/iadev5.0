# -*- coding: utf-8 -*-
import delia_parser.deliaobject
import delia_tokenizer


class DeliaObject(delia_parser.deliaobject.DeliaObject):
    def listing_gen(self, skip_comment=False, skip_macro_comment=False, skip_include_comment=True):
        self.reset()
        return self.indent_gen(list(self.scan_all()), skip_comment, skip_macro_comment, skip_include_comment)

    def indent_gen(self, tokens_gen, skip_comment, skip_macro_comment, skip_include_comment):
        token_bbloc = [delia_tokenizer.BEGIN_TOKEN]
        token_ebloc = [delia_tokenizer.END]
        last_path_idx = -1
        last_lineno = 0
        indent_level = 0
        ret = ""

        for token_infos in tokens_gen:
            token = delia_tokenizer.get_token(*token_infos)
            type = delia_tokenizer.get_type(*token_infos)
            path_idx = delia_tokenizer.get_path(*token_infos)
            lineno = delia_tokenizer.get_lineno(*token_infos)

            if type in (delia_tokenizer.MACRO_SUB_IN, delia_tokenizer.MACRO_SUB_OUT):
                continue

            if type == delia_tokenizer.MACRO:
                if not skip_macro_comment:
                    yield "%%***** MACRO %s *****%%" % token
                indent_level += 1
                continue

            if type == delia_tokenizer.END_MACRO:
                if not skip_macro_comment:
                    yield "%%***** END.MACRO %s *****%%" % token
                indent_level -= 1
                continue

            if type == delia_tokenizer.INCLUDE_TOKEN:
                for token_infos in tokens_gen:
                    type = delia_tokenizer.get_type(*token_infos)
                    if type == delia_tokenizer.comment:
                        continue
                    else:
                        break
                for token_infos in tokens_gen:
                    type = delia_tokenizer.get_type(*token_infos)
                    if type == delia_tokenizer.comment:
                        continue
                    else:
                        break
                continue

            if type == delia_tokenizer.comment and skip_comment:
                continue

            if type in token_ebloc:
                indent_level -= 1

            if last_path_idx != path_idx:
                if not skip_include_comment:
                    if last_path_idx < path_idx:
                        yield "!***** to enter %s *****" % self.files[path_idx]
                    else:
                        yield "!***** to leave %s *****" % self.files[last_path_idx]
                last_path_idx = path_idx
                last_lineno = 0

            if last_lineno != lineno:
                last_lineno = lineno
                if ret != "" and not ret.isspace():
                    yield ret
                ret = "\t" * indent_level + token
            else:
                if type == delia_tokenizer.COLON:
                    ret += token
                else:
                    ret += " " + token

            if type in token_bbloc:
                indent_level += 1

        if ret != "" and not ret.isspace():
            yield ret


class Procedure(DeliaObject):
    pass


class Schema(DeliaObject):
    pass
