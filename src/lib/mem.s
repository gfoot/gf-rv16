# Memory allocation routines
#
# The heap starts at _top, rounded up to the next multiple of 8 bytes.  The block header is 8 bytes and all
# allocations are rounded up to the next multiple of 8 as well.
#
# The heap management structure is:
#
#    heapdata + 0    firstfree    pointer to 'first' free block (start of list, not first in memory)
#    heapdata + 2    first        pointer to first block
#
# Each block consists of a header and a footer, surrounding an area of memory.
#
#    header + 0    prev         pointer to previous block in memory
#    header + 2    nextfree     pointer to next free block
#    header + 4    prevfree     pointer to previous free block
#    header + 6    blocksize    block size not including header
#
# If a block is allocated, nextfree and prevfree will both be null.  They will also both be null if this
# is the only free block.  The first and last blocks in the free list will also have corresponding next/prev
# pointers set to null.
#
# blocksize is the size of the block, not the size that was requested.  The next neighbouring block in memory 
# is located at relative offset blocksize + sizeof(alloc_header).  The previous block is found through the 
# prev pointer.


alloc_heapdata = (_top+7) & ~7

alloc_heapdata_firstfree = 0
alloc_heapdata_first = 2
alloc_heapdata__size = 4


alloc_header_prev = 0
alloc_header_nextfree = 2
alloc_header_prevfree = 4
alloc_header_blocksize = 6
alloc_header__size = 8


alloc_init:
	# a0 = total heap size to use

	la		a1, alloc_heapdata                  # a1 = heapdata pointer

	addi	a2, a1, (alloc_heapdata__size+7) & ~7 # a2 = block header pointer
	sw		a2, alloc_heapdata_first(a1)
	sw		a2, alloc_heapdata_firstfree(a1)

	li		t0, 0                               # Initialise header fields - most are 0
	sw		t0, alloc_header_prev(a2)
	sw		t0, alloc_header_nextfree(a2)
	sw		t0, alloc_header_prevfree(a2)

	add		t0, a1, a0                          # Calculate size of block
	sub		t0, t0, a2
	addi	t0, t0, -alloc_header__size         # Subtract the size of the block's own header
	addi	t0, t0, -alloc_header__size         # Subtract the size of the sentinel header that marks the end of the heap space
	andi	t0, t0, ~7                          # Round down to multiple of alignment
	sw		t0, alloc_header_blocksize(a2)

	addi	a0, a2, alloc_header__size          # Skip over the header we just wrote
	add		a0, a0, t0                          # Skip over the free block of memory

	sw		a2, alloc_header_prev(a0)           # Write a final header with zero size to mark the end of the heap
	li		t0, 0
	sw		t0, alloc_header_nextfree(a0)       # No next free block
	sw		t0, alloc_header_prevfree(a0)       # No prev free block
	sw		t0, alloc_header_blocksize(a0)      # Zero size

	ret


malloc:
	addi	sp, sp, -6
	sw		ra, (sp)
	sw		s0, 2(sp)
	sw		s1, 4(sp)

	# a0 = size required - round it up to the next multiple
	addi	a0, a0, 7
	andi	a0, a0, ~7

	la		a1, alloc_heapdata
	lw		a1, alloc_heapdata_firstfree(a1)    # a1 = current block
	li		a2, 0                               # a2 = best block so far
	li		s0, -1                              # s0 = best block's size (small is good)

1:
	lw		t0, alloc_header_blocksize(a1)      # t0 = current block size
	bltu	t0, a0, 2f                          # if a0 is bigger, this block is no good
	bgeu	t0, s0, 2f                          # if the existing candidate is smaller, skip
	mv		s0, t0                              # record new best block
	mv		a2, a1
2:
	lw		a1, alloc_header_nextfree(a1)
	bnez	a1, 1b
	
	bnez	a2, 1f                              # If we found a good block, use it

	mv		s0, a0

	call	printimm
	.asciz "\r\n\nOut of memory while allocating "

	mv		a0, s0
	call	printnum

	call	printimm
	.asciz " bytes\r\n\n"

	call	heapdump

	call	visualiseheap

	ebreak
	call	exit

