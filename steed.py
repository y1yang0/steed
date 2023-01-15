# Copyright (c) 2023 Yi Yang <kelthuzadx@qq.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>
import re
import string

t = """
(def hello-world ()
 (- (* 2 5) 5)
 (+ 3 3)
)
(+ 1 23)
(hello-world)
"""

TheBuiltin = [
    {'name': "format", 'param': ['a', 'b'], 'body': None}
]


def log_trace(a, b):
    print(f"== Evaluate S-expression {a} that produces {b}({type(b)})")


def make_sexpr(text):
    """
    convert source code to s-expressions and make s-expressions to python
    objects to facilitate further use

    :param text: source code
    :return: s-expression list
    """
    text = text.replace('\n', '')

    def unit(idx):
        def accept_if(i, cond):
            s = text[i]
            while i + 1 < len(text):
                i += 1
                ch = text[i]
                if cond(ch):
                    s += text[i]
                else:
                    break
            return s, i

        if text[idx].isalpha():
            # identifiers
            return accept_if(idx, lambda c: ('a' <= c <= 'z') or ('A' <= c <= 'Z') or c == '-')
        if text[idx] in '()+*/%\'':
            # operators
            return text[idx], i + 1
        elif text[idx] == '\"':
            # string
            end = text.index('\"', idx + 1)
            return text[idx:end + 1], end + 1
        elif text[idx].isnumeric() or text[idx] == '-':
            # minus(-) operator
            if text[idx] == '-':
                if idx + 1 < len(text) and (not text[idx + 1].isnumeric()):
                    return "-", idx + 1
            # 3.14, -3
            return accept_if(idx, lambda c: c.isnumeric() or c == '.')
        elif text[idx] == ' ':
            return " ", idx + 1
        return "Invalid-" + text[idx], idx + 1

    i = 0
    sexprs = []
    while i < len(text):
        lexeme, ni = unit(i)
        i = ni
        if lexeme != ' ':
            sexprs.append(lexeme)
    invalid = [item.replace('Invalid-', '') for item in sexprs if 'Invalid-' in item]
    if len(invalid) > 0:
        print("SyntaxError: Found invalid content " + str(invalid))
        exit(-1)

    # i.e. ['(', '+', '1', '2', ')'] =-> [['+', '1', '2']]
    def to_py_list(i):
        if sexprs[i] != '(':
            raise ValueError("Must start with (")
        sub = []
        k = i + 1
        while k < len(sexprs):
            if sexprs[k] == '(':
                to_py_list(k)
            if sexprs[k] != ')':
                sub.append(sexprs[k])
            else:
                break
            k += 1
        if sexprs[k] != ')':
            raise ValueError("Must close with )")
        # delete elements i range of [), so we can replace these elements with sub
        del sexprs[i:k]
        sexprs[i] = sub

    # process top-level s-expressions
    i = 0
    while i < len(sexprs):
        if sexprs[i] == '(':
            to_py_list(i)
        i += 1
    return sexprs


def eval_sexpr(ctx, sexprs):
    if type(sexprs) is not list:
        val = eval(sexprs)
        # log_trace(sexprs, val)
        return val

    if len(sexprs) == 0:
        log_trace(sexprs, None)
        return None

    action = sexprs[0]
    if action in '+-*/%':
        # arithmetic
        code = f"{eval_sexpr(ctx, sexprs[1])}{action}{eval_sexpr(ctx, sexprs[2])}"
        val = eval(code)
        log_trace(sexprs, val)
        return val
    elif action == 'quote' or action == '\'':
        # quote
        log_trace(sexprs, sexprs)
        return sexprs
    elif action == 'def':
        # function definition
        func = {'name': sexprs[1], 'param': sexprs[2], 'body': sexprs[3:]}
        ctx['func'].append(func)
        log_trace(sexprs, func)
        return func
    else:
        # general identifier, either a use of var or function call
        for v in ctx['var']:
            if v['name'] == action:
                log_trace(sexprs, v['value'])
                return v['value']

        for f in ctx['func']:
            if f['name'] == action:
                ctx['var'].append({"name": f['param'], "value": None})
                body = f['body']
                ret_val = None
                for i in range(len(body)):
                    v = eval_sexpr(ctx, body[i])
                    if i == len(body) - 1:
                        ret_val = v
                log_trace(sexprs, ret_val)
                return ret_val

    raise ValueError("Should not reach here")


if __name__ == '__main__':
    sexprs = make_sexpr(t)
    ctx = {"func": [], "var": []}
    for i in sexprs:
        val = eval_sexpr(ctx, i)
