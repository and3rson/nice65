#!/usr/bin/python3

from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import os
import sys

from lark import Lark, Token, Transformer, Discard

# NMOS 6502 Opcodes
# https://www.masswerk.at/6502/6502_instruction_set.html
# https://www.westerndesigncenter.com/wdc/documentation/w65c02s.pdf (page 21)
INSTRUCTIONS = [
    'adc', 'and', 'asl', 'bcc', 'bcs', 'beq', 'bit', 'bmi', 'bne', 'bpl',
    'brk', 'bvc', 'bvs', 'clc', 'cld', 'cli', 'clv', 'cmp', 'cpx', 'cpy',
    'dec', 'dex', 'dey', 'eor', 'ina', 'inc', 'inx', 'iny', 'jmp', 'jsr',
    'lda', 'ldx', 'ldy', 'lsr', 'nop', 'ora', 'pha', 'php', 'pla', 'plp',
    'rol', 'ror', 'rti', 'rts', 'sbc', 'sec', 'sed', 'sei', 'sta', 'stx',
    'sty', 'tax', 'tay', 'tsx', 'txa', 'txs', 'tya',
]
# CMOS 65C02 Opcodes
# https://wilsonminesco.com/NMOS-CMOSdif/
# https://www.westerndesigncenter.com/wdc/documentation/w65c02s.pdf (page 21)
CMOS_INSTRUCTIONS = [
    'bbr0', 'bbr1', 'bbr2', 'bbr3', 'bbr4', 'bbr5', 'bbr6', 'bbr7',
    'bbs0', 'bbs1', 'bbs2', 'bbs3', 'bbs4', 'bbs5', 'bbs6', 'bbs7',
    'bra', 'phx', 'phy', 'plx', 'ply',
    'rmb0', 'rmb1', 'rmb2', 'rmb3', 'rmb4', 'rmb5', 'rmb6', 'rmb7',
    'smb0', 'smb1', 'smb2', 'smb3', 'smb4', 'smb5', 'smb6', 'smb7',
    'stp', 'stz', 'trb', 'tsb', 'wai',
]

instructions = INSTRUCTIONS + CMOS_INSTRUCTIONS

instructions_def = ' | '.join(['"' + instr + '"i' for instr in instructions])


definition = r'''
    %import common.NUMBER
    %import common.HEXDIGIT
    %import common.LETTER
    %import common.WORD
    %import common.WS_INLINE

    _WS: WS_INLINE

    start: line*
    line: _WS* labeldef? _WS* statement? _WS* comment? "\n"

    labeldef: LABEL ":"
    LABEL: "@"? (LETTER | "_")+ (LETTER | "_" | NUMBER)*
    statement: asm_statement | control_command | constant_def
    asm_statement: INSTR (_WS* OPERAND (_WS* "," _WS* OPERAND)?)?
    control_command: "." WORD _WS* /[^\n]+/?
    constant_def: LABEL _WS* "=" /[^\n]+/
    comment: ";" SENTENCE?
    SENTENCE: /[^\n]+/

    INSTR: ''' + instructions_def + r'''
    OPERAND: LITERAL | IMMEDIATE | REGISTER | LABEL

    LITERAL: NUMBER | "$" HEXDIGIT+ | /.+/
    IMMEDIATE: "#" LITERAL
    REGISTER: "A"i | "X"i | "Y"i
'''


class SpaceTransformer(Transformer):
    def WS(self, tok: Token):
        return Discard


grammar = Lark(definition)


def main(infile, outfile, modify_in_place, recursive):
    if recursive:
        for root, dirs, files in os.walk(infile):
            for file in files:
                if file.endswith('.' + recursive):
                    path = os.path.join(root, file)
                    print('Fixing', path)
                    main(path, None, True, False)
        return

    with open(infile, 'r') as fobj:
        content = fobj.read()
        if content.startswith('; nice65: ignore'):
            print('Ignoring', infile)
            return

        tree = grammar.parse(content)

    if modify_in_place:
        outfile = open(infile, 'w')
    elif outfile == '-':
        outfile = sys.stdout
    else:
        outfile = open(outfile, 'w')

    tree = SpaceTransformer().transform(tree)

    for line in tree.children:
        s = ''
        for i, child in enumerate(line.children):
            if child.data == 'comment':
                sentence = (child.children[0] if child.children else '').strip()
                padding = (24 - len(s)) if i > 0 else 0
                s += ' ' * padding + ('; ' + sentence).strip()
            elif child.data == 'labeldef':
                label = child.children[0].strip()
                if label.startswith('@'):
                    padding = ' ' * 4
                else:
                    padding = ''
                s += padding + label + ':'
            elif child.data == 'statement':
                pad_count = 8 - len(s)
                if pad_count > 0:
                    padding = ' ' * pad_count
                else:
                    padding = '\n' + ' ' * 8

                statement = child.children[0]

                if statement.data == 'control_command':
                    s += padding + '.' + ' '.join(statement.children)
                elif statement.data == 'asm_statement':
                    s += padding + statement.children[0].upper()
                    if len(statement.children) > 1:
                        s += ' ' + ', '.join(statement.children[1:])
                elif statement.data == 'constant_def':
                    s += padding + ' = '.join(map(str.strip, statement.children))
                else:
                    raise NotImplementedError('Unknown statement type: ' + child.children[0].data)
        print(s, file=outfile)

    outfile.close()


if __name__ == '__main__':
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('infile', help='Input file')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-o', '--outfile', metavar='outfile', help='Output file, defaults to "-" for stdout', default='-')
    group.add_argument('-m', '--modify-in-place', help='Use input file as output target', action='store_true')
    group.add_argument('-r', '--recursive', metavar='ext', help='Search subdirectories for all files by extension')
    args = parser.parse_args()
    main(**vars(args))
