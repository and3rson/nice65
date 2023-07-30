.data
foo:.byte 1
.code
         ;        Fill zeropage with zeroes
fill:
pha
phx

lda  #0
ldx#0
@again: sta     $00   ,x  ;Yeah, we can use stz, but I just need some code to test nice65!
   inx
bne fill  ; Repeat

plx
pla

rts
