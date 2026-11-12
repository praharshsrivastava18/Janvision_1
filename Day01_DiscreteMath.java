import java.util.*;

public class Day01_DiscreteMath {
    static List<Integer> bfs(Map<Integer, List<Integer>> graph, int start) {
        Set<Integer> seen = new HashSet<>();
        Queue<Integer> queue = new ArrayDeque<>();
        List<Integer> order = new ArrayList<>();
        seen.add(start);
        queue.add(start);
        while (!queue.isEmpty()) {
            int node = queue.remove();
            order.add(node);
            for (int next : graph.getOrDefault(node, List.of())) {
                if (seen.add(next)) queue.add(next);
            }
        }
        return order;
    }
    public static void main(String[] args) {
        Map<Integer, List<Integer>> graph = Map.of(
            0, List.of(1, 2), 1, List.of(0, 3),
            2, List.of(0, 3), 3, List.of(1, 2, 4), 4, List.of(3));
        List<Integer> result = bfs(graph, 0);
        if (!result.equals(List.of(0, 1, 2, 3, 4))) throw new AssertionError(result);
        System.out.println("BFS order: " + result);
    }
}
