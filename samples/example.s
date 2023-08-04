.macro foobar aa, bb, cc
lda aa
ldx bb
ldy cc
.endmacro

.data
foo:.byte 1

.code
         ;        Fill zeropage with zeroes
fill:
PHa
Phx

lDa  #0
LdX #0
@again: sta     $00   ,x  ;Yeah, we can use stz, but I just need some code to test nice65!
   inx
bne fill  ; Repeat

; Do unnecessary throwaway stuff to test expressions
lda #<($42  +  %10101010- (foo*2))
cmp foo+2
jmp :+
: lda $1234

@ridiculously_long_label_just_for_the_sake_of_it:PLX
pla

rts
