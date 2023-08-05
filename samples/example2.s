; This example must be linted with "-l" option
  ; Waste some cycles
decr ldx #42
agn  dex
     bne agn ;repeat
     rts
