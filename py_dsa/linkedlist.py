class Node:
    def __init__(self, data):
        self.data = data
        self.next = None
        self.head = None


class Ops:
    def __init__(self) -> None:
        self.list = Node(None)
        self.head = self.list

    def append(self, data):
        node = Node(data)
        if self.head.data is None:
            self.list = node
            self.head = self.list
            return
        pointer = self.list
        while pointer.next:
            pointer = pointer.next
        pointer.next = node

    def get_first_item(self) -> Node:
        print(f"FIRST ITEM is == {self.head.data}")
        return self.head.data

    def get_last_item(self):
        curr = self.list
        while True:
            if curr.data is None:
                return None
            if curr.next == None:
                print(f"LAST ITEM is == {curr.data}")
                return curr.data
            curr = curr.next

    def pop(self):
        # TODO: to be implemented later
        # remove last item from the LL
        pass

    def print(self):
        node = self.head
        while True:
            print(node.data, end="-->")
            if node.next is None:
                print("NULL\n")
                break
            node = node.next

    def prepend(self):
        # TODO: to be implemented later
        # insert item into the begining of LL
        pass

    def del_position(self, index):
        # Zero based index
        if index == 0:
            self.head = self.list.next
            node = self.list.next
            self.list.next = None
            self.list = node
            return

        # move till (pos - 1), then remove next item
        pointer = self.head
        for i in range(index-1,0,-1):
            if pointer.next is None:
                print(f"Index {index} Out of range")
                return
            pointer = pointer.next
        pointer.next = pointer.next.next

    def recursive_del_postion(self, node: Node, index) -> Node:
        if node is None:
            return None
        if index == 0:
            return node.next

        node.next = self.recursive_del_postion(node.next, index - 1)
        return node


if __name__ == "__main__":
    obj = Ops()
    for i in range(1,11):
        obj.append(i)
    obj.print()
    obj.get_first_item()
    obj.get_last_item()
    obj.del_position(3)
    obj.print()
    obj.recursive_del_postion(obj.head,6)
    obj.print()
    obj.recursive_del_postion(obj.head,9)
    obj.print()
