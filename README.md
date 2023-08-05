# nice65
Code formatter for CC65 assembly (WIP).

Requirements:

- Python 3.x
- [Lark](https://github.com/lark-parser/lark)

Features:
- Makes ugly code less ugly
- Fixes indentation and letter cases (mnemonics, registers)
- Understands weird labels, such as colon-less (C64 style) and unnamed (`:`, `:+++`)
- Support for basic macros
- Skip files with `; nice65: ignore` comment
- Tested with [C64 Kernal/Basic](https://github.com/mist64/c64rom) and [my 6502-based SBC ROM code](https://github.com/and3rson/deck65)

Not implemented yet:
- Complex macros
- Proper formatting of arithmetic expressions
- Better indentation of comments based on deduced context

Notes:
- Colon-less label mode (`-l`) breaks macros due to [ambiguity of the syntax](https://github.com/cc65/cc65/discussions/2158#discussioncomment-6644905). Use this option only with legacy code that contains no macros (such as C64 source code).

# Installation

```sh
pip install nice65
```

## Example usage

```sh
# Reformat and print to STDOUT
nice65 samples/example.s

# Modify file in-place
nice65 samples/example.s -m

# Write result to another file
nice65 samples/example.s -o samples/clean.s
# or
nice65 samples/example.s > samples/clean.s

# Recursively reformat all files in directory with extension ".s"
nice65 ./samples/ -r

# Recursively reformat all files in directory with extension ".asm"
nice65 ./samples/ -r -p '*.asm'
```

Before:
```asm
.macro ldax aa, bb ; do stuff
lda aa
ldx bb ; load bb
.endmacro

.macro push_all
    phA
    phX
    PHy
.endmacro

.data
foo:.byte 1

.code
         ;        Fill zeropage with zeroes
fill:
push_all
start: ldax #0, #0
@again: sta     $00   ,x  ;Yeah, we can use stz, but I just need some code to test nice65!
   inx
bne @again  ; Repeat

; Do unnecessary throwaway stuff to test expressions
lda #<($42  +  %10101010- (foo*2))
cmp foo+2
jmp :+
: lda $1234

@ridiculously_long_label_just_for_the_sake_of_it:PLX
pla

end:rts
```

After:
```asm
.macro  ldax aa, bb     ; do stuff
        LDA aa
        LDX bb          ; load bb
.endmacro

.macro  push_all
        PHA
        PHX
        PHY
.endmacro

.data
foo:    .byte 1

.code
; Fill zeropage with zeroes
fill:
        push_all
start:  ldax #0, #0
    @again:
        STA $00, X      ; Yeah, we can use stz, but I just need some code to test nice65!
        INX
        BNE @again      ; Repeat

; Do unnecessary throwaway stuff to test expressions
        LDA #<($42+%10101010-(foo*2))
        CMP foo+2
        JMP :+
    :   LDA $1234

    @ridiculously_long_label_just_for_the_sake_of_it:
        PLX
        PLA

end:    RTS
```


## Using with Vim

```vim
:nnoremap <M-r> :%! nice65 -<CR>
```

## Using with NeoVim

If you want to be fancy, here's an example on how to have nice65 configured as code formatter for NeoVim with null-ls:

1. Make sure you have the following neovim plugins installed:
    - `maxbane/vim-asm_ca65` - sets filetype for CA65 buffers
    - `jose-elias-alvarez/null-ls.nvim` - allows to run custom scripts as language servers

2. Add configuration:

    ```lua
    local null_ls = require("null-ls")
    null_ls.setup({
        on_attach = on_attach, -- Remove this line if you don't use on_attach
    })
    null_ls.register({
        method = null_ls.methods.FORMATTING,
        filetypes = { 'asm_ca65' },
        generator = null_ls.formatter({
            command = 'nice65',
            args = {'-'},
            to_stdin = true,
            from_stdout = true,
        }),
    })
    ```

3. Trigger the formatting:

    ```vim
    :lua vim.lsp.buf.format()
    ```
