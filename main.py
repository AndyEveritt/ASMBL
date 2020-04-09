from src.ASMBL_parser import Parser

import json
import argparse
import os


def arg_parser_json(arg):
    if arg is None:
        return arg
    if not os.path.exists(arg):
        raise argparse.ArgumentTypeError("The file %s does not exist!" % arg)
    else:
        return json.load(open(arg, 'r'))  # return a dict from the json


if __name__ == "__main__":

    arg_parser = argparse.ArgumentParser(description='ASMBL Code Creation Tool')
    arg_parser.add_argument('--config', '-C', type=arg_parser_json, default='config.json',
                            metavar='FILE', help='path to json config file')

    args = arg_parser.parse_args()

    asmbl_parser = Parser(args.config)
    asmbl_parser.create_output_file(asmbl_parser.merged_gcode_script)
    pass
