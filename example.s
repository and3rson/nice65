; Fill zeropage with zeroes
fill:
pha
phx

lda  #0
ldx    #0
@again: sta     $00,     x
inx
bne fill  ; Repeat

plx
pla

rts
