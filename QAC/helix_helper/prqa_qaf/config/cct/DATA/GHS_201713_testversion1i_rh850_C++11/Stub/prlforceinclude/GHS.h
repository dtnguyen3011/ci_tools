#ifndef GENERIC_FI_H
#define GENERIC_FI_H

/* Compilers may use another function within the assert macro to exit the 
 * program. QAC thus does not see an "exit" function and assumes the 
 * function returns, which it does not.
 * The below pragma tells QAC the compiler supplied function does not
 * return.
 */

/* examples - GCC, ICC, BCC 3.1, BCC 5.5, CYGWIN gcc, Watcom 1.6 */
#pragma PRQA_NO_RETURN __assert_fail
#pragma PRQA_NO_RETURN __assert_perror_fail
#pragma PRQA_NO_RETURN __assert

/* SDCC, BCC 5.5, Digital Mars DM 8.4, LCC, Watcom 1.6, Fujitsu F2MM,FR */
#pragma PRQA_NO_RETURN _assert

/* HI-TECH PCCLite */
#pragma PRQA_NO_RETURN _fassert

/* DJGPP, D.J.Delorie gcc DOS port */
#pragma PRQA_NO_RETURN __dj_assert

/* Watcom 1.6, MSVS 08 */
#pragma PRQA_NO_RETURN _wassert
#pragma PRQA_NO_RETURN __wassert
#pragma PRQA_NO_RETURN _assert99
#pragma PRQA_NO_RETURN _wassert99
#pragma PRQA_NO_RETURN __assert99
#pragma PRQA_NO_RETURN __wassert99

/* Renesas M32R compiler */
#pragma PRQA_NO_RETURN _Assert

/* NEC 78K0 series 16bit compiler */
#pragma PRQA_NO_RETURN __assertfail
#pragma PRQA_NO_RETURN __assertfail_n
#pragma PRQA_NO_RETURN __assertfail_f


/* Depending on the code that the compiler maker uses within the assert macro,
 * QAC may issue warnings. It is also possible that when the NDEBUG macro is used
 * to suppress the assertion code, QAC may issue a "no side-effects" warning.
 * To eliminate these, we turn off all warnings for the assert macro.
 */
#pragma PRQA_MACRO_MESSAGES_OFF "assert"


/* Any other items that may be required in a "force-include" file should be placed below. */

/* Prototypes for the below v850 intrinsic functions can be found 
 * in include/v800/v800_ghs.h. 
 */

#if defined(__cplusplus)
extern "C"
{
void __DI();
void __EI();
}
#endif
unsigned int __DIR(void);
unsigned int __EIR(void); 
void __RIR(unsigned int);
unsigned int __GETSR(void);
void __SETSR(unsigned int);
extern unsigned int __MULUH(unsigned int a, unsigned int b);
extern signed int __MULSH(signed int a, signed int b);

#else
#error "Multiple include"
#endif  /* ifndef GENERIC_FI_H */