1:
	mv		a1, a2
	mv		t0, s0
	# The block pointed at by a1 has size t0 which is big enough.  Split it if it is significantly bigger.

	sub		t0, t0, a0                          # t0 = excess space
	li		a2, 32
	bltu	t0, a2, .malloc_nosplit				# branch if it's not worth splitting
	j		.malloc_split

.malloc_nosplit:
	lw		t0, alloc_header_nextfree(a1)       # Unchain this block from the free blocks chain
	lw		a2, alloc_header_prevfree(a1)
	beqz	a2, 1f
	sw		t0, alloc_header_nextfree(a2)       # If a2 is not null, point it past this block
	j		2f
1:
	la		a2, alloc_heapdata                  # If a2 was null then we need to instead update heapdata's first free block pointer
	sw		t0, alloc_heapdata_firstfree(a2)
	li		a2, 0
2:
	beqz	t0, 1f                              # If a1's nextfree was not null...
	sw		a2, alloc_header_prevfree(t0)       # ... point that next block's prevfree back to a2
1:
	li		t0, 0
	sw		t0, alloc_header_nextfree(a1)       # Clear the next/prev free pointers as the block itself is not free
	sw		t0, alloc_header_prevfree(a1)

	addi	a0, a1, alloc_header__size          # Return the block's data address

	j		.malloc_return

.malloc_split:
	addi	t0, t0, -alloc_header__size         # Rewrite a1's block header with the size residue
	sw		t0, alloc_header_blocksize(a1)

	add		a2, a1, t0                          # Calculate the location for the new block header
	addi	a2, a2, alloc_header__size

	sw		a1, alloc_header_prev(a2)           # Initialise a2's header fields
	sw		a0, alloc_header_blocksize(a2)

	li		t0, 0
	sw		t0, alloc_header_nextfree(a2)       # Clear a2's next/prev free pointers as the block itself is not free
	sw		t0, alloc_header_prevfree(a2)

	addi	a1, a2, alloc_header__size          # Advance past the new block header...
	add		a1, a1, a0                          # ... and the data block, to reach the next block
	sw		a2, alloc_header_prev(a1)           # Update its prev pointer

	addi	a0, a2, alloc_header__size          # Return the new block's data address

.malloc_return:
	lw		ra, (sp)
	lw		s0, 2(sp)
	lw		s1, 4(sp)
	addi	sp, sp, 6
	ret



free:
	# a0 = pointer to data memory to be freed
	addi	a0, a0, -alloc_header__size			# a0 = pointer to block header

	# See if we can just merge this block with the previous one
	lw		a1, alloc_header_prev(a0)           # a1 = previous block, if any
	beqz	a1, 2f
	lw		a2, alloc_header_prevfree(a1)       # if its prevfree is not null, then the block is free
	bnez	a2, 1f
	lw		a2, alloc_header_nextfree(a1)       # check nextfree as well in case it was the first block in the free chain
	beqz	a2, 2f
1:
	j		.free_combine_prev
2:

	# See if we can merge this block with the next one instead
	lw		a1, alloc_header_blocksize(a0)
	add		a1, a1, a0
	addi	a1, a1, alloc_header__size
	lw		a2, alloc_header_prevfree(a1)
	bnez	a2, 1f
	lw		a2, alloc_header_nextfree(a1)
	beqz	a2, 2f
1:
	j		.free_combine_next
2:

	# Neither neighbouring block is free, so we just add this block to the free chain and leave it fragmented
	la		a1, alloc_heapdata
	lw		a2, alloc_heapdata_firstfree(a1)    # Look up first free block

	sw		a2, alloc_header_nextfree(a0)       # Copy it into the newly-freed block's nextfree pointer

	sw		a0, alloc_heapdata_firstfree(a1)    # Point heapdata's firstfree pointer at the newly-freed block

	beqz	a2, 1f                              # If the old first free block was not null...
	sw		a0, alloc_header_prevfree(a2)       # ... update its prevfree pointer to point to the newly-freed block
1:
	ret

