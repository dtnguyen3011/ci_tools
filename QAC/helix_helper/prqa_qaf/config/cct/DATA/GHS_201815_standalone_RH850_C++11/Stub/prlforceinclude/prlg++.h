#ifndef PRLGCC_FI_H
#define PRLGCC_FI_H

#ifndef __QACPP_MAJOR__
#error "PRLGCC requires __QACPP_MAJOR__ and __QACPP_MINOR__ version numbers"
#elif ((__QACPP_MAJOR__ < 32) || ((__QACPP_MAJOR__ == 32) && (__QACPP_MINOR__ < 1)))
#error "PRLGCC requires QA C++ version 3.2 or later"
#endif

// for some installations of g++ these implicit macros may not be
// included in the 'g++' output
#ifndef __cplusplus
# define __cplusplus 199811
#endif

#ifndef __STDC__
#  define __STDC__
#endif

#ifndef _GNU_SOURCE
#  define _GNU_SOURCE
#endif

// CR-15557 statement expressions
#define sigsetjmp sigsetjmp
#define siglongjmp siglongjmp
template <typename sigjmp_buf> extern int sigsetjmp (sigjmp_buf, int);
template <typename sigjmp_buf> extern void siglongjmp (sigjmp_buf, int);

// FD_ISSET and FD_ZERO macros
#define __FD_ISSET(fd, fdsp) ((fd)!=0)
extern "C" void* memset(void*, int, PRQA_SIZE_T);
#define FD_ZERO(p) memset((p),0,sizeof(*(p)))

#define __WAIT_INT(status) (status)

// These types are defined using __attributes__ and so end up being
// different to 'float' and 'double'.
typedef volatile float __m128;
typedef volatile double __m128d;
typedef volatile int __m128i;


// PR-16183
#define __builtin_offsetof(type, member) __qacpp_offsetof(type, member)

// Extension keywords
#define _Complex
#define __FUNCTION__                              "__FUNCTION__"
#define __PRETTY_FUNCTION__                       "__PRETTY_FUNCTION__"
#define __asm                                     asm
#define __asm__                                   asm
#define asm                                       _ignore_paren
#define __attribute                               __attribute__
#define __attribute__                             _ignore_paren
#define __const                                   __const__
#define __const__                                 const
#define __declspec(x)                             __attribute__((x))
#define __decltype                                decltype
#define __extension__
#define __func__                                  "__func__"
#define __imag__
#define __inline                                  __inline__
#define __inline__                                inline
#define __null                                    0
#define __real__
#define __restrict                                __restrict__
#define __restrict__
#define __signed                                  __signed__
#define __signed__                                signed
#define __thread
//#define thread_local
#define __volatile                                __volatile__
#define __volatile__                              volatile

#define __alignof                                 __alignof__
#if (__QACPP_MAJOR__ < 42)
#define __alignof__(x)                            sizeof(char)
#else
#define __alignof__(x)                            alignof(x)
#endif

// TR1 functions
#define __has_nothrow_assign(x)                   __qacpp_has_nothrow_assign(x)
#define __has_nothrow_constructor(x)              __qacpp_has_nothrow_constructor(x)
#define __has_nothrow_copy(x)                     __qacpp_has_nothrow_copy(x)
#define __has_trivial_assign(x)                   __qacpp_has_trivial_assign(x)
#define __has_trivial_constructor(x)              __qacpp_has_trivial_constructor(x)
#define __has_trivial_copy(x)                     __qacpp_has_trivial_copy(x)
#define __has_trivial_destructor(x)               __qacpp_has_trivial_destructor(x)
#define __has_virtual_destructor(x)               __qacpp_has_virtual_destructor(x)
#define __is_abstract(x)                          __qacpp_is_abstract(x)
#define __is_base_of(x,y)                         __qacpp_is_base_of(x,y) || (!__qacpp_is_union(x) && __qacpp_is_same(typename __qacpp_remove_cv<x>::type, typename __qacpp_remove_cv<y>::type))
#define __is_class(x)                             __qacpp_is_class(x)
#define __is_convertible_to(x,y)                  __qacpp_is_convertible(x,y)
#define __is_empty(x)                             __qacpp_is_empty(x)
#define __is_enum(x)                              __qacpp_is_enum(x)
#define __is_pod(x)                               __qacpp_is_pod(x)
#define __is_polymorphic(x)                       __qacpp_is_polymorphic(x)
#define __is_union(x)                             __qacpp_is_union(x)
#define __is_standard_layout(x)                   __qacpp_is_standard_layout(x)

