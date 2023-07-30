#!/usr/bin/python3

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import os
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

instructions = INSTRUCTIONS + CMOS_INSTRUCTIONS

instructions_def = " | ".join(['"' + instr + '"i' for instr in instructions])


definition = (
    # fmt: off
    r"""
    %import common.NUMBER
    %import common.HEXDIGIT
    %import common.LETTER
    %import common.WORD
    %import common.WS_INLINE -> _WS
    %ignore _WS

    start: line*
    line: (labeldef statement | statement | labeldef)? comment? "\n"

    labeldef: LABEL ":"?
    LABEL: "@"? (LETTER | "_")+ (LETTER | "_" | NUMBER)*
    statement: asm_statement | control_command | constant_def
    asm_statement: INSTR (_WS+ operand ("," operand)?)?
    control_command: "." WORD (_WS+ /[^\n]+/)?
    constant_def: LABEL "=" /[^\n]+/
    comment: ";" SENTENCE?
    SENTENCE: /[^\n]+/

    INSTR: """ + instructions_def + r"""

    ?operand: REGISTER | (/#/? /[<>]/? expr)
    ?expr: LITERAL (OP expr)?
        | /\(/ expr /\)/ -> expr

    REGISTER: "A"i | "X"i | "Y"i
    LITERAL: NUMBER | /\$/ HEXDIGIT+ | /%/ /[01]+/ | LABEL | /'.'/ | /\*/
    OP: "+" | "-" | "*" | "/"
"""
    # fmt: on
)

grammar = Lark(definition)


def main(infile, outfile, modify_in_place, recursive):
    if recursive:
        for root, dirs, files in os.walk(infile):
            for file in files:
                if file.endswith("." + recursive):
                    path = os.path.join(root, file)
                    print("Fixing", path)
                    main(path, None, True, False)
        return

    with open(infile, "r") as fobj:
        content = fobj.read()
        if content.startswith("; nice65: ignore"):
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
        s = ""
        for i, child in enumerate(line.children):
            if child.data == "comment":
                sentence = (child.children[0] if child.children else "").strip()
                s_len = len(s)
                if '\n' in s:
                    s_len = s_len - s.rfind('\n') - 1
                padding = (24 - s_len) if i > 0 else 0
                s += " " * padding + ("; " + sentence).strip()
            elif child.data == "labeldef":
                label = child.children[0].strip()
                if label.startswith("@"):
                    padding = " " * 4
                else:
                    padding = ""
                s += padding + label + ":"
            elif child.data == "statement":
                pad_count = 8 - len(s)
                if pad_count > 0:
                    padding = " " * pad_count
                else:
                    padding = "\n" + " " * 8

                statement = child.children[0]

                if statement.data == "control_command":
                    s += padding + "." + " ".join(statement.children)
                elif statement.data == "asm_statement":
                    mnemonic = statement.children[0]
                    s += padding + mnemonic.upper()
                    operands = statement.children[1:]
                    if operands:
                        args = []
                        for operand in operands:
                            args.append(flatten_expr(operand))
                        s += " " + ", ".join(args)
                elif statement.data == "constant_def":
                    s += padding + " = ".join(map(str.strip, statement.children))
                else:
                    raise NotImplementedError(
                        "Unknown statement type: " + child.children[0].data
                    )
        print(s, file=outfile)

    outfile.close()


def flatten_expr(operand):
    parts = []
    if isinstance(operand, Token):
        parts.append(str(operand))
    else:
        for child in operand.children:
            parts.extend(flatten_expr(child))
    return "".join(parts)


if __name__ == "__main__":
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument("infile", help="Input file")
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
        metavar="ext",
        help="Search subdirectories for all files by extension",
    )
    args = parser.parse_args()
    main(**vars(args))