.free_combine_prev:
	# a0 = new block to free
	# a1 = previous neighbour that is already free
	#
	# In this case we update the next block's prev pointer to point back to the previous block (a1)
	# and increase the size of the previous block to use up all the memory from the freed block (a0).
	# The free block links don't need updating as the header doesn't move.

	# Find the next block so we can update its prev pointer
	lw		a2, alloc_header_blocksize(a0)
	add		a2, a2, a0
	addi	a2, a2, alloc_header__size          # a2 = a0->next
	sw		a1, alloc_header_prev(a2)           # a0->next->prev = a1 = a0->prev

	sub		a0, a2, a1                          # Gap from a1 to a2
	addi	a0, a0, -alloc_header__size         # ... minus block header size
	sw		a0, alloc_header_blocksize(a1)      # a1->size = a2 - a1 - sizeof(alloc_header)

	# We could stop here, but there's also an opportunity to combine with the next block if that one is also free.
	# It's different to the "free_combine_next" case below though because here both blocks are already in the
	# free chain, so one of them must be removed.  We remove the next block because that's easiest.

	# See if the next block (a2) is also a free block.  We know that it is not the only free block, so
	# it is free if and only if at least one of its prevfree/nextfree pointers is not null
	lw		a0, alloc_header_prevfree(a2)
	lw		t0, alloc_header_nextfree(a2)
	bnez	t0, 1f
	bnez	a0, 2f

	ret

1:	# Unlink the block - t0 is non-null, a0 may or may not be null
	sw		a0, alloc_header_prevfree(t0)       # a2->nextfree->prevfree = a2->prevfree
	bnez	a0, 2f                              # if a0 is non-null, go ahead to 2 to update its nextfree pointer
	la		a0, alloc_heapdata                  # otherwise, there is no prevfree block so we need to update the heapdata itself
	sw		t0, alloc_heapdata_firstfree(a0)    # heapdata->firstfree = t0
	j		1f
2:	# There are two ways to get here - but either way a0 is non-null and t0 doesn't need further unlinking
	sw		t0, alloc_header_nextfree(a0)       # a2->prevfree->nextfree = a2->nextfree

1:	# The block at a2 is now no longer in the free block chain so we can consume it.
	# Rather than repeating the code from "free_combine_prev", we can just update a0 and
	# chain back there.  a1 is still set correctly.  It will merge the blocks and then attempt
	# to merge forwards again, which should fail but is harmless anyway.
	mv		a0, a2
	j		.free_combine_prev


.free_combine_next:
	# a0 = new block to free
	# a1 = next neighbour in memory, which is already free
	#
	# We need to set a0->next->next->prev = a0, and then a0->blocksize = a0->next->next - a0 - sizeof(alloc_header),
	# and also update the free block linked list to include a0's header rather than a1's
	
	# Start by updating the free block linked list pointers as we already have a0 and a1 ready for that
	lw		a2, alloc_header_prevfree(a1)       # a2 = a1->prev
	sw		a2, alloc_header_prevfree(a0)       # a0->prev = a2
	beqz	a2, 1f                              # if a2:
	sw		a0, alloc_header_nextfree(a2)       #     a2->next = a0  // rather than a1
	j		2f                                  # else:
1:                                              #
	la		a2, alloc_heapdata                  #     a2 = heapdata
	sw		a0, alloc_heapdata_firstfree(a2)    #     a2->firstfree = a0  // rather than a1
2:
	lw		a2, alloc_header_nextfree(a1)       # a2 = a1->next
	sw		a2, alloc_header_nextfree(a0)       # a0->next = a2
	beqz	a2, 1f                              # if a2:
	sw		a0, alloc_header_prevfree(a2)       #     a2->prev = a0  // rather than a1
1:

	# Now find a0->next->next == a1->next
	lw		a2, alloc_header_blocksize(a1)
	add		a2, a2, a1
	addi	a2, a2, alloc_header__size          # a2 = a1 + a1->blocksize + sizeof(alloc_header)

	sw		a0, alloc_header_prev(a2)           # a2->prev = a0
	sub		a2, a2, a0
	addi	a2, a2, -alloc_header__size         # a2 = a2 - a0 - sizeof(alloc_header)
	sw		a2, alloc_header_blocksize(a0)

	ret