#define __has_assign(x)                           false
#define __has_copy(x)                             false
#define __has_finalizer(x)                        false
#define __has_user_destructor(x)                  false
#define __is_delegate(x)                          false
#define __is_interface_class(x)                   false
#define __is_ref_array(x)                         false
#define __is_ref_class(x)                         false
#define __is_sealed(x)                            false
#define __is_simple_value_class(x)                false
#define __is_value_class(x)                       false
#define __must_be_array(x)                        false

#if (__QACPP_MAJOR__ < 42)
#define __is_literal_type(x)                      false
#else
#define __is_literal_type(x)                      __qacpp_is_literal(x)
#endif
#define __is_literal(x)                           __is_literal_type(x)

#define __is_trivial(x)                           (__has_trivial_constructor(x) && __has_trivial_copy(x) && __has_trivial_destructor(x))
#if (__QACPP_MAJOR__ < 42)
#define __is_trivially_copyable(x)                (__has_trivial_copy(x) && __has_trivial_destructor(x))
#define __is_trivially_constructible(x,y)         false
#define __is_trivially_assignable(x,y)            false
#else
#define __is_trivially_copyable(x)                __qacpp_is_trivially_copyable(x)
#define __is_trivially_constructible(x,y)         __qacpp_is_trivially_constructible(x, y)
#define __is_trivially_assignable(x,y)            __qacpp_is_trivially_assignable(x, y)
#endif

#if (__QACPP_MAJOR__ < 42)
#define __is_final(x)                             false
#else
#define __is_final(x)                             __qacpp_is_final(x)
#endif
#if (__QACPP_MAJOR__ < 40)
#define __underlying_type(x)                      int
#else
#define __underlying_type(x)                      __qacpp_underlying_type(x)
#endif
#if (__QACPP_MAJOR__ < 42)
#define static_assert                             _ignore_semi
#endif

// Updates for TR1 MATH
#define GLIBCXX_USE_C99_MATH_TR1

// C '1x
#define _Pragma                                   _ignore_paren

// Forward declaration of 'type_info' (implicitly available in g++)
namespace std
{
  class type_info;
}

// Remove declarations that refer to __int128
#ifdef __GLIBCXX_TYPE_INT_N_0
#  undef __GLIBCXX_TYPE_INT_N_0
#endif

#ifdef __SIZEOF_INT128__
#  undef __SIZEOF_INT128__
#endif

// we don't support variable templates prior to QA-C++ 4.2
#if (__QACPP_MAJOR__ < 42) && defined(__cpp_variable_templates)
#  undef __cpp_variable_templates
#endif

// we don't support __has_include
#ifdef __has_include
#  undef __has_include
#endif

// we don't support __has_include_next
#ifdef __has_include_next
#  undef __has_include_next
#endif

// QAC++ from 4.1 onwards has __PRQA_COUNTER__ that can be used for __COUNTER__
#if (__QACPP_MAJOR__ >= 41)
#define __COUNTER__ __PRQA_COUNTER__
#endif

#if defined (__CYGWIN__) || defined (__MINGW32__) || defined (__WIN32)
/* gcc on windows requires additional workarounds */
#include "prlgcc_windows.h"
#endif

// =======================================================================================
//
// Work Around Flags
//
// =======================================================================================

//Brace-initialization
#if (__QACPP_MAJOR__ < 40)
#  define PRL_GCC_01
#endif

// Generalized Constant Expressions
#define PRL_GCC_02

// Reference to qualified name in primary specialization (PR-21834)
#define PRL_GCC_03

// Late parsing of exception specifications not finding functions (PR-21835)
#define PRL_GCC_04

// Pre standard rvalue reference
#define PRL_GCC_05

// Explicit 'const' on constexpr begin member
#define PRL_GCC_06

// GCC Statement Expressions
#if ((__QACPP_MAJOR__ < 40) || ((__QACPP_MAJOR__ == 40) && (__QACPP_MINOR__ < 1)))
#  define PRL_GCC_07
#endif

// GCC Void* Pointer Arithmetic
#define PRL_GCC_08

// Lambdas
#if (__QACPP_MAJOR__ < 40)
#  define PRL_GCC_09
#endif

// Deduction issue with aliases PR23313
#define PRL_GCC_10

// Unicode character types
#if (__QACPP_MAJOR__ < 41)
#  define PRL_GCC_11
#endif

// __STRICT_ANSI__ resulting in redefinition of inline keyword
#define PRL_GCC_12

// Use of numeric_limits::max in a context that requires a constant expression.
#if (__QACPP_MAJOR__ < 42)
#  define PRL_GCC_13
#endif

#endif // PRLGCC_FI_H
