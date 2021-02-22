; Simple G-code containing 2 layers, rel/abs positioning mode, print and travel moves.

M104 S210 ; Set temperature to 210*C

G28 ; Home
G1 Z10.0
G1 X100 Y100 ; Move away from build plate corner
G0 Z0.2 ; Move to first layer height

G91 ; Set relative positioning
M83
; LAYER 1
G1 Y10 E0.025
G1 X20 E0.025
G1 Y-10 E0.025
G1 X-20 E0.025
G3 X10 Y10 I105 J105 E0.025

G90 ; Set absolute positioning
G0 X100 Y100 Z0.4 ; Move to seconds layer height

; LAYER 2

G1 Y110 E0.025
G1 X120 E0.025
G1 Y100 E0.025
G1 X100 E0.025

M104 S0 ; Disable hotend
