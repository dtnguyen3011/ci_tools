#ifndef GH_RH_CPP_FI_H
#define GH_RH_CPP_FI_H

typedef union
{	/* pun float types as integer array */
	unsigned short _Word[8];
	float _Float;
	double _Double;
	long double _Long_double;
	} 
_PRL_Dconst;

extern const _PRL_Dconst _PRL_Finf , _PRL_Fnan;
#define __INFINITY__  ::_PRL_Finf._Float
#define __NAN__  ::_PRL_Fnan._Float


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

#define __is_literal_type(x)                      __qacpp_is_literal(x)
#define __is_literal(x)                           __is_literal_type(x)

#define __is_trivial(x)                           (__has_trivial_constructor(x) && __has_trivial_copy(x) && __has_trivial_destructor(x))
#define __is_trivially_copyable(x)                __qacpp_is_trivially_copyable(x)
#define __is_trivially_constructible(x,y)         __qacpp_is_trivially_constructible(x, y)
#define __is_trivially_assignable(x,y)            __qacpp_is_trivially_assignable(x, y)

#define __is_final(x)                             __qacpp_is_final(x)
#define __underlying_type(x)                      __qacpp_underlying_type(x)

#define __is_constructible( a , b ... )          false
#define __is_destructible( a )                   false
#define __is_trivially_destructible(x)          __qacpp_has_trivial_destructor(x)
#define __is_nothrow_constructible(x)           false
#define __is_nothrow_assignable(x)              false
#define __is_nothrow_destructible(x)            false

// C '1x
#define _Pragma                                   _ignore_paren





#else
#error "Multiple include"
#endif  /* ifndef GH_ARM_CPP_FI_H */