heapdump:
	addi	sp, sp, -4
	sw		ra, (sp)
	sw		s0, 2(sp)

	addi	sp, sp, -memstats__size
	mv		a0, sp
	call	memstats

	call	printimm
	.asciz "    memstats: "

	lw		a0, memstats_total_allocated(sp)
	call	printhex16
	li		a0, ' '
	call	putchar
	lw		a0, memstats_total_free(sp)
	call	printhex16
	li		a0, ' '
	call	putchar
	lw		a0, memstats_num_allocated(sp)
	call	printhex16
	li		a0, ' '
	call	putchar
	lw		a0, memstats_num_free(sp)
	call	printhex16
	li		a0, ' '
	call	putchar
	lw		a0, memstats_largest_free(sp)
	call	printhex16

	call	printimm
	.asciz "\r\n"

	addi	sp, sp, memstats__size


	la		s0, alloc_heapdata

	call	printimm
	.asciz "\r\n=== Heap dump ===\r\n\n"

	call	printimm
	.asciz "All blocks:\r\n\n"

	lw		s0, alloc_heapdata_first(s0)

1:
	mv		a0, s0
	call	printblockheader

	lw		a0, alloc_header_blocksize(s0)
	beqz	a0, 1f

	add		s0, s0, a0
	addi	s0, s0, alloc_header__size
	j		1b

1:
	call	printimm
	.asciz "\nFree blocks:\r\n\n"

	la		s0, alloc_heapdata
	lw		s0, alloc_heapdata_firstfree(s0)
1:
	mv		a0, s0
	call	printblockheader

	lw		s0, alloc_header_nextfree(s0)
	bnez	s0, 1b

	li		a0, 10
	call	putchar

	lw		ra, (sp)
	lw		s0, 2(sp)
	addi	sp, sp, 4
	ret


printblockheader:
	addi	sp, sp, -6
	sw		ra, (sp)
	sw		a0, 2(sp)
	sw		a1, 4(sp)

	mv		a1, a0

	call	printhex16

	call	printimm
	.asciz " - "

	lw		a0, alloc_header_prev(a1)
	call	printhex16
	li		a0, ' '
	call	putchar

	lw		a0, alloc_header_prevfree(a1)
	call	printhex16
	li		a0, ' '
	call	putchar

	lw		a0, alloc_header_nextfree(a1)
	call	printhex16
	li		a0, ' '
	call	putchar

	lw		a0, alloc_header_blocksize(a1)
	call	printhex16

	call printimm
	.asciz "\r\n"

	lw		ra, (sp)
	lw		a0, 2(sp)
	lw		a1, 4(sp)
	addi	sp, sp, 6
	ret


memstats_total_allocated = 0
memstats_total_free = 2
memstats_num_allocated = 4
memstats_num_free = 6
memstats_largest_free = 8
memstats__size = 10

memstats:
	# Return details like total allocated, total free, largest free block
	#
	# It would be nice to track high watermark but that requires constant updating
	# Also total requested vs allocated as we sometimes return a larger block to avoid fragmenting it

	addi	sp, sp, -6
	sw		ra, (sp)
	sw		s0, 2(sp)
	sw		s1, 4(sp)

	li		t0, 0
	sw		t0, memstats_total_allocated(a0)
	sw		t0, memstats_total_free(a0)
	sw		t0, memstats_num_allocated(a0)
	sw		t0, memstats_num_free(a0)
	sw		t0, memstats_largest_free(a0)

	la		s0, alloc_heapdata
	lw		a2, alloc_heapdata_firstfree(s0)
	lw		s0, alloc_heapdata_first(s0)

	# Preload this before the loop
	lw		s1, alloc_header_blocksize(s0)

5:
	lw		a1, alloc_header_prevfree(s0)
	bnez	a1, 1f
	lw		a1, alloc_header_nextfree(s0)
	bnez	a1, 1f
	beq		s0, a2, 1f

	# It's an allocated block
	lw		t0, memstats_total_allocated(a0)
	add		t0, t0, s1
	sw		t0, memstats_total_allocated(a0)

	lw		t0, memstats_num_allocated(a0)
	addi	t0, t0, 1
	sw		t0, memstats_num_allocated(a0)

	j		2f

