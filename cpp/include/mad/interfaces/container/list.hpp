#pragma once

#include <boost/signals2.hpp>

#include <vector>

namespace mad { namespace interfaces { namespace container {

template <typename ItemT>
class List
{
public:
  using iterator = typename std::vector<ItemT>::iterator;

  using const_iterator = typename std::vector<ItemT>::const_iterator;

public:
  iterator begin();

  const_iterator begin() const;

  iterator end();

  const_iterator end() const;

  ItemT& front();

  const ItemT& front() const;

  ItemT& back();

  const ItemT& back() const;

  void push_back(const ItemT& item);

  size_t size() const;

public:
  boost::signals2::signal<void(const ItemT&, const const_iterator&)> itemAboutToBeInserted;

  boost::signals2::signal<void(const const_iterator&)> itemInserted;

private:
  std::vector<ItemT> m_items;
};

template <typename ItemT>
typename List<ItemT>::iterator List<ItemT>::begin()
{
  return m_items.begin();
}

template <typename ItemT>
typename List<ItemT>::const_iterator List<ItemT>::begin() const
{
  return m_items.begin();
}

template <typename ItemT>
typename List<ItemT>::iterator List<ItemT>::end()
{
  return m_items.end();
}

template <typename ItemT>
typename List<ItemT>::const_iterator List<ItemT>::end() const
{
  return m_items.end();
}

template <typename ItemT>
ItemT& List<ItemT>::front()
{
  return m_items.front();
}

template <typename ItemT>
const ItemT& List<ItemT>::front() const
{
  return m_items.front();
}

template <typename ItemT>
ItemT& List<ItemT>::back()
{
  return m_items.back();
}

template <typename ItemT>
const ItemT& List<ItemT>::back() const
{
  return m_items.back();
}

template <typename ItemT>
void List<ItemT>::push_back(const ItemT& item)
{
  itemAboutToBeInserted(item, m_items.end());
  m_items.push_back(item);
  itemInserted(std::prev(m_items.end(), 1));
}

template <typename ItemT>
size_t List<ItemT>::size() const
{
  return m_items.size();
}

}}} // namespace mad::interfaces::container
