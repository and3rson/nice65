.macro  ldax aa, bb     ; do stuff
        LDA aa
        LDX bb          ; load bb
.endmacro

.macro  pushall
        PHA
        PHX
        PHY
.endmacro

.data
foo:    .byte 1

.code
; Fill zeropage with zeroes
fill:
        pushall
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
