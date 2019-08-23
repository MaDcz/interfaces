#pragma once

#include "node.hpp"

#include <iterator>
#include <memory>
#include <stdexcept>
#include <string>
#include <unordered_map>

namespace mad { namespace interfaces { namespace tree {

class MapNode : public virtual Node
{
public:
  using key_type = std::string;

  class KeyValuePair
  {
  public:
    KeyValuePair()
    {
    }

    KeyValuePair(const key_type& key, std::unique_ptr<Node>&& value)
      : m_key(key),
        m_value(std::move(value))
    {
    }

    const key_type& key() const
    {
      return m_key;
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
    key_type m_key;
    std::unique_ptr<Node> m_value;
  };

  class Iterator : public std::iterator<std::bidirectional_iterator_tag, KeyValuePair>
  {
  private:
    using base_type = std::iterator<std::bidirectional_iterator_tag, KeyValuePair>;

  public:
    Iterator() {}
    explicit Iterator(typename std::unordered_map<key_type, KeyValuePair>::iterator it) : m_it(it) {}
    Iterator& operator++() { ++m_it; return *this; }
    Iterator operator++(int) { Iterator tmp(*this); operator++(); return tmp; }
    bool operator==(const Iterator& other) const { return m_it == other.m_it; }
    bool operator!=(const Iterator& other) const { return m_it != other.m_it; }
    typename base_type::reference operator*() const { return m_it->second; }
    typename base_type::pointer operator->() const { return &m_it->second; }
    Iterator& operator--() { --m_it; return *this; }
    Iterator operator--(int) { Iterator tmp(*this); operator--(); return tmp; }

  private:
    typename std::unordered_map<key_type, KeyValuePair>::iterator m_it;
  };

  class ConstIterator : public std::iterator<std::bidirectional_iterator_tag, const KeyValuePair>
  {
  private:
    using base_type = std::iterator<std::bidirectional_iterator_tag, const KeyValuePair>;

  public:
    ConstIterator() {}
    explicit ConstIterator(typename std::unordered_map<key_type, KeyValuePair>::const_iterator it) : m_it(it) {}
    ConstIterator& operator++() { ++m_it; return *this; }
    ConstIterator operator++(int) { ConstIterator tmp(*this); operator++(); return tmp; }
    bool operator==(const ConstIterator& other) const { return m_it == other.m_it; }
    bool operator!=(const ConstIterator& other) const { return m_it != other.m_it; }
    typename base_type::reference operator*() const { return m_it->second; }
    typename base_type::pointer operator->() const { return &m_it->second; }
    ConstIterator& operator--() { --m_it; return *this; }
    ConstIterator operator--(int) { ConstIterator tmp(*this); operator--(); return tmp; }

  private:
    typename std::unordered_map<key_type, KeyValuePair>::const_iterator m_it;
  };

  using iterator = Iterator;
  using const_iterator = ConstIterator;

public:
  // The class is made movable only explicitly here as the MSVC was throwing a compilation error
  // without it. It was trying to copy the instance even with the use of std::move().
  MapNode() = default;

  MapNode(const MapNode&) = delete;
  MapNode& operator=(const MapNode&) = delete;

  MapNode(MapNode&&) = default;
  MapNode& operator=(MapNode&&) = default;

  ~MapNode() {}

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
        insert.first->second = KeyValuePair(insert.first->first, std::move(node));

    return std::make_pair(iterator(insert.first), insert.second);
  }

  bool empty() const { return m_nodes.empty(); }

  size_t size() const { return m_nodes.size(); }

  iterator find(const key_type& key) { return iterator(m_nodes.find(key)); }

  const_iterator find(const key_type& key) const { return const_iterator(m_nodes.find(key)); }

  size_t erase(const key_type& key) { return m_nodes.erase(key); }

  void clear() { m_nodes.clear(); }

private:
  std::unordered_map<key_type, KeyValuePair> m_nodes;
};

}}} // namespace mad::interfaces::tree
