#!/usr/bin/python

import re
import pprint
import textwrap

def main():

    commands_str = ""
    qcommands_buf = open('ascii-protocol-quick-commands.html')\
                      .read()\
                      .replace('&#160;', ' ')
    commands = {}
    for m in  re.findall('<tr>(.*?)</tr>',qcommands_buf,re.MULTILINE|re.S):
        c = re.findall('<td>[\n\s]*(.*?)[\n\s]*</td>',m,re.MULTILINE|re.S)
        if not c: continue

        # Start parsing!

        # Key and Name 
        n = re.search('<a href="#(.*)">(.*)</a>',c[0])
        key = n.group(1)
        name = n.group(2)
        scope = c[1]

        param_str = c[2]\
                      .replace('\n','')\
                      .replace('<p>','')\
                      .replace('</p>','')
        param_opts = param_str.split('<br />')

        param_rack = []

        for param_opt in param_opts:
            params = param_opt.split(' ')

            param_optional = False
            param_keywords = None

            param_data = []

            for param in params:
                if not param: continue
                m = re.search('\[(.*?)\]',param)
                if m:
                    param_optional = True
                    param = m.group(1)

                m = re.search('\((.*?)\)',param)
                if m: param = m.group(1)

                m = re.search('(?:<i>(.*)</i>|<i>(.*)|(.*)</i>)',param)
                if m:
                    param_keywords = False
                    param = m.group(1) or m.group(2) or m.group(3)
                    param_name = param
                else:
                    param_keywords = param.split('|')
                    param_name = "_".join(param_keywords)

                
                param_rec = {
                    'param_name': param_name,
                    'param_optional': param_optional,
                    'param_keywords': param_keywords,
                }

                if param_rec:
                    param_data.append(param_rec)
            param_rack.append(param_data)

        param_list_strs = []
        param_list_documentation = ""
        for pr in param_rack:
            param_list = []
            for r in pr:
                s = r['param_name']
                if r['param_optional']:
                    s += '=None'
                param_list.append(s)
                param_str_documentatopn = ""
            param_list_strs.append(", ".join(param_list))

        returns = c[3]\
                      .replace('\n','')\
                      .replace('<p>','')\
                      .replace('</p>','')

        description = re.sub('<.*?>','',c[4])

        param_first = ' ' + param_list_strs[0] if param_list_strs else ''

        rec = {
            'key': key,
            'name': name,
            'scope': scope,
            'param_first': param_first,
            'param_list': "\n        ".join(param_list_strs),
            'parameters': param_opts,
            'returns': returns,
            'description': description
        }

        commands.setdefault(key,{})
        commands[key][param_str] = rec

        commands_str += '''
def {key}(self,{param_first}):
    """
    {description}

    Scope: {scope}
    Parameters: 
        {param_list}
    :returns: {returns}
    
    """
    return self.blocking_request("{name}",{param_first})
        '''.format(**rec)

    open('ascii-protocol-parsed.py','w').write("\n    ".join(commands_str.splitlines()))

    import pprint
    pprint.pprint(commands.keys())

main()
