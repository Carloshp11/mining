from subprocess import Popen, PIPE
from typing import Tuple, Union, List


def join_dicts(*dicts: dict) -> dict:
    def join_dict_with_list(dict1: dict, ll: Tuple[dict]):
        return join_dict_with_list({**dict1, **ll[0]}, ll[1:]) if len(ll) > 0 else dict1

    assert len([k for dict_ in dicts for k in dict_.keys()]) == len(set([k for dict_ in dicts for k in dict_.keys()])), \
        'dicts have one or more duplicated keys. Join not possible'
    return join_dict_with_list(dicts[0], dicts[1:])


def execute_bash(args: Union[str, List[str]], continue_on_error: bool = False) -> Tuple:
    if isinstance(args, list):
        args = ' '.join(args)

    p = Popen(args, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)
    output, err = p.communicate(b"input data that is passed to subprocess' stdin")
    rc = p.returncode
    if not continue_on_error and rc != 0:
        raise Exception('execute_bash {} got the following error:'.format(args) + str(err))
    if args[0] == 'ls':
        output = str(output).split('\\n')
    return output, err, rc
