import java.util.*;

public class Day07_AlgorithmsLab {
    static int knapsack(int[] weights, int[] values, int capacity) {
        int[] best = new int[capacity + 1];
        for (int i = 0; i < weights.length; i++)
            for (int cap = capacity; cap >= weights[i]; cap--)
                best[cap] = Math.max(best[cap], best[cap - weights[i]] + values[i]);
        return best[capacity];
    }
    static int[] dijkstra(List<List<int[]>> graph, int source) {
        int[] dist = new int[graph.size()]; Arrays.fill(dist, Integer.MAX_VALUE);
        dist[source] = 0;
        PriorityQueue<int[]> pq = new PriorityQueue<>(Comparator.comparingInt(a -> a[0]));
        pq.add(new int[]{0, source});
        while (!pq.isEmpty()) {
            int[] cur = pq.remove(); int cost = cur[0], node = cur[1];
            if (cost != dist[node]) continue;
            for (int[] edge : graph.get(node)) {
                int next = edge[0], candidate = cost + edge[1];
                if (candidate < dist[next]) { dist[next] = candidate; pq.add(new int[]{candidate, next}); }
            }
        }
        return dist;
    }
    public static void main(String[] args) {
        int value = knapsack(new int[]{2, 3, 4}, new int[]{4, 5, 7}, 5);
        List<List<int[]>> graph = new ArrayList<>();
        for (int i = 0; i < 4; i++) graph.add(new ArrayList<>());
        int[][][] edges = {{{1,4},{2,1}}, {{0,4},{2,2},{3,1}},
            {{0,1},{1,2},{3,5}}, {{1,1},{2,5}}};
        for (int i = 0; i < edges.length; i++) graph.get(i).addAll(Arrays.asList(edges[i]));
        int distance = dijkstra(graph, 0)[3];
        if (value != 9 || distance != 4) throw new AssertionError("algorithm result");
        System.out.println("knapsack: " + value + " | dist to 3: " + distance);
    }
}
