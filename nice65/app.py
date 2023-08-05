#!/usr/bin/python3

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, Action
import fnmatch

try:
    import importlib_metadata as metadata
except ImportError:
    from importlib import metadata
import os
import re
import sys

from lark import Lark, Token, Transformer, Discard

# NMOS 6502 Opcodes
# https://www.masswerk.at/6502/6502_instruction_set.html
# https://www.westerndesigncenter.com/wdc/documentation/w65c02s.pdf (page 21)
INSTRUCTIONS = [
    # fmt: off
    'adc', 'and', 'asl', 'bcc', 'bcs', 'beq', 'bit', 'bmi', 'bne', 'bpl',
    'brk', 'bvc', 'bvs', 'clc', 'cld', 'cli', 'clv', 'cmp', 'cpx', 'cpy',
    'dec', 'dex', 'dey', 'eor', 'ina', 'inc', 'inx', 'iny', 'jmp', 'jsr',
    'lda', 'ldx', 'ldy', 'lsr', 'nop', 'ora', 'pha', 'php', 'pla', 'plp',
    'rol', 'ror', 'rti', 'rts', 'sbc', 'sec', 'sed', 'sei', 'sta', 'stx',
    'sty', 'tax', 'tay', 'tsx', 'txa', 'txs', 'tya',
    # fmt: on
]
# CMOS 65C02 Opcodes
# https://wilsonminesco.com/NMOS-CMOSdif/
# https://www.westerndesigncenter.com/wdc/documentation/w65c02s.pdf (page 21)
CMOS_INSTRUCTIONS = [
    # fmt: off
    'bbr0', 'bbr1', 'bbr2', 'bbr3', 'bbr4', 'bbr5', 'bbr6', 'bbr7',
    'bbs0', 'bbs1', 'bbs2', 'bbs3', 'bbs4', 'bbs5', 'bbs6', 'bbs7',
    'bra', 'phx', 'phy', 'plx', 'ply',
    'rmb0', 'rmb1', 'rmb2', 'rmb3', 'rmb4', 'rmb5', 'rmb6', 'rmb7',
    'smb0', 'smb1', 'smb2', 'smb3', 'smb4', 'smb5', 'smb6', 'smb7',
    'stp', 'stz', 'trb', 'tsb', 'wai',
    # fmt: on
]

COL1_COMMANDS = {'segment', 'zeropage', 'data', 'code', 'bss', 'include', 'import', 'importzp', 'export', 'exportzp'}

instructions = INSTRUCTIONS + CMOS_INSTRUCTIONS

instructions_def = " | ".join(['"' + instr + '"i' for instr in instructions])


def main():
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("infile", help='Input file, pass "-" to read from for stdin')
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-o",
        "--outfile",
        metavar="outfile",
        help='Output file, defaults to "-" for stdout',
        default="-",
    )
    group.add_argument(
        "-m",
        "--modify-in-place",
        help="Use input file as output target",
        action="store_true",
    )
    group.add_argument(
        "-r",
        "--recursive",
        help="Recursively fix all files",
        action="store_true",
    )
    parser.add_argument(
        "-p",
        "--pattern",
        help="Match file names by Unix shell-style wildcard when used with -r",
        default='*.s',
    )
    parser.add_argument(
        "-l",
        "--colonless-labels",
        help="Allow labels without a colon (this option breaks macros, use with legacy code only)",
        action="store_true",
    )
    parser.add_argument(
        "-v",
        "--version",
        help="Show version",
        nargs=0,
        action=Version,
    )
    args = parser.parse_args()

    definition = (
        # fmt: off
        r"""
        %import common.NUMBER
        %import common.HEXDIGIT
        %import common.LETTER
        %import common.WS_INLINE -> _WS
        %ignore _WS

        start: line*
        line: (labeldef statement | statement | labeldef | numeric_var | constant_def)? comment? "\n"

        labeldef: LABEL ":" """ + ('?' if args.colonless_labels else '') + r""" | ":"

        statement: asm_statement | macro_start | macro_end | control_command
        asm_statement: INSTR (_WS+ operand ("," operand)?)?
        macro_start: ".macro" IDENT (IDENT ("," IDENT)*)?
        macro_end: ".endmacro"
        control_command: "." IDENT (_WS+ /[^\n]+/)?
        constant_def: LABEL /=|:=/ /[^\n]+/
        numeric_var: IDENT control_command

        comment: INDENT* ";" SENTENCE?

        ?operand: REGISTER | (/#/? /[<>]/? expr)
        ?expr: LITERAL (OP expr)?
            | /\(/ expr /\)/ -> expr

        SENTENCE: /[^\n]+/
        INSTR: """ + (instructions_def if args.colonless_labels else 'IDENT') + r"""
        REGISTER: "A"i | "X"i | "Y"i
        LITERAL: NUMBER | /\$/ HEXDIGIT+ | /%/ /[01]+/ | LABEL | LABEL_REL | /'.'/ | /\*/
        LABEL: "@"? IDENT
        IDENT: /[a-zA-Z_][a-zA-Z0-9_]*/
        LABEL_REL: /:[\+\-]+/
        OP: "+" | "-" | "*" | "/" | "|" | "^" | "&"
        INDENT: /[ ]+/
    """
        # fmt: on
    )

    grammar = Lark(definition)

    if args.recursive:
        for root, _, files in os.walk(args.infile):
            for file in files:
                if fnmatch.fnmatch(file, args.pattern):
                    path = os.path.join(root, file)
                    print("Fixing", path, file=sys.stderr)
                    fix(grammar, path, None, True, args.colonless_labels)
    else:
        fix(
            grammar,
            args.infile,
            args.outfile,
            args.modify_in_place,
            args.colonless_labels,
        )


