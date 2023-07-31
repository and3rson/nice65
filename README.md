# nice65
Code formatter for CC65 assembly (WIP).

Requirements:

- Python 3.x
- [Lark](https://github.com/lark-parser/lark)

Features:
- Makes ugly code less ugly
- Fixes indentation and letter cases (mnemonics, registers)
- Understands colon-less labels
- Tested with [C64 Kernal/Basic](https://github.com/mist64/c64rom) and [my 6502-based SBC ROM code](https://github.com/and3rson/deck65)

Not implemented yet:
- Macros (basic ones might work though).
- Proper formatting of arithmetic expressions
- Better indentation of comments based on deduced context

## Example usage

```sh
# Reformat and print to STDOUT
./nice65.py example.s

# Modify file in-place
./nice65.py example.s -m

# Write result to another file
./nice65.py example.s -o clean.s

# Recursively reformat all files in directory with extension ".s"
./nice65.py ./src/ -r s
```

## Using with NeoVim

Here's an example on how to have nice65 configured as code formatter for NeoVim with null-ls

1. Make sure you have the following neovim plugins installed:
    - `maxbane/vim-asm_ca65` - sets filetype for CA65 buffers
    - `jose-elias-alvarez/null-ls.nvim` - allows to run custom scripts as language servers

2. Add configuration:

    ```lua
    local null_ls = require("null-ls")
    null_ls.setup({
        on_attach = on_attach,              -- Use your on_attach function here
    })
    null_ls.register({
        method = null_ls.methods.FORMATTING,
        filetypes = { 'asm_ca65' },
        generator = null_ls.formatter({
            command = '/path/to/nice65.py', -- point at nice65.py in your filesystem
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
