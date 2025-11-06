# Implementation of the "Tak" function: https://dl.acm.org/doi/10.1145/1411829.1411833
#
# Based on one of BigEd's implementations here: https://www.stardot.org.uk/forums/viewtopic.php?t=31956
# but with the x<=y comparisons inlined at the recursion points, and the function arguments reversed
# to make it easier to return z.

_start:
    li    sp, $ff00

    li    a2, 15
    li    a1, 11
    li    a0, 7

    call  tak
    ebreak


tak:

    ; IF X%<=Y% =Z%
    bgt   a2, a1, tak2
    ret

tak2:
    .x = 2
    .y = 4
    .z = 6
    .a = 8
    .b = 10
    addi  sp, sp, -12
    sw    ra, (sp)
2:
    sw    a2, .x(sp)
    sw    a1, .y(sp)
    sw    a0, .z(sp)

    ; A% = FNT2( X%-1, Y%, Z%)
    addi  a2, a2, -1
    ble   a2, a1, 1f
    call  tak2
1:
    sw    a0, .a(sp)

    ; B% = FNT2( Y%-1, Z%, X%)
    lw    a2, .y(sp)
    lw    a1, .z(sp)
    lw    a0, .x(sp)
    addi  a2, a2, -1
    ble   a2, a1, 1f
    call  tak2
1:
    sw    a0, .b(sp)

    ; C% = FNT2( Z%-1, X%, Y%)
    lw    a2, .z(sp)
    lw    a1, .x(sp)
    lw    a0, .y(sp)
    addi  a2, a2, -1
    ble   a2, a1, 1f
    call  tak2
1:

    lw    a2, .a(sp)
    lw    a1, .b(sp)
    bgt   a2, a1, 2b

    lw    ra, (sp)
    addi  sp, sp, 12
    ret