class Version(Action):
    def __call__(self, parser, namespace, values, option_string):
        print('nice65 version', metadata.version("nice65"), file=sys.stderr)
        parser.exit()


def fix(grammar, infile, outfile, modify_in_place, colonless_labels):
    if infile == "-":
        content = sys.stdin.read()
    else:
        with open(infile, "r") as fobj:
            content = fobj.read()
            options_match = re.findall(r'^[ \t]*;\s*nice65:([^\n]+)$', content, re.MULTILINE)
            if options_match:
                options_str = options_match[0].lower().replace(',', ' ')
                options = set(filter(None, map(str.strip, options_str.split(' '))))
                if 'ignore' in options:
                    print("Ignoring", infile)
                    return

    tree = grammar.parse(content)

    if modify_in_place:
        outfile = open(infile, "w")
    elif outfile == "-":
        outfile = sys.stdout
    else:
        outfile = open(outfile, "w")

    for line in tree.children:
        string = ""
        for i, child in enumerate(line.children):
            if child.data == "comment":
                is_tail = bool(len(string))
                if is_tail:
                    sentence = next(iter([x for x in child.children if x.type == "SENTENCE"]), "").strip()
                    s_len = len(string)
                    if '\n' in string:
                        s_len = s_len - string.rfind('\n') - 1
                    padding = (24 - s_len) if i > 0 else 0
                    string += " " * padding + ("; " + sentence).strip()
                else:
                    sentence = next(iter([x for x in child.children if x.type == "SENTENCE"]), "").strip()
                    indent = str(next(iter([x for x in child.children if x.type == "INDENT"]), ""))
                    if indent:
                        padding = ' ' * 8
                    else:
                        padding = ''
                    string += padding + '; ' + sentence
            elif child.data == "labeldef":
                if child.children:
                    # Named label definition
                    label = child.children[0].strip()
                else:
                    # Unnamed label
                    label = ''

                if label.startswith("@") or not label:
                    padding = " " * 4
                else:
                    padding = ""
                string += padding + label + ":"
            elif child.data == "statement":
                pad_count = 8 - len(string)
                if pad_count > 0:
                    padding = " " * pad_count
                else:
                    padding = "\n" + " " * 8

                statement = child.children[0]

                if statement.data == "control_command":
                    name = statement.children[0].strip()
                    string += (
                        (padding if name not in COL1_COMMANDS else '')
                        + "."
                        + name.lower()
                        + " "
                        + " ".join(statement.children[1:])
                    )
                elif statement.data == "macro_start":
                    name = statement.children[0].strip()
                    string += ".macro ".ljust(8, ' ') + name + " " + ", ".join(map(str.strip, statement.children[1:]))
                elif statement.data == "macro_end":
                    string += ".endmacro"
                elif statement.data == "asm_statement":
                    mnemonic = statement.children[0]
                    string += padding + (mnemonic.upper() if mnemonic.lower() in instructions else mnemonic)
                    operands = statement.children[1:]
                    if operands:
                        args = []
                        for operand in operands:
                            args.append(flatten_expr(operand))
                        string += " " + ", ".join(args)
                else:
                    raise NotImplementedError("Unknown statement type: " + child.children[0].data)
            elif child.data == "numeric_var":
                name, cmd = child.children
                string = name.strip().ljust(8, ' ') + '.' + ' '.join(map(str.strip, cmd.children))
            elif child.data == "constant_def":
                name, assign, value = child.children
                string += name.strip() + " " + assign.strip() + " " + value.strip()
            else:
                raise NotImplementedError("Unknown child in line: " + child.data)
        print(string.rstrip(), file=outfile)

    outfile.close()


def flatten_expr(operand):
    parts = []
    if isinstance(operand, Token):
        string = str(operand)
        if operand.type == 'REGISTER':
            string = string.upper()
        parts.append(string)
    else:
        for child in operand.children:
            parts.extend(flatten_expr(child))
    return "".join(parts)


if __name__ == "__main__":
    main()
