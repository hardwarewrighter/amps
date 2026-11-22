INCLUDE memory.x
ENTRY(Reset)
_stack_top = ORIGIN(RAM) + LENGTH(RAM) - 8;
SECTIONS {
  .vector_table ORIGIN(FLASH) : { KEEP(*(.vector_table)); } > FLASH
  .text : ALIGN(4) { *(.text .text.*); *(.rodata .rodata.*); . = ALIGN(4); } > FLASH
  .data : ALIGN(4) {
    _sdata = .; *(.data .data.*); . = ALIGN(4); _edata = .;
  } > RAM AT > FLASH
  _sidata = LOADADDR(.data);
  .bss (NOLOAD) : ALIGN(4) {
    _sbss = .; *(.bss .bss.*); *(COMMON); . = ALIGN(4); _ebss = .;
  } > RAM
  /DISCARD/ : { *(.ARM.exidx* .ARM.extab*); }
}
ASSERT(SIZEOF(.vector_table) == 192, "Invalid vector table");
ASSERT(_ebss < _stack_top - 1024, "Insufficient stack space");
