// qacpp_reference_traits.h
//

#ifndef PRLGCC_INCLUDED_QACPP_REFERENCE_TRAITS
#define PRLGCC_INCLUDED_QACPP_REFERENCE_TRAITS

template<typename __type>
struct __qacpp_remove_reference
{
 typedef __type type;
};
template<typename __type>
struct __qacpp_remove_reference<__type &>
{
 typedef __type type;
};

template<typename __type>
struct __qacpp_remove_reference<__type &&>
{
 typedef __type type;
};

template <class __type>
struct __qacpp_add_lvalue_reference
{
  typedef __type & type;
};


template<typename __type>
struct __qacpp_remove_cv
{
  typedef __type type;
};

template<typename __type>
struct __qacpp_remove_cv<const __type>
{
  typedef __type type;
};

template<typename __type>
struct __qacpp_remove_cv<volatile __type>
{
  typedef __type type;
};

template<typename __type>
struct __qacpp_remove_cv<const volatile __type>
{
  typedef __type type;
};

#endif
