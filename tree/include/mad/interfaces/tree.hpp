#ifndef __MAD_INTERFACES_TREE_HPP__
#define __MAD_INTERFACES_TREE_HPP__

#include <iterator>
#include <map>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace mad { namespace interfaces { namespace tree {

class Node
{
public:
  virtual ~Node() {}
};

class MapNode : public Node
{
public:
  using key_type = std::string;

  class KeyValuePair
  {
  public:
    KeyValuePair()
    {
    }

    KeyValuePair(const key_type* key, std::unique_ptr<Node> value)
      : m_key(key),
        m_value(std::move(value))
    {
    }

    const key_type& key() const
    {
      return *m_key;
    }

    Node& value()
    {
      return *m_value;
    }

    const Node& value() const
    {
      return *m_value;
    }

  private:
    const key_type* m_key = nullptr;
    std::unique_ptr<Node> m_value;
  };

  class Iterator : public std::iterator<std::bidirectional_iterator_tag, KeyValuePair>
  {
  private:
    typedef std::iterator<std::bidirectional_iterator_tag, KeyValuePair> base_type;

  public:
    Iterator() {}
    explicit Iterator(typename std::map<key_type, KeyValuePair>::iterator it) : m_it(it) {}
    Iterator& operator++() { ++m_it; return *this; }
    Iterator operator++(int) { Iterator tmp(*this); operator++(); return tmp; }
    bool operator==(const Iterator& other) const { return m_it == other.m_it; }
    bool operator!=(const Iterator& other) const { return m_it != other.m_it; }
    typename base_type::reference operator*() const { return m_it->second; }
    typename base_type::pointer operator->() const { return &m_it->second; }
    Iterator& operator--() { --m_it; return *this; }
    Iterator operator--(int) { Iterator tmp(*this); operator--(); return tmp; }

  private:
    typename std::map<key_type, KeyValuePair>::iterator m_it;
  };

  class ConstIterator : public std::iterator<std::bidirectional_iterator_tag, const KeyValuePair>
  {
  private:
    typedef std::iterator<std::bidirectional_iterator_tag, const KeyValuePair> base_type;

  public:
    ConstIterator() {}
    explicit ConstIterator(typename std::map<key_type, KeyValuePair>::const_iterator it) : m_it(it) {}
    ConstIterator& operator++() { ++m_it; return *this; }
    ConstIterator operator++(int) { ConstIterator tmp(*this); operator++(); return tmp; }
    bool operator==(const ConstIterator& other) const { return m_it == other.m_it; }
    bool operator!=(const ConstIterator& other) const { return m_it != other.m_it; }
    typename base_type::reference operator*() const { return m_it->second; }
    typename base_type::pointer operator->() const { return &m_it->second; }
    ConstIterator& operator--() { --m_it; return *this; }
    ConstIterator operator--(int) { ConstIterator tmp(*this); operator--(); return tmp; }

  private:
    typename std::map<key_type, KeyValuePair>::const_iterator m_it;
  };

  typedef Iterator iterator;
  typedef ConstIterator const_iterator;

public:
  iterator begin() { return iterator(m_nodes.begin()); }
  const_iterator begin() const { return const_iterator(m_nodes.begin()); }
  iterator end() { return iterator(m_nodes.end()); }
  const_iterator end() const { return const_iterator(m_nodes.end()); }

  std::pair<iterator, bool> insert(const key_type& key, std::unique_ptr<Node> node)
  {
    if (!node)
      throw std::logic_error("Passed node is nullptr");

    auto insert = m_nodes.emplace(key, KeyValuePair());
    if (insert.second)
        insert.first->second = KeyValuePair(&insert.first->first, std::move(node));

    return std::make_pair(iterator(insert.first), insert.second);
  }

  iterator find(const key_type& key)
  {
    return iterator(m_nodes.find(key));
  }

  const_iterator find(const key_type& key) const
  {
    return const_iterator(m_nodes.find(key));
  }

private:
  std::map<key_type, KeyValuePair> m_nodes;
};

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

#endif //__MAD_INTERFACES_TREE_HPP__
