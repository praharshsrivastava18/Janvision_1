import java.util.*;

public class Day05_TreesHeaps {
    static class Node { int key; Node left, right; Node(int key) { this.key = key; } }
    static Node insert(Node root, int key) {
        if (root == null) return new Node(key);
        if (key < root.key) root.left = insert(root.left, key);
        else if (key > root.key) root.right = insert(root.right, key);
        return root;
    }
    static void inorder(Node root, List<Integer> out) {
        if (root == null) return;
        inorder(root.left, out); out.add(root.key); inorder(root.right, out);
    }
    public static void main(String[] args) {
        Node root = null;
        for (int key : new int[]{8, 3, 10, 1, 6}) root = insert(root, key);
        List<Integer> sorted = new ArrayList<>(); inorder(root, sorted);
        PriorityQueue<Integer> heap = new PriorityQueue<>(List.of(8, 3, 10, 1, 6));
        if (!sorted.equals(List.of(1, 3, 6, 8, 10)) || heap.remove() != 1)
            throw new AssertionError("tree/heap");
        System.out.println("BST inorder: " + sorted + " | heap minimum: 1");
    }
}
