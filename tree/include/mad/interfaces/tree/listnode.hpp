#ifndef __MAD_INTERFACES_TREE_LISTNODE_HPP__
#define __MAD_INTERFACES_TREE_LISTNODE_HPP__

#include "node.hpp"

#include <cassert>
#include <iterator>
#include <memory>
#include <stdexcept>
#include <vector>

namespace mad { namespace interfaces { namespace tree {

class ListNode : public Node
{
public:
  class Iterator : public std::iterator<std::random_access_iterator_tag, Node>
  {
  private:
    typedef std::iterator<std::random_access_iterator_tag, Node> base_type;

  public:
    Iterator() {}
    explicit Iterator(typename std::vector<std::unique_ptr<Node>>::iterator it) : m_it(it) {}
    Iterator& operator++() { ++m_it; return *this; }
    Iterator operator++(int) { Iterator tmp(*this); operator++(); return tmp; }
    bool operator==(const Iterator& other) const { return m_it == other.m_it; }
    bool operator!=(const Iterator& other) const { return m_it != other.m_it; }
    typename base_type::reference operator*() const { return *m_it->get(); }
    typename base_type::pointer operator->() const { return m_it->get(); }
    Iterator& operator--() { --m_it; return *this; }
    Iterator operator--(int) { Iterator tmp(*this); operator--(); return tmp; }
    Iterator operator+(typename base_type::difference_type n) const { return Iterator(m_it+n); }
    Iterator operator-(typename base_type::difference_type n) const { return Iterator(m_it-n); }
    bool operator<(const Iterator& other) const { return m_it < other.m_it; }
    bool operator>(const Iterator& other) const { return m_it > other.m_it; }
    bool operator<=(const Iterator& other) const { return m_it <= other.m_it; }
    bool operator>=(const Iterator& other) const { return m_it >= other.m_it; }
    Iterator& operator+=(typename base_type::difference_type n) { m_it += n; return *this; }
    Iterator& operator-=(typename base_type::difference_type n) { m_it -= n; return *this; }
    typename base_type::reference operator[](size_t n) const { return *m_it[n]; }

  private:
    typename std::vector<std::unique_ptr<Node>>::iterator m_it;
  };

  class ConstIterator : public std::iterator<std::random_access_iterator_tag, const Node>
  {
  private:
    typedef std::iterator<std::random_access_iterator_tag, const Node> base_type;

  public:
    ConstIterator() {}
    explicit ConstIterator(typename std::vector<std::unique_ptr<Node>>::const_iterator it) : m_it(it) {}
    ConstIterator& operator++() { ++m_it; return *this; }
    ConstIterator operator++(int) { ConstIterator tmp(*this); operator++(); return tmp; }
    bool operator==(const ConstIterator& other) const { return m_it == other.m_it; }
    bool operator!=(const ConstIterator& other) const { return m_it != other.m_it; }
    typename base_type::reference operator*() const { return *m_it->get(); }
    typename base_type::pointer operator->() const { return m_it->get(); }
    ConstIterator& operator--() { --m_it; return *this; }
    ConstIterator operator--(int) { ConstIterator tmp(*this); operator--(); return tmp; }
    ConstIterator operator+(typename base_type::difference_type n) const { return ConstIterator(m_it+n); }
    ConstIterator operator-(typename base_type::difference_type n) const { return ConstIterator(m_it-n); }
    bool operator<(const ConstIterator& other) const { return m_it < other.m_it; }
    bool operator>(const ConstIterator& other) const { return m_it > other.m_it; }
    bool operator<=(const ConstIterator& other) const { return m_it <= other.m_it; }
    bool operator>=(const ConstIterator& other) const { return m_it >= other.m_it; }
    ConstIterator& operator+=(typename base_type::difference_type n) { m_it += n; return *this; }
    ConstIterator& operator-=(typename base_type::difference_type n) { m_it -= n; return *this; }
    typename base_type::reference operator[](size_t n) const { return *m_it[n]; }

  private:
    typename std::vector<std::unique_ptr<Node>>::const_iterator m_it;
  };

  typedef Iterator iterator;
  typedef ConstIterator const_iterator;

public:
  iterator begin() { return iterator(m_nodes.begin()); }
  const_iterator begin() const { return const_iterator(m_nodes.begin()); }
  iterator end() { return iterator(m_nodes.end()); }
  const_iterator end() const { return const_iterator(m_nodes.end()); }

  Node& operator[](size_t pos)
  {
    auto node = m_nodes[pos].get();
    assert(node);
    return *node;
  }

  const Node& operator[](size_t pos) const
  {
    auto node = m_nodes[pos].get();
    assert(node);
    return *node;
  }

  Node& at(size_t pos)
  {
    auto node = m_nodes.at(pos).get();
    assert(node);
    return *node;
  }

  const Node& at(size_t pos) const
  {
    auto node = m_nodes.at(pos).get();
    assert(node);
    return *node;
  }

  size_t size() const { return m_nodes.size(); }

  void add(std::unique_ptr<Node> node)
  {
    if (!node)
      throw std::logic_error("Passed node is nullptr");
    m_nodes.emplace_back(std::move(node));
  }

private:
  std::vector<std::unique_ptr<Node>> m_nodes;
};

}}} // namespace mad::interfaces::tree

#endif // __MAD_INTERFACES_TREE_LISTNODE_HPP__
