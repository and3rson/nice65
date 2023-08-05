; This example must be linted with "-l" option
; Waste some cycles
decr:   LDX #42
        ; loop
agn:    DEX
        BNE agn         ; repeat
        RTS