1:
	# It's a free block
	lw		t0, memstats_largest_free(a0)
	bltu	s1, t0, 1f
	sw		s1, memstats_largest_free(a0)
1:
	lw		t0, memstats_total_free(a0)
	add		t0, t0, s1
	sw		t0, memstats_total_free(a0)

	lw		t0, memstats_num_free(a0)
	addi	t0, t0, 1
	sw		t0, memstats_num_free(a0)

2:
	# Advance to next block
	addi	s0, s0, alloc_header__size
	add		s0, s0, s1
	lw		s1, alloc_header_blocksize(s0)
	bnez	s1, 5b

	# Return
	lw		ra, (sp)
	lw		s0, 2(sp)
	lw		s1, 4(sp)
	addi	sp, sp, 6
	ret



visualiseheap:
	# Display a complete map of heap usage
	#
	# The system has 64K of memory and my display is big enough to fit 64 rows and 128 columns
	# At that size each character represents 8 bytes, which is also the heap granularity
	# 
	# So I can draw '.' for free and 'X' for used
	# Or maybe I can show block sizes as <==> but then a single-character block wouldn't work
	# But a block can never be less than 16 bytes, which takes up two characters, so that's
	# fine
	# What about locations outside the heap?  Maybe X for those
	#
	# XXXXXXXXXXXXXXXX........<==>..<===><==><>...<>..<=><=><===>.......XXXXX
	#
	# The heap blocks are walkable in order so it's easy to just walk through and output
	# the diagram as we go

	addi	sp, sp, -6
	sw		ra, (sp)
	sw		s0, 2(sp)
	sw		s1, 4(sp)

	li		s1, 0                              # s1 = current memory position

	la		s0, alloc_heapdata
	lw		t0, alloc_heapdata_firstfree(s0)   # t0 = first free block address
	lw		s0, alloc_heapdata_first(s0)       # s0 = start of next block

	# Print X until we reach the heap
	li		a0, 'X'                            # start char
	li		a1, 'X'                            # mid char
	li		a2, '|'                            # end char
	call	visualiseheap_printchunk

3:
	# Is this block free?
	beq		s0, t0, 1f
	lw		a0, alloc_header_prevfree(s0)
	bnez	a0, 1f

	# Used block
	li		a0, '<'
	li		a1, '='
	li		a2, '>'
	j		2f

1:	# Free block
	li		a0, '.'
	mv		a1, a0
	mv		a2, a1

2:
	lw		ra, alloc_header_blocksize(s0)
	beqz	ra, 1f
	add		s0, s0, ra
	addi	s0, s0, alloc_header__size

	call	visualiseheap_printchunk

	j		3b

1:	# End of heap - print X until the top of memory
	li		s0, 0
	li		a0, '|'
	li		a1, 'X'
	mv		a2, a1
	call	visualiseheap_printchunk

	# Return
	lw		ra, (sp)
	lw		s0, 2(sp)
	lw		s1, 4(sp)
	addi	sp, sp, 6
	ret


visualiseheap_printchunk:
	# This is not a normal function - it modifies s1 and preserves t0 for the caller
	addi	sp, sp, -10
	sw		ra, (sp)
	sw		t0, 2(sp)
	sw		a2, 4(sp)
	sw		a1, 8(sp)
	
2:
	li		t0, 1023
	and		t0, t0, s1
	bnez	t0, 1f

	sw		a0, 6(sp)
	li		a0, 13
	call	putchar
	li		a0, 10
	call	putchar
	lw		a0, 6(sp)

1:
	addi	s1, s1, 8
	beq		s1, s0, 1f

	call	putchar
	lw		a0, 8(sp)
	j		2b

1:	# Last character
	lw		a0, 4(sp)
	call	putchar

	lw		t0, 2(sp)
	lw		ra, (sp)
	addi	sp, sp, 10
	ret

