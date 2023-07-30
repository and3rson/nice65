#!/usr/bin/python3

from argparse import ArgumentParser

from lark import Lark, Token, Transformer, Discard

# NMOS 6502 Opcodes
# https://www.masswerk.at/6502/6502_instruction_set.html
# https://www.westerndesigncenter.com/wdc/documentation/w65c02s.pdf (page 21)
INSTRUCTIONS = [
    'adc', 'and', 'asl', 'bcc', 'bcs', 'beq', 'bit', 'bmi', 'bne', 'bpl',
    'brk', 'bvc', 'bvs', 'clc', 'cld', 'cli', 'clv', 'cmp', 'cpx', 'cpy',
    'dec', 'dex', 'dey', 'eor', 'inc', 'inx', 'iny', 'jmp', 'jsr', 'lda',
    'ldx', 'ldy', 'lsr', 'nop', 'ora', 'pha', 'php', 'pla', 'plp', 'rol',
    'ror', 'rti', 'rts', 'sbc', 'sec', 'sed', 'sei', 'sta', 'stx', 'sty',
    'tax', 'tay', 'tsx', 'txa', 'txs', 'tya'
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
    statement: asm_statement | control_command
    asm_statement: INSTR (_WS* OPERAND (_WS* "," _WS* OPERAND)?)?
    control_command: "." WORD _WS* /[^\n]+/?
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


def main(filename):
    grammar = Lark(definition)
    with open(filename, 'r') as fobj:
        tree = grammar.parse(fobj.read())
        # print(tree.pretty())

    tree = SpaceTransformer().transform(tree)
    # print(tree.pretty())

    for line in tree.children:
        s = ''
        for i, child in enumerate(line.children):
            if child.data == 'comment':
                padding = (24 - len(s)) if i > 0 else 0
                s += ' ' * padding + '; ' + (child.children[0] if child.children else '').strip()
            elif child.data == 'labeldef':
                s += child.children[0] + ':'
            elif child.data == 'statement':
                # print(child.children[0])
                if child.children[0].data == 'control_command':
                    s += ' ' * (8 - len(s)) + '.' + ' '.join(child.children[0].children)
                else:
                    s += ' ' * (8 - len(s)) + child.children[0].children[0]
                    if len(child.children[0].children) > 1:
                        s += ' ' + ', '.join(child.children[0].children[1:])
        print(s)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('filename', help='input file')
    args = parser.parse_args()
    main(**vars(args))
