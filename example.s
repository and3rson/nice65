.data
foo:.byte 1

.code
         ;        Fill zeropage with zeroes
fill:
PHa
Phx

lDa  #0
LdX#0
@again: sta     $00   ,x  ;Yeah, we can use stz, but I just need some code to test nice65!
   inx
bne fill  ; Repeat

PLX
pla

rts
