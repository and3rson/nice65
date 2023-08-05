; This example must be linted with "-l" option
; Waste some cycles
decr:   LDX #42
agn:    DEX
        BNE agn         ; repeat
        RTS
