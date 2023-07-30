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

@ridiculously_long_label_just_for_the_sake_of_it:PLX
pla

rts
