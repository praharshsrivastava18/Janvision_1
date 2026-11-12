import java.util.*;

public class Day04_DataStructures {
    static class Node {
        int value; Node next;
        Node(int value, Node next) { this.value = value; this.next = next; }
    }
    static List<Integer> values(Node head) {
        List<Integer> result = new ArrayList<>();
        while (head != null) { result.add(head.value); head = head.next; }
        return result;
    }
    public static void main(String[] args) {
        Deque<String> stack = new ArrayDeque<>();
        stack.push("A"); stack.push("B");
        if (!stack.pop().equals("B")) throw new AssertionError("LIFO");
        Queue<String> queue = new ArrayDeque<>();
        queue.add("A"); queue.add("B");
        if (!queue.remove().equals("A")) throw new AssertionError("FIFO");
        Node head = new Node(3, new Node(5, new Node(8, null)));
        if (!values(head).equals(List.of(3, 5, 8))) throw new AssertionError("list");
        System.out.println("stack/queue OK; linked list: " + values(head));
    }
}
